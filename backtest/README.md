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
