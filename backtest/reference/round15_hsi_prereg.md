# Round 15 pre-registration: Hang Seng (HSI/MHI) battery

Written 2026-08-26, BEFORE any HSI data was obtained or inspected. Data hunt in
progress; every test below is conditional on finding intraday data whose timezone
and session structure can be established empirically (open-step volatility
fingerprint at 09:15/09:30 HKT, per the round-9 method).

Market facts the tests are built on: HKEX derivatives (HSI/MHI futures) open
09:15 HKT; the cash index opens 09:30; lunch break 12:00-13:00; close 16:30
HKT (16:00 cash auction era-dependent); after-hours session to ~03:00. The
09:15-09:30 window is futures trading WITHOUT the cash market - the mechanism
behind the user's observed "Judas at the HSI open".

## H-A: pre-open push reversal (the user's observation)

Definitions:
- push = return from 09:15 to 09:30 HKT (futures/CFD), normalized by 14-day ATR.
- Descriptive (primary): rank correlation of push vs the 09:30->10:30 return and
  vs the 09:30->16:00 return. The observation predicts NEGATIVE correlation,
  strengthening with |push|. Judged by gradient across push quintiles.
- Economics (secondary): fade the push at 09:30 when |push| >= {0.3, 0.5} x ATR14:
  enter opposite to the push, stop {0.5, 1.0} x the 09:15-09:30 range beyond its
  extreme, exits {10:30, 12:00, 16:00 HKT}. Cost: 10 index points round trip
  (HK50 CFD-grade), sensitivity at 5 and 15. 2x2x3 = 12 cells.

## H-B: the 09:30-10:30 window - breakout vs reversal

Mirror of the deployed gold construction on HSI's home session:
- Range = 09:30-10:30 HKT high/low. First subsequent 60m close beyond enters
  (a) WITH the break (breakout arm) and (b) AGAINST it (fade arm) - both arms
  pre-registered so the sample cannot pick the winner silently. Stop 2x range,
  flat 16:00 HKT (no overnight). 2 arms x 1 config = 2 cells + halves.
- Interpretation guard: gold's Asia edge is a breakout edge on a slow-discovery
  session; HSI at 09:30 HKT is a HOME session (fast discovery). The meta-law
  predicts the breakout arm FAILS here. Stating that prediction now.

## H-C: cross-market correlation gates (only if partner data found)

If Nikkei/China A50/USDCNH intraday or daily partners are obtained: 20-day corr
of HSI daily returns vs each partner, lag-1 causal, gating H-B's better arm.
Same protocol as round 13 (thresholds both directions, halves, overlap check).
Prediction from round 13's lesson: partners re-select the same macro state;
expect no incremental gate.

## Discipline

- Halves split at the sample midpoint (exact date set once data span is known).
- Every cell above counts in the ledger (12 + 2 + partner cells).
- Max-stat circular-shift permutation over the full battery before any positive
  is believed.
- Prior stated for the record: five Judas/sweep constructions have failed in
  this repo (gold rounds 2 & 8, indices round 9, TV round 10). H-A differs by
  mechanism (futures-only pre-open window), which is why it gets one test - the
  mechanism, not the pattern, earns it.
