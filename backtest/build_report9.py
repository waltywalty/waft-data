"""Round-10 report: the TradingView scripts under the house battery."""
import json

T = json.load(open("results/tv_scripts.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap">')

pc = lambda v: "pos-1" if v >= 1.0 else "neg-1"
cells = T["cells"]


def row(c):
    return (f'<tr><td class="lbl">{c["mkt"]}</td><td class="lbl">{c["label"]}</td>'
            f'<td class="num">{c["n"]:,}</td><td class="num">{c["win"]*100:.1f}%</td>'
            f'<td class="num {pc(c["pf"])}">{c["pf"]:.3f}</td>'
            f'<td class="num">{c["t"]:+.2f}</td>'
            f'<td class="num muted">{c["pf_zero_cost"]:.3f}</td>'
            f'<td class="num muted">{c["is_pf"]:.3f}</td>'
            f'<td class="num muted">{c["os_pf"]:.3f}</td></tr>')


cisd_rows = "\n".join(row(c) for c in cells if c["family"].startswith("cisd"))
st_rows = "\n".join(row(c) for c in cells if c["family"] == "strsi")
ov_rows = "\n".join(
    f'<tr><td class="lbl">{k}</td><td class="num">{v["n"]}</td>'
    f'<td class="num {pc(v["pf"])}">{v["pf"]:.3f}</td></tr>'
    for k, v in T["gold_corr_overlay"].items())
isos = T["isos"]
isos_rows = "\n".join(
    f'<tr><td class="lbl">{r["mkt"]} {r["label"]}</td>'
    f'<td class="num">{r["is_pf"]:.3f}</td><td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>'
    f'<td class="num {pc(r["os_pf"])}">{r["os_pf"]:.3f}</td></tr>'
    for r in isos["top10"])

worst_t = min(c["t"] for c in cells if c["family"] == "strsi")
n_pos = sum(1 for c in cells if c["t"] > 0)

HTML = f"""<title>Scripts on Trial</title>
{FONTS}
{CSS}
<div class="wrap">
<header>
<p class="eyebrow">XAUUSD research &middot; round 10</p>
<h1>Four TradingView scripts, one honest battery</h1>
<p class="standfirst">The user supplied four Pine scripts: a session-lines visualizer,
the ICT &ldquo;Venom&rdquo; and &ldquo;Silver Bullet&rdquo; models, and a
Supertrend+RSI strategy. Extracted to mechanical rules and run on gold and three
indices &mdash; 72 cells &mdash; they produce the worst signal this repo has ever
measured, one inverted trend filter, and exactly one watch item that does not clear
the bar but has earned a place in the notebook.</p>
<div class="provenance">
<span>markets <b>XAU &middot; SPX &middot; NDX &middot; RTY</b></span>
<span>cells <b>72</b></span>
<span>cells with t &gt; 0 <b>{n_pos}</b></span>
<span>worst t <b>{worst_t:+.0f}</b></span>
</div>
</header>

<section>
<h2><span class="n">01</span>What the scripts actually contain</h2>
<ul>
<li><strong>&ldquo;TJR-Style Sessions&rdquo;</strong> draws session highs and lows;
it has no entry logic. Its testable content &mdash; the NY AM session trading against
London-session levels &mdash; was run through the same machinery as the ICT models.</li>
<li><strong>&ldquo;Venom&rdquo; and &ldquo;Silver Bullet&rdquo;</strong> share one
mechanism beneath the order-block decoration: <em>CISD</em> &mdash; break of an opening
range, then entry against the break when price closes back through the open of the
candle run that produced it. Venom uses an 08:00-09:30 ET range traded to the close;
Silver Bullet a 09:00-10:00 range traded 10:00-11:00 (a to-EoD variant was added).</li>
<li><strong>&ldquo;Supertrend+RSI&rdquo;</strong> is fully mechanical &mdash; and
contains a real defect: in Pine v5/v6, <code>ta.supertrend</code> returns direction
<code>-1</code> for an <em>uptrend</em>, so the script&rsquo;s
<code>upTrend = stDir == 1</code> makes its &ldquo;trend filter&rdquo; trade longs when
the supertrend is bearish. Both readings were tested. The $240k-notional sizing and
pyramiding in the script are dressing on the signal and were replaced by the house
per-trade accounting.</li>
</ul>
</section>

<section>
<h2><span class="n">02</span>Supertrend + RSI: the worst signal ever measured here</h2>
<p class="lede">Every market, every parameter set, both direction readings: it loses
<em>before</em> costs. The t-statistics reach {worst_t:+.0f} on thirty-thousand-trade
samples. The inverted &ldquo;as written&rdquo; version is even worse than the intended
one &mdash; but neither is salvageable, and no parameter in the script&rsquo;s input
panel changes that.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Mkt</th><th class="l">Variant</th><th>n</th><th>win</th>
<th>PF</th><th>t</th><th>PF@0</th><th>IS</th><th>OS</th></tr></thead>
<tbody>{st_rows}</tbody></table></div>
<p>Mechanism: RSI crossing 55 inside a supertrend regime is a momentum-chase entry at
the most expensive point of a 5-minute swing, with a trailing stop tight enough to be
tagged by normal noise. High trade frequency then multiplies a small negative gross
edge by thousands. This family is buried with prejudice.</p>
</section>

<section>
<h2><span class="n">03</span>The CISD reversal: dead net, with one watch item</h2>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Mkt</th><th class="l">Window / target</th><th>n</th><th>win</th>
<th>PF</th><th>t</th><th>PF@0</th><th>IS</th><th>OS</th></tr></thead>
<tbody>{cisd_rows}</tbody></table></div>
<p>The TJR window (NY against London levels) is dead everywhere &mdash; the fourth
independent construction of a session-sweep entry to fail in this repo. The strict
10-11 Silver Bullet window is dead everywhere. The indices are dead everywhere net.</p>
<p><strong>The watch item.</strong> Gold&rsquo;s Silver-Bullet-to-EoD cell is the one
place the family breathes: PF 1.068 net (t +0.52, nothing), zero-cost 1.198, with
2024-25 at 1.26/1.08 by year. Two decompositions temper and sharpen it: year-by-year
is noisy around 1.0-1.1 (2021 1.12, 2022 0.88, 2023 1.09) so this is not a clean
regime break; and the <em>shorts</em> carry it &mdash; PF 1.247 (n=275) fading upside
breaks across a five-year gold bull, against 0.936 for longs. That last cut is
post-hoc and counts as a hypothesis, not a finding.</p>
<h3>Correlation overlay (gold) and the honest OOS panel</h3>
<div class="tbl-wrap" style="max-width:520px"><table>
<thead><tr><th class="l">Cell / regime</th><th>n</th><th>PF</th></tr></thead>
<tbody>{ov_rows}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Top 10 by IS t</th><th>IS PF</th><th>IS t</th><th>OS n</th><th>OS PF</th></tr></thead>
<tbody>{isos_rows}</tbody></table></div>
<p>For the first time the honest-OOS panel reads above water (top-10 median OS PF
{isos["honest_median_os_pf"]:.3f} vs population {isos["population_median_os_pf"]:.3f})
&mdash; but look at the IS column: every selected cell was at or below 1.0 in-sample.
Selection found nothing; the recent era is simply kinder to this family, on gold
especially. That is a regime observation, not an edge. By the house standard &mdash;
both halves, same sign &mdash; the cell fails.</p>
<div class="verdict"><div class="head">Verdict and disposition</div>
<p><strong>Nothing from these scripts is deployable or combinable.</strong> The
Supertrend+RSI family and the TJR/strict-Silver-Bullet windows join the graveyard.
The gold CISD-to-EoD reversal &mdash; and specifically its short side &mdash; goes on
the watch list: re-test when the 2026 gold data accumulates, and if the pattern is
real it will still be there. It does not touch the deployed strategy, whose own
forward log remains the gate for every change.</p></div>
</section>

<section>
<h2><span class="n">04</span>Methods</h2>
<ul>
<li>Entries at bar closes only; stops and targets walked on 5-minute paths with the
conservative stop-first rule; right-endpoint discipline throughout.</li>
<li>CISD levels reconstructed from the scripts&rsquo; own logic: the open of the last
opposite-body candle run (up to 5 bars) before the break; stop at the session extreme
at trigger time; first break side only, per the scripts&rsquo; guards.</li>
<li>Supertrend implemented with Wilder smoothing and verified to flip on close-through
band, matching <code>ta.supertrend</code>; the stop trails the line exactly as the
script&rsquo;s recomputed-per-bar exit does.</li>
<li>Costs $0.30/oz and 0.6/2.0/0.4 index points round trip; every cell re-priced at
zero cost. Era splits: gold 2024+, SPX 2020+, NDX 2021+, RTY 2017+. All 72 cells
reported; no significance claimed anywhere.</li>
</ul>
<footer><p>Round 10. Engine and runner: <code>run_tv.py</code>; results in
<code>results/tv_scripts.json</code>.</p></footer>
</section>
</div>
"""
open("results/report9.html", "w").write(HTML)
print(f"written results/report9.html ({len(HTML):,} bytes)")
