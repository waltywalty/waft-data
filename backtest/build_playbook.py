"""The standalone playbook page: the deployed rule, its evidence, the risk
plan, the forward-test protocol, and the graveyard. Regenerate and republish
whenever a round changes any of it."""
CSS = open("report_style.css").read()
assert "{{" not in CSS
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap">')

HTML = f"""<title>Asia Gold Playbook</title>
{FONTS}
{CSS}
<div class="wrap">
<header>
<p class="eyebrow">Living document &middot; last updated 2026-08-26 &middot; after round 16</p>
<h1>The Asia gold playbook</h1>
<p class="standfirst">One strategy survived nine rounds of testing: the Asia-open
range breakout on gold, gated by the gold/AUDUSD correlation regime. This page is the
complete rule, the honest numbers behind it, the risk plan, and the list of everything
that was tried and buried. Posture: <strong>forward-test, don't size up.</strong></p>
<div class="provenance">
<span>instrument <b>spot XAUUSD / CFD</b></span>
<span>backtest <b>652 trades &middot; 2020&ndash;2025</b></span>
<span>PF <b>1.320</b></span><span>t <b>+2.54</b></span>
</div>
</header>

<section>
<h2><span class="n">01</span>The rule</h2>
<p class="lede">Six steps, in order, every trading day. The steps are a sequence:
each one gates the next.</p>
<div class="verdict"><div class="head">Step 1 &middot; The regime filter (this IS the edge)</div>
<p>Compute the 20-day rolling correlation of gold and AUDUSD daily log returns using
only <em>closed</em> daily bars through yesterday. Trade only when it is
<strong>&le; 0.5</strong>. If the AUDUSD feed is unavailable, skip the day entirely
&mdash; unfiltered the system loses (PF 0.85). The filter keeps roughly 60% of days;
a live skip-rate far from ~38% means the calculation is wrong. Mechanism: low
correlation marks the days gold trades on its own flows rather than as a dollar proxy
&mdash; the days breakouts follow through. Round 8 confirmed the ordering from the
mirror side: fading breakouts is <em>worst</em> on exactly these days. Round 15&rsquo;s
session split locates the payoff: the Asia leg contributes ~17% of the edge, ~70%
accrues between the London open and the NY morning &mdash; Asia sets the direction,
London and New York pay it.</p></div>
<div class="verdict"><div class="head">Step 2 &middot; The range</div>
<p>At 09:30 Hong Kong (01:30 UTC &mdash; HK has no DST; on MetaTrader the broker hour
must be derived at runtime, never hardcoded) form the high/low of the first
<strong>60 minutes</strong>.</p></div>
<div class="verdict"><div class="head">Step 3 &middot; The entry</div>
<p>The first subsequent 60-minute candle to <em>close</em> beyond the range enters in
that direction at its close. One trade per day, first break only. <strong>No entry
after 08:00 London</strong> &mdash; the late entries lose on their own (PF 0.951).</p></div>
<div class="verdict"><div class="head">Step 4 &middot; The stop</div>
<p>2&times; the range width from entry. This is a drawdown-control choice, not an edge
choice: no stop at all backtests better (PF 1.450 vs 1.320) and every tightening costs
profit factor on a smooth gradient. Never tighter than 2&times;: a 1&times; stop is hit
on 72% of trades and doubles slippage sensitivity.</p></div>
<div class="verdict"><div class="head">Step 5 &middot; The exit</div>
<p>Flat at <strong>16:00 New York</strong>, same day, no exceptions. Round 9 closed
this question: the average trade is underwater for its first three hours, then accrues
monotonically into the NY close, and the drift dies overnight. No clock, target, trail,
or breakeven variant beats it &mdash; the two that beat its profit factor compound to
barely 60% of its equity, because they scratch trades that go on to win.</p></div>
<div class="verdict"><div class="head">Step 6 &middot; The size</div>
<p><strong>Flat 1% of equity per trade</strong>, sized off the actual 2&times;-range
stop distance. Round 9 closed this question too: losing streaks carry no usable
information (p = 0.12), and every streak-keyed ladder delivers a worse
drawdown-per-return price than a flat fraction. If more aggression is ever wanted, the
honest dial is the flat percentage &mdash; knowing flat 2% has historically meant a
~42% median drawdown across orderings.</p></div>
</section>

<section>
<h2><span class="n">02</span>What the numbers honestly say</h2>
<div class="stats">
<div class="stat"><div class="k">trades / win rate</div><div class="v dim">652 &middot; 40.2%</div></div>
<div class="stat"><div class="k">profit factor</div><div class="v pos-t">1.320</div></div>
<div class="stat"><div class="k">backtest CAGR @1%</div><div class="v dim">+20.7%</div></div>
<div class="stat"><div class="k">planning CAGR</div><div class="v dim">+12.8%</div></div>
</div>
<p>The +20.7%/yr figure (2020-2025, max DD 16%) includes gold&rsquo;s exceptional
2024-25; the 2020-23 half gives ~+12.8%/yr at similar drawdown &mdash; <strong>plan on
the smaller number</strong>. The rule passes a correlation-aware max-statistic
randomization test (p = 0.036) but fails Bonferroni at any plausible count of tests
this repo has run. That is exactly the boundary between &ldquo;probably real&rdquo; and
&ldquo;proven&rdquo;, and it is why the posture is forward-test-don&rsquo;t-size.
Expect losing months; the filter signal&rsquo;s half-life is ~27 days &mdash; judge
monthly, never daily.</p>
<p>Streak expectations, for nerve-holding: losing streaks average 2.3 trades, one in
ten reaches 5, and the historical record is 9 (with 8 right behind it) &mdash; milder
than the ~11 a fair coin would produce at this win rate. A 9-loss streak at 1% risk is
a ~9% dent: designed to be survivable.</p>
<p><strong>Signal droughts are equally normal.</strong> Stand-aside stretches
(correlation above 0.5) average 12 trading days, hit 2+ weeks about four times a year
(20 times in the 2020-2025 sample), and the record is 61 trading days &mdash; twelve
weeks of no trades. Monthly trade counts run 11.7 on average with a historical minimum
of 1; a near-empty month happens roughly annually. A quiet chart is the filter working,
not the strategy failing. The threshold is not a dial to relieve boredom: the marginal
trades between 0.5 and 0.6 run PF 1.07 at t +0.04 &mdash; coin flips that pay spread
&mdash; and the 0.6-0.7 band is net negative.</p>
</section>

<section>
<h2><span class="n">03</span>Execution</h2>
<ul>
<li><strong>Platform:</strong> MT5 (never MT4 &mdash; the filter reads a second symbol
in the tester). <code>backtest/mt5/AsiaOpenGold.mq5</code> v1.20 implements the exact
rule; verified by DST transliteration vs the IANA database (0/2,557 mismatches), a
C++ type-check, and an independent Python replay reproducing all 652 trades. First
MetaEditor compile may still need a trivial fix.</li>
<li><strong>Instrument:</strong> spot/CFD by default. MGC micro futures need
roughly &ge; $20-25,000 before the rule can be expressed at sane risk (integer
contracts; see below), else granularity turns the strategy into a calm-day-only
distortion.</li>
<li><strong>MGC bracket expression (round-11 option):</strong> on a futures account
that clears the size bar, the same entries can be run as a &plusmn;15-20-point MGC
bracket (&asymp;$150-200 risk and target per contract, RR 1:1) with the 16:00-NY
flat as the fallback &mdash; backtests in line with the deployed exits
(PF 1.15-1.37 across the bracket family) because the bracket is wide enough to
bind on under half of trades. It is an <em>expression</em> of the rule, not an
upgrade: fixed points do not scale with gold&rsquo;s price or volatility the way
the 2&times;-range stop does, so re-check the bracket width yearly against
~0.5-0.8% of spot.</li>
<li><strong>Now:</strong> demo 4&ndash;8 weeks (~40 trades). Reconcile every trade and
every skipped day against the rule; a skip-share far from ~38% means the filter is
miscomputed.</li>
<li><strong>Kill criteria (decided in advance):</strong> stop if live drawdown exceeds
~25% at 1% risk (1.5&times; the backtest max), or if after ~150 live trades the profit
factor sits below 1.0.</li>
</ul>
</section>

<section>
<h2><span class="n">04</span>The forward test that earns changes</h2>
<p class="lede">Nothing changes the deployed rule on backtest evidence &mdash; the
sample is mined out. The EA logs two candidates per trade to
<code>AsiaOpenGold_forward_v2.csv</code> (one line per trade, written after the exit; scored with <code>analyze_forward.py</code>); live data decides.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Candidate</th><th class="l">Backtest claim</th><th class="l">Fires on</th><th class="l">Promote if</th></tr></thead>
<tbody>
<tr><td class="lbl">Opening-range relative volume &ge; 1.25</td>
<td class="lbl">PF 1.843 vs 1.320, halves agree</td><td class="num">~20% of trades</td>
<td class="lbl">gated subset beats the base after 6-12 months</td></tr>
<tr><td class="lbl">Prior session was an inside day</td>
<td class="lbl">PF 1.616, n=94, halves agree</td><td class="num">~14% of trades</td>
<td class="lbl">same</td></tr>
<tr><td class="lbl">London 08:00 add to a winner (round 12)</td>
<td class="lbl">standalone PF 1.592, t +2.98, halves 1.24 / 2.27 &mdash; pre-registered,
derived from the drift structure itself</td><td class="num">~50% of trades</td>
<td class="lbl">EA v1.20 logs it; score with <code>analyze_forward.py</code>, same 6-12-month bar</td></tr>
</tbody></table></div>
<p>Round 12 also settled the mechanism&rsquo;s geography: the identical construction
moved to the London open is dead (PF 0.87-0.91, both halves), completing the gradient
Asia (works) &rarr; London (dead) &rarr; NY (dead). The edge is specifically the
illiquid Asia open on regime-filtered days &mdash; not &ldquo;opening ranges&rdquo; in
general. A 09:30-NY re-entry in the Asia direction is the only NY-session construction
in twelve rounds with a positive full-sample t (best cell +1.80, in-profit + 2R stop,
halves 1.09 / 1.67) &mdash; a weaker sibling of the London add, listed here for the
record, not for capital.</p>
<p>If the gated subsets do not beat the unconditioned strategy on data no search has
touched, the leads die &mdash; the fate of most subgroup findings, and the log will say
so honestly.</p>
</section>

<section>
<h2><span class="n">05</span>The graveyard</h2>
<p class="lede">Every one of these was tested to the same standard and failed. They are
listed so they stay buried.</p>
<ul>
<li>Raw breakouts without the filter &mdash; 11 of 12 configurations lose (round 1).</li>
<li>Sweep / reclaim / &ldquo;Judas&rdquo; entries &mdash; adversely selected, losing
<em>before</em> costs; found independently twice on gold (rounds 2, 8) and again on
three indices (round 9).</li>
<li>Same-day AUDUSD agreement (round 2); CNY as a filter &mdash; a degraded dollar
sensor (round 5).</li>
<li>The NY open on gold, both directions &mdash; 123-cell fade grid and 117-cell
follow grid, both dead; the confirmation candle consumes the move (rounds 7-8).</li>
<li>Band mean reversion at every width incl. 2.6&sigma; &mdash; the effect is worth
exactly one spread (round 8); same on SPX/NDX/RTY (round 9).</li>
<li>The NY open on the indices &mdash; 84 cells, 15 filter cuts, best t +0.48; the
Zarattini anomaly replicates gross and dies at the spread (round 9).</li>
<li>Tight stops, ATR-fraction stops, NR7 conditioning, prior-day-range vetoes,
first-bar-direction entries (round 8).</li>
<li>Exit &ldquo;improvements&rdquo; &mdash; targets, trails, breakeven moves, overnight
holds (round 9).</li>
<li>Streak-keyed sizing ladders &mdash; ordering luck; flat risk dominates (round 9).</li>
<li>Supertrend+RSI in NY hours &mdash; loses before costs on every market and
parameter set, t-statistics to &minus;52; the script&rsquo;s trend filter is also
inverted by Pine&rsquo;s supertrend direction semantics (round 10).</li>
<li>ICT CISD reversals in the TJR (NY-vs-London) and strict 10-11 Silver Bullet
windows, on gold and all three indices (round 10) &mdash; the fourth and fifth
independent session-sweep constructions to fail here.</li>
<li>Volatility and volume filters on the NY ORB &mdash; the strong-breakout cuts
produced the repo&rsquo;s sharpest in-sample mirage (gold IS t +2.32 &rarr; OS PF 0.77);
on the indices the surviving direction inverts the intuition and still loses (round 11).</li>
<li>The 30m-range / 10m-confirm / EMA-pullback continuation entry &mdash; better fills
than the raw break, still inside the spread; prior-hour-level exits worst of all
(round 11).</li>
<li>Fixed 15-20-point brackets on NY-session entries &mdash; dead everywhere, and
structurally terrible on MNQ where 15 points is 0.35% against a 2-point spread. On the
Asia gold entry a &plusmn;20pt MGC bracket works (PF 1.37) because it barely binds:
it re-derives the wide-stop result, adds nothing (round 11).</li>
<li>Alternative correlation partners &mdash; silver, a synthetic dollar index, EUR, JPY,
GBP, CHF, CAD, CNY, WTI, the S&amp;P 500 and 10-year yields, 416 cells: every FX gate
re-selects 88&ndash;92% of the AUD gate&rsquo;s days, every rescue of AUD-skipped days
flips sign between halves, and the best stacked gate is matched by random regime series
(max-stat p 0.21 / 0.30). One macro state, one gate; no frequency exists beyond it
(round 13).</li>
<li>Eyeballed chart patterns, round 14: the Asia-range &ldquo;ping-pong&rdquo; (tap one
line, tap the other) is a real 64% statistic &mdash; 67&ndash;68% on calm and
stand-aside days, as the eye claimed &mdash; but fading the first tap loses in every
configuration; the path runs too far before reverting. The &ldquo;magnet&rdquo; premise
(range line confluent with a prior high/low attracts price) is measurably false:
confluent and non-confluent lines get re-crossed identically (5.43 vs 5.43 per line).
The pattern was real; the base rate owned it.</li>
<li>The researched battery, round 15: intraday momentum (Gao/Baltussen last
half-hour) sign-flipped on 20 years of our index data; turn-of-month days earn
exactly the all-days mean; trend-sign overlays on the gold rule have no gradient;
gap-fill base rates replicate (82&ndash;87% small-gap fills) and the fade still
loses everywhere; pre-FOMC drift dropped a priori as documented dead. 38 cells,
zero survivors.</li>
<li>The Hang Seng home-session range (round 15b) &mdash; the gold construction on
HSI&rsquo;s own 09:30&ndash;10:30 window: breakout arm dead (PF 0.87) as the
price-discovery law predicted, fade arm worse; Nikkei/A50/HSCEI/CSI300 correlation
gates rescue nothing. The pre-open fade survived to the watch list instead.</li>
<li>The round-16 hunt, ~58 cells: Asia-session ORB transplanted to US indices dies
both directions (t to &minus;12; away-session chop taxes breakout AND fade); Connors
RSI2/IBS daily mean reversion is mostly equity drift in bursts (random long-burst
null t +2.9, p 0.125); gold/silver ratio reversion, IBS-on-Asia, Unger raw
session-breakout, 80-20 fades all dead; two refereed anomalies (Nikkei open vs
prior-day SPX, Gotobi USDJPY fix flow) replicate descriptively and sit inside the
spread. The one survivor went to the watch list.</li>
</ul>
<div class="note"><p><strong>Watch list (not tradeable, not forgotten):</strong>
(1) the gold CISD-to-EoD reversal (09:00-10:00 ET range, entry against the first break
on a close back through the driving candle run, held to the close) &mdash; PF 1.068 net,
t +0.52, zero-cost 1.20, strength in the short side (PF 1.247, post-hoc) and in 2024-25;
(2) the gated volume-profile reversion on gold&rsquo;s overnight profile (breakdown
through a value-area edge on declining volume, reclaim on growing volume, target the
opposite edge) &mdash; PF 1.045, the round-11 grid&rsquo;s only both-halves survivor
(1.07/1.03) at t +0.31, with the absorption gates improving results directionally on
every market. Both fail today&rsquo;s standard; both are re-tests for when 2026 gold
data accumulates. Neither touches the deployed rule.
(3) the HSI pre-open fade (round 15b): when the 09:15&ndash;09:30 HKT futures-only
bar moves &ge;0.3&times; ATR14, fade it at the 09:30 cash open, stop 0.5&times; the
pre-open range, hold to 16:00 HKT &mdash; PF 2.02, t +1.60, both halves positive,
max-stat p 0.030, cost-robust to 15 points; but n=43. Watch bar pre-committed:
re-test at 80+ trades on the live feed; promote at PF &ge;1.4 with both halves
positive; no parameter may move.
(4) Turtle Soup long on JP225 (round 16): a 20-day-low undercut reclaimed the same
day &rarr; long at close, exit +5 sessions &mdash; 76% win, PF 4.01, t +3.38, both
halves positive, battery max-stat p 0.027; but n=33. Re-test when the live feed
doubles the sample; promote at PF &ge;1.5 with both halves positive; frozen.</p></div>
<div class="note"><p><strong>One sentence:</strong> trade the Asia open only when gold
is not a dollar proxy, hold to the New York close with a wide stop at flat 1% risk, and
let the forward log &mdash; not another backtest &mdash; earn every change.</p></div>
</section>

<section>
<h2><span class="n">06</span>The record</h2>
<p>Full round-by-round write-ups live in <code>backtest/results/report*.html</code>
(index in <code>backtest/README.md</code>), research notes in
<code>backtest/reference/</code>. This page supersedes nothing; it summarizes
everything.</p>
<footer><p>Maintained alongside the research branch. Update cadence: whenever a round
changes the rule, the risk plan, or the graveyard.</p></footer>
</section>
</div>
"""
open("results/playbook.html", "w").write(HTML)
print(f"written results/playbook.html ({len(HTML):,} bytes)")
