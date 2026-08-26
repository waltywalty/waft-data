# Goal ledger: 5 upgrades OR 3 intertwinable strategies

Goal set 2026-08-26. Bar for counting a finding (unchanged house standard):
both-halves sign agreement, smooth gradient, max-stat survival, explicit costs,
pre-registration. Watch-list-grade findings count as HALF an upgrade (they are
promises, not P&L); forward-test-candidate grade counts as one.

## Score

| # | Finding | Round | Grade | Count |
|---|---------|-------|-------|-------|
| 1 | HSI pre-open fade (watch item #3) | 15b | watch | 0.5 |

Pre-goal candidates (rvol gate, inside-day gate, London add-leg, NY re-entry,
MGC bracket) predate the goal and are NOT counted.

## Round 16 pre-registration (before any test runs)

A. **Meta-law transplant** - Asia-session ORB on US indices: 60m range from
   01:30 UTC on SPX and NDX (their AWAY session, slow discovery), first 60m
   close beyond enters, stop 2x range, exits {London open 08:00 UTC-ish,
   NY open 14:30 UTC-ish}. Gates: none / realized-vol tercile / VIX level
   (if VIX data lands). 2 mkts x 2 exits x 3 gate states = 12 cells + halves.
   Prediction: the meta-law says this should WORK directionally; if it fails,
   the law is gold-specific and the playbook says so.
B. **Daily mean reversion, Connors family** - RSI(2) < {5,10} and IBS < {0.2}
   buy-the-close, exit close > 5-day MA or RSI(2) > 70, only above 200d MA;
   SPX/NDX/RTY daily from our intraday. 3 mkts x 3 rule variants = 9 cells.
   Published family with multi-decade support; expect decay, test gradient.
C. **Gold/silver ratio reversion** - daily ratio z-score (60d) bands +/-2,
   revert to mean, both legs (we can only express the gold leg intraday spot;
   test as daily overlay signal on gold direction). 4 cells.
D. **VIX gate on the deployed gold rule** - VIX level terciles on the 652
   deployed trades (data pending). 3 cells.

Every cell counts in the ledger; halves at sample midpoints; costs per market
as in mkts.py; battery max-stat at round end.

## Round 16 results (first sweep, 2026-08-26)

| Battery | Verdict | Ledger |
|---|---|---|
| A meta-law transplant (SPX/NDX Asia-session ORB) | DEAD both arms: breakout t to -12, derived fade t to -9.7, both halves; 2020+ converges to ~0. Refines the meta-law: slow-session structure is gold-specific; index away-sessions are untradeable chop (adverse selection taxes both directions). | 12 + 6 |
| B Connors daily mean reversion (RSI2/IBS x 3 mkts) | TRAP EXPOSED: raw numbers look strong (SPX IBS PF 1.62, t +3.54, both halves +) but the max-stat null of randomly-timed long bursts yields t +2.86 median - the "edge" is mostly equity drift harvested in bursts; timing adds only best-of-9 luck (p=0.125). Not counted. | 9 |
| C gold/silver ratio reversion | DEAD: short-gold leg PF 0.29 (bull market), long leg flat, n=16/17. | 4 |
| D VIX gate on deployed gold rule | Descriptive only: monotone gradient PF 1.45/1.40/1.13 calm->stressed, mechanism-coherent (calm macro = gold on own flows), but all terciles positive, halves mixed - not an upgrade (round-13 Q3 lesson). | 6 |

Score unchanged: 0.5 / 5 upgrades (HSI watch item). Practitioner deep-dive agent
pending; its candidates form the next battery.
