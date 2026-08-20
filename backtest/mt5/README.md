# AsiaOpenGold — MT5 expert advisor

Implements the rule validated in `backtest/results/report5.html`.

**MT5 only.** The edge comes from a filter that reads AUDUSD while trading gold, and MT4's
Strategy Tester cannot faithfully model a second symbol. An MQL4 port would run live but
could never be verified.

## Install

1. Copy `AsiaOpenGold.mq5` to `MQL5/Experts/` in your terminal's data folder
   (File → Open Data Folder).
2. Compile in MetaEditor (F7).
3. Add **both** XAUUSD and AUDUSD to Market Watch, and let their **daily** history download
   fully — the filter reads 25 daily bars of each.

## Inputs that matter

| Input | Default | Notes |
|---|---|---|
| `InpAudSymbol` | `AUDUSD` | Must match your broker exactly: `AUDUSD.m`, `AUDUSD#`, … |
| `InpRangeMinutes` | 60 | 15 and 30 also tested positive; 60 was strongest |
| `InpRangeStartUtcH/M` | 01:30 UTC | = 09:30 Hong Kong, year round. Do not convert by hand |
| `InpCorrMax` | 0.50 | 0.40 tested slightly stronger (t 3.01 vs 2.76) |
| `InpStopRangeMult` | 2.0 | 1.0 is a trap: tight stops bleed to slippage |
| `InpRiskPercent` | 1.0 | 2% roughly doubles both return and drawdown |

## Backtest settings

- **Model: "Every tick based on real ticks."** The rule triggers on candle closes and carries
  an intrabar stop; "Open prices only" produces fiction.
- Period 2020-08-21 → 2025-08-01 to compare against the research.
- Use variable spread from real ticks. Entry is 01:30 UTC, a thin hour — modelling a fixed
  London-hours spread will flatter the result substantially.
- Deposit and leverage to taste; at $2,000 and 1% risk the position is ~0.02 lots.

## What a correct run should produce

Roughly **652 trades, 138 a year, ~40% win rate, profit factor near 1.32**, average hold
11.1 hours, stop hit on about half. If your numbers are far from these, suspect the time
offset or the spread model before suspecting the strategy.

Check the journal line printed at init:

```
Broker clock is UTC+3. 01:30 UTC = 04:30 server time.
```

That must say **03:30 in winter and 04:30 in summer** on a normal EET/EEST broker. If it
does not move across the March and October changeovers, the EA is reading the wrong hour
for part of the year.

## Design notes

- **Time.** Everything is computed in UTC. The broker's offset is derived at runtime from
  `TimeCurrent() - TimeGMT()` and **re-derived daily**, because EET→EEST shifts it. London
  and New York anchors use explicit EU and US daylight-saving rules, which differ by a few
  weeks each spring and autumn.
- **The 60-minute blocks are anchored on 01:30 UTC**, not on the hour, so they are built
  from M5 bars rather than the H1 series. Using H1 bars would place the range half an hour
  off and is the single easiest way to fail to reproduce the backtest.
- **The filter reads only closed daily bars** (index 1 and older), which is the
  lagged-one-day version that was validated. It also checks that both symbols' most recent
  closed daily bars are the same day and refuses to trade if they are not.
- **If the correlation cannot be computed, the day is skipped.** Trading unfiltered is where
  the losses live: profit factor 0.85 against 1.34.
- **Sizing never rounds up.** If 1% risk does not reach the minimum lot, the trade is
  skipped rather than taken at a larger risk than intended.

## Before real money

Reproduce the numbers above in the tester, then demo for 4–8 weeks — about 40 trades, enough
to catch an implementation bug, not enough to prove an edge. Log every skipped day and its
reason; if the share of days skipped is far from ~38%, the correlation calculation is wrong.

## Verification status

The EA has **not been compiled by MetaEditor** — that is a closed Windows binary and was not
reachable from the environment this was written in. Three other checks were run instead, in
`verify/`:

| Check | What it proves | Result |
|---|---|---|
| `test_dst.py` | The calendar arithmetic, transliterated from the MQL5, against the IANA tz database, every day 2020–2026 | 0 mismatches in 2,557 days |
| `mql5_shim.h` + `transform.py` | Syntax and types, by rewriting MQL5-only syntax into C++ and compiling with `g++ -Wall -Wextra` | 0 errors, 0 warnings |
| `replay_ea.py` | The decision logic, by re-implementing `OnTick` in Python and comparing trades to the research engine | 652/652 identical: same days, directions, entry and exit prices, exit reasons |

The replay also **caught a real defect** — not in the EA, in the research. The published spec
and the EA both stop taking entries at 08:00 London; the backtest behind the original headline
numbers had no such deadline. Those 93 extra late entries lose money (0.951 profit factor), so
the EA's stricter version is the better one. The research engine now enforces the deadline and
the reported figures are the corrected ones.

None of this substitutes for a MetaEditor compile. Expect to fix something on first build.
