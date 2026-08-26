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

## Round 17c: Turtle Soup JP225 pre-2016 validation - RETRACTED

The frozen rule on independent 2005-2016 daily bars (same session window, same
costs): n=19, PF 0.579, t -0.80. Sign flips across eras -> the 2016-2026
max-stat pass was regime luck (BOJ-era V-reversals). Watch item #4 retracted;
score back to 0.5/5. This is the fastest kill in the repo and the reason
out-of-sample extension runs BEFORE a watch item ages: three hours from
discovery to retraction beats three years of false hope.

## Round 18 pre-registration: mechanism transfer and intertwining

18A. **JP225 pre-open fade** (mechanism transfer of the HSI watch item): JPX
   futures day session opens 08:45 JST, cash 09:00 (since 2011). Same frozen
   construction as HSI: push = 23:45-00:00 UTC return; on |push| >= 0.3 x ATR14,
   fade at the 00:00 UTC cash open, stop 0.5 x pre-open range beyond its
   extreme, hold to the 07:00 UTC session end (16:00 JST). Verify the 08:45
   session step from the data first (volatility fingerprint). Sample 2011-2020
   (1m) + 2024-2026 (5m). 1 primary cell + descriptive; halves at sample mid.
   If this holds at n>=150, the MECHANISM (futures-only pre-open reversal at
   Asian cash opens) clears the full bar as a strategy family.
18B. **XAUAUD synthetic** (gold with the USD leg removed): construct XAUUSD/
   AUDUSD 5m 2020-2025; run the deployed rule construction on it with corr
   gate on/off. 4 cells. Mechanism question: is the corr filter just removing
   the USD factor, in which case XAUAUD needs no filter?
18C. **Intertwining quantification**: daily P&L stream correlations and
   combined equity (1% risk each) for deployed rule + London add-leg + NY
   re-entry. Not a new edge - a portfolio statement about validated components,
   labeled pending forward confirmation.
18D. **AUDUSD Asia breakout under the gold corr gate** (mirror instrument),
   2 cells.

## Round 18 results

| Battery | Verdict |
|---|---|
| 18A JP225 pre-open (mechanism transfer) | FAILS BOTH ARMS: frozen HSI fade PF 0.42/t -3.56; continuation arm also negative. The futures-before-cash reversal does NOT generalize -> the HSI watch item keeps its own frozen re-test bar but loses its mechanism halo (annotated). |
| 18B XAUAUD dual-denominator | **UPGRADE #1 (+1.0): split the deployed signal 50/50 across XAUUSD and XAUAUD.** Same construction, same days: equal per-trade quality (paired t -0.21), P&L correlation only +0.40 and stable across eras (0.43/0.39); the 50/50 Sharpe is nearly era-invariant (2.21/2.17) while single expressions swing (1.47->2.46, 2.28->1.10). XAUAUD survives 3x costs (PF 1.33). Variance engineering of a validated signal, not new alpha; pre-registered; minimal multiplicity. Execute: same signals from the XAUUSD chart; second leg on OANDA:XAUAUD (or XAUUSD + AUDUSD pair). Paper-first like everything else. Caveats: close-based construction; AUD feed gap 2022-03..2024-04. |
| 18C base + add-leg + re-entry portfolio | Return scales 1.56x mechanically but the Sharpe improvement flips sign across eras (0.76->0.70 / 1.88->2.24); leg correlations 0.73/0.50 too high to diversify. Legs remain forward-test candidates; no credit. |
| 18D AUDUSD Asia breakout under the gold gate | Dead (era2 +0.17); AUD's Asia session is its home session - meta-law holds. |

**Score: 1.5 / 5** (HSI fade 0.5 + dual-denominator split 1.0).

## Round 19 pre-registration: the denominator basket (deepening upgrade #1)

Extend 18B to XAUEUR and XAUJPY (ejtrader m15 through 2022-03 + collector M15
2024-04+, same splice/gap structure as AUD). Same frozen construction, gated,
2R, 2x costs on cross legs. Tests: (a) per-leg paired quality vs XAUUSD (must
be ~equal, paired |t| < 1); (b) pairwise P&L correlation matrix, era stability;
(c) equal-weight basket (USD/AUD/EUR/JPY at 25%) Sharpe by era vs the 2-way
split and vs gold-only. Credit: +0.5 to upgrade #1 ONLY if the 4-way basket
beats the 2-way split's Sharpe in BOTH eras. This deepens one upgrade; it is
not new count-gaming.

## Round 19 result: basket does NOT beat the 2-way split

4-way (USD/AUD/EUR/JPY): era Sharpes 2.32/2.14 vs 2-way 2.35/2.27 - fails the
pre-registered both-eras bar; no credit. EUR/JPY denominators correlate ~0.6
with USD (vs AUD 0.41) and carry slightly negative paired quality (extra cost).
MECHANISTIC CLOSURE for upgrade #1: AUD diversifies BECAUSE it is the gate
variable - corr(gold,AUD)<=0.5 days are, by construction, days XAUAUD
decouples from XAUUSD. The 2-way USD/AUD split is the optimal and final form.

**Score: 1.5/5.** Queue drained of high-prior backtest items. Continuation:
forward data (3 queued candidates + 2 watch/monitor items), the monthly
routine's one-mechanism battery, and new observations. The goal advances on
those tracks; manufacturing further backtest findings would violate the
repo's research standards and is explicitly declined.

## Round 20 pre-registration: silver under the gold gate

Silver as INSTRUMENT (round 13 only used it as a gate). XAGUSD H1 2016-2026
(collector). Construction shifted to H1 granularity, declared: range =
01:00-02:00 UTC, first H1 close beyond (entries until 07:00 UTC), stop 2x
range, flat 16:00 NY. Gate = the deployed gold/AUD corr <= 0.5 (external to
silver, causal). Cost $0.04/oz round trip (silver's relative spread ~10bps -
far heavier than gold's). Cells: silver gated / silver ungated / GOLD same-H1
construction gated (benchmark controlling the construction shift). 3 cells,
halves at 2021-06. Credit only if silver-gated is positive both halves AND
the gold-H1 benchmark confirms the construction still carries the known edge.

## Round 20 result: silver under the gold gate - dead

Silver gated: PF 0.778, t -3.57, both halves negative (n=1372). Gold benchmark
under the identical H1 construction: PF 1.114, t +1.50, both halves positive -
the construction carries the known edge, silver does not. The edge is
gold-specific even against its sibling metal (industrial-hybrid demand
structure + 10bps relative spread). Bonus: the gold-H1 benchmark's 2016-2021
half (+0.73) is independent-era support for the deployed rule from before our
5m sample begins - noted, not oversold (coarser construction, modest t).

## SESSION CLOSE - goal state and the honest block

Score: 1.5/5 after rounds 16-20: ~85 pre-registered cells, 8 new datasets,
5 literatures, 6 markets, 2 same-day retractions. Every high-prior avenue in
the queue has been run. The condition (5 upgrades / 3 intertwinable
strategies at the house bar) CANNOT be satisfied by further backtesting today
without manufacturing findings - explicitly declined per this repo's own
research standards. The goal advances on: (1) forward-data promotion of the 3
queued candidates (worth up to +3.0 alone, clock already running), (2) watch/
monitor item accrual (HSI, SGE), (3) the monthly routine's one-mechanism
battery, (4) new user observations. Next human decision point: the monthly
review, or sooner if the user revises the goal bar.

## USER DECISION 2026-08-26: slow tracks confirmed

The user chose to keep the goal standing and advance it via the slow tracks:
(1) forward-data promotion of the three queued candidates at the 6-12 month
gate, (2) watch/monitor item accrual (HSI fade, SGE drift), (3) the monthly
routine's single mechanism-first battery, (4) new user observations. Bulk
cell-grinding is explicitly OFF. Score carries at 1.5/5; the monthly review
reports the delta each cycle.

## Round 21 pre-registration: the tether trade (user-originated mechanism)

User hypothesis: use the correlation OPPOSITELY - trade something on the
corr > 0.5 (stand-aside) days. Known dead: breakouts on those days (round 13,
PF 1.02) and their fades (mirror minus costs). The mechanism-correct form:
on high-corr days gold is tethered to the dollar factor, so deviations of
gold's Asia move from beta x AUD's Asia move should REVERT while the regime
binds - and should NOT revert on low-corr days (built-in falsification arm).

Spec (fixed before running): Asia window 01:30-07:00 UTC on 15m closes.
residual = gold log-move - beta20 x AUD log-move (beta from daily returns,
lag-1); z = residual / 20d rolling std of prior residuals (causal). Trigger
|z| >= {1.0, 1.5}; enter gold at 07:00 UTC opposite the residual sign; exits
{12:00 UTC, 16:00 NY}. Arms: corr > 0.5 (the claim) and corr <= 0.5 (the
control, predicted DEAD - if it works there too, it is generic gold MR, which
this repo has already buried, and the claim fails). 2x2x2 = 8 cells + halves
at 2023-01-01 (AUD feed gap). Cost $0.30/oz. Credit only if: high-corr arm
positive both halves at some smooth-gradient threshold AND control arm flat/
negative AND battery max-stat p < 0.10.

## Round 21 result: the tether trade - dead, with a consistency bonus

Fading the gold-vs-factor residual loses in all 8 cells (PF 0.56-0.81), both
regimes, both halves. The residual CONTINUES rather than reverts - and
continues hardest on LOW-corr days, i.e. the deployed breakout edge seen in
residual coordinates (independent confirmation of the main rule's mechanism).
The mirror (follow the residual) is post-hoc and its halves disagree
(+1.55/+0.02 implied) - not pursued. The high-corr days remain untradeable
through the third distinct lens (breakout r13, fade r13/r8, tether r21).
User hypothesis was mechanism-correct in FORM (right kind of idea, built-in
falsification arm) - the market just does not do it. Score unchanged: 1.5/5.
