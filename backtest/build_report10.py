"""Round-11 report: ORB filters, the EMA-pullback entry, point targets, and
the volume-profile value-area reversion."""
import json
import numpy as np

A = json.load(open("results/orb_filters.json"))
B = json.load(open("results/ema_points.json"))
D = json.load(open("results/vprofile.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap">')
pc = lambda v: "pos-1" if v >= 1.0 else "neg-1"


def row(c, label=None):
    return (f'<tr><td class="lbl">{c["mkt"]}</td><td class="lbl">{label or c["label"]}</td>'
            f'<td class="num">{c["n"]:,}</td><td class="num">{c["win"]*100:.1f}%</td>'
            f'<td class="num {pc(c["pf"])}">{c["pf"]:.3f}</td>'
            f'<td class="num">{c["t"]:+.2f}</td>'
            f'<td class="num muted">{c["pf_zero_cost"]:.3f}</td>'
            f'<td class="num muted">{c["is_pf"]:.3f}</td>'
            f'<td class="num muted">{c["os_pf"]:.3f}</td></tr>')


HEAD = ('<thead><tr><th class="l">Mkt</th><th class="l">Cell</th><th>n</th><th>win</th>'
        '<th>PF</th><th>t</th><th>PF@0</th><th>IS</th><th>OS</th></tr></thead>')

a_gold = "\n".join(row(c) for c in A["cells"] if c["mkt"] == "XAU")
a_isos = "\n".join(
    f'<tr><td class="lbl">{r["mkt"]} {r["label"]}</td>'
    f'<td class="num">{r["is_pf"]:.3f}</td><td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num {pc(r["os_pf"])}">{r["os_pf"]:.3f}</td></tr>'
    for r in A["isos"]["top8"])
a_idx = "\n".join(row(c) for c in A["cells"]
                  if c["mkt"] != "XAU" and ("rvol" in c["label"] or "unfiltered" in c["label"])
                  and "15m" in c["label"])

b_ema = "\n".join(row(c) for c in B["cells"] if c["family"] == "ema_pull")
b_pts = "\n".join(row(c) for c in B["cells"] if c["family"] == "points")
b_asia = "\n".join(row(c) for c in B["cells"] if c["family"] == "points_asia")

# volume-profile: per market x gate summary + full gold rows
vp_sum = ""
for mkt in ("XAU", "SPX", "NDX", "RTY"):
    for gate in ("no volume gates", "absorb+grow gates"):
        cs = [c for c in D["cells"] if c["mkt"] == mkt and gate in c["label"]]
        if not cs:
            continue
        med = float(np.median([c["pf"] for c in cs]))
        best = max(cs, key=lambda c: c["pf"])
        vp_sum += (f'<tr><td class="lbl">{mkt}</td><td class="lbl">{gate}</td>'
                   f'<td class="num">{len(cs)}</td>'
                   f'<td class="num {pc(med)}">{med:.3f}</td>'
                   f'<td class="num">{best["pf"]:.3f}</td>'
                   f'<td class="lbl muted">{best["label"].split(" / ", 1)[1] if " / " in best["label"] else best["label"]}</td></tr>\n')
watch = next(c for c in D["cells"]
             if c["mkt"] == "XAU" and "overnight / absorb+grow gates / target va_opp" in c["label"])

HTML = f"""<title>Filters, Pullbacks, and the Profile</title>
{FONTS}
{CSS}
<div class="wrap">
<header>
<p class="eyebrow">XAUUSD research &middot; round 11</p>
<h1>Filters, pullbacks, point targets, and the profile</h1>
<p class="standfirst">Four commissions: volatility and volume filters on the opening-range
breakout, a 30-minute-range EMA-pullback continuation entry, the micro-futures
point-target framing, and a volume-profile value-area reversion with absorption
confirmation. 230 cells. The filters produce the cleanest in-sample mirage this repo has
recorded, the point panel quietly re-derives a known truth about the one strategy that
works, and the absorption idea earns a spot on the watch list.</p>
<div class="provenance">
<span>markets <b>XAU &middot; SPX &middot; NDX &middot; RTY</b></span>
<span>cells <b>72 + 86 + 72</b></span>
<span>micro contracts <b>MGC &middot; MES &middot; MNQ &middot; M2K</b></span>
</div>
</header>

<section>
<h2><span class="n">01</span>ORB filters: the mirage, photographed</h2>
<p class="lede">Impulse (range width / ATR), relative volume, and ATR regime, as terciles
and median splits on the fixed 15m/30m NY ORB. Gold first &mdash; watch the IS and OS
columns:</p>
<div class="tbl-wrap"><table>{HEAD}<tbody>{a_gold}</tbody></table></div>
<div class="tbl-wrap" style="max-width:640px"><table>
<thead><tr><th class="l">Honest OOS: top 8 by IS t</th><th>IS PF</th><th>IS t</th><th>OS PF</th></tr></thead>
<tbody>{a_isos}</tbody></table></div>
<p><strong>This is the sharpest selection mirage in eleven rounds.</strong> Strong-volume
and impulsive-range breakouts on gold posted the best in-sample numbers the NY family has
ever shown (PF 1.474, t +2.32) and collapsed out of sample (0.771, 0.725). Had we skipped
the honest split, these filters would have looked like a rescue. On the indices the
surviving direction actually <em>inverts</em> the intuition: quiet, weak-volume opens
break out better than strong ones (Crabel&rsquo;s compression logic) &mdash; and still
nothing clears water net:</p>
<div class="tbl-wrap"><table>{HEAD}<tbody>{a_idx}</tbody></table></div>
</section>

<section>
<h2><span class="n">02</span>The EMA-pullback continuation</h2>
<p class="lede">30-minute range, 10-minute close outside it, pullback to the EMA, entry on
the continuation close. The 2-minute 20-EMA is a 40-minute smoothing span, implemented as
its exact time-equivalent (8-period EMA on 5m) with a 20-period 5m variant alongside; the
2-minute microstructure itself is bracketed, not simulated.</p>
<div class="tbl-wrap"><table>{HEAD}<tbody>{b_ema}</tbody></table></div>
<p>The pullback gets a better fill than the raw break &mdash; zero-cost PFs sit near or
above 1.1 in half the cells &mdash; but nothing survives costs, and the prior-hour-level
exit is the worst of every exit tested (PF 0.62-0.86: the level is too close, so it
harvests noise and forfeits the day). Same physics as every NY-session entry before it:
the confirmation structure pays the spread, the market keeps the rest.</p>
</section>

<section>
<h2><span class="n">03</span>Micro-futures point targets</h2>
<p class="lede">Target +15 or +20 points, stop = target / RR for RR 1-3, flat at the close
if neither hits. MGC $10/pt &middot; MES $5/pt &middot; MNQ $2/pt &middot; M2K $5/pt. A
fixed point target is a very different object per market: 15 points is 0.78% of gold,
0.73% of SPX, 1.78% of RTY &mdash; and just 0.35% of NDX.</p>
<div class="tbl-wrap"><table>{HEAD}<tbody>{b_pts}</tbody></table></div>
<p><strong>MNQ is the cautionary row.</strong> A 15-20-point Nasdaq target is 0.35-0.47%
&mdash; a scalp target carrying a 2-point spread, i.e. 10-13% of the prize on every
attempt. Every MNQ cell is a disaster (PF 0.56-0.75, t to &minus;13). Fixed point
brackets must be denominated per market or they quietly become ten different strategies.</p>
<h3>The Asia gold entry, re-priced as MGC brackets</h3>
<div class="tbl-wrap"><table>{HEAD}<tbody>{b_asia}</tbody></table></div>
<p>These look exciting &mdash; +20pt RR 1:1 shows PF 1.374, t +3.46, halves agreeing
1.36/1.39 &mdash; and the honest reading is that <strong>they re-derive a known result
rather than find a new one</strong>. At +20 points, 56% of trades still exit on the
16:00-NY clock: the bracket is wide enough to mostly not bind, so the cell converges
toward the round-8/9 benchmarks (deployed 2R/clock 1.320, t +2.54; no-stop/clock 1.450,
t +3.42) and lands between them. A $200-risk, $200-target MGC bracket on the Asia entry
is a perfectly reasonable way to <em>express</em> the strategy on futures &mdash; roughly
equivalent to a wide stop &mdash; but it adds nothing beyond what the stop-width gradient
already established, and the deployed configuration stands.</p>
</section>

<section>
<h2><span class="n">04</span>The volume-profile value-area reversion</h2>
<p class="lede">Profile over a completed window (prior RTH / overnight / prior 24h), 70%
value area from the POC out; breakdown through the edge on declining volume, reclaim on
growing volume, stop at the extreme, targets POC / opposite edge / EoD. Tick-volume
caveat applies to every volume gate. 72 cells; per-market summary:</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Mkt</th><th class="l">Volume gates</th><th>cells</th>
<th>median PF</th><th>best PF</th><th class="l">best cell</th></tr></thead>
<tbody>{vp_sum}</tbody></table></div>
<p>Not deployable anywhere &mdash; but two things deserve their ink. First, the
<strong>absorption gates improve the raw fade on nearly every market and window</strong>
(NDX 1.08&rarr;1.21, RTY 0.88&rarr;1.02, SPX 0.88&rarr;1.03 on matched cells): a
mechanism-consistent, cross-market direction that random filters do not produce, even
through the fog of tick volume. Second, exactly one cell passes the both-halves sign
check above water: gold, overnight profile, gated, opposite-edge target &mdash;
PF {watch["pf"]:.3f} (n={watch["n"]}, IS {watch["is_pf"]:.3f} / OS {watch["os_pf"]:.3f},
t {watch["t"]:+.2f}). At that t it is a watch-list entry, not a strategy.</p>
<div class="verdict"><div class="head">Round-11 disposition</div>
<p>Nothing changes the deployed strategy. The ORB filters and the EMA-pullback join the
graveyard; the point-target panel is answered (viable as an MGC expression of the Asia
entry, structurally poor on MNQ, dead on every NY entry); and the watch list gains its
second entry: the gated volume-profile reversion on gold&rsquo;s overnight profile,
alongside the CISD short. Both are re-tests for when new gold data accumulates &mdash;
neither touches live capital.</p></div>
</section>

<section>
<h2><span class="n">05</span>Methods</h2>
<ul>
<li>All entries at bar closes; conservative stop-first path walks; causal features
(prior-session ATR, rolling 1-year ATR median, 14-session volume baselines) throughout;
value areas computed only from completed windows.</li>
<li>The 2-minute chart does not exist in this data; its EMA was mapped to the identical
smoothing span on 5m bars and labelled as such. Point-target fills inside 5-minute bars
use the same conservative both-touch rule as everywhere else.</li>
<li>230 cells this round, all reported; the only positive-t families are re-derivations
of the validated Asia entry. No significance claimed for anything new.</li>
</ul>
<footer><p>Round 11. Engines: <code>mkts.py</code>, <code>run_orb_filters.py</code>,
<code>run_ema_pullback.py</code>, <code>run_vprofile.py</code>. Results:
<code>orb_filters.json</code>, <code>ema_points.json</code>, <code>vprofile.json</code>.</p></footer>
</section>
</div>
"""
open("results/report10.html", "w").write(HTML)
print(f"written results/report10.html ({len(HTML):,} bytes)")
