"""The Double Seven dossier: stats, equity curves vs the S&P, the overlay
variant, ES/NQ futures costs. Data from results/r28b_d7.json (round 28b)."""
import json, math

D = json.load(open("results/r28b_d7.json"))
spx = D["SPX_cfd"]
cur = spx["curves"]
dates, sA, sB, sC = cur["dates"], cur["strategy"], cur["buyhold"], cur["overlay"]

# ---- chart geometry (log y) -------------------------------------------------
W, H, ML, MR, MT, MB = 860, 380, 46, 132, 16, 30
lo = math.log10(0.5)
hi = math.log10(max(sC) * 1.15)
def X(i): return ML + (W - ML - MR) * i / (len(dates) - 1)
def Y(v): return MT + (H - MT - MB) * (1 - (math.log10(max(v, 0.51)) - lo) / (hi - lo))
def path(vals): return "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
gridv = [0.5, 1, 2, 5, 10, 20]
grid = "".join(
    f'<line x1="{ML}" x2="{W-MR}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" class="grid"/>'
    f'<text x="{ML-8}" y="{Y(g)+4:.1f}" class="ax" text-anchor="end">{g}x</text>' for g in gridv)
years_ticks = ""
for i, dt in enumerate(dates):
    if dt.endswith("-12-31") and int(dt[:4]) % 5 == 0:
        years_ticks += f'<text x="{X(i):.1f}" y="{H-8}" class="ax" text-anchor="middle">{int(dt[:4])+1}</text>'
def endlab(vals, cls, name):
    return (f'<text x="{W-MR+8}" y="{Y(vals[-1])+4:.1f}" class="endlab {cls}">'
            f'{name} {vals[-1]:.1f}x</text>')
CH = f"""<figure><div class="chart" id="chartbox">
<svg viewBox="0 0 {W} {H}" role="img" aria-label="Growth of $1, 2005-2025, log scale: Double Seven strategy-only, S&P buy and hold, and the 2x overlay">
{grid}{years_ticks}
<path d="{path(sB)}" class="ln s2"/>
<path d="{path(sA)}" class="ln s1"/>
<path d="{path(sC)}" class="ln s3"/>
{endlab(sC, "t3", "overlay")}{endlab(sB, "t2", "buy &amp; hold")}{endlab(sA, "t1", "D7 only")}
<line id="xh" x1="0" x2="0" y1="{MT}" y2="{H-MB}" class="xhair" visibility="hidden"/>
<rect id="hit" x="{ML}" y="{MT}" width="{W-ML-MR}" height="{H-MT-MB}" fill="transparent"/>
</svg>
<div id="tip" class="tip" hidden></div></div>
<figcaption>Growth of $1 on the S&amp;P, 2005&ndash;2025, log scale, net of costs.
The strategy alone is in the market only 28% of the time; the overlay holds the
index always and doubles exposure while a Double Seven signal is open.</figcaption>
</figure>
<script>
(function(){{
  var dates={json.dumps(dates)}, A={json.dumps(sA)}, B={json.dumps(sB)}, C={json.dumps(sC)};
  var box=document.getElementById('chartbox'), svg=box.querySelector('svg'),
      hit=document.getElementById('hit'), xh=document.getElementById('xh'),
      tip=document.getElementById('tip');
  var ML={ML}, MR={MR}, Wv={W};
  function show(ev){{
    var r=svg.getBoundingClientRect();
    var fx=(ev.clientX-r.left)/r.width*Wv;
    var i=Math.round((fx-ML)/(Wv-ML-MR)*(dates.length-1));
    if(i<0||i>=dates.length){{hide();return;}}
    var x=ML+(Wv-ML-MR)*i/(dates.length-1);
    xh.setAttribute('x1',x); xh.setAttribute('x2',x); xh.setAttribute('visibility','visible');
    tip.hidden=false;
    tip.innerHTML='<b>'+dates[i].slice(0,7)+'</b><br>'+
      '<span class="d t3"></span> overlay '+C[i].toFixed(2)+'x<br>'+
      '<span class="d t2"></span> buy &amp; hold '+B[i].toFixed(2)+'x<br>'+
      '<span class="d t1"></span> D7 only '+A[i].toFixed(2)+'x';
    var bx=box.getBoundingClientRect();
    var px=(x/Wv)*r.width+(r.left-bx.left);
    tip.style.left=Math.min(Math.max(px+12,4),bx.width-170)+'px';
    tip.style.top='18px';
  }}
  function hide(){{xh.setAttribute('visibility','hidden');tip.hidden=true;}}
  hit.addEventListener('mousemove',show); hit.addEventListener('mouseleave',hide);
  hit.addEventListener('touchstart',function(e){{show(e.touches[0]);}},{{passive:true}});
  hit.addEventListener('touchmove',function(e){{show(e.touches[0]);}},{{passive:true}});
}})();
</script>"""

def strow(v, label):
    s = v[label]
    ex = f"{s.get('exposure', 1)*100:.0f}%" if "exposure" in s else "100%"
    return (f"<tr><td class=\"lbl\">{s['label']}</td><td class=\"r\">{s['final']:.2f}x</td>"
            f"<td class=\"r\">{s['cagr']*100:+.1f}%</td><td class=\"r\">{s['max_dd']*100:.1f}%</td>"
            f"<td class=\"r\">{s['sharpe']:.2f}</td><td class=\"r\">{s['mar']:.2f}</td>"
            f"<td class=\"r\">{ex}</td></tr>")

yr_rows = "".join(
    f"<tr><td class=\"lbl\">{y}</td><td class=\"r\">{v[0]:+.1f}%</td><td class=\"r\">{v[1]:+.1f}%</td>"
    f"<td class=\"r {'pos' if v[0] >= 0 else 'neg'}\">{'&#9679;' if v[0] >= v[1] else ''}</td></tr>"
    for y, v in spx["yearly"].items())

nq = D["NDX_fut_NQ"]
es = D["SPX_fut_ES"]

HTML = f"""<title>The Double Seven Dossier</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{ --ground:#FBFBFC; --surface:#FFFFFF; --sunk:#F3F4F7; --ink:#16191F;
  --ink-2:#4A515E; --ink-3:#7C8496; --rule:#DFE2E9; --brass:#8A6420;
  --pos:#1B6E55; --neg:#A83226;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ground:#0E1116; --surface:#161A21; --sunk:#1B2029; --ink:#E8EAEF;
  --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --neg:#E58275;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; }} }}
:root[data-theme="dark"] {{ --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
  --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --neg:#E58275; --s1:#3987e5; --s2:#d95926; --s3:#199e70; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.6; }}
.wrap {{ max-width:900px; margin:0 auto; padding:34px 20px 90px; }}
h1 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:32px; margin:0 0 4px; text-wrap:balance; }}
h2 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:21px; margin:38px 0 10px; }}
h2 .n {{ color:var(--brass); font-family:"IBM Plex Mono",monospace; font-size:13px;
  margin-right:10px; letter-spacing:.06em; }}
p, li {{ max-width:72ch; color:var(--ink-2); }}
p strong, li strong {{ color:var(--ink); }}
.kicker {{ font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--brass); margin-bottom:8px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); border-radius:6px; overflow:hidden; margin:20px 0; }}
.stat {{ background:var(--surface); padding:14px 16px; }}
.stat .k {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-3); }}
.stat .v {{ font-family:"IBM Plex Mono",monospace; font-size:22px; margin-top:4px;
  font-variant-numeric:tabular-nums; }}
.tblwrap {{ overflow-x:auto; border:1px solid var(--rule); border-radius:6px;
  background:var(--surface); margin:14px 0; }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.07em;
  text-transform:uppercase; color:var(--ink-3); text-align:right; padding:10px 12px;
  border-bottom:1px solid var(--rule); }}
th:first-child {{ text-align:left; }}
td {{ padding:9px 12px; border-bottom:1px solid var(--rule); }}
td.r {{ text-align:right; font-family:"IBM Plex Mono",monospace; white-space:nowrap;
  font-variant-numeric:tabular-nums; }}
td.lbl {{ color:var(--ink-2); }}
tr:last-child td {{ border-bottom:none; }}
.pos {{ color:var(--pos); }} .neg {{ color:var(--neg); }}
figure {{ margin:22px 0; }}
figcaption {{ font-size:13px; color:var(--ink-3); margin-top:10px; max-width:66ch; }}
.chart {{ position:relative; background:var(--surface); border:1px solid var(--rule);
  border-radius:6px; padding:14px 8px 6px; overflow-x:auto; }}
svg {{ display:block; max-width:100%; height:auto; }}
.grid {{ stroke:var(--rule); stroke-width:1; }}
.ax {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; fill:var(--ink-3); }}
.ln {{ fill:none; stroke-width:2; }}
.s1 {{ stroke:var(--s1); }} .s2 {{ stroke:var(--s2); }} .s3 {{ stroke:var(--s3); }}
.endlab {{ font-family:"IBM Plex Mono",monospace; font-size:11px; }}
.t1 {{ fill:var(--s1); color:var(--s1); }} .t2 {{ fill:var(--s2); color:var(--s2); }}
.t3 {{ fill:var(--s3); color:var(--s3); }}
.xhair {{ stroke:var(--ink-3); stroke-width:1; stroke-dasharray:3 3; }}
.tip {{ position:absolute; background:var(--surface); border:1px solid var(--rule);
  border-radius:6px; padding:8px 10px; font-family:"IBM Plex Mono",monospace;
  font-size:12px; color:var(--ink-2); pointer-events:none; line-height:1.5;
  box-shadow:0 2px 8px rgba(0,0,0,.12); }}
.tip b {{ color:var(--ink); }}
.d {{ display:inline-block; width:10px; height:3px; border-radius:2px; vertical-align:middle; }}
.d.t1 {{ background:var(--s1); }} .d.t2 {{ background:var(--s2); }} .d.t3 {{ background:var(--s3); }}
.verdict {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--brass);
  border-radius:6px; padding:16px 20px; margin:20px 0; }}
.verdict p {{ margin:6px 0; }}
footer {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--rule);
  font-size:13px; color:var(--ink-3); max-width:72ch; }}
ul {{ padding-left:20px; }}
code {{ font-family:"IBM Plex Mono",monospace; font-size:.9em; background:var(--sunk);
  padding:1px 5px; border-radius:4px; }}
</style>
<div class="wrap">
<div class="kicker">watch-list item 4 &middot; paper stream D7 &middot; round 28b deep-dive</div>
<h1>The Double Seven Dossier</h1>
<p>Connors &amp; Alvarez, 2008, replicated at frozen parameters on 20 years of our
S&amp;P data: close above the 200-day SMA, buy a 7-day closing low at the close,
exit at a 7-day closing high. Long only, no stop, as published. This page is the
full picture behind the fourth paper stream &mdash; the honest strengths, the
tail, and the two variants the strategy can be run as.</p>
<div class="stats">
<div class="stat"><div class="k">trades / win</div><div class="v">253 &middot; 80.2%</div></div>
<div class="stat"><div class="k">profit factor</div><div class="v pos">2.30</div></div>
<div class="stat"><div class="k">halves</div><div class="v">2.40 / 2.28</div></div>
<div class="stat"><div class="k">drift-null p</div><div class="v">0.005</div></div>
<div class="stat"><div class="k">signals / yr</div><div class="v">~13</div></div>
</div>

<h2><span class="n">01</span>Three ways to hold it, one chart</h2>
{CH}
<div class="tblwrap"><table>
<thead><tr><th>Variant (SPX, CFD costs)</th><th>Final</th><th>CAGR</th><th>Max DD</th><th>Sharpe</th><th>MAR</th><th>Exposure</th></tr></thead>
<tbody>
{strow(spx, "strategy")}
{strow(spx, "buyhold")}
{strow(spx, "overlay")}
</tbody></table></div>
<div class="verdict">
<p><strong>On your &ldquo;reinvest idle cash into the S&amp;P&rdquo; idea:</strong>
because the trades themselves are S&amp;P longs, parking flat cash in the S&amp;P
and then also taking the trades means you are simply always long &mdash; that IS
buy &amp; hold. The economically real version is the <strong>overlay</strong>:
hold the index as your base and go 2&times; while a signal is open. It earned
15.2%/yr vs 8.6% for buy &amp; hold &mdash; but look at the drawdown column: the
overlay inherits every index crash AND doubles into dips during them (D7 buys
weakness, and in 2008/2020 weakness kept falling). 60% drawdown is the price of
that extra return. The <strong>strategy-only</strong> version is the opposite
temperament: it gives up return (6.5%/yr) to cut the worst drawdown from 57% to
15% and carries the best risk-adjusted numbers (Sharpe 0.69, MAR 0.43) while
being in the market only 28% of the time &mdash; the other 72% of the capital is
free to fund the gold streams.</p></div>

<h2><span class="n">02</span>On ES and NQ futures</h2>
<p>Costs barely matter at a ~7-day hold, so the futures numbers are nearly
identical to CFD &mdash; the instrument choice is about swap and leverage, not
edge. The honest difference is between the two indices:</p>
<div class="tblwrap"><table>
<thead><tr><th>Market (futures costs)</th><th>n</th><th>Win</th><th>PF-side stats</th><th>Strategy CAGR</th><th>Strategy max DD</th><th>Worst trade</th><th>Worst open excursion</th></tr></thead>
<tbody>
<tr><td class="lbl">ES / S&amp;P (0.35 pt RT)</td><td class="r">{es['n']}</td><td class="r">{es['win']*100:.1f}%</td>
<td class="r">payoff {es['payoff']:.2f}</td><td class="r">{es['strategy']['cagr']*100:+.1f}%</td>
<td class="r">{es['strategy']['max_dd']*100:.1f}%</td><td class="r neg">{es['worst_trade_pct']:+.1f}%</td>
<td class="r neg">{es['worst_mae_pct']:.1f}%</td></tr>
<tr><td class="lbl">NQ / Nasdaq (0.75 pt RT)</td><td class="r">{nq['n']}</td><td class="r">{nq['win']*100:.1f}%</td>
<td class="r">payoff {nq['payoff']:.2f}</td><td class="r">{nq['strategy']['cagr']*100:+.1f}%</td>
<td class="r">{nq['strategy']['max_dd']*100:.1f}%</td><td class="r neg">{nq['worst_trade_pct']:+.1f}%</td>
<td class="r neg">{nq['worst_mae_pct']:.1f}%</td></tr>
</tbody></table></div>
<p><strong>The NQ tail is the warning label.</strong> The Nasdaq version's full-sample
numbers look richer, but its no-stop reality is brutal: the worst single trade lost
22.9% and the worst open position was down 37.7% before resolving &mdash; and its
drift-null pass was borderline (p&nbsp;=&nbsp;0.028 vs 0.005 on the S&amp;P). The
S&amp;P is where the effect is cleanest (worst trade &minus;7.4%, worst excursion
15%), which is why the paper stream is <strong>SPX only</strong>. If it is ever
funded, MES micro futures avoid the multi-day CFD swap drag that these numbers do
not model.</p>

<h2><span class="n">03</span>Year by year, strategy vs buy &amp; hold</h2>
<div class="tblwrap"><table>
<thead><tr><th>Year</th><th>D7 only</th><th>Buy &amp; hold</th><th>D7 ahead</th></tr></thead>
<tbody>{yr_rows}</tbody></table></div>
<p>The pattern to expect: the strategy lags in melt-up years (it is flat 72% of
the time) and earns its keep in rough ones &mdash; its edge is <em>when</em> it is
in the market, not how often. Judge it on drawdown-adjusted terms and on the SPRT
boundary, never on a bull-year comparison against buy &amp; hold.</p>

<h2><span class="n">04</span>The paper protocol</h2>
<ul>
<li><strong>Chart:</strong> S&amp;P 500 daily (SP:SPX or OANDA:SPX500USD) with the
<code>Double Seven [paper]</code> indicator from the paste board; alerts
<strong>D7 BUY</strong> and <strong>D7 EXIT</strong> fire at the close.</li>
<li><strong>Journal:</strong> log under the new <strong>D7</strong> chip; entry =
signal-day close, exit = exit-day close, stop = entry (there is none). Expect
roughly one signal a month and multi-day open losers &mdash; that is the design,
not a malfunction.</li>
<li><strong>Decision:</strong> the SPRT boundaries are frozen in
<code>sprt.py</code> (win 80.2% vs 63.7% null, payoff 0.57): median ~25 trades to
promote or ~22 to kill &mdash; about two years of signals. The monthly review
scores it automatically.</li>
<li><strong>Frozen:</strong> 7-day extremes, 200-day SMA, long only, no stop.
Nothing may be tuned before the boundary decides.</li>
</ul>
<footer>Round 28 replication + 28b deep-dive &middot; <code>run_r28_daily.py</code>,
<code>run_r28b_d7.py</code> &middot; drift null = matched-hold random longs above
the 200 SMA (3,000 sims) &middot; sub-strict-Bonferroni for its round, hence watch
list rather than deployment &middot; CFD swap on multi-day holds not modeled
(futures preferred if ever funded) &middot; data: SPX/NDX 5m feeds 2005&ndash;2025,
session-verified.</footer>
</div>
"""
open("results/report_d7.html", "w").write(HTML)
print("results/report_d7.html written,", len(HTML), "bytes")
