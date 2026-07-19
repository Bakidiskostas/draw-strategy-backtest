# -*- coding: utf-8 -*-
"""HTML template for the dashboard. The /*__DATA__*/null token is replaced with JSON."""

DASHBOARD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Draw Ledger — Draw Betting Analysis</title>
<meta name="theme-color" content="#10141b">
<link rel="icon" href="__ICON_SRC__">
<link rel="apple-touch-icon" href="__ICON_SRC__">
<link rel="manifest" href="site.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Draw Ledger">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#10141b; --panel:#171d26; --row:#1e2530; --line:#2a323e;
  --ink:#e8ecf3; --mute:#8b95a7; --dim:#5f6b7d;
  --signal:#57d0a3; --risk:#e56a63; --warn:#e0a962; --info:#6ea8fe;
  --accent:#57d0a3;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:'Inter',system-ui,sans-serif;line-height:1.5;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:'Space Grotesk',sans-serif;font-weight:600;
  letter-spacing:-.01em;margin:0}
.mono{font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums}
.banner-wrap{width:100%;line-height:0;border-bottom:1px solid var(--line)}
.banner-wrap svg{width:100%;height:auto;display:block}
header{border-bottom:1px solid var(--line);padding:30px 0 26px;
  background:linear-gradient(180deg,#141a23,transparent)}
.brand{display:flex;align-items:center;gap:14px;margin-bottom:2px}
.logo{width:46px;height:46px;border-radius:11px;border:1px solid var(--line)}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:11px;
  letter-spacing:.28em;text-transform:uppercase;color:var(--dim)}
h1{font-size:clamp(30px,5vw,46px);margin:8px 0 6px;font-weight:700}
.sub{color:var(--mute);font-size:14px;max-width:64ch}
.gen{color:var(--dim);font-size:12px;margin-top:10px}
.mono.gen{font-family:'JetBrains Mono',monospace}
.banner{background:rgba(229,106,99,.10);border:1px solid rgba(229,106,99,.35);
  border-radius:10px;padding:12px 16px;margin-top:18px;font-size:12.5px;
  color:#f0b7b3}
.banner b{color:var(--risk)}
section{padding:42px 0;border-bottom:1px solid var(--line)}
.sec-head{display:flex;align-items:baseline;gap:14px;margin-bottom:22px}
.sec-num{font-family:'JetBrains Mono',monospace;color:var(--accent);
  font-size:13px;font-weight:500}
.sec-head h2{font-size:22px}
.sec-desc{color:var(--mute);font-size:13.5px;margin:-12px 0 22px;max-width:74ch}
.gauge{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:28px 30px 34px}
.gauge-cap{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;
  color:var(--mute);font-size:12.5px;margin-bottom:26px}
.axis{position:relative;height:74px;margin:8px 6px 0}
.axis-line{position:absolute;top:52px;left:0;right:0;height:2px;background:var(--line)}
.tick{position:absolute;top:44px;width:1px;height:18px;background:var(--line)}
.tick span{position:absolute;top:22px;left:50%;transform:translateX(-50%);
  font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--dim)}
.mark{position:absolute;top:0;transform:translateX(-50%);text-align:center;width:110px}
.mark .dot{width:11px;height:11px;border-radius:50%;margin:38px auto 0;
  position:relative;z-index:2}
.mark .lbl{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;
  margin-bottom:2px}
.mark .cap{font-size:10.5px;color:var(--mute);line-height:1.3}
.vig-band{position:absolute;top:50px;height:6px;border-radius:3px;
  background:linear-gradient(90deg,var(--warn),transparent);opacity:.5}
.legend{display:flex;gap:22px;flex-wrap:wrap;margin-top:30px;font-size:12px;color:var(--mute)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.swatch{width:10px;height:10px;border-radius:50%}
.verdict{margin-top:24px;padding:16px 18px;background:var(--row);
  border-left:3px solid var(--signal);border-radius:0 8px 8px 0;
  font-size:13.5px;color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:12px;overflow:hidden;margin-top:18px}
.stat{background:var(--panel);padding:18px 20px}
.stat .k{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.08em}
.stat .v{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;margin-top:6px}
.stat .n{font-size:11px;color:var(--mute);margin-top:3px}
.next-card{background:var(--panel);border:1px solid var(--accent);
  border-radius:14px;padding:26px 28px;position:relative;overflow:hidden}
.next-card::before{content:"NEXT CANDIDATE";position:absolute;top:16px;right:20px;
  font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.2em;
  color:var(--accent);opacity:.7}
.match{font-size:24px;font-weight:600;font-family:'Space Grotesk',sans-serif}
.match .vs{color:var(--dim);margin:0 10px;font-weight:400}
.meta{color:var(--mute);font-size:13px;margin-top:6px}
.meta .mono{color:var(--ink)}
.rates{display:flex;gap:26px;margin-top:18px;flex-wrap:wrap}
.rate .k{font-size:11px;color:var(--dim);text-transform:uppercase}
.rate .v{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;margin-top:2px}
.big-odds{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:var(--accent)}
.calc{background:var(--row);border:1px solid var(--line);border-radius:12px;
  padding:22px 24px;margin-top:20px}
.calc h3{font-size:15px;margin-bottom:4px}
.calc .hint{color:var(--mute);font-size:12.5px;margin-bottom:16px}
.calc-inputs{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-end;margin-bottom:18px}
.field label{display:block;font-size:11px;color:var(--dim);text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:6px}
.field input{background:var(--bg);border:1px solid var(--line);color:var(--ink);
  font-family:'JetBrains Mono',monospace;font-size:15px;padding:9px 12px;
  border-radius:8px;width:140px}
.field input:focus{outline:none;border-color:var(--accent)}
.stake-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px}
.stake{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stake .mode{font-size:11px;color:var(--mute);text-transform:uppercase;letter-spacing:.05em}
.stake .amt{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;margin-top:5px}
.stake.dbl{border-color:var(--risk)}
.stake.dbl .amt{color:var(--risk)}
.stake.rec .amt{color:var(--ink)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:10.5px;
  text-transform:uppercase;letter-spacing:.08em;color:var(--dim);
  padding:10px 12px;border-bottom:1px solid var(--line);font-weight:500}
td{padding:11px 12px;border-bottom:1px solid var(--row)}
tbody tr:hover{background:var(--row)}
td.mono{font-family:'JetBrains Mono',monospace}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;
  font-family:'JetBrains Mono',monospace;font-weight:500}
.pill.hi{background:rgba(87,208,163,.14);color:var(--signal)}
.pill.mid{background:rgba(224,169,98,.14);color:var(--warn)}
.reality{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:26px 30px}
.reality h3{font-size:16px;margin-bottom:14px;color:var(--warn)}
.reality ul{margin:0;padding-left:0;list-style:none}
.reality li{padding:10px 0 10px 26px;position:relative;font-size:13.5px;
  color:var(--ink);border-bottom:1px solid var(--row)}
.reality li:last-child{border-bottom:none}
.reality li::before{content:"->";position:absolute;left:0;color:var(--warn);
  font-family:'JetBrains Mono',monospace}
.reality b{color:var(--signal);font-weight:600}
.reality .bad{color:var(--risk);font-weight:600}
.lg-filter{display:flex;align-items:center;gap:10px;margin:0 0 14px}
.lg-filter label{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
.lg-filter select{background:var(--bg);border:1px solid var(--line);color:var(--ink);
  font-family:'JetBrains Mono',monospace;font-size:13px;padding:8px 12px;border-radius:8px}
.lg-filter select:focus{outline:none;border-color:var(--accent)}
.seg{display:inline-flex;gap:0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{background:var(--bg);color:var(--mute);border:none;
  font-family:'JetBrains Mono',monospace;font-size:13px;padding:8px 14px;cursor:pointer;
  border-right:1px solid var(--line)}
.seg button:last-child{border-right:none}
.seg button.on{background:var(--accent);color:#0c1016;font-weight:700}
.seg button:hover:not(.on){color:var(--ink)}
.filters{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-end;margin:0 0 16px}
.filters .grp{display:flex;flex-direction:column;gap:7px}
.filters label{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
.bar{height:7px;border-radius:4px;background:var(--accent);display:inline-block;
  vertical-align:middle;margin-left:8px;min-width:2px}
.bt-note{color:var(--mute);font-size:12.5px;margin-top:12px}
.neg{color:var(--risk)} .pos{color:var(--signal)}
tbody tr.clickable{cursor:pointer}
.modal-overlay{position:fixed;inset:0;background:rgba(8,11,16,.72);z-index:50;
  display:flex;align-items:center;justify-content:center;padding:20px}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  max-width:640px;width:100%;max-height:82vh;overflow:auto;padding:22px 24px}
.modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.modal-head h3{font-size:17px}
.modal-x{background:none;border:none;color:var(--mute);font-size:26px;cursor:pointer;line-height:1}
.modal-x:hover{color:var(--ink)}
.modal-sub{color:var(--mute);font-size:12.5px;margin:0 0 16px}
.runs-grid{display:flex;flex-wrap:wrap;gap:8px}
.run-chip{background:var(--row);border:1px solid var(--line);border-radius:8px;
  padding:8px 12px;font-family:'JetBrains Mono',monospace;font-size:13px;min-width:64px}
.run-chip .n{font-size:10px;color:var(--dim);text-transform:uppercase}
.run-chip .v{font-size:16px;font-weight:700;color:var(--signal)}
.run-chip.bust{border-color:var(--risk)}
.run-chip.bust .v{color:var(--risk)}
.runs-note{margin-top:16px;padding:12px 14px;background:var(--row);border-radius:8px;
  font-size:12.5px;color:var(--mute)}
.hist{display:flex;flex-direction:column;gap:6px}
.hist-row{display:grid;grid-template-columns:92px 1fr 46px;align-items:center;gap:10px}
.hist-k{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--mute)}
.hist-bar-wrap{background:var(--row);border-radius:5px;height:16px;overflow:hidden}
.hist-bar{height:100%;background:var(--accent);border-radius:5px;min-width:2px}
.hist-c{font-family:'JetBrains Mono',monospace;font-size:12px;text-align:right}
.follow-tbl{margin-top:10px;width:auto}
.follow-tbl td{padding:5px 16px 5px 0;border:none;font-size:12.5px}
.follow-tbl .bad{color:var(--risk)}
footer{padding:34px 0 60px;color:var(--dim);font-size:12px}
footer b{color:var(--mute)}
.empty{color:var(--mute);font-size:14px;padding:24px;background:var(--panel);
  border:1px dashed var(--line);border-radius:12px;text-align:center}
@media (max-width:640px){.axis{height:96px}.mark{width:82px}h1{font-size:30px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="banner-wrap">__BANNER__</div>
<header><div class="wrap">
  <div class="eyebrow">Draw Ledger · football-data.co.uk</div>
  <h1>Draw Betting Analysis</h1>
  <p class="sub">Market efficiency, edge, and staking risk for football draws —
     built on real closing odds, with nothing sugar-coated.</p>
  <div class="banner"><b>Not betting advice.</b> This is an analysis and education
     tool. Betting has a negative expected value and can be addictive. Never stake
     money you cannot afford to lose. See the footer for help resources.</div>
  <div class="gen mono" id="gen"></div>
</div></header>

<section id="market"><div class="wrap">
  <div class="sec-head"><span class="sec-num">01</span><h2>Is the market efficient?</h2></div>
  <p class="sec-desc">The fair odds come from the actual draw rate in the data. The
     market pays slightly less — the gap is the bookmaker's margin. If the two nearly
     coincide, the data is clean and there is no free money in the average price.</p>
  <div class="gauge">
    <div class="gauge-cap">
      <span>Axis: implied draw probability</span>
      <span id="gauge-range" class="mono"></span>
    </div>
    <div class="axis" id="axis"></div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--signal)"></i>Actual rate (data)</span>
      <span><i class="swatch" style="background:var(--info)"></i>Market price (median)</span>
      <span><i class="swatch" style="background:var(--warn)"></i>Bet365 margin</span>
    </div>
    <div class="verdict" id="verdict"></div>
  </div>
  <div class="stats" id="stats"></div>
</div></section>

<section id="next"><div class="wrap">
  <div class="sec-head"><span class="sec-num">02</span><h2>Upcoming candidate matches</h2></div>
  <p class="sec-desc">Upcoming fixtures where the two teams' average draw rate (last
     6 months) clears the threshold. The odds shown are the best available draw price
     on the market — what you would shop for if you actually bet.</p>
  <div id="next-slot"></div>
</div></section>

<section id="calc-sec"><div class="wrap">
  <div class="sec-head"><span class="sec-num">03</span><h2>Stake calculator</h2></div>
  <p class="sec-desc">For the next candidate. Change the current accumulated loss (if
     you are mid losing-streak) and the double step to see what each system demands.</p>
  <div id="calc-slot"></div>
</div></section>

<section id="reality"><div class="wrap">
  <div class="sec-head"><span class="sec-num">04</span><h2>Reality check</h2></div>
  <div class="reality"><h3>What the backtest shows</h3>
    <ul id="reality-list"></ul>
  </div>
</div></section>

<section id="leagues"><div class="wrap">
  <div class="sec-head"><span class="sec-num">05</span><h2>By league</h2></div>
  <p class="sec-desc">How many matches each league contributed, its overall draw rate,
     and how many cleared each threshold. This is where you see which leagues drive the
     draws — and where any edge would concentrate.</p>
  <div style="overflow-x:auto"><table id="lg"></table></div>
</div></section>

<section id="backtest"><div class="wrap">
  <div class="sec-head"><span class="sec-num">06</span><h2>Backtest by threshold</h2></div>
  <p class="sec-desc">Walk-forward on historical data. flat = constant €1. Bust@ is the
     losing-streak length that counts as a blow-up. P&amp;L/yr spreads the profit over the
     ~5-season span, which is the honest way to read it.</p>
  <div class="filters">
    <div class="grp"><label for="league-filter">League</label>
      <select id="league-filter"></select></div>
    <div class="grp"><label>Bust at</label>
      <div class="seg" id="bust-seg"></div></div>
    <div class="grp"><label>Withholding tax</label>
      <div class="seg" id="tax-seg">
        <button data-t="none" class="on">None</button>
        <button data-t="de">Germany 5.3%</button>
        <button data-t="gr">Greece tiered</button>
      </div></div>
  </div>
  <div style="overflow-x:auto"><table id="bt"></table></div>
  <p class="bt-note">busts = how many times a 10-loss streak blew up ·
     capital = the bankroll you would have needed to survive the worst stretch.</p>
</div></section>

<footer><div class="wrap">
  <p>Source: football-data.co.uk (free, public data). Analysis tool, not a
     recommendation. Gambling has a negative expected value — over time the house
     wins. Only ever stake what you can afford to lose.</p>
  <p style="margin-top:10px"><b>Need help?</b> Germany: BIÖG free & anonymous
     helpline 0800 137 27 00 · check-dein-spiel.de. International: gamcare.org.uk ·
     begambleaware.org · Gamblers Anonymous (gamblersanonymous.org).</p>
</div></footer>

<script>
const DATA = /*__DATA__*/null;
function fmt(n,d=2){return Number(n).toLocaleString('en-US',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function pctToX(p,lo,hi){return ((p-lo)/(hi-lo))*100;}

function renderGauge(){
  const d=DATA.diag;
  document.getElementById('gen').textContent =
    'Generated '+DATA.generated+' · '+d.matches.toLocaleString('en-US')+
    ' matches · '+d.date_from+' -> '+d.date_to+
    ((DATA.tax&&DATA.tax!=='none')?' · tax: '+DATA.tax:'');
  const real=d.draw_rate;
  const marketImpl=+(100/d.odds_median).toFixed(1);
  const devig=d.devig_draw;
  const vals=[real,marketImpl,devig||real].filter(Boolean);
  let lo=Math.floor(Math.min(...vals)-3), hi=Math.ceil(Math.max(...vals)+3);
  document.getElementById('gauge-range').textContent=lo+'% - '+hi+'%';
  const axis=document.getElementById('axis');
  axis.innerHTML='<div class="axis-line"></div>';
  for(let t=lo;t<=hi;t++){
    if(t%2)continue;
    const x=pctToX(t,lo,hi);
    axis.insertAdjacentHTML('beforeend',
      `<div class="tick" style="left:${x}%"><span>${t}%</span></div>`);
  }
  if(d.devig_draw){
    const a=pctToX(Math.min(devig,marketImpl),lo,hi);
    const b=pctToX(Math.max(devig,marketImpl),lo,hi);
    axis.insertAdjacentHTML('beforeend',
      `<div class="vig-band" style="left:${a}%;width:${b-a}%"></div>`);
  }
  const marks=[
    {p:real,c:'var(--signal)',l:real+'%',cap:'actual'},
    {p:marketImpl,c:'var(--info)',l:marketImpl+'%',cap:'market (median '+d.odds_median+')'},
  ];
  marks.forEach(mk=>{
    const x=pctToX(mk.p,lo,hi);
    axis.insertAdjacentHTML('beforeend',
      `<div class="mark" style="left:${x}%">
         <div class="lbl" style="color:${mk.c}">${mk.l}</div>
         <div class="cap">${mk.cap}</div>
         <div class="dot" style="background:${mk.c}"></div></div>`);
  });
  const gap=(marketImpl-real).toFixed(1);
  let v;
  if(d.margin){
    v=`Bet365 margin <b>${d.margin}%</b>. The market prices the draw as
       <b>${marketImpl}%</b>, while in the data it happens <b>${real}%</b> of the time
       — a ${gap}-point gap, which is the bookmaker's cut. The odds are
       <b>lower</b> than fair (${d.fair_odds}), not high. The market is efficient;
       there is no gift in the average price.`;
  }else{
    v=`The market prices the draw as ${marketImpl}%, the actual rate is ${real}%.
       The odds reflect risk plus the bookmaker's margin.`;
  }
  document.getElementById('verdict').innerHTML=v;
}

function renderStats(){
  const d=DATA.diag;
  const cells=[
    ['Draw rate',d.draw_rate+'%','over '+d.matches.toLocaleString('en-US')+' matches'],
    ['Fair odds',d.fair_odds,'= 1 / rate'],
    ['Median odds',d.odds_median,'what the market pays'],
    ['Bet365 margin',(d.margin?d.margin+'%':'—'),'3-way overround'],
    ['Odds range',d.odds_min+'–'+d.odds_max,d.pct_below_3+'% below 3.00'],
  ];
  document.getElementById('stats').innerHTML=cells.map(c=>
    `<div class="stat"><div class="k">${c[0]}</div>
      <div class="v mono">${c[1]}</div><div class="n">${c[2]}</div></div>`).join('');
}

function bucketPill(r){const cls=r>=45?'hi':'mid';return `<span class="pill ${cls}">${r}%</span>`;}

function renderNext(){
  const c=DATA.candidates;
  const slot=document.getElementById('next-slot');
  if(!c.length){
    slot.innerHTML='<div class="empty">No upcoming candidate right now. Two reasons: most European leagues are on '+
      'their summer break, and the extra leagues (Argentina, Brazil) are not part of '+
      'the upcoming-fixtures odds feed. This fills in once the European season starts.</div>';
    return;
  }
  const n=c[0];
  slot.innerHTML=`<div class="next-card">
    <div class="match">${n.home}<span class="vs">×</span>${n.away}</div>
    <div class="meta"><span class="mono">${n.date} ${n.time}</span> · ${n.league}</div>
    <div class="rates">
      <div class="rate"><div class="k">${n.home}</div><div class="v">${n.home_rate}%</div></div>
      <div class="rate"><div class="k">${n.away}</div><div class="v">${n.away_rate}%</div></div>
      <div class="rate"><div class="k">Average</div><div class="v" style="color:var(--signal)">${n.pair_rate}%</div></div>
      <div class="rate"><div class="k">Best draw odds</div><div class="v big-odds">${n.best_odds}</div><div class="k" style="margin-top:2px">${n.odds_src}</div></div>
    </div></div>`;
  if(c.length>1){
    let rows=c.slice(1).map(x=>`<tr>
      <td class="mono">${x.date} ${x.time}</td>
      <td>${x.home} × ${x.away}</td>
      <td>${x.league}</td>
      <td>${bucketPill(x.pair_rate)}</td>
      <td class="mono">${x.best_odds}</td>
      <td>${x.odds_src}</td></tr>`).join('');
    slot.insertAdjacentHTML('beforeend',
      `<div style="overflow-x:auto;margin-top:22px"><table>
        <thead><tr><th>Date</th><th>Match</th><th>League</th>
        <th>Avg draw</th><th>Odds</th><th>Bookmaker</th></tr></thead>
        <tbody>${rows}</tbody></table></div>`);
  }
}

function renderCalc(){
  const slot=document.getElementById('calc-slot');
  if(!DATA.candidates.length){
    slot.innerHTML='<div class="empty">The calculator activates once there is an '+
      'upcoming candidate. It stakes for recovery targets '+
      DATA.targets.join(', ')+'€ plus the double sequence.</div>';
    return;
  }
  const n=DATA.candidates[0];
  slot.innerHTML=`<div class="calc">
    <h3>Next: ${n.home} × ${n.away}</h3>
    <div class="hint">Best market draw odds found: <b>${n.best_odds}</b> (${n.odds_src}).
      You may not get that exact price — set the odds you can actually bet below.
      Recovery recovers the accumulated loss plus the target in one win; double just doubles.</div>
    <div class="calc-inputs">
      <div class="field"><label>Draw odds</label>
        <input id="odds" type="number" value="${n.best_odds}" min="1.01" step="0.01"></div>
      <div class="field"><label>Accumulated loss €</label>
        <input id="cum" type="number" value="0" min="0" step="1"></div>
      <div class="field"><label>Double step (0=first)</label>
        <input id="step" type="number" value="0" min="0" max="12" step="1"></div>
    </div>
    <div class="stake-grid" id="stakes"></div>
  </div>`;
  const recalc=()=>{
    let o=parseFloat(document.getElementById('odds').value);
    if(!(o>1)){o=n.best_odds;}
    const cum=Math.max(0,+document.getElementById('cum').value||0);
    const step=Math.max(0,+document.getElementById('step').value||0);
    let cells=DATA.targets.map(t=>{
      const s=Math.ceil(((cum+t)/(o-1))*100)/100;
      return `<div class="stake rec"><div class="mode">Recovery €${t}</div>
        <div class="amt">€${fmt(s)}</div></div>`;
    });
    const dbl=Math.pow(2,step);
    const worst=Math.pow(2,10)-1;
    cells.push(`<div class="stake dbl"><div class="mode">Double (step ${step})</div>
      <div class="amt">€${fmt(dbl,0)}</div>
      <div class="mode" style="margin-top:6px">worst case: €${worst}</div></div>`);
    document.getElementById('stakes').innerHTML=cells.join('');
  };
  document.getElementById('odds').addEventListener('input',recalc);
  document.getElementById('cum').addEventListener('input',recalc);
  document.getElementById('step').addEventListener('input',recalc);
  recalc();
}

function renderReality(){
  const bt=DATA.backtest;
  const flat=bt.find(r=>r.mode=='flat'&&r['threshold_%']==40&&r.bust_at==10)
        || bt.find(r=>r.mode=='flat');
  const rec=bt.find(r=>r.mode=='recovery'&&r['threshold_%']==40&&r['target_€']==5&&r.bust_at==10)
        || bt.find(r=>r.mode=='recovery');
  const dbl=bt.find(r=>r.mode=='double'&&r['threshold_%']==40&&r.bust_at==10)
        || bt.find(r=>r.mode=='double');
  const items=[];
  if(flat&&rec){
    items.push(`At the ${flat['threshold_%']}% threshold, <b>flat</b> returned
      €${fmt(flat.final_pnl)} with max drawdown €${fmt(flat.max_drawdown)};
      recovery (€${rec['target_€']} target) returned €${fmt(rec.final_pnl)} with drawdown
      €${fmt(rec.max_drawdown)}. Similar profit — the martingale only adds risk.`);
  }
  if(dbl){
    items.push(`<span class="bad">Double</span> at ${dbl['threshold_%']}% reached a
      max stake of €${fmt(dbl.max_stake,0)} and a worst streak of
      <span class="bad">€${fmt(dbl.worst_bust_loss)}</span>. One bust erases dozens of wins.`);
  }
  items.push(`Any edge lives in <b>match selection</b>, not in staking. If it is real,
    flat betting captures it without bust risk.`);
  items.push(`The edge in the filtered buckets is small, on small samples, and carries
    selection bias. It needs out-of-sample validation before you trust it.`);
  document.getElementById('reality-list').innerHTML=
    items.map(i=>`<li>${i}</li>`).join('');
}

function renderLeagues(){
  const lg=DATA.leagues||[];
  const el=document.getElementById('lg');
  if(!lg.length){el.parentElement.innerHTML='<div class="empty">No per-league breakdown available.</div>';return;}
  const thrs=Object.keys(lg[0]).filter(k=>k.startsWith('cand_')).map(k=>k.slice(5));
  const maxM=Math.max(...lg.map(r=>r.matches));
  let head='<thead><tr><th>League</th><th>Matches</th><th>Draw %</th>'+
    thrs.map(t=>`<th>Cand ${t}%</th>`).join('')+'</tr></thead>';
  let body='<tbody>'+lg.map(r=>{
    const w=Math.round((r.matches/maxM)*90)+8;
    return `<tr><td>${r.name}</td>
      <td class="mono">${r.matches.toLocaleString('en-US')}<span class="bar" style="width:${w}px"></span></td>
      <td class="mono">${r.draw_pct}%</td>`+
      thrs.map(t=>`<td class="mono">${r['cand_'+t]}</td>`).join('')+'</tr>';
  }).join('')+'</tbody>';
  el.innerHTML=head+body;
}

function renderBacktest(){
  const bt=DATA.backtest;
  const leagues=[...new Set(bt.map(r=>r.league))];
  const busts=[...new Set(bt.map(r=>r.bust_at))].sort((a,b)=>a-b);
  const sel=document.getElementById('league-filter');
  const seg=document.getElementById('bust-seg');
  const nameOf=code=>{
    if(code==='ALL')return 'All leagues (combined)';
    const l=(DATA.leagues||[]).find(x=>x.code===code);
    return l?l.name:code;
  };
  sel.innerHTML=leagues.map(c=>`<option value="${c}">${nameOf(c)}</option>`).join('');
  // default bust = 10 if present, else the middle value
  let curBust = busts.includes(10) ? 10 : busts[Math.floor(busts.length/2)];
  let curTax = 'none';
  const taxSeg=document.getElementById('tax-seg');
  seg.innerHTML=busts.map(b=>`<button data-b="${b}">${b}</button>`).join('');
  const cols=[['threshold_%','Threshold'],['mode','Mode'],['target_€','Target'],
    ['matches','Matches'],['real_draw_%','Real %'],['avg_odds','Avg odds'],
    ['cycles_won','Wins'],['busts','Busts'],['avg_bust_loss','Avg bust €'],
    ['final_pnl','P&L €'],['pnl_per_year','P&L/yr €'],['total_staked','Staked €'],['tax_paid','Tax €'],
    ['capital_needed','Capital €'],['roc','P&L/Cap'],['min_bankroll','Min bal €'],
    ['worst_streak','Worst run'],['worst_streak_capital','Follow €'],
    ['max_stake','Max stake']];
  const draw=()=>{
    seg.querySelectorAll('button').forEach(b=>
      b.classList.toggle('on', +b.dataset.b===curBust));
    taxSeg.querySelectorAll('button').forEach(b=>
      b.classList.toggle('on', b.dataset.t===curTax));
    const pick=sel.value;
    const data=bt.filter(r=>r.league===pick && r.bust_at===curBust)
      .map(r=>{const tv=(r.taxv&&r.taxv[curTax])?r.taxv[curTax]:{}; return {...r,...tv};});
    let head='<thead><tr>'+cols.map(c=>`<th>${c[1]}</th>`).join('')+'</tr></thead>';
    let body='<tbody>'+data.map(r=>{
      const tds=cols.map(c=>{
        let v=r[c[0]];let cls='mono';
        if(c[0]=='final_pnl'||c[0]=='pnl_per_year'||c[0]=='roc')cls+=((typeof v==='number'&&v<0)?' neg':' pos');
        if(c[0]=='min_bankroll'&&typeof v==='number'&&v<0)cls+=' neg';
        if(c[0]=='mode'||c[0]=='target_€')cls='';
        return `<td class="${cls}">${v}</td>`;
      }).join('');
      return `<tr class="clickable" data-skey="${r.league}|${r['threshold_%']}" data-thr="${r['threshold_%']}">${tds}</tr>`;
    }).join('')+'</tbody>';
    document.getElementById('bt').innerHTML=head+body;
    document.querySelectorAll('#bt tbody tr.clickable').forEach(tr=>{
      tr.addEventListener('click',()=>openStreaks(tr.dataset.skey,tr.dataset.thr,pick));
    });
  };
  sel.addEventListener('change',draw);
  seg.addEventListener('click',e=>{
    const b=e.target.closest('button'); if(!b)return;
    curBust=+b.dataset.b; draw();
  });
  taxSeg.addEventListener('click',e=>{
    const b=e.target.closest('button'); if(!b)return;
    curTax=b.dataset.t; draw();
  });
  draw();
}

function openStreaks(key,thr,league){
  const st=(DATA.streaks||{})[key];
  if(!st){return;}
  const dist=st.dist||{};
  const attempts=Object.keys(dist).map(Number).sort((a,b)=>a-b);
  if(!attempts.length){return;}
  const maxCount=Math.max(...attempts.map(k=>dist[k]));
  const totalDraws=attempts.reduce((s,k)=>s+dist[k],0);
  const lgName=(league==='ALL')?'All leagues':(((DATA.leagues||[]).find(x=>x.code===league)||{}).name||league);
  document.getElementById('runs-title').textContent='Draws by attempt — '+lgName;
  document.getElementById('runs-sub').textContent=
    `Threshold ${thr}% · ${totalDraws} draws · worst streak: ${st.worst} bets. `+
    `"Attempt k" = the draw finally came on the k-th bet (after k-1 straight non-draws).`;
  // histogram bars
  const bars=attempts.map(k=>{
    const c=dist[k];
    const w=Math.round((c/maxCount)*100);
    const worstTag=(k===st.worst)?' style="color:var(--risk);font-weight:700"':'';
    return `<div class="hist-row">
      <div class="hist-k"${worstTag}>Attempt ${k}</div>
      <div class="hist-bar-wrap"><div class="hist-bar" style="width:${w}%"></div></div>
      <div class="hist-c">${c}</div></div>`;
  }).join('');
  // capital to follow the worst streak, per recovery target + double
  const o=st.worst_odds||[];
  const rows=(DATA.targets||[]).map(t=>{
    let cum=0,tot=0;
    o.forEach(od=>{const s=Math.ceil(((cum+t)/(od-1))*100)/100;tot+=s;cum+=s;});
    return `<tr><td>Recovery €${t}</td><td class="mono">€${fmt(tot)}</td></tr>`;
  }).join('');
  const dblCost=Math.pow(2,o.length)-1;
  const flatCost=o.length;
  document.getElementById('runs-body').innerHTML=
    `<div class="hist">${bars}</div>`+
    `<div class="runs-note"><b>Worst case: ${st.worst} bets before a draw.</b> To follow that
      whole streak to its win, this is the total capital you must stake:
      <table class="follow-tbl"><tbody>
        <tr><td>Flat €1</td><td class="mono">€${fmt(flatCost,0)}</td></tr>
        ${rows}
        <tr><td class="bad">Double</td><td class="mono bad">€${fmt(dblCost,0)}</td></tr>
      </tbody></table>
      Uses the real odds of the ${st.worst} matches in that worst streak. This is the
      "follow it through, no bust cap" cost — the number that decides if you can survive it.</div>`;
  document.getElementById('runs-modal').style.display='flex';
}
function closeRuns(){document.getElementById('runs-modal').style.display='none';}

if(DATA){renderGauge();renderStats();renderNext();renderCalc();renderReality();renderLeagues();renderBacktest();document.addEventListener('click',e=>{if(e.target&&(e.target.id==='runs-close'||e.target.id==='runs-modal'))closeRuns();});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRuns();});}
else{document.body.insertAdjacentHTML('beforeend',
   '<div class="wrap"><p class="empty" style="margin:40px 0">No data found. '+
   'Run main.py first.</p></div>');}
</script>
<div id="runs-modal" class="modal-overlay" style="display:none">
  <div class="modal">
    <div class="modal-head">
      <h3 id="runs-title">Draws per run</h3>
      <button id="runs-close" class="modal-x">×</button>
    </div>
    <p class="modal-sub" id="runs-sub"></p>
    <div id="runs-body"></div>
  </div>
</div>
</body>
</html>"""
