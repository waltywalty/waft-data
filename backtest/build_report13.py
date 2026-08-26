"""Round 13 report: eleven more correlation partners as regime gates."""
import json, numpy as np

r = json.load(open("results/corrpartners.json"))

NAMES = dict(aud="AUDUSD (incumbent)", eur="EURUSD", gbp="GBPUSD", jpy="JPY (per USD, inv.)",
             chf="CHF (inv.)", cad="CAD (inv.)", cny="CNY (inv.)", dxy="Dollar index (synthetic)",
             xag="Silver", wti="WTI crude", ust10="US 10y yield (diff)", spx="S&amp;P 500")
OVERLAP = dict(eur=92, jpy=88, chf=88, cad=91, gbp=89, dxy=88, xag=56, cny=33, wti=64, ust10=12, spx=91)

def fmt(x, d=2, plus=True):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "&ndash;"
    return f"{x:+.{d}f}" if plus else f"{x:.{d}f}"

def best_cell(cells, min_n):
    ok = [c for c in cells if c["n"] >= min_n and c["t"] is not None and np.isfinite(c["t"])]
    return max(ok, key=lambda c: c["t"]) if ok else None

def q1_rows():
    out = []
    for k, v in r["partners"].items():
        b = best_cell(v["sweep"], 100)
        both = b["is_"]["t"] > 0 and b["os_"]["t"] > 0
        ov = f"{OVERLAP[k]}%" if k in OVERLAP else "&ndash;"
        out.append(f"<tr><td>{NAMES[k]}</td><td>{b['side']} {b['thr']:+.1f}</td>"
                   f"<td>{b['n']}</td><td>{b['pf']:.3f}</td><td>{fmt(b['t'])}</td>"
                   f"<td>{fmt(b['is_']['t'])}</td><td>{fmt(b['os_']['t'])}</td>"
                   f"<td>{ov}</td></tr>")
    return "\n".join(out)

def q2_rows():
    out = []
    for k, v in r["rescue"].items():
        b = best_cell(v["sweep"], 60)
        if b is None:
            continue
        verdict = ("<span class='bad'>sign flip</span>" if b["is_"]["t"] <= 0 or b["os_"]["t"] <= 0
                   else "<span class='ok'>both +</span>")
        out.append(f"<tr><td>{NAMES[k]}</td><td>{b['side']} {b['thr']:+.1f}</td>"
                   f"<td>{b['n']}</td><td>{b['pf']:.3f}</td><td>{fmt(b['t'])}</td>"
                   f"<td>{fmt(b['is_']['t'])}</td><td>{fmt(b['os_']['t'])}</td><td>{verdict}</td></tr>")
    return "\n".join(out)

def q3_rows():
    out = []
    for k, v in r["q3_and"].items():
        out.append(f"<tr><td>AUD &and; {NAMES[k]}</td><td>{v['side']} {float(v['thr']):+.1f}</td>"
                   f"<td>{v['n']}</td><td>{float(v['pf']):.3f}</td><td>{fmt(float(v['t']))}</td>"
                   f"<td>{fmt(float(v['is_t']))}</td><td>{fmt(float(v['os_t']))}</td></tr>")
    return "\n".join(out)

ms, msa = r["maxstat"], r["maxstat_and"]
base, dep, rb = r["base"], r["aud_control"], r["rescue_base"]

HTML = f"""<title>Round 13: Correlation Partners</title>
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
h1 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:32px; margin:0 0 4px;
  text-wrap:balance; }}
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
.tblwrap {{ overflow-x:auto; border:1px solid var(--rule); border-radius:6px;
  background:var(--surface); margin:14px 0; }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.07em;
  text-transform:uppercase; color:var(--ink-3); text-align:right; padding:10px 12px;
  border-bottom:1px solid var(--rule); white-space:nowrap; }}
th:first-child, td:first-child {{ text-align:left; }}
td {{ padding:8px 12px; border-bottom:1px solid var(--rule); text-align:right;
  font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; white-space:nowrap; }}
tr:last-child td {{ border-bottom:none; }}
.ok {{ color:var(--pos); }} .bad {{ color:var(--neg); }}
.note {{ font-size:13px; color:var(--ink-3); max-width:72ch; }}
footer {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--rule);
  font-size:13px; color:var(--ink-3); max-width:72ch; }}
</style>
<div class="wrap">
<div class="kicker">Asia-open gold &middot; research round 13 &middot; August 2026</div>
<h1>Eleven more correlation partners, one conclusion</h1>
<p>The deployed rule stands aside when the 20-day gold/AUDUSD correlation is above 0.5
&mdash; and it has been standing aside for weeks. The commission: gate the same breakout
on other macro partners (silver, the dollar, EUR, JPY, GBP, CHF, CAD, CNY, oil, the
S&amp;P&nbsp;500, 10-year yields) and see whether any of them adds edge or, better,
rescues trades the AUD gate skips. Three questions were pre-registered before any
gating: <strong>Q1</strong> does any partner beat AUD on the full set;
<strong>Q2</strong> does any partner find a tradeable subset among AUD-skipped days;
<strong>Q3</strong> does a second gate stacked on AUD improve per-trade quality.
Every cell counted: <strong>{r['ledger_cells']} cells</strong> in the ledger.</p>

<div class="verdict">
<p><strong>Verdict: negative on all three questions.</strong> The best cell in the whole
grid (t {fmt(ms['observed'])}) is matched by a random circular-shift search half the time
(permutation median {fmt(ms['perm_p50'])}, p&nbsp;=&nbsp;{ms['p']:.2f}). Every rescue cell
flips sign between halves. The stacked gates that look good both halves are matched by
random series ANDed onto AUD (p&nbsp;=&nbsp;{msa['p']:.2f}). No change to the deployed
rule, and no frequency gain exists in this direction.</p>
</div>

<h2><span class="n">01</span>Data and provenance</h2>
<p>Daily FX from the FRED mirror on GitHub (through Dec 2025), silver / WTI / 10-year
yields from Alpha Vantage dailies, S&amp;P 500 from our own verified intraday file, gold
from the same broker-EET daily closes the deployed filter uses. The synthetic dollar
index is the DXY basket re-weighted without SEK. Sanity signs all landed where macro says
they should: silver most gold-correlated (+0.45 mean), the dollar index negative
(&minus;0.42), yields negative (&minus;0.34), oil and equities weak (+0.14). The AUD
control reproduced the deployed set exactly: {dep['n']} trades, PF
{dep['pf']:.3f}, t {fmt(dep['t'])}. Base (no gate): {base['n']} trades, PF
{base['pf']:.3f}, t {fmt(base['t'])}.</p>

<h2><span class="n">02</span>Q1 &mdash; every gate is the same gate</h2>
<p>Best threshold cell per partner on all {base['n']} breakout trades. The last column is
the share of AUD-selected trades the partner's own best cell also keeps &mdash; the FX
partners and the dollar index keep 88&ndash;92% of the same days. They are not new
filters; they are the same macro state read through a different window.</p>
<div class="tblwrap"><table>
<thead><tr><th>Partner</th><th>Best cell</th><th>n</th><th>PF</th><th>t</th>
<th>t 2020&ndash;23</th><th>t 2024&ndash;25</th><th>Keeps of AUD set</th></tr></thead>
<tbody>{q1_rows()}</tbody></table></div>
<p class="note">Silver's t {fmt(ms['observed'])} is the grid's best number, on fewer
trades than AUD keeps &mdash; and its decile gradient is jagged
(&minus;0.6, +2.2, +1.2, +0.6, +2.5, &minus;0.9, &hellip;), the signature of noise, not
of a regime. The house rule is gradient over peak, and no partner produces a smoother
gradient than the incumbent.</p>

<h2><span class="n">03</span>Q2 &mdash; the skipped days stay dead</h2>
<p>The {rb['n']} trades the AUD gate skips are collectively edge-free (PF
{rb['pf']:.3f}, t {fmt(rb['t'])}). For each partner, the best cell on this subset only
&mdash; and every single one is negative in 2020&ndash;23 and positive in 2024&ndash;25.
That is not a filter finding tradeable days; that is 2024&ndash;25 being a gold bull.
A gate that only works in the half where everything worked is no gate.</p>
<div class="tblwrap"><table>
<thead><tr><th>Partner</th><th>Best cell</th><th>n</th><th>PF</th><th>t</th>
<th>t 2020&ndash;23</th><th>t 2024&ndash;25</th><th>Both halves</th></tr></thead>
<tbody>{q2_rows()}</tbody></table></div>

<h2><span class="n">04</span>Q3 &mdash; stacked gates are selection, not signal</h2>
<p>Second gates ANDed onto the deployed set (base: {dep['n']} trades, PF {dep['pf']:.3f},
t {fmt(dep['t'])}). Two cells &mdash; silver and CNY &mdash; improve both halves, which
is exactly why the permutation test matters: ANDing a <em>random</em> circularly-shifted
regime series onto the real AUD gate and keeping the best cell reaches t
{fmt(msa['perm_p50'])} at the median and beats the observed {fmt(msa['observed'])}
{msa['p']*100:.0f}% of the time. Dropping a third of the trades for a quality bump that
selection alone explains &mdash; and that runs <em>against</em> the round's goal of more
frequency &mdash; is a trade we decline.</p>
<div class="tblwrap"><table>
<thead><tr><th>Gate</th><th>Best cell</th><th>n</th><th>PF</th><th>t</th>
<th>t 2020&ndash;23</th><th>t 2024&ndash;25</th></tr></thead>
<tbody>{q3_rows()}</tbody></table></div>

<h2><span class="n">05</span>What this settles</h2>
<p>The round strengthens the round-12 meta-law rather than the strategy: the edge is
gated by <strong>one</strong> macro state &mdash; loosely, &ldquo;the dollar factor is
not driving gold today&rdquo; &mdash; and AUDUSD is already an adequate window onto it.
Ten other windows onto the same state neither sharpen it (Q1), extend it (Q2), nor
refine it beyond chance (Q3). The frequency we have is the frequency the edge has.
Droughts, including the current one, are the filter doing its job &mdash; the playbook's
drought table stands unchanged.</p>

<footer>Method: 20-day rolling correlation of daily log returns (yield uses simple
differences), calendar-reindexed, lagged one day; trades = 60-minute Asia-open breakout,
2&times; range stop, 16:00-NY exit, $0.30 round-trip cost plus $0.30 stop slippage;
halves split at 2024-01-01. Multiplicity: {r['ledger_cells']} cells, max-statistic
circular-shift permutation ({ms['n_perm']} + {msa['n_perm']} draws). Data files are not
committed; sources are scripted in fetch_data.sh and run_corrpartners.py.</footer>
</div>
"""

open("results/report13.html", "w").write(HTML)
print(f"written results/report13.html ({len(HTML):,} bytes)")
