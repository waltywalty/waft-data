# Round 15 pre-registration: the researched battery

Written 2026-08-26 after the five research reports, BEFORE any test was run.
Halves split: sample midpoint per family (index families: 2005-2015 vs 2016-2025,
with 2021-2025 additionally reported as the honest recent slice; gold families:
2020-23 vs 2024-25). Costs per mkts.py (SPX 0.6 / NDX 2.0 / RTY 0.4 index-point
round trips; gold $0.30/oz + $0.30 stop slippage). Every cell counts.

## F1. Intraday momentum, last half-hour (SPX/NDX/RTY, 2005-2025)

- Signal A (Gao 2018): r1 = prior 16:00 ET close -> 10:00 ET (includes overnight
  gap). At 15:30 ET take sign(r1) into the close, flat 16:00.
- Signal B (Baltussen 2021, the mechanism version): rod = prior close -> 15:30 ET.
  Same trade.
- Conditioning (ONE regime factor per the correlated-gates warning): trailing
  10-day realized vol above/below its rolling median.
- Cells: 3 markets x 2 signals x 3 slices (all/high-vol/low-vol) = 18.
- Predictions on record: same-signed but attenuated post-2013; high-vol slice
  carries it; NQ >= ES per practitioner replications; plain Gao r1 may be dead
  (Rosa 2022) while rod survives.

## F2. Turn-of-month (SPX/NDX/RTY daily closes, 2005-2025)

- V1 (McConnell-Xu): long from the close of the second-to-last trading day of the
  month through the close of the 3rd trading day of the next (4 trading-day hold).
- V2 (Etula "Dash for Cash"): long from the close of T-3 (3rd-to-last) through the
  close of T+2.
- Cells: 3 markets x 2 variants = 6. Prediction: positive but weakened in the
  2016-2025 half; V2 >= V1 per the RFS mechanism.

## F3. Time-series momentum overlay on the deployed gold rule

- Trend state at trade date: sign of gold's trailing {63, 126, 189, 252}-day
  return (daily closes, lag-1). On the 652 deployed trades: split trades whose
  direction AGREES with the trend sign vs DISAGREES.
- Cells: 4 lookbacks x 2 arms = 8. Judged by gradient across lookbacks.
- Confound stated now: 2024-25 is one long uptrend, so agree-longs will
  concentrate there; the halves check is the guard.

## F4. Session-split of the deployed trades (descriptive, 0 cells)

Split each of the 652 trades' P&L at 07:00 UTC (London open) and 14:00 UTC
(~London PM-fix hour): entry->07:00 / 07:00->14:00 / 14:00->exit. Purpose: locate
where the drift accrues, testing the "London bias" claim against our own edge.
Diagnostic only - round 9 already showed early exits lose money; no rule change
can come from this table alone.

## F5. Opening gap fill (SPX and NDX RTH, 2005-2025)

- Gap = today's 09:30 ET open vs prior 16:00 close, in % buckets
  {0.05-0.2, 0.2-0.5, >0.5}.
- Descriptive: same-session fill rate per bucket (touch of prior close before
  16:00), and fill-by-noon rate. Prediction: 70-90% for small gaps, <40% large.
- Economics: enter at the 09:35 ET bar close toward the fill, target = prior
  close, stop = 2x gap beyond entry, time exit 12:00 ET. 2 markets x 3 buckets
  = 6 cells. Prediction: descriptives replicate, net economics thin or negative.

## F6. Pre-FOMC drift - DROPPED

Documented dead 2015-2019 (Kurov et al. FRL 2021) with only ~8 events/yr;
a conditional-revival test would be underpowered and multiplicity-expensive.
Recorded as not run, by decision, before running anything.

## F7. HSI battery

Separate pre-registration: reference/round15_hsi_prereg.md (conditional on data).

Ledger for this file: 18 + 6 + 8 + 6 = 38 cells + HSI's 14+ when data lands.
Max-stat permutation across each family's grid before any positive is believed.
