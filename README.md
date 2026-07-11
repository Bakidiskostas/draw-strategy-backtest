# Draw Ledger — Football Draw Strategy Backtest & Dashboard

**[▶ Live demo](https://bakidiskostas.github.io/draw-strategy-backtest/)**

A research tool that backtests draw-betting strategies (including the martingale
system) against real historical football results and closing odds, and generates
a self-contained HTML dashboard. Built to answer one question honestly: **does any
of this actually work?**

Data comes from [football-data.co.uk](https://www.football-data.co.uk/), which
publishes free, public CSVs of results and bookmaker odds.

---

## ⚠️ This is not betting advice

**Read this before anything else.**

- This is an **analysis and education tool**, not a tipster and not a system to make
  money. Nothing here is financial or betting advice.
- **Betting has a negative expected value.** Over time, the bookmaker's margin means
  the average bettor loses. This project's own backtest demonstrates exactly that.
- The **martingale** system (doubling after a loss) does not change the expected
  value. It trades a steady trickle of small wins for rare, catastrophic losses. In
  the backtest, a single 10-loss streak wipes out dozens of wins.
- **Gambling can be addictive** and can lead to serious financial and personal harm.
  If you bet at all, only ever stake money you can afford to lose entirely.

### Where to get help

- **Germany** — BIÖG (formerly BZgA) free, anonymous helpline:
  **0800 137 27 00** · [check-dein-spiel.de](https://www.check-dein-spiel.de/)
- **International (English)** — [GamCare](https://www.gamcare.org.uk/) ·
  [BeGambleAware](https://www.begambleaware.org/) ·
  [Gamblers Anonymous](https://www.gamblersanonymous.org/)

If betting stops feeling like a hobby and starts feeling like a need, please reach
out to one of the services above.

---

## What it does

Given historical data and a set of draw-rate thresholds, the script:

1. **Downloads** results + closing odds for the leagues/seasons you pick (cached
   locally so it only downloads once).
2. Computes each team's **rolling 6-month draw rate** *before* each match — no
   look-ahead bias.
3. **Filters** matches where the two teams' average draw rate clears a threshold
   (40/45/50%, configurable), keeping only the higher-rated fixture when two
   candidates kick off at the same time.
4. **Simulates** three staking systems walk-forward on real closing odds:
   - `flat` — constant €1 stake (the honest baseline)
   - `recovery` — martingale sized to recover accumulated losses + a profit target
   - `double` — classic doubling (1-2-4-8-…)
5. Runs a **market-efficiency diagnostic**: the actual draw rate vs. the market's
   implied probability, plus Bet365's computed margin (overround).
6. Finds **upcoming candidate fixtures** from `fixtures.csv` and computes the stake
   each system would require.
7. Writes a self-contained **`dashboard.html`** you can open in any browser.

## Key finding

Across ~15,000 matches from Europe's top and second divisions, the market is
efficient: Bet365's margin is ~6%, and its de-vigged implied draw probability sits
within a fraction of a percent of the actual draw rate. Any apparent profit in the
filtered buckets comes from **match selection**, not from the staking system — and
flat betting captures it with a fraction of the drawdown and **zero bust risk**.
The martingale adds only risk. The small edge that does appear is on small samples
with selection bias and has not been validated out-of-sample.

In short: the data says what betting math always says. This repo just lets you see
it for yourself.

## Install

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## Usage

```bash
# default run: European top + second divisions, 5 seasons, thresholds 35/40/45/50
python martingale_backtest.py

# customise
python martingale_backtest.py --thresholds 35 40 45 50 --targets 1 5 10 20 25
python martingale_backtest.py --leagues I2 SP2 F2 I1 --seasons 2324 2425 2526
python martingale_backtest.py --mode flat
python martingale_backtest.py --list-leagues
```

Outputs: `backtest_results.csv` and `dashboard.html` in the working directory.

`dashboard_template.py` must sit next to `martingale_backtest.py` — the main script
imports the HTML template from it.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--leagues` | SP2 I2 F2 I1 F1 G1 D2 E1 | league codes (see `--list-leagues`) |
| `--seasons` | 2122 … 2526 | seasons, football-data.co.uk format |
| `--thresholds` | 35 40 45 50 | draw-rate cutoffs (%) |
| `--targets` | 1 5 10 20 25 | recovery profit targets (€) |
| `--mode` | both | `flat`, `recovery`, `double`, or `both` |
| `--max-steps` | 10 | consecutive losses before a bust |

## How to read the results

- `real_draw_%` vs `avg_odds` — the actual draw rate against the market's implied
  probability (≈ `1/avg_odds`). This is where a real edge would show up.
- `busts` — how many times a 10-loss streak blew up. This is the real risk.
- `flat` vs `recovery`/`double` — compare profit against `max_drawdown` and
  `capital_needed`. Similar profit with far less drawdown means the staking system
  is adding risk, not return.

## Optional: Argentina & Brazil upcoming games

football-data.co.uk's fixtures feed does not cover the extra leagues, so upcoming
Argentina and Brazil matches (with draw odds) come from [The Odds API](https://the-odds-api.com)
instead. It is free (500 requests/month, no credit card) and the script uses only
~2 requests per run.

1. Get a free key at https://the-odds-api.com (email only).
2. Paste it into the `set "ODDS_API_KEY="` line in `run.bat`, or set it as an
   environment variable named `ODDS_API_KEY`.
3. Run as usual. Without a key, everything else works; only the Argentina/Brazil
   upcoming picks are skipped.

## Data & attribution

Bet365 and other bookmaker names are trademarks of their respective owners. This is an independent research project, not affiliated with or endorsed by any bookmaker or data provider. Odds figures are computed from publicly available data for analysis only.


Match data and odds belong to [football-data.co.uk](https://www.football-data.co.uk/)
and its providers. This project does not redistribute their data; the CSVs are
downloaded at runtime by the end user and are git-ignored. Please respect their
terms of use.

## License

MIT — see [LICENSE](LICENSE). Covers the source code only, not the data.
