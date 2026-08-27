"""The symphony portfolio page: all streams combined on the common window,
plus the single-strategy curves the user asked for. Data: results/r28d_symphony.json."""
import json

D = json.load(open("results/r28d_symphony.json"))
cur = D["curves"]
dates = cur["dates"]
SERIES = [("always", "always-invested", "s1"),
          ("gold100", "100% gold", "s2"),
          ("opt2x", "mix 2x", "s3"),
          ("spx", "S&amp;P B&amp;H", "s4"),
          ("d7100", "100% D7", "s5")]

W, H, ML, MR, MT, MB = 860, 400, 46, 128, 16, 30
allv = [v for k, _, _ in SERIES for v in cur[k]]
lo, hi = min(allv) * 0.97, max(allv) * 1.03
def X(i): return ML + (W - ML - MR) * i / (len(dates) - 1)
def Y(v): return MT + (H - MT - MB) * (1 - (v - lo) / (hi - lo))
def path(vals): return "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
grid = ""
for g in (1.0, 1.5, 2.0, 2.5):
    if lo <= g <= hi:
        grid += (f'<line x1="{ML}" x2="{W-MR}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" class="grid"/>'
                 f'<text x="{ML-8}" y="{Y(g)+4:.1f}" class="ax" text-anchor="end">{g:g}x</text>')
ticks = ""
for i, dt in enumerate(dates):
    if dt[5:7] == "01" and dt[8:10] <= "07":
        ticks += f'<text x="{X(i):.1f}" y="{H-8}" class="ax" text-anchor="middle">{dt[:4]}</text>'
paths, endlabs = "", ""
used_y = []
for k, name, cls in SERIES:
    paths += f'<path d="{path(cur[k])}" class="ln {cls}"/>'
    y = Y(cur[k][-1])
    while any(abs(y - u) < 13 for u in used_y):
        y += 13
    used_y.append(y)
    endlabs += f'<text x="{W-MR+8}" y="{y+4:.1f}" class="endlab t-{cls}">{name} {cur[k][-1]:.2f}x</text>'

CH = f"""<figure><div class="chart" id="chartbox">
<svg viewBox="0 0 {W} {H}" role="img" aria-label="Growth of $1, Nov 2020 to Aug 2025: portfolio variants vs single strategies vs the S&P">
{grid}{ticks}{paths}{endlabs}
<line id="xh" x1="0" x2="0" y1="{MT}" y2="{H-MB}" class="xhair" visibility="hidden"/>
<rect id="hit" x="{ML}" y="{MT}" width="{W-ML-MR}" height="{H-MT-MB}" fill="transparent"/>
</svg><div id="tip" class="tip" hidden></div></div>
<figcaption>Growth of $1, weekly sampled, net of costs, common window Nov 2020 &ndash;
Aug 2025 (the span where every stream has data; MHI's feed starts 2022-07 and its
sleeve sits in cash before that). The unlevered optimal mix is in the table below;
it is omitted from the chart for legibility.</figcaption></figure>
<script>
(function(){{
  var dates={json.dumps(dates)};
  var S={json.dumps({k: cur[k] for k, _, _ in SERIES})};
  var names={json.dumps({k: n for k, n, _ in SERIES})};
  var cls={json.dumps({k: c for k, _, c in SERIES})};
  var order={json.dumps([k for k, _, _ in SERIES])};
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
    var html='<b>'+dates[i]+'</b>';
    order.forEach(function(k){{
      html+='<br><span class="d d-'+cls[k]+'"></span> '+names[k]+' '+S[k][i].toFixed(2)+'x';
    }});
    tip.innerHTML=html; tip.hidden=false;
    var bx=box.getBoundingClientRect();
    var px=(x/Wv)*r.width+(r.left-bx.left);
    tip.style.left=Math.min(Math.max(px+12,4),bx.width-190)+'px'; tip.style.top='16px';
  }}
  function hide(){{xh.setAttribute('visibility','hidden');tip.hidden=true;}}
  hit.addEventListener('mousemove',show); hit.addEventListener('mouseleave',hide);
  hit.addEventListener('touchstart',function(e){{show(e.touches[0]);}},{{passive:true}});
  hit.addEventListener('touchmove',function(e){{show(e.touches[0]);}},{{passive:true}});
}})();
</script>"""

def row(key):
    s = D[key]
    return (f"<tr><td class=\"lbl\">{s['label']}</td><td class=\"r\">{s['final']:.2f}x</td>"
            f"<td class=\"r\">{s['cagr']*100:+.1f}%</td><td class=\"r\">{s['max_dd']*100:.1f}%</td>"
            f"<td class=\"r\">{s['vol']*100:.1f}%</td><td class=\"r\">{s['sharpe']:.2f}</td>"
            f"<td class=\"r\">{s['mar']:.2f}</td></tr>")

w = D["weights_opt"]
cm = D["sleeve_corr"]

HTML = f"""<title>The Symphony Portfolio</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{ --ground:#FBFBFC; --surface:#FFFFFF; --sunk:#F3F4F7; --ink:#16191F;
  --ink-2:#4A515E; --ink-3:#7C8496; --rule:#DFE2E9; --brass:#8A6420;
  --pos:#1B6E55; --neg:#A83226;
  --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100; --c5:#e87ba4; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ground:#0E1116; --surface:#161A21; --sunk:#1B2029; --ink:#E8EAEF;
  --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --neg:#E58275;
  --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181; }} }}
:root[data-theme="dark"] {{ --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
  --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --neg:#E58275;
  --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181; }}
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
.verdict {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--brass);
  border-radius:6px; padding:16px 20px; margin:20px 0; }}
.verdict p {{ margin:6px 0; }}
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
figure {{ margin:22px 0; }}
figcaption {{ font-size:13px; color:var(--ink-3); margin-top:10px; max-width:70ch; }}
.chart {{ position:relative; background:var(--surface); border:1px solid var(--rule);
  border-radius:6px; padding:14px 8px 6px; overflow-x:auto; }}
svg {{ display:block; max-width:100%; height:auto; }}
.grid {{ stroke:var(--rule); stroke-width:1; }}
.ax {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; fill:var(--ink-3); }}
.ln {{ fill:none; stroke-width:2; }}
.s1 {{ stroke:var(--c1); }} .s2 {{ stroke:var(--c2); }} .s3 {{ stroke:var(--c3); }}
.s4 {{ stroke:var(--c4); }} .s5 {{ stroke:var(--c5); }}
.endlab {{ font-family:"IBM Plex Mono",monospace; font-size:11px; }}
.t-s1 {{ fill:var(--c1); }} .t-s2 {{ fill:var(--c2); }} .t-s3 {{ fill:var(--c3); }}
.t-s4 {{ fill:var(--c4); }} .t-s5 {{ fill:var(--c5); }}
.xhair {{ stroke:var(--ink-3); stroke-width:1; stroke-dasharray:3 3; }}
.tip {{ position:absolute; background:var(--surface); border:1px solid var(--rule);
  border-radius:6px; padding:8px 10px; font-family:"IBM Plex Mono",monospace;
  font-size:12px; color:var(--ink-2); pointer-events:none; line-height:1.55;
  box-shadow:0 2px 8px rgba(0,0,0,.12); }}
.tip b {{ color:var(--ink); }}
.d {{ display:inline-block; width:10px; height:3px; border-radius:2px; vertical-align:middle; }}
.d-s1 {{ background:var(--c1); }} .d-s2 {{ background:var(--c2); }} .d-s3 {{ background:var(--c3); }}
.d-s4 {{ background:var(--c4); }} .d-s5 {{ background:var(--c5); }}
footer {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--rule);
  font-size:13px; color:var(--ink-3); max-width:72ch; }}
ul {{ padding-left:20px; }}
code {{ font-family:"IBM Plex Mono",monospace; font-size:.9em; background:var(--sunk);
  padding:1px 5px; border-radius:4px; }}
</style>
<div class="wrap">
<div class="kicker">the four streams together &middot; common window Nov 2020 &ndash; Aug 2025</div>
<h1>The Symphony Portfolio</h1>
<p>All the validated and watch-list streams run as one book: the deployed gold rule
(1% risk per trade), the Double Seven S&amp;P sleeve, and the HSI pre-open fade
(1% risk, capped at a 25% weight because it is an n=43 watch item). The headline
finding is the correlation matrix: <strong>the three sleeves are statistically
uncorrelated</strong> (gold&ndash;D7 0.00, gold&ndash;MHI &minus;0.01, D7&ndash;MHI
0.02) &mdash; they earn in different markets, different sessions, different
mechanisms. That is what makes a portfolio more than its parts.</p>

<h2><span class="n">01</span>The equity curves</h2>
{CH}

<h2><span class="n">02</span>The scoreboard</h2>
<div class="tblwrap"><table>
<thead><tr><th>Portfolio</th><th>Final</th><th>CAGR</th><th>Max DD</th><th>Vol</th><th>Sharpe</th><th>MAR</th></tr></thead>
<tbody>
{row("opt")}{row("opt2x")}{row("always")}{row("gold100")}{row("d7100")}{row("spx")}
</tbody></table></div>
<div class="verdict">
<p><strong>How to read it.</strong> The in-sample optimal split is
<strong>gold {w['gold']*100:.0f}% / D7 {w['d7']*100:.0f}% / MHI {w['mhi']*100:.0f}%</strong>
&mdash; the optimizer loads the low-volatility sleeves, which is why the unlevered
mix &ldquo;only&rdquo; earns 9%: it also only draws down 5.8%. Because Sharpe
survives leverage, the same mix at 2&times; earns 18.4% at an 11.4% drawdown
&mdash; nearly the gold strategy&rsquo;s return at two-thirds of its drawdown, and
a higher Sharpe (1.38) than anything else on the page. The
<strong>always-invested</strong> variant answers the near-100%-exposure question:
100% S&amp;P buy-and-hold as the base with the strategy mix running on margin on
top &mdash; 22.8%/yr vs the index&rsquo;s 13.0% at the SAME ~22% drawdown. Every
variant beats holding the index on risk-adjusted terms; which one fits is a
temperament choice, not a math one.</p></div>

<h2><span class="n">03</span>The honest caveats</h2>
<ul>
<li><strong>The weights are in-sample.</strong> The 20/55/25 split was chosen by
looking at this exact window; treat it as a shape (&ldquo;diversify, cap the
watch item&rdquo;), not a precision dial. With near-zero correlations, any
reasonable split captures most of the benefit.</li>
<li><strong>The window is friendly to every sleeve.</strong> 2020&ndash;2025 is
gold&rsquo;s strong era, a mostly-rising S&amp;P (D7's PF 2.28 half), and MHI's
only era. The dossier's 20-year D7 curve and the gold rule's era split
(+12.8%/yr planning number) are the sobriety checks.</li>
<li><strong>MHI is a watch item</strong> (43 trades, frozen params, promotion bar
at 80) &mdash; its 25% cap is a discipline, and its live weight today should be
paper-only regardless.</li>
<li><strong>The gold sleeve is modeled single-leg.</strong> The deployed
dual-denominator split (half XAUUSD, half XAUAUD) further stabilizes it (era-
invariant Sharpe ~2.2 in round 18) &mdash; the real sleeve is slightly better
than shown.</li>
<li><strong>Leverage and the always-invested base assume margin instruments</strong>
(CFD/futures) where the strategy sleeves consume little cash; CFD swap on D7's
multi-day holds is not modeled.</li>
</ul>
<footer>Round 28d &middot; <code>run_r28d_symphony.py</code> &rarr;
<code>results/r28d_symphony.json</code> &middot; sleeves: deployed gold trade set
(1% risk), Double Seven SPX daily (frozen 7/200), HSI fade regenerated at frozen
0.3/0.5 params &middot; daily-rebalanced weighted returns, net of each stream's
modeled costs &middot; nothing here changes the paper-first posture: the symphony
trades on paper until the SPRT boundaries promote its parts.</footer>
</div>
"""
open("results/report_symphony.html", "w").write(HTML)
print("results/report_symphony.html written,", len(HTML), "bytes")
