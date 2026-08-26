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

## Round 16 second sweep pre-registration (from the practitioner deep dive)

E. **IBS on Asia indices** (published-US family, virgin OOS territory): IBS<0.2
   & close>200dMA -> long at close, exit IBS>0.8 or 10d. HSI, JP225, AUS200
   daily bars from 1h (day session). 3 cells + shifted-signal max-stat (the
   drift null that killed battery B applies here too).
F. **Nikkei conditional open-fade** (refereed 2026 paper): prior-day SPX return
   terciles condition JP225 first-30-min return; trade = fade at Tokyo open on
   extreme prior-SPX days, hold 30m. JP225 1m 2005-2020. 2 cells + descriptive.
G. **Turtle Soup daily** (Raschke; oxfordstrat 42-market replication exists):
   20d-extreme undercut + same-day reclaim of the prior extreme -> fade at
   close, exit +5d. Both sides x {gold, SPX, NDX, HSI, JP225}. 10 cells.
H. **Gotobi USDJPY** (arXiv 2301.13204, structural fix-flow mechanism): long
   USDJPY 06:00->~10:00 JST on gotobi days (5/10/15/20/25/30, business days;
   sensitivity: weekend-shifted-to-Friday). Control = same window other days.
   USDJPY H1 2016-2026. 4 cells.

## Round 16 second sweep results

| Battery | Verdict |
|---|---|
| E IBS on HSI/JP225/AUS200 | dead (JP225 +1.85 inside drift null p 0.133) |
| F Nikkei open vs prior SPX | replicates (rho -0.097, p<1e-4) - inside the spread, untradeable |
| G Turtle Soup daily x5 mkts | **JP225 long survives: PF 4.01, t +3.38, halves +1.57/+3.71, max-stat p 0.027, n=33 -> WATCH ITEM #4 (+0.5)** |
| H Gotobi USDJPY | relative effect real (-0.4 vs -2.1 bps), absolute trade loses, decayed post-2021 |
| I Unger prev-session breakout JP225 | dead raw (t -2.58); profits live in mined filters |
| J 80-20 next-day fade | flat |

**Score: 1.0 / 5** (HSI pre-open fade 0.5 + Turtle Soup JP225 0.5).
Next avenues queued: London add-leg spec refinement (pre-goal candidate, could be
promoted by forward data not backtest), trend-day labeling as conditioner for the
NY re-entry, gotobi-style fix-flow scan on gold (London fix already dead pre-2015;
Shanghai benchmark fix unexplored), HSI watch-item accrual.

## Round 17a pre-registration: Shanghai fix-flow scan on gold

SGE benchmark auctions at 10:15 and 14:15 Beijing (02:15 / 06:15 UTC; no DST).
Descriptive-first: mean 5m XAUUSD returns per slot 01:00-07:00 UTC over the full
sample, halves split 2024-01-01. Named windows (pre-declared, 2 cells): drift
INTO each auction (30 min before) and reversal AFTER (30 min). Economics only
if a named window shows |mean| > $0.30 cost with both halves same-signed.

Result: into-AM-fix drift +0.76 bps/day, t +2.56, halves +0.43/+3.25 (both
positive, era-skewed to 2024+). Sub-cost (~$0.25/oz vs $0.30) -> no economics
per pre-reg. MONITOR: re-score yearly; if the China-era drift doubles it clears
cost. Other three windows and control: nothing.

## Goal status after rounds 16-17a

Score 1.0/5 (HSI pre-open fade + Turtle Soup JP225, both watch-grade, both
frozen). The honest bottleneck is now FORWARD DATA, not search breadth: the
strongest upgrade candidates (rvol gate, inside-day gate, London add-leg, NY
re-entry, both watch items) are all waiting on live trades, and the round-16
experience shows additional backtest cells are yielding myths-exposed and
sub-cost anomalies, not deployable edges. Continued avenues, in order:
(1) watch-item accrual (HSI live feed, JP225 feed), (2) forward-test log
scoring at the 6-12-month gate, (3) new mechanism-first hypotheses as they
arise (user observations have outperformed literature imports 2:1), (4) the
queued trend-day conditioner test for the NY re-entry.

## Round 17b pre-registration: trend-day conditioner on the NY re-entry

Base = round-12 NY 09:30 re-entry, in_profit + 2R (PF 1.333, t +1.80, halves
1.09/1.67). Conditioner (Crabel/trend-day literature, causal at entry): the
09:30-NY price's position within the day-so-far range (from 01:30 UTC) must
align with the Asia direction: longs pos >= {0.7, 0.8}, shorts <= {0.3, 0.2}.
2 cells; improvement bar = both halves improve AND per-trade t rises without
n collapsing below ~150.

Result 17b: FAILS. align>=0.7 n=219 PF 1.324 t +1.52 (base 1.333/+1.80, IS
degrades +1.09->+0.48); align>=0.8 kills it (PF 1.02). The re-entry needs no
conditioning beyond in-profit; trend-day position adds nothing. Queue empty.
