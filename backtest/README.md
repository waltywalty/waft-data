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

## Data

Five-minute spot XAUUSD, 350,903 bars, 2020-08-21 to 2025-08-01. Timestamps confirmed
to be UTC empirically (the intraday volatility peak shifts by exactly one hour across
US daylight-saving boundaries while staying fixed in UTC). Prices agree with an
independent broker feed to a median $0.17 over 35,480 overlapping bars.
