# XAUUSD opening-range breakout — 09:30 HKT

Backtest of the Asia-open breakout: form a range from the first 5/15/30 minutes after
09:30 Hong Kong time (01:30 UTC), enter on the first candle to *close* beyond it, hold
to a fixed clock time in the London session.

## Running it

```bash
pip install pandas numpy scipy
./fetch_data.sh          # ~35 MB, not committed
python3 validate_data.py # integrity + empirical timezone identification
python3 cross_check.py   # price cross-validation vs an independent feed
python3 run_grid.py      # the 12 configurations specified
python3 bias.py          # does the breakout capture the day's direction?
python3 bias2.py         # ... and is that direction forecastable or already realised?
python3 entries.py       # alternative entry mechanics
python3 filters.py       # confluence filters, in-sample vs out-of-sample
python3 filters2.py      # filter consistency screen
python3 final_tests.py   # risk overlays + randomisation null
python3 stress_best.py   # stress the best configuration found
python3 summarize.py     # writes results/summary.json
python3 build_report.py  # writes results/report.html
```

## Headline result

Eleven of the twelve specified configurations lose money net of a $0.30 round trip.
The breakout does identify the day's direction (60% of days for a 30-minute range,
measured from the 09:30 open) but essentially all of that is the move already made by
the time the confirming candle closes — measured from the actual fill the hit rate is
51%. No confluence filter survived an in-sample/out-of-sample split.

Full write-up: `results/report.html`.

## Round two — sweep entries and the AUD filter

```bash
python3 audusd_align.py     # empirical timezone identification for both AUDUSD feeds
python3 run_sweep_grid.py   # bias -> liquidity sweep -> reclaim, 16 variants x 7 exits
python3 run_structure.py    # the sweep used as an exit instead of an entry
python3 run_audusd.py       # AUDUSD confluence: same-day agreement and correlation regime
python3 audusd_stress.py    # placebo, confound controls, within-year tests
python3 validate_filter.py  # independent re-implementation + generalisation checks
python3 summarize2.py && python3 build_report2.py
```

The sweep entry gives a far better fill than the breakout close but still loses: requiring a
sweep selects for the days the bias failed (profit factor 0.61 on days that sweep versus 1.93
on days that never do). Same-day AUDUSD agreement with the gold bias is not predictive
(p = 0.20). The 20-day gold/AUDUSD correlation *regime* is: trading only when it sits at or
below 0.5 lifts the profit factor from 1.13 to 1.34 and the t-statistic from 1.14 to 2.76,
generalises to 11 of 12 other configurations, is monotonic in the threshold, holds in both
in-sample and out-of-sample halves, and survives a block-shuffle placebo at p < 0.001.

Write-up: `results/report2.html`.

## Data

Five-minute spot XAUUSD, 350,903 bars, 2020-08-21 to 2025-08-01. Timestamps confirmed
to be UTC empirically (the intraday volatility peak shifts by exactly one hour across
US daylight-saving boundaries while staying fixed in UTC). Prices agree with an
independent broker feed to a median $0.17 over 35,480 overlapping bars.

## Round three — thresholds and position sizing

```bash
python3 thresholds.py        # correlation cut-off x rolling-window grid
python3 portfolio.py         # $2,000 account, risk-managed vs all-in
python3 portfolio_stress.py  # stop width, slippage, path dependence, all-in autopsy
python3 summarize3.py && python3 build_report3.py
```

The filter is robust to both of its parameters: every populated cell of the
window x threshold grid (10-90 day windows, cut-offs 0.0-0.8) has a profit factor
above 1.0, and the cut-off curve is monotonic from 0.6 down to 0.0. The strongest
t-statistic is at a 0.4 cut (t = 3.01, n = 569).

Sizing dominates. From $2,000 over five years: risking 1% per trade with a 2x-range
stop returns 17.8% a year with a 20% drawdown, versus buy-and-hold gold at 11.6%
and 20%. All-in at 20:1 ends higher but passes through $153 on the way — 99.98%
below its own peak — and gold's worst adverse intraday excursion in the sample
(5.80%) would have zeroed that account outright. Tight stops leak badly: a 1x-range
stop is hit on 72% of trades and fifty cents of slippage costs more than half the
result, while a 3x stop barely notices.

Write-up: `results/report3.html`.

## Round four — MGC micro futures vs spot

```bash
python3 futures_basis.py  # MGC Dec-26 vs the relay's own spot quotes: basis + tracking
python3 run_mgc.py        # the rule costed as MGC across six account sizes
python3 build_report4.py
```

Rounds one to three all used spot XAUUSD, where position size is continuous. MGC is
10 troy ounces per contract: about $21,800 of notional, ~$1,300 initial margin at 6%,
and ~$108 of risk against a 2x-range stop. On a $2,000 account one contract risks 5.4%
and ties up 65% as margin, so a 1% risk target takes **zero** trades and every risk
level that can be traded loses money. MGC needs roughly $25,000 to express the rule and
$50,000 before granularity costs nothing; at $50,000 it finishes ahead of spot.

Skipped trades are not a random sample - a trade is skipped when its stop is widest, so
a small futures account trades a systematically calm-day-only version of the strategy.

The signal itself carries over: the basis averaged $0.48 (0.011% of price) and futures
vs spot tracking converges to 0.94 correlation / 0.95 slope at an 8-hour horizon, with
the shortfall at 30 minutes explained by feed jitter rather than decoupling. Tick
rounding to the $0.10 grid is a non-event ($0.002/oz).

Write-up: `results/report4.html`.

## Round five — the yuan as a second reference

```bash
python3 run_cny.py           # CNY vs AUD head to head, cross-tab, joint regression
python3 cny_window.py        # window sweep for CNY
python3 cny_incremental.py   # does CNY add anything to AUD?
```

Tested on the hypothesis that Chinese demand should make CNY a useful regime
reference. It does carry the same kind of signal - the gold/CNYUSD correlation
gradient runs the same direction (PF 1.128 unfiltered -> 1.378 at the tightest
cut) - but weaker than AUD at every matched quantile, and it never clears
significance without a best-of-grid window pick.

The 2x2 cross-tab looks additive (AUD-low + CNY-low gives PF 1.436, both high
gives 0.623) but neither incremental test is significant: CNY inside the
AUD-filtered set gives p = 0.12, and in a joint regression AUD survives
(t = -2.58) while CNY does not (t = -1.12). CNY's apparent out-of-sample
validation is an artefact - its 90-day filter keeps 96% of days in 2024-25, so
it is barely filtering there, while AUD keeps a stable 57% -> 72% and lifts in
both halves.

Likely reason: the filter measures whether gold is trading as a dollar proxy,
not Chinese demand. CNY is managed (daily sd 0.271% against AUD's 0.676%, and
5.8% of days show no change at all), so it is a degraded dollar sensor. The
right instruments for the China thesis would be the Shanghai Gold Exchange
premium over London, or offshore CNH - neither reachable from this environment.

## Round six — MetaTrader deployment

```bash
python3 mt_fidelity.py   # daily-close convention, correlation staleness, DST, swap
python3 deployable.py    # the exact EA configuration, scored honestly
python3 build_report5.py
```

The rule survives every MetaTrader-specific change tested. Recomputing the filter from
broker EET daily bars instead of the research convention gives PF 1.343 vs 1.337 (the
three conventions agree on 94% of days), and computing BOTH sides from broker bars gives
1.537 kept vs 0.740 excluded over the window where two feeds exist. A correlation lagged
one to three days still works; it only sags around five.

It must be MT5, not MT4: the edge is a filter that reads AUDUSD while trading gold, and
MT4's Strategy Tester cannot faithfully backtest a second symbol.

Deployable configuration (60m range from 01:30 UTC, 2x-range stop, corr <= 0.5, exit
16:00 NY): 745 trades, 158/year, 10.7h average hold, stopped 51%, win 40%, PF 1.270,
+$1.39/oz, t = 2.26. On $2,000 at 1% risk that is 17.5%/yr with a 20% drawdown - but the
2020-23 half alone gives 9.6%/yr at the same drawdown, which is the more honest planning
number.

Two traps: 09:30 HKT is 03:30 broker time in winter and 04:30 in summer, so a hardcoded
server hour is wrong half the year; and if the AUDUSD feed is missing the EA must skip
the day rather than trade unfiltered (0.85 profit factor unfiltered vs 1.34 filtered).

Write-up: `results/report5.html`.

## Reference material

`backtest/reference/` holds the loop-engineering framework document plus our assessment of
it and a checklist for future strategy work. `loop_metrics.py` applies its three metrics to
this rule: ICIR +0.340 (against +0.041 for the raw breakout direction alone — an independent
confirmation that the edge is the filter, not the breakout), signal half-life 27 days against
a 0.45-day hold, and a Bonferroni correction that the rule **fails** at any plausible test
count even though the correlation-aware randomisation test passes it.

## MT5 expert advisor

`backtest/mt5/AsiaOpenGold.mq5` implements the deployable configuration. See
`backtest/mt5/README.md` for install, tester settings, and the numbers a correct run should
reproduce.

## Round seven — the New York opening range

```bash
python3 run_ny.py        # 80 configurations: 4 range lengths x 10 exits x filter on/off
python3 run_ny_sens.py   # confirmation timeframe, deadline, stops, costs, filter generalisation
python3 build_report6.py
```

Tested the 09:30 ET opening-range breakout with five clock exits and five liquidity targets
(previous day, Asia, London, prior hour, measured move). **It does not work.** With a stop at
the far side of the range, 1 of 39 configurations clears a 1.0 profit factor (median 0.899);
**with no stop at all, 0 of 39** (median 0.847); with the AUD filter, 12 of 39 (median 0.974).
The best t-statistic across all 117 scored cells is +0.70 - lower than a correlated search this
size over pure noise would normally produce.

Selecting the strongest cells on pre-2024 data only and reading 2024-25 gives a median
out-of-sample profit factor of 0.954, against 0.930 for the whole population: in-sample
strength buys no out-of-sample advantage whatsoever.

The mechanism is the useful part. New York breaks *hold* far better than Asia ones - 45%
whipsaw against 79% - but there is nothing left to capture: after a 15-minute range and a
5-minute confirmation, price has already moved $4.74 from the open and the average forward move
is +$0.10, against Asia's +$1.56. At zero cost the strategy runs a 1.030 profit factor, so the
spread is the entire story.

Finer confirmation is monotonically better on a 15-minute range (5m 0.892, 15m 0.835, 30m 0.799,
60m 0.722), which brackets the untestable 1-minute case at roughly 0.92-0.94 - better, still
losing.

The AUD correlation filter improved all 39 cells, but those cells share most of their trades;
tested properly at the trade level only 1 of 5 configurations reaches significance and the
continuous relationship is flat. It neither confirms nor refutes round two.

**Four defects were caught and fixed during this round.** Two by hand (the first engine
returned PF 2.479 at t = 12): FX sessions labelled by start date rather than end date, so
"previous day" ran to 17:00 ET *today*; and a pandas `.loc` slice inclusive of its right
endpoint, so the London window swallowed the first bar of the opening range.

Two more by a five-lens adversarial audit (`ny-orb-audit` workflow, 24 candidates, 22 refuted):
the exit path used the same inclusive-slice pattern, giving every trade five extra minutes of
stop and target exposure after it should have closed; and the out-of-sample panel ranked
candidates by their *whole-sample* t-statistic before declaring post-2024 the holdout, so the
selector had already seen it. The first was immaterial, the second flattered.

`build_levels()` now carries a lookahead audit, and `run()` takes `use_stop` so the grid's
treatment of the protective stop is explicit rather than implied.

Write-up: `results/report6.html`.

## Round eight — three strategies from the wild, and a fade

```bash
python3 run_ny_fade.py   # 123 cells: fading the first NY break, symmetry-proven engine
python3 run_meanrev.py   # the "2.6 sigma" pullback on its full gradient, 5m/15m/60m
python3 run_judas.py     # daily-structure Judas sweep: 45 cells + funnel + variations
python3 run_judas2.py    # canonical-ICT addendum: killzones, PDH/PDL bias, deep sweeps
python3 run_adapt.py     # practitioner adaptations onto the Asia ORB + gates on the fade
python3 build_report7.py
```

Round seven's parting question — if NY breaks hold but leave nothing, is the money in
fading them? — answered: **no**. The fade engine is proven to be the exact mirror of the
follow engine (1,174 trades, P&L negated to 0.00e+00), and the fade loses $0.13/oz
*before* costs. The correlation filter's ordering inverts exactly as its mechanism
predicts (fades are worst on the low-correlation days the Asia strategy trades), and the
seductive corr>0.5 corner collapses under honest pre-2024 ranking (OS median 0.655).

Three research sweeps (56 sources: Zarattini/Aziz and replications, Crabel, the Bollinger
canon, Belkhayate, the OU-falsification study, ICT and Turtle Soup) fed mechanical specs
for the user's three named strategies:

* **2.6-sigma pullback**: at zero cost, PF 1.006 — the reversion is real and worth exactly
  one spread. Negative net everywhere liquid; only n<=250 tails at 3.5 sigma clear 1.0.
  No practitioner gate (ADX regime, band-walk veto, news scrub, VWAP anchoring) finds a
  paying subset. The "trend gate is the strategy" claim fails on gold.
* **Judas sweep**: loses at zero cost (PF 0.735 gross) — adverse selection, not friction,
  replicating round two's sweep-entry verdict on an independent construction. 45-cell
  median PF 0.613; canonical killzones/PDH-PDL/deep-sweep refinements all move the right
  direction and all stay under water; honest OOS median 0.201 with two cells at 0.000.
  Our take-everything win rate (27.1%) matches the one independent mechanical ICT test
  in the literature (29.6%).
* **Asia-ORB adaptations** (50 tests on the exact deployed 652-trade set): Zarattini's
  tight-ATR-stops claim *reverses* on gold — a smooth gradient from 0.05xATR (PF 1.155)
  to no stop (PF 1.450), every step agreeing across halves. Two forward-test leads
  survive with both-halves sign agreement: top-quintile relative volume in the opening
  range (PF 1.843, t +2.54) and Crabel inside-day conditioning (PF 1.616, n=94). NR7,
  the prior-day-range veto and the first-bar-direction entry do not transfer. Nothing
  re-sizes the deployed configuration.

Research notes with all sources: `reference/strategy_research.json`.
Write-up: `results/report7.html`.

## Round nine — exits, streaks, sizing, and the index expedition

```bash
python3 run_exits.py           # exit families on frozen deployable entries + hold curve
python3 run_exit_portfolio.py  # equity-curve comparison of the PF-improving exits
python3 run_sizing.py          # streak statistics, dependence tests, sizing ladders
./fetch_index_data.sh          # SPX/NDX/RTY intraday CFD data (not committed)
python3 index_data.py          # feed verification + unified 5m UTC caches
python3 run_nyidx.py           # 84 cells: four NY-open families x three indices
python3 run_nyidx_filters.py   # pre-registered rescue filters on the Zarattini spec
python3 build_report8.py && python3 build_playbook.py
```

**The exit question is closed.** The average trade is underwater for its first three
hours, accrues monotonically into the 16:00-NY close, and the drift dies overnight
(PF 1.05, halves disagree). Among ~20 challengers, none beats the clock's expectancy;
the two that beat its profit factor (breakeven at +1 range, 2x-range trail) compound
$2,000 to $3.9k/$3.7k vs the clock's $6.1k at identical 1% risk - they scratch trades
that go on to win the NY session.

**Streaks are coin-flip-ordinary.** Mean losing streak 2.34, longest 9 (next 8) vs
~10.8 expected from iid chance. P(win|prev loss) 42.8% vs 36.4% after a win - the
ladder's direction, but chi2 p=0.12. Loss-ladder sizing over 2,000 shuffled orderings:
median outcomes comparable to flat 2% with far fatter drawdown tails (x2-cap-8%:
median DD 69%, P(DD>50%) 96%). Sizing stays flat.

**The NY open on SPX/NDX/RTY: real gross, dead net.** Twenty years of index CFD data
(two feeds, timezone-verified by the 09:30-ET volatility step both seasons, feeds
agreeing to +0.007%). 84 cells across the Zarattini first-bar spec, ORB follow/fade,
Judas sweeps (open and pre-open), and open-hours mean reversion: zero cells with t > 0.
The Zarattini anomaly replicates gross on all three indices (zero-cost PF 1.13-1.20,
n≈4-5k each) and is fully consumed by a realistic spread - exactly the independent
replication's caveat. Rescue filters fail: tick-volume rvol makes SPX/NDX worse;
gap-alignment's least-bad cut runs against the folklore at t +0.48. The combination
condition ("find a strong NY strategy first") is not met; the portfolio stays gold-only.

Write-ups: `results/report8.html` (round 9) and `results/playbook.html` (the living
playbook).

## Round ten — the TradingView scripts

```bash
python3 run_tv.py         # CISD reversal (Venom/Silver Bullet/TJR windows) + Supertrend+RSI
python3 build_report9.py  # results/report9.html
```

Four user-supplied Pine scripts, extracted to mechanical rules and run on XAUUSD, SPX,
NDX, RTY (72 cells). The Supertrend+RSI strategy is the worst signal this repo has
measured: it loses BEFORE costs on every market and parameter set (t to -52 on 33k-trade
samples), and its trend filter is inverted as written (Pine's ta.supertrend returns
direction -1 for an uptrend; the script trades stDir == 1 as "up"). The ICT CISD
reversal is dead net everywhere except one watch item: gold, 09:00-10:00 range, entry
against the first break on a close back through the driving candle run, held to the
close - PF 1.068 (t +0.52), zero-cost 1.20, strength in the shorts (PF 1.247, post-hoc)
and in 2024-25. Fails the both-halves standard; parked on the watch list for a re-test
when 2026 data accumulates. The TJR (NY-vs-London) window is the fourth independent
session-sweep construction to fail here. Playbook graveyard and watch list updated.

Write-up: `results/report9.html`.

## Round eleven — ORB filters, EMA pullback, point targets, volume profile

```bash
python3 run_orb_filters.py   # impulse / rvol / ATR-regime filters on the NY ORB
python3 run_ema_pullback.py  # 30m range + 10m confirm + EMA-pullback entry, plus
                             # the micro-futures 15/20-point RR 1-3 panel
python3 run_vprofile.py      # volume-profile value-area reversion, absorption gates
python3 build_report10.py
```

230 cells across four markets. **The ORB filters produced the repo's sharpest in-sample
mirage**: strong-volume/impulsive-range gold cells at IS t +2.32 collapsed to OS PF 0.77;
on the indices the surviving direction inverts the intuition (quiet, weak-volume opens
break out better - Crabel's compression) and still loses net. The EMA-pullback entry gets
better fills than the raw break and still dies inside the spread; prior-hour-level exits
are the worst tested. Fixed 15-20-point brackets: dead on every NY entry, structurally
terrible on MNQ (0.35% targets vs a 2-point spread, t to -13); on the Asia gold entry a
+/-20pt MGC bracket posts PF 1.374 / t +3.46 with halves agreeing - but 56% of trades
still exit on the clock, so it re-derives the wide-stop result between the deployed 2R
(1.320) and no-stop (1.450) benchmarks rather than finding anything new. The
volume-profile reversion is not deployable (population median OS 0.990) but the
absorption gates improve the raw fade on nearly every market, and gold's gated
overnight-profile cell is the grid's only both-halves survivor (PF 1.045, t +0.31) -
watch-list entry #2.

Write-up: `results/report10.html`. Playbook graveyard and watch list updated.

## Round twelve — derived strategies and the MGC option

```bash
python3 run_derived.py   # 10 pre-registered cells derived from the validated drift
```

Instead of importing another retail strategy, round 12 derived constructions from the
repo's own meta-findings (edges live where price discovery is slow; the Asia drift runs
to the NY close; interference only hurts). Results, all pre-registered:

* **London 08:00 add to a winner** (re-enter the Asia direction at the London open when
  the original trade is in profit): standalone PF 1.592, t +2.98, halves 1.238/2.265,
  n=323 — the strongest derived result to date; forward-test candidate #3 (needs an EA
  logging extension).
* **NY 09:30 re-entry**: the first NY-session construction in twelve rounds with a
  positive full-sample t (in-profit + 2R: PF 1.333, t +1.80, halves 1.088/1.670);
  weaker sibling of the London add, recorded not deployed.
* **London-open ORB** (the symmetry test): dead (PF 0.82-0.91, both halves agree),
  completing the price-discovery gradient Asia works / London dead / NY dead - the edge
  is the illiquid Asia open specifically, not opening ranges in general.

Playbook updated: MGC bracket expression added as an instrument option; forward-test
candidates now number three.

## Round 13 — alternative correlation partners (negative, and clarifying)

The commission: gate the same breakout on other macro partners — silver, a synthetic
dollar index, EUR, JPY, GBP, CHF, CAD, CNY, WTI, the S&P 500, 10-year yields — hoping
for more trades or more edge. Three pre-registered questions, 416 cells, all counted
(`run_corrpartners.py`, sources appended to `fetch_data.sh`):

* **Q1 (beat AUD?)** No. Every FX partner's best cell re-selects 88–92% of the AUD
  gate's days — the same macro state through a different window. Silver's best t
  (+2.82) sits on a jagged decile gradient; the grid-wide max-stat permutation gives
  p = 0.21.
* **Q2 (rescue AUD-skipped days?)** No. The 410 skipped trades are collectively dead
  (PF 1.020, t −0.33), and every partner's best rescue cell flips sign between halves —
  positive only in the 2024–25 bull. No frequency gain exists in this direction.
* **Q3 (stack a second gate?)** No. AUD∧CNY and AUD∧silver improve both halves, but a
  random circularly-shifted series ANDed onto the AUD gate matches them 30% of the
  time (p = 0.30) — selection, not signal — and stacking cuts frequency, the opposite
  of the goal.

Write-up: `results/report13.html`. Playbook graveyard updated; the deployed rule and
its drought expectations stand unchanged.
