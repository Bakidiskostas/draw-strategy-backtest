#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Martingale Draw Strategy Backtest
=================================
Κατεβάζει ιστορικά αποτελέσματα + closing odds από το football-data.co.uk
(δωρεάν, νόμιμα δεδομένα) και κάνει walk-forward simulation της στρατηγικής:

  1. Υπολόγισε rolling ποσοστό ισοπαλιών κάθε ομάδας (τελευταίο 6μηνο).
  2. Αν ο μέσος όρος των δύο ομάδων > threshold -> υποψήφιο στοίχημα.
  3. Αν δύο υποψήφια ματς παίζουν ίδια μέρα/ώρα -> μόνο το μεγαλύτερο ποσοστό.
  4. Martingale: μετά από ήττα, αύξηση ποντάρισματος. Δύο modes:
       - "recovery": stake = (σωρευτικές απώλειες + target_profit)/(odds-1)
                     (σωστό sizing για αποδόσεις ~3.2)
       - "double":   κλασικός διπλασιασμός 1-2-4-8-...
  5. Μετά από MAX_STEPS σερί ήττες -> "σκάσιμο", καταγραφή, reset.

Χρήση:
  python martingale_backtest.py                        # default grid
  python martingale_backtest.py --thresholds 35 40 45 50 --targets 1 5 10
  python martingale_backtest.py --leagues I2 SP2 F2 G1 --seasons 2324 2425 2526
  python martingale_backtest.py --mode double
  python martingale_backtest.py --list-leagues
"""

import argparse
import io
import math
import os
import sys
import re
import difflib
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    requests = None

from dashboard_template import DASHBOARD_TEMPLATE

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
# "Extra" leagues live in one all-seasons file per country, different columns.
EXTRA_URL = "https://www.football-data.co.uk/new/{code}.csv"

# Main-format leagues (season-by-season files, rich odds columns).
LEAGUES = {
    "E0": "England Premier League",
    "E1": "England Championship",
    "D1": "Germany Bundesliga",
    "D2": "Germany 2. Bundesliga",
    "SP1": "Spain La Liga",
    "SP2": "Spain Segunda",
    "I1": "Italy Serie A",
    "I2": "Italy Serie B",
    "F1": "France Ligue 1",
    "F2": "France Ligue 2",
    "N1": "Netherlands Eredivisie",
    "P1": "Portugal Primeira Liga",
    "B1": "Belgium Pro League",
    "G1": "Greece Super League",
    "T1": "Turkey Super Lig",
    "SC0": "Scotland Premiership",
}

# Extra-format leagues (one file per country, all seasons; different schema).
EXTRA_LEAGUES = {
    "ARG": "Argentina Primera Division",
    "AUT": "Austria Bundesliga",
    "BRA": "Brazil Serie A",
    "SWZ": "Switzerland Super League",
    # Also available on the same source if you want them:
    # CHN DNK FIN IRL JPN MEX NOR POL ROU RUS SWE USA
}
LEAGUES.update(EXTRA_LEAGUES)

DEFAULT_LEAGUES = [
    # second divisions (draw-heavy) + top divisions, main format
    "SP2", "I2", "F2", "I1", "F1", "G1", "D2", "E1",
    "D1", "P1", "B1", "N1", "SC0",
    # extra-format leagues
    "AUT", "SWZ", "ARG", "BRA",
]
DEFAULT_SEASONS = ["2122", "2223", "2324", "2425", "2526"]

WINDOW_DAYS = 180        # rolling "last 6 months"
MIN_MATCHES = 8          # min matches in the window for a reliable rate
DATA_DIR = Path(os.environ.get("MB_DATA_DIR", "data"))


# ---------------------------------------------------------------- data layer
def download_csv(league: str, season: str) -> Path | None:
    """Κατεβάζει (με cache) ένα CSV σεζόν/λίγκας."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{league}_{season}.csv"
    if path.exists() and path.stat().st_size > 1000:
        return path
    if requests is None:
        print("  !! requests missing (pip install requests)")
        return None
    url = BASE_URL.format(season=season, league=league)
    try:
        r = requests.get(url, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 (research script)"})
        if r.status_code != 200 or len(r.content) < 1000:
            print(f"  !! Not found: {url}")
            return None
        path.write_bytes(r.content)
        print(f"  ✓ {league} {season} ({len(r.content)//1024} KB)")
        return path
    except Exception as e:
        print(f"  !! Download error {url}: {e}")
        return None


def download_extra(code: str) -> Path | None:
    """Download (cached) an all-seasons file for an extra-format league."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{code}_ALL.csv"
    if path.exists() and path.stat().st_size > 1000:
        return path
    if requests is None:
        print("  !! requests missing (pip install requests)")
        return None
    url = EXTRA_URL.format(code=code)
    try:
        r = requests.get(url, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 (research script)"})
        if r.status_code != 200 or len(r.content) < 1000:
            print(f"  !! Not found: {url}")
            return None
        path.write_bytes(r.content)
        print(f"  OK {code} (extra, {len(r.content)//1024} KB)")
        return path
    except Exception as e:
        print(f"  !! Download error {url}: {e}")
        return None


def load_extra_league(code: str, date_from: pd.Timestamp) -> pd.DataFrame | None:
    """Load an extra-format league and map its columns to the main schema."""
    p = download_extra(code)
    if p is None:
        return None
    try:
        df = pd.read_csv(io.StringIO(p.read_text(encoding="latin-1")),
                         on_bad_lines="skip")
    except Exception as e:
        print(f"  !! Read error {p}: {e}")
        return None
    # Extra files use Home/Away/Res/HG/AG instead of HomeTeam/AwayTeam/FTR/...
    rename = {"Home": "HomeTeam", "Away": "AwayTeam", "Res": "FTR",
              "HG": "FTHG", "AG": "FTAG"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    needed = {"HomeTeam", "AwayTeam", "FTR", "Date"}
    if not needed.issubset(df.columns):
        print(f"  !! {code}: unexpected columns, skipping. Got: {list(df.columns)[:12]}")
        return None
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True,
                                errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df[df["Date"] >= date_from]
    df = df.assign(League=code, Season="extra", Div=code)
    return df


def load_matches(leagues: list[str], seasons: list[str]) -> pd.DataFrame:
    """Load and merge all CSVs into one date-sorted DataFrame."""
    # earliest requested season -> date cutoff for extra (all-seasons) files
    yr = min(int("20" + s[:2]) for s in seasons)
    date_from = pd.Timestamp(f"{yr}-07-01")

    frames = []
    for lg in leagues:
        if lg in EXTRA_LEAGUES:
            df = load_extra_league(lg, date_from)
            if df is not None and len(df):
                frames.append(df)
            continue
        for ss in seasons:
            p = download_csv(lg, ss)
            if p is None:
                continue
            try:
                df = pd.read_csv(io.StringIO(p.read_text(encoding="latin-1")),
                                 on_bad_lines="skip")
            except Exception as e:
                print(f"  !! Read error {p}: {e}")
                continue
            df = df.assign(League=lg, Season=ss)
            frames.append(df)
    if not frames:
        sys.exit("No data loaded. Check connection / league codes.")
    m = pd.concat(frames, ignore_index=True).copy()

    m = m.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTR"])
    m["Date"] = pd.to_datetime(m["Date"], format="mixed", dayfirst=True)
    if "Time" not in m.columns:
        m["Time"] = "15:00"
    m["Time"] = m["Time"].fillna("15:00")

    # Απόδοση ισοπαλίας. Προτεραιότητα σε ΜΕΣΗ CLOSING τιμή αγοράς (AvgCD)
    # -> Pinnacle closing (PSCD) -> Bet365 closing (B365CD) -> μη-closing
    # μέσοι όροι. ΔΕΝ χρησιμοποιούμε Max* (είναι η καλύτερη τιμή της αγοράς,
    # upward-biased -> υποθέτει ότι πάντα πιάνεις το κορυφαίο book).
    pref = ["AvgCD", "PSCD", "B365CD", "AvgD", "PSD", "B365D", "BbAvD"]
    odds_cols = [c for c in pref if c in m.columns]
    m["DrawOdds"] = pd.NA
    m["OddsSource"] = pd.NA
    for c in odds_cols:
        vals = pd.to_numeric(m[c], errors="coerce")
        take = m["DrawOdds"].isna() & vals.notna()
        m.loc[take, "DrawOdds"] = vals[take]
        m.loc[take, "OddsSource"] = c
    m["DrawOdds"] = pd.to_numeric(m["DrawOdds"], errors="coerce")
    m = m.dropna(subset=["DrawOdds"])

    m["IsDraw"] = (m["FTR"] == "D").astype(int)
    m = m.sort_values(["Date", "Time"]).reset_index(drop=True)

    dr = m["IsDraw"].mean()
    print(f"\nTotal matches: {len(m)} | Period: "
          f"{m["Date"].min().date()} to {m["Date"].max().date()} | "
          f"Overall draw rate: {dr:.1%}")
    print(f"Fair draw odds (no margin) = 1/{dr:.3f} = {1/dr:.2f}")

    print("\n-- Draw odds diagnostic --")
    print("Price source (matches per column):")
    for src, cnt in m["OddsSource"].value_counts().items():
        print(f"   {src:7s} {cnt:6d}")
    q = m["DrawOdds"].quantile([0, .10, .25, .50, .75, .90, 1.0])
    print("DrawOdds distribution:")
    print(f"   min={q[0.0]:.2f}  p10={q[0.10]:.2f}  p25={q[0.25]:.2f}  "
          f"median={q[0.50]:.2f}  mean={m['DrawOdds'].mean():.2f}  "
          f"p75={q[0.75]:.2f}  p90={q[0.90]:.2f}  max={q[1.0]:.2f}")
    below3 = (m["DrawOdds"] < 3.0).mean()
    print(f"   Share of matches with odds < 3.00: {below3:.1%}")

    # --- Γανιότα (overround / vig) της Bet365, υπολογισμένη από τα δεδομένα ---
    # overround = (1/H + 1/D + 1/A) - 1. Προτίμηση closing (B365C*), αλλιώς pre.
    for tag, (ch, cd, ca) in {
        "closing": ("B365CH", "B365CD", "B365CA"),
        "pre-match": ("B365H", "B365D", "B365A"),
    }.items():
        if all(c in m.columns for c in (ch, cd, ca)):
            h = pd.to_numeric(m[ch], errors="coerce")
            d = pd.to_numeric(m[cd], errors="coerce")
            a = pd.to_numeric(m[ca], errors="coerce")
            over = (1/h + 1/d + 1/a) - 1
            over = over.dropna()
            print(f"\n-- Bet365 margin ({tag}) over {len(over)} matches --")
            print(f"   Mean margin: {over.mean():.2%}  |  "
                  f"median: {over.median():.2%}")
            # how much of the margin sits on the draw leg
            draw_vig = (1/d / (1/h + 1/d + 1/a)) - m["IsDraw"].mean()
            print(f"   Implied draw prob (Bet365, de-vig): "
                  f"{(1/d/(1/h+1/d+1/a)).mean():.1%}  vs  "
                  f"actual {m['IsDraw'].mean():.1%}")
            break
    return m


# ------------------------------------------------------- rolling draw rates
def add_rolling_draw_rates(m: pd.DataFrame) -> pd.DataFrame:
    """
    Για κάθε ματς: ποσοστό ισοπαλιών κάθε ομάδας στα WINDOW_DAYS πριν
    την ημερομηνία του ματς (ΧΩΡΙΣ το ίδιο το ματς -> όχι look-ahead bias).
    """
    long = pd.concat([
        m[["Date", "HomeTeam", "IsDraw"]].rename(columns={"HomeTeam": "Team"}),
        m[["Date", "AwayTeam", "IsDraw"]].rename(columns={"AwayTeam": "Team"}),
    ]).sort_values("Date").reset_index(drop=True)

    history: dict[str, list[tuple[pd.Timestamp, int]]] = {}
    for team, grp in long.groupby("Team"):
        history[team] = list(zip(grp["Date"], grp["IsDraw"]))

    def rate_before(team: str, date: pd.Timestamp) -> tuple[float, int]:
        cutoff = date - pd.Timedelta(days=WINDOW_DAYS)
        rel = [d for dt, d in history.get(team, []) if cutoff <= dt < date]
        return (sum(rel) / len(rel) if rel else float("nan"), len(rel))

    rates_h, n_h, rates_a, n_a = [], [], [], []
    for _, row in m.iterrows():
        rh, nh = rate_before(row["HomeTeam"], row["Date"])
        ra, na = rate_before(row["AwayTeam"], row["Date"])
        rates_h.append(rh); n_h.append(nh)
        rates_a.append(ra); n_a.append(na)
    m = m.copy()
    m["HomeDrawRate"], m["HomeN"] = rates_h, n_h
    m["AwayDrawRate"], m["AwayN"] = rates_a, n_a
    m["PairRate"] = (m["HomeDrawRate"] + m["AwayDrawRate"]) / 2
    return m


def select_candidates(m: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Φίλτρο threshold + κανόνας 'ίδια ώρα -> μόνο το μεγαλύτερο ποσοστό'."""
    c = m[(m["PairRate"] >= threshold)
          & (m["HomeN"] >= MIN_MATCHES)
          & (m["AwayN"] >= MIN_MATCHES)].copy()
    if c.empty:
        return c
    # Ίδια μέρα & ώρα (σε όλες τις λίγκες) -> κρατάμε το μεγαλύτερο PairRate
    c = (c.sort_values("PairRate", ascending=False)
          .groupby(["Date", "Time"], as_index=False)
          .head(1)
          .sort_values(["Date", "Time"])
          .reset_index(drop=True))
    return c


# ----------------------------------------------------------- the simulation
def greek_tax(net_win: float) -> float:
    """Greek tiered tax on the NET winnings of a single betting slip.
    0-100 free, 100-200 @2.5%, 200-500 @5%, 500+ @7.5% (progressive)."""
    if net_win <= 100:
        return 0.0
    brackets = [(100, 0.0), (200, 0.025), (500, 0.05), (float("inf"), 0.075)]
    tax, prev = 0.0, 0.0
    for cap, rate in brackets:
        if net_win > prev:
            tax += (min(net_win, cap) - prev) * rate
            prev = cap
        else:
            break
    return tax


def simulate(cands: pd.DataFrame, mode: str, target: float,
             max_steps: int, base_stake: float = 1.0,
             tax_mode: str = "none", tax_rate: float = 0.0) -> dict:
    """
    Σειριακή προσομοίωση ενός παίκτη: ένα ποντάρισμα τη φορά,
    χρονολογική σειρά, πραγματικές closing odds.
    tax_mode: 'none' | 'de' (rate on every stake) | 'gr' (tiered on each win).
    """
    bankroll = 0.0
    cum_loss = 0.0
    step = 0
    peak, max_dd = 0.0, 0.0
    min_bankroll = 0.0
    max_stake_used = 0.0
    cycles_won, busts, bets = 0, 0, 0
    worst_seq_loss = 0.0
    total_staked = 0.0
    total_tax = 0.0
    step_at_bust = []

    for _, row in cands.iterrows():
        odds = float(row["DrawOdds"])
        if mode == "recovery":
            stake = (cum_loss + target) / (odds - 1)
        elif mode == "double":
            stake = base_stake * (2 ** step)
        else:  # flat -> σταθερό ποντάρισμα, καθόλου martingale
            stake = base_stake
        stake = math.ceil(stake * 100) / 100
        max_stake_used = max(max_stake_used, stake)
        total_staked += stake
        bets += 1

        # Germany: 5.3% of every stake, regardless of outcome
        if tax_mode == "de":
            t = tax_rate * stake
            bankroll -= t
            total_tax += t

        if row["IsDraw"] == 1:
            # Οι απώλειες του κύκλου έχουν ΗΔΗ αφαιρεθεί από το bankroll
            # στα προηγούμενα χαμένα ποντάρια. Εδώ προσθέτουμε ΜΟΝΟ το
            # καθαρό κέρδος του νικηφόρου στοιχήματος. (Το cum_loss είναι
            # απλώς μεταβλητή για το sizing, ΔΕΝ αφαιρείται ξανά.)
            net_win = stake * (odds - 1)
            bankroll += net_win
            # Greece: tiered tax on this slip's net winnings
            if tax_mode == "gr":
                t = greek_tax(net_win)
                bankroll -= t
                total_tax += t
            cycles_won += 1
            cum_loss, step = 0.0, 0
        else:
            bankroll -= stake
            cum_loss += stake
            step += 1
            if mode != "flat" and step >= max_steps:
                busts += 1
                worst_seq_loss = max(worst_seq_loss, cum_loss)
                step_at_bust.append(cum_loss)
                cum_loss, step = 0.0, 0

        peak = max(peak, bankroll)
        max_dd = max(max_dd, peak - bankroll)
        min_bankroll = min(min_bankroll, bankroll)

    avg_bust = (sum(step_at_bust) / len(step_at_bust)) if step_at_bust else 0.0
    return {
        "bets": bets,
        "cycles_won": cycles_won,
        "busts": busts,
        "final_pnl": round(bankroll, 2),
        "max_drawdown": round(max_dd, 2),
        "min_bankroll": round(min_bankroll, 2),
        "max_stake": round(max_stake_used, 2),
        "worst_bust_loss": round(worst_seq_loss, 2),
        "avg_bust_loss": round(avg_bust, 2),
        "total_staked": round(total_staked, 2),
        "tax_paid": round(total_tax, 2),
        "capital_needed": round(max_dd, 2),
    }


def streak_analysis(cands: pd.DataFrame) -> dict:
    """Distribution of 'attempts until a draw'.
    dist[k] = how many times the draw finally came on the k-th attempt
    (i.e. after k-1 straight non-draws). worst = the longest such streak.
    worst_odds = the real odds of each bet in that worst streak."""
    dist: dict[int, int] = {}
    worst, worst_odds, cur = 0, [], []
    for _, row in cands.iterrows():
        cur.append(float(row["DrawOdds"]))
        if row["IsDraw"] == 1:
            k = len(cur)
            dist[k] = dist.get(k, 0) + 1
            if k > worst:
                worst, worst_odds = k, cur[:]
            cur = []
    # a trailing run of non-draws never resolved into a draw -> not counted
    return {"dist": dist, "worst": worst, "worst_odds": worst_odds}


def follow_cost(odds_list: list, mode: str, target: float,
                base: float = 1.0) -> float:
    """Total capital you must stake to follow a whole streak to its win."""
    if not odds_list:
        return 0.0
    if mode == "flat":
        return round(len(odds_list) * base, 2)
    if mode == "double":
        return round(base * (2 ** len(odds_list) - 1), 2)
    cum = total = 0.0                     # recovery
    for o in odds_list:
        s = math.ceil(((cum + target) / (o - 1)) * 100) / 100
        total += s
        cum += s
    return round(total, 2)


def draws_per_run(cands: pd.DataFrame, max_steps: int) -> list[int]:
    """How many draws happen between busts (a max_steps losing streak).
    Independent of the staking mode — depends only on the draw sequence."""
    runs, wins, loss_streak = [], 0, 0
    for d in cands["IsDraw"]:
        if d == 1:
            wins += 1
            loss_streak = 0
        else:
            loss_streak += 1
            if loss_streak >= max_steps:
                runs.append(wins)
                wins, loss_streak = 0, 0
    runs.append(wins)      # trailing run with no closing bust
    return runs


# ------------------------------------------------ upcoming fixtures + odds
FIXTURES_URL = "https://www.football-data.co.uk/fixtures.csv"

# targets που εμφανίζει το dashboard για τον υπολογισμό ποντάρισματος
DASH_TARGETS = [5, 10, 15, 20, 25]


def download_fixtures() -> pd.DataFrame | None:
    """Κατεβάζει τους προσεχείς αγώνες (τρέχουσα εβδομάδα) με αποδόσεις."""
    if requests is None:
        return None
    try:
        r = requests.get(FIXTURES_URL, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 (research script)"})
        if r.status_code != 200 or len(r.content) < 200:
            print("  !! fixtures.csv download failed")
            return None
        fx = pd.read_csv(io.StringIO(r.content.decode("latin-1")),
                         on_bad_lines="skip")
        fx = fx.dropna(subset=["Date", "HomeTeam", "AwayTeam"])
        fx["Date"] = pd.to_datetime(fx["Date"], format="mixed", dayfirst=True)
        if "Time" not in fx.columns:
            fx["Time"] = "15:00"
        fx["Time"] = fx["Time"].fillna("15:00")
        print(f"  OK fixtures.csv: {len(fx)} upcoming matches")
        return fx
    except Exception as e:
        print(f"  !! fixtures error: {e}")
        return None


def best_draw_odds(row: pd.Series) -> tuple[float, str]:
    """Μεγαλύτερη διαθέσιμη απόδοση ισοπαλίας + ποιος bookie τη δίνει."""
    books = {"MaxD": "market max", "B365D": "Bet365", "PSD": "Pinnacle",
             "AvgD": "market avg", "BbMxD": "market max", "WHD": "William Hill",
             "IWD": "Interwetten", "VCD": "VC Bet"}
    best_o, best_src = 0.0, "-"
    for col, name in books.items():
        if col in row.index:
            v = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(v) and v > best_o:
                best_o, best_src = float(v), name
    return best_o, best_src


def team_rate_now(m: pd.DataFrame, team: str, asof: pd.Timestamp):
    cutoff = asof - pd.Timedelta(days=WINDOW_DAYS)
    sub = m[((m["HomeTeam"] == team) | (m["AwayTeam"] == team))
            & (m["Date"] >= cutoff) & (m["Date"] < asof)]
    if len(sub) < MIN_MATCHES:
        return float("nan"), len(sub)
    return sub["IsDraw"].mean(), len(sub)


# The Odds API (free tier: 500 req/month, needs a free key set as ODDS_API_KEY).
# Covers leagues that football-data.co.uk's fixtures.csv does NOT (Argentina, Brazil).
ODDS_API_BASE = "https://api.the-odds-api.com/v4/sports/{sport}/odds/"
ODDS_SPORT_KEYS = {
    "soccer_argentina_primera_division": "Argentina Primera Division",
    "soccer_brazil_campeonato": "Brazil Serie A",
}


def _norm_team(name: str) -> str:
    """Normalize a club name so different sources can be matched."""
    s = str(name).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    for tok in ("club atletico", "atletico", "deportivo", "club", "cd", "ca",
                "fc", "ac", "sc", "afc", "cf", "de", "the", "fbc"):
        s = re.sub(rf"\b{tok}\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _match_team(name: str, norm_map: dict, norm_keys: list) -> str | None:
    n = _norm_team(name)
    if n in norm_map:
        return norm_map[n]
    close = difflib.get_close_matches(n, norm_keys, n=1, cutoff=0.86)
    return norm_map[close[0]] if close else None


def parse_odds_events(events: list, m: pd.DataFrame, league_name: str,
                      min_threshold: float, unmatched: set) -> list[dict]:
    """Turn The Odds API events into candidate rows (testable, no network)."""
    today = pd.Timestamp.now(tz="UTC")
    teams = pd.unique(pd.concat([m["HomeTeam"], m["AwayTeam"]]))
    norm_map = {}
    for t in teams:
        norm_map.setdefault(_norm_team(t), t)
    norm_keys = list(norm_map.keys())
    out = []
    for ev in events:
        best = 0.0
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk.get("key") != "h2h":
                    continue
                for oc in mk.get("outcomes", []):
                    if oc.get("name") == "Draw" and float(oc.get("price", 0)) > best:
                        best = float(oc["price"])
        if best <= 1:
            continue
        ct = pd.to_datetime(ev.get("commence_time"), utc=True, errors="coerce")
        if pd.isna(ct) or ct < today:
            continue
        hm = _match_team(ev.get("home_team", ""), norm_map, norm_keys)
        am = _match_team(ev.get("away_team", ""), norm_map, norm_keys)
        if not hm:
            unmatched.add(ev.get("home_team", ""))
        if not am:
            unmatched.add(ev.get("away_team", ""))
        if not hm or not am:
            continue
        asof = ct.tz_convert(None)
        rh, _ = team_rate_now(m, hm, asof)
        ra, _ = team_rate_now(m, am, asof)
        if math.isnan(rh) or math.isnan(ra):
            continue
        pair = (rh + ra) / 2
        if pair < min_threshold:
            continue
        out.append({
            "date": asof.strftime("%Y-%m-%d"), "time": asof.strftime("%H:%M"),
            "league": league_name, "home": hm, "away": am,
            "home_rate": round(rh * 100, 1), "away_rate": round(ra * 100, 1),
            "pair_rate": round(pair * 100, 1),
            "best_odds": round(best, 2), "odds_src": "Odds API (best)",
            "implied": round(100 / best, 1),
        })
    return out


def fetch_odds_api_candidates(m: pd.DataFrame, api_key: str,
                              min_threshold: float = 0.35) -> list[dict]:
    """Fetch upcoming Argentina/Brazil fixtures + draw odds from The Odds API."""
    if requests is None:
        return []
    out, unmatched = [], set()
    for sport, name in ODDS_SPORT_KEYS.items():
        try:
            r = requests.get(ODDS_API_BASE.format(sport=sport),
                             params={"apiKey": api_key, "regions": "eu,uk",
                                     "markets": "h2h", "oddsFormat": "decimal"},
                             timeout=30)
            if r.status_code != 200:
                print(f"  !! Odds API {sport}: HTTP {r.status_code} "
                      f"{r.text[:100]}")
                continue
            events = r.json()
        except Exception as e:
            print(f"  !! Odds API error {sport}: {e}")
            continue
        got = parse_odds_events(events, m, name, min_threshold, unmatched)
        print(f"  {name}: {len(got)} candidate(s) from {len(events)} fixtures")
        out += got
    if unmatched:
        print(f"  (Odds API: {len(unmatched)} team names had no history match — "
              f"e.g. {', '.join(list(unmatched)[:3])})")
    return out


def find_upcoming_candidates(m: pd.DataFrame, fx: pd.DataFrame,
                             min_threshold: float = 0.35) -> list[dict]:
    """Upcoming matches whose two teams average draw rate >= threshold."""
    today = pd.Timestamp.now().normalize()
    out = []
    for _, row in fx.iterrows():
        asof = row["Date"]
        if pd.isna(asof) or asof < today:   # only genuinely upcoming fixtures
            continue
        rh, nh = team_rate_now(m, row["HomeTeam"], asof)
        ra, na = team_rate_now(m, row["AwayTeam"], asof)
        if math.isnan(rh) or math.isnan(ra):
            continue
        pair = (rh + ra) / 2
        if pair < min_threshold:
            continue
        odds, src = best_draw_odds(row)
        if odds <= 1.0:
            continue
        out.append({
            "date": asof.strftime("%Y-%m-%d"),
            "time": str(row.get("Time", "")),
            "league": LEAGUES.get(row.get("Div", ""), row.get("Div", "")),
            "home": row["HomeTeam"], "away": row["AwayTeam"],
            "home_rate": round(rh * 100, 1), "away_rate": round(ra * 100, 1),
            "pair_rate": round(pair * 100, 1),
            "best_odds": round(odds, 2), "odds_src": src,
            "implied": round(100 / odds, 1),
        })
    out.sort(key=lambda d: (d["date"], d["time"]))
    return out


def stake_table(odds: float, cum_loss: float = 0.0) -> dict:
    """Προτεινόμενο ποντάρισμα ανά mode, για δεδομένη απόδοση + τρέχουσα ζημιά."""
    t = {}
    for tgt in DASH_TARGETS:
        t[f"recovery_{tgt}"] = math.ceil(((cum_loss + tgt) / (odds - 1)) * 100) / 100
    return t


def compute_diagnostics(m: pd.DataFrame) -> dict:
    dr = float(m["IsDraw"].mean())
    q = m["DrawOdds"].quantile([0, .10, .25, .50, .75, .90, 1.0])
    diag = {
        "matches": int(len(m)),
        "date_from": str(m["Date"].min().date()),
        "date_to": str(m["Date"].max().date()),
        "draw_rate": round(dr * 100, 1),
        "fair_odds": round(1 / dr, 2),
        "odds_min": round(float(q[0.0]), 2),
        "odds_p25": round(float(q[0.25]), 2),
        "odds_median": round(float(q[0.50]), 2),
        "odds_mean": round(float(m["DrawOdds"].mean()), 2),
        "odds_p75": round(float(q[0.75]), 2),
        "odds_max": round(float(q[1.0]), 2),
        "pct_below_3": round(float((m["DrawOdds"] < 3.0).mean()) * 100, 1),
        "margin": None, "devig_draw": None,
    }
    if all(c in m.columns for c in ("B365CH", "B365CD", "B365CA")):
        h = pd.to_numeric(m["B365CH"], errors="coerce")
        d = pd.to_numeric(m["B365CD"], errors="coerce")
        a = pd.to_numeric(m["B365CA"], errors="coerce")
        over = ((1/h + 1/d + 1/a) - 1).dropna()
        diag["margin"] = round(float(over.mean()) * 100, 2)
        diag["devig_draw"] = round(float((1/d/(1/h+1/d+1/a)).mean()) * 100, 1)
    return diag


def build_dashboard(diag: dict, candidates: list[dict],
                    backtest_rows: list[dict], path: str = "dashboard.html",
                    leagues_breakdown: list[dict] | None = None,
                    streaks_map: dict | None = None,
                    tax_label: str = "none"):
    """Write a self-contained HTML dashboard with data embedded."""
    import json
    payload = {
        "diag": diag,
        "candidates": candidates,
        "backtest": backtest_rows,
        "leagues": leagues_breakdown or [],
        "streaks": streaks_map or {},
        "targets": DASH_TARGETS,
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "tax": tax_label,
    }
    html = DASHBOARD_TEMPLATE.replace(
        "/*__DATA__*/null", json.dumps(payload, ensure_ascii=False))
    # Embed the icon as a data URI so the logo/favicon always show, even if the
    # PNG file isn't served next to the HTML. Falls back to the file path.
    icon_src = "icon-512.png"
    icon_path = Path("icon-512.png")
    if icon_path.exists():
        import base64
        b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
        icon_src = f"data:image/png;base64,{b64}"
    html = html.replace("__ICON_SRC__", icon_src)
    Path(path).write_text(html, encoding="utf-8")
    print(f"Saved: {path}")


def run_backtest(m: pd.DataFrame, thresholds, targets, modes,
                 max_steps_list, years: float, label: str,
                 tax_mode: str = "none", tax_rate: float = 0.0) -> list[dict]:
    """Run the full backtest grid on a (possibly league-filtered) DataFrame."""
    rows = []
    for thr_pct in thresholds:
        cands = select_candidates(m, thr_pct / 100)
        n = len(cands)
        adr = cands["IsDraw"].mean() if n else float("nan")
        ao = cands["DrawOdds"].mean() if n else float("nan")
        sa = streak_analysis(cands)
        for max_steps in max_steps_list:
            for mode in modes:
                tgts = targets if mode == "recovery" else [None]
                if mode == "flat":
                    tgts = [None]
                for tgt in tgts:
                    res = simulate(cands, mode, tgt or 1.0, max_steps,
                                   tax_mode=tax_mode, tax_rate=tax_rate)
                    cap = res["capital_needed"]
                    roc = round(res["final_pnl"] / cap, 2) if cap > 0 else "-"
                    wsc = follow_cost(sa["worst_odds"], mode, tgt or 1.0)
                    rows.append({
                        "league": label,
                        "threshold_%": thr_pct, "bust_at": max_steps,
                        "mode": mode,
                        "target_€": tgt if tgt is not None else "-",
                        "matches": n,
                        "real_draw_%": round(adr * 100, 1) if n else "-",
                        "avg_odds": round(ao, 2) if n else "-",
                        **res,
                        "pnl_per_year": round(res["final_pnl"] / years, 2),
                        "roc": roc,   # P&L / Capital = return on capital at risk
                        "worst_streak": sa["worst"],
                        "worst_streak_capital": wsc,
                    })
    return rows


def league_breakdown(m: pd.DataFrame, thresholds, leagues) -> list[dict]:
    """Per-league counts: matches, draw rate, and candidates per threshold."""
    out = []
    for lg in leagues:
        sub = m[m["League"] == lg]
        if len(sub) == 0:
            continue
        row = {"code": lg, "name": LEAGUES.get(lg, lg),
               "matches": int(len(sub)),
               "draw_pct": round(float(sub["IsDraw"].mean()) * 100, 1)}
        for thr in thresholds:
            row[f"cand_{int(thr)}"] = int(len(select_candidates(sub, thr / 100)))
        out.append(row)
    out.sort(key=lambda r: r["matches"], reverse=True)
    return out


# --------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Martingale draw backtest")
    ap.add_argument("--leagues", nargs="+", default=DEFAULT_LEAGUES)
    ap.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    ap.add_argument("--thresholds", nargs="+", type=float,
                    default=[40, 45, 50],
                    help="in %% (e.g. 40 45 50)")
    ap.add_argument("--targets", nargs="+", type=float, default=[5, 10, 15, 20, 25],
                    help="profit target per winning cycle in EUR (recovery mode)")
    ap.add_argument("--mode", choices=["recovery", "double", "both"],
                    default="both")
    ap.add_argument("--max-steps", nargs="+", type=int, default=[8, 9, 10, 11, 12],
                    help="consecutive losses that count as a bust (one or more)")
    ap.add_argument("--tax", choices=["none", "de", "gr"], default="none",
                    help="withholding tax: de=Germany 5.3%% on stake, "
                         "gr=Greece tiered on winnings")
    ap.add_argument("--list-leagues", action="store_true")
    args = ap.parse_args()

    if args.list_leagues:
        for k, v in LEAGUES.items():
            print(f"  {k:4s} {v}")
        return

    print("Downloading data from football-data.co.uk ...")
    m = load_matches(args.leagues, args.seasons)
    print("Computing rolling draw rates (6-month window, no look-ahead)...")
    m = add_rolling_draw_rates(m)

    # span of the dataset in years, for annualized P&L
    years = max((m["Date"].max() - m["Date"].min()).days / 365.25, 0.5)

    modes = (["flat", "recovery", "double"] if args.mode == "both"
             else [args.mode])
    tax_rate = 0.053 if args.tax == "de" else 0.0
    tax_label = {"none": "none", "de": "Germany 5.3% on stake",
                 "gr": "Greece tiered on winnings"}[args.tax]
    if args.tax != "none":
        print(f"Applying withholding tax: {tax_label}")

    # combined ("ALL") backtest + a per-league backtest for the dropdown
    rows = run_backtest(m, args.thresholds, args.targets, modes,
                        args.max_steps, years, "ALL",
                        tax_mode=args.tax, tax_rate=tax_rate)
    present = [lg for lg in args.leagues if (m["League"] == lg).any()]
    for lg in present:
        rows += run_backtest(m[m["League"] == lg], args.thresholds,
                             args.targets, modes, args.max_steps, years, lg,
                             tax_mode=args.tax, tax_rate=tax_rate)

    # per-league breakdown (matches, draw rate, candidates per threshold)
    breakdown = league_breakdown(m, args.thresholds, present)

    # streak analysis per league|threshold, for the click-to-inspect modal
    streaks_map = {}

    def add_streaks(sub: pd.DataFrame, label: str):
        for thr_pct in args.thresholds:
            c = select_candidates(sub, thr_pct / 100)
            sa = streak_analysis(c)
            streaks_map[f"{label}|{thr_pct}"] = {
                "dist": {str(k): v for k, v in sorted(sa["dist"].items())},
                "worst": sa["worst"],
                "worst_odds": [round(o, 2) for o in sa["worst_odds"]],
            }

    add_streaks(m, "ALL")
    for lg in present:
        add_streaks(m[m["League"] == lg], lg)

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print("\n" + "=" * 100)
    print(f"RESULTS (walk-forward, real closing odds) | span {years:.1f} years")
    print("=" * 100)
    # console shows the combined "ALL" view; the CSV/dashboard hold every league
    all_view = out[out["league"] == "ALL"].drop(columns=["league"])
    print(all_view.to_string(index=False))
    out.to_csv("backtest_results.csv", index=False)
    print("\nSaved: backtest_results.csv (includes per-league rows)")

    print("\n-- By league (matches / candidates per threshold) --")
    if breakdown:
        print(pd.DataFrame(breakdown).to_string(index=False))

    # ---- Dashboard: diagnostics + upcoming candidates + stakes ----
    print("\nBuilding dashboard...")
    diag = compute_diagnostics(m)
    print("Fetching upcoming fixtures (fixtures.csv)...")
    fx = download_fixtures()
    candidates = []
    cand_thr = min(args.thresholds) / 100    # match the lowest backtest threshold
    if fx is not None:
        candidates = find_upcoming_candidates(m, fx, min_threshold=cand_thr)
        print(f"  Upcoming candidates (>={int(cand_thr*100)}%): {len(candidates)}")
    else:
        print("  (No upcoming fixtures — the dashboard will show analysis only.)")
    # Argentina/Brazil via The Odds API (optional). Key from env var, or from a
    # local odds_key.txt (git-ignored) — so no launcher script is required.
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key and Path("odds_key.txt").exists():
        api_key = Path("odds_key.txt").read_text(encoding="utf-8").strip()
    if api_key:
        print("Fetching Argentina/Brazil odds (The Odds API)...")
        candidates += fetch_odds_api_candidates(m, api_key, min_threshold=cand_thr)
        candidates.sort(key=lambda d: (d["date"], d["time"]))
    else:
        print("  (Set ODDS_API_KEY for Argentina/Brazil upcoming games — see README.)")
    build_dashboard(diag, candidates, rows, leagues_breakdown=breakdown,
                    streaks_map=streaks_map, tax_label=tax_label)

    print("""
How to read this:
  matches         how many matches passed the filter (few = threshold too strict)
  real_draw_%     the ACTUAL draw rate among the filtered matches
                  (compare with 1/avg_odds ~ the market's implied probability)
  final_pnl       final profit/loss in EUR
  busts           how many times a max_steps losing streak blew up
  bust_at         losing-streak length treated as a blow-up (compared 9-12)
  pnl_per_year    final_pnl spread over the dataset span (the honest figure)
  roc             P&L / Capital = return on the capital you had to risk
  capital_needed  the bankroll you would need to survive the worst stretch
""")


if __name__ == "__main__":
    main()
