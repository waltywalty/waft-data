"""Round 15b report: the Hang Seng battery."""
import json

r = json.load(open("results/hsi.json"))
d = r["ha_desc"]
ms = r["ha_maxstat"]
cs = r["ha_cost_sens"]

ha_rows = "\n".join(
    f"<tr><td class='lbl'>{k.replace('_',' ').replace('t0.3','|push| &ge; 0.3 ATR,').replace('s0.5','stop 0.5&times;,').replace('s1.0','stop 1.0&times;,').replace('c1030','exit 10:30').replace('c1200','exit 12:00').replace('c1600','exit 16:00')}</td>"
    f"<td>{v['n']}</td><td>{float(v['pf']):.3f}</td><td>{float(v['t']):+.2f}</td>"
    f"<td>{float(v['h1']['t']):+.2f}</td><td>{float(v['h2']['t']):+.2f}</td></tr>"
    for k, v in r["ha_econ"].items() if v["n"] >= 15)

hb_rows = "\n".join(
    f"<tr><td class='lbl'>{k}</td><td>{v['n']}</td><td>{float(v['pf']):.3f}</td>"
    f"<td>{float(v['t']):+.2f}</td><td>{float(v['h1']['t']):+.2f}</td><td>{float(v['h2']['t']):+.2f}</td></tr>"
    for k, v in r["hb"].items())

cost_rows = "\n".join(
    f"<tr><td class='lbl'>{c} points round trip</td><td>{v['n']}</td><td>{v['pf']:.3f}</td>"
    f"<td>{v['t']:+.2f}</td><td>{v['exp']:+.1f}</td></tr>" for c, v in cs.items())

grad = " &middot; ".join(f"{x:+.1f}" for x in d["grad_quintiles"])

HTML = f"""<title>The Hang Seng Battery</title>
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
.wrap {{ max-width:880px; margin:0 auto; padding:34px 20px 90px; }}
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
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px;
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
<div class="kicker">Hang Seng / MHI &middot; research round 15b &middot; August 2026</div>
<h1>The eye finds its first survivor</h1>
<p>The user&rsquo;s chart observation: HSI futures push hard one way between the
09:15 derivatives open and the 09:30 cash open, then reverse. Pre-registered
before any data existed on disk (<code>reference/round15_hsi_prereg.md</code>),
tested on a spliced 4.5-year 15-minute HSI CFD series (two independent brokers,
median splice difference 3.1&nbsp;bps; session structure verified from the data:
97% of days open 01:15 UTC, the cash-open bar&rsquo;s median range is 136 points
vs 84 pre-open). {r['ledger']} cells in the ledger.</p>

<div class="verdict">
<p><strong>Verdict: the pre-open reversal is real, survives its max-stat test
(p&nbsp;=&nbsp;{ms['p']:.3f}), and goes to the watch list &mdash; not to
capital &mdash; because 43 trades is 43 trades.</strong> The home-session
breakout (H-B) failed exactly as the price-discovery meta-law predicted, and
no cross-market correlation gate rescues it (H-C). The sixth Judas
construction tested in this repo is the first with a pulse &mdash; and the
difference is that this one has a mechanism: fifteen minutes of futures
trading with no cash market underneath.</p>
</div>

<h2><span class="n">01</span>H-A &mdash; the pre-open push reversal</h2>
<div class="stats">
<div class="stat"><div class="k">days</div><div class="v">{d['n']}</div></div>
<div class="stat"><div class="k">&rho; push vs next hour</div><div class="v">{d['rho_1030']:+.3f}</div></div>
<div class="stat"><div class="k">p-value</div><div class="v">{d['p_1030']:.3f}</div></div>
<div class="stat"><div class="k">max-stat p</div><div class="v">{ms['p']:.3f}</div></div>
</div>
<p>Descriptively the effect is small but sign-consistent: mean 09:30&rarr;10:30
move by push quintile (most negative &rarr; most positive push) runs
{grad} points &mdash; down-pushes bounce, up-pushes fade. It does NOT extend to
the full day (&rho; {d['rho_1600']:+.3f}, p {d['p_1600']:.2f}): this is an
open-auction effect, not a day-direction signal. The economics concentrate
where the mechanism says they should &mdash; large pushes (&ge;0.3 daily ATR
in one 15-minute bar, ~10 days a year):</p>
<div class="tblwrap"><table>
<thead><tr><th>Cell (all: fade the push at 09:30)</th><th>n</th><th>PF</th><th>t</th>
<th>t &rarr;2024-04</th><th>t 2024-05&rarr;</th></tr></thead>
<tbody>{ha_rows}</tbody></table></div>
<p>Every cell is positive in both halves, and the grid&rsquo;s best t (+1.60)
beats {100-ms['p']*100:.0f}% of circularly-shifted placebo signals (permutation
median {ms['perm_p50']:+.2f}). Cost sensitivity on the best cell (fade to the
16:00 HKT close, stop 0.5&times; the pre-open range beyond its extreme):</p>
<div class="tblwrap"><table>
<thead><tr><th>Cost assumption</th><th>n</th><th>PF</th><th>t</th><th>mean pts</th></tr></thead>
<tbody>{cost_rows}</tbody></table></div>
<p><strong>Why watch, not trade:</strong> 43 trades over 4.5 years cannot
clear this repo&rsquo;s evidence bar (the deployed gold rule stands on 652).
The t of +1.60 is respectable for the sample but modest in absolute terms, the
cells share the same 43 days (six variants of one bet, not six confirmations),
and 2022&ndash;2026 contains exactly one HSI regime cycle. The data source
updates hourly, so the sample grows ~10 trades/year on its own; the re-test
bar is pre-set below.</p>

<h2><span class="n">02</span>H-B &mdash; the home-session range, as predicted</h2>
<p>The gold construction transplanted to HSI&rsquo;s own 09:30&ndash;10:30
window, both arms pre-declared. The pre-registration predicted the breakout
arm fails because 09:30 HKT is the Hang Seng&rsquo;s <em>home</em> open &mdash;
fast price discovery, the opposite of gold&rsquo;s thin Asia session. It did.
The fade arm is worse, so the range carries mild gross follow-through &mdash;
just nothing that survives 10 points of cost.</p>
<div class="tblwrap"><table>
<thead><tr><th>Arm</th><th>n</th><th>PF</th><th>t</th>
<th>t &rarr;2024-04</th><th>t 2024-05&rarr;</th></tr></thead>
<tbody>{hb_rows}</tbody></table></div>

<h2><span class="n">03</span>H-C &mdash; correlation gates do not rescue it</h2>
<p>Nikkei, China A50, HSCEI and CSI300-futures 20-day correlation gates on the
better H-B arm, round-13 protocol: every gated cell with real sample size stays
negative (best: A50 le-gate, t &minus;0.19 on n=233). The round-13 lesson
transfers unchanged to a new market: correlation windows onto the same macro
state do not create edges that are not there.</p>

<h2><span class="n">04</span>The watch-list entry, pre-committed</h2>
<p><strong>Rule under watch:</strong> when the 09:15&ndash;09:30 HKT pre-open
bar moves &ge; 0.3&times; the 14-day ATR, fade it at the 09:30 cash open; stop
0.5&times; the pre-open range beyond its extreme; hold to 16:00 HKT.
<strong>Re-test trigger:</strong> when the live feed brings the trade count to
80+ (roughly 2029) or after any 20-trade block, whichever first; promote only
if PF &ge; 1.4 and both the old and new halves stay positive; kill on new-half
t &le; 0. No parameter may move between now and then &mdash; the grid above is
the whole search, already spent.</p>

<footer>Pre-registration: <code>reference/round15_hsi_prereg.md</code> (committed
before data acquisition). Data: HK50/HK33 15m spliced (Yuan archive + Oanda
collector, fetch commands in <code>fetch_data.sh</code>); partners JP225,
CHCUSD, HSCHKD, CFFEX_IF. Code <code>run_hsi.py</code>; numbers
<code>results/hsi.json</code>. Cost 10 index points round trip (MHI-realistic);
halves at 2024-05-01; ambiguous stop/target bars scored as stops.</footer>
</div>
"""

open("results/report_hsi.html", "w").write(HTML)
print(f"written results/report_hsi.html ({len(HTML):,} bytes)")
