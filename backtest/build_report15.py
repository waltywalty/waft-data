"""Round 15 report: the researched battery (five families from five research agents)."""
import json

r = json.load(open("results/r15.json"))

def row(label, v):
    a = v["all"]
    return (f"<tr><td class='lbl'>{label}</td><td>{a['n']}</td>"
            f"<td>{a['mean_bps']:+.2f}</td><td>{a['t']:+.2f}</td>"
            f"<td>{v['h1']['t']:+.2f}</td><td>{v['h2']['t']:+.2f}</td></tr>")

f1_rows = "\n".join(row(k.replace("_", " "), v) for k, v in r["f1"].items()
                    if "vol" not in k or "hivol" in k)
f2_rows = "\n".join(row(k.replace("_", " "), v) for k, v in r["f2"].items())
f3_rows = "\n".join(
    f"<tr><td class='lbl'>{k.replace('_',' ')}</td><td>{v['n']}</td><td>{float(v['pf']):.3f}</td>"
    f"<td>{float(v['t']):+.2f}</td><td>{float(v['is_t']):+.2f}</td><td>{float(v['os_t']):+.2f}</td></tr>"
    for k, v in r["f3"].items())
f5_rows = ""
for mk, v in r["f5"].items():
    for b in ("small", "mid", "large"):
        if f"econ_{b}" in v:
            f5_rows += row(f"{mk} fade {b} gap (fill {v['fill_rate'][b]*100:.0f}%)", v[f"econ_{b}"]) + "\n"

sh = r["f4"]["share"]

HTML = f"""<title>The Researched Battery</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{ --ground:#FBFBFC; --surface:#FFFFFF; --sunk:#F3F4F7; --ink:#16191F;
  --ink-2:#4A515E; --ink-3:#7C8496; --rule:#DFE2E9; --brass:#8A6420;
  --pos:#1B6E55; --neg:#A83226; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ground:#0E1116; --surface:#161A21; --sunk:#1B2029; --ink:#E8EAEF;
  --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --neg:#E58275; }} }}
:root[data-theme="dark"] {{ --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
  --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38;
  --brass:#D5A64A; --pos:#5CBE99; --neg:#E58275; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.6; }}
.wrap {{ max-width:900px; margin:0 auto; padding:34px 20px 90px; }}
h1 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:32px; margin:0 0 4px; text-wrap:balance; }}
h2 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:22px; margin:40px 0 10px; }}
h2 .n {{ color:var(--brass); font-family:"IBM Plex Mono",monospace; font-size:14px;
  margin-right:10px; letter-spacing:.06em; }}
p {{ max-width:70ch; color:var(--ink-2); }}
p strong {{ color:var(--ink); }}
.kicker {{ font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--brass); margin-bottom:8px; }}
.verdict {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--brass);
  border-radius:6px; padding:16px 20px; margin:20px 0; }}
.verdict p {{ margin:6px 0; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); border-radius:6px; overflow:hidden; margin:18px 0; }}
.stat {{ background:var(--surface); padding:13px 15px; }}
.stat .k {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-3); }}
.stat .v {{ font-family:"IBM Plex Mono",monospace; font-size:21px; margin-top:4px;
  font-variant-numeric:tabular-nums; }}
.tblwrap {{ overflow-x:auto; border:1px solid var(--rule); border-radius:6px;
  background:var(--surface); margin:14px 0; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.07em;
  text-transform:uppercase; color:var(--ink-3); text-align:right; padding:10px 12px;
  border-bottom:1px solid var(--rule); white-space:nowrap; }}
th:first-child, td:first-child {{ text-align:left; }}
td {{ padding:7px 12px; border-bottom:1px solid var(--rule); text-align:right;
  font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.lbl {{ font-family:"IBM Plex Sans",sans-serif; color:var(--ink-2); white-space:normal; }}
tr:last-child td {{ border-bottom:none; }}
.note {{ font-size:13px; color:var(--ink-3); max-width:72ch; }}
footer {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--rule);
  font-size:13px; color:var(--ink-3); max-width:72ch; }}
</style>
<div class="wrap">
<div class="kicker">Asia-open gold &amp; index futures &middot; research round 15 &middot; August 2026</div>
<h1>Five literatures, thirty-eight cells, one insight</h1>
<p>Five research agents surveyed the academic and practitioner literature for
futures-leaning strategies (notes in <code>backtest/reference/</code>). The
ranked shortlist was pre-registered in <code>round15_prereg.md</code> before any
test ran: intraday momentum (the strongest academic candidate), turn-of-month,
a trend overlay on the deployed gold rule, opening-gap fills, and a session-split
diagnostic of our own trades. Pre-FOMC drift was dropped a priori (documented
dead 2015&ndash;2019). {r['ledger']} cells, all counted.</p>

<div class="verdict">
<p><strong>Verdict: every published edge tested is dead on our data &mdash; and
the diagnostic reframed our own strategy.</strong> Intraday momentum is not
merely decayed but sign-flipped on 20 years of index CFDs. Turn-of-month days
earn exactly the all-days average. The trend overlay has no gradient. Gap-fill
base rates replicate beautifully (82&ndash;87% for small gaps) and the fade
still loses everywhere. The keeper: <strong>only 17% of our deployed gold edge
accrues during Asian hours &mdash; 70% accrues between the London open and the
NY morning.</strong> Asia sets the direction; London and New York pay it.</p>
</div>

<h2><span class="n">01</span>F1 &mdash; intraday momentum: reversed, not decayed</h2>
<p>The Gao et al. (JFE 2018) rule &mdash; sign of the prior-close&rarr;10:00&nbsp;ET
return traded into the last half-hour &mdash; and Baltussen et al.&rsquo;s
rest-of-day variant, with the pre-registered high-vol conditioning. On SPY
1993&ndash;2013 this was Sharpe&nbsp;1.08; Rosa (2022) already found it dead
out-of-sample; on our 2005&ndash;2025 CFDs it is <em>negative</em>, most
significantly on the low-vol days the literature said to avoid. The only cell
with the literature&rsquo;s sign (RTY rest-of-day, high vol) flips sign between
halves. Full table incl. low-vol cells in <code>results/r15.json</code>.</p>
<div class="tblwrap"><table>
<thead><tr><th>Cell</th><th>n</th><th>bps/trade</th><th>t</th>
<th>t 2005&ndash;15</th><th>t 2016&ndash;25</th></tr></thead>
<tbody>{f1_rows}</tbody></table></div>
<p class="note">CFD closes are not SPY closes: our 16:00-ET marks carry CFD
spread and any feed idiosyncrasies, so this kills the rule <em>for us</em>
without adjudicating the ETF literature. RTY sample ends 2020 in this frame
(data gap); its recent column is empty.</p>

<h2><span class="n">02</span>F2 &mdash; turn-of-month carries zero excess</h2>
<p>Both windows (McConnell&ndash;Xu; Etula &ldquo;Dash for Cash&rdquo;),
2005&ndash;2025. Held-day returns match the unconditional daily mean almost
exactly &mdash; SPX +4.3&ndash;5.8 bps/day held vs +4.0 all days, NDX
+5.7&ndash;6.9 vs +6.5. The 90-year anomaly is simply absent from the modern
sample.</p>
<div class="tblwrap"><table>
<thead><tr><th>Cell</th><th>n days</th><th>bps/day</th><th>t</th>
<th>t 2005&ndash;15</th><th>t 2016&ndash;25</th></tr></thead>
<tbody>{f2_rows}</tbody></table></div>

<h2><span class="n">03</span>F3 &mdash; trend overlay: no gradient, no overlay</h2>
<p>Deployed trades whose direction agrees vs disagrees with gold&rsquo;s trailing
trend sign, four lookbacks. Agreement helps at 252 days, hurts at 63&ndash;189,
with in-sample halves scattered around zero &mdash; the signature of noise, not
of a regime. The breakout does not need the trend&rsquo;s permission.</p>
<div class="tblwrap"><table>
<thead><tr><th>Cell</th><th>n</th><th>PF</th><th>t</th>
<th>t 2020&ndash;23</th><th>t 2024&ndash;25</th></tr></thead>
<tbody>{f3_rows}</tbody></table></div>

<h2><span class="n">04</span>F4 &mdash; where our edge actually lives</h2>
<div class="stats">
<div class="stat"><div class="k">entry &rarr; London 07:00</div><div class="v">{sh['to_ldn']*100:.0f}%</div></div>
<div class="stat"><div class="k">07:00 &rarr; 14:00 UTC</div><div class="v">{sh['ldn_to_fix']*100:.0f}%</div></div>
<div class="stat"><div class="k">14:00 &rarr; exit</div><div class="v">{sh['fix_to_exit']*100:.0f}%</div></div>
</div>
<p>The session-split of all 652 deployed trades, on actual prices. The
&ldquo;London bias&rdquo; literature says gold&rsquo;s return accrues in Asian
hours and dies in London/NY hours &mdash; our strategy is the opposite:
<strong>the Asia leg contributes 17%, the London-to-NY-morning leg 70%</strong>.
The deployed rule is not a bet on the overnight gold drift; it uses the thin
Asia open to identify the day&rsquo;s direction and then harvests the
follow-through when real liquidity arrives. This also re-explains round 12
in one line: the London 08:00 add-a-winner candidate works because it adds
size exactly where the P&amp;L density is highest. Diagnostic only &mdash; no
rule change (round 9 already showed every early exit loses money).</p>

<h2><span class="n">05</span>F5 &mdash; gap fills: real base rate, losing trade</h2>
<p>Descriptives replicate the practitioner literature almost exactly: small
gaps (0.05&ndash;0.2%) fill 82&ndash;87% same-session, mostly by noon; large
gaps (&gt;0.5%) fill 34&ndash;40%. The pre-registered fade (enter 09:35 toward
the fill, stop 2&times; gap, out by noon) loses in every bucket on both markets
&mdash; the no-fill days are the big trend days, and their losses swamp the
many small wins. Third time this repo has proven a true base rate is not an
edge (rounds 14&rsquo;s ping-pong and magnet, now this).</p>
<div class="tblwrap"><table>
<thead><tr><th>Cell</th><th>n</th><th>bps/trade</th><th>t</th>
<th>t 2005&ndash;15</th><th>t 2016&ndash;25</th></tr></thead>
<tbody>{f5_rows}</tbody></table></div>

<h2><span class="n">06</span>What this settles</h2>
<p>The five research reports (graveyard-checked, decay-annotated) plus 38 dead
cells buy something durable: the best-documented public anomalies in index
futures do not survive contact with 20 years of our own data at our own costs
&mdash; consistent with the McLean&ndash;Pontiff post-publication decay the
agents flagged on nearly every candidate. No max-stat test was needed: there is
no positive to validate. The F4 mechanism line goes into the playbook; the
Hang Seng battery (pre-registered separately) runs when its data lands.</p>

<footer>Specs pre-registered in <code>reference/round15_prereg.md</code>;
research notes in <code>reference/round15_primary_sources.md</code> and the five
agent reports; code <code>run_r15.py</code>; numbers <code>results/r15.json</code>.
Costs: SPX 0.6 / NDX 2.0 / RTY 0.4 index points round trip; halves at 2016-01-01.
Known data caveat: RTY frame ends 2020-05.</footer>
</div>
"""

open("results/report15.html", "w").write(HTML)
print(f"written results/report15.html ({len(HTML):,} bytes)")
