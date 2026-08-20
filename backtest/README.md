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
