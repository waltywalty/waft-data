"""Round-9 report: exits, streaks, sizing ladders, and the index expedition."""
import json

E = json.load(open("results/exits.json"))
S = json.load(open("results/sizing.json"))
EP = json.load(open("results/exit_portfolio.json"))
NX = json.load(open("results/nyidx.json"))
NF = json.load(open("results/nyidx_filters.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap">')

pc = lambda v: "pos-1" if v >= 1.0 else "neg-1"


def vrow(r):
    ag = '<span class="pos-t">agree</span>' if r.get("agree") else '<span class="neg-t">disagree</span>'
    return (f'<tr><td class="lbl">{r["label"]}</td><td class="num">{r["n"]}</td>'
            f'<td class="num {pc(r["pf"])}">{r["pf"]:.3f}</td>'
            f'<td class="num">{r["exp"]:+.2f}</td><td class="num">{r["t"]:+.2f}</td>'
            f'<td class="num muted">{r["is_pf"]:.3f}</td>'
            f'<td class="num muted">{r["os_pf"]:.3f}</td><td class="lbl">{ag}</td></tr>')


hold_rows = "\n".join(
    f'<tr><td class="lbl">+{h["h"]}h</td><td class="num">{h["mean"]:+.2f}</td>'
    f'<td class="num muted">{h["median"]:+.2f}</td></tr>' for h in E["hold_curve"])
clock_rows = "\n".join(vrow(r) for r in E["clock"])
tgt_rows = "\n".join(vrow(r) for r in E["target"])
trail_rows = "\n".join(vrow(r) for r in E["trail"])
be_rows = "\n".join(vrow(r) for r in E["breakeven"])
ovn = E["overnight"][0]

ep_rows = "\n".join(
    f'<tr><td class="lbl">{k}</td><td class="num">{v["pf"]:.3f}</td>'
    f'<td class="num">{v["exp"]:+.2f}</td>'
    f'<td class="num {"pos-2" if v["final"] > 5000 else "pos-1"}">${v["final"]:,.0f}</td>'
    f'<td class="num">{v["cagr"]*100:+.1f}%</td><td class="num">{v["mdd"]*100:.1f}%</td></tr>'
    for k, v in EP.items())

st = S["streaks"]
dep = S["dependence"]
SCHEME_LBL = {"flat1": "flat 1% (deployed)", "flat2": "flat 2%",
              "lad1.5c4": "&times;1.5 per loss, cap 4%", "lad2c8": "&times;2 per loss, cap 8%",
              "add.5c3": "+0.5%/loss, cap 3%", "anti1.5": "&times;1.5 per win, cap 4%",
              "halfloss": "halve after a loss"}
rp = S["real_path"]
bt = S["bootstrap"]
sz_rows = "\n".join(
    f'<tr><td class="lbl">{SCHEME_LBL[k]}</td>'
    f'<td class="num">${rp[k]["final"]:,.0f}</td>'
    f'<td class="num">{rp[k]["mdd"]*100:.1f}%</td>'
    f'<td class="num">${bt[k]["median_final"]:,.0f}</td>'
    f'<td class="num">{bt[k]["median_mdd"]*100:.1f}%</td>'
    f'<td class="num">{bt[k]["p95_mdd"]*100:.1f}%</td>'
    f'<td class="num {"neg-2" if bt[k]["p_dd50"] > 0.3 else ("neg-1" if bt[k]["p_dd50"] > 0.05 else "pos-1")}">'
    f'{bt[k]["p_dd50"]*100:.1f}%</td></tr>' for k in SCHEME_LBL)

# ---- index summary: per family x index, median net PF / best t / median zero-cost PF
import statistics
fam_lbl = {"zarattini": "Zarattini first-bar", "orb": "ORB follow", "orb_fade": "ORB fade",
           "judas": "Judas sweep", "meanrev": "Open mean reversion"}
cells = NX["cells"]
fam_rows = ""
for fam in fam_lbl:
    row = f'<tr><td class="lbl">{fam_lbl[fam]}</td>'
    for idx in ("SPX", "NDX", "RTY"):
        cs = [c for c in cells if c["family"] == fam and c["idx"] == idx]
        if not cs:
            row += '<td class="num muted">—</td>' * 3
            continue
        mpf = statistics.median(c["pf"] for c in cs)
        bt_ = max(c["t"] for c in cs)
        mz = statistics.median(c["pf_zero_cost"] for c in cs)
        row += (f'<td class="num {pc(mpf)}">{mpf:.3f}</td>'
                f'<td class="num muted">{bt_:+.2f}</td>'
                f'<td class="num muted">{mz:.3f}</td>')
    fam_rows += row + "</tr>\n"

nf_rows = ""
for idx, res in NF.items():
    for lbl, r in res.items():
        nf_rows += (f'<tr><td class="lbl">{idx}</td><td class="lbl">{lbl}</td>'
                    f'<td class="num">{r["n"]}</td>'
                    f'<td class="num {pc(r["pf"])}">{r["pf"]:.3f}</td>'
                    f'<td class="num">{r["t"]:+.2f}</td>'
                    f'<td class="num muted">{r["pf0"]:.3f}</td></tr>\n')

isos = NX["isos"]
isos_rows = "\n".join(
    f'<tr><td class="lbl">{r["idx"]} {r["label"]}</td>'
    f'<td class="num">{int(r["is_n"])}</td><td class="num">{r["is_pf"]:.3f}</td>'
    f'<td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>'
    f'<td class="num {pc(r["os_pf"])}">{r["os_pf"]:.3f}</td></tr>'
    for r in isos["top10"][:6])

best_t = max(c["t"] for c in cells)
n_pos_t = sum(1 for c in cells if c["t"] > 0)

HTML = f"""<title>The Clock, the Streak, and the Indices</title>
{FONTS}
{CSS}
<div class="wrap">
<header>
<p class="eyebrow">XAUUSD research &middot; round 9</p>
<h1>The clock survives, the ladder fails, the indices decline</h1>
<p class="standfirst">Three questions settled and one expedition returned empty-handed:
no exit beats holding to the New York close; losing streaks are coin-flip-ordinary and
sizing up into them buys drawdown, not return; and twenty years of S&amp;P, Nasdaq and
Russell intraday data confirm the literature's own caveat &mdash; the NY-open anomalies
are real gross and dead net. The portfolio stays gold-only, by evidence rather than
default.</p>
<div class="provenance">
<span>gold <b>652 deployed trades, 2020&ndash;2025</b></span>
<span>indices <b>SPX &middot; NDX &middot; RTY, 2005&ndash;2025, 5-min</b></span>
<span>index cells <b>84 + 15 filter cuts</b></span>
</div>
</header>

<section>
<h2><span class="n">01</span>The verdict up front</h2>
<div class="stats">
<div class="stat"><div class="k">best exit found</div><div class="v dim">16:00 NY</div></div>
<div class="stat"><div class="k">longest loss streak</div><div class="v dim">9 &middot; iid expects ~11</div></div>
<div class="stat"><div class="k">ladder P(DD&gt;50%)</div><div class="v neg-t">41&ndash;96%</div></div>
<div class="stat"><div class="k">index cells with t &gt; 0</div><div class="v neg-t">{n_pos_t} / {len(cells)}</div></div>
</div>
</section>

<section>
<h2><span class="n">02</span>Is there a better exit? No &mdash; and here is why</h2>
<p class="lede">Entries frozen at the deployed spec; only the exit varied. First the
diagnostic that needs no parameter search: the average trade's open P&amp;L, hour by
hour after the fill.</p>
<div class="tbl-wrap" style="max-width:440px"><table>
<thead><tr><th class="l">Hours held</th><th>mean $/oz</th><th>median</th></tr></thead>
<tbody>{hold_rows}
<tr style="border-top:2px solid var(--rule)"><td class="lbl"><strong>16:00 NY close</strong></td>
<td class="num pos-t"><strong>+2.51</strong></td><td class="num">+1.30</td></tr></tbody></table></div>
<p>The trade is underwater for its first three hours, turns during London, and accrues
monotonically into the New York close &mdash; then the drift dies: holding overnight
returns PF {ovn["pf"]:.3f} with the halves disagreeing. The 16:00-NY exit harvests the
whole of a drift that lasts exactly one trading day.</p>
<h3>Clock alternatives</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Exit</th><th>n</th><th>PF</th><th>exp</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{clock_rows}</tbody></table></div>
<h3>Targets, trails, breakeven moves</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Variant</th><th>n</th><th>PF</th><th>exp</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{tgt_rows}{trail_rows}{be_rows}</tbody></table></div>
<p>Two variants beat the deployed profit factor with both halves agreeing &mdash; the
breakeven move at +1 range and the 2&times;-range trail. Profit factor is a ratio;
compounding pays expectancy. At identical 1% risk:</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Exit</th><th>PF</th><th>exp $/oz</th><th>$2,000 &rarr;</th><th>CAGR</th><th>max DD</th></tr></thead>
<tbody>{ep_rows}</tbody></table></div>
<div class="verdict"><div class="head">Verdict</div>
<p>The deployed clock exit compounds to 1.6&times; the equity of either
&ldquo;improvement&rdquo; while giving up about one point of drawdown. The breakeven stop
gets tagged in the mid-day chop the hold curve shows is normal, scratching trades that
on average go on to win the New York session. <strong>The exit question is closed:
16:00 New York stays.</strong></p></div>
</section>

<section>
<h2><span class="n">03</span>Streaks: the record is nine, and chance expected eleven</h2>
<div class="stats">
<div class="stat"><div class="k">mean loss streak</div><div class="v dim">{st["loss"]["mean"]:.2f}</div></div>
<div class="stat"><div class="k">90th percentile</div><div class="v dim">{st["loss"]["p90"]:.0f}</div></div>
<div class="stat"><div class="k">longest / next</div><div class="v dim">{st["loss"]["max"]} / {st["loss"]["second"]}</div></div>
<div class="stat"><div class="k">iid expectation</div><div class="v dim">~{S["iid_expected_max_loss_streak"]:.0f}</div></div>
</div>
<p>Losing streaks average {st["loss"]["mean"]:.2f} trades (median {st["loss"]["median"]:.0f});
the worst ever was {st["loss"]["max"]} in a row, once, with {st["loss"]["second"]} right
behind it &mdash; so 9 is not an outlier to discount; plan for it. But a fair coin at
this win rate over 652 trades would typically produce a run of ~{S["iid_expected_max_loss_streak"]:.0f}:
the strategy's worst streak is <em>milder</em> than chance. Winning streaks: mean
{st["win"]["mean"]:.2f}, longest {st["win"]["max"]}.</p>
<p>Do streaks predict anything? P(win after a loss) = {dep["p_after_loss"]*100:.1f}%
against {dep["p_after_win"]*100:.1f}% after a win &mdash; the direction a loss-ladder
needs, but &chi;&sup2; p = {dep["chi2_p"]:.2f} and runs-test z = {dep["runs_z"]:+.2f}:
statistically indistinguishable from independence.</p>
</section>

<section>
<h2><span class="n">04</span>Sizing ladders: paying more for the same distribution</h2>
<p class="lede">Each scheme run on the real trade sequence, then on 2,000 shuffles of
the same trades &mdash; order is luck, and the shuffles price it.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Scheme</th><th>real final</th><th>real DD</th>
<th>median final</th><th>median DD</th><th>p95 DD</th><th>P(DD&gt;50%)</th></tr></thead>
<tbody>{sz_rows}</tbody></table></div>
<div class="verdict"><div class="head">Verdict</div>
<p>The ladders&rsquo; spectacular real-path results are ordering luck riding on a p=0.12
effect. Across shuffles, &times;1.5-capped-4% delivers a median outcome below flat 2%
while carrying a 41% chance of losing half the account; &times;2-capped-8% makes that
96%. <strong>Whatever return level is wanted, a flat fraction buys it with a thinner
drawdown tail than any streak-keyed ladder. Sizing stays flat.</strong> The mild
after-loss edge, if it ever reaches significance in live logs, would justify revisiting
&mdash; the forward log now captures what it needs.</p></div>
</section>

<section>
<h2><span class="n">05</span>The index expedition: real gross, dead net</h2>
<p class="lede">Twenty years of S&amp;P 500, Nasdaq-100 and Russell 2000 intraday CFD
data (two independent feeds, timezone-verified by the 09:30-ET volatility step in both
seasons, feeds agreeing to +0.007% where they overlap). Four strategy families at the
NY open and pre-open, 84 cells. Best t-statistic anywhere: {best_t:+.2f}. Cells with
positive t: {n_pos_t} of {len(cells)}.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Family</th><th>SPX PF</th><th>t*</th><th>PF@0</th>
<th>NDX PF</th><th>t*</th><th>PF@0</th><th>RTY PF</th><th>t*</th><th>PF@0</th></tr></thead>
<tbody>{fam_rows}</tbody></table></div>
<p>The Zarattini first-bar row is the story: the published QQQ anomaly <em>replicates
gross</em> on all three indices (zero-cost PF 1.13&ndash;1.20 over 4,000&ndash;5,000
trades each) and is consumed entirely by a realistic spread &mdash; precisely the
independent replication&rsquo;s warning that the $0.07/share edge dies at 2.2&cent; of
slippage. Our engines reproduce the honest version of the literature, not the headline.</p>
<h3>The pre-registered rescue filters</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Index</th><th class="l">Cut</th><th>n</th><th>PF</th><th>t</th><th>PF@0</th></tr></thead>
<tbody>{nf_rows}</tbody></table></div>
<p>Relative volume &mdash; the one filter with academic-grade evidence &mdash; makes
SPX and NDX <em>worse</em> here (tick-count CFD volume is not exchange volume; the
caveat was stated before the test and it bit). Gap-alignment&rsquo;s least-bad cut runs
<em>against</em> the folklore direction at t {max(r["t"] for res in NF.values() for r in res.values()):+.2f}: noise.</p>
<h3>Honest out-of-sample (rank on the Oanda era, read the recent era)</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th>IS n</th><th>IS PF</th><th>IS t</th><th>OS n</th><th>OS PF</th></tr></thead>
<tbody>{isos_rows}</tbody></table></div>
<div class="verdict"><div class="head">The combination question</div>
<p>The stated condition was: find a strong NY-open strategy first, then combine it with
the Asia gold strategy. The condition is not met &mdash; the best of 84 cells and 15
filter cuts is statistically zero &mdash; and combining a validated edge with a
zero-expectancy component only dilutes it. <strong>The portfolio remains the Asia gold
strategy alone.</strong> Honest top-10 IS-ranked cells read median OS PF
{isos["honest_median_os_pf"]:.3f} against a population of
{isos["population_median_os_pf"]:.3f}: nothing selectable either.</p></div>
</section>

<section>
<h2><span class="n">06</span>Methods and defects</h2>
<ul>
<li><strong>Data provenance.</strong> Oanda 1-minute (2005-2020) and an MT5 broker
export (2020-2025), located on GitHub, harmonized to 5-minute UTC. Both timezone claims
verified by the sharpest fingerprint available: the 09:30-ET open is a &ge;2&times;
one-bar volatility step, in winter and summer separately, in every feed. The Russell has
a 2020-2025 intraday hole (no free source found); its results cover 2005-2020.</li>
<li><strong>Costs.</strong> 0.6 / 2.0 / 0.4 index points round trip (SPX/NDX/RTY);
every cell also re-priced at zero cost to separate &ldquo;no anomaly&rdquo; from
&ldquo;anomaly smaller than the spread&rdquo; &mdash; they are different findings and
round 9 produced both.</li>
<li><strong>One crash, no silent error.</strong> A conditional-precedence bug in the
stop/target scanner raised a TypeError on first run (a None guard protecting only one
branch); fixed and re-run. Nothing produced wrong numbers silently.</li>
<li><strong>Exit-study consistency.</strong> The re-walked deployed variant differs
slightly from the recorded deployable set (path-slice conventions, n=645 vs 652); all
exit comparisons use the same walker, so the comparison is internally exact.</li>
<li><strong>Multiplicity.</strong> ~60 exit/sizing tests and 99 index tests, all
reported. No significance claimed anywhere; no correction needed for null results.</li>
</ul>
<footer>
<p>Round 9. Engines: <code>run_exits.py</code>, <code>run_exit_portfolio.py</code>,
<code>run_sizing.py</code>, <code>index_data.py</code>, <code>run_nyidx.py</code>,
<code>run_nyidx_filters.py</code>. Index data cached locally from
FutureSharks/financial-data (Oanda) and ts4blader/market_data (MT5); not committed.</p>
</footer>
</section>
</div>
"""
open("results/report8.html", "w").write(HTML)
print(f"written results/report8.html ({len(HTML):,} bytes)")
