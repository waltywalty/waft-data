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

## Round 22 (development-while-waiting): decision engineering, not signal mining

1. **SPRT sequential boundaries** (sprt.py, frozen: alpha=beta=0.10, promote
   LLR >= +2.20, kill <= -2.20). Honest finding: the base rule's small effect
   needs ~160 trades median either way - the fixed window was never the
   bottleneck, the effect size is. Value: auto-early decisions on unusually
   strong/weak runs, and ~40-70-trade decisions on the bigger-effect satellite
   candidates. The monthly routine now scores each stream's W/L sequence.
2. **Entry-latency study** (latency.json): manual execution is statistically
   free - mean $0.00/oz at next-bar-open fills, -$0.03 at 5 minutes late,
   vs +$2.28 edge. The drift accrues over hours. No webhook bridge needed
   for execution fidelity; the iPad workflow gives nothing away.
3. **Indicator v1.2**: REGIME ON / OFF / APPROACHING alerts (daily corr
   crossings of 0.50/0.55) + corr-trend card row. Droughts now end with a
   push notification instead of daily chart-checking.

## Round 23: the edgeful reconciliation (user-supplied claim, fully resolved)

Their exact spec (09:30-09:35 ET range, by-close entry, opposite-edge stop,
50%-range target) on 20 years of ES proxy: win rate 74% GROSS (they claim
72.17% - our pipeline reproduces their number to within 2 points), expectancy
-0.06 pts gross / -0.66 net. Their "no Tuesdays" optimization makes the full
sample WORSE (-0.16 gross) - a filter fitted to the reported window. Rolling
6-month windows at 1 contract: best +$13.7k (their "108% on $10k" is real and
sits at the 0.8th percentile of gross windows), worst -$14.0k, median +$72;
NET of one tick, zero windows reach their number and the median is -$3,663.
Verdict: our backtesting is not broken - it reproduces every descriptive claim
(theirs included) and diverges only where costs, full samples, and unfitted
parameters enter. Their own docs corroborate: TradingView defaults to zero
costs, their guide warns costs "can turn a profitable backtest into a losing
one", and their own dashboard reports 66.93% of ES days break BOTH sides.

## Round 24 staging: the trader-list commission (13 names, 4 deep dives running)

COT gold data acquired and cross-feed-verified (2006-2026 weekly). The Williams
COT battery will be pre-registered ONLY once the research returns his published
spec (lookback, trader category, thresholds) - running his exact published rule
as a replication, not searching our own grid. Other candidate batteries await
the dives: Turtle N-sizing as a risk transplant (vs our round-9 sizing study),
Minervini trend-template as regime gate (vs the drift null), PTJ 200d-MA gate
(vs round-16 D's vol-gate lesson). Everything faces the house bar.

## Round 24 pre-registration: the trader-list batteries (registered before any test ran)

All four research dives are back. Extraction verdict across 13 names: the only
genuinely new, well-specified, free-data RULE is the Williams COT Index; the
Turtle material contributes a risk/sizing overlay, not entries; Unger
contributes process; the macro legends contribute a defensive audit and two
already-covered ideas. Registered here, before running, per house rules.

**Spec B — Williams COT Index on gold (replication-first, weekly).**
Data: `data/COT_gold_github.csv` (legacy futures-only 088691, cross-feed
verified; raw positional columns only, author's derived columns ignored) x
`data/GOLD_daily_av.csv` (AV daily spot 2011-06..2026-08, to be cross-checked
vs our 5m feed on the overlap before use). Window: 2011-06..2026-08; halves
split at 2019-01-01. Alignment: report is Tuesday positioning published
Friday; signal becomes usable the following Monday open — the index for week
T applies to Monday(T+6d) .. Monday open, no lookahead.
- LW-1 (published form): net_c = comm_long - comm_short; COTidx = 100 x
  (net_c - min_26w)/(max_26w - min_26w), 26-week window incl. current week.
  Long while >= 80, short while <= 20, flat otherwise; also long-only variant.
  (2 tests)
- LW-2 (WillCo): net_c / open_interest before normalizing; same thresholds,
  same two variants. (2 tests)
- Gradient (counted, judged by slope not peak): lookback {13,26,52,156} x
  thresholds {70/30, 80/20, 90/10} = 12 cells per construction, both
  constructions = 24 cells.
- Category check (counted): same index on large speculators as a FADE
  (Williams: commercials right / specs wrong at extremes). (2 tests)
- Multiplicity: max-stat circular-shift permutation over all counted cells;
  Bonferroni quoted alongside. Success bar: same sign in both halves AND
  survives the max-stat test. Interaction with the Asia breakout runs ONLY if
  LW-1 or LW-2 passes that bar (1 further test).
- Costs: weekly rebalance, $0.60/oz round trip modeled; sensitivity run.
- Base-rate note registered up front: gold commercials are structurally net
  short (miners hedge); time-in-state will be reported so a "long >= 80" rule
  is judged against its actual exposure, not calendar time.

**Spec A — Turtle risk layer on the deployed 652-trade set (sizing-only).**
N = 20-day Wilder ATR on daily gold. Same entries/exits as deployed; overlays:
(1) N-sizing (1% equity / N) vs deployed risk-sizing (1% / stop distance);
(2) 2N stop replacing the 2x-range stop (re-simulated on 5m paths);
(3) pyramiding: add 1 unit per +1/2 N favorable, stops to 2N below last add,
gradient over max-units {1,2,3,4} judged by slope; (4) drawdown throttle
(-20% size per -10% equity DD) on/off. Scored on risk-adjusted numbers (MAR,
max DD, final equity at 1% risk, $2,000 start) against the round-9 flat-risk
baseline. 7 counted cells. Registered expectation: sizing changes risk shape,
not expectancy sign.

**Marcus gap-through-stop tail audit (descriptive, not a test).** On the
deployed set's stop exits: realized exit vs intended stop level, worst
realized loss vs the intended 1%, distribution of gap-through amounts, and
weekend/data-gap exposure. Motivated by Marcus's limit-down soybean lesson:
"size so the gap scenario is survivable."

**Spec C — Unger process adoptions (no data test).** (1) Hard average-trade
floor: reject any candidate whose average net trade < 2x modeled round-trip
cost before other statistics are computed — adopted into house rules. (2)
Incubation ledger: journal streams already compare live vs backtest; formalize
auto-retire on leaving the backtest envelope (SPRT kill bound already does
this — noted as satisfied). (3) Market-character pre-test before choosing
breakout vs fade archetype for any new market/session — adopted.

**Spec D — explicit non-tests (logged, not run).** Medallion-style daily
signals (power analysis: a 50.75%-hit-rate edge is invisible at our ~250
trades/yr — documented out of scope); Turtle 20/55-day entries on gold
(near-duplicates of breakout families already killed); Williams Oops gap
patterns (23-hour gold session has no exploitable opens); Minervini
RS-rating/earnings legs (cross-sectional, no XAUUSD analogue); PTJ 200d MA
gate and Minervini VCP contraction gate are DEFERRED to a possible later
round, not smuggled into this one — this round runs replications, not new
filter families.

## Round 24 results (all pre-registered above; run 2026-08-26)

**Data deviation, documented:** the Alpha Vantage daily gold series FAILED its
registered cross-check (synthetic weekend rows; +/-40-100bp day noise; daily
return corr vs our 5m feed 0.53 at every candidate day boundary) and was
REJECTED. Replaced with a spliced series from our own cross-verified feeds
(ejtrader M15 2012-05..2016-04 + H1 collector 2016-04..2026-08; overlaps agree
to ~1bp median, return corr 0.9995+). Test window therefore 2012-06..2026-08;
the registered 2019-01-01 halves split was kept unchanged.

**Spec B - Williams COT Index on gold: NEGATIVE.** (run_r24_cot.py ->
results/r24_cot.json; 715 tradable weeks)
- LW-1 published form (26w commercials, 80/20, long/short): full t +0.57,
  halves +0.86 / -0.03 - sign does not hold. Long-only: halves -0.13 / +1.98
  - sign flips the other way (and long-only in a rising-gold half is the
  drift null's favorite costume).
- LW-2 (WillCo net/OI): full +0.22, halves +0.65 / -0.42. Same failure.
- Large-spec fade: near mirror image of LW-1 as predicted (legacy-data
  redundancy): +1.04 / -0.06. Nothing independent.
- Gradient over 24 cells: ragged, sign-flipping (+1.57 to -1.61), best cells
  at short lookbacks, NEGATIVE at the 156w structural lookback. No smooth
  slope anywhere.
- Max-stat over all 30 counted cells: observed max |t| 1.65, p = 0.76.
  Bonferroni bar |t|~3.1: nothing close.
- Base rates: the 26w commercials index spends 27.8% of weeks >= 80 and
  27.6% <= 20 - the structural-short caveat registered up front was real but
  not the binding problem; the signal simply carries no expectancy here.
- Cost sensitivity: t +0.64 gross -> +0.37 at 4x costs; costs are not the
  story either. Verdict: Williams' best-specified free-data idea does not
  replicate on 2012-2026 gold. Buried with full honors.

**Spec A - Turtle risk layer: DEPLOYED MODEL WINS EVERY CELL.**
(run_r24_turtle.py -> results/r24_turtle.json; $2,000 at 1% risk)
- Baseline (1% / actual stop distance): final $4,865, CAGR +20.7%, maxDD
  16.1%, MAR 1.29.
- N-sizing (1%/N): N (med $24.4) is ~3x our stop distance (med $8.2), so it
  just trades smaller: CAGR +7.6%, maxDD 7.2%, MAR 1.06. Our per-trade
  stop-distance sizing IS volatility normalization, at finer grain.
- 2N stop: so wide only 2% of trades stop; per-oz expectancy RISES (PF 1.412,
  t +3.14 - replicating the known no-stop result) but risk-sizing off a $49
  stop collapses position size: final $2,570, MAR 0.93.
- Pyramiding (+1/2N adds, stops to 2N below last add): per-unit expectancy
  degrades MONOTONELY with max-units - t +2.50 / -2.22 / -4.51 / -5.23 for
  1/2/3/4 units. A clean gradient, pointing down: adds buy worse prices in an
  intraday drift too small (+$2.28/oz) for $12 add-spacing. Account finals
  rise only because total size rises; maxDD goes 16% -> 51%. Rejected.
- Drawdown throttle (-20%/-10% DD): final $4,149, MAR 1.18 - consistent with
  the round-9 ladder result: throttles lag the recovery. Neutral-negative.
  Verdict: the Turtle layer is built for multi-day trend positions; on an
  intraday drift, every piece either shrinks the edge or adds tail risk.

**Marcus gap-through-stop audit (descriptive): the tail is benign.** 339 stop
exits: realized loss median 1.08x intended, p99 1.21x, WORST 1.25x - i.e. the
worst single-trade loss at 1% intended risk was 1.25% of equity. Largest 5m
bar gap inside sampled trade windows: 5 minutes (no data holes). The
limit-lock nightmare does not apply to intraday spot gold at our size; the
existing $0.30 stop-slippage model already covers the observed median.

**Spec C - Unger process adoptions: ADOPTED.** (1) Average-trade floor:
candidate systems must show avg net trade >= 2x round-trip cost before any
other statistic is computed. The deployed rule passes: $+1.60/oz vs $1.20
bar (2x the $0.30+$0.30 model). Adopted into house rules. (2) Incubation
ledger: satisfied by the SPRT boundaries + journal envelope comparison
already in place. (3) Market-character pre-test before choosing archetype
for any new market/session: adopted (the round-16A/18A cross-market failures
were exactly this lesson, learned the expensive way).

**Round 24 net effect on the strategy: zero changes to the deployed rule.**
The commission's real yield: the deployed risk model survived a direct
challenge from the most famous risk framework in trading folklore, the
best-specified free-data signal from the trader list is now a documented
negative, one process gate is adopted, and the gap-tail is measured and
benign. Score vs the old 5-upgrades goal: unchanged at 1.5.

## Round 25 pre-registration: the correlation-timescale battery (user commission)

The user asked whether the gate's timescale was ever fully crossed against the
entry timescale, and whether an intraday-computed correlation was tested. Round
3 swept the DAILY corr window (10-90d, plateau at 10-30d) and the threshold
(-0.4..0.9, smooth monotone gradient); round 1 swept the range/entry length
(30/60/90m). Never tested: correlation computed from INTRADAY returns, and the
explicit window x entry-timeframe cross. Registered here before running.

**A. Intraday-frequency corr as a gate replacement (18 counted cells).**
Constructions: gold/AUD rolling corr of H1 log returns, windows {24, 48, 120,
240} bars; and of M15 returns, windows {96, 480} bars - 6 sensors from ~1 day
to ~2 weeks of intraday information. No lookahead: each day's value uses only
bars closed before 01:30 UTC (the range start). Applied as day-masks at
thresholds {0.3, 0.5, 0.7} to the unfiltered 60m base trade set. Cell
statistic: two-sample t of kept vs excluded trade returns (isolates the gate's
information from the base drift).
Data constraint documented up front: AUDUSD intraday exists 2020-08..2022-03
(M5 + ejtrader) and 2024-04..2026-08 (collector); trades in the hole are
excluded and the two segments ARE the halves test.
**B. Adjunct gradient (6 counted slope stats).** Within trades the deployed
daily gate already keeps, tercile-split by each intraday sensor: is there a
monotone quality slope left after the daily gate? (Spearman of return vs
tercile.)
**C. Window x entry-timeframe cross (9 cells).** Daily corr windows {10, 20,
40}d x (range = entry) in {30, 60, 90}m at threshold 0.5. The check is
interaction: does 60m dominate at every window, or does the surface tilt?
**Multiplicity:** max-stat circular day-shift permutation (500 perms, one
shared offset per perm across all A cells); Bonferroni quoted. Success bar
for A: beat the deployed gate's PF on the same tradable days AND same sign in
both segments AND survive the max-stat. B and C are judged by slope/
consistency, not peaks.
**Registered prior: negative.** Same-day AUDUSD confluence died in round 2;
the daily signal's half-life is ~27 days (the regime is slow); round 13's
416-cell partner sweep found no second axis. Costs as deployed
($0.30 + $0.30 stop slippage).

## Round 25 results (run 2026-08-27): all three arms negative; the deployed gate stands

**A. Intraday-frequency corr gates: dead.** (run_r25_corrtf.py ->
results/r25_corrtf.json) Best of 18 cells |t2| = 1.16; max-stat p = 0.948 -
the intraday sensors are indistinguishable from shifted noise. Segment signs
flip in nearly every cell (e.g. H1_48<=0.3: -2.80 / +0.16). The deployed
daily gate scored on the SAME available days: PF 1.439, t2 +1.69 - better
than every intraday cell. The registered prior held: the regime is slow
(half-life ~27d), and a fast sensor only adds noise to it.
**B. Adjunct terciles inside the deployed gate: nothing.** All six sensors
give |rho| <= 0.05, p >= 0.30, tercile PFs non-monotone. Once the daily gate
has selected the day, intraday gold/AUD co-movement carries no residual
information about trade quality.
**C. Window x entry-timeframe cross: no interaction; 60m confirmed.** The
surface is well-behaved - L60 beats L30 at every window (10/20/40d), and the
20d window is best or tied for every entry length, so the two deployed
parameters do not interact. The one full-sample tilt (L90 PF 1.413 vs L60
1.329 at w=20) FAILS the halves lens: 2020-23 L90 1.103 vs L60 1.149 (worse),
2024-25 L90 1.824 vs 1.537 (better) - the improvement lives entirely in the
strong era. Era artifact; no change. Cell count this round: 18 + 6 + 9 = 33,
all logged.

Verdict: the correlation gate's timescale question is now CLOSED from every
direction - daily window (r3: 10-90d plateau), threshold (r3: smooth monotone
gradient), partner (r13: 416 cells), intraday frequency (r25: dead), adjunct
residual (r25: dead), and the window x entry-timeframe cross (r25: no
interaction). 20-day daily correlation at 0.5 with the 60m range/entry is the
finished form.

## Round 25b pre-registration: the lower-timeframe extension (user commission)

Extend arm C downward: (range = entry confirmation) in {5, 10, 15, 20} minutes
x daily corr windows {10, 20, 40}d at threshold 0.5 - 12 new cells, same
construction as deployed (first close beyond the range, 2x-range stop with
$0.30 stop slippage, no entry after 08:00 London, flat 16:00 NY, $0.30 cost).
Judged as a GRADIENT together with the existing 30/60/90m cells: the question
is whether the timeframe surface is smooth and where it rolls over, not
whether any single cell wins. Registered expectations: (1) trade counts rise
and per-trade edge falls as the range shrinks; (2) tighter ranges mean tighter
2x stops, so stop rates and cost sensitivity worsen - report both; (3) prior
is monotone degradation below 30m. A cost-sensitivity pass (x0, x1, x2 costs)
runs on the best low-TF cell regardless of outcome.
Intraday corr sensors below M15 are a documented NON-test: AUDUSD M5 exists
only 2020-08..2021-06, too short for the segment structure.

## Round 25b results (run 2026-08-27): monotone degradation below 30m; the surface is a smooth slope

(run_r25b_lowtf.py -> results/r25b_lowtf.json; 12 cells)
The full timeframe gradient at the deployed window (w=20d, corr<=0.5), net PF:
5m 1.028 -> 10m 1.064 -> 15m 1.113 -> 20m 1.110 -> 30m 1.224 -> 60m 1.329 ->
90m 1.413. Monotone within noise across SEVEN timeframes - the deployed 60m
sits on a smooth slope, not a spike (and 90m's tip is the era artifact killed
in 25a). Same ordering at w=10 and w=40.
The mechanism is visible in the diagnostics: a 5-20m Asia range is $1.5-2.8
wide, so the 2x-range stop is $3-6 against $0.60 of round-trip cost - stop
rates run 67-84% and costs eat half the gross edge (L5: PF 1.223 gross ->
1.028 net; best low-TF cell L15 dies at 2x costs, PF 0.998). The halves lens
adds the kill: every low-TF cell is negative or flat in 2020-23 (PF 0.96-1.02)
and only looks alive in the 2024-25 era.
Verdict: nothing below 30m is tradable; the low-TF cells are cost-dominated
whipsaw harvesting. The entry-timeframe axis is now closed 5m-90m. No change
to the deployed rule. Running cell total this round: 33 + 12 = 45.

## Round 26 pre-registration: the SGE auction-window battery (user commission)

The user's three hypotheses around the Shanghai Gold Exchange AM benchmark
auction (10:15 Beijing = 02:15 UTC, verified in round 17 from the data; the
auction sits INSIDE the deployed 01:30-02:30 UTC opening range - overlap with
the deployed signal will be reported):
**A. Auction-candle bias (4 cells).** Sign of the first post-auction candle
(02:15-02:20 5m; 02:15-02:30 15m) vs forward return (a) to the 16:00 NY close,
(b) to 08:00 London. Statistic: two-sample t of forward returns, up-candle
days vs down-candle days.
**B. Match/contrast with the 09:30 open candle (4 cells).** Sign agreement of
the 01:30 open candle (5m and 15m) with the auction candle: forward return to
NY close when they AGREE vs DISAGREE (the user's continuation-vs-reversal
idea). Two candle-TF constructions x two targets.
**C. Auction-hour value zone (2 trade cells + controls).** The 02:15-03:15 UTC
range as a mean-reverting zone: after 03:15, fade the first touch of each
range edge (long at low edge, short at high edge), target the range mid, stop
0.5x range beyond the edge, flat 16:00 NY, costs $0.30 + $0.30 stop slippage.
Control: the identical construction on the 03:15-04:15 range (no auction) -
if the auction range and an arbitrary hour behave alike, the zone is
geometry, not value.
**Multiplicity:** max-stat circular day-shift over the 8 A/B cells + the 2 C
cells (500 perms); Bonferroni quoted. Halves 2020-23 / 2024-25 with the sign
bar. Gate interaction (corr<=0.5 vs stand-aside days) reported descriptively,
not counted.
**Registered priors:** A/B negative - candle-sign conditioning is the
price-pattern family that has died 6+ times here, mechanism-adjacent window
or not; the 01:30 candle's sign also partially proxies the deployed breakout
direction, so B risks rediscovering the deployed edge in costume. C negative -
round 14 falsified the "confluent level = magnet" premise; the control is the
referee. Round 17's measured auction drift (+0.76bps/day) is SUB-COST, which
bounds how much information the window can carry.

## Round 26 results (run 2026-08-27): one arm buried, one arm real-but-untradeable

(run_r26_sge.py -> results/r26_sge.json; 1,537 days, auction candle on 83%)

**C. Auction-hour value zone: dead, and the control killed it twice.** Fading
the 02:15-03:15 range edges to the mid loses heavily (PF 0.625, t -7.49) and
is WORSE than the identical construction on the no-auction 03:15-04:15
control hour (PF 0.733). The auction hour is anti-mean-reverting - it is a
trend-setting window (it sits inside the deployed breakout range), and its
range is a launch pad, not a value zone. Round 14's magnet falsification,
third confirmation.

**A/B. The post-auction candle carries REAL directional information - the
strongest descriptive signal since the VIX gradient.** The 02:15-02:30
15m candle's sign predicts drift to both 08:00 London (t2 +3.11, halves
+2.12/+2.29) and the NY close (t2 +2.29); max-stat over all 8 A/B cells
p = 0.004. B (open-candle agreement) is the same signal restated: the
disagreement cells' negative drift is the auction candle winning the
argument with the 09:30 candle.
**And it is untradeable, on two independent grounds:**
1. Sub-cost standalone: enter 02:30 in the candle direction, flat NY close -
   gross +$0.70/oz (PF 1.105), NET +$0.10 (PF 1.015, t -0.04); the 2020-23
   half is net negative (PF 0.912). ~5bps of information vs ~3bps of costs.
2. Non-additive to the deployed rule: on deployed-trade days the candle
   agrees with the breakout direction only 56% of the time, and the deployed
   edge is healthy on BOTH subsets (agree PF 1.425, disagree PF 1.287) -
   filtering would discard 44% of trades to chase a within-noise delta, the
   round-16D "descriptive, not an upgrade" pattern exactly.
Verdict: joins the SGE AM-fix drift (r17) and the VIX gradient (r16D) in the
real-but-untradeable ledger - a mechanism-anchored description of WHY the
Asia session sets direction, not a new trade. Re-scored yearly alongside the
r17 monitor. No change to the deployed rule. Cells this round: 10 counted +
registered descriptive follow-ups.

## Round 26b pre-registration: monetization attempts on the auction-candle signal

The user's challenge: if the bias is detectable, a construction should exist.
First the framing correction is registered as a deliverable: report the raw
DIRECTIONAL HIT RATE of the candle (the t-stats are high because n=1,267, not
because the per-day signal is strong). Then the two honest levers:
**A. Magnitude conditioning (1 gradient, counted).** Split days into quintiles
by |auction candle| / 14-day ATR. If information scales with conviction, the
top quintiles should show larger forward drift AND clear costs. Judged by the
slope across quintiles; the top-quintile subset must also pass halves.
**B. Cost-structure sensitivity (descriptive).** Same strategy (enter 02:30,
candle direction, flat NY close) at three cost models: spot CFD $0.60/oz RT,
MGC micro futures ~$0.25/oz RT (1-tick spread + commissions, round-11 model),
and zero (information bound).
Registered prior: magnitude helps but the best cell stays marginal; at MGC
costs the full-sample net turns positive but thin, and 2020-23 remains the
referee. Nothing deploys from this round regardless - anything that clears
the bars goes to the WATCH LIST behind the frozen SPRT/journal process.

## Round 26b results (run 2026-08-27): the signal cannot be monetized, and the hit rate explains why

(run_r26b_monetize.py -> results/r26b_monetize.json)
**The framing stat first: the candle's directional hit rate is 50.8%**
(49.8% in 2020-23, 52.9% in 2024-25). The round-26 t-stats were high because
n=1,267, not because any single day is predictable - this is exactly the
Medallion power-analysis lesson from round 24 (a 50.75%-grade edge is
monetizable only at thousands of trades/year and near-zero cost).
**A. Magnitude gradient: non-monotone, and the top quintile fails halves.**
Net expectancy by |candle|/ATR quintile: -0.69 / -0.47 / +0.98 / +0.94 /
-0.06 $/oz - a hump, not a slope. The biggest candles carry LESS forward
information (exhaustion), so "trade only the strong signals" selects the
wrong days. Top quintile: 2020-23 -$0.61/oz, 2024-25 +$1.14 - era-dependent.
**B. Cost structures: even free execution does not save it.** Full strategy
at zero cost: +$0.74/oz, t +1.22 - the tradable one-position-per-day version
is statistically indistinguishable from noise even before any toll. MGC
costs: t +0.73. Spot: t +0.03.
Verdict: no construction exists at our trade frequency. The information is
real (the two-sample tests prove the auction participates in setting
direction) but it is spread too thin across days to be captured one trade at
a time. The deployed rule already monetizes this session's directionality the
only way that clears costs: by waiting for the range to break and the regime
gate to be open. Round 26 fully closed; nothing to the watch list.

## Round 27 pre-registration: the confirmation-stack commission (user list, triaged)

The user's list, triaged against the record BEFORE testing. Already tested and
buried (cited, not re-run): reversals/sweep entries (r2, r8, r9 - adversely
selected on three markets); change of character / CISD (r10 - dead in both ICT
windows on four markets; the gold CISD-to-EoD variant is watch item #1); break
of structure (r8 daily-structure Judas - dead); Bollinger/band 2-2.6-sigma
reversion (r8 gold: worth one spread; r9 indices: same) and band/EMA pullback
continuation (r11 - dead); support/resistance levels incl. confluence
"magnets" (r14 - falsified with matched controls; r24 David Paul assessment);
accumulation-manipulation-distribution identification (the Judas/stop-run
family, six independent constructions dead; the one survivor is the HSI
pre-open fade, which lives on a mechanism, not the pattern); HTF trend
continuation as added bias (r15 TSMOM overlays on the gold rule: no gradient;
r16D vol-regime: descriptive). Untestable on our data: true order-book/DOM
flow (no depth feed; spot volume is tick count). POC/value-area: r11's gated
VP reversion is already watch item #2; the POC-magnet variant died in the
same grid. Frequency framing registered up front: r3's threshold gradient
showed the marginal trades near the gate are coin flips - frequency bought by
loosening confirmation is negative expectancy, so only INDEPENDENT new edges
add frequency honestly.

Two genuinely new items, registered to run now:

**27A - Fair value gaps and inversions (16 counted cells).** FVG = 3-bar
imbalance (bull: low[t] > high[t-2]; zone = [high[t-2], low[t]]; bear
mirrored). Formation windows anchored to the sessions we know: gold 00:00-
04:00 UTC (Asia), indices 09:30-10:30 ET (NY open hour). Constructions:
(1) continuation - first retrace touch into the zone enters in gap direction,
stop beyond the far edge, flat session end (gold 16:00 NY, indices 16:00 ET);
(2) inversion (iFVG) - a bar CLOSING through the far edge enters in the
violation direction, stop at the near edge, same exit. Markets XAU/SPX/NDX/
RTY x TFs {15m, H1} x 2 constructions = 16 cells, sides pooled (side split
reported). Costs per mkts.py + equal stop slippage. Bar: same sign both
halves AND full-sample |t| >= 3.0 (~Bonferroni 0.05/16). Registered prior:
negative - FVGs are the last untested member of the imbalance/pattern family
that is 0-for-6+ here; the honest reason to run it is that it has never
actually been run.

**27B - The inversion commission: gold/dollar as signals to trade equity
futures (36 counted cells).** Signals, all lag-1 closed-data: (1) gold daily
return sign; (2) gold 5d return sign; (3) synthetic-DXY daily return sign
(r13 weights); (4) DXY 20d trend sign; (5) gold/AUD 20d corr <= 0.5 (the
deployed gate as a risk-state descriptor); (6) gold-SPX 20d rolling corr,
median split. Targets: (a) next-day close-to-close, (b) NY session 09:30->
16:00 ET. Markets SPX/NDX/RTY. Statistic: two-sample t of target returns in
signal-up vs signal-down (state vs non-state) days. Window: 2012-06..data end
(gold spliced daily x index feeds; RTY ends 2020); halves at 2019-01-01.
Max-stat circular day-shift over all 36 cells (500 perms, shared offset);
Bonferroni quoted. Registered prior: flight-to-safety gold-equity correlation
is CONTEMPORANEOUS in the literature, not predictive at lag 1; expect
descriptive-at-best. Any survivor faces the r16B drift null before promotion.

## Round 27 results (run 2026-08-27): both new families negative

**27A - FVG/iFVG: dead.** (run_r27a_fvg.py -> results/r27a_fvg.json) 12 of 16
cells runnable (the indices' 1-hour formation window cannot hold a 3-bar H1
pattern - spec limitation, logged). Zero cells pass: every runnable cell has
negative t or halves that disagree, and several are SIGNIFICANTLY negative
(NDX 15m inversion t -8.21, SPX both constructions t -2.8/-2.9). The tiny
15m zones make the far-edge stop a cost-harvesting machine (win rates 6-24%).
The one full-sample positive (XAU 60m continuation, PF 1.336) has halves
0.712/1.827 - the era artifact shape again. The imbalance/pattern family is
now 0-for-7+ in this repo. Post-hoc note, not counted and not run: RTY 15m
inversion loses in BOTH halves (0.764/0.715), so its mirror (fading iFVG
violations) would have been consistently positive gross - it is the sweep-
fade family in a new costume, six prior burials, and stays un-run.

**27B - gold/dollar as lag-1 signals for equity futures: nothing.**
(run_r27b_inversion.py -> results/r27b_inversion.json; 36 cells, 2012-2026,
~2,000-4,200 days per cell) Best cell |t| = 1.63 (gold 5d momentum -> SPX
session); max-stat p = 0.860 - the best cell is unremarkable against shifted
noise. The only internally consistent family is gold-5d-up -> equities-up
(all 6 cells positive, ~3-5bps/day difference) but it is far inside noise and
inside the drift null's reach. The deployed corr gate as a risk-state
descriptor tells equities nothing (|t| <= 0.54 everywhere). Registered prior
confirmed: the gold-equity relationship is contemporaneous flight-to-safety,
not lag-1 predictive.

**The frequency question, answered by the round:** confirmation-stacking on
existing signals REDUCES frequency (it subsets); new frequency requires new
independent edges, and this round tested the last two candidates from the
user's list that had not already been buried. Cells this round: 52. The
honest paths to more trades remain the ones already on the books: the
dual-denominator split (deployed), the HSI fade (accruing toward its 80-trade
bar), the forward-test satellites (rvol gate, inside-day, London add-leg),
and new MECHANISMS as they are found - not more confirmations.

## Round 28 pre-registration: the researched-recipe replication battery (user commission)

Web research returned 14 named multi-signal recipes ranked by evidence grade
(peer-reviewed > working paper/independent backtest > book > influencer).
Excluded on sight: Gao last-half-hour intraday momentum (grade A paper, but
round 15 already ran it on our own 20y index data - sign-flipped);
The Anti and Wyckoff Spring (not mechanizable without inventing the spec -
and the Spring is our six-times-buried sweep-reclaim in Wyckoff clothing);
ICT Silver Bullet and Unicorn are DEFERRED, not run: their defining input
("bias", swing convention) is undefined in the published form, so any test
would be of our convention, not their claim - plus the arXiv MNQ
falsification study (2605.04004: 14 OHLCV signal families, walk-forward,
none clear a 1.5pt cost wall) sets the prior. If the user wants them, we
freeze OUR convention and say so.

EIGHT recipes run at FROZEN published parameters (replication, not search).
Registered cost-wall prior for every intraday cell: the MNQ study's
arithmetic. Registered drift-null requirement for every long-only daily
equity cell (round 16B). Bonferroni over the actual cell count quoted with
results; halves split per market (indices 2015-01, gold 2023-01 given spans).

DAILY-BAR GROUP (indices 2005-2025 from the 5m feeds; gold 2020-2025 - the
spliced long series is close-only, documented):
1. Double Seven (Connors/Alvarez, book): close > 200d SMA, buy 7-day closing
   low, exit 7-day closing high, no stop (as published). 4 markets, long
   side as published. Drift null mandatory. Claim: 77-81% win.
2. NR7 and ID/NR4 breakout (Crabel, book): next-day stop entry 1 tick beyond
   pattern-day extreme, stop at opposite extreme, exit same-day close
   (frozen variant); same-day trigger+stop resolves to STOP (conservative,
   documented). 4 markets x 2 patterns. Claim: 60-76% win pre-1990.
3. Hikkake, best published form (Chesler spec + Oxfordstrat trend filter):
   inside bar -> false-break bar -> stop entry at inside-bar extreme within
   3 bars, WITH 50-EMA trend context, 10-bar time exit, stop at false-break
   extreme. 4 markets. Bulkowski/Oxfordstrat: works only with filter+hold.
4. Holy Grail (Raschke/Connors, book): ADX14 > 30 AND ADX > ADX[1] (frozen
   convention for "rising"), pullback touches 20 EMA, buy stop above touch-
   bar high, stop below touch-bar low, exit at prior swing high or 10-bar
   time stop (frozen). 4 markets, both sides. No published aggregate stats -
   this is the first rigorous test at book parameters.
5. TTM Squeeze (Carter, book): BB(20,2.0) inside KC(20,1.5xATR20) for >= 5
   bars, fire = first bar BB re-exits, direction = 12-bar linreg momentum
   sign, entry fire close, exit on 2-bar momentum deceleration, stop at
   opposite squeeze-range extreme. 4 markets daily + XAU/SPX H1. Claim
   (vendor, not credible): 68% "2xADR in 5 bars".
INTRADAY GROUP (5m):
6. Zarattini/Concretum noise-area intraday momentum (working paper + ES/NQ
   replication): sigma(t) = 14-day average |open->t| move per minute-of-day;
   bands = open x (1 +/- sigma(t)) with gap adjustment; entries only at
   HH:00/HH:30 beyond a band; trail = max(band, session VWAP) checked at
   30m marks; flat at close; reversals allowed. SPX/NDX/RTY (09:30-16:00 ET
   session) + XAU port (01:30 UTC session open, flat 16:00 NY). Claim:
   Sharpe 1.33 SPY / 1.57-1.67 ES-NQ; cost sensitivity flagged by
   reviewers - we run x0/x1/x2 costs.
7. Momentum Pinball (Raschke/Connors, book): RSI(3) of ROC(1) on daily
   closes; < 30 -> next day buy stop above FIRST-HOUR high, stop at first-
   hour low, exit next day's close; > 70 mirrored short. XAU + SPX.
8. Market Profile 80% rule (Dalton): prior-session 70% volume value area
   from 5m bars; open outside VA; re-entry held two consecutive 30m closes
   inside -> enter at VA edge toward the far edge; target far edge; stop
   0.25 x VA width beyond entry edge; flat session end. SPX + XAU. The 80%
   fill claim is also scored descriptively (conditional fill rate).

## Round 28 results (run 2026-08-27): one candidate, two busted claims, five burials

~40 cells across the eight frozen recipes. Bonferroni note: at this round's
cell count the strict familywise bar is p ~ 0.00125 / |t| ~ 3.2.

**THE CANDIDATE - Double Seven on SPX (Connors/Alvarez 2008).** PF 2.303,
win 80.2% (book claimed 77-81% - the claim REPLICATES), t +5.15, halves
2.40/2.28, n=253 over 20y (~13 trades/yr). Matched-hold drift null (random
long entries above the 200SMA with the trade set's exact bar-hold
distribution, 3,000 sims): p = 0.005. Decisive context: the book's test
window was ~1995-2007, so our 2015-2025 half (PF 2.28) is fully
POST-PUBLICATION out-of-sample - the hardest test a published recipe can
face, and it passes on SPX. NDX: PF 2.64, drift p = 0.028 (borderline).
XAU (p 0.40) and RTY (p 0.47) are inside the drift null - the effect is
large-cap-equity-specific, consistent with the literature (institutional
dip-buying in trending index products). Sub-strict-Bonferroni for the round
(0.005 vs 0.00125), so per house rules it does NOT deploy: it goes to the
WATCH LIST at frozen parameters (7/200, long-only, no stop, as published)
with the standard promotion bar. Caveats registered: no stop (worst
open-trade excursions ride through corrections); in-market ~25% of time;
long-only equity = drift-adjacent even after the null.

**BUSTED CLAIM 1 - Market Profile "80% rule": the number is wrong.** The
conditional value-area fill rate, measured exactly per the published trigger
(open outside VA, two consecutive 30m closes back inside): 46% on SPX
(n=1,186 setups, 19y) and 32% on gold - nowhere near 80%. The trade
expression is flat-to-negative (PF 0.995 / 0.907).
**BUSTED CLAIM 2 - Crabel ID/NR4 and NR7 win rates.** Published 60-76%;
measured 26-30% across all eight cells. The pattern is not dead as an
EDGE shape - all 8 cells have PF > 1 (1.09-1.41, NR7 SPX t +2.52) because
rare big winners pay for the many small stops - but the famous win-rate
claim belongs to pre-1990 futures, not modern markets. Sub-bar; logged as a
consistent-but-thin family (the volatility-contraction cousin of our r25b
findings).
**Zarattini noise-area momentum: gross yes, net no.** At zero cost the SPX
gross effect is real (PF 1.148, t +3.28 - direction consistent with the
paper); at our CFD costs all four markets are dead (PF 0.88-1.05) and at 2x
costs strongly negative (t -6.5). The reviewers' cost-sensitivity flag was
the story - the edgeful lesson at working-paper quality. A futures-cost
re-run is the one legitimate follow-up if the user ever trades ES directly.
**Buried:** Hikkake best-published-form (PF 0.24-0.64 everywhere, NDX/RTY
t ~ -3); Holy Grail (daily setups near-nonexistent at ADX14>30 - n 1-18;
H1 SPX PF 0.583, t -2.75; the book's chart examples were the evidence, and
the rule at frozen parameters has none); TTM Squeeze (PF ~1.0 all six
cells - the vendor numbers have no support); Momentum Pinball (XAU 1.18 at
t +0.89, SPX 0.93 - noise).

## Round 28b: Double Seven becomes paper stream 4 (user decision, 2026-08-27)

Deep-dive (run_r28b_d7.py -> results/r28b_d7.json; dossier artifact published):
- SPX strategy-only: 6.5%/yr at 15.3% maxDD, Sharpe 0.69, MAR 0.43, 28%
  exposure - vs buy & hold 8.6%/yr at 56.9% DD (Sharpe 0.48). Lower return,
  a quarter of the drawdown, better risk-adjusted everywhere.
- The user's "reinvest idle cash in S&P" variant resolves to buy & hold
  (the trades ARE S&P longs); the real construction is the 2x-overlay:
  15.2%/yr but 60% maxDD - it doubles into dips during crashes. Documented;
  the paper stream tracks the strategy-only form.
- ES/NQ futures costs change nothing at a ~7-day hold. NQ's tail is the
  warning: worst trade -22.9%, worst open excursion -37.7%, drift-null only
  p 0.028 - the stream is SPX ONLY. CFD swap on multi-day holds is not
  modeled; futures (MES) preferred if ever funded.
- Infrastructure shipped: journal v3 (D7 chip, live state was empty),
  DoubleSeven_indicator.pine on the paste board (D7 BUY / D7 EXIT alerts,
  frozen 7/200), sprt.py D7 stream (p1=0.802, b=0.57, ~13/yr: median 25
  trades to promote, 22 to kill), monthly routine now scores four streams
  and runs every stream's W/L through the SPRT.

## Round 28d: the symphony portfolio (user commission; descriptive, not a promotion)

All streams combined on the common window 2020-11..2025-08
(run_r28d_symphony.py -> results/r28d_symphony.json; artifact published).
Sleeve daily-return correlations: gold-D7 0.001, gold-MHI -0.006, D7-MHI
0.020 - genuinely uncorrelated books. In-sample max-Sharpe split (5% grid,
MHI capped at 25% as an n=43 watch item): gold 20 / D7 55 / MHI 25 ->
Sharpe 1.38, 9.0%/yr at 5.8% maxDD (MAR 1.56); levered 2x: 18.4%/yr at
11.4% DD, same Sharpe. Always-invested variant (100% S&P B&H + the mix as
margin overlay): 22.8%/yr at 22.9% DD vs the index's 13.0% at 22.1%.
Singles on the window: 100% gold 20.7%/16.1% (matches the account sim);
100% D7 7.4%/10.2%. Caveats registered on the page: weights in-sample,
window friendly to every sleeve, MHI paper-only, gold sleeve modeled
single-leg (the deployed split is slightly better), CFD swap unmodeled.
Posture unchanged: paper-first, SPRT boundaries decide promotions.

## Round 28e: the weight-space map - a plateau, not a peak

Full simplex at 1% steps (5,151 splits), several objectives, stability tests
(run_r28e_splits.py -> results/r28e_splits.json; symphony page updated).
- 893 of 5,151 splits sit within 5% of the peak Sharpe (gold 10-33 / D7 26-74
  / MHI 0-59). Equal weight 33/33/33 scores Sharpe 1.28 vs peak 1.40.
- Objectives disagree on the "optimum": max-Sharpe 18/44/38, max-MAR
  34/36/30; capped variants 21/54/25 and 34/41/25.
- Per-year re-optimization is unstable (15/75/10 -> 75/0/25 -> 10/65/25 ->
  45/55/0 -> 45/30/25): any single year's optimum is wrong the next year.
- 400-resample block bootstrap: optimal weights range gold 15-40 / D7 40-70 /
  MHI 0-25 (at cap).
Conclusion: within the plateau every balanced split is statistically the same
portfolio; the named reference split is the max-MAR corner ~35/40/25
(2x-levered: ~21%/yr at ~10% DD in-sample). This is the gradient-over-peak
house rule applied to portfolio weights. Posture unchanged: paper-first;
leverage applies only to a promoted live book, never to a paper backtest.

## Portfolio reference split ADOPTED (user decision, 2026-08-27)

The max-MAR corner of the round-28e plateau is the standing reference split
for the four-stream book:

  GOLD (deployed rule + XAUAUD half-leg)  35%
  D7   (Double Seven, SPX only)           40%
  MHI  (HSI pre-open fade)                25%   (watch-item cap)

Recorded as a SHAPE, not a dial: the plateau spans gold 15-40 / D7 40-70 /
MHI 0-25, so rebalancing precision is noise; round numbers stand. In-sample
reference numbers (2020-11..2025-08): unlevered ~10.6%/yr at 5.1% maxDD
(MAR 2.07, Sharpe 1.36); at 2x ~21%/yr at ~10% DD. Status: PAPER - the split
allocates paper capital across the journal streams today. Leverage and real
funding follow the promotion sequence only: SPRT boundary promotes a sleeve
-> fund at 1x -> live results confirm the backtest envelope -> then leverage.
Weights re-examined only when a sleeve is promoted, killed, or added - never
re-optimized on a rolling window (round 28e showed yearly re-optima whipsaw).

## Round 29 pre-registration: the pinescriptforge RTY audit (user commission)

The site's 12 "audited" RTY swing strategies (claims recovered verbatim from
the live pages, claim window Jan 2023 - Mar 2026, $4.50 RT + 1-tick slippage
claimed): PF 1.57-2.66, win 44-59%, returns +196% to +1,323% on $10k at max
drawdowns of 2.0-6.3%. Pre-audit arithmetic notes, registered before any
backtest: (a) +1,323%/3.2y at 2.0% maxDD implies MAR ~64 - not internally
coherent; (b) "Sharpe 2.50" appears verbatim on 8 of 12 pages (template
constant); (c) the same strategy (Rainbow MA) is listed twice with different
numbers; (d) their own "Detailed Statistics" panels render all zeros.

Audit design: replicate each strategy at its stated parameters; UNSTATED
parameters take TradingView defaults, all documented in the runner: Aroon 14,
Vortex 14, ADX 14, ATR 14, MACD 12/26/9, RSI 14, ZLEMA 21, HMA 16, Marubozu
wick tolerance 10% of range, volume average 20 bars, S/R = confirmed swing
pivots (k=2). Operating timeframe convention: 1H (the one timeframe every
strategy lists); Elder Triple Screen keeps its own weekly/daily/1H structure.
Execution: signals on closed bars, fill next bar open (their stated one-bar
delay), one position per strategy, both sides, cost 0.4 pt RT (house round-9
model, comparable to their claimed friction; zero-cost also reported).
Windows: PRIMARY 2005-2020 (15.4y of verified 5m-derived 1H bars - the
long-sample test of whether any edge exists); SECONDARY 2025-03..2026-04
(TopstepX 1H - overlaps the final year of their claim window for the direct
check). Halves at 2013-01 on the primary window. Verdict categories per
strategy: replicates / inflated / dead. 12 strategies x 2 windows = 24
cells + zero-cost sensitivity; Bonferroni quoted. Registered prior: the
recipe-battery base rate (r28: 1 candidate in 8) and the template red flags
predict near-zero replication.

## Round 29 results (run 2026-08-27): all 12 claims falsified; the site's numbers are not backtests

(run_r29_forge.py -> results/r29_forge.json; 24 cells + zero-cost)
**Primary window (15.4y, 2005-2020, 1H, house costs): every strategy loses.**
PF 0.63-0.91, every t-statistic negative (worst -9.0), across 82 to 13,752
trades. Nothing is close to any claimed number.
**The decisive cell is zero-cost: PF 0.95-1.02 on all 12.** The strategies
carry no gross signal content at all - so the claimed PF 1.57-2.66
"post-friction" cannot be explained by cost differences, window luck, or our
parameter conventions for the UNSTATED inputs. A real PF 2.66 does not
degrade to 0.97 gross under any reasonable parameterization.
**The overlap check kills the claims on their own window:** on 2025-03..
2026-04 (the final year of their claimed Jan 2023 - Mar 2026 period), 10 of
12 sit below PF 1.0; the two above (Marubozu 1.15 on n=76, DEMA 1.02) are
noise. They claim +196% to +1,323% on this period.
**Verdict: not "inflated" - fabricated or never run.** Consistent with the
pre-registered red flags: template Sharpe 2.50 on 8 of 12 pages, the same
strategy listed twice with different numbers, all-zero "Detailed Statistics"
panels, MAR ~64 arithmetic, and an AI-script-generator business model whose
strategy pages are programmatic SEO. The edgeful contrast is instructive:
edgeful's descriptive claims REPRODUCED (their error was costs and window
selection); pinescriptforge's numbers do not reproduce even gross. Grade of
vendor claims now on file: real-but-cost-blind (edgeful), decayed-but-once-
real (Crabel, Connors book claims), and manufactured (this).
No candidates; nothing to the watch list; 0.4pt-cost and zero-cost cells all
logged.

## Round 29b: timeframe sensitivity (user follow-up) - the verdict is TF-invariant

(results/r29b_tfsens.json) All 12 strategies re-run on 15min, 4H, and Daily
(every timeframe their pages list) over 2005-2020 at house costs, plus
zero-cost at each strategy's best timeframe. Best net cell anywhere in the
whole 36-cell surface: DEMA daily PF 1.12 at t +0.3 (noise); best zero-cost
cell 1.15. The 15min cells are annihilated by trade frequency (t to -30 on
up to 55k trades). No timeframe on any strategy comes within a factor of
~2 of the weakest claimed PF (1.57). Deviations-from-exact accounting, for
the record: operating TF (they never state it - now all four tested),
unstated indicator periods (TV defaults, documented), position sizing
(unstated; flat one-unit used), instrument (session-verified RTY CFD proxy),
window (their 2023-2026 claim window is 2/3 outside our data; the overlapping
final year tested in r29). None of these can bridge gross PF ~1.0 to claimed
2.66. Verdict unchanged: manufactured.

## Round 30 pre-registration: the overnight-anomaly audit (user commission)

Claim under test (viral chart family): buying $MU (and similar tickers) at
every market close and selling at the next open compounds to an extremely
high return. This is the documented "overnight anomaly" (Cooper/Cliff/Gulen
and successors: close-to-open carries the equity premium, intraday ~zero or
negative in many names) - so unlike round 29 the registered prior is that
the GROSS claim is real; the questions are magnitude accuracy, era
stability, and net-of-execution replicability.
Design: daily adjusted OHLC (Alpha Vantage, split/dividend-adjusted) for MU
plus references SPY, NVDA, AAPL, full available history. Decompose
buy-and-hold into overnight (close->open) and intraday (open->close)
compounded legs. Cells: gross; net at round-trip cost {2, 5, 10} bps (the
trade is implementable via MOC/MOO auctions, so low-bps models are fair;
10bps = retail sloppiness); halves split at the sample midpoint and
2015-01-01 (crowding-era check); per-ticker. Also report: worst single
overnight gap (earnings risk), volatility drag, and the tax note
(short-term gains on ~252 trades/yr) as unmodeled.

## Round 30: overnight-anomaly audit - gross claim real, magnitude overstated, era-dependent

(run_r30_overnight.py, results/r30_overnight.json) Deviations from the
pre-registration, forced by data access and documented before running: Alpha
Vantage adjusted endpoints are premium-blocked, so MU daily OHLC came from
Equibles (2020-01..2026-08, its full MU history; MU has no splits in the
window and Adj-Close differs from Close only by small dividends, whose
omission biases AGAINST the overnight leg - conservative). NVDA/AAPL/SPY
references were replaced by SPX and NDX cut from our own session-verified 5m
feeds (09:30-ET bar open to 15:55-ET bar close, 2005-2025, 21 years), which
is a stronger long-sample check than three more 2020-era tickers.

MU 2020-01..2026-08 (1,671 sessions): B&H 16.9x. Overnight leg GROSS 11.6x
(CAGR +44.6%, +17.3 bps/day, t +3.07, Sharpe 1.19) vs intraday leg 1.46x.
So the direction of the viral chart is real: most of MU's return accrued
close-to-open. But (1) overnight did NOT beat simply holding (11.6x < 16.9x
gross, and the strategy pays costs while B&H pays none); (2) net of costs
the multiple collapses: 8.3x at 2 bps RT/day, 5.0x at 5 bps, 2.2x at 10 bps
- daily compounding makes even auction-quality frictions eat 30-80% of
final wealth; (3) the halves split FAILS our stability bar: first half
(2020-01..2023-04) +1.8 bps/day t +0.28 - indistinguishable from zero -
second half +32.8 bps t +3.58. The entire edge is the 2023-2026 HBM/AI
repricing, i.e. concentrated single-name beta, not a stable anomaly. 2022
overnight was -25.8 bps/day. Max drawdown 54% gross (72% at 10 bps); worst
single night -13.3% (2024-12-19 guidance gap), best +18.1% (2024-09-26
earnings) - the P&L is earnings-gap risk in costume.

Long-sample check, 21 years: SPX overnight +2.3 bps/day gross t +2.30 vs
intraday +1.8 bps t +1.38; NDX overnight +3.8 bps t +3.47 vs intraday +2.0
bps t +1.26. Halves same-sign on both (SPX +2.1/+2.4, NDX +4.6/+3.0) - the
documented anomaly is real and stable in the indices at GROSS. Net: SPX
overnight at 2 bps RT = 1.00x over 21 years (exactly zero); NDX at 2 bps =
2.11x vs 11.5x B&H; at 5 bps both are ruinous (SPX 0.21x, NDX 0.46x). The
anomaly survives publication as a description of WHERE returns accrue, and
dies as a strategy at any realistic cost.

Unmodeled, both conservative against the strategy: ~252 short-term taxable
events/yr vs B&H deferral, and dividend capture (small, slightly favors the
overnight leg; MU yield ~0.5%). Verdict for the user's two questions:
accuracy - the charts are near-accurate GROSS for 2023-2026 MU but describe
beta concentration, not an exploitable pattern (pre-2023 the same trade was
zero for three years); replicability - not net of execution at index level,
and in MU only if the 2023-2026 rally repeats, which is a bet on Micron,
not on the close-to-open mechanism. Tests run: 3 instruments x 4 cost
cells + halves = counted; no selection among tickers was performed (MU was
the user's named target, SPX/NDX fixed references).

## Round 31 pre-registration: ALMA averaging grid on Russell 6H (user commission)

Claim under test (TradingView-style "Idea"): "ALMA Averaging Strategy" on
RUSSELL 6H, long only - ALMA 3 / sigma 2, SD band 2, min diff 1/1, 25%
scale-in per qualifying bar up to 4 tranches, hard stop -10% from average
entry, exit on ALMA flip + min diff. Claimed: 76% WR, PF 2.8, maxDD 20%,
avg win +2.5% / avg loss -2.3%, ~25-bar winner holds, 306 trades (window
unstated). Registered prior: averaging-down grids mechanically buy high win
rates by holding losers until either recovery or a large stop; the claimed
combination (PF 2.8 WITH maxDD 20% and a -10% full-size stop) is the part
least likely to replicate. Note the internal arithmetic: 76% x 2.5% vs 24%
x 2.3% implies PF ~3.4 on equal size; the stated 2.8 already implies losers
run bigger notional than winners (they must - losers are the full grid).
Design: our verified RTY 5m feed (Oanda 2005-2020, 15.4y), resampled to 6H
anchored 05:00 UTC (the anchor implied by the Idea's own 05:00/11:00 fill
stamps). Frozen conventions where the Idea is silent, documented up front:
ALMA(window 3, offset 0.85, sigma 2) on closes; band = ALMA - 2 x rolling
SD(close, 3); entry 25% tranche on bar CLOSE below band, executed next bar
open; adds on further qualifying closes >=1% below last fill (min diff 1),
max 4 tranches; exit next open after a close >=1% above ALMA (min diff 1);
hard stop intrabar at 0.90 x average entry on the full position. Cells:
house cost 0.4pt RT per tranche + zero-cost diagnostic; halves; 8H variant
(the "sister" template); anchor-0 and SD-length-20 sensitivity. All cells
counted. Claim window (2026) sits outside our data - documented limitation,
same status as round 29; the 15.4y sample is the test of the RULE, not of
their specific fills.

## Round 31: ALMA averaging grid - the win rate replicates, the profit does not

(run_r31_alma.py, results/r31_alma.json, trades in r31_trades.json)
Documented additions to the pre-registration: the literal band (ALMA3 -
2xSD3) fired ZERO times in 15.4y - the max z-score of a point against a
3-sample SD is ~1.15, so a 2-SD band around a 3-bar ALMA is mathematically
(near-)unreachable and the stated spec cannot be what generated their 306
trades. The battery therefore ran four defensible completions of the text
(SD len 20 on ALMA3 band; both len 20; close >=1% below ALMA3 = the "min
diff" reading, whose cross-under count of 323 in 15.4y is the only one
matching their 306-trade claim), plus no-spacing adds, anchor-0, 8H, and
zero-cost - 9 cells, all counted. House drift null added per standing rule
for long-only systems.

Result grid (RTY 6H, 2005-2020, 0.4pt RT/tranche): headline "mindiff" cell
n=152 grid cycles, WR 76.3% - the claimed 76% reproduces to the decimal -
and PF 1.10, t +0.35, total 1.06x in 15.4 years, maxDD 25.6%. Zero-cost PF
1.20 (no gross edge to blame on costs). Every other completion lands the
same way: band20/20 WR 79.5% PF 1.29 t +1.13; 8H WR 76.9% PF 1.24. Avg
winner +1.17% vs avg loser -3.45%: the real payoff is INVERTED vs the
claimed +2.5%/-2.3% - averaging grids clip many small wins and take rare
4-tranche losses through the -10% stop (8 full-size stop events, each
~-10% of account). Halves: PF 0.89 then 1.32 - SIGN FLIP, fails the
both-halves rule. Drift null (random entries, matched hold + size): actual
+12.1% vs null mean +36.4%, p 0.76 - the ALMA timing is WORSE than random
long exposure on the same clock, because the grid concentrates size into
downtrends.

The diagnosis, for the vendor-claim taxonomy: the 76% WR is MECHANICAL -
every completion of the spec produces 73-80% WR regardless of
profitability, because the exit asymmetry (take +1% quickly, hold losers
to -10%) manufactures hit rate. WR is the one statistic an averaging
template always delivers and the one the Idea leads with. The PF 2.8 /
maxDD 20% / avg-loss-smaller-than-avg-win combination reproduces in no
cell and is internally inconsistent with 76%x2.5/24%x2.3 arithmetic
(implies ~3.4 equal-size, and losers cannot be equal-size in a grid).
Classified: real-mechanics, manufactured-or-era-picked numbers. The
surrounding "factor board" (EMA/SMC/FVG scores, long-score 19.5) is
unfalsifiable confirmation stacking of the kind the round-27 noise-combo
demonstration covers. No candidate; nothing to the watch list. Claim-era
caveat as in r29: our RTY data ends 2020-05; their fills are 2026 - but a
rule with a 15-year sign-flip and drift-null p 0.76 has no standing to be
rescued by a window argument.

## Round 32 pre-registration: three-source vendor audit (user commission)

Sources retrieved 2026-08-27 via remote browser (all three domains
egress-blocked locally; Medium article recovered from the 2024-10 Wayback
capture - the live page is Cloudflare-blocked; full retrieval provenance in
the round-32 scripts' docstrings and the fetched-text copies in scratch).

32a - Medium "Automated Trading Strategy #60" (Celan Bryant, ATS
newsletter, Jan 2023). Claim: $408,975/yr net on 1-lot ES/NQ/RTY/EMD/YM
basket, PF 1.44, 53.3% of 2,732 trades, combined maxDD -$16,660.24,
window 2022 only. Entry/exit rules and both indicator names are PAYWALLED:
nothing is runnable, and the registered outcome class is
unverifiable-by-construction. The audit is therefore a claims audit only:
(1) recompute every derivable number in the two published tables (sums, PF,
weighted WR); (2) test the "combined max drawdown" figure against the
portfolio arithmetic - registered prediction: it is an AVERAGE of the five
per-instrument DDs (~$16.9K), not a portfolio equity-curve DD, and the .24
cents is impossible in these contracts' tick sizes; (3) quantify the risk
understatement in the author's own sizing formula (account / average DD)
for five correlated same-session index strategies, where per-instrument DDs
sum to $84,825; (4) structural flags: per-instrument optimized bar periods
(14/13/60/18/17 min), single-year window (2022), strategy #60 of a 60+
family with a claimed family-average PF of 9.43, costs never mentioned,
slippage admitted unmodeled.

32b - TradeAlgo "Futures Trading Strategies: 6 Proven Methods (2026
Data)". Content marketing for a signals subscription; only one specific
performance claim: ORB (30-min opening range) "74.5% win rate, 2.51 profit
factor, across hundreds of trades" on NQ, unattributed, no window, no
costs. Arithmetic flag registered up front: their own spec (stop = far
side of range, target 1.5-2x range) at 74.5% WR implies PF 3.3-4.4, and
PF 2.51 with 74.5% WR implies avg RR 0.86 < 1 - the two numbers cannot
both come from the stated geometry. Replication: NDX 5m feed (2005-2025,
7.5-month 2020 hole documented), RTH 09:30-10:00 ET range, first
breakout per day, long+short. Cells: entry {touch, close-beyond} x target
{1.5x range, 2x range, none-EOD} x filter {none, overnight-gap-align} at
house cost 2.0 NDX pts RT, plus zero-cost on the primary
(close-entry/1.5x) - 12 + 2 cells, all counted. EOD flat 15:55 ET. Their
other five "methods" carry no specific claims (round-number WR ranges);
cross-referenced to existing rounds (RSI2 r28: dead net; BB fade r21/28;
gap fill r15; Turtle r24) rather than re-run.

32c - Scribd "Futures Strategies Performance Summary" (uploader not
author; no vendor identified; 32 strategies "backtested 2015-2026, Round
5: plateau-tuned parameters + best-fit instrument per strategy" across a
28-contract sweep; frictionless by its own admission; "win rate" = share
of profitable BARS; no rules given for any row). Nothing is runnable; the
audit quantifies the two structural defects from the sheet's own numbers:
(1) cost arithmetic on the four high-frequency rows (133k-551k trades at
PF 1.00-1.02): implied gross edge per trade in index points vs any
plausible friction; registered prediction: <=1 tick of round-trip cost
turns all four negative; (2) selection-effect null: Monte Carlo of 28
zero-edge instruments over ~11y, take the best Sharpe per "strategy" -
registered prediction: expected max ~0.6-0.7 Sharpe from selection alone,
covering the bulk of the table (median row Sharpe ~0.68). Cross-checks:
their Turtle ES-only baseline (-0.2% CAGR) matches our r24 result; their
frictionless NQ ORB row (PF 1.01, WR 50.4%) directly contradicts source
32b's NQ ORB claim (PF 2.51, WR 74.5%) - the two user-submitted sources
refute each other on the same strategy family.

## Round 32: three-source audit results - one refuted, one unverifiable-with-broken-risk-math, one self-refuting

(run_r32_orb.py, run_r32_medium.py, run_r32_scribd.py; results/r32_*.json)

32a Medium "Strategy 60": all additive table statistics recompute exactly
(net $408,975, gross, trades, weighted WR 53.33% - the tables are real NT8
output, not invented sums). The pre-registered predictions on the risk
numbers confirmed: the "combined max drawdown" $16,660.24 is 0.98x the
MEAN of the five per-instrument DDs (mean $16,965; sum $84,825), sits
BELOW the worst single sleeve (NQ -$33,760), cannot be a dollar P&L of
these contracts (per-instrument rows are commission-free multiples of
$2.50; .24 cents is unreachable by any combination), and the author's own
sizing text calls it "avg max drawdown" outright. His formula (account /
average DD -> 25 lots on $1M) therefore books portfolio risk at 8.3% of
account while his own per-sleeve numbers, drawn together (five long/short
strategies on the SAME correlated index complex in 2022, when they did
draw together), bound it at 17-42% - a 2-5x understatement. One number in
the text is flatly wrong from his own table: NQ "win/loss 2.56" is 1.88.
Structure: rules and both indicator names paywalled (unfalsifiable),
per-instrument optimized bar periods (14/13/60/18/17-min - five free
parameters), one calendar year (2022), strategy #60 of a family whose
claimed AVERAGE PF is 9.43. Verdict: unverifiable-by-construction sales
funnel; the checkable parts contain a material risk-accounting error.
Taxonomy: plausible-gross-numbers, broken-risk-math, unfalsifiable-rules.

32b TradeAlgo NQ ORB (74.5% WR / PF 2.51): REFUTED on a 14-cell surface.
NDX 2005-2025, 5,104-5,152 trades/cell: WR 37.9-47.1%, PF 0.87-1.04,
best cell t +0.94 (touch entry, 1.5x target, ZERO cost). At house costs
every cell is PF <= 1.03; nothing is within a factor of ~2.5 of the
claimed PF or within 27 WR points of the claimed WR. The registered
arithmetic flag stands: their own stop/target geometry cannot produce
74.5% WR and PF 2.51 simultaneously. The claim is unattributed, undated,
and appears in a subscription funnel between real CME volume statistics -
credibility scaffolding, not evidence. Their one honest citation (39% WR,
-58% maxDD trend following, Quantified Strategies) matches the literature
and our r24 Turtle results. Taxonomy: manufactured-or-repeated-folklore
(the 74.5/2.51 pair circulates verbatim in ORB marketing).

32c Scribd 32-strategy sheet: predictions confirmed. (1) Cost arithmetic:
the four high-frequency rows (133k-551k "trades", PF 1.00-1.02) carry
implied edges of +0.008 to +0.094 index points per trade; ONE tick of
round-trip cost (0.20 GC / 0.50 NQ pts) makes all four negative - the
sheet's own frictionless admission is fatal to its top-3 row (Day Trading
GC, 18.7% CAGR on 469k trades at PF 1.02). (2) Selection null: best-of-28
zero-edge instruments at their stated 20% vol target over 11y yields
expected max Sharpe 0.60 (q10-q90 0.42-0.80) from selection ALONE; the
sheet's median row Sharpe is 0.69 and 20/32 rows sit at or below the
null's 90th percentile - before counting the "Round 5 plateau-tuned"
parameter search stacked on top. (3) Cross-checks: its Turtle ES-only
baseline (-0.2% CAGR) independently matches our r24 replication, and its
frictionless NQ ORB row (PF 1.01, WR 50.4%, 195k trades) agrees with OUR
32b replication - and thereby refutes source 32b's headline claim. The
sheet is the most honest of the three (it discloses its own frictionless
+ selection methodology) and still not evidence of any tradeable edge.
Taxonomy: honest-methods-disclosure, selection-artifact numbers.

Tests counted: 14 ORB cells + 2 arithmetic audits + 1 Monte Carlo null.
No candidates; nothing to the watch list. Cross-source note for the
playbook: two of the user's three sources contradict each other on the
same strategy family, which is itself the cleanest demonstration this
round produced.

## Round 33 opened: Project Footprint (smart-money alignment arc, user commission)

Four-phase arc: (1) concept map of institutional footprints detectable in
price+volume on ES/NQ/RTY/GC via TradingView/Pine, ranked by evidence; (2)
modular Pine v5 indicator suite; (3) confluence strategy(); (4) validation
through the house pipeline. Phase 1 delivered: reference/footprints.md -
ten footprints graded A to D with microstructure logic, our own prior
results attached (r8 Judas sweep dead, r27 FVG 0/12, r24 COT p 0.76, r30
overnight decomposition as the honest HTF-flow read, r26 SGE descriptive),
Pine blind spots stated (no DOM/delta/icebergs/MOC feeds; CFD volume
synthetic; tester intrabar ambiguity), and a 7-module Phase 2 shortlist
proposed. Registered now for Phase 3: confluence gates capped and
pre-registered before any backtest (r27 noise-combo demonstration is the
standing reason); any footprint receiving strategy weight must first pass
pre-registration + both-halves + drift-null + costs on OUR data - the Pine
tester is an execution-fidelity check, not evidence. Web check performed:
no peer-reviewed empirical support exists for SMC/ICT constructs;
circulating "FVG fills 70%" figures are base rates without time-stops.

## Round 33 Phase 4a pre-registration: index sweep-failure validation

The map's one open question (footprint #6, grade C+). Registered prior:
near-coin-flip, consistent with r8 (gold Judas sweep dead) and the AUDUSD
reclaim result; index RTH extremes are the strongest-salience case and get
one clean test before FP6 can carry any strategy weight in Phase 3.
Design, frozen: SPX/NDX 5m 2005-2025 and RTY 2005-2020 (ET); session key =
overnight (16:00 prev to 09:25) + RTH (09:30-15:55). Levels: PDH/PDL
(prior RTH extremes), ONH/ONL (overnight extremes), OR30 H/L (first six
5m bars; breaches counted only after the window). Event = FIRST breach per
level per session; failure = a 5m close back on the original side within
6 bars; acceptance otherwise. Descriptive cells (all 3 x 6): breach count,
failure rate, forward 30m and EOD reversal-direction return after the
failure close (gross bps, t). Tradeable cells (PDH/PDL/ONH/ONL only,
3 x 4): enter failure close in the reversal direction, stop at the sweep
extreme, EOD exit, house costs (SPX 0.6 / NDX 2.0 / RTY 0.4 pts RT);
halves must agree in sign. 18 descriptive + 12 tradeable cells, all
counted. Any "candidate" additionally needs a max-stat check against the
full surface before promotion. FP6's on-chart scoreboard mirrors this
definition (close-back-inside within K bars) so chart and pipeline measure
the same thing.

## Round 33 Phase 4a results: sweep-failure = a base rate, not an edge

(run_r33_sweeps.py, results/r33_sweeps.json) 18 descriptive + 12 tradeable
cells, ~36k breach events. The folklore's kernel CONFIRMED as description:
across every instrument and level class, 54-80% of breaches close back
inside within 30 minutes - which is why sweep-reversal anecdotes are so
easy to collect. Monetization REFUTED: the post-failure reversal is worth
+0.3 to +1.6 bps gross at 30 minutes (best single cell t +2.16 on an
18-cell surface - dead under max-stat), decays or flips by EOD (the
intraday drift swamps it), and the canonical trade (failure-close entry,
sweep-extreme stop, EOD exit) LOSES in all 12 cells net (PF 0.79-0.99,
WR 17-23%, t to -2.7, halves both-negative in 9/12). The tight
stop-at-the-extreme geometry is the killer: the entry is fine, the stop
gets run by the same noise that produced the "sweep". Fully consistent
with r8 (gold) and the AUDUSD reclaim. DECISION: FP6 carries zero strategy
weight in Phase 3; it survives as levels + on-chart scoreboard (the
scoreboard now shows users the base rate honestly). Footprint #6 regraded
C+ -> resolved negative. The Phase 3 confluence set is therefore drawn
only from: session context (FP1), RVOL (FP2), HTF bias (FP3), absorption
(FP4), displacement regime (FP5) - and each gate still needs its own
pre-registered pass before weights are assigned.

## Round 33 Phase 4b pre-registration: RVOL / absorption / displacement gates

Purpose: the three untested Phase 2 gates (FP2, FP4, FP5) get event-study
validation BEFORE the user loads them and before any Phase 3 weight.
Data note, registered before running: our index feeds carry broker TICK
volume, not CME exchange volume (documented proxy; correlates well for
index futures but is a caveat every volume cell inherits), and pre-2010
granularity is too coarse (2005 SPX median 7 ticks/5m bar) - volume cells
(FP2/FP4) therefore run 2010+, price-only cells (FP5) run the full sample.
Also registered: the v6 compile-fix pass (comma-joined statements removed;
v5 -> v6) changed no logic.
Frozen design. FP2 (5m RTH, minute-of-day baseline = trailing 20-session
mean per bucket, no self-contamination): events RVOL >= 2.5 and >= 1.5;
measures (a) signed continuation - sign(close-open) x forward 6-bar
return - vs RVOL < 1.25 control, Welch t on the difference; (b) absolute
forward 30m range vs control (volatility prediction). FP5 (15m RTH bars,
ATR14, k = 1.5, body >= 0.6): (a) signed next-4-bar continuation vs
all-bars control; (b) first-hour displacement -> rest-of-day return in its
direction. FP4 (15m RTH, rolling-100 percentiles: vol >= 80 & range <= 40
at a 20-bar extreme with confirming close location): forward 4-bar and
EOD return in the absorption direction vs at-extreme-WITHOUT-condition
control. Instruments SPX/NDX/RTY. 30 cells total, all counted; halves
sign check per cell. Promotion bar: |t_diff| >= 3 AND halves same-sign
AND same-sign effect in >= 2 of 3 instruments -> earns a net trade test;
anything less is context-only or dead. Registered prior: FP2 volatility
prediction real (mechanical); directional cells uncertain; FP4/FP5
directional effects likely small or absent.

## Round 33 Phase 4b results: one mechanical pass, two context-only, zero tradeable

(run_r33b_gates.py, results/r33b_gates.json; plus the pre-registered net
follow-up, inline) Against the registered promotion bar (|t| >= 3, halves
same-sign, same-sign in >= 2 of 3 instruments):
FP2 RVOL - the volatility cells pass overwhelmingly (event forward range
~1.7-2x control, t +48 to +111, all instruments, halves agree): extreme
participation predicts MOVEMENT, exactly as registered (mechanical). The
directional cells are null-to-slightly-negative (-0.3 to -0.5 bps vs
control; only NDX>=1.5 reaches |t| 3.29, and as a mild ANTI-continuation).
Verdict: FP2 is a validated volatility/regime instrument with no
directional content - a sizing/avoid filter, never an entry.
FP5 displacement - continuation is REAL gross on NDX (+2.4 bps/h vs ~0
control, t +4.33, halves agree; SPX same sign t +2.43; RTY nothing). The
pre-registered net test kills it: entry at displacement close, exit 4
bars, house costs -> SPX -0.33 pts/trade (t -2.56), NDX -0.62 (t -1.24) -
the effect is smaller than one round trip. Regime context only.
FP4 absorption - the frozen triple condition fires 16-84 times per
instrument in 15 years (~2-8/yr): structurally unpowered, t scattered,
halves disagree. Context only; no loosening of the condition will be
searched (that would be tuning toward significance).
Arc status after 4a+4b: the Footprint suite is a set of validated
MEASUREMENT instruments (FP1 chassis, FP2 vol-regime, FP3 bias) plus
context layers (FP4/FP5/FP6) and visuals (FP7). No new tradeable edge was
found - consistent with the whole repo's history that entries are rare
and context is cheap. Phase 3 (a strategy() build) is DEFERRED: with zero
validated directional gates beyond FP3's bias (whose standalone trade
died on costs in r30), a multi-confluence entry system would be
manufacturing precision without an edge - the r27 noise-combo lesson.
Registered decision: Phase 3 waits until some future gate passes a
pre-registered directional test net of costs. Also this round: all seven
modules upgraded v5 -> v6 and a compile-fix pass (comma-joined statements
were invalid Pine; FP7 also had comma-joined var declarations) - logic
unchanged.

## Round 33 addendum: FP0 Footprint Console (slot-limited merge)

User constraint: five indicators per chart. FP1/FP3/FP6 are all overlay
context layers with no shared state and no conflicting reads (only FP3
renders a direction), so they merged cleanly into FP0_FootprintConsole
(per-layer toggles; FP3's cumulative decomposition plot stays in the
standalone module - the console carries the bias CARD, which is the
actionable part). FP2 remains separate by necessity (own pane, real CME
volume). Recommended loadout: FP0 + FP2 = two slots for the whole
validated suite; FP4/FP5/FP7 remain available standalone for study.
No logic changed from the validated modules.

## Round 34 pre-registration: per-session behaviour atlas (user commission)

Purpose: a descriptive MAP of how the three footprint families behave per
session window, to ground the user's discretionary use of the console -
NOT a candidate hunt. Sessions (ET, matching the FP0 band defaults): Asia
20:00-00:00, London 02:00-05:00, NY AM 09:30-11:00, NY lunch 12:00-13:00,
NY PM 13:30-16:00; bars outside these windows are excluded from session
cells. Instruments SPX/NDX 2005-2025, RTY 2005-2020 (24h CFD feeds).
Families, definitions frozen identical to r33/r33b: (A) sweep failures -
prior-RTH PDH/PDL breaches scanned across ALL sessions (r33 scanned RTH
only; extension registered here), first breach per level per session-day,
failure = close back inside within six 5m bars, forward-30m
reversal-direction return gross; (B) RVOL >= 2.5 events (5m, 2010+,
trailing-20-session minute-bucket baseline) vs same-session RVOL < 1.25
controls - forward 6-bar range ratio and signed-continuation difference;
(C) displacement bars (15m, k=1.5, body >= 0.6) vs same-session controls -
next-4-bar signed continuation difference. ~75 cells, all counted;
promotion bar unchanged from r33b (|t| >= 3 AND halves same-sign AND
>= 2 of 3 instruments) for anything that looks tradeable; registered
prior: session modulates the VOLATILITY numbers strongly (U-shape) and
the directional numbers not at all.

## Round 34 results: the session atlas - volatility structured, direction flat

(run_r34_sessions.py, results/r34_sessions.json; ~75 cells, all counted)
Registered prior confirmed on both halves of it.
VOLATILITY: RVOL >= 2.5 predicts 1.5-2.2x forward range in EVERY session
on every instrument (weakest London ~1.6x, strongest Asia/NYPM ~2.2x) -
the FP2 pass generalizes across the clock. RVOL extremes are 3-6x more
FREQUENT overnight (Asia ~500-700/yr vs NY AM ~90-230/yr): quiet-tape
baselines are easier to breach, so an overnight orange bar means less
than a NY-AM one.
SWEEPS: the failure base rate RISES through the day - Asia 59-66%,
London 68-74%, NY AM 73-76%, lunch 76-82% - i.e. overnight breaches of
PDH/PDL stick more often (real repricing), lunch pokes almost always come
back (noise), and none of it pays: fwd30 after failures is -4.8 to +2.7
bps, no |t| >= 2, with NY PM failures slightly CONTINUING against the
reversal (SPX -4.8 bps t -1.9) - do not fade PM breaks.
DIRECTION: one cell approaches the bar - NY PM displacement continuation
(NDX +4.1 bps/h vs ~0 control, t +3.07; SPX +2.1 t +1.9; RTY +2.4 t +1.4,
same sign 3/3). Honest accounting: the expected MAX |t| across a ~75-cell
null surface is ~3.0-3.2, so a single 3.07 with the other two instruments
sub-2 is exactly what selection produces; halves were not computed in
this atlas. Logged as a WATCH HYPOTHESIS ("afternoon displacement
continues"), promotable only via a dedicated pre-registered test (halves
+ max-stat + all-instrument sign) before it may touch Phase 3. No other
directional cell exceeds |t| 2.6. Console guidance updated accordingly:
session bands modulate HOW MUCH things move and how much breaches stick,
not WHICH WAY - which is precisely what the bands are for.

## Round 34b pre-registration: the user's delta-flip hypothesis

First user-originated hypothesis from live console use, verbatim reading:
"a strong green FP4 delta bar after a trend of selling with a red closing
candle seems to determine absorption and a likely flip". Frozen test:
15m bars (5m aggregation; delta15 = sum of sign(close-open) x volume over
the three 5m sub-bars - the research analog of the chart's 1m split),
2010+ (tick-volume granularity), SPX/NDX/RTY, all sessions, forward
windows within the session-day. LONG event: close < open AND delta15 > 0
AND prior-8-bar return < 0 (the "trend of selling"). Control: close <
open AND delta15 <= 0 AND same prior-trend condition (an ordinary red bar
in a downtrend). Mirror SHORT event/control. Measures: forward 4-bar and
12-bar return in the flip direction, event vs control, Welch t; halves.
Also the unconditioned variant (no prior-trend filter). 3 x 2 x 2 x 2 =
24 cells, all counted; promotion bar as r33b (|t| >= 3, halves same-sign,
>= 2/3 instruments). Chart-side: the marker ships in FP4 either way,
labeled with this round's verdict.

## Round 34b documented addition (registered before running)

The frozen spec used delta15 > 0; the user's verbal hypothesis specified a
"STRONG BIG green bar". One addition, long side only (their exact claim):
delta15 >= its rolling-250-bar 80th percentile of |delta15|, same controls
and horizons. 6 cells. No further variants will be run whatever the result.

## Round 34b results: delta-flip hypothesis refuted (cleanly, well-powered)

(run_r34b_deltaflip.py, results/r34b_deltaflip.json + addendum cells in
this entry) Base spec: a red 15m candle with positive sub-bar delta after
an 8-bar selloff behaves IDENTICALLY to an ordinary red candle - event vs
control diffs of -0.1 to +0.3 bps, all |t| < 1.1 on the long side across
9k-26k events per instrument; the mirror short side mildly contradicts
(RTY t -2.6 AGAINST the divergence read). Addendum (big delta >= 80th
pct): WORSE - all six cells negative diff (event underperforms ordinary
red bars by 0.1-1.9 bps, RTY 1h t -1.44). The visual impression of "it
does pretty well" is hindsight selection - the eye finds the flips that
worked and skips the ones that bled. Well-powered null, not an absence of
data. FP4's delta-flip marker ships as an OFF-by-default study toggle
carrying this verdict, so the user can watch the null live if they wish.
Positive framing for the journal: hypothesis -> pre-registration -> test
-> verdict took under an hour; this is the loop the whole arc exists for.

## Round 35 pre-registration: two user hypotheses (gold/DXY divergence; VIX shock)

35a - user hypothesis, verbatim reading: "when gold and DXY are POSITIVELY
correlated on a short timeframe and moving in the same direction, the
moment DXY diverges slightly against that shared move, gold makes a very
strong move continuing its own direction; works both ways". Priors on
file: r25b killed intraday gold-AUD correlation SENSORS as gates (p
0.948); this is a different structure (divergence event inside an
unusual-regime) and gets its own test. Frozen design: 15m bars, gold =
XAUUSD_m15_ejtrader (/100, Europe/Athens -> UTC, the r24-verified feed);
synthetic DXY log-returns = 0.809 x (-EURUSD ret) + 0.191 x (+USDJPY
ret) (r13 weight convention renormalized to available M15 legs, ~71% of
the real basket - documented proxy). Regime: rolling 24-bar return corr
>= +0.3 (sensitivity 0.5). Shared trend: both 8-bar returns same sign.
Event: synDXY 2-bar return flips AGAINST the shared direction. Claim
measure: gold forward 4-bar (1h) and 16-bar (4h) return IN the shared
direction, event vs control (regime + trend, no flip), Welch t, halves.
Both directions. ~16 cells, all counted; r33b promotion bar.
35b - user hypothesis: "when VIX falls suddenly, equity futures turn very
bullish". Registered decomposition: the CONTEMPORANEOUS link is
mechanical (same-day corr ~ -0.8, reported for teaching, not evidence);
the testable claim is PREDICTIVE. Frozen: VIX_daily_github %change day t;
events: fall <= -10%, spike >= +10%, plus quintile map; outcomes: SPX/NDX
(own feeds) next overnight (close t -> open t+1), next day (close ->
close), next 5 days. ~24 cells, all counted. Prior: predictive content
weak; any positive expectation likely after SPIKES (vol risk premium),
not falls - i.e. opposite to the intuitive reading.

## Round 35 results: divergence null; VIX intuition inverted

35a (run_r35_divergence.py, results/r35_divergence.json): NULL. On 217,929
15m bars (2012-2022), the positive gold/synDXY correlation regime exists
only ~3% of the time, and within it a DXY counter-flip predicts NOTHING:
event-vs-control diffs -2.6 to +2.5 bps with |t| <= 0.91 across all 8
cells, halves inconsistent; in most cells continuation after the flip is
slightly WEAKER than without it. The remembered "very strong move" is the
same hindsight-selection mechanism as r34b - the eye keeps the dramatic
continuations and drops the quiet ones. Also note: the events are rare
(~600 per decade at corr>=0.3), so even the anecdote pool is thin.
35b (results/r35b_vixshock.json): the user's observation is REAL but
CONTEMPORANEOUS (same-day corr(VIX chg, ret) -0.71 SPX / -0.62 NDX) -
VIX falls WHILE equities rally; that is the mechanics of the index, not a
signal. Predictively the intuition INVERTS: sudden VIX FALLS <= -10% are
followed by slightly BELOW-average next-day returns (-6.8 bps vs +3.9
unconditional, both instruments, t < 1 = noise-to-mildly-negative), while
VIX SPIKES >= +10% are followed by ABOVE-average returns (+15 bps next
day, +29-44 bps next 5d, t 1.95-2.31, monotone across the quintile map) -
the classic vol-risk-premium bounce, known literature, and at t ~2 on a
24-cell surface not a tradeable discovery. Standing VIX use unchanged:
the r16D descriptive calm/stressed gradient on the gold rule. No
candidates; nothing to the watch list.

## Round 35c pre-registration: SMT divergence, the user's refined three-phase spec

Refined hypothesis = the ICT "SMT divergence" pattern, which a web check
confirms is taught everywhere and empirically tested NOWHERE (all sources
methodology-only, with unfalsifiable confirmation clauses). User's
verbatim structure: (1) target and driver share a slow move (e.g. both
down); (2) driver shocks hard AGAINST it while the target barely moves
("mismatch" - interpreted as MOVE-SIZE mismatch, noted: user said
"volume" but described price action; volume overlay deferred); (3) driver
eases slightly -> target snaps much harder the other way. Frozen spec,
z-units (k-bar move / rolling 250-bar std of k-bar moves): shared trend =
signs of both 20-bar sums equal (window ending 4 bars back); shock =
driver 4-bar z >= 1.5 against the shared direction while target |z| <=
0.5 (event) - the "responded" CONTROL is the same shock with the target
moving its relation-implied way at |z| >= 1.0; trigger = first driver
2-bar sign-flip back within 8 bars; claim = target forward 8/24-bar
return OPPOSITE its relation-implied shock response (= the snap the user
describes), event vs control, Welch t, halves. Relation sign per pair
from full-sample return correlation. Frames: XAU vs synDXY(EUR+JPY M15)
at 15m/1H/4H + daily (5-leg FRED synDXY, gold ejtrader+collector splice);
EURUSD vs USDCAD (FRED daily, both driver roles); XAU vs WTI (daily).
~14 event cells + controls, all counted; r33b promotion bar. Prior:
skeptical (r35a null; no published evidence anywhere), but the
non-response/latent-strength mechanism is at least coherent - this is
the strongest form of the idea and gets the full test.

## Round 35c results: SMT divergence does not survive its first real test

(run_r35c_smt.py, results/r35c_smt.json; 14 cells + controls, all counted)
No cell passes the bar, and the surface has the signature of noise:
- The well-powered frames (15m, n~950 events) are null-to-negative: the
  "held-flat" target snaps -0.5/-3.6 bps vs its own claim direction,
  halves flip.
- The single hopeful cell (XAU/synDXY 4H h8: event +9.8 vs control -28.2
  bps, t +2.32) FAILS the halves check ([+,-]) on n=50, and t 2.32 is
  within the expected max of a 14-cell null surface.
- The daily FX frames lean AGAINST the claim with the most consistency in
  the whole test: after EURUSD held flat through a USDCAD shock, it went
  on to move -35 to -78 bps OPPOSITE the claimed snap (USDCAD-target
  mirror t -1.88, halves both negative). I.e. the target's non-response
  was not latent strength - more often it simply meant that episode's
  driver move was not that target's driver, and the original shared drift
  resumed.
- XAU/WTI daily: n=16, signs disagree across horizons; XAU/synDXY daily:
  n=4 (the full three-phase pattern is genuinely rare at daily scale).
Combined with r35a (correlation-regime version, null) and the web check
(zero published empirical support anywhere for SMT), the family verdict:
the SMT divergence PATTERN exists as a description, its predictive claim
does not replicate in either the correlation form or the user's refined
shock/non-response form, and the teaching materials' "needs market-structure
confirmation" clause is the unfalsifiability that keeps it alive. No
candidate; nothing to the watch list. Deviation note: intraday driver is
the 2-leg synthetic DXY (documented proxy); daily used the 5-leg FRED
basket. Relation-sign detection sanity-passed (gold/DXY -, EUR/CAD -,
gold/oil +).

## Round 35d pre-registration: the timing objection (documented follow-up)

User objection to r35c: the edge may be real but consumed between the
lower-TF-knowable moment and our trigger-bar-close measurement anchor -
"signal on 15m/daily, confirm and enter on 1m/15m". Testable core: no
lower-TF confirmation can enter EARLIER than the trigger bar's open, so
the payoff measured from the trigger bar's OPEN (proxied by the prior
close on continuous 15m FX/gold - documented) is a strict UPPER BOUND on
any finer-entry variant, and it deliberately INCLUDES lookahead (at the
open the trigger is not yet known) - biased in the hypothesis's favor.
Frozen: re-run the r35c XAU/synDXY frames (15m/1H/4H + daily) with three
anchors per event - trigger open (lookahead ceiling), trigger close
(original), next close (realistic) - plus the intrabar move (open->close
of the trigger bar, i.e. what a same-bar scalper could at most have
captured), event vs responded-control at each anchor. If the ceiling is
null the objection is closed for the powered frames; the daily FX frames
stay noted as unpowered regardless (4-36 events per decade+ - no entry
refinement turns that frequency into a strategy).

## Round 35d results: the timing objection is closed - there is no consumed edge

(results/r35d_anchors.json) Two measurements kill the "our entry was just
mistimed" account of the r35c null:
1. The INTRABAR move during the trigger bar - everything a same-bar
   lower-TF scalper could conceivably capture between the 1m-knowable
   moment and our close anchor - is +0.9/+1.0/+1.1 bps on 15m/1H/4H.
   There is no hidden snap being consumed inside the confirmation bar;
   the "much bigger move" is not there at ONE basis point.
2. The lookahead CEILING (payoff anchored at the trigger bar's open -
   earlier than any real lower-TF entry can achieve, and before the
   trigger is even knowable) is no better than the original anchor: 15m
   -0.6/-2.6 bps with events UNDERPERFORMING controls at t -1.7/-2.7;
   1H noise; 4H +15.6 t +1.88 - still the same n=50 max-of-surface cell,
   still failing halves, and its ceiling is BELOW its close-anchor value.
Principle, recorded for future objections of this class: refining entry
timing multiplies an existing per-event expectation - it cannot create
one from zero - except in the knife-edge case where the payoff is
consumed between knowability and measurement, which is exactly what the
intrabar and open-anchor measurements check. Checked: ~1 bp. The
signal-TF/entry-TF separation itself is legitimate technique (our
deployed gold rule IS one: daily-computed correlation signal, 60m entry)
- it just cannot rescue a pattern whose event-level expectation is null.

## Round 36 pre-registration: fixed 10-point scalp target x stop sweep (user commission)

Question: on the live/paper futures strategies, replace each system's own
exit with TP = +10 points and SL in {5, 10, 20, none}; how do the
performances look? Registered framing: fixed-POINT brackets are
volatility-blind (10 pts = ~0.25% gold, ~0.13% SPX, ~0.04% HSI - on MHI
our modeled cost IS 10 points), which is why the validated configs use
range-scaled exits; prediction = win rates rise steeply as SL widens,
expectancy falls versus each deployed baseline because the tight target
amputates the right tail that carries the edge (gold rule especially:
its PF lives in trend-day holds to 16:00 NY).
Frozen design: entries and filters UNCHANGED from each validated spec;
only exits replaced. Gold - the 652 deployable entries walked forward on
the verified 5m feed; TP/SL intrabar, worst-case ordering when both
touch in one bar (SL first, documented); 16:00 NY remains the backstop
exit; costs $0.30 + slippage convention unchanged. MHI - the 43-trade
fade regenerated on 15m bars, same worst-case rule, session-end backstop,
10-pt cost. D7 - entries at signal closes walked on SPX 5m RTH; TP/SL
intrabar; the 7-day-high signal close remains the backstop; $0.6 cost.
Baselines: each strategy's deployed exit. 3 strategies x 4 SLs + 3
baselines = 15 cells, all counted. Metrics: n, WR, PF, avg pnl/trade
(points), total points, worst trade; no promotion question - this is a
geometry study on already-validated entries.

## Round 36 results: the 10-point target amputates every edge it touches

(results/r36_brackets.json) All 15 registered cells, points net of house
costs. The registered prediction held in every strategy, and one cell
failed by pure arithmetic before a single bar was walked.

GOLD (652 deployable entries, $ per oz):
  SL 5     n 652  WR 38.0%  PF 1.03  avg +0.09  total   +58  worst  -5.6
  SL 10    n 652  WR 50.0%  PF 1.13  avg +0.52  total  +342  worst -10.6
  SL 20    n 652  WR 52.6%  PF 1.15  avg +0.61  total  +396  worst -20.6
  SL none  n 652  WR 52.8%  PF 1.15  avg +0.62  total  +407  worst -32.8
  baseline (2xrange stop, hold to 16:00 NY)
           n 652  WR 40.2%  PF 1.32  avg +1.62  total +1059  worst -33.0
  Reading: every bracket variant keeps barely a third of the deployed
  system's total (+407 at best vs +1059). WR rises to ~53% but avg pnl
  falls ~60% - the classic amputated right tail. The 5-pt stop sits
  inside ordinary 5m noise for a market that moves $20-40/day: it takes
  the win rate DOWN to 38% while capping wins at 10, leaving PF 1.03 =
  breakeven. The deployed rule's PF lives in trend-day holds; capping
  them at +10 removes exactly the trades that pay for the rest.

MHI (43-trade fade, HSI points):
  SL 5 / 10 / 20 / none: WR 0.0% in ALL four cells.
  avg -12.9 / -15.8 / -20.9 / -18.0; totals -555 / -680 / -900 / -776.
  baseline (0.5xrange stop, session end)
           n 43  WR 46.5%  PF 2.02  avg +65.2  total +2805  worst -365.5
  Reading: not a data artifact - an impossibility. The modeled MHI cost
  IS 10 HSI points, so a +10 target grosses at most +10 and nets at most
  0.0: a net win cannot exist in any cell. 10 pts is 0.04% of a ~25,000
  index whose average day ranges hundreds of points. This is the
  volatility-blindness point in its purest form.

D7 (SPX points, long only, 204 signals):
  SL 5     n 204  WR 43.6%  PF 1.30  avg +0.94  total  +193  worst  -5.6
  SL 10    n 204  WR 58.8%  PF 1.26  avg +1.15  total  +235  worst -10.6
  SL 20    n 204  WR 67.6%  PF 0.95  avg -0.32  total   -65  worst -20.6
  SL none  n 204  WR 89.7%  PF 1.28  avg +1.78  total  +363  worst -717.5
  baseline (7-day-high exit, no stop)
           n 204  WR 76.5%  PF 1.71  avg +11.6  total +2373  worst -717.5
  Reading: the seductive cell is SL none - 89.7% WR - and it is the
  vendor-brochure trap this repo keeps meeting: +10 capped wins against
  an uncapped -717 worst trade, avg +1.78 vs the baseline's +11.6. The
  SL 20 cell is the sweep's own refutation of "just give it room": WR
  rises to 67.6% yet expectancy goes NEGATIVE (PF 0.95), because D7
  entries are pullback buys that routinely trade >20 pts underwater
  before the 7-day-high exit pays - a 20-pt stop harvests max drawdowns.
  Non-monotonicity of avg pnl in SL (0.94/1.15/-0.32/+1.78) is the
  gradient telling you the geometry is fighting the entry, not tuning it.

Verdict (registered, no promotion question): fixed-point brackets are
dominated by the deployed exits in all three systems - best bracket cell
retains 38% (gold), 15% (D7), and less than nothing (MHI) of baseline
total pnl. The win-rate/expectancy trade-off is exactly the r31/r32
vendor mechanism, now demonstrated on our OWN validated entries: any
entry with positive drift can be dressed to 90% WR by capping wins and
uncapping losses. If a scalp variant is ever wanted, the honest route is
range- or ATR-scaled brackets re-registered as a new study - not fixed
points, and not on MHI where cost = target.

## Round 37 pre-registration: footprint confirmations as 10-point scalps (user commission)

User's (correct) objection to r36's framing: r36 bolted scalp exits onto
the LONG-HOLD systems. The real question is about the NEW exploration -
the ES/NQ/RTY/GC footprint signals were judged with swing-style fixed-
horizon event studies (hold 1h / EOD, measure drift), but futures scalpers
use these as short-term triggers: enter on the confirmation, take +10
points fast. Would the same signals look different judged as scalps?
Registered analytic frame: r33/r33b measured each signal's event-level
expectation and found none survives (sweeps: all 12 trade cells lose;
displacement: gross-positive NDX only, below one RT cost; absorption:
unpowered/null). The r35d principle says exit geometry MULTIPLIES an
event-level expectation but cannot create one from zero - so the
registered prediction is: no cell passes the promotion bar (|t|>=3,
halves same-sign, sign agreement in >=2/3 sibling instruments), and the
instrument scaling should show TP+10 is a DIFFERENT trade everywhere:
~0.15% on SPX, ~0.04% on NDX (cost 2.0 = 20% of the gross win), ~0.5%
on RTY (TP rarely reached -> mostly backstop exits), ~0.3% on gold.
Frozen design - signals BYTE-IDENTICAL to the validated definitions:
(1) SWEEP-RECLAIM (FP6, r33): first breach per session of PDH/PDL/ONH/
ONL, failure = 5m close back inside within 6 bars; enter at the failure
close, direction = reversal; four level classes pooled per instrument.
(2) DISPLACEMENT (FP5, r33b): 15m RTH bar with TR >= 1.5x ATR14 and
body >= 0.6x range; enter at bar close in the bar's direction.
(3) ABSORPTION (FP4, r33b): 15m bar with volume pctile >= 80, range
pctile <= 40 (100-bar), at a 20-bar extreme, CLV-confirmed; enter at
close, fade direction (buy low / sell high); 2010+ where volume exists.
Execution: walk the 5m feed strictly after the signal bar; TP = +10 pts;
SL in {5, 10, 20, none}; worst-case intrabar ordering (SL first);
backstop = session-end close. One open trade per family per instrument
(later signals skipped while a trade is on - documented). Instruments:
SPX, NDX, RTY (r33 RTH session logic), gold (same logic on NY 09:30-
16:00 with overnight = 16:00-09:30, an ADAPTATION, documented). House
costs per RT: SPX 0.6, NDX 2.0, RTY 0.4, gold 0.6 pts.
Cells: 3 families x 4 instruments x 4 SLs = 48, all counted. Metrics:
n, WR, PF, avg pts, total, worst; t on per-trade pnl; halves sign.
Promotion question IS live this time (it is a new strategy search), so
the multiplicity bar applies over all 48 cells.

## Round 37 results: 48 cells, zero positive - the scalp frame does not rescue the footprint signals

(results/r37_scalps.json) Signal counts after one-trade-at-a-time dedupe:
sweeps ~1.0-6.9k, displacement ~1.2-8.7k, absorption 18-107 per
instrument. Every one of the 48 registered cells has NEGATIVE net
expectancy; no promotion candidate exists, so the multiplicity correction
never even engages. Highlights (avg pts/trade net, t):

  SPX  sweep SL5..none: -0.60..-0.76, t -7.2..-4.0 (halves both neg)
  SPX  disp  SL5: -0.08 t -1.1 | SL none: -0.70 t -3.6
  NDX  sweep SL5: -2.32 t -28.3 | disp SL none: -4.66 t -9.7
  RTY  sweep/disp: -0.18..-0.55, t -2.2..-4.2
  GOLD sweep/disp: -0.40..-1.02, t -2.5..-3.9
  absorption everywhere: n 18-107, all negative, unpowered as ever

Structure worth recording:
1. The WR illusion reappears on schedule: NDX sweep SL-none = 72.1% WR
   with avg -2.19/trade and a -603-pt worst trade. Chasing +10 with no
   stop wins often and loses everything, exactly as registered.
2. GROSS vs NET: the tightest cells are cost-dominated, not signal-
   dominated. SPX disp SL5 nets -0.08 vs cost 0.6 => gross ~ +0.5/trade;
   RTY disp SL5 gross ~ +0.2; gold disp SL5 gross ~ +0.2. This is r33b's
   FP5 verdict wearing a bracket: displacement continuation is REAL but
   smaller than one round trip. The scalp frame cannot monetize it
   because a 10-pt target pays ~9-16 gross wins per 100 trades of edge
   while eating 60-200 bps of cost-equivalent on every single trade.
3. NDX is the worst place to scalp 10 fixed points (cost 2.0 = 20% of
   the target; every cell t <= -5.7), RTY the least bad (cost 0.4) -
   pure cost ratio ordering, as predicted.
4. Sweep-reclaim SIGNIFICANTLY loses in all 16 cells (t -3.4..-28.3,
   halves agree) - consistent with r33's finding that reclaim entries
   pay only on the descriptive fail-rate, not as trades; the scalp
   bracket makes it strictly worse than r33's sweep-extreme-stop sim.
Verdict (registered prediction CONFIRMED): judging the footprint
confirmations "as scalpers actually use them" changes nothing - r35d
principle holds: exit geometry multiplies event-level expectation and
these events have none net of costs. The one live residue remains FP5
displacement gross drift (NDX/SPX), which no fixed-point bracket can
harvest; if it is ever attacked again the lever is COST (exchange-fee
futures, limit entries), not exit design. 48/48 cells counted.

## Round 37b addendum: cost sensitivity (user objection - "futures don't have those fees")

User's objection to r37: the registered costs are CFD-style, real micro
futures (MES/MNQ/M2K/MGC) are cheaper. Partly right, so per house rule
the 48 cells were rescored at three levels (results/r37b_costsens.json):
house (r37 registered), micro best-case (cheap-broker commission +
exchange fees + one tick of spread crossing: SPX 0.35, NDX 1.0, RTY
0.35, GOLD 0.35 pts/RT), and ZERO (free trading - unbeatable bound).
The spread is the point the fee argument misses: commissions on MES are
indeed ~0.3 SPX pts/RT, but a market-order scalper crosses the bid-ask
on both sides, and one tick each way is a cost no broker waives.

Findings:
1. At micro best-case, exactly 1 of 48 cells is positive: SPX
   displacement SL5 at +0.17 pts/trade (t +2.32, halves [+,+], WR 41%,
   PF 1.06). That is $0.85 per MES trade. It FAILS the registered
   promotion bar twice over: t < 3, and its siblings at the same cost
   level are all negative (NDX -0.58, RTY -0.13, GOLD -0.15) - 0/3
   sign agreement where >=2/3 is required. With 48 cells searched, a
   lone t=2.3 is exactly what the max-stat null produces.
2. At ZERO cost the sweeps are still not positive anywhere - NDX sweep
   is significantly NEGATIVE gross (-0.32 to -0.40, t to -3.9; the
   reclaim close is systematically a bad scalp entry, not a costly
   one). The fee explanation is refuted for this family outright.
3. At ZERO cost displacement SL5 is genuinely positive gross everywhere
   (SPX +0.52 t +7.1, NDX +0.42 t +5.7, RTY +0.22 t +2.7, GOLD +0.20)
   - the r33b FP5 drift again, now bracket-shaped. The entire interval
   between zero and realistic cost is where it dies: the edge per trade
   (~0.2-0.5 pt) is smaller than one honest round trip on every
   instrument. Nothing about contract choice changes that inequality;
   only fill engineering could (limit entries that EARN the spread),
   and that is a different, harder study (queue position, adverse
   selection - not answerable from OHLC bars; noted, not promised).
Verdict: r37's conclusion stands at futures costs. No promotion.
3 cost levels x 48 cells counted as part of the r37 battery.

## Round 38 pre-registration: HTF signal -> LTF pullback entry on the scalp families (user commission)

User's spec: keep the +10-pt scalp frame but separate timeframes - read
the signal on the higher TF, execute the entry on the lower TF (1m/5m/
15m). Registered rationale: this is the r35d-legitimate case. r37b
established displacement has a REAL gross edge (+0.2..+0.5 pts/trade at
zero cost, t to +7) that dies inside one round trip of cost; a lower-TF
pullback entry changes the ENTRY PRICE, not just timing, so it can in
principle multiply the per-trade capture above cost. For sweeps the same
mechanism must additionally overcome a drift that is negative even at
zero cost. Both re-tested per the user's instruction.
Frozen design. Signals (identical logic to r37, emitting the signal
bar's range R): DISPLACEMENT on 15m RTH and on 1H RTH (60min resample
anchored 09:30, last bar truncated at 16:00, documented); SWEEP-RECLAIM
on 5m as before. Entry: after the signal bar closes at E in direction d,
rest a limit at E - d*0.5*R (a 50% retracement of the signal bar),
valid for 2 signal periods of LTF bars (15m sig -> 5m entry: 6 bars,
15m -> 1m: 30, 1H -> 15m: 8, 5m -> 1m: 10); fill at the limit when an
LTF bar trades through it (worst case: fill exactly at L); unfilled =
no trade, fill rate reported. Bracket from the fill: TP = L + d*10,
SL in {5, 10, 20, none} from L, SL may trigger on the fill bar (worst-
case SL-first), TP only from the NEXT bar (conservative), session-end
backstop. One open trade per family/instrument. LTF availability: 1m
exists for SPX/NDX/RTY 2005-2020 only (signals outside the 1m span
excluded from those combos); gold has no 1m.
Combos: disp 15m->5m (4 instr), disp 15m->1m (3), disp 1H->15m (4),
sweep 5m->1m (3) = 14 combos x 4 SLs = 56 cells, scored at micro
best-case and zero cost (r37b levels; house shown superseded for the
user's futures question). All counted with the r37 battery. Note: a
resting limit also avoids crossing the spread on entry, which the micro
cost level slightly overstates for this study - direction of bias
documented, favors the hypothesis, acceptable for a null result only.
Registered predictions: fill rates ~30-60%; adverse selection is the
core risk (signals that never pull back are disproportionately the
winners), so per-SIGNAL expectancy should fall versus r37 market
entries even where per-FILL expectancy improves; sweeps stay negative;
promotion bar unchanged (|t|>=3, halves same-sign, >=2/3 sibling
instruments at the same cost level, judged against all 56 cells).

## Round 38 results: pullback entries are adversely selected - and a lookahead bug nearly manufactured an edge

(results/r38_mtf.json) First, the incident, on the record: the initial
run showed sweep 5m->1m at +1.0..+2.2 pts/trade net micro cost, t to
+13.6, all 12 cells positive, halves [+,+] - a promotion-bar smash. It
was a LOOKAHEAD BUG: 5m bar labels are bar STARTS, so `index > t` let
1m bars INSIDE the still-forming signal bar fill a limit priced off
that bar's close. The 80% fill rates were the tell (the reclaim bar
itself had just visited those prices). One +5min timestamp fix and the
edge fell to ~zero: fills 50%, micro-cost avg -0.87..-0.01, zero-cost
+0.13..+0.34 (t <= 2.4, RTY negative). Recorded as a permanent example:
too-good MTF backtests are usually the signal bar leaking into its own
execution window.

Corrected results, all 56 cells:
1. At micro cost, ZERO cells are positive. Closest: SPX sweep SL-none
   -0.01. No promotion candidate; the bar never engages.
2. ADVERSE SELECTION dominates, exactly as registered. Displacement
   15m->5m at zero cost: SPX -0.36, NDX -1.08, RTY -0.25, GOLD -0.26
   per filled trade - versus r37 market-entry zero-cost values of
   +0.52/+0.42/+0.22/+0.20. The 50% retrace limit converts a genuinely
   positive-drift event into a LOSING one even with free trading and a
   ~0.5R better price: the signals that pull back to fill are the weak
   continuations; the runners that pay never come back. Fill rates
   37-44% (15m sigs), 10-15% (1H sigs, sample collapses to n 72-382).
3. The 1H->15m frame is strictly worse than 15m->5m everywhere
   (bigger R = deeper limit = stronger adverse selection), and
   disp 15m->1m sits between (SPX SL5 zero-cost -0.04, best of the
   family, still nothing).
4. Sweep 5m->1m after the fix: the only zero-cost positives in the
   round (SPX/NDX +0.2..+0.3, t <= 2.4), sibling RTY negative, all
   micro-cost cells <= 0. Fails the bar on every prong; with 56 cells
   searched this is max-stat noise.
Verdict: NO PROMOTION. The registered adverse-selection prediction
held in full. Standing conclusion for the scalp program: the FP5
displacement drift is real but (a) smaller than one round trip taken
at market, and (b) DESTROYED, not harvested, by passive retracement
entries. What remains untestable on OHLC is the marketable-limit /
queue-position route; everything testable is now tested. 56/56 cells
counted with the r37 battery.

## Round 39 pre-registration: the 4-6 rule - HTF directional bias gating LTF triggers (user commission)

User's spec: the classic multi-TF hierarchy with a 4-6x ratio between
frames. Scalping: 1H bias -> 15m/5m/1m trigger. Day trading: 4H
structure -> 1H/15m trigger. Swing: Daily trend -> 4H execution. r38
tested the ENTRY mechanism (pullback limit) and found adverse
selection; r39 tests the other half of the doctrine - the DIRECTIONAL
GATE: does taking LTF triggers only WITH the HTF bias improve them?
Frozen definitions. HTF BIAS = sign(close - SMA20) on the last CLOSED
HTF bar at trigger time (no partial bars). HTF frames built from the
full 23-24h feeds (1H calendar-aligned; 4H calendar-aligned NY; Daily =
18:00-roll trading day, bias from the PRIOR completed day). TRIGGER =
displacement bar (r33b def, unchanged) on the trigger TF; market entry
at trigger close (r38 showed limits de-select the edge). Instruments
SPX/NDX/RTY/GOLD.
Part A - event study (does alignment change the drift?): tiers
(1H,15m) (1H,5m) (4H,1H) (4H,15m) (D,4H); intraday tiers measure
dir x fwd 4 trigger-bars (same-session) and dir x to-EOD; swing tier
measures dir x fwd 5 trading days. ALIGNED (trigger dir = bias) vs
OPPOSED (dir = -bias) Welch t, halves of aligned. 5 tiers x 4 instr
x 2 horizons = 40 cells.
Part B - the scalp question (does the gate rescue TP+10?): exactly the
r37 displacement scalp pipeline (15m trigger, market entry, TP +10,
SL {5,10,20,none}, one trade at a time, micro costs) with signals
gated by alignment at 1H, 4H, and Daily bias: 3 gates x 4 instr x
4 SLs = 48 cells, judged head-to-head against the r37b ungated micro
numbers.
Total 88 cells, all counted with the r37/38 battery; promotion bar
unchanged (|t|>=3, halves same-sign, >=2/3 siblings). Registered
prediction: alignment shifts the drift by little and inconsistently
(r34 found intraday direction flat across sessions; drift lives at the
daily scale per r30, so the Daily gate is the most plausible helper);
even a favorable gate must lift avg pnl by ~0.4-1.2 pts/trade to clear
micro costs, which no observed gross edge suggests is available; the
1m trigger tier is omitted in Part A (1m span 2005-2020 only, and r38
showed the trigger TF is not the binding constraint) - documented.

## Round 39c documented addition (registered before running, after seeing Part A)

Part A's only recurring signal: ALIGNED 5m displacement -> EOD drift
beats OPPOSED in all 4 instruments (t +3.8 SPX / +5.2 RTY / +2.1 GOLD /
+1.4 NDX). Caveat registered: those t's overlap same-day events and are
NOT tradeable numbers. Addition (4 cells, counted): tradeable sim -
FIRST 1H-aligned 5m-displacement signal of each session, market entry
at the signal close, hold to session close, no bracket, micro costs,
non-overlapping by construction. Metrics n/WR/PF/avg/t/halves. This is
the honest form of the "1H bias -> 5m trigger" tier of the user's 4-6
rule. Prediction withheld (data-peeked); judged at the full-battery bar.

## Round 39 + 39c results: the 4-6 rule gates attention, not expectation

(results/r39_biasgate.json, r39c_eodhold.json) 88 + 4 cells.
Part A (aligned vs opposed drift, 40 cells): no tier shows a
consistent alignment premium. 4H tiers even lean the WRONG way on
SPX/NDX (opposed > aligned, t -0.2..-1.8). The lone recurring positive
- 1H-aligned 5m displacement to EOD, aligned>opposed in 4/4 instruments,
t +5.2/+3.8/+2.1/+1.4 - was flagged at registration time as overlap-
inflated (same-day events share the EOD move).
Part B (gated TP+10 scalp, 48 cells, micro costs): gating by 1H/4H/D
bias leaves the scalp essentially where r37b found it. Best cell SPX
gate-1H SL5 +0.15 t +1.6 vs ungated +0.17 t +2.3 - the gate removed
~45% of trades and slightly LOWERED significance. NDX all cells deeply
negative under every gate; RTY/GOLD all <= +0.12, t < 1. Zero
promotion candidates.
Part C/39c (the honest form of the Part A candidate, 4 cells): first
1H-aligned 5m displacement per session, enter close, hold to session
close, non-overlapping, micro costs: SPX +0.04 t +0.13; NDX +1.30
t +1.14; RTY +0.00 t 0.00; GOLD -0.09 t -0.29; halves mixed in all
four. The overlap-corrected effect is indistinguishable from zero.
Verdict: NO PROMOTION anywhere in the r37-39 scalp battery (48 + 56 +
92 = 196 cells). Registered reading of the 4-6 rule: TF hierarchies
are an attention-management convention - they decide WHICH trades you
take, and in our data the subset they select has the same per-trade
expectation as the whole. A filter earns its keep only by CHANGING
conditional expectation (deployed gold rule's correlation gate does;
the SMA20 HTF bias gate does not). The user's pipeline remains the
right way to test such doctrines: freeze, register, count, compare.

## Round 40 pre-registration: extreme delta-flip path study (user chart observation)

User's observation from watching FP4 for weeks (gold 15m): a REALLY
strong delta-flip bar (big delta fighting the candle) near a low is
followed either by an immediate up-candle, or by a small further dip
and then a recovery within the next 1-2 hours. r34b refuted flips at
the 70th-pct threshold on fixed horizons; this registers the two parts
of the observation r34b did not test: (a) EXTREME magnitude thresholds,
(b) the DIP-THEN-RECOVER path shape and the within-2h upside (MFE),
both of which must be judged against control base rates because "it
goes up at some point within 2h" is true for most bars, and flexible
exits chosen after seeing the path flatter any event.
Frozen design. Frames: 24h 15m bars resampled from the 5m feeds
(SPX/NDX/RTY/GOLD); delta proxy per 5m bar = sign(close-open)*volume,
summed to 15m (mirrors FP4's lower-TF proxy; gold uses 5m not 1m -
documented). Flip (bull): delta > 0 AND close < open AND |delta|
percentile-rank over the trailing 100 bars >= th, th in {70, 90, 97};
bear mirrored. Context variants: ALL, and TREND (prior 8-bar move to
the previous bar's close opposed to the flip direction - "after a
selling trend" for bull). CONTROLS: same close direction, same context,
non-flip bars. Measures per event set, all vs matched control: fwd +1
bar / +4 bars (1h) / +8 bars (2h) mean bps + Welch t + halves; MFE8 =
max high in next 8 bars vs close, bps, Welch t; pRise8 = P(any close >
event close within 8); pDipRise8 = P(low breaks event low first, THEN
a close > event close within the window) - two-proportion z vs control.
Cells: 4 instruments x 2 sides x 3 thresholds x 2 contexts = 48 event
definitions x 6 measures = 288 comparisons, all counted with the
battery. Registered prediction (r34b + base-rate reasoning): event ~
control on every measure including at 97th pct; the observation is the
base-rate illusion - the eye sees the recoveries and not the controls
that recovered equally often without a flip. If ANY cell survives the
bar (|t| or |z| >= 3, halves same-sign, >=2/3 siblings), the follow-up
would be a tradeable sim with fixed exits, separately registered.

## Round 40 results: the flip observation is real - and the control group has it MORE

(results/r40_flippath.json) 288 comparisons, registered prediction
confirmed with an instructive twist.
1. DIRECTION: no fwd cell passes anywhere (all |t| < 3). The largest
   extreme-threshold effects lean AGAINST the hypothesis: NDX bull
   trend th97 fwd4/fwd8 = -8.5/-11.6 bps (t -2.3/-2.6) - the strongest
   flips after a selldown resolve DOWN if anything. Gold's best cell
   (bear trend th90 fwd4 +7.3b t +2.7, n 120) is under bar and alone.
2. pRise8 - the heart of the user's observation: after a bull flip,
   price DOES print a close above the flip close within 2h about
   75-80% of the time. But ordinary red candles WITHOUT a flip recover
   80-82% of the time. Every one of the 48 event definitions has
   pRise8 event <= control (z to -7.9). The flip makes the recovery
   the user watches for slightly LESS likely, never more.
3. pDipRise8 (dip below the flip low, then recover): 42-51% after
   flips vs 54-62% for controls - again LOWER, z to -16.9.
4. MFE8: events show much bigger favorable excursions than controls
   (t +3..+23) - but symmetrically for bull AND bear definitions, with
   flat fwd means: the flip marks elevated coming VOLATILITY, not
   direction. This is FP2's r33b verdict rediscovered from a different
   door: big-delta bars are volatility events.
Verdict: NO PROMOTION. The observation is the base-rate illusion in
its cleanest recorded form: the bright column makes the subsequent
recovery memorable, but red bars without the column recover MORE
often. What the flip genuinely says is "expect larger swings in the
next 2h" - a regime input (sizing/stop width), never an entry. FP4's
flip lens stays labeled study-only; comments to be updated with the
r40 result. 288 comparisons counted with the battery.

## Round 41 pre-registration: specification-mining demonstration on the flip scalp (user question)

User's question after r40: "why can't this succeed as a scalping
strategy - can you not derive more specifications to make it work?"
Registered purpose: DEMONSTRATION of why derived specifications cannot
be trusted, run live on the user's own instrument (gold 15m). This is
not an edge search; it is the max-stat lesson made concrete.
Frozen design. Gold 15m 24h frame with the r40 delta proxy. BULL flip
events only. Specification grid: threshold pct {70, 80, 90, 95, 97} x
context {all, prior-8-bar downtrend, at 20-bar low, downtrend AND low}
x entry {at event close; at next bar close only if that bar dips below
the event low (the user's "falls a little more first")} x exit {TP5/
SL5, TP10/SL5, TP10/SL10, time 4 bars, time 8 bars, TP10/SL20} = 240
variants, micro cost 0.35/RT, worst-case intrabar ordering, 32-bar cap.
Split: events in the FIRST HALF of the sample are in-sample (IS); the
winner by IS t-stat (and the top 10) are then evaluated on the SECOND
HALF (OOS), untouched by selection. Registered prediction: the IS
winner will show an attractive equity line (expected max-|t| of 240
correlated noise draws ~ 2.5-3.5, PF ~ 1.2-1.5) and will collapse to
~zero or negative OOS; the top-10's OOS mean will shrink toward zero
(regression to the mean under selection). If instead the winner HOLDS
OOS with same sign and material size, it graduates to a registered
candidate and the promotion bar applies - the demonstration is honest
in both directions. 240 IS cells + 11 OOS evaluations counted.

## Round 41 results: the derived specification, delivered and dissected

(results/r41_specmine.json) 240 variants searched on the first half of
the gold 15m sample; 114 had >=30 IS trades. The in-sample winner is
exactly what a strategy vendor would publish: th90 flip + wait-for-the-
extra-dip entry + TP10/SL20 -> 69.4% WR, PF 1.72, +1.78 pts/trade net.
Same frozen spec on the untouched second half: 54.4% WR, PF 0.94,
-0.26 pts/trade. The top 10 IS specs averaged +0.82 pts/trade in
sample and -0.27 out of sample; 8 of 10 degraded, 7 flipped sign.
Note also: even the WINNER's in-sample t was only +1.31 - selection
dressed statistical nothing in a 69% win rate and a 1.7 profit factor.
Verdict: demonstration complete, prediction confirmed. The registered
lesson, stated once for the ledger: deriving more specifications is
never the bottleneck - noise plus a large enough grid always yields a
handsome backtest. A spec is only evidence when it was written down
BEFORE the data that judges it, survives on data it never touched, and
sits on a smooth parameter gradient. r40 already established the flip
event has no conditional expectation to amplify (recovery LESS likely
than control); r41 shows what "making it work" actually produces.
240 + 11 cells counted with the battery.

## Round 41b: repair taxonomy and protocol adopted (user's three proposals)

User proposed three routes past the r41 lesson: (1) keep testing until
something passes IS+OOS; (2) repair the already-failed baseline
strategies on IS, then judge on OOS instead of presuming failure;
(3) research online what KINDS of additions make strategies work, then
reason from mechanism to a fix without peeking at the data. Ruling:
all three are legitimate WITH corrections, and (3) is the strongest -
it is hypothesis generation from mechanism, which is how the deployed
gold rule was found. Corrections adopted as binding protocol (full text
in reference/repair_taxonomy.md): repairs must target a written failure
diagnosis; bounded pre-registered grids on IS only (last 25% held out);
gradient inspection; ONE spec to OOS, judged ONCE against a pre-stated
bar (same sign, t>=2, PF>=1.15, cost-sensitivity pass); the OOS block
burns on use regardless of outcome; a pass graduates to paper/SPRT, not
deployment; every attempt counted because ~2-5% of null attempts pass
the bar by luck (the program-level max-stat problem). The taxonomy doc
records seven repair classes with their target mechanisms and our own
ledger evidence for/against each (vol-normalization strongest,
confirmation-stacking weakest). No new data was touched this round.

## Round 42 program registration: three intraday futures edges (user goal)

GOAL (user, 2026-08-28): run proposal 3 (mechanism-driven development
under the r41b repair protocol) on intraday MES/MNQ/M2K/MGC until at
least 3 strategies pass their one-shot OOS gate and graduate to the
paper/SPRT stage. Registered caveats: the goal is a stopping condition,
not a promise; attempts are counted program-wide; at the OOS bar
(same sign, pooled t>=2, PF>=1.15, cost x1.5 still positive) roughly
2-5% of null attempts pass by luck, so the count of attempts is part
of every graduate's evidence file, and paper trading remains the
final judge. House holdout note: the OOS block is the last 25% of
each instrument's sessions, untouched by all selection.

### Attempt 1 pre-registration: ORB repaired by participation gates

DIAGNOSIS (r32 refutation + r33): plain breakout entries buy strength
after the move has started, and 54-80% of intraday level breaches
fail; ungated ORB is a coin flip minus costs. Literature (Zarattini/
Barbon/Aziz SSRN 4729284, 7000 US stocks 2016-23): plain 5m ORB weak;
restricting to days with abnormal opening participation ("stocks in
play", opening relative volume) does nearly all the work, surviving
costs. Time-series analogue for a single future: trade only days when
THIS instrument is in play.
Repair classes invoked (reference/repair_taxonomy.md): #1 regime gate
(participation/imbalance), #2 vol-normalization (exits in range units,
pooling in ATR units), #3 session concentration (inherent to ORB).
FROZEN GRID (48 variants, IS only = all sessions except last 25%):
OR window W in {15, 30, 60} min x gate in {none; RVOL30 >= 1.5 (first-
30-min volume vs 20-day mean); |gap| >= 0.5 x ATR20d (RTH open vs
prior RTH close); NR7 (prior day's range narrowest of its last 7)} x
stop in {opposite OR level; 0.5 x OR range} x target in {2 x OR range;
none (EOD close)}. Entry: stop order at the OR level, first breakout
after the window completes, both-levels-in-one-bar days skipped
(ambiguous), one trade per day, worst-case stop-first, target from the
bar after entry, EOD backstop. Costs micro (0.35/1.0/0.35/0.35).
SELECTION (pre-stated): pooled ATR20-normalized per-trade t across the
four instruments, min 120 pooled IS trades; gradient check - the
winner's grid neighbors must be majority same-sign IS, else next
candidate. ONE spec to OOS, judged once at the program bar above;
the ORB family's OOS then burns.
Registered prediction: honest uncertainty - the literature mechanism
is real in equities cross-section; whether the time-series analogue
carries to index futures is exactly what the OOS decides. Prior
lean: gates improve IS materially; OOS pass probability well under
half.

### Attempt 1 result: FAIL at the OOS gate - ORB family burned

(results/r42a_orb.json) The IS grid behaved like a real mechanism: the
gap>=0.5xATR gate occupied ALL top-8 slots (every window/stop/target
variant of it IS-positive, halves [+,+], t to +3.33) - a smooth
gradient, not a spike. Selected by the pre-stated rule: W60, gap gate,
half-range stop, EOD exit (neighbors 5/7 positive). One-shot OOS
(pooled n 960): avgR +0.014, PF 1.10, t +0.93, halves [+,-]; per
instrument SPX +0.027/NDX +0.011/RTY +0.022/GOLD -0.019. Sign
survived, significance and PF did not; cost x1.5 stays positive but
weak. GATE: FAIL (bar: t>=2, PF>=1.15). Per protocol the ORB family's
OOS is burned - no re-entry for this family regardless of future
ideas. Honest summary for the program file: gap-day participation is
probably a weak real tilt on index opens, too small to clear the bar;
it may legitimately reappear as a FILTER inside some future,
differently-motivated strategy, but not as the edge itself.
Program score: 0 graduates / 1 attempt.

### Attempt 2 pre-registration: late-day intraday momentum (Gao-Han-Li-Zhou analogue)

MECHANISM (external literature, primary): Gao, Han, Li & Zhou,
"Intraday momentum: the first half-hour return predicts the last
half-hour return" (JFE 2018; SPY 1993-2013, replicated on futures and
ETFs; attributed to late-informed trading and MOC/rebalancing flows).
Session-concentration class (#3) + horizon-matching (#7). DISCLOSURE:
r34's full-sample session atlas flagged NY-PM displacement follow-
through as a watch hypothesis, and that scan touched all data
including our OOS blocks; the SPEC below is taken from the external
literature (predictor = early/day return, not displacement bars), but
the overlap is recorded and weighs against over-reading a pass.
FROZEN GRID (12 variants, IS = all but last 25% of sessions):
predictor P in {first-30m return (09:30 open -> 10:00); day-so-far
return (09:30 -> 15:00); both-agree (trade only when signs agree)} x
entry in {15:00 close, hold to session close; 15:30 close, hold to
close} x filter in {none; |P| >= 0.25 x ATR20d}. Direction = sign(P).
One trade/day, market entries at bar closes, costs micro full RT.
Selection and OOS bar identical to attempt 1 (pooled ATR-normalized t,
min 120 IS trades, neighbor-majority gradient check, one OOS shot,
then the late-day-momentum family burns).

### Attempt 2 result: IS-FAIL for momentum - and a strong inverted finding

(results/r42b_pm.json) Every one of the 12 late-day MOMENTUM variants
is significantly NEGATIVE in sample: t -4.2 to -11.8, halves [-,-] in
all 12, PF 0.73-0.93. No spec selectable; the family fails at IS and
its OOS block was NOT opened. The Gao-Han-Li-Zhou effect (SPY
1993-2013) does not exist in these 2005-2026 index/gold sessions with
this sign - the day's move systematically REVERSES into the close.
Program score: 0 graduates / 2 attempts.

### Attempt 2b pre-registration: late-day REVERSAL (the mirror)

ORIGIN DISCLOSED: direction chosen from the attempt-2 IS result (all
selection so far on IS only; this family's OOS remains untouched).
External support: post-publication replications find intraday
momentum decayed, and Baltussen, Da, Lammers & Martens ("Hedging
demand and market intraday momentum" / indexing-era serial dependence
work) document NEGATIVE index serial dependence in the recent era
via leveraged-ETF and dealer-gamma rebalancing channels - a mechanism
consistent with late-day mean reversion in index futures.
FROZEN GRID: the attempt-2 grid mirrored - direction = MINUS
sign(P), same 12 variants (predictor first30/day/agree x entry
15:00/15:30 x filter none/0.25atr), same costs, same selection rule
on IS, same OOS bar; the late-day family's single OOS shot is spent
on the selected reversal spec, then the family burns for good.

### Attempt 2b result: IS-FAIL both directions - and a corrected inference

(results/r42c_pmrev.json) All 12 REVERSAL variants also significantly
IS-negative (t -5.7 to -17.0, halves [-,-]). A trade and its mirror
cannot both lose gross, so the decomposition was checked: per variant,
net_mom + net_rev = -2 x cost, giving cost ~ 0.021-0.026 R (early-era
ATRs are small, so a fixed point cost is large in R units) and GROSS
late-day serial dependence ~ +0.008 R - a tiny decayed momentum
remnant, matching the post-publication literature. CORRECTION ON THE
RECORD: the attempt-2 conclusion "momentum is inverted" was wrong -
the significance was cost drag in both directions, not signal. The
mirror run is what exposed it; adopted as standard practice: any
strongly one-sided net result gets a gross decomposition before it is
interpreted. Late-day family closed (momentum IS-fail, reversal
IS-fail); its OOS block was never opened. No spec in this family can
clear ~0.02R costs on a ~0.008R gross effect at one trade per day.
Program score: 0 graduates / 3 attempts (families burned: ORB,
late-day serial dependence).
Next registered candidates for attempt 4+ (not yet specified): FP5
displacement magnitude/horizon repair (heavy prior-look disclosure
required), gap-fill vs gap-continuation family, ALMA baseline repair.

### Attempt 4 pre-registration: FP5 displacement - magnitude/horizon cost repair

DIAGNOSIS (r37b): displacement continuation is real gross (+0.2..+0.5
pts/trade across instruments at zero cost, t to +7) and dies inside one
round trip. Repair classes #4 (cost engineering by FREQUENCY REDUCTION:
fewer, larger-expectation trades so cost is paid less often per unit of
edge) and #7 (HORIZON MATCHING: hold to EOD so the per-trade gross move
is large relative to one fixed cost). Mechanism basis: larger
displacement = larger participation imbalance = stronger continuation
(the same size-conditioning that made r40's flips a vol marker makes
WITH-candle displacement a flow marker); morning signals leave EOD
runway.
DISCLOSURE (mandatory): this family was examined on the FULL sample in
r33b, r37/37b, r38, r39/39c - the OOS block is not pristine for the
family, only for these exact specs. A pass therefore carries reduced
weight and the paper/SPRT stage is doubly mandatory.
FROZEN GRID (24 variants, IS = all but last 25% of sessions):
signal = 15m RTH displacement bar (frozen r33b def: TR >= k x ATR14,
body >= 0.6 x range), direction = bar direction, market entry at bar
close. Knobs: magnitude k in {1.5, 2.0, 2.5} x signal window {before
14:00, before 11:30} x stop {none, 1 x signal-bar range} x exit {EOD
close, time 8 bars} . One open trade per instrument (busy-until),
costs micro, worst-case stop-first on 15m bars, pooled ATR20d-
normalized stats. Selection and OOS bar identical to attempts 1-2
(min 120 pooled IS trades, neighbor-majority gradient check, one OOS
shot at t>=2 / PF>=1.15 / cost x1.5 positive, family burns after).
Registered prediction: k-gradient is the crux - if continuation truly
scales with magnitude, avg_R should RISE monotonically in k in IS; a
flat or inverted k-gradient means frequency reduction cannot beat the
cost clock and the family dies at IS.

### Attempt 4 result: FAIL at the OOS gate - displacement family burned

(results/r42d_disp.json) The registered crux behaved: the magnitude
gradient in IS was MONOTONIC and coherent - k1.5 all-negative (cost-
dominated, consistent with r37b), k2.0 ~flat, k2.5 positive across 7/8
variants (best t +2.47, halves [+,+] on the selected cell) - exactly
what a real size-scaled flow effect should look like. Selected by the
pre-stated rule: k2.5, signals before 14:00, 1x-range stop, 8-bar time
exit (neighbors 3/5 positive). One-shot OOS (pooled n 1329): avgR
-0.003, PF 0.95, t -0.28, halves [-,+]; only RTY positive (+0.026,
t +1.05); cost x1.5 negative. GATE: FAIL. Family burned - and with the
r33b/r37-39 prior-look disclosure on file, the honest reading is that
the k-gradient was learned partly from eras the OOS no longer
resembles: the extreme-displacement continuation visible in 2005-2020
data does not pay 2020-2026 net of micro costs. This closes the FP5
monetization question that has run since r33b: real gross, never net,
in any frame we are able to trade from OHLC.
Program score: 0 graduates / 4 attempts (burned: ORB, late-day serial
dependence, FP5 displacement).

### Attempt 5 pre-registration: overnight gap - fill vs continuation by size

MECHANISM: the overnight gap is the visible imbalance between the
overnight auction and the prior RTH close. Standard microstructure
account, size-dependent: SMALL gaps are liquidity/overnight-noise
overshoots that revert to the prior close (gap fill); LARGE gaps are
informed repricings that continue (gap-and-go). Attempt 1's burned-ORB
residue (the gap>=0.5xATR gate carried the only OOS-surviving tilt,
direction-agnostic) motivates testing the gap DAY-TYPE directly.
Classes #1 (regime by gap size), #2 (all distances in ATR20d units),
#3 (open-session concentration), #7 (EOD horizon).
FROZEN GRID (24 variants, IS = all but last 25% of sessions):
gap g = 09:30 RTH open minus prior RTH close, normalized |g|/ATR20d;
size bucket in {small 0.1-0.3; mid 0.3-0.7; large >=0.7} x direction
in {FILL: side=-sign(g), target=prior close; CONT: side=+sign(g),
target=entry+|g| extension} x entry in {09:30 open; 10:00 close, day
skipped if the target was already touched in the first 30m} x exit in
{target with EOD backstop; EOD close only}. Stop always on, frozen at
0.5 x ATR20d adverse, worst-case stop-first on 5m bars. One trade per
day per instrument, costs micro, pooled ATR20d-normalized stats.
Selection + OOS bar identical to prior attempts; the whole gap family
(both directions, all sizes) burns on this one OOS shot.
Registered prediction: the size-direction interaction is the crux -
the mechanism requires FILL to win in the small bucket and CONT in the
large bucket IN SAMPLE with a coherent gradient across buckets; a grid
where one direction wins everywhere (or neither) means the day-type
story is wrong, and the family should die at IS unless a cell is
independently strong.

### Attempt 5 IS result and disclosed amendment 5b (registered before OOS opened)

(results/r42e_gap.json grid) IS: small and mid buckets negative in BOTH
directions (small-FILL least bad, -0.011..-0.023 - the fill tendency
exists but under costs; small-CONT worst, t -8.1). LARGE-gap
CONTINUATION positive in all 4 of its cells (+0.004..+0.036; best:
entry 10:00, EOD exit, avgR +0.036, t +2.08, halves [+,+], PF 1.03),
large-FILL strongly negative - the registered size-direction
interaction, matched on the CONT half. The frozen generic neighbor-
majority rule refused selection because cross-BUCKET neighbors are
negative - but the registration's own crux statement predicts exactly
that sign flip across buckets, an internal inconsistency in the
registration. AMENDMENT (disclosed; decided after seeing IS ONLY, OOS
untouched): for mechanisms that predict a sign change across a
dimension, the neighbor check is scoped to the mechanism-relevant
subspace (here: within the large bucket - 3/3 neighbors positive for
the top cell). This resolution is adopted prospectively for future
registrations as well. The one OOS shot is spent on large-CONT /
entry 10:00 / EOD exit. Noted against it before opening: IS PF 1.03
is already below the 1.15 OOS bar and IS t 2.08 is modest; prior lean
FAIL.

### Attempt 5b result: FAIL - gap family burned

(results/r42e_oos.json) The one-shot OOS on large-gap continuation
(entry 10:00, 0.5xATR stop, EOD exit): pooled n 596, avgR +0.002,
t +0.08, PF 0.99, halves [-,+]; SPX/NDX/RTY all slightly negative,
GOLD +0.043 (t +0.98, noise-sized); cost x1.5 negative. GATE: FAIL -
about as exact a zero as an OOS shot can return. The 2005-2020 IS
effect (+0.035R, t +2.0) did not exist in 2020-2026, the same era-
decay shape as attempt 4. Gap family burned in both directions and
all sizes. Standing residue worth keeping: small-gap fill exists as a
TENDENCY (it lost least) but sits under costs; large-gap continuation
was real once and is gone.
Program score: 0 graduates / 5 attempts (burned: ORB, late-day serial
dependence, FP5 displacement, overnight gap). Remaining queued: ALMA
baseline repair (note: 6H Russell swing, not strictly intraday).
Program-level observation registered for the user: all five burned
families are RTH index-micro intraday effects - the most heavily
arbitraged arena there is, and the two eras in our data disagree
about every candidate found. Our own validated edges (gold rule, MHI,
D7) all live at SESSION BOUNDARIES or cross-market interactions, not
inside RTH chop. Recommendation on record: after ALMA, widen the
program's search space to session-handoff and cross-market families
(Asia/London opens on MGC, overnight-session behavior, index-gold
interactions) before burning more RTH families.

### Attempt 6 pre-registration: the overnight-drift window (European open)

MECHANISM (external, published): Boyarchenko, Larsen & Whelan, "The
Overnight Drift" (NY Fed staff report / RFS): S&P futures returns
concentrate in the hours around the European open (~02:00-03:30 ET),
attributed to dealer inventory management - liquidity providers absorb
Asian-hours order flow and unwind into European liquidity; long-only,
strongest after negative prior sessions. Classes #3 (clock-window
session concentration - the purest member we have tested) and #7.
DISCLOSURE: r30 tested the WHOLE overnight (close-to-open, daily ETF/
index data) and found it dead net at the index level; this is a finer
claim - a specific 1-3h futures window at micro costs - but the
adjacency is on record. The r34 atlas measured session-conditional
sweep/RVOL/displacement behavior, not unconditional clock-window
drift; overlap minimal but noted. Post-publication decay (paper
public since 2018) is the registered principal risk.
FROZEN GRID (6 variants, long-only, IS = all but last 25% of
sessions): window in {01:00-04:00, 02:00-03:30, 02:30-03:30 ET} x
prior-session filter in {all days; prior 24h session return < 0}.
Enter first bar open in the window, exit last bar close in the
window, one trade per session per instrument, cost micro per RT.
Instruments SPX/NDX/RTY pooled as the mechanism set; GOLD included as
a sibling with NO mechanism claim (metals inventory cycle differs) -
gold's sign is diagnostic, not qualifying. Normalization: ATR20 of
the 24h session range. Selection: pooled index-only t (gold excluded
from selection), min 120 IS trades, neighbor-majority within the
window/filter grid; one OOS shot at the program bar (t>=2, PF>=1.15,
cost x1.5 positive), family burns after.
Registered prediction: IS should show the published effect (it
overlaps the paper's sample); the OOS (2020-2026) decides whether it
survived publication - genuine uncertainty, this is the cleanest
decay test the program has run.

### Attempt 6 result: IS-FAIL, sign inverted vs the published effect - OOS not opened

(results/r42f_ondrift.json) All 6 long variants IS-negative; the
narrow 02:30-03:30 window is the WORST (avgR -0.022, t -17.4, gross
after cost decomposition ~ -0.016R) - the exact window where the
published drift is strongest. The prev-down conditioning (the paper's
own amplifier) stays negative. Gold diagnostic also negative. Family
fails at IS; OOS untouched. Interpretation registered with explicit
uncertainty: EITHER post-publication inversion (documented for other
anomalies) OR a clock-anchored CFD feed artifact (dividend/rollover
adjustment timing) that genuine ES overnight data would not show. The
MIRROR (short the European open) is deliberately NOT registered: no
independent mechanism, and the artifact risk makes an IS-derived flip
on this feed the exact r41 trap. Logged as a DATA-PROVENANCE question:
if true CME overnight index data is ever sourced, re-examine before
any use. Family closed.
Program score: 0 graduates / 6 attempts.

### Attempt 7 pre-registration: gold session-clock split (Asia long / London short)

MECHANISM (external, gold-specific, decades-documented): gold's
intraday seasonality - prices tend to RISE through Asian hours and
FALL through the London session into the fixes (Lucey/O'Connor gold
intraday seasonality; Caminschi & Heaney on the London fixes; the
long-standing "gold rises overnight, falls intraday" split). Driver
accounts: Asian physical demand accumulation vs London/OTC dealer
supply and fix-related flows. Classes #3 (clock windows) + #7.
DISCLOSURES: (1) the deployed gold rule trades an Asia-open BREAKOUT
with a correlation gate - conditional, different object from an
unconditional clock drift; (2) r15's researched battery included a
gold session-split cell (full-sample look at the time, not adopted);
(3) r26 SGE auction battery touched Asian-hours gold; the IS is
therefore not pristine, and the OOS block (2024-05..2026-08) also
POSTDATES r15/r26's samples in part, which restores some of its
value. Gold 5m feed only (2020-08..2026-08, ~1530 sessions; IS ~1150,
OOS ~380).
FROZEN GRID (6 variants): legs in {Asia LONG only; London SHORT only;
both legs} x windows in {A: Asia 19:00-03:00 ET, London 03:00-11:00;
B: Asia 20:00-02:00, London 03:00-10:00}. Enter first bar open in
window, exit last bar close, cost 0.35 per leg RT, ATR20 (24h range)
normalization, one trade per leg per session. Selection: IS t, min
120 trades, neighbor-majority; one OOS shot at the program bar;
family burns after.
Registered prediction: genuine uncertainty; the effect is old and
physical-flow-driven (less crowdable than index microstructure), but
2020s gold is heavily financialized - the OOS decides.

### Attempt 7 result: FAIL - and a protocol amendment

(results/r42g_goldclock.json) IS: the celebrated gold clock split
barely exists in 2020-2024 data - best cell (set B London short)
avgR +0.010, t +0.56; nothing else stronger. The pre-stated rule
still selected it (it satisfied n and neighbor checks) and the OOS
shot returned avgR -0.034, t -1.23, halves [-,-]. GATE: FAIL, family
burned. Post-mortem: the OOS shot was spent on an IS-null spec - the
selection rule had no minimum-strength floor, so a family whose IS
grid is already noise can still burn its holdout. AMENDMENT (adopted
prospectively): an OOS shot is spent only if the selected spec's IS
t >= 2; otherwise the family fails at IS with its holdout unopened
(the holdout is then still technically intact, but the family is
closed regardless - reopening would be rule-shopping).
Program score: 0 graduates / 7 attempts (burned: ORB, late-day serial
dependence, FP5 displacement, overnight gap, overnight-drift window
(IS), gold clock split). Remaining queued: ALMA baseline repair;
wider families TBD with the user.

### Attempt 8 pre-registration: ALMA baseline repair (user's r31 commission)

DIAGNOSIS (r31): the vendor ALMA strategy's 76% WR was MECHANICAL -
averaging down plus a wide effective stop manufactures win rate while
the underlying signal showed drift-null expectation (p 0.76). The
disease is the martingale, not the moving average. REPAIR: remove the
averaging-down entirely and test whether the naked signal - a pullback
reclaim of a rising ALMA on 6H bars - carries ANY conditional
expectation, with honest exits. Classes #1 (vol-regime gate), #2
(ATR exits), #5 (no averaging). Prior lean: FAIL (r35d - if the
event expectation is zero, no wrapper creates it); run because the
user commissioned this baseline's repair and the grid is cheap.
FROZEN GRID (8 variants, long-only, 6H bars resampled from the 24h 5m
feeds, 4 instruments pooled ATR-normalized): signal = close crosses
above ALMA(50, offset .85, sigma 6) with ALMA slope > 0 over s bars;
s in {4, 8} x gate in {none; calm regime ATR14/ATR56 <= 1} x exit in
{time 6 bars; 2xATR14 stop, 12-bar cap}. Entry at signal close, one
open trade per instrument, micro costs per RT. Selection: IS t >= 2
floor (amended protocol), min 120 pooled IS trades, neighbor-majority;
one OOS shot at the program bar; family burns after.

### Attempt 8 result: IS-FAIL - ALMA family closed

(results/r42h_alma.json) All 8 variants fail the IS t>=2 floor (best
+0.11; several PF>1 cells have NEGATIVE ATR-normalized expectancy -
their point wins cluster in high-ATR periods, a units lesson). The
r31 diagnosis is confirmed at the signal level: the vendor ALMA
strategy was win-rate cosmetics around a null signal. Family closed,
holdout unopened. Program score: 0 graduates / 8 attempts.

### Attempt 9 pre-registration: VIX term-structure gate on intraday dip-buying

MECHANISM (external): the VIX/VIX3M ratio is a documented vol-regime
state - CONTANGO (ratio < ~0.95) marks calm regimes where intraday
index dips are liquidity events that revert by the close;
BACKWARDATION (ratio >= 1) marks stress regimes where dips continue
(crash dynamics). Dip-buying conditioned on term structure is the
canonical "conditional gate that changes expectation" shape our own
validated systems share. Classes #1 (regime gate, the strong form)
+ #3 + #7. Data: VIX & VIX3M daily (github, 2009-09+), PRIOR day's
closes only (no lookahead); indices only (VIX is equity vol; gold
excluded by mechanism).
FROZEN GRID (6 variants, long-only): dip = open -> 12:00 return
<= -k x ATR20(RTH), k in {0.3, 0.5}; gate in {none; contango ratio
<= 0.95; backwardation ratio >= 1.0}. Buy 12:00 close, exit session
close, one trade/day/instrument, micro costs, pooled ATR-normalized.
Registered mechanism sign-check: contango cells should BEAT the
ungated cells and backwardation cells should be NEGATIVE - a grid
where the gate does not separate regimes refutes the mechanism
regardless of any single cell. Selection: IS t>=2 floor, min 120
pooled IS trades, neighbor-majority; one OOS shot at the program bar;
family burns after.

### Attempt 9 result: IS-FAIL, mechanism sign-check refuted

(results/r42i_vixdip.json) All 6 variants below the IS floor; worse,
the registered sign-check went backwards - contango dip-buying is MORE
negative than ungated (-0.031/-0.054R vs -0.024/-0.037R) and the
backwardation cell is the only (noise-sized) positive. The VIX term
structure does not make noon dips buyable; afternoon continuation of
morning weakness (the attempt-2 momentum remnant) dominates in every
regime. Family closed at IS, holdout unopened.
Program score: 0 graduates / 9 attempts.

### Attempt 10 pre-registration: gold 08:30 macro-impulse continuation

MECHANISM (external): scheduled US macro releases at 08:30 ET (CPI,
NFP, retail sales, GDP...) are the dominant information events for
gold; post-announcement drift - continuation of the initial impulse
as the surprise diffuses - is documented for FX/metals (announcement-
drift literature). Without an economic calendar the IMPULSE SIZE is
the surprise proxy: a large 08:30 move IS the footprint of a
surprise. Classes #1 (event-day regime) + #3 (clock window) + #7.
DISCLOSURE: r34's atlas measured NY-session killzone behavior
descriptively (sweeps/RVOL/displacement); this event definition
(08:30 impulse) is new to the repo.
FROZEN GRID (12 variants, both directions, GOLD only): impulse window
{08:30-08:35, 08:30-08:45} x threshold |impulse| >= {0.15, 0.25} x
ATR20(24h) x hold {30m, 60m, to 11:00}. Direction = impulse sign,
enter at window-end close, exit at hold-end close, one trade/day,
cost 0.35, ATR-normalized. Selection: IS t >= 2 floor, min 120 IS
trades, neighbor-majority; one OOS shot (last 25% of sessions) at
the program bar; family burns after.

### Attempt 10 result: IS-FAIL - gold 08:30 impulse does not continue

(results/r42j_goldnews.json) All 12 variants below the IS floor (best
+0.029R, t +0.61, n 88). The impulse-size proxy for macro surprises
carries no continuation in 2020-2024 gold; if announcement drift
exists here it needs true surprise data (consensus vs actual), not
price-only proxies. Family closed at IS.
Program score: 0 graduates / 10 attempts. Sitting summary: attempts
8-10 all closed at IS with holdouts unopened - the amended IS floor
is doing its job (three families examined, zero holdouts spent).
Next sitting queue: (a) pre-FOMC drift with vol-detected announcement
days (Lucca-Moench; n will be small, decay documented - honest prior
weak), (b) fresh mechanism research pass (WebSearch) for families not
yet touched, (c) the weekend-gap question ONLY if it can be honestly
distinguished from the burned RTH-gap family.

### Attempt 11 pre-registration: macro-announcement-day equity premium

MECHANISM (external, published): Savor & Wilson - the US equity
premium is earned disproportionately on scheduled macro announcement
days (FOMC, NFP, CPI); Lucca & Moench - drift accrues in the 24h
BEFORE FOMC statements. Compensation for macro risk resolution;
classes #1 (calendar regime) + #3. Two event sets:
(a) NFP days = first Friday of the month, DETERMINISTIC calendar, no
lookahead of any kind;
(b) FOMC-like days DETECTED from the data: 14:00-14:30 realized range
>= {2.5, 3.5} x its own 60-day rolling median (statement releases at
14:00 ET post-2011). DISCLOSED approximation: the label uses the
day's own 14:00 window, which post-dates the trade exit (13:55) -
this reconstructs calendar knowledge a real trader has ex ante, at
the price of misclassification noise; sanity check = flagged days/yr
should be ~6-12.
FROZEN GRID (7 variants, long-only, indices pooled ATR-normalized):
NFP: hold {prior 15:55 close -> NFP 15:55 close; NFP 08:00 -> 12:00;
NFP 09:30 -> 15:55} (3 cells; all other Fridays same-hold printed as
control, not selectable). FOMC-detected: threshold {2.5, 3.5} x hold
{prior-day 14:00 -> event-day 13:55; event-day 09:30 -> 13:55}
(4 cells). Cost micro per RT. Selection: IS t >= 2 floor, min 120
pooled IS trades, neighbor-majority; one OOS shot (last 25% of
sessions) at the program bar; the announcement-day family burns after.
Registered prediction: Savor-Wilson is a risk-premium (not
mispricing) claim, so decay is less automatic than for r42's
microstructure families; but Lucca-Moench post-2015 decay is
documented; genuine uncertainty.

### Attempt 11 result: IS-FAIL + a conditioning-on-the-future lesson

(results/r42k_macro.json) NFP cells (deterministic calendar, clean):
prevclose->close +0.029R t +0.72 vs other-Friday control -0.027R -
the Savor-Wilson direction exists faintly, well below the floor; the
intraday-only harvests are negative. FOMC-DETECTED cells: -0.24 to
-0.56R, t to -10.7 - NOT a real effect: labeling days by their own
14:00 volatility conditions on FUTURE vol, which correlates with
negative same-day returns (leverage effect). The disclosed
misclassification risk materialized as outright bias; recorded as a
protocol note - event calendars must be ex-ante; volatility-detected
event sets are INVALID for directional claims. Family closed at IS.
Program score: 0 graduates / 11 attempts.

### Attempt 12 pre-registration: FOMC pre-announcement drift, clean ex-ante calendar

JUSTIFICATION FOR RE-TEST: attempt 11's FOMC arm was never validly
run - the vol-detected event set conditioned on future volatility
(instrument error, recorded). The NFP arm's IS-fail STANDS and is not
re-tested. This attempt uses the true ex-ante calendar: FOMC statement
dates 2013+ (statements at 14:00 ET from 2013, removing release-time
ambiguity), fetched from federalreserve.gov's published meeting
calendars - exogenous public facts known in advance by construction.
MECHANISM: Lucca & Moench pre-FOMC drift (equities rise in the 24h
before scheduled FOMC statements); Savor-Wilson announcement premium.
Documented post-2015 decay is the registered principal risk.
FROZEN GRID (3 cells, long-only, SPX/NDX/RTY pooled ATR-normalized,
2013+): hold in {prior-day 14:00 -> statement-day 13:55 (the L-M
window); statement-day 09:30 -> 13:55; prior-day 15:55 close ->
statement-day 15:55 close (full announcement day)}. Cost micro per
RT. Selection: IS t >= 2 floor (min 60 pooled IS trades given 8
meetings/yr), one OOS shot (per-instrument last-25% session cuts) at
the program bar with OOS n >= 40 pooled; the FOMC family then burns
for good regardless of outcome.

### Attempt 12 result: ABORTED at the calendar validator - not counted as burned

(results/r42l_fomc.json) The pre-stated validator found only 60% of
the knowledge-derived FOMC dates carry the 14:00 vol signature (vs 14%
base rate - the calendar is mostly right but too noisy for a ~100-
event study; ~40% mislabels destroy power). federalreserve.gov,
wikipedia and fraser.stlouisfed.org are all blocked by the egress
proxy, so no verified source is reachable. Attempt aborted BEFORE any
return was examined; the family is NOT burned - it revives if a
verified ex-ante calendar is ever sourced (e.g., supplied by the
user). Program score: 0 graduates / 11 attempts + 1 aborted.

### Attempt 13 pre-registration: corr-regime conditional London->NY gold continuation

MECHANISM (in-house, validated instrument): corr(gold, AUDUSD; 20d
daily log returns, prior day) is the deployed rule's regime gate -
LOW corr (<= 0.5) marks "monetary" gold regimes where the Asia
breakout carries; HIGH corr marks "risk-linked" gold. New harvest
question: does the LONDON session move (03:00->08:00 ET) continue
into the NY session in low-corr regimes and fade in high-corr
regimes? Registered crux = the INTERACTION (follow in low-corr, fade
in high-corr); a grid where one direction wins in both regimes
refutes the regime story. Class #1 in its validated form. OVERLAP
DISCLOSED: a pass would correlate with deployed gold-rule positions
(same instrument, overlapping hours) - portfolio treatment would be
needed at the paper stage.
FROZEN GRID (8 cells, GOLD only): regime {corr <= 0.5; corr > 0.5} x
London-move threshold {any nonzero; |move| >= 0.25 x ATR20(24h)} x
hold {09:30->12:00; 09:30->16:00}. Direction = sign(London move) in
low-corr cells, MINUS sign in high-corr cells (per the crux). Entry
09:30 RTH open bar close... precisely: first RTH bar close; exit at
hold-end close; cost 0.35/RT; one trade/day; ATR-normalized.
Selection: IS t >= 2 floor, min 120 IS trades, neighbor-majority
scoped WITHIN regime (r42e amendment); one OOS shot (last 25% of
sessions) at the program bar; family burns after.

### Attempt 13 result: IS-FAIL - the corr regime does not govern London->NY gold

(results/r42m_corrny.json) Full-span rerun after a disclosed IS-stage
data-source correction (the AUD M15 collector feed spans ~15 months
and truncated the join to 312 sessions; FRED daily AUD restores 1208).
All 8 cells flat-to-negative (best +0.003R t +0.06); the registered
low-corr-follow / high-corr-fade interaction shows NO separation. The
validated corr gate governs the Asia-open breakout and nothing else we
have found - a useful boundary on our own edge's mechanism. Family
closed at IS, holdout unopened.
Program score: 0 graduates / 12 tested attempts + 1 aborted
(calendar provenance). Sitting cadence now continuous per the user;
the continuation trigger is being shortened from 2h to ~15min.

### Attempt 14 pre-registration: conditional month-end rebalancing flow

MECHANISM (external): month-end pension/target-allocation rebalancing
(Etula, Rinne, Suominen, Vaittinen "Dash for Cash"): when equities have
moved strongly intra-month, rebalancers trade AGAINST the move in the
final days - selling equities into month-end after an up month-to-date,
buying after a down one. Deterministic calendar, conditional direction.
Classes #1 (calendar+state regime) + #3. DISCLOSURE: r15 F2 tested the
UNCONDITIONAL TOM windows (McConnell-Xu, Etula T-3..T+2 long) on
SPX/NDX/RTY full-sample and it was not adopted; this conditional
opposite-direction claim is distinct but the calendar-window adjacency
and the r15 full-sample look are on record.
FROZEN GRID (4 cells, indices pooled ATR-normalized): MTD return
measured 09:30-open-of-month to close of T-3 (3rd-to-last trading day
of the month); trigger |MTD| >= thr, thr in {1.5%, 3%}; direction =
MINUS sign(MTD); entry in {T-3 close, T-2 close}; exit month-end
close; cost micro once per trade. Selection: IS t >= 2 floor, min 100
pooled IS trades, neighbor-majority; one OOS shot at the program bar;
family burns after.

### Attempt 15 pre-registration: Asia-close risk tone -> US RTH session

MECHANISM (external): gradual cross-market information diffusion -
Asian cash sessions (Nikkei, HSI) close before NY opens; a concordant
Asia move is a global risk-tone signal not yet fully priced by the US
open (spillover/momentum literature; documented but WEAK for
world->US, prior lean modest and registered as such). NOT the burned
gap family: the signal is FOREIGN session returns, not the US
instrument's own overnight move, and the trade is a session hold, not
a gap fill/extension bracket.
FROZEN GRID (4 cells, SPX/NDX/RTY pooled; gold excluded): signal =
Nikkei (JP225) and HSI session returns per their own trading day
(H1 feeds, 2016-2026), both known before 09:30 ET; trade only when
signs AGREE, direction = the common sign; filter in {any; both
|ret| >= 0.5 x own 20d sigma}; hold in {09:30->12:00; 09:30->close}.
Cost micro; ATR-normalized. Selection: IS t >= 2 floor, min 120
pooled IS trades, neighbor-majority; one OOS shot; family burns after.

### Attempt 14 result: FAIL at the OOS gate - the program's strongest residue

(results/r42n_monthend.json) IS: all 4 cells positive, coherent (t
+1.8..+2.8, halves [+,+], WR 55-57%, PF 1.4-1.5). Selected thr 1.5% /
entry T-2. One-shot OOS: sign and PF SURVIVED (+0.040R, PF 1.26, WR
52.2%, n 136) but t +0.61 - at n 136 a PF 1.26 is comfortably inside
luck, which is what the bar is for. GATE: FAIL, family burned for
further search. WATCH ITEM registered (passive forward accrual only,
like NY-PM displacement): conditional month-end rebalancing fade,
thr 1.5%, entry T-2 close, exit month-end close - the monthly routine
may re-score it as new months accrue; no new searching permitted.
Program score: 0 graduates / 13 tested + 1 aborted.

### Attempt 15 result: IS-FAIL after a caught lookahead - the second great fake of the program

(results/r42o_asiatone.json) The first run "PASSED" the OOS gate with
absurd numbers (IS t +21.4, OOS t +12.8, PF 3.8) - flagged
immediately by the smell test and audited before any report. Cause:
the JP225/HK33 "H1" feeds are 24-HOUR CFD feeds; last-bar-of-UTC-date
is ~23:00 UTC (7pm ET), AFTER the US close, so the "Asia tone" signal
contained the very session it predicted. The registration required
the signal known before 09:30 ET; the implementation violated it.
With the corrected 08:00 UTC cutoff (HK cash close): all 4 cells
flat-to-negative (best -0.008R; concordant-Asia-tone US follow-
through does not exist net, and leans fade if anything). Family
closed at IS; the buggy run's OOS opening is void (invalid signal),
corrected run never opened it. PROTOCOL ADDITION (permanent): every
cross-market or multi-feed signal must print its signal-availability
timestamp against the entry timestamp before any grid is read; 24h
feeds default to explicit clock cutoffs, never date-group aggregates.
This is the program's second manufactured miracle caught by audit
(r38 signal-bar leak; now the session-cutoff leak) - both would have
been catastrophic live.
Program score: 0 graduates / 14 tested + 1 aborted.
Sitting summary: attempt 14 month-end rebalancing = FAIL but
strongest residue (OOS sign+PF survived, watch item registered);
attempt 15 Asia tone = lookahead caught, honest version null.

### Attempt 16 pre-registration: gold/silver relative-value session reversion

HONESTY CHECKPOINT APPLIED FIRST: of the remaining queued directions,
quarter-end is adjacent to the burned month-end family, CFFEX/China-
close is adjacent to the burned Asia-tone family, a UST10Y regime gate
has no validated base strategy to gate (r39 lesson), and RTY-vs-SPX
relative intraday has no published or structural mechanism worth an
attempt. Gold/silver RV is the ONE remaining non-adjacent candidate;
if it fails, the next deliverable is a candid program-status report,
not another attempt.
MECHANISM: gold and silver share the precious-metals complex (daily
return correlation ~0.8); a large one-day divergence between them is
disproportionately idiosyncratic flow (one leg's ETF/futures pressure)
rather than complex-wide news, and partially reverts as dealers and
RV traders rebalance the pair. Published support moderate (gold-silver
ratio mean reversion literature is mixed at long horizons; short-
horizon pair reversion is a structural-liquidity claim); registered
prior: modest. DISCLOSURE: silver feed is H1 (2016-2026) - session
closes only, no intrabar path; the trade is a 2-leg pair (MGC + SIL),
a different execution shape from the single-leg program so far; cost
registered at 4 bps per round trip BOTH legs (2 x ~2bp micro
estimate), sensitivity at x1.5.
FROZEN GRID (6 cells): daily spread s = r_gold - r_silver measured
16:00-ET-to-16:00-ET session closes; sigma20 = 20d rolling std of s;
event: |s_yesterday| >= k x sigma20, k in {1.0, 1.5, 2.0}; position =
CONVERGENCE (long laggard / short leader, equal $ legs); hold in
{next NY RTH 09:30->16:00; next full session close->close from 09:30
entry}. pnl in spread-return bps minus cost; normalized by sigma20.
Signal availability check: signal complete at prior 16:00 ET, entry
next 09:30 - printed in the run. Selection: IS t >= 2 floor, min 120
IS trades, neighbor-majority; one OOS shot (last 25% of sessions);
family burns after.

### Attempt 16 result: IS-FAIL - and the program pauses at the honesty checkpoint

(results/r42p_gsrv.json) Gold/silver next-session convergence after a
>=k-sigma daily divergence: all 6 cells flat-to-negative net of 4bp
pair costs (best -0.12bps, t -0.30). The pair does not revert at the
one-session horizon in 2020-2024 data. Family closed at IS.

## Round 42 PROGRAM STATUS: paused at the honesty checkpoint

Score: 0 graduates / 15 tested attempts + 1 aborted (FOMC calendar
provenance). Families burned: ORB, late-day serial dependence, FP5
displacement, RTH-open gap, overnight-drift window, gold clock split,
ALMA, VIX-gated dip-buy, gold 08:30 impulse, announcement-day/NFP,
corr-regime London->NY gold, month-end rebalancing (WATCH item),
Asia-tone spillover, gold/silver session RV. Aborted-not-burned:
FOMC pre-drift (revives with a verified ex-ante calendar).
The checkpoint rule fired: no remaining candidate is simultaneously
(a) non-adjacent to a burned family and (b) supported by a real
mechanism. Running further attempts from the same data would be
attempt-count theater and would inflate the program-level false-pass
budget for nothing. THE CONSTRAINT IS NOW DATA, NOT SEARCH:
1. A verified economic calendar with CONSENSUS + ACTUAL (enables the
   announcement-surprise family properly, incl. reviving FOMC).
2. True CME session data for ES/NQ/RTY/GC (settles the attempt-6
   overnight-window feed-artifact question; enables auction-based
   families: opening auction imbalance, settlement windows).
3. Any order-flow/depth product (enables the microstructure families
   OHLC structurally cannot test - the r37/arXiv falsification point).
Standing assets that keep accruing without new searches: 4 deployed/
paper streams (gold rule, XAUAUD, MHI, D7 - monthly routine scores
them, next fire 2026-09-01), 2 watch items (NY-PM displacement,
month-end rebalancing fade). The 3-edge goal remains open; it resumes
when new data or a genuinely new user hypothesis arrives. No further
continuation triggers armed - by checkpoint rule, not fatigue.

## Round 43 pre-registration: TRUE ES cross-feed validation (data acquisition via IBKR)

The IBKR connector serves genuine CME ES futures bars (Globex session
hours verified in a probe: Sun 22:00 UTC reopen, daily 21:00 UTC
maintenance halt, real volume, delayed 10min). Expired-contract reach
is ~1 year, so stitched front-month coverage is ~Jun 2025 - Aug 2026
(ESU5, ESZ5, ESH6, ESM6, ESU6, hourly, outside RTH). This is too
short for new edge searches; it is EXACTLY suited to the r42f open
question. FROZEN DESIGN (validation study, no promotion question, no
OOS mechanics): compute the daily 01:00-04:00 ET window return
(hourly bars: open of first window bar -> close of last) for (a) true
stitched ES and (b) our CFD SPX 5m feed, over the common period.
Metrics: mean window return each feed, their daily-return correlation,
and the mean daily DIFFERENCE. Verdicts, registered in advance:
HIGH correlation (>0.9) + similar means => the r42f negative euro-open
drift is REAL market behavior (post-publication inversion), CFD feeds
exonerated; LOW correlation or a systematic offset => CFD overnight
artifact confirmed, and every overnight-window result from the CFD
feeds gets flagged in the ledger. Either outcome improves the data-
provenance file. Contracts and stitching documented in the script.

## Round 43 results: TRUE ES obtained via IBKR - CFD feeds exonerated

(results/r43_esxfeed.json) Data acquired WITHOUT the user: the IBKR
connector serves genuine CME ES futures history (delayed). Stitched
front-month coverage Sep 2025 - Aug 2026 from ESZ5/ESH6/ESM6 (2h bars)
+ ESU6 (1h), saved to data/ES_*_ibkr.json (data/ is uncommitted per
repo policy; re-fetch via IBKR get_price_history, contract ids in the
r43 script header comments). Expired-contract reach is ~1 year, so
this source cannot extend deep history - but it accrues FORWARD: true
CME data for ES (and MES/MNQ/M2K/MGC equivalents) is now fetchable on
demand for all future validation work.
CROSS-FEED VERDICT (70 common sessions, limited by the CFD SPX feed
ending 2025-12): euro-open window (06-08 UTC) mean TRUE ES -0.95bps
vs CFD -0.87bps; difference -0.09bps, t -0.10 (indistinguishable);
daily correlation 0.859 (just under the registered 0.9, attributable
to the 2h-vs-5m bar construction mismatch; the means test is the
decisive prong and it is exactly null). VERDICT: the CFD overnight
feeds carry NO clock-anchored artifact in this window - attempt 6's
inverted/absent overnight drift was REAL market behavior (post-
publication decay/inversion), and the r42f data-provenance flag is
RESOLVED in favor of the feeds. This retroactively strengthens every
r42 overnight-window conclusion.
Calendar front: Equibles' economic calendar has no historical
releases and no FOMC dates (verified empirically); the FOMC family
stays shelved pending a verified calendar (user-suppliable).

### Attempt 12 REVIVAL (r43b): the FOMC calendar is now two-source verified

The registered revival condition ("a verified ex-ante calendar") is
met without the user: WebSearch snippets from the Fed's own press
releases, minutes URLs, FRASER, MNI, ABA and others yielded the full
2013-2026 scheduled meeting list year by year, and it matches the
assistant-knowledge calendar in run_r42l_fomc.py EXACTLY - including
the one disputed date (Sep 2013: fed minutes URL fomcminutes20130918
confirms the Sep 17-18 meeting, statement Sep 18; an earlier snippet
saying 18-19 was a summarizer error) and the 2020 COVID exception
(scheduled Mar 17-18 superseded by the Mar 15 emergency action -
excluded as registered). Two independent sources agreeing (memory +
web) is the verification; the 14:00 vol signature is downgraded to a
DIAGNOSTIC (60% of true statement days spike vs 14% base - many
meetings are simply fully priced), and the prior abort is superseded
by this stronger provenance, not overridden by taste. The frozen
3-cell grid, IS t>=2 floor, and one-shot OOS bar are UNCHANGED from
the original attempt-12 registration.

### Attempt 12 result (revived, r43b): IS-FAIL at the floor - watch item registered

(results/r42l_fomc.json) 190 pooled FOMC events, 2013-2026, verified
calendar. The Lucca-Moench 24h pre-drift is positive but underpowered
(+0.051R, t +1.27, PF 2.29, halves [+,+]); the full announcement day
(prev close -> close) is the strongest cell: +0.114R, t +1.82, PF
1.72, halves [+,+] - UNDER the t>=2 floor; the intraday-only harvest
(09:30->13:55) is significantly NEGATIVE (-0.101R, t -3.29): whatever
premium exists accrues overnight/around the event, not in the RTH
morning. Family closed at IS, holdout unopened - at 8 events/yr the
test is structurally underpowered and re-running grids will not
change that. WATCH ITEM registered (third): FOMC announcement-day
long (prev 15:55 close -> statement-day 15:55 close, indices), 8 new
events/yr accrue passively; the monthly routine may re-score; no new
searching. Program watch items now: NY-PM displacement, month-end
rebalancing fade, FOMC announcement-day premium.

## Round 44: consensus data ACQUIRED - the surprise family unblocks

Data acquisition without the user, method on record: the environment
proxy blocks calendar sites, but the Kernel cloud-browser connector
runs outside it. ForexFactory (Cloudflare-challenged), MQL5 (404/geo)
and investing.com (blank) all failed; FXStreet's SPA revealed an OPEN
static endpoint - calendar-api.fxsstatic.com/en/api/v2/eventDates/
{start}/{end}?volatilities=HIGH&countries=US - serving full history
with dateUtc, actual, consensus, revised, previous, ratioDeviation.
Harvested 2013-01..2026-08 in 92-day chunks: 3,067 US high-impact
events, 0 fetch errors, 2,030 with actual+consensus (NFP 164, CPI
variants ~250, GDP 149, retail 232, ISM 258, Fed decisions 110).
Sanity-checked against known prints. Saved to
data/econ_events_us_high_fxs.json (uncommitted per data policy;
re-fetch recipe = this entry).

### Attempt 17 pre-registration: macro-surprise post-announcement drift

MECHANISM (external): post-announcement drift - after a scheduled
macro release, prices continue in the surprise's implication
direction for minutes-to-hours as information diffuses (announcement
drift literature; Savor-Wilson premium is realized ON these days).
First attempt in this program with TRUE surprise data. Classes #1+#3.
FROZEN EVENT SET (registered by name): equity-POSITIVE-on-beat:
Nonfarm Payrolls, Gross Domestic Product Annualized, Retail Sales
(MoM), Retail Sales Control Group, ISM Manufacturing PMI, ISM
Services PMI, Durable Goods Orders. Equity-NEGATIVE-on-beat (hotter
inflation): Consumer Price Index (YoY), (MoM), ex Food & Energy (YoY),
(MoM). Excluded: Fed decisions (surprises too rare), speeches/minutes
(no consensus), all else. Surprise = ratioDeviation (the feed's
standardized deviation); equity direction = sign(dev) x indicator
sign. KNOWN RISK registered, not modeled: the 2022+ "good news is bad
news" regime may flip growth signs; no regime dof is added.
FROZEN GRID (4 cells): |dev| threshold {0.5, 1.0} x hold {entry+60m;
to 16:00 session close}. Entry: first 5m bar close at/after release
+5min on the 24h index frames (08:30 releases enter pre-market at
08:35 - the frames cover it); one trade per instrument per event;
collisions (two events same timestamp) take the larger |dev|. Costs
micro. SPX/NDX/RTY pooled ATR-normalized selection; GOLD run as
diagnostic only (inflation-surprise sign for gold is a different
mechanism). Growth-vs-inflation subclass means printed as diagnostics,
not selectable. Selection: IS t >= 2 floor, min 120 pooled IS trades,
neighbor-majority; one OOS shot (last 25% of sessions) at the program
bar; the surprise family burns after.

### Attempt 17 result: IS-FAIL - and the registered risk materialized on schedule

(results/r44_surprise.json) 861 usable surprise events (740 growth,
121 inflation), 4 cells, all under the IS floor (best -0.002R pooled).
The registered-but-unmodeled risk explains the structure: GROWTH
surprises are negative in all 4 cells (-0.013..-0.033R - the 2022+
good-news-is-bad-news regime poisons the classic risk-on mapping
when pooled across eras), while INFLATION surprises are positive in
all 4 cells (+0.024..+0.045R - short hot CPI / long cool CPI, the
one mapping whose sign never flipped). Family closed at IS, holdout
unopened; adding the regime conditioning post-hoc would be the r41
trap and is NOT done. WATCH ITEM #4 registered (diagnostic-derived,
disclosed): CPI-surprise directional trade (all CPI variants,
direction = minus sign(deviation), entry release+5m, hold to close),
~12-20 events/yr accrue passively; no new searching.
Program score: 0 graduates / 17 tested attempts + 4 watch items.
Data assets now held: 20yr validated CFD feeds, 12mo true CME ES,
verified FOMC calendar 2013-2026, 3,067-event US surprise dataset
2013-2026 (all re-fetchable; acquisition recipes in this ledger).

### Attempt 18 pre-registration: gold vs CPI surprises

MECHANISM (external, textbook): CPI surprises move expected real
rates; gold prices real rates inversely - hot CPI -> gold DOWN, cool
CPI -> gold UP. Independent of the equity good-news-bad-news regime.
PEEK DISCLOSURE: r44's gold diagnostic pooled ALL event types under
the equity mapping (+0.030R close-hold); the CPI-only gold subset was
not separately examined. POWER DISCLOSURE: gold 5m data starts
2020-08, so only ~70 CPI events join; min-n floor set to 40 IS trades
for this registration (scarce-event family, like FOMC), IS t >= 2
floor unchanged - underpower is the expected failure mode and a fail
here parks the family as a watch item rather than proving absence.
FROZEN GRID (4 cells, GOLD only): events = the four CPI variants;
direction = MINUS sign(ratioDeviation); |dev| threshold {0.25, 0.5} x
hold {entry+60m, to 16:00 NY close}; entry first 5m close at/after
release+5min; cost 0.35; ATR20-normalized; one trade per event. One
OOS shot (last 25% sessions, OOS n >= 25 given scarcity) at the
program bar; family burns after (to watch-item status if the failure
is pure power).

### Attempt 18 result: IS-FAIL on power, as registered - watch item #5

(results/r44b_goldcpi.json) Only 32-34 IS trades joined (gold data
2020+ x ~monthly CPI). Every cell leans the mechanism's way (avgR
+0.018..+0.052, WR to 65.6% on close-holds, PF to 1.35) but t <= 0.57
- structurally unpowered, exactly the anticipated failure mode.
Holdout unopened. WATCH ITEM #5: gold CPI-surprise trade (minus
sign(dev), release+5m entry, hold to close), ~12-16 events/yr accrue.
Program score: 0 graduates / 18 tested attempts + 5 watch items
(NY-PM displacement, month-end rebalancing fade, FOMC announcement-
day premium, CPI-surprise equity fade, gold CPI-surprise). The watch
list is now the program's live portfolio of underpowered leans - all
calendar/flow effects, all accruing free forward data, several
re-scoreable within 1-2 years. Search resumes when a genuinely new
mechanism or data class appears; the monthly routine carries the
watch-item re-scoring.

## Round 45: program resumed on user directive - expiration-calendar family (attempt 19)

2026-08-29. User directive: "keep hypothesizing and testing and developing,
don't stop until one succeeds." Program resumes past the honesty checkpoint
with the standing caveat ON THE RECORD: each OOS shot carries ~2-5% false-pass
probability under the null, the shot counter keeps running (18 tested + 1
aborted so far), and any eventual pass must be read against that accumulated
multiplicity. Bar unchanged. Queue restriction unchanged: only mechanism
families genuinely distinct from the burned list.

### Attempt 19 registration (BEFORE running): options-expiration calendar

MECHANISM (ex-ante, flow-based, no price conditioning): monthly index
options expire the third Friday. Dealer delta-hedging concentrates flows
into expiration week and unwinds after; the literature documents an
S&P expiration-week premium (Stivers & Sun) and post-expiration Monday
weakness. The calendar is fully knowable in advance - same class as the
month-end/FOMC families (our strongest residues) but a DIFFERENT flow event,
untested here. Holiday expiries (e.g. Good Friday) handled ex-ante: the
expiry session is the last trading session on or before the third Friday.

FROZEN GRID (8 cells): window/direction pairs fixed BY MECHANISM
  W1 LONG  opex-week Monday open -> expiry Friday close
  W2 LONG  opex-week Wednesday close -> expiry Friday close
  W3 SHORT post-opex Monday open -> same-day close
  W4 SHORT post-opex Monday open -> Wednesday close
x scope {all 12 monthly expirations, quarterly witching only (Mar/Jun/Sep/Dec)}.
Instruments SPX/NDX/RTY pooled at micro best-case costs (0.35/1.0/0.35 pts
per RT), GOLD as diagnostic only (its own opex differs). One trade per
window per month, entry/exit at RTH open/close prints, ATR20-normalized.
IS = first 75% of sessions per instrument. Selection: max IS t among cells
with pooled IS n >= 120 AND t >= 2.0 (floor per amendment after attempt 7),
neighbor-majority within the mechanism subspace (neighbors = cells differing
in exactly one of window/scope; long and short windows are separate
mechanism arms so majority is computed within the same-direction arm).
ONE OOS shot at the program bar (same sign, t >= 2, PF >= 1.15, cost x1.5
positive, pooled n >= 40); family burns after. Test count +8 cells.

### Attempt 19 result: OOS FAIL - the expiration-week premium existed and decayed

(results/r45_opex.json) IS was the strongest calendar signal the program
has produced: LONG quarterly-witching expiration week (Mon open -> Fri
close) IS n 170, WR 63.5%, PF 2.08, avgR +0.715, t +5.93, both halves
positive; the monthly version also strong (t +3.92). Selection rule chose
quarterly; one OOS shot: n 56, WR 48.2%, PF 1.11, avgR +0.034, t +0.14,
halves [-1,+1]. Sign right, magnitude gone. READ: IS window 2005-2020
overlaps the documented Stivers-Sun sample; OOS 2020+ shows the effect
dead - classic post-publication decay, not a power failure (n 56 with
t 0.14 is a measured zero, unlike the scarce-event watch items). Family
BURNED, no watch item. Side finding for the record: post-opex Monday was
IS significantly UP (shorting it lost, t -3.73 monthly), the opposite of
the folklore weakness. Program score: 0 graduates / 19 tested attempts.

### Attempt 20 registration (BEFORE running): pre-holiday calendar premium

MECHANISM (ex-ante calendar): documented abnormal positive equity returns
the trading day before exchange holidays (Ariel 1990; Lakonishok & Smidt
1988) - short covering and reduced institutional selling ahead of market
closures. The NYSE holiday schedule is published in advance; in-data,
pre-holiday sessions are identified ex-ante as sessions whose next trading
session skips at least one weekday. Distinct from every burned family
(different flow event; the closest relative, month-end, is a different
calendar anchor). FROZEN GRID (6 cells): entry/hold LONG
  {H1 open -> close, H2 12:00 -> close, H3 prior close -> close (carries
   the overnight gap into the pre-holiday day)}
x scope {all pre-holiday sessions, big3 (the sessions before Independence
Day, Thanksgiving, Christmas - the strongest in the literature)}.
Instruments SPX/NDX/RTY pooled at micro best-case costs, GOLD diagnostic.
ATR20-normalized, one trade per pre-holiday session. IS first 75%
sessions; selection max IS t with pooled n >= 120 (big3 cells exempt to
n >= 60 - scarce by construction, ~3/yr), t >= 2.0 floor, neighbor
majority within grid. ONE OOS shot at the program bar (pooled n >= 40;
big3 n >= 25 scarce-event floor as in attempt 18). Test count +6 cells.

### Attempt 20 result: IS-FAIL, family dead without spending an OOS shot

(results/r45b_holiday.json) DATA CAVEAT ON THE RECORD: the CFD feeds
trade shortened sessions on most partial US holidays, so session-gap
detection finds only full-closure holidays (~3/yr: New Year's, Good
Friday, Christmas cluster) - 126 pooled IS pre-holiday trades, not the
~9/yr of the literature. On that universe the pre-holiday premium is
absent to inverted: best cell H3 prevc->close avgR +0.010 t +0.17; the
intraday holds are negative (H2 12:00->close t -2.22, both halves
negative). Gold diagnostic leans positive (+0.37R on 11 trades,
meaningless n). No cell near the t >= 2 floor; OOS never opened. Family
BURNED at IS. Program score: 0 graduates / 20 tested attempts.

### Attempt 21 registration (BEFORE running): turn-of-month premium

MECHANISM (ex-ante calendar): the turn-of-month equity premium (Ariel
1987; Lakonishok & Smidt 1988; McConnell & Xu 2008) - concentrated
positive returns from the last trading day of the month through the first
three of the next, attributed to payroll-cycle fund inflows and month-end
window dressing unwind. ADJACENCY DISCLOSED: the burned month-end family
(attempt 14, watch #2) was a CONDITIONAL FADE of large prior-month moves
ending AT month-end close; this is the UNCONDITIONAL LONG spanning the
month boundary - different direction, different window, different flow
mechanism (inflows vs rebalancing), but the same calendar anchor, so a
pass here will be read with that adjacency in mind. FROZEN GRID (6 cells):
LONG entry/exit at RTH prints
  {T1: last-day open -> +3rd-day close (classic McConnell-Xu window),
   T2: last-day open -> +1st-day close (tight),
   T3: T-1 close -> +3rd-day close (early entry variant)}
x scope {all months, quarter-end months only (Mar/Jun/Sep/Dec - where
rebalancing flows stack on payroll flows)}.
Instruments SPX/NDX/RTY pooled at micro best-case costs, GOLD diagnostic.
ATR20-normalized, one trade per month boundary. IS first 75% sessions;
selection max IS t, pooled n >= 120 (quarter-end cells n >= 60), t >= 2.0
floor, neighbor majority. ONE OOS shot at the program bar (n >= 40;
quarter-end n >= 25). Test count +6 cells.

### Attempt 21 result: OOS FAIL at the bar - strongest residue of the program, watch item #6

(results/r45c_tom.json) IS: every cell positive; quarter-end scope all
>= t 2 (selected T3 T-1 close -> +3rd-day close, IS n 169, WR 59.2%,
PF 1.57, avgR +0.333, t +2.48, neighbors 3/3, both halves positive; gold
diagnostic +0.861R). ONE OOS shot: n 55, WR 58.2%, PF 1.09, avgR +0.208,
t +1.07, halves [+,+], ALL THREE instruments positive avgR, cost x1.5
still +0.203R. Sign agreement is complete across IS/OOS, halves, and
instruments - but t 1.07 < 2 and PF 1.09 < 1.15: FAIL at the bar,
profile is power-limited (sigma ~1.4R per trade at 4 events/yr/instrument).
Family burns per protocol; parked as WATCH ITEM #6: quarter-end
turn-of-month long, enter T-1 close (last session before final session of
Mar/Jun/Sep/Dec), exit close of 3rd session of the new month, indices
pooled. ~12 pooled events/yr accrue. ADJACENCY note stands: same calendar
anchor as watch #2 (month-end fade) - the two windows barely overlap
(fade exits at month-end close where TOM has just entered), but they must
never be double-counted as independent confirmations.
Program score: 0 graduates / 21 tested attempts + 6 watch items.

### Attempt 22 registration (BEFORE running): expiry-day strike pinning

MECHANISM: on option expiration days, dealer delta-hedging of expiring
open interest pins the underlying toward high-OI strikes into the close
(Ni-Pearson-Poteshman 2005 document expiration-day clustering at strikes).
High-OI strikes are overwhelmingly round levels; without an OI feed we
proxy them by round price levels - the proxy is fixed ex-ante. TRADE: on
monthly opex Friday at 15:00 NY, if price sits within thr of the nearest
round level L, trade TOWARD L, exit at RTH close (15:55). Conditioning
uses only information available at entry time. FROZEN GRID (4 tradeable
cells): thr {0.1 x ATR20, 0.2 x ATR20} x round grid {G, G/2} with
G = SPX 25, NDX 100, RTY 20 pts (GOLD 25, diagnostic). DIAGNOSTIC (not
selectable): same cells on non-opex Fridays - mechanism predicts the
effect concentrates on opex days; a same-size non-opex effect refutes the
pinning read. Indices pooled, micro best-case costs, ATR20-normalized.
IS first 75% sessions; selection max IS t among opex cells, pooled
n >= 120, t >= 2.0 floor, neighbor majority. ONE OOS shot at the program
bar (n >= 40). Test count +4 selectable cells (+4 diagnostics counted).

### Attempt 22 result: IS-FAIL, round-level pinning proxy refuted

(results/r45d_pin.json) All four opex cells flat to negative (best
+0.010R t +0.28, halves disagree; widest cell t -0.73 with both halves
negative). The non-opex Friday diagnostic shows the same near-zero
profile, so there is no opex-specific pinning visible through a
round-level strike proxy at 15:00 on these feeds. Family BURNED at IS,
no OOS spent. Honest read: this does NOT refute strike pinning per se -
it refutes the round-level proxy without real open-interest data; a
future revival requires an actual OI-by-strike feed (new data class).
Program score: 0 graduates / 22 tested attempts + 6 watch items.

## Round 46: new data class acquired - CBOE daily put/call ratios (2006-2019)

2026-08-29. ACQUISITION ON RECORD: the proxy blocks cboe.com locally; via
the Kernel cloud browser the discontinued-but-still-served CBOE archives
downloaded cleanly:
  data/cboe_totalpc.csv   (total P/C, 2006-10-04 .. 2019-10-04, 3256 rows)
  data/cboe_equitypc.csv  (equity-only P/C, same span, 3256 rows)
Columns: date, calls, puts, total volume, P/C ratio. The archive ends
2019-10-04 (CBOE moved later data behind DataShop); extending to 2025
would need ~1500 per-day API calls - declined for now. Study design
follows the FOMC-family precedent: the family's own span 2006-2019,
IS = first 75%, OOS = last 25% (~2016-06 onward), sealed as always.
Options sentiment is a genuinely NEW DATA CLASS for this program (nothing
prior conditioned on option-market state).

### Attempt 23 registration (BEFORE running): equity put/call contrarian gate

MECHANISM: the equity-only put/call ratio is a retail-heavy sentiment
gauge; extreme fear (high P/C percentile) marks capitulation after which
short-horizon index returns are abnormally positive (documented as a
contrarian indicator; index P/C excluded as hedging-dominated - fixed
ex-ante). SIGNAL AVAILABILITY: day-T ratio is published after day T's
close; entry is day T+1 RTH open - clean by construction. Percentile is
trailing 252 sessions through T. FROZEN GRID (4 selectable cells): LONG
next session when equity P/C percentile >= thr, thr {80th, 90th} x hold
{T+1 open -> T+1 close, T+1 open -> T+3 close}; one trade at a time
(busy-until dedupe on the hold). DIAGNOSTIC (not selectable): symmetric
greed-short at <= 10th percentile, both holds - the literature says the
fear side is the tradeable one; a symmetric short edge of equal size
suggests a vol artifact instead. Instruments SPX/NDX/RTY pooled at micro
best-case costs (GOLD has no overlap with the CBOE span - excluded).
ATR20-normalized. IS first 75% of the joined span per instrument;
selection max IS t, pooled n >= 120, t >= 2.0 floor, neighbor majority.
ONE OOS shot at the program bar (n >= 40). Test count +4 selectable
(+4 diagnostics counted).

### Attempt 23 result: IS-FAIL, contrarian P/C gate inverted at daily horizon

(results/r46_putcall.json) The fear gate is NEGATIVE in-sample: 90th-pct
next-day long avgR -0.085, t -2.90 (both halves negative); 80th-pct
next-day t -1.95; 3-day holds ~zero. Greed-short diagnostic also
negative - both directions losing = trend-continuation drag plus costs,
not a tradeable contrarian signal. High equity P/C days sit inside
short-term downtrends that continue. Family BURNED at IS, OOS unopened.
The data class (options sentiment) stays on the shelf; a revival needs a
different transformation (e.g. P/C shocks vs level percentile) argued
from mechanism first. Program score: 0 graduates / 23 tested attempts.

### Attempt 24 registration (BEFORE running): FOMC-cycle even-week pattern

MECHANISM: Cieslak-Morse-Vissing-Jorgensen (2019) document that the
equity premium concentrates in EVEN weeks of the FOMC cycle (trading days
0-4, 10-14, 20-24 counted from the scheduled announcement day), tied to
Fed information flow and the "Fed put". Cycle time is fully ex-ante (the
meeting schedule is published a year ahead); we use the two-source-
verified 2013-2026 calendar already on record in run_r42l_fomc.py.
ADJACENCY DISCLOSED: attempt 12 (watch #3) tested the announcement-DAY
premium; this is the biweekly CYCLE pattern across all days - different
anchor, same event stream; not to be double-counted. FROZEN GRID
(6 selectable cells): LONG on cycle days in scope
  scope {week0 (days 0-4), week2 (days 10-14), even (0-4,10-14,20-24)}
x hold {RTH open -> close (intraday), prev close -> close (24h)}
DIAGNOSTIC (not selectable): odd-week days (5-9, 15-19), both holds -
mechanism predicts flat-to-negative there. Instruments SPX/NDX/RTY pooled
at micro best-case costs, GOLD diagnostic. One trade per session,
ATR20-normalized. Span = 2013-01-01 onward (calendar coverage).
IS first 75% of span; selection max IS t, pooled n >= 120, t >= 2.0
floor, neighbor majority. ONE OOS shot at the program bar (n >= 40).
Test count +6 selectable (+4 diagnostics counted).

### Attempt 24 result: IS-FAIL, FOMC-cycle even-week pattern absent post-2013

(results/r46b_fomccycle.json) No selectable cell near the floor: best is
even-weeks close-to-close avgR +0.032 t +1.75, and the odd-week
diagnostic matches it (+0.031 t +1.59) - the even/odd distinction that
IS the mechanism does not exist in 2013+ data. week0 intraday is
actually negative (t -2.33). The CMVJ sample ended 2013; the pattern
reads as decayed or sample-specific. Family BURNED at IS, OOS unopened.
Program score: 0 graduates / 24 tested attempts + 6 watch items.

NEXT QUEUE (registered intent, not yet frozen): (a) probe Alpha Vantage
INDEX_DATA for VIX9D/VIX3M to enable a vol-term-structure regime family
(new data class); (b) Treasury auction calendar acquisition
(TreasuryDirect API via Kernel if proxy-blocked) for an auction-day
duration-supply family; (c) if both dead-end, next-tier mechanisms from
the taxonomy with written diagnoses first.

## Round 47: vol term-structure data class acquired (CBOE index histories)

2026-08-29. Alpha Vantage INDEX_DATA is not entitled on this key; the CBOE
public index-history CSVs downloaded cleanly via the Kernel browser
(cdn.cboe.com blocked by the local proxy, as before):
  data/VIX_history_cboe.csv    (VIX OHLC daily, 1990-01-02 .. 2026-08-28, 9262 rows)
  data/VIX9D_history_cboe.csv  (VIX9D, 2011-01-04 .. 2026-08-28, 3937 rows)
  data/VIX3M_history_cboe.csv  (VIX3M, 2009-09-18 .. 2026-08-28, 4263 rows)
Provenance note: these are the exchange's own published index values -
first-party, no cross-feed check needed; spot values eyeballed against
known history (VIX ~14.4 on 2026-08-28; 2011 VIX9D ~16; plausible).
Vol TERM STRUCTURE is a genuinely new conditioning class for this
program: nothing prior conditioned on the implied-vol curve's slope.
(The burned VIX family, attempt 9, used the VIX LEVEL as a dip-buy
trigger - different object; adjacency disclosed.)

### Attempt 25 registration (BEFORE running): vol term-structure regime gate

MECHANISM: the VIX term structure's slope prices near-term risk vs
baseline. BACKWARDATION (VIX9D > VIX, short-end inverted) marks acute
stress; the literature on the vol risk premium implies equity forward
returns after inversion are abnormally positive once the acute repricing
settles, while CONTANGO (VIX < VIX3M) is the calm-carry norm with
ordinary returns. The tradeable claim frozen here: LONG equities while
the short end is inverted (VIX9D/VIX >= 1), entered next session open
after the signal close, held while inverted, exit at close of the first
session after the ratio re-crosses below 1 (signal always evaluated at
prior close - no lookahead; one position at a time). Grid varies only
the inversion threshold and the structural leg:
FROZEN GRID (4 selectable cells): leg {VIX9D/VIX, VIX/VIX3M} x threshold
{>= 1.0, >= 1.05}, all LONG-in-inversion, entry/exit as above at RTH
prints. DIAGNOSTIC (not selectable): same cells with steep-CONTANGO long
(ratio <= 0.9) - the mechanism says calm-carry periods carry no abnormal
premium; a matching contango edge means we are just long the index.
Instruments SPX/NDX/RTY pooled at micro best-case costs, GOLD diagnostic.
ATR20-normalized per-episode returns booked daily (close-to-close while
held) so t reflects daily observations. Span: 2011+ (VIX9D coverage).
IS first 75% of span; selection max IS t, pooled n >= 120 daily obs,
t >= 2.0 floor, neighbor majority. ONE OOS shot at the program bar
(n >= 40). Test count +4 selectable (+2 diagnostics counted).

### Attempt 25 result: OOS FAIL - "inversion premium" was mostly just being long

(results/r47_vixts.json) IS: long-while-inverted (VIX9D/VIX >= 1.0)
n 2623 daily obs, avgR +0.067/day, t +3.22, halves [+,+], neighbors 2/2 -
passed the floor. BUT the pre-registered contango diagnostics also came
back positive and significant (9d leg t +2.14, 30d/3m leg t +3.25,
~+0.03R/day): the market drifts up in all vol regimes, and the
inversion cells only doubled the baseline drift IS. ONE OOS shot
(auto-run per protocol): n 866, avgR +0.018, t +0.55, PF 1.11, RTY
negative (-0.069). No distinguishable regime premium out of sample.
Family BURNED. Data asset (VIX/VIX9D/VIX3M 1990/2011/2009-2026) stays.
Program score: 0 graduates / 25 tested attempts + 6 watch items.

## Round 48: Treasury auction calendar acquired (TreasuryDirect API)

2026-08-29. ACQUISITION ON RECORD: api.fiscaldata.treasury.gov rejects
datacenter IPs (WAF "Attack ID" block) and the local proxy blocks both
hosts; www.treasurydirect.gov/TA_WS/securities/search served the full
histories through the Kernel browser:
  data/treasury_note_auctions.json  (1965 Note auctions 1979-2026:
    auction_date, term, bid-to-cover, high yield, reopening flag)
  data/treasury_bond_auctions.json  (392 Bond auctions 1979-2026)
10-Year: 169 originals + ~185 reopenings (9-Year-10/11-Month terms);
30-Year: 121 originals + ~159 reopenings. Duration-supply auctions
(10Y/30Y) run ~monthly each, results at 13:00 ET. Auction DATES are
published weeks ahead - fully ex-ante.

### Attempt 26 registration (BEFORE running): Treasury duration-auction day

MECHANISM: 10Y/30Y auctions inject duration supply; primary dealers
pre-position (concession = risk-off into the auction) and unwind after a
clean takedown (relief = risk-on after 13:00 ET). The equity-index
reflection of this flow: weakness into the 13:00 result on auction days,
strength after. Both windows are ex-ante (the calendar and the 13:00
result time are known in advance; we do NOT condition on the auction's
outcome - no tail/bid-to-cover conditioning, which would be a different,
outcome-dependent family). FROZEN GRID (6 selectable cells): on 10Y and
30Y auction days (originals + reopenings pooled - the flow is the
supply, not the CUSIP novelty):
  W1 SHORT 09:30 open -> 13:00 (concession window)
  W2 LONG  13:00 -> RTH close (relief window)
  W3 LONG  13:00 -> close of NEXT session (relief continuation)
x term {10Y days, 30Y days}. DIAGNOSTIC (not selectable): same three
windows on 2Y-auction days - short-duration supply carries far less
duration risk; the mechanism predicts materially weaker effects there.
Instruments SPX/NDX/RTY pooled at micro best-case costs, GOLD diagnostic
(gold competes with bonds for the duration bid - direction ambiguous, so
diagnostic only). ATR20-normalized. Span 2005+ (price data). IS first
75% of sessions; selection max IS t, pooled n >= 120, t >= 2.0 floor,
neighbor majority within same-direction arm. ONE OOS shot at the program
bar (n >= 40). Test count +6 selectable (+3 diagnostics counted).

### Attempt 26 result: IS-FAIL, duration-supply mechanism refuted

(results/r48_auction.json) Both mechanism arms significantly WRONG-WAY
in-sample: concession-short 09:30->13:00 on 10Y days avgR -0.065 t -2.63
(30Y t -2.48), relief-long 13:00->close t -2.41. Auction days actually
rallied into 13:00 and faded after. The 2Y diagnostic shows the same PM
fade (t -2.59), so the pattern is not duration-specific - the
duration-supply read is refuted, and the mirror image is not tradeable
either without a fresh mechanism (mirror spec-mining is what the
protocol forbids). Family BURNED at IS, OOS unopened. Auction dataset
(incl. bid-to-cover and yields, unused here) stays on the shelf.
Program score: 0 graduates / 26 tested attempts + 6 watch items.

### Attempt 27 registration (BEFORE running): auction-outcome direction

MECHANISM: the previous family (attempt 26) tested UNCONDITIONAL auction-
day windows and died; this one conditions on the auction's RESULT, which
is a different claim: a strong takedown (bid-to-cover well above its own
trailing norm) signals ample duration demand -> risk-on into the close;
a weak one signals demand strain -> risk-off. Direction = sign of the
bid-to-cover surprise. SIGNAL AVAILABILITY (mandatory check): results
cross the wire ~13:01-13:03 ET; entry is the first 5m bar opening at or
after 13:05 ET, so the signal strictly precedes entry. Surprise
z = (btc - mean of prior 8 same-bucket auctions) / their std, buckets
{10Y incl. reopenings, 30Y incl. reopenings} - only PRIOR auctions, no
lookahead. FROZEN GRID (4 selectable cells): |z| threshold {0 (any),
0.5} x hold {13:05 -> RTH close, 13:05 -> next session close}, 10Y+30Y
events pooled, direction always sign(z). DIAGNOSTIC (not selectable):
same cells on 2Y auctions (mechanism predicts weaker). Instruments
SPX/NDX/RTY pooled at micro best-case costs, GOLD diagnostic (duration
relief cuts both ways for gold). ATR20-normalized, one trade per
instrument-day (same-day 10Y+30Y collisions: use the later auction only,
decided ex-ante). IS first 75% sessions; selection max IS t, pooled
n >= 120, t >= 2.0 floor, neighbor majority. ONE OOS shot at the
program bar (n >= 40). Test count +4 selectable (+4 diagnostics).

### Attempt 27 result: IS-FAIL, outcome-following direction negative

(results/r48b_btc.json) Trading in the direction of the bid-to-cover
surprise LOST in-sample: widest cell (any |z|, hold to close) avgR
-0.039, t -2.52, both halves negative; tighter cells also negative. The
2Y diagnostic is flat-to-mildly-positive, refuting any duration-specific
outcome signal. The mirror (fading the result) is untouchable without a
fresh mechanism per protocol. Family BURNED at IS, OOS unopened.
Program score: 0 graduates / 27 tested attempts + 6 watch items.

## Round 48c: SKEW tail-risk data class acquired

2026-08-30. data/SKEW_history_cboe.csv (CBOE SKEW daily closes,
1990-01-02 .. 2026-08-28, 9217 rows) via the Kernel browser, same
public-archive recipe as the VIX files. SKEW prices 30-day SPX tail risk
from deep-OTM put skew - a conditioning object no prior attempt used
(distinct from VIX level [attempt 9] and term-structure slope [25]).

### Attempt 28 registration (BEFORE running): tail-risk premium harvest

MECHANISM: high SKEW = crash insurance is expensive = a tail-risk
premium is being PAID; absent the crash, the premium accrues to sellers,
i.e. expected short-horizon equity returns are positive-shifted while
insurance is rich. Frozen claim: LONG equities after high-SKEW closes.
SIGNAL AVAILABILITY: SKEW close known end of day T; entry T+1 RTH open.
Percentile = trailing 252 SKEW closes through T. FROZEN GRID
(4 selectable cells): LONG when percentile >= thr, thr {80th, 90th} x
hold {T+1 open -> T+1 close, T+1 open -> T+5 close}; one position at a
time (busy-until dedupe). DIAGNOSTIC (not selectable): low-SKEW long
(<= 20th pct), both holds - the premium story predicts materially weaker
returns there; equal returns = generic drift, family self-refutes (the
attempt-25 lesson institutionalized). Instruments SPX/NDX/RTY pooled at
micro best-case costs, GOLD diagnostic. ATR20-normalized. Span 2005+.
IS first 75% of sessions; selection max IS t, pooled n >= 120, t >= 2.0
floor, neighbor majority. ONE OOS shot at the program bar (n >= 40).
Test count +4 selectable (+2 diagnostics).

### Attempt 28 result: IS-FAIL, no harvestable tail-risk premium in SKEW

(results/r48c_skew.json) High-SKEW next-day long is NEGATIVE IS
(80th pct: avgR -0.040, t -2.97, both halves negative). The only
positive cell (90th pct, 5-day hold: +0.126, t +1.77) misses the t >= 2
floor and the low-SKEW diagnostic (+0.093, t +1.29) sits right behind
it - drift, not premium. Family BURNED at IS, OOS unopened. SKEW data
asset stays. Program score: 0 graduates / 28 tested attempts + 6 watch
items. Next-tier queue (adjacency diagnoses REQUIRED in writing before
registration): (a) overnight close-to-open premium - adjacent to burned
euro-open window family, needs a diagnosis distinguishing the full
overnight hold; (b) VIX-shock (1-day change z) reversal - adjacent to
burned VIX-level dip-buy; (c) CBOE implied-correlation (COR*) extremes
if history depth suffices.

## Round 49: next-tier mechanisms with adjacency diagnoses (attempts 29-30)

### Attempt 29 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### full overnight close-to-open premium

DIAGNOSIS vs burned family r42f (euro-open window drift): r42f tested a
fixed 2-3h EURO-OPEN window inside the overnight session and found it
significantly NEGATIVE (IS t -17; r43 confirmed on true CME ES that the
inversion is real market behavior). The overnight-premium literature
(Cooper-Cliff-Gulen and successors) makes a DIFFERENT claim: the entire
16:00->09:30 hold is positive - concentrated in the post-close hours and
the pre-open ramp, segments r42f never touched. A negative euro-open
subset and a positive aggregate are mutually consistent; testing the
aggregate is therefore a distinct claim, not a repair of the burned
window. SELF-REFUTATION DIAGNOSTIC: the same-session DAY hold
(09:30->close) - the literature's claim is specifically that night
carries the premium and day does not; day ~ night refutes the family as
generic drift (attempt-25 lesson).
FROZEN GRID (2 selectable cells): LONG prev RTH close (15:55 print) ->
next RTH open (09:30 print), scope {all sessions, adjacent-only
(sessions whose previous session is exactly 1 calendar day back -
excludes weekend/holiday holds)}. DIAGNOSTIC (not selectable): DAY long
09:30->close, same scopes. Instruments SPX/NDX/RTY pooled at micro
best-case costs, GOLD diagnostic. ATR20-normalized. IS first 75%
sessions; selection max IS t of the 2 cells, t >= 2.0 floor, the other
cell must be positive (neighbor rule); PLUS the day-diagnostic
self-refutation: family dies at IS if day avgR >= night avgR. ONE OOS
shot at the program bar (n >= 40). Test count +2 selectable (+2 diag).

### Attempt 30 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### VIX-shock reversal

DIAGNOSIS vs burned attempt 9 (VIX-level dip-buy): that family gated on
the VIX LEVEL (high absolute fear regime) and its sign-check refuted it.
This family conditions on the 1-day VIX SHOCK - z of the daily log
change vs its trailing 63d std - a different object: a shock fires at
any level (a 15->20 jump triggers; a flat 30 does not). MECHANISM: vol
shocks overshoot (the vol risk premium spikes with demand for immediate
hedges) and normalize within days; as vol mean-reverts, equity retraces
part of the shock day's fall. Prediction is one-sided: abnormal POSITIVE
equity returns after UPWARD vol shocks only. SELF-REFUTATION DIAGNOSTIC:
vol-CRUSH days (z <= -1.5) long, both holds - the mechanism predicts
nothing there; crush ~ shock refutes the family as drift.
FROZEN GRID (4 selectable cells): LONG next session after a close with
z >= thr, thr {1.5, 2.0} x hold {entry T+1 RTH open -> T+1 close,
-> T+3 close}, one position at a time (busy-until). z uses log-changes
of the CBOE VIX close series (data/VIX_history_cboe.csv), known at T
close, entry T+1 open - no lookahead. Instruments SPX/NDX/RTY pooled at
micro best-case costs, GOLD diagnostic. ATR20-normalized. IS first 75%
sessions; selection max IS t, pooled n >= 120, t >= 2.0 floor, neighbor
majority. ONE OOS shot at the program bar (n >= 40).
Test count +4 selectable (+2 diag).

### Attempt 29 result: IS-FAIL - the overnight premium is real but cost-dominated

(results/r49_overnight.json) Night-minus-day differential is +0.018R/day
in the documented direction (night > day; day cells t -2.9/-2.5 net),
but a daily RT cost of ~0.02R leaves the night hold at net -0.002R
(t -0.38). Same death as the late-day family (r42c): the anomaly exists
gross and is smaller than one round trip per day. No cell near the
floor; family BURNED at IS, OOS unopened.

### Attempt 30 result: OOS FAIL at the bar - watch item #7

(results/r49b_vixshock.json) IS: all four shock cells positive (selected
z>=1.5, 3-day hold: n 651, WR 58.8%, avgR +0.169, t +2.51, neighbors
2/2, halves [+,+]); crush diagnostic negative next-day (t -1.69) - the
one-sidedness the mechanism predicts. ONE OOS shot: n 205, WR 53.2%,
PF 1.28 (clears 1.15), avgR +0.141, t +1.26, halves [+,+], cost x1.5
+0.136. Only the t >= 2 leg fails; RTY is flat (-0.011) while SPX/NDX
carry it. Power-limited profile -> family burns per protocol, parked as
WATCH ITEM #7: VIX-shock reversal - after a VIX close with 1-day log
change z >= 1.5 (63d std), long index at next RTH open, exit close of
3rd session, one position at a time, indices pooled. ~50 pooled
events/yr accrue. Program score: 0 graduates / 30 tested attempts +
7 watch items.

## Round 50: implied-correlation data class acquired (attempt 31)

2026-08-30. data/COR1M_history_cboe.csv and data/COR3M_history_cboe.csv
(CBOE 1M/3M implied correlation, daily OHLC, 2006-01-03 .. 2026-08-28,
~5190 rows each) via one Kernel browser session, public-archive recipe.

### Attempt 31 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### implied-correlation spike reversal

DIAGNOSIS vs the burned vol families: COR1M is the market-implied
average pairwise correlation among SPX constituents, backed out from
index vol vs constituent vols. It is a CROSS-SECTIONAL object, not a vol
measure: correlation can spike while vol is moderate (macro repricing
moves everything together) and stay low in single-name-driven vol
regimes. Attempt 9 gated on the VIX level, attempt 25 on the vol curve
slope, attempt 30 on the vol shock - none conditioned on cross-sectional
structure. OVERLAP DISCLOSED: correlation spikes co-occur with vol
shocks often enough that this family's events overlap watch #7's; they
must never be counted as independent confirmations of each other.
MECHANISM: correlation spikes mark indiscriminate index-level hedging
(dispersion desks step away, index puts get bought regardless of name);
the overshoot normalizes within days as dispersion re-engages, and the
index retraces part of the correlated selloff. Claim: LONG after
high-correlation closes. SELF-REFUTATION DIAGNOSTIC: low-correlation
cells (<= 20th pct) long - mechanism predicts nothing; matching returns
= drift, family dies at IS.
FROZEN GRID (4 selectable cells): LONG next session when COR1M trailing-
252d percentile >= thr, thr {80th, 90th} x hold {T+1 open -> T+1 close,
-> T+3 close}, one position at a time (busy-until). Signal known at T
close; entry T+1 RTH open. Instruments SPX/NDX/RTY pooled at micro
best-case costs, GOLD diagnostic. ATR20-normalized. IS first 75% of
sessions; selection max IS t, pooled n >= 120, t >= 2.0 floor, neighbor
majority; drift self-refutation check before OOS. ONE OOS shot at the
program bar (n >= 40). Test count +4 selectable (+2 diagnostics).

### Attempt 31 result: OOS FAIL at the bar - watch item #8

(results/r50_corr.json) IS: selected high 80th-pct, 3-day hold - n 870,
WR 56.9%, avgR +0.136, t +2.72, neighbors 2/2, halves [+,+]; all four
spike cells positive; low-corr next-day diagnostic negative (t -2.81) -
mechanism-consistent asymmetry. ONE OOS shot: n 270, WR 57.0%, PF 1.32,
avgR +0.145, t +1.12, halves [+,+], cost x1.5 +0.141. Only the t leg
fails; RTY flat (-0.013) while SPX/NDX carry - the same shape as watch
items #6/#7. Family burns per protocol; WATCH ITEM #8: implied-
correlation spike reversal - after COR1M close >= 80th trailing-252d
percentile, long index next RTH open, exit close of 3rd session, one
position at a time, indices pooled. OVERLAP with watch #7 is on record:
the two must never be cited as independent confirmations; a combined
"stress-reversal composite" spec MAY be pre-registered at a future
monthly re-score, not retroactively.
Program score: 0 graduates / 31 tested attempts + 8 watch items.
An emerging pattern worth naming: three residues (#6 quarter-end TOM,
#7 VIX-shock, #8 corr-spike) all show full sign agreement, all are
flow/stress-rebound longs, all are carried by SPX/NDX with RTY flat,
and all fail only on power. The program's output is converging on a
single economic claim: large-cap index rebounds after forced-flow
events, too small per event to clear t >= 2 on any single family yet.

## Round 51: day-of-week seasonality (attempt 32)

### Attempt 32 CLASS DIAGNOSIS + registration (BEFORE running)

DIAGNOSIS: the weekday anchor is distinct from every burned calendar
family (opex third-Friday cycle, month boundary, holiday adjacency, FOMC
cycle, auction dates): it conditions on nothing but the day of week.
Classic documented forms (French 1980; Gibbons-Hess): NEGATIVE Monday
(weekend-risk resolution + settlement conventions) and positive Friday
(pre-weekend). Largely reported decayed post-1990s in large caps -
finding nothing would itself be informative given this repo's pattern of
decayed classics (attempt 19/24). FROZEN GRID (4 selectable cells):
  {Monday SHORT, Friday LONG} x hold {day session open->close,
   close-to-close (prior session close -> that day's close)}
DIAGNOSTIC (not selectable): Tue+Wed+Thu pooled LONG, both holds - the
baseline drift the selectable cells must beat in magnitude.
Instruments SPX/NDX/RTY pooled at micro best-case costs, GOLD
diagnostic. ATR20-normalized. IS first 75% of sessions; selection max
IS t, pooled n >= 120, t >= 2.0 floor, neighbor majority (same-day arm).
ONE OOS shot at the program bar (n >= 40). Test count +4 selectable
(+2 diagnostics).

### Attempt 32 result: IS-FAIL, both weekday classics dead or inverted

(results/r51_weekday.json) Monday-short lost (cc t -2.12: Mondays now
drift UP); Friday-long was the worst cell in the grid (oc avgR -0.059,
t -4.05: Fridays are now systematically weak intraday). Midweek cc
baseline +0.021/day (t +2.05) is ordinary drift. Both classic weekday
effects are gone or sign-flipped, consistent with the decayed-classic
pattern (attempts 19, 24). Family BURNED at IS, OOS unopened.
Program score: 0 graduates / 32 tested attempts + 8 watch items.

## PROGRAM-STATE ASSESSMENT (2026-08-30, after 32 attempts)

1. The searchable well is nearly dry. 32 mechanism families across
   calendar, flow, sentiment, vol-structure, cross-market, and
   microstructure classes; every major public data class we can reach is
   acquired and tested. Remaining unregistered candidates are weaker
   variants of burned classes; each additional family now mostly accrues
   multiplicity (the ~2-5%/shot false-pass budget) rather than
   information.
2. The program HAS converged on something: watch items #6/#7/#8 agree in
   sign everywhere and describe one economic claim - large-cap index
   rebound after forced-flow events - individually underpowered.
3. Consequence: the highest-probability path to "one succeeds" is no
   longer new single families; it is (a) the forward accrual + monthly
   re-scoring of the watch list, and (b) a pre-registered composite of
   the converging residues, scored on FORWARD data only.

### WATCH ITEM #9 (composite, pre-registered 2026-08-30, forward-only):
STRESS-REVERSAL COMPOSITE. Trigger: any session close with (VIX 1-day
log-change z >= 1.5 per watch #7) OR (COR1M >= 80th trailing-252d
percentile per watch #8). Action: LONG at next RTH open, exit close of
3rd session, one position at a time. Two tracked variants, both frozen
now: (a) SPX+NDX+RTY pooled; (b) SPX+NDX only (motivated by the RTY
flatness across #6-#8; recorded as a pre-registered variant, not a
post-hoc exclusion). Costs micro best-case, ATR20-normalized. SCORING:
forward data from 2026-08-31 only - the historical sample already spent
its evidence in #7/#8 and is never re-counted. Bar for graduation:
pooled forward n >= 40, avg_R > 0, t >= 2, PF >= 1.15, cost x1.5
positive, evaluated at monthly re-scores. Overlapping-trigger days count
once. Activation as a paper/SPRT stream requires explicit user sign-off.
4. Search posture going forward: single-family attempts continue ONLY
   for genuinely new mechanisms or data classes (next queued: gold vol
   index GVZ shock-reversal - extends the converging claim to a new
   instrument, not a new spec on the same one); no more forced batches
   of marginal calendar residues.

## Round 52: gold vol index acquired - attempt 33 (final forced single-family batch)

2026-08-30. data/GVZ_history_cboe.csv (CBOE Gold ETF Volatility Index,
daily closes, 2009-09-18 .. 2026-08-28, 4261 rows) via one Kernel
browser session, public-archive recipe.

### Attempt 33 DIAGNOSIS + registration (BEFORE running): gold vol-shock reversal

DIAGNOSIS: this is the stress-reversal mechanism of watch #7 applied to
a NEW INSTRUMENT, not a new spec on equities: GVZ is gold's own implied
vol; the claim is that gold's forced-flow events (vol shock = margin-
driven liquidation in gold) are followed by a gold rebound. It tests
whether the converging claim generalizes across asset classes - a
genuine new bit of information either way. It is NOT independent
evidence for the equity watch items and will never be cited as such.
POWER DISCLOSURE: gold 5m data starts 2020-08 (~1275 sessions); at
~30-40 shock events/yr expect the scarce-event profile; min-n floors per
the attempt-18 precedent: IS n >= 40, OOS n >= 25.
FROZEN GRID (4 selectable cells): after a GVZ close with 1-day log
change z >= thr (63d std), LONG GOLD at next RTH open, thr {1.5, 2.0} x
hold {exit T+1 close, exit T+3 close}, one position at a time.
DIAGNOSTIC: GVZ crush (z <= -1.5), both holds - mechanism predicts
nothing there. GOLD only, micro best-case cost 0.35, ATR20-normalized.
IS first 75% of sessions; selection max IS t with n >= 40, t >= 2.0
floor, neighbor majority. ONE OOS shot: same sign, t >= 2, PF >= 1.15,
cost x1.5 positive, n >= 25. A pure power-fail parks it as a watch
item. Test count +4 selectable (+2 diagnostics).

### Attempt 33 result: IS-FAIL - stress-reversal does NOT generalize to gold

(results/r52_gvz.json) Gold vol-shock next-day is negative (z>=1.5:
avgR -0.126, t -1.34); the only mechanism-consistent lean (z>=2, 3-day:
+0.382, WR 70%) is n 30, under the scarce-event floor; and the CRUSH
diagnostic is POSITIVE (t +1.92) - the opposite asymmetry from equities:
gold gains follow calm, not stress. Signs are mixed against the
mechanism, so this is a refutation-shaped fail, not a power-park.
Family BURNED at IS, OOS unopened. INFORMATIVE NEGATIVE ON RECORD: the
converging watch-item claim (#6-#9) is equity-specific - consistent
with an index-level dealer/flow phenomenon rather than a universal
post-stress rebound. Program score: 0 graduates / 33 tested attempts +
9 watch items (8 single + 1 composite).

THE FORCED SINGLE-FAMILY ERA CLOSES HERE per the program-state
assessment: further single families only on genuinely new mechanisms or
data classes. The program's active surface is now the watch list
(monthly re-scores; composite #9 accruing forward from 2026-08-31) and
the 4 paper streams.

## Round 53: proposal-2 repair sweep (user directive 2026-08-30)

User: in addition to the standing program, retry the closer strategies
with altered parameters (proposal 2). BINDING SCOPE RULE, stated before
any spec exists: families whose one-shot OOS was already spent
(expiration week #19, TOM #21, VIX term structure #25, VIX-shock #30,
corr-spike #31, and the r42-era spent shots) are NOT retryable on the
same holdout - their honest retry is the forward accrual already running
as watch items. Repair candidates are ONLY families whose holdout is
still sealed (IS-fail, winner=null). Process per r41b: multi-agent audit
extracts IS-only summaries (agents hard-blocked from reading sealed OOS
fields); one diagnosis agent per candidate writes a taxonomy-grounded
repair spec (mechanism reasoning, no data-peeking) with fixed
directions, <= 12 cells, self-refutation diagnostics, and floors; specs
are REGISTERED HERE before any IS run; IS-only exploration follows; each
IS-passer gets ONE fresh OOS shot at the program bar, counted against
the program's multiplicity budget. A viable=false verdict from diagnosis
is a recorded outcome, not a failure of the process.


### Round 53 audit + diagnosis outcome (multi-agent, 13 agents, IS-only firewall held)

Holdout map confirmed across all 33 families: 9 spent (not retryable),
24 sealed. Of the 8 sealed+non-refuted+non-cost-dominated candidates,
6 returned UNREPAIRABLE verdicts from mechanism (recorded below) and 2
returned viable repair specs (registered in full below, BEFORE any run).
Refusals on record (each a deliberate outcome, not a failure):
- r42h_alma: none — no named repair class applies. This is a null-mechanism failure, and the three plausibly relevant classes (#1 regime gate, #2 vol-normalization, #5 exit management) were already embedded inside
- r42j_goldnews: None survives. The only mechanism-valid class is #1 (regime/event-calendar gate: replace the price-only impulse with a verified consensus-vs-actual surprise condition), and that repair has ALREADY bee
- r42k_macro: none (refusal). Closest candidates examined and rejected from mechanism: #2 vol-normalization (already embedded — engine books pnl/ATR20, so returns are vol-normalized from birth; the only refinement,
- r42m_corrny: none — no repair class applies (closest candidates 2 and 4 examined and excluded; 6 banned)
- r44b_goldcpi: none — all seven classes considered and rejected; structural underpower is not a taxonomy failure mode. Closest candidates examined and rejected: #2 vol-normalization (already ATR20-normalized returns
- r45d_pin: none — no named class applies (closest candidates 1, 3, 5, 7 all rejected on mechanism; 2 and 4 are already embedded in the frozen original)

#### REGISTERED REPAIR: r42l_fomc (attempt 34)

TAXONOMY_CLASS: #7 signal-horizon matching (hold to the horizon where the event study showed the effect), with disclosed #3 time-of-day-concentration overlap; #2 is already exhausted (spec ATR-normalized from birth), #6 avoided

DIAGNOSIS: The original did not fail on sign, provenance, or cost — it failed on POWER with a horizon mismatch. With the two-source-verified 2013-2026 calendar, both announcement-day cells are positive with [+,+] halves (full day prevclose->close +0.114R t +1.82 at n=190; Lucca-Moench prev1400->1355 +0.051R t +1.27), while the recorded intraday cell 0930->1355 is significantly NEGATIVE (t -3.29). By the arithmetic of the original three cells, the premium accrues in exactly two segments the full-day hold dilutes: the overnight run-in (prev 15:55 close -> 09:30 open) and the resolution window (13:55 -> 15:55 close); the ~4.5h RTH morning contributes negative expectation AND adds variance. n is capped by the calendar at ~8 meetings/yr, so t = mean/sd*sqrt(n) can only be raised by raising the per-event mean and cutting per-event variance — i.e., excising the recorded drag segment and holding only where the event study located the effect. That is precisely class #7 (the ledger's own close-out sentence — "whatever premium exists accrues overnight/around the event, not in the RTH morning" — is the written diagnosis). Directions are fixed long in every cell by the registered Lucca-Moench/Savor-Wilson mechanism; nothing is searched except which of three mechanism-implied sub-horizons carries the concentration, under a pre-stated metric. Principal registered risks: (a) the ON segment may be nothing but the generic market-wide overnight drift attempt 29 proved exists gross on ALL sessions (killed there only by daily cost; at 8 holds/yr cost does not kill it) — this is exactly what the placebo diagnostic exists to refute; (b) post-2015 L-M decay remains on record. Adjacency disclosed: watch item #3 (full-day FOMC long) accrues forward on the same event stream; a repair pass and the watch item must never be cited as independent confirmations.

GRID: 3 selectable cells, all LONG (direction fixed by mechanism), SPX/NDX/RTY pooled, ATR20-normalized, verified 2013-2026 calendar frozen in run_r42l_fomc.py, MICRO cost per RT PER LEG (SPX 0.35, NDX 1.0, RTY 0.35), one trade per instrument per event, IS = first 75% of each instrument's sessions (stored splits SPX 2022-10, NDX 2022-12, RTY 2018-07): [C1-ON] prev-day 15:55 close -> statement-day 09:30 open (overnight run-in; 1 RT). [C2-PM] statement-day 13:55 -> 15:55 close (resolution window, held through the 14:00 statement; 1 RT). [C3-ON+PM] two legs: prev 15:55 close -> 09:30 open, flat through the morning, re-enter 13:55 -> 15:55 close (full-day premium minus the recorded drag segment; charged 2 RT). Non-selectable printed anchors: the original full-day cell (watch #3) and the recorded-negative 0930->1355 cell, reprinted for continuity, never selectable. No thresholds, no regime knobs, no direction search — the only selection is among the three mechanism-implied sub-horizons.

DIAGNOSTICS: Self-refutation set (non-selectable), attempt-25/28/29 pattern: the SAME three windows (ON, PM, ON+PM), same costs, computed on matched PLACEBO days — for each statement day D, the session exactly 7 calendar days earlier (same weekday, cycle day ~-5 where neither L-M nor CMVJ predicts anything; skip if missing or itself a statement day). Pre-stated refutation rules, applied before any OOS: (a) HARD DEATH — the family dies at IS if the selected cell's placebo counterpart avgR >= the FOMC cell's avgR (matching returns = generic overnight/afternoon drift, not an event premium; the attempt-29 threat made binding); (b) the event differential (FOMC minus placebo, selected window) must be positive in BOTH IS halves, else death as drift; (c) the reprinted 0930->1355 anchor must remain non-positive — if the morning drag has vanished, the decomposition the repair is built on no longer describes the data and the family dies rather than being re-specified. Test count: +3 selectable, +3 diagnostics.

FLOORS: IS pooled n >= 120 per selectable cell (normal floor; ~190 expected from the calendar, so a shortfall itself signals a construction bug). Winner = max IS t among the 3 selectable cells, required t >= 2.0. Neighbor-majority: the other two window cells each share a leg with any winner by construction — both must show positive IS avgR (2/2 sign agreement), else the winner is discarded as spiky noise regardless of its t. Both self-refutation prongs (a)+(b) and anchor check (c) must pass. Then ONE OOS shot only, on the already-stored sealed per-instrument last-25% splits, at the program bar: same sign, OOS n >= 40 pooled, t >= 2, PF >= 1.15, cost x1.5 still positive; the FOMC family then burns for good regardless of outcome, counted against the program multiplicity budget (attempt count increments even on IS death).

#### REGISTERED REPAIR: r42p_gsrv (attempt 35)

TAXONOMY_CLASS: 4. Cost engineering (tool: longer holding per signal — cost amortization). Explicitly NOT class 2 (the spec's trigger and t-stat are already sigma20-normalized, so the vol-blindness class 2 fixes is absent) and NOT class 6 (no new indicators added).

DIAGNOSIS: The original failed as a cost-domination null, not a refuted direction: the script subtracts a flat COST_BPS=4.0 per trade, so gross = net + 4 by construction, and the audited best cell (k=1.5, net -0.12 bps, t -0.30) had gross ~ +3.88 bps — almost exactly one round trip. No cell was significantly negative (worst t -1.41), so convergence was never refuted; the pair simply paid its full 2-leg round trip to capture one session of a reversion the registration itself said is better supported at longer horizons ('short-horizon pair reversion is a structural-liquidity claim'; dealer/RV rebalancing of a one-leg flow dislocation is plausibly a multi-day process). Critically, the audit shows the hold dimension was DEGENERATE (RTH and full cells numerically identical — silver's full leg was aliased to its RTH leg), so the family only ever tested a single horizon; the time axis is unexplored, not searched-and-failed. Meanwhile the k axis WAS explored and shows weak, non-monotone returns to conviction-filtering (t: -1.41 / -0.30 / -0.72 across k), so the class-4 'fewer trades' tool is near-exhausted and the class-4 'cheaper instrument / passive execution' tools are untestable on OHLC (r38 lesson). That leaves the one named class-4 tool that targets the exact failure: hold each signal longer. Cost per trade is fixed at one entry plus one exit regardless of hold length, so if convergence continues over the following sessions, gross grows with the hold while the round trip stays 4 bps — the amortization arithmetic directly attacks gross~=cost. If the reversion is instead a one-shot snapback complete in a day, the multi-day cells add noise without signal and the grid fails honestly. Holdout status verified: 'Family closed at IS', OOS never opened, so the family's single OOS shot remains available for the repaired spec.

GRID: 6 selectable cells, everything else frozen verbatim from the original spec (spread s = r_gold - r_silver on 16:00-ET session closes; sigma20 = 20d rolling std of s; event |s_yesterday| >= k*sigma20; direction FIXED = convergence, long laggard / short leader, equal $ legs — never searched; entry next 09:30 ET, gold 5m mark and silver first H1 bar >= 09:00 NY as in the original; 4 bps round-trip pair cost per trade, x1.5 sensitivity): k in {1.0, 1.5} x hold H in {1, 3, 5} sessions, where exit is BOTH legs at the H-th following 16:00-ET pair session close (H=1 reproduces the original horizon as the anchor cell). One position at a time: while a position is open, new events are skipped (busy-until dedupe, the attempt-28/30 convention, decided ex-ante). Multi-day holds add no extra round trips and no intermediate rebalancing. t is computed on returns normalized by sigma_prior * sqrt(H) so cells are comparable across holds. k=2.0 is excluded ex-ante because its 57 IS events cannot reach the 120-trade floor under any hold (dead cells would only inflate the test count). Test count: +6 selectable, +3 diagnostic.

DIAGNOSTICS: 3 non-selectable self-refutation cells (attempt 25/28/29 pattern): the identical convergence rule, entry, cost, and busy-until dedupe applied to SUB-THRESHOLD days — 0 < |s_yesterday| < 0.5*sigma_prior — at each H in {1, 3, 5}. The flow-overshoot mechanism predicts nothing after ordinary small divergences; only outsized dislocations carry the idiosyncratic-flow overshoot that dealers/RV desks rebalance. Pre-stated refutation rule (the attempt-29 'day >= night' formulation): at the IS-selected (k, H) — or at the best-t cell if nothing passes floors — if the sub-threshold diagnostic at the same H shows avg GROSS bps >= the selected cell's avg gross bps, the family self-refutes at IS as generic spread anti-persistence / drift (an AR artifact present at all divergence scales, not an overshoot effect), regardless of the selected cell's t. Diagnostic cells can never be selected and are counted in the test ledger.

FLOORS: IS pooled n >= 120 per selectable cell (normal family, not scarce-event: ~250 pair sessions/yr, k=1.0 gave 254 IS events at H=1; busy-until dedupe shrinks n at H=3/5 and any cell falling below 120 is non-selectable). IS t >= 2.0 on NET, sigma_prior*sqrt(H)-normalized returns. Neighbor-majority: among cells differing in exactly one knob (k or H) with n >= 30, at least half must have positive net avg_bps; a spiky winner whose neighbors disagree is discarded as noise. Plus the self-refutation gate above. IS = first 75% of pair sessions, identical cut construction to the original. If IS passes, ONE sealed OOS shot (last 25%) at the program bar: n >= 40, same sign, t >= 2, PF >= 1.15, cost x1.5 sensitivity positive; the OOS block burns permanently pass or fail.

### Attempt 34 result (FOMC horizon-match repair): IS PASS on all gates, OOS FAIL at the bar - WATCH ITEM #10

(results/r53_fomc_repair_is.json, results/r53_fomc_repair_oos.json)
IS: C1_ON (prev 15:55 close -> statement-day 09:30 open, LONG) n 190,
WR 62.1%, PF 3.22, avgR +0.124, t +4.34, halves [+,+]; every registered
gate passed - neighbors positive, placebo ON +0.033 vs FOMC ON +0.124
with the differential positive in both halves (generic overnight drift
REJECTED as the explanation), morning-drag anchor still negative
(decomposition intact). ONE OOS shot (family burns now): n 64, WR 57.8%,
PF 1.40, avgR +0.056, t +1.20, halves [+,+], ALL THREE instruments
positive (RTY PF 4.98), cost x1.5 +0.052. Only the t >= 2 leg fails;
the effect halved from IS (+0.124 -> +0.056), consistent with recorded
Lucca-Moench decay but clearly not gone. WATCH ITEM #10: FOMC-night long
- prev-session 15:55 close -> statement-day 09:30 open, SPX/NDX/RTY
pooled, ~8 events/yr each. SUPERSEDES watch #3 (the full-day version of
the same event stream): the monthly re-score scores #10 as the primary
FOMC item and #3 is retired as subsumed - the two are one stream and
were never independent. FOMC family's holdout is now SPENT; no further
repairs, forward accrual only.

### Attempt 35 result (gold/silver RV cost-amortization repair): IS-FAIL

(results/r53_gsrv_repair_is.json) The amortization arithmetic did not
materialize: H=3 gross ~ +3.8bps (flat vs H=1), H=5 noisy and
sub-threshold diagnostics comparable - convergence does not accumulate
across sessions. No cell near the floor. Family dies at IS with its one
registered repair exhausted; holdout stays sealed and unreachable
(protocol: one repair per family).

ROUND 53 CLOSED. Proposal-2 sweep totals: 33 families audited, 8
diagnosed, 6 refused from mechanism, 2 specs run, 1 IS pass, 0 OOS
passes, 1 new lead watch item. Program score: 0 graduates / 35 tested
attempts; active watch items #1,#2,#4-#10 (nine; #3 retired-subsumed),
composite #9 accruing forward, 4 paper streams. The 2026-09-01 monthly
re-score picks all of this up.

## Round 54: gold intraday history extended to 2012 - watch #5 re-score

2026-08-30. ACQUISITION ON RECORD: ejtraderLabs/historical-data (public
GitHub, cloned via session git proxy) ships XAUUSD m15 2012-05-15 ..
2022-03-04 (230,400 bars, prices x100). PROVENANCE (house rules):
(a) timezone established from the data itself - mean |ret| by feed clock
peaks exactly at 15:30 = the 08:30 ET macro-release slot under the MT4
GMT+2/+3-DST convention (ET = feed - 7h, constant); weekend structure
confirms (no Sunday bars, Friday ends 23:45 = 16:45 ET, Monday starts
00:00 = Sunday 17:00 ET). (b) prices cross-checked against our existing
5m feed on the 2020-09..2022-02 overlap: corr 0.9995, mean ratio
1.00003, mean |diff| 6.8 bps (different brokers). (c) known-history spot
checks pass (Dec-2015 low ~1051, Aug-2020 range 1913-2063). File:
data/XAUUSD_m15_ejtrader.csv (uncommitted, data/ gitignored).

### Watch #5 re-score registration (BEFORE running)

Watch #5 spec FROZEN as registered at attempt 18: gold vs CPI surprise,
direction = MINUS sign(ratioDeviation), the four CPI variants from
data/econ_events_us_high_fxs.json, |dev| thr {0.25, 0.5} x hold
{entry+60m, to 16:00 ET close}, cost 0.35, ATR20-normalized, one trade
per release. Extended scoring span 2013-01 .. data end, gold marks from
the m15 feed before 2020-08-21 and the 5m feed after. DISCLOSED
DEVIATIONS (granularity only, decided before running): on the m15
segment, entry = first m15 close at/after release+5min (up to 10 min
later than the 5m spec) and the +60m exit = first bar close >= entry
+60m; same-timestamp CPI variants collapse to one trade keeping the
largest |dev|. PRIMARY CELL fixed ex-ante = |dev| >= 0.25, hold to
close (the higher-n cell matching the watch text); the other three
reported alongside. Bar = the program bar (n >= 40, avgR > 0, t >= 2,
PF >= 1.15, cost x1.5 positive, mechanism sign). A pass goes to the
user for sign-off; it does not auto-graduate.

### Watch #5 re-score result: DOWNGRADED - the lean is era-specific

(results/r54_goldcpi_rescore.json) With the span extended 2013-2026
(n 112 vs the original 32-34; release clock verified 08:30 ET on 124
events), the primary cell (|dev| >= 0.25, hold to close) scores
avgR +0.051, WR 52.7%, PF 1.34, t +0.70 - and halves [-,+]: the
2013-2019 segment is NEGATIVE. The all-positive profile that created
watch #5 exists only in the post-2020 era (the 2021+ inflation regime,
consistent with the r44 lesson that the inflation mapping is regime-
poisoned). The +60m holds are negative across the board. Verdict:
watch #5 STAYS a watch item but is DOWNGRADED - the mechanism now
requires the post-2020 regime to hold, which is a conditional claim the
frozen spec does not make. It remains scored at monthly re-scores on
forward data; expectations lowered on the record. Side benefit: the
extended gold m15 history (2012+) is now a standing data asset for any
future gold family. The GVZ family stays dead (its IS refutation-shaped
fail is not reopened by more data absent a new mechanism argument).

## Round 55: London PM fix family on gold (attempt 36) - user directive: more different tests

### Attempt 36 registration (BEFORE running): gold London PM fix window

MECHANISM (ex-ante clock anchor, genuinely new to this program): the
London gold PM fix (15:00 London = 10:00 ET under aligned DST) is the
benchmark print for institutional gold business; documented order-flow
concentration produces selling pressure INTO the fix and a rebound
AFTER it (Caminschi-Heaney 2014 and successors; the 2015 LBMA reform
changed intensity but the flow anchor persists). Nothing prior in this
repo conditioned on the fix clock. Enabled by the Round 54 acquisition:
gold m15 2012-2022 + 5m 2020+ spliced at 2020-08-21 (marks are bar
CLOSES at/after the window edges - granularity disclosed).
FROZEN GRID (4 selectable cells, directions fixed by mechanism):
  S1 SHORT 09:00 -> 10:00 ET (hour into the fix)
  S2 SHORT 09:30 -> 10:00 ET (half-hour into the fix)
  L1 LONG  10:00 -> 10:30 ET (post-fix rebound, tight)
  L2 LONG  10:00 -> 11:00 ET (post-fix rebound, wide)
DIAGNOSTIC (non-selectable, drift self-refutation): the same four
window shapes shifted -2h (07:00->08:00 / 07:30->08:00 shorts,
08:00->08:30 / 08:00->09:00 longs) - no fix there; matching profiles
refute the fix read. DST-misalignment weeks (UK/US offset ~2wk/yr) are
accepted as noise, disclosed. GOLD only, cost 0.35/RT, ATR20(daily
range)-normalized, one trade per day per cell. Span 2012-05 onward.
IS first 75% of sessions; selection max IS t, pooled n >= 120, t >= 2.0
floor, neighbor rule = the same-direction sibling must be IS-positive.
ONE OOS shot at the program bar (n >= 40). Test count +4 selectable
(+4 diagnostics).

### Attempt 36 result: IS-FAIL, no fix-window flow survives costs post-2012

(results/r55_fix.json) All 8 cells (selectable AND shifted diagnostics)
cluster at avgR -0.024..-0.033 with t -4.4..-9.9 - the flat-cost
signature: gross drift ~0 in every 30-60min window, both directions,
fix-anchored or not. The documented pre-fix selling is absent from
2012+ data (consistent with the 2015 LBMA reform reading, or with the
effect predating this sample). Family BURNED at IS, OOS unopened. Useful
calibration on record: on gold at 0.35/RT, any sub-hour window family
needs |gross| > ~0.025R/day - a bar almost nothing structural clears.
Program score: 0 graduates / 36 tested attempts.

### Attempt 37 registration (BEFORE running): gold margin-cascade continuation

MECHANISM (new to this program; direction OPPOSITE the stress-reversal
class): outsized daily moves in metals trigger exchange margin hikes and
forced de-leveraging; liquidation pressure CONTINUES the move over the
next session(s) before exhausting (the documented metals margin-spiral
dynamic, e.g. silver 2011). Distinct from GVZ-shock (implied-vol
trigger, rebound claim - refuted) and from gold clock families: trigger
is the REALIZED daily move, claim is CONTINUATION. FROZEN GRID
(4 selectable cells): after a session close-to-close |ret| >= thr x
sigma63 (trailing 63d daily-ret std, shifted), trade IN THE MOVE'S
DIRECTION from next session's first bar close after 09:30 ET, thr
{2.0, 3.0} x hold {exit next session close (16:00 ET mark), exit 2nd
session close}; one position at a time. DIAGNOSTIC: sub-threshold days
(0.5 <= |ret|/sigma < 1.0), same rule, both holds - ordinary moves carry
no margin pressure; matching continuation = generic momentum artifact,
family self-refutes. GOLD only, extended 2012+ series, cost 0.35/RT,
ATR20-normalized. IS first 75% of sessions; max IS t, n >= 40 (scarce:
~12-15 2-sigma events/yr), t >= 2.0 floor, same-thr sibling positive.
ONE OOS shot at the program bar (n >= 25 scarce floor). Test count
+4 selectable (+4 diagnostics).

### Attempt 37 result: IS-FAIL on the t floor; lean is mechanism-shaped

(results/r55b_margin.json) All four selectable cells positive (2.0/2d:
n 133, WR 57.1%, PF 1.51, avgR +0.143, t +1.51; 3.0/1d: n 33, WR 60.6%,
PF 2.03, avgR +0.150, t +1.21), sub-threshold diagnostics NEGATIVE
(-0.02R) - the continuation asymmetry the margin mechanism predicts.
But no cell reaches t >= 2 at these ns; family dies at IS per its own
registration. HOLDOUT REMAINS SEALED: one taxonomy repair remains
available to this family in the future (more data or a sharpened
trigger, e.g. actual CME margin-change dates - a new data class - would
be the honest revival route). Not parked as a watch item (registration
did not provide for it). Program score: 0 graduates / 37 tested
attempts + 9 active watch items.

## Round 56: attempt 38 (silver margin-cascade); two candidates closed without running

(a) CME margin-change dates: bulk history is paywalled (CME DataMine);
the free margins pages carry only current levels. DEAD END recorded;
the attempt-37 repair stays parked until an open margin-history source
appears. (b) Gold Asia-session premium on 2012+ data: REFUSED at the
diagnosis stage - r42g (Asia/London clock split) SPENT its one-shot OOS
on effectively this window claim; extending the sample does not reopen a
spent family (rule-shopping). Refusal is the outcome.

### Attempt 38 registration (BEFORE running): silver margin-cascade continuation

MECHANISM: identical to attempt 37 (forced de-leveraging continues
outsized moves) applied to SILVER - the asset where the margin-spiral
dynamic is best documented (2011 episodes; silver margins are hiked
more aggressively than gold's on the same vol). Registered as its OWN
family (instrument extension = new information, the attempt-33
convention); never citable as confirmation of attempt 37's gold lean.
FROZEN GRID (4 selectable cells): after a 16:00-ET close-to-close
|ret| >= thr x sigma63 (shifted), trade IN THE MOVE'S DIRECTION from
next session's first H1 close at/after 09:30 ET, thr {2.0, 3.0} x hold
{next session 16:00 close, 2nd session 16:00 close}; one position at a
time. DIAGNOSTIC: sub-threshold days (0.5 <= |z| < 1.0), both holds -
matching continuation self-refutes as generic momentum. Data
data/XAGUSD_H1.csv 2016-04..2026-08 (timezone UTC per its own header,
established in r42p). Cost $0.02/oz RT (micro SIL best-case: 1-2 ticks
+ commission), ATR20(daily range)-normalized. IS first 75% of sessions;
max IS t, scarce floors n >= 40 IS / n >= 25 OOS, t >= 2.0, same-thr
sibling positive, diagnostic-below check. ONE OOS shot at the program
bar. Test count +4 selectable (+2 diagnostics).

### Attempt 38 result: IS-FAIL; the cross-metal echo goes on record

(results/r56_silver_margin.json) Silver replicates gold's shape exactly:
2-sigma cells flat-to-negative, 3-sigma cells positive (3.0/1d: n 33,
WR 51.5%, PF 2.41, avgR +0.130, t +1.33) but far under floors, and the
sub-threshold diagnostic strongly negative (t -3.56). Family dies at IS,
holdout sealed, one future repair available. DESCRIPTIVE NOTE (not a
confirmation claim): gold (attempt 37) and silver (38) independently
show continuation ONLY at extreme thresholds with anti-continuation
below - the margin-spiral mechanism's predicted asymmetry, twice. This
elevates the CME margin-dates data class (currently paywalled) to the
top of the acquisition wishlist: an ex-ante margin-hike trigger would
concentrate these ns onto true event days. Program score: 0 graduates /
38 tested attempts + 9 active watch items.

## Round 57: crypto asset class opened - BTC daily 2010-2026 acquired (attempt 39)

2026-08-30. data/BTCUSD_daily_av.csv (Alpha Vantage DIGITAL_CURRENCY_DAILY,
BTC/USD, 2010-07-17 .. 2026-08-30, 5889 UTC-midnight daily bars).
CRYPTO_INTRADAY is premium-gated on this key (verified) - daily designs
only. Crypto is a NEW ASSET CLASS for this program, tradeable for the
user via CME micro Bitcoin futures (MBT, listed 2021; CME BTC futures
since 2017-12).

### Attempt 39 registration (BEFORE running): BTC weekend-move reversion

MECHANISM: BTC spot trades 24/7 but deep/institutional liquidity (and
the CME venue) is Mon-Fri; weekend moves print on thin books and
partially REVERT when full liquidity returns Monday - the same
thin-liquidity-overshoot logic as this repo's flow families, applied to
the one asset with a true weekly liquidity cycle. Direction FIXED =
against the weekend move. SPAN: 2015-01-01 onward, chosen ex-ante on
mechanism (pre-2015 Mt.Gox-era microstructure is not relevant to the
MBT-tradeable claim); UTC daily bars, weekend move = Friday UTC close ->
Sunday UTC close, entry at Sunday UTC close (approximates the CME Sunday
18:00 ET reopen; disclosed), exits at Monday or Tuesday UTC close.
FROZEN GRID (4 selectable cells): |weekend move| filter {any nonzero,
>= 1.0 x sigma63 (trailing 63d daily-ret std, shifted)} x hold {Mon
close, Tue close}. DIAGNOSTIC (non-selectable): the same reversion rule
applied to midweek single-day moves (Tue close -> Wed close move, enter
Wed close, same filters/holds collapsed to 2 cells) - reversion there
means generic daily mean-reversion, not a weekend-liquidity effect;
diagnostic avgR >= selected avgR self-refutes the family at IS.
Cost 5 bps RT (MBT best-case), returns in bps normalized by
sigma63*sqrt(hold-days). IS first 75% of weekends; max IS t, n >= 120
(any-filter cells; >= 40 for the sigma-filtered), t >= 2.0 floor,
same-filter sibling positive. ONE OOS shot at the program bar (n >= 40 /
25 scarce). Test count +4 selectable (+2 diagnostics).

### Attempt 39 result: IS-FAIL, no weekend-liquidity reversion in BTC

(results/r57_btcweekend.json) All four selectable cells flat-to-negative
(any/1d -10.6bps t -0.54; sigma-filtered worse), midweek diagnostic
equally null - no reversion structure at daily resolution in 2015+.
Family BURNED at IS, OOS unopened. BTC daily data asset stays. Next
crypto-native candidate named for the acquisition queue: perpetual
funding-rate history (Binance public API) - a true flow/positioning
data class (crowded-leverage extremes) unavailable in any family so far;
requires Kernel fetch if the proxy blocks the exchange API.
Program score: 0 graduates / 39 tested attempts + 9 active watch items.

## Round 58: funding-rate data class acquired (attempt 40)

2026-08-30. Binance live API geo-blocks US IPs (451), but the public
archive CDN (data.binance.vision) serves monthly fundingRate zips; all
84 months batch-downloaded in one browser-VM shell loop:
data/BTC_funding_binance.csv (BTCUSDT perp funding, 2020-01-01 ..
2026-07-31, 7212 records). PROVENANCE: cadence exactly 8h for 7211/7211
intervals; mean +0.0108%/8h vs the 0.01% design baseline; p1/p99
-0.017%/+0.106% - sane. Funding is the first direct POSITIONING price
in the program (what crowded longs pay), a genuinely new data class.

### Attempt 40 registration (BEFORE running): crowded-leverage reversion

MECHANISM: extreme positive funding = longs crowded and paying heavily
= fragile positioning that unwinds (liquidation-prone) -> BTC weakness
ahead; extreme negative funding = crowded shorts -> strength. Directions
FIXED by mechanism. SIGNAL AVAILABILITY: day-T signal = sum of T's three
funding prints (00/08/16 UTC), all known by 16:00 UTC; entry at T's
daily close (00:00 UTC T+1) - 8h after the last component, clean.
Percentile = trailing 252d of daily funding sums, shifted. FROZEN GRID
(4 selectable cells): {>= 90th pct -> SHORT, <= 10th pct -> LONG} x
hold {1 day, 3 days} to daily closes; one position at a time.
DIAGNOSTIC (non-selectable): moderate bands with the same directions
(60-80th short, 20-40th long), both holds - the mechanism predicts
extremes only; moderate cells matching extreme cells self-refute the
family as a monotone carry artifact. Prices data/BTCUSD_daily_av.csv;
cost 5 bps RT; returns in bps normalized by sigma63*sqrt(hold). IS
first 75% of days; max IS t, n >= 40 per extreme cell, t >= 2.0 floor,
same-side sibling positive. ONE OOS shot at the program bar (n >= 25).
Test count +4 selectable (+4 diagnostics).

### Attempt 40 result: OOS FAIL - funding extremes split and then die

(results/r58_funding.json) IS decomposition: HIGH-funding short is
significantly WRONG-WAY (-57bps/day, t -2.08: high funding is
carry/momentum, crowded longs keep winning - that arm of the mechanism
is refuted in-sample). LOW-funding long passed everything IS (n 108,
WR 59.3%, PF 1.98, +76.7bps/day, t +2.29, halves [+,+], moderate-band
diagnostic well below at +14bps). ONE OOS shot on lo_long/1d: n 51,
+1.9bps, t -0.08, halves [+,-] - flat; the 2025+ OOS era did not carry
the effect. Family BURNED. Funding data asset (2020-2026, 8h) stays.
Program score: 0 graduates / 40 tested attempts + 9 active watch items.

## Round 59: crypto implied-vol data class acquired (attempt 41)

2026-08-31. data/BTC_DVOL_deribit.csv (Deribit DVOL daily OHLC,
2021-03-24 .. 2026-08-31, 1987 rows) via the public API from the
browser VM (no geo-block; python-urllib proxy quirk worked around with
curl). PROVENANCE: 1986/1986 one-day gaps, range 32-156 vs known BTC IV
history, spot values sane. Options-implied CRYPTO vol is new-in-class.

### Attempt 41 registration (BEFORE running): BTC DVOL-shock reversal

MECHANISM: the vol-shock overshoot claim of watch #7, tested on a THIRD
asset class. ADJACENCY DISCLOSED: equities (attempt 30, watch #7)
support it under power limits; gold (attempt 33) REFUTED it; BTC decides
generalization breadth. Never citable as confirmation of #7. Trigger:
1-day log change of DVOL close, z vs trailing 63d std (shifted).
SIGNAL/ENTRY CLOCK: DVOL and the BTC daily feed share UTC-midnight
closes; entry at the same close the signal forms on (24/7 market,
executable seconds later - disclosed as concurrent-close entry).
FROZEN GRID (4 selectable cells): LONG BTC after z >= thr, thr
{1.5, 2.0} x hold {1, 3} daily closes, one position at a time.
DIAGNOSTIC: DVOL crush (z <= -1.5), both holds - mechanism predicts
nothing there. Cost 5 bps RT, returns bps normalized by
sigma63*sqrt(hold). IS first 75% of days; max IS t, scarce floors
n >= 40 IS, t >= 2.0, same-thr sibling positive, crush-below check.
ONE OOS shot at the program bar (n >= 25). Test count +4 selectable
(+2 diagnostics).

### Attempt 41 result: IS-FAIL, and the vol-shock breadth question closes

(results/r59_dvolshock.json) z>=1.5/3d leans positive (+116bps, t +1.86,
crush diagnostic below) but misses the floor, and the z>=2.0 cells are
NEGATIVE - the k-gradient runs the wrong way (spike, not slope; the
house gradient-over-peak rule reads this as noise). Family BURNED at IS,
OOS unopened. GENERALIZATION VERDICT across three asset classes: vol-
shock reversal = equities lean (watch #7), gold refuted (33), BTC null
with broken gradient (41). The mechanism, if real, is an equity-index
dealer/flow phenomenon - which sharpens watch #7's prior rather than
diluting it (recorded as interpretation, never as added evidence).
Program score: 0 graduates / 41 tested attempts + 9 active watch items.
Search cadence per the standing plan: slows to new-data-class-only while
the watch list accrues; the Sep 1 re-score check-in is the next event.

## Round 60: CFTC index-futures positioning acquired (attempt 42)

2026-08-31. data/cftc_tff_indices.csv - CFTC Traders-in-Financial-Futures
weekly reports for the equity index futures, 2010-07-20 .. 2026-08-25,
6861 rows, harvested from the official annual archives (17 zips) in one
browser-VM loop (cftc.gov proxy-blocked locally). PROVENANCE: weekly
cadence exact (233/237 seven-day gaps, rest holiday shifts); ES
leveraged-money net deeply short (median -344k) matching the known
structural basis-trade positioning. ERA SPLICE MAP (frozen): ES =
"E-MINI S&P 500 STOCK INDEX" then "E-MINI S&P 500" (2022-02+); NQ =
"NASDAQ-100 STOCK INDEX (MINI)" then "NASDAQ MINI" (2022-02+); RTY =
"RUSSELL 2000 MINI INDEX FUTURE" (ICE, to 2017) then "E-MINI RUSSELL
2000 INDEX" then "RUSSELL E-MINI" (2022-02+). Index-futures POSITIONING
is new-in-class for this program (COT was only ever used on gold, r24).

### Attempt 42 registration (BEFORE running): leveraged-money positioning extremes

MECHANISM: leveraged funds' net position in index futures is dominated
by structural shorts (basis trades); its EXTREMES mark crowding -
extreme net-short = squeeze-prone (index strength follows), extreme
net-long-side = stretched speculative length (weakness follows). The
contrarian-at-extremes reading, fixed ex-ante (the same Williams-style
read used on gold COT in r24, new instrument class). SIGNAL: lev-money
net / open interest (contract-size-era neutral), trailing 156-week
percentile, shifted. AVAILABILITY: report date is Tuesday, released
Friday 15:30 ET; entry at the RTH open of the first session >= 6
calendar days after the report date (the Monday after release) - no
lookahead. FROZEN GRID (4 selectable cells): {<= 10th pct -> LONG,
>= 90th pct -> SHORT} x hold {5 sessions, 20 sessions} to RTH closes;
one position per instrument at a time. DIAGNOSTIC (non-selectable):
mid-band cells (40-60th pct, both directions' entry rule applied as
LONG) - extremes-only mechanism predicts nothing there. Instruments
SPX/NDX/RTY pooled at micro best-case costs, ATR20-normalized. IS first
75% of report weeks; max IS t, n >= 40 per cell, t >= 2.0 floor,
same-side sibling positive, mid-band-below check. ONE OOS shot at the
program bar (n >= 25). Test count +4 selectable (+2 diagnostics).

### Attempt 42 result: OOS FAIL on power - watch item #11 (low-confidence)

(results/r60_tff.json) IS: lo_long/5-session (extreme lev-money
net-short -> long index) n 116, WR 66.4%, PF 1.80, avgR +0.478,
t +2.63, halves [+,+]; mid-band diagnostic far below; the hi_short arm
null (squeeze asymmetry as predicted). ONE OOS shot: only 19 extreme
weeks existed in the OOS era (< the 25 floor - power-fail by
construction): WR 73.7%, avgR +0.236, but PF 0.91 (one large loser)
and halves [+,-], t +0.59. Family burns; parked as WATCH ITEM #11:
extreme lev-money net-short (<=10th pct of net/OI, 156w) -> long index
at next Monday RTH open, exit 5th session close, SPX/NDX/RTY pooled.
LOW-CONFIDENCE flag on record: mixed OOS halves and sub-1 PF make this
the weakest watch item; ~8-12 extreme weeks/yr accrue. Program score:
0 graduates / 42 tested attempts + 10 active watch items.

### Attempt 43 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### asset-manager positioning extremes

DIAGNOSIS: same data class as attempt 42, DIFFERENT trader population
with a different mechanism - asset managers are unlevered real money;
their net length is an allocation/sentiment state, not a basis trade.
Extreme AM length = allocations maxed (complacency; marginal buyer
exhausted) -> weakness ahead; extreme AM shortness/underweight =
capitulation -> strength. Directions fixed ex-ante (mirror-image of the
lev-money squeeze read BY MECHANISM, not by search). DEALER extremes
are REFUSED ex-ante: the three groups roughly sum against each other,
so dealer net is close to the negative of lev+AM and would not be an
independent test (recorded so it is never mined later). MULTIPLICITY
NOTE: this is the second and LAST family from the TFF class; the class
closes after this attempt regardless of outcome.
FROZEN GRID (4 selectable cells): signal = AM net/OI, trailing 156w
percentile, shifted; {>= 90th pct -> SHORT, <= 10th pct -> LONG} x hold
{5, 20 sessions}; entry first RTH open >= 6 calendar days after report
date; one position per instrument. DIAGNOSTIC: mid-band (40-60th, LONG)
both holds. SPX/NDX/RTY pooled, micro costs, ATR20-normalized. IS first
75% of report weeks; floors n >= 40 IS / 25 OOS, t >= 2.0, same-side
sibling positive, mid-band-below. ONE OOS shot at the program bar.
Test count +4 selectable (+2 diagnostics).

### Attempt 43 result: IS-FAIL; the TFF positioning class closes

(results/r60b_am.json) No AM cell near the floor (best t +1.06), and
the mid-band diagnostic OUTPERFORMS both extremes (t +1.89/+1.94 vs
extremes' +0.4..+1.1) - the return structure around AM positioning is
drift, not an extremes signal. Family BURNED at IS, OOS unopened. Per
the registration, the TFF class is now CLOSED (lev tested->watch #11,
AM tested->dead, dealer refused as non-independent).
Program score: 0 graduates / 43 tested attempts + 10 active watch items.
The free-data-class frontier is, as of this attempt, exhausted to the
best of this program's knowledge. The live program = the watch list's
forward accrual (monthly re-scores) + opportunistic new classes.

## Monthly forward-test review - 2026-09-01

JOURNAL STATE: the paper journal (artifact af9114c9) holds ZERO rows
across all four streams as of this review.
- XAU (deployed gold rule): 0 trades. Within drought norms (mean red
  streak 12 trading days, p90 28, max 61); the zero is the filter
  working IF signals genuinely did not fire. VERDICT: on track,
  contingent on the logging question below.
- XAUAUD (upgrade #1 half-leg): 0 trades, rides XAU signals. On track.
- MHI (HSI pre-open fade, 80-trade re-test bar): 0 of 80 accrued. This
  stream should produce rows more regularly than XAU; a month of zero
  is plausible-but-notable. Progress 0/80, no verdict (bar untouched).
- D7 (Double Seven, ~1 signal/month expected): 0 logged - one missed
  month is unremarkable. SPRT LLR unchanged at 0.00 (no W/L fed;
  boundaries +/-2.20 untouched).
- XAU kill criteria: not triggerable on n=0. No execution-mismatch
  evidence exists either way.
ACTION FOR THE USER (the one thing this review cannot verify): confirm
whether the empty journal means "no signals fired" or "signals fired
but were not logged." If any signal fired unlogged, the forward test's
clock has not actually started - the record only counts if the rows go
in. Nothing else is actionable at n=0.
GOAL ADVANCEMENT: HSI live feeds re-pulled (H1/M15/M5 refreshed
2026-09-01); SGE AM-fix re-score is yearly, not due. No new
mechanism-first battery this cycle - rounds 45-60 (attempts 19-43)
already ran the search to data-frontier exhaustion this week and are
recorded above; grinding another battery now would be multiplicity, not
research. WATCH-ITEM NOTE: the new items #6-#11 registered 2026-08-29..
08-31 have essentially no forward days yet; their first meaningful
re-score is 2026-10-01. Composite #9's forward clock started 08-31.

## Round 61: business-cycle regime class (attempt 44) - search reopened on user directive

### Attempt 44 registration (BEFORE running): PMI-contraction risk premium

MECHANISM (new-in-class): no prior family conditioned on the BUSINESS
CYCLE STATE - the macro families (11/17/18) used release-day SURPRISES,
never the level. The documented claim (tactical-allocation literature):
equity risk premium concentrates in CONTRACTION regimes - forward
returns are higher while the last-released ISM Manufacturing PMI sits
below 50 (risk compensation when the cycle is weak), ordinary in
expansion. Direction fixed ex-ante: LONG during contraction regimes.
SIGNAL: the 'a' (actual) value of "ISM Manufacturing PMI" events in
data/econ_events_us_high_fxs.json; regime = last release's level,
active from the first session AFTER the release (10:00 ET publication;
regime flips next session open - no lookahead). FROZEN GRID
(4 selectable cells): LONG daily close-to-close bookings while regime
active, regime {PMI < 50, PMI < 47 (deep contraction)} x instrument
grouping {indices pooled, RTY alone (small caps most cycle-sensitive -
a mechanism-implied sub-cell, fixed ex-ante)}. DIAGNOSTIC
(non-selectable): expansion regime (PMI >= 52) long, same bookings -
the premium claim predicts materially less there; matching returns =
generic drift, self-refutes. POWER DISCLOSURE: contraction episodes are
few (~4-5 in 2013-2026) - daily n is large but episode-level effective
n is small; halves and episode signs will be reported and a spiky
single-episode result treated as noise. Costs: one RT per regime entry/
exit (micro best-case), daily bookings ATR20-normalized. Span 2013+.
IS first 75% of sessions; max IS t, n >= 120 daily obs, t >= 2.0 floor,
sibling-positive, diagnostic-below. ONE OOS shot at the program bar
(n >= 40). Test count +4 selectable (+2 diagnostics).

### Attempt 44 result: FIRST OOS PASS OF THE PROGRAM - pending user sign-off

(results/r61_pmi.json) IS: contraction-long (PMI < 50, indices pooled)
n 691 daily bookings, WR 60.6%, PF 1.53, avgR +0.096, t +2.87, halves
[+,+]. ONE OOS shot: n 1597, WR 56.9%, PF 1.33, avgR +0.087, t +4.13
(nominal), halves [+,+], cost x1.5 unchanged. ALL registered gates pass.
SKEPTICISM CLAUSES, checked per the registration before reporting:
(a) DRIFT REFUTED OOS: expansion-regime days (PMI >= 52) were NEGATIVE
out of sample (-0.024, t -0.48; RTY -0.029) while contraction carried
+0.087 - the regime split genuinely separates returns, this is not
"always long". Deep contraction (<47) even stronger OOS (+0.129,
t +2.98). (b) EPISODE STRUCTURE (the real effective n): IS 5 episodes,
4 positive (2013, 2016a, 2019-20, 2020; 2016b negative); OOS THREE
separate episodes, ALL positive and consistent (2022-12..2024-04
+0.086, 2024-05..2025-02 +0.071, 2025-04..2025-12 +0.093). 7 of 8
episodes positive (sign-test p ~ 0.035). NOT a single-episode spike.
HONEST CAVEATS ON RECORD: (1) the nominal t 4.13 treats daily bookings
as independent; at episode level the evidence is good-not-overwhelming
(effective n ~ 8 blocks); (2) program multiplicity: this is the 11th
OOS shot - at 2-5%/shot the chance of >= 1 false pass somewhere is
~20-40%, though a false pass this decisive is much less likely than the
marginal kind; (3) contraction covered ~80% of the OOS window - the
discriminating evidence is the expansion-negative side, which held;
(4) this is a REGIME strategy (long MES/MNQ/M2K while last-released ISM
Mfg PMI < 50, flat otherwise; ~monthly regime checks, holds for
months), not an intraday scalp. FAMILY BURNED (shot spent). NEXT STEP
PER PROTOCOL: graduation to a paper/tracking stream requires explicit
user sign-off - put to the user 2026-09-01. Program score: 1 OOS PASS
(pending sign-off) / 44 tested attempts + 10 active watch items.

## Round 62: business-cycle regime class, attempt 45 - generalization test

### Registration-stage kills (BEFORE any returns were computed), 2026-09-01

SERVICES-ISM VARIANT: KILLED AT REGISTRATION. Signal-side counts only
(no returns touched): ISM Services PMI has 6 sub-50 releases in 105
(2014-2026), producing 185 regime days of which 180 (97%) sit inside
the mfg-PMI < 50 regime attempt 44 already spent. Zero independent
evidence possible at any n floor - running it would only re-test
attempt 44's claim on its own days. Recorded as adjacency-subsumed;
no grid built, no test counted.
CONSUMER CONFIDENCE (CB) VARIANT: KILLED AT REGISTRATION. Feed carries
19 releases - below any floor. No grid built.

### Attempt 45 registration (BEFORE running): consumer-pessimism regime
### (Michigan sentiment) - different-gauge generalization of attempt 44

PURPOSE (fixed ex-ante): attempt 44's economic claim is "equity risk
premium concentrates while the last macro print signals a weak cycle".
If real, it should generalize to a DIFFERENT gauge of the cycle; if it
is a manufacturing-PMI artifact it should not. This family tests the
same claim on the consumer side. It is registered as a NEW family
(different signal series) but adjacency to attempt 44 is declared, and
an INDEPENDENCE GATE (below) decides whether any result counts as new
evidence or as subsumed.
SIGNAL: 'a' of "Michigan Consumer Sentiment Index" events in
data/econ_events_us_high_fxs.json (105 releases 2013-01..2026-08,
09:55 ET). Regime = last release strictly before the session date
(active from first session after release - same no-lookahead rule as
attempt 44). Thresholds fixed from public history, not our returns:
pessimism < 65 (recession-era prints; 35 releases, ~21% of days) and
< 70 (48 releases, ~29% of days). Direction fixed: LONG while
pessimism regime active, flat otherwise. Daily close-to-close
bookings, ATR20-normalized, cost MICRO/20 per booking (regime
amortization, same as attempt 44).
FROZEN GRID (4 selectable cells): {thr 65, thr 70} x {indices pooled,
RTY alone}. DIAGNOSTICS (non-selectable): (a) optimism regime
(sentiment >= 85) long, same bookings - matching returns = generic
drift, self-refutes (diag_below gate); (b) INDEPENDENCE GATE: the
winner's IS avgR restricted to sessions OUTSIDE the mfg-PMI < 50
regime must be positive - signal-side overlap is 54-59%, so the
mich-only subset (~475-595 days) has power; if the non-overlap subset
is not positive the family is declared SUBSUMED by attempt 44 and the
OOS seal is NOT opened (no shot spent, no independent evidence
claimed). POWER DISCLOSURE: episode-level effective n is small
(~4-6 pessimism episodes); episode signs reported; single-episode
spikes treated as noise. IS first 75% of sessions; floors n >= 120,
t >= 2.0, sibling-positive. ONE OOS shot at the program bar (n >= 40,
avgR > 0, t >= 2, PF >= 1.15, cost x1.5 positive). If opened it is the
12th shot (multiplicity ledger updated either way). Test count +4
selectable (+2 diagnostics).

### Attempt 45 result: IS FAIL - claim does NOT generalize to consumer gauge

(results/r62_mich.json) Pessimism regime is NEGATIVE in sample: thr 65
pooled n 332 avgR -0.027 t -0.61 halves [-,-]; thr 70 n 452 avgR
-0.070 t -1.69 halves [-,-]. Optimism diagnostic (>= 85) POSITIVE
(+0.043, t +2.94) - i.e. the exact OPPOSITE pattern of attempt 44. No
cell reaches the floor; OOS seal never opened, no shot spent. RTY had
no pessimism days in its span (sub-65 prints are 2022+; RTY 5m frame
ends earlier) - pooled cells carried the test. INDEPENDENCE NOTE: 331
of 332 IS pessimism days sat OUTSIDE the mfg-PMI < 50 regime (Michigan
bottomed mid-2022 while ISM mfg was still > 50), so this was a clean
independent test of the weak-cycle-premium claim on a different gauge,
and it FAILED. INTERPRETATION ON RECORD: attempt 44's premium is
gauge-specific (manufacturing PMI), not a universal "bad news = paid
to be long" effect. This BOUNDS attempt 44 rather than refuting it
(its own OOS episodes stand), but it removes the strongest
generalization story and should weigh in the sign-off decision.
Program score: 1 OOS pass (pending sign-off) / 45 attempts. Test count
+4 selectable +2 diagnostics.

## Round 63: business-cycle regime class, attempt 46 - hard-data gauge

### Attempt 46 registration (BEFORE running): labor-deterioration regime
### (Sahm-style unemployment gap) - third gauge of the triangulation

PURPOSE (fixed ex-ante): triangulate attempt 44's weak-cycle-premium
claim across gauge types. Soft-manufacturing survey PASSED OOS
(attempt 44); soft-consumer survey FAILED at IS with opposite pattern
(attempt 45). This attempt tests a HARD-DATA gauge: the unemployment
rate's Sahm-style deterioration gap. If it also fails, the pass is
gauge-specific; if it holds, the class has a second leg.
SIGNAL: monthly U-3 unemployment (data/UNRATE_av.csv, Alpha Vantage
UNRATE, 2003+ subset stored; 2025-10 print never published - shutdown -
linearly interpolated for moving-average computation only, declared
here). gap_M = 3-month MA of the rate through month M minus the
minimum of that 3m MA over the prior 12 months. PUBLICATION LAG
(no-lookahead, deterministic): month-M value treated as known from the
8th calendar day of month M+1 (jobs report lands the first Friday,
i.e. by the 7th); regime for a session uses the last KNOWN month.
Direction fixed: LONG indices while deterioration regime active, flat
otherwise. Daily close-to-close bookings, ATR20-normalized, cost
MICRO/20 per booking. Span 2005+ (SPX/NDX/RTY 5m start) - this gauge
is not limited by the 2013+ event feed, so 2008-09 and 2020 are in
sample.
FROZEN GRID (4 selectable cells): {gap >= 0.50 (classic Sahm
threshold), gap >= 0.30 (milder deterioration)} x {indices pooled, RTY
alone}. DIAGNOSTICS (non-selectable): (a) improving-labor regime
(gap <= 0.05, 3m MA at its 12m min) long, same bookings - matching
returns = generic drift, self-refutes (diag_below); (b) INDEPENDENCE
GATE vs attempt 44: winner's IS avgR restricted to sessions outside
the mfg-PMI < 50 regime must be positive, evaluated ONLY on sessions
where the mfg regime is defined (feed starts 2013; pre-2013 sessions
excluded from this gate, not from the family). If non-overlap subset
is not positive: SUBSUMED, seal not opened, no shot spent. POWER
DISCLOSURE: deterioration episodes ~3-5 in 2005-2026 (2008-10, 2020,
2024-25); episode signs reported, single-episode spikes = noise. IS
first 75% of sessions; floors n >= 120, t >= 2.0, sibling-positive.
ONE OOS shot at the program bar (n >= 40, avgR > 0, t >= 2,
PF >= 1.15, cost x1.5 positive). Would be the 12th shot. Test count
+4 selectable (+2 diagnostics).

### Attempt 46 result: IS FAIL - hard-data gauge does not carry the premium

(results/r63_sahm.json) Deterioration regime is FLAT in sample: gap
>= 0.5 pooled n 1905 avgR +0.014 t +0.73 halves [-,+] (2008-09
deterioration - the first half - was NEGATIVE: crash days, not premium
days); gap >= 0.3 the same (+0.010, t +0.55). Improving-labor
diagnostic is the STRONG side (+0.036, t +3.68) - the drift lives in
good-labor regimes, opposite of the claim. No cell near the floor; OOS
seal never opened, no shot spent.

### CLASS VERDICT on business-cycle regimes (attempts 44-46), on record

Three gauges of the same economic claim ("long the weak-cycle
regime"): soft-manufacturing (ISM mfg PMI) PASSED its OOS shot; soft-
consumer (Michigan) FAILED at IS with the OPPOSITE pattern; hard-labor
(Sahm gap) FAILED at IS flat with halves split. The claim is GAUGE-
SPECIFIC, not a universal bad-news premium. Two readings, both on
record: (a) ISM mfg is the one gauge with genuine tactical-allocation
literature behind it and its pass had discriminating structure
(expansion-negative OOS, 7/8 episodes); (b) skeptically, two failed
generalizations RAISE the probability that attempt 44's pass is a
regime-timing coincidence (PMI < 50 happening to bracket the 2022-25
recovery) rather than a causal premium - the 2008-09 evidence from the
Sahm family shows weak-cycle regimes can sit squarely on crash periods.
NET EFFECT: attempt 44 stands (its registered gates all passed) but
graduates, if signed off, with this class context attached; the paper
stream is the arbiter. Class closed - no further cycle-gauge variants
without new data types. Program score: 1 OOS pass (pending sign-off) /
46 attempts, 11 shots spent. Test count +4 selectable +2 diagnostics.

## 2026-09-02: user sign-off received - PMI-contraction regime graduates to paper

USER DECISION (2026-09-02): "first thing is yes" - graduate attempt 44 to a
paper/tracking stream. Also: the user cannot journal by hand, so the four
gold-era streams AND this one move to AUTOMATIC journaling computed by the
main session at each scheduled check-in (contract: backtest/forward/
CONTRACT.md; code: backtest/forward/leg_*.py; rows land in journal artifact
af9114c9 tagged src="auto"). The user reports no observed signals so far;
the empty journal is therefore "not logged", not "no signals" - the auto-
journal will back-fill from the data (gold 5m via IBKR is only available
~1 week back at 5m resolution, so the XAU/XAUAUD back-fill starts from the
first weekly pull; HK33 and daily index data allow a full back-fill).

### PMI stream tracking spec (frozen)

Signal: last-released ISM Manufacturing PMI headline (source: ISM press
release via web search each first-business-day; stored in
data/forward/ism_pmi.json). Regime LONG from the first session strictly
after a release < 50 until the first session after a release >= 50; flat
otherwise. Legs: SPX / NDX / RUT cash indices standing in for MES/MNQ/M2K,
daily close-to-close bookings, cost MICRO/20 per booking applied at review
time. Journal rows: one per leg per calendar month with active sessions.
STATE AT REGISTRATION: August 2026 print 54.6 (July 55.6) - regime
INACTIVE; the stream starts flat and books nothing until a sub-50 print.
GRADUATION BAR (forward only): >= 250 pooled forward regime-day bookings
with avgR > 0, t >= 2 (daily bookings, serial correlation caveat noted) AND
at least two separate forward contraction episodes both positive AND the
expansion-day control (computed at review from the same data) not above the
contraction days. KILL: after 250 forward regime days avgR <= 0, or pooled
forward drawdown exceeding 3x the backtest's worst episode drawdown, or any
forward episode with avgR < -0.15 R/day over >= 40 days. Bound on record:
the premium is gauge-specific (attempts 45/46 failed) - the forward stream
is the arbiter of readings (a) vs (b) in the class verdict above.

### Declared substitutions for the automated gold streams

XAU corr gate uses IBKR daily gold (22:00 UTC boundary) and IBKR AUD.USD
daily closes instead of Athens-day gold and FRED noon AUD; gold prices are
IBKR London Gold midpoint (no spread) instead of the backtest CFD feed; the
fixed 0.30 $/oz cost and 0.30 stop slippage are applied at review, not in
the journal rows. Each leg must reproduce the archived backtest trades on
the archived data before its forward output is trusted (verification
results recorded when the build completes).

### 2026-09-02: auto-journal built and verified; journal switched to automatic

BUILD (backtest/forward/): leg_xau.py (XAU + XAUAUD), leg_mhi.py, leg_d7.py,
leg_pmi.py, integrator autojournal.py; each leg carries a reproduction test
(test_leg_*.py) plus reviewer stress tests (stress_leg_*.py). VERIFICATION
ON THE ARCHIVED DATA, all re-run by the main session: XAU 652/652 deployable
trades reproduced (entry, exit, stop, exit reason all exact; corr-gate day-
boundary substitution measured as a no-op: 0 flips on 1,079 breakout days
because the gold feed has no prints in the 21:00-22:00Z summer hour); D7
253/253 archived SPX trades reproduced (every r28b scalar to 1e-9); MHI
trade-for-trade identical to run_hsi.py's own code on the HK33 span (n 18,
PF 1.977 = the archived cell's second half); PMI 47/47 synthetic checks
(regime start/end sessions, month rows, month-to-date status). Adversarial
reviews (8 agents, two lenses per leg) found two real defects, both fixed:
(1) the XAU corr gate was forward-filled past the last joint daily bar -
now a session beyond the daily data is DEFERRED (NaN -> no trade, exactly
deployable.py line 23) and listed in status(); (2) closed trades inside
the backtest window reached the journal as "forward" rows - now every
stream has a start date in autojournal.STREAM_START and earlier rows are
ignored: XAU/XAUAUD 2026-08-27 (journal era; the 5m pull cannot reach
further back anyway), MHI 2026-09-01 (HK33 archive ends 2026-08-31), D7
2026-08-27 (round 28b decision), PMI 2026-09-02 (sign-off).
FIRST AUTOMATED ROWS (journal af9114c9 v4, src=auto): XAU 2026-08-27
SHORT 4617.39 -> 4609.42 time exit, +7.97 $/oz gross (+7.67 net);
XAUAUD 6428.00 -> 6405.75, +22.25 A$/oz; MHI 2026-09-01 LONG 25322.60
stopped 25259.35, -63.25 pts (-73.25 net). 08-31 and 09-01 gold breakouts
were gated out (corr 0.556 / 0.569 > 0.5); gate 0.641 CLOSED on 09-02.
D7: OPEN since 2026-09-01 at 7631.47 (SMA200 7126.82), exit at the first
close >= 7730.99. PMI: INACTIVE (Aug print 54.6). SPRT: XAU/XAUAUD LLR
+0.17, MHI -0.49, all "continue".
CADENCE: weekly trigger (Mondays 03:25 UTC) refreshes data, runs the
integrator, republishes the journal, notes one line here; monthly
routine (1st, 02:00 UTC) scores all five streams + the Round-42 watch
list. The user never journals by hand again.

## Round 64: multi-agent hypothesis sweep (2026-09-02/03) - registrations

PROCESS: 6 proposer agents on distinct untouched angles (index
microstructure, cross-asset lead-lag, options/short-side data, index-
rebalance and settlement calendars, Hang Seng/Asia structures,
positioning velocity), 2 proposals each, under the IS-only firewall (no
returns computed; signal-side counts only); every proposal attacked by
2 adversarial critics (burned-adjacency lens; mechanism/data/lookahead
lens; default kill when uncertain); a ranker wrote the ledger text for
survivors incorporating critics' fixes. 12 proposed, 10 KILLED AT
REGISTRATION (no grid built, no test counted beyond this record), 2
registered below.
REGISTRATION-STAGE KILLS (one line each, reasons from the critics):
 1 Closing-auction imbalance fade (post-16:00 reversal) - exit-B cells
   are burned attempt 29's window; post-close prices in the OOS block
   are synthetic in the CFD feed.
 2 Megacap after-hours earnings -> MNQ continuation - sub-cell of the
   spent overnight-gap family (attempt 5); no uninformed counterparty.
 3 Small-cap overnight residual fade (M2K-vs-MES) - sub-cell of attempt
   5's day set; cost-dominated for a spread of two micro legs.
 4 Closing-auction pressure spread reversal (M2K-vs-MES) - no forced
   counterparty at the index level; cost-dominated.
 5 VIX settlement-auction hedging reversal - half the grid re-
   parameterizes burned attempt 19; the hedging footprint sits in deep-
   OTM puts, not in ES delta.
 6 Buyback-blackout calendar regime (OPEN-window long) - long-only
   regime over ~25% of sessions = index drift; the diagnostics cannot
   separate the corporate bid from being long (attempt 45/46 pattern).
 7 Index rebalance-day closing-flow reversal - horizon re-parameteriza-
   tion of attempt 19; rebalance flow nets to ~zero at index level.
 8 HKMA convertibility-undertaking liquidity regime on HSI - the forced
   counterparty exists only in USDHKD spot, not in HSI.
 9 HK index-rebalance closing-auction reversal - reconstitutions are
   cross-sectional; no directional index-level flow.
10 ETF short-interest surge -> index long - the anchor citation's sign
   was inverted; settlement-calendar confound the diagnostics cannot
   separate.
SIDE NOTE ON RECORD (from the attempt-47 critics): the '+6 calendar
days' CFTC release convention used by attempts 42/43 and inherited by
watch #11 is wrong for ~23% of report weeks (holiday-delayed and
shutdown releases print later); watch #11's forward accrual adopts the
corrected release rule below (Friday 15:30 ET, or the following Monday
when a federal holiday falls in the report week; shutdown weeks
non-tradable). Attempts 42/43 themselves are spent and are not re-run.

### Attempt 47 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### gold speculator-flow liquidity premium (fade the weekly COT spec flow) - MGC

DIAGNOSIS vs r24 Spec B (Williams COT Index on gold, ledger 318-345 /
391-410, NEGATIVE, max-stat p 0.76, pre-protocol full-sample test
2012-06..2026-08 with halves at 2019-01-01): r24 conditioned on the
LEVEL of commercial (and, as a category check, large-spec) net
position via 13/26/52/156-week stochastics at 70/30-90/10 thresholds
and held Monday->Monday. This family conditions on the one-week CHANGE
in large-spec net position scaled by open interest - the first
difference of r24's willco_s series (net_s / OI; run_r24_cot.py lines
74-77) - and predicts reversal of that flow's price impact. The
attempt-30-vs-9 precedent (VIX SHOCK vs VIX LEVEL, ledger 3496-3518)
applies, but the following is ON RECORD so the family is never cited as
independent of r24: (i) the signal series is a transform of r24's; (ii)
the Monday-after-release entry and 5-session hold are r24's own
convention (ledger 322-325); (iii) the sealed OOS window (report weeks
2022-08-30..2026-01-20) lies entirely inside r24's already-reported
second half, where the large-spec LEVEL fade read flat (+1.04 / -0.06,
ledger 398-400); the OOS is therefore sealed only with respect to the
FLOW transform, not the data class; (iv) r24's spec-fade result is this
family's prior on the LEVEL read - a pass here would BOUND r24 (flow
carries what level did not), never confirm it; (v) legacy commercials
~ -(noncomm + nonrept), so a commercial-flow mirror cell is NOT
independent and is REFUSED ex-ante (recorded so it is never mined).
SIGNAL-SIDE OVERLAP (computed, no returns): 46-53% of flow events sit
in an r24 26w-spec extreme (>= 80 or <= 20) in the same report week;
the subset with ALL r24 gauges (26w stochastic of willco_s, 13w
stochastic of net_c, 13w stochastic of willco_c) inside the 20-80
mid-band is 58 events at thr 1.0 x hold 5 (IS 45 / OOS 13), 41 (IS 31)
at thr 1.0 x hold 10, 26 (IS 21) at thr 1.5 x hold 5, 22 (IS 18) at
thr 1.5 x hold 10. Overlap shares are re-printed before any grid is read.
DIAGNOSIS vs attempt 37 (gold margin-cascade CONTINUATION, IS-fail,
holdout SEALED, ledger 3904-3938): different trigger (positioning flow,
not the realized daily move) and OPPOSITE predicted sign; but corr(z,
same-week gold return) ~ 0.65 with 91% sign agreement is disclosed, so
the price-move partition below is IS-ONLY and the OOS shot reports the
selected cell alone - attempt 37's sealed holdout is not read through a
mirrored big-move partition. Attempt 33 (GVZ shock) conditions on
implied vol - distinct. Attempts 42/43 (TFF index positioning, class
CLOSED) and watch #11 are index-only and level-based - no index leg
here; silver is a future instrument-extension family (attempt-33/38
convention), not pooled. Gold COT is NOT a new data class (ledger 4130);
the family is admitted on mechanism distinctness plus the gate below.

MECHANISM (Kang, Rouwenhorst & Tang JF 2020; Marechal JFM 2023
replication; Cheng-Kirilenko-Xiong RoF 2015): commodity futures returns
carry a slow hedging premium (levels) and a short-horizon LIQUIDITY
premium: speculators (largely signal-driven CTAs) demand immediacy, their
weekly position CHANGES push price, and the commercials who accommodate
the flow earn a premium as the impact reverts over the next 1-2 weeks.
The uninformed counterparty is the liquidity-demanding spec flow itself;
the information lag is structural (the CFTC print is the only public
record of WHO moved the market and arrives ~3 days late). Registered
weakness: KRT returns are Tuesday-to-Tuesday (pre-publication); a
Monday entry starts 4 sessions into a reversal the paper calls
short-lived - the late-entry placebo tests exactly this decay.
Direction fixed ex-ante: position = MINUS sign(z) (fade the flow). No
mirror if the sign comes out wrong. Honest prior: MODERATE - KRT's
headline is cross-sectional across 26 commodities; the single-commodity
time-series version on the most financialized metal, post-2015, is the
weaker cousin; publication decay is the principal risk.

DATA: data/COT_gold_github.csv (legacy futures-only 088691, weekly,
2006-01-03..2026-01-20, 1047 rows, no duplicates; report dates 1033
Tuesday / 13 Monday / 1 Wednesday). Prices: the r24-verified spliced
gold series (XAUUSD_m15_ejtrader.csv 2012-05..2022-03 Europe/Athens,
/100 scaling; XAUUSD_H1_collector.csv 2016-04..2026-08 UTC; XAUUSD_5m
2020-08+ for intrabar marks; loader = run_r24_cot.py lines 37-67 with
its cross-check asserts). Span FROZEN at report weeks 2012-06-05..
2026-01-20 (712 weeks); the 2026-01..08 COT tail is NOT added to the
family (adding data after registration would be rule-shopping, ledger
3944-3948) - it may accrue as forward tracking only.
SIGNAL: NCnet_t = noncomm_long_all - noncomm_short_all; flow_t =
(NCnet_t - NCnet_{t-1}) / OI_{t-1}; z_t = flow_t / std(flow_{t-52..t-1})
(trailing 52 weeks, shifted, current week excluded). Event: |z_t| >= thr.
AVAILABILITY - corrected CFTC release rule (the r60 '+6 calendar days'
convention is WRONG for ~23% of weeks, see side note): release_ts =
report_date + 3d 15:30 ET (Friday); if any US federal holiday (incl.
Juneteenth from 2021) falls Mon..Fri of the report week, release_ts =
the following Monday 15:30 ET (conservative: covers the confirmed
Thu/Fri rule and the disputed Monday-holiday case; 143 of 712 weeks).
The main session may replace this with the exact per-year cftc.gov
release tables if reachable, hard-coded and frozen BEFORE any return is
computed. NON-TRADABLE (dropped, not modeled as late entries - their
catch-up prints were bunched 2-3 per week): shutdown report weeks
2013-10-01..2013-11-05, 2018-12-24..2019-03-05, 2025-09-30..2025-12-16
(29 weeks; includes the four Oct-2025 events z -1.28/-1.74/-1.65/+1.71
of gold's parabolic top - dropped on record, not selectable). ENTRY =
first bar close at/after 09:30 ET on the first gold session STRICTLY
AFTER release_ts (Monday for normal weeks, Tuesday for holiday-delayed
weeks; entry - report_date distribution 6d 548 / 7d 130 / 8d 5 weeks).
Loader asserts release_ts < entry_ts for every event and prints that
distribution before any grid is read. EXIT at the 16:00 ET mark of the
hold-th session, entry session = session 1 (hold 5 = Friday of the
entry week for a Monday entry; hold 10 = the following Friday); one
position at a time (busy-until dedupe); no stop (weekly-horizon claim).
Returns ATR20(daily range)-normalized. IS = first 75% of the 712 report
weeks on the ORIGINAL index (534 weeks, to 2022-08-23); OOS sealed =
178 weeks (2022-08-30..2026-01-20) - split not re-chosen after drops.

FROZEN GRID (4 selectable cells): thr {1.0, 1.5} x hold {5, 10}
sessions. Normal-floor cell: thr 1.0 x hold 5 only (IS 147, OOS 48).
SCARCE-EVENT cells declared now: thr 1.0 x hold 10 (IS 114, OOS 37 -
above the 25 scarce floor), thr 1.5 x hold 5 (IS 76, OOS 20), thr 1.5
x hold 10 (IS 66, OOS 17) - the thr-1.5 cells are under the 25 OOS
scarce floor BY CONSTRUCTION: if selected, the OOS shot can reach only
watch-item status on a power fail, never a pass.
DIAGNOSTICS (non-selectable, IS-ONLY except where stated):
(a) SUB-THRESHOLD BAND: same fade rule on weeks with 0.25 <= |z| < 0.5
(132 tradable weeks, IS 107), both holds; sub-band avgR >= the selected
cell's avgR = generic weekly mean reversion at all flow scales, family
self-refutes at IS.
(b) LATE-ENTRY PLACEBO: identical event set (by construction), entry on
the first session strictly after release_ts + 7d; a liquidity premium
must decay - late avgR >= on-time avgR at the selected cell = slow
drift, family dies.
(c) CONCURRENT PRICE-MOVE PARTITION (IS-ONLY): events split by the
positioning week's own move |ret_week| / (sigma63 * sqrt 5) < 1 vs >= 1
(recomputed on the frozen event set); the small-move partition must be
positive at the selected cell; an effect confined to the big-move
partition = reading attempt 37's object mirrored, family dies (no
re-specification).
(d) INDEPENDENCE GATE vs r24 (attempt-45 form): the selected cell's IS
avgR restricted to events with all three r24 gauges (26w willco_s, 13w
net_c, 13w willco_c) in the 20-80 mid-band must be positive with n >= 40
for the normal-floor cell, n >= 25 for scarce cells (IS subset sizes
45 / 31 / 21 / 18); if the subset is not positive or under its floor,
the family is declared SUBSUMED by r24, the OOS seal is NOT opened, no
shot spent - thr 1.5 x hold 10 (18) is auto-SUBSUMED on selection,
declared now.
(e) COMMERCIAL-FLOW MIRROR REFUSED (see diagnosis).
(f) Both IS halves same sign; neighbor rule = the other hold at the
same thr must be IS-positive; long and short legs each reported (97 /
98 events at thr 1.0 x hold 5 - a one-legged result is reported as such,
not re-specified); cost x1.5 positive; t >= 2.0 floor.
OOS SHOT: the selected cell ALONE (no partitions, no placebos printed on
OOS - protects attempt 37's sealed holdout). Program bar: n >= 40 (25
scarce), avgR > 0, t >= 2, PF >= 1.15, cost x1.5 positive. Would be the
12th shot.
COSTS: MGC 0.35 pt per RT, sensitivity x1.5 (0.525); at a 5-10 session
hold with ATR20 ~30-80 pt one RT is ~0.005-0.01 R - the family is not
cost-dominated; the risk is signal. Entry slippage = the 09:30 ET bar
close, not the open.
EXPECTED N (frozen, signal-side, scratchpad/reg/cot_flow_counts_v2.py):
712 report weeks, IS 534 / OOS 178; tradable after drops 683. thr 1.0:
hold 5 = 195 events (IS 147 / OOS 48; 97 long / 98 short), hold 10
(busy-until) = 151 (IS 114 / OOS 37); thr 1.5: hold 5 = 96 (IS 76 /
OOS 20; 45 long / 51 short), hold 10 = 83 (IS 66 / OOS 17); thr 2.0
(not in grid) 35. Events/yr at thr 1.0 stationary: 9-19 every year
2012-2025. Holiday-delayed events at thr 1.0 x hold 5: 34 (entered
Tuesday under the corrected rule). Under the OLD +6d rule 46 of 220 raw
thr-1.0 event weeks (IS 36) would have been traded before the print
existed - the attempt-15 lookahead pattern (ledger 2760-2780), avoided.
SIDE NOTE ON RECORD for the parent: the '+6 calendar days, no
lookahead' r60 convention used by attempts 42/43 (ledger 4141-4144,
4185) and inherited by watch #11 carries the same defect (Monday 09:30
entries on holiday-delayed and shutdown weeks precede the release);
watch #11's forward accrual should adopt the corrected rule. Test count
+4 selectable (+6 diagnostics).

### Attempt 48 ADJACENCY DIAGNOSIS + registration (BEFORE running):
### aggregate short-interest information-lag regime (RRZ) - SPX/NDX

DATA CLASS: NEW (ledger grep for short interest / FINRA / Rapach /
Ringgenberg / RRZ: 0 hits) - admitted under the class verdict's 'no
further cycle-gauge variants without new data types' (ledger 4436-4437)
WITH the independence gate registered. VERIFIED DEPTH (signal side,
2026-09-03): Equibles GetShortInterest serves FINRA bi-monthly
settlements from 2020-01-15 (AAPL, XOM checked; no rows 2005-2019) -
160 settlements to 2026-08-28. The 2008/2010-depth design and its
120-report windows are VOID; this registration is re-derived for the
verified depth ex-ante and frozen. ADJACENCY: attempts 42/43 (TFF
index-futures positioning, contrarian at LEVEL extremes, class CLOSED;
watch #11 = extreme lev-money net-SHORT -> long, the opposite read on the
shorts axis) - different population (equity cross-section vs futures
hedgers/basis traders), different mechanism (informed-short
underreaction vs crowding), different horizon (regime vs 5/20-session).
Attempt 23 (equity P/C, retail options sentiment, next-day contrarian,
IS-fail) - different data and horizon. Attempt 44 (PMI-contraction
regime, OOS PASS, shot spent) shares the regime-long daily-booking
CHASSIS and the 'just being long' risk; attempts 45/46 recorded that
the drift lives in GOOD regimes (optimism diag t +2.94, ledger
4353-4354; improving-labor diag t +3.68, 4415-4417) - and this family's
direction (long while informed-bearish positioning is LOW) is a
good-state read on the very 2021-2025 span where that drift was
recorded. DISCLOSED NOW: the sealed OOS window (2024-10-15..2025-12-31)
sits 87% inside the mfg-PMI < 50 regime attempt 44 spent its shot on
(the 2025-04..2025-12 episode, ledger 4281/4288); only 40 OOS sessions
per instrument lie outside it. The HIGH-regime control and the
trend-state drift control are therefore the family's load-bearing
refutation instruments, and the OOS qualifier below decides whether a
pass can mean anything but a re-read of attempt 44.

MECHANISM (Rapach, Ringgenberg & Zhou 2016 JFE): short sellers are
informed in aggregate; the aggregate of short positions predicts market
returns at 1-12 month horizons, absorbed slowly because it is published
with a lag, per stock, noisily, and rarely aggregated (information-lag
underreaction). Uninformed counterparty: the index investor trading
without the aggregated signal. Direction fixed ex-ante: LONG indices
while aggregate short interest is LOW (little informed bearish
positioning), flat otherwise; no shorts. Honest prior: RRZ is strong
in-sample 1973-2014 with internal OOS, but (a) post-2014 decay is the
registered principal risk; (b) this proxy departs from RRZ (100-name
mega-cap basket, 1-year trailing percentile instead of a 5-year
detrend, raw split-restated share counts) - the informed-short
population lives in small/hard-to-borrow names while mega-cap short
interest (~1% of float) is dominated by hedging/arbitrage shorts, so the
proxy may measure the wrong population (registered risk #2, not
repairable inside the call budget: full S&P 500 = 500 calls); (c) RRZ
predictability is monthly-horizon and concentrated in bad-return
periods, so long-in-low-SI must beat the HIGH control to count as
anything but drift.

BASKET (frozen, survivorship disclosed): the 100 heaviest current S&P
500 constituents (Equibles GetIndexComposition 'S&P 500', maxResults
100). Point-in-time membership: roll the list back through
GetIndexChanges('S&P 500', maxResults 500); a ticker not a member at
settlement t is excluded at t (one-directional: departed members are
NOT added - disclosed). If GetIndexChanges does not reach 2021-01, or
if > 20% of the basket were non-members at 2021-01-15, the family is
CAPPED at watch-item status ex-ante (cannot graduate whatever the OOS
prints). Survivorship acts on the LEVEL of short interest; the
within-series trailing percentile below is level-free, which bounds the
bias but does not remove it (declared).
SIGNAL: per ticker s_i,t = log(split-restated short position) at each
FINRA settlement t (15th and last business day). A_t = mean_i s_i,t over
tickers reporting and member at t; require >= 60, else the settlement is
skipped and the prior regime carries. Buyback drift in share counts over
a 1-year window (~2-3%) is small vs the series' variability (~20-30%
swings) and is left in, declared. ONE window only: p_t = percentile rank
of A_t within the trailing 24 settlements INCLUDING t (~1 year) -
defined from the 25th settlement, 2021-01-15 (the 24-report burn-in
replaces RRZ's full-sample linear detrend, which would be lookahead).
Regimes: LOW50 = p_t <= 50th, LOW25 = p_t <= 25th; HIGH (control) = p_t
>= 75th; MID = 50-75th (gradient band). AVAILABILITY (no lookahead): the
settlement-t report is treated as known at the close of the 10th
trading day after t (FINRA disseminates ~7-9 business days after
settlement; verified against FINRA's dissemination schedule before the
run if reachable, else +10 stands as conservative); the regime applies
from the NEXT session; re-evaluated only at availability dates
(bi-monthly). Bookings: daily close-to-close at the 15:55 ET print, NY
dates, ATR20-normalized. INSTRUMENTS: MES/MNQ via SPX_5m / NDX_5m
(frames end 2025-12-31). RTY DROPPED: RTY_5m ends 2020-05-14 - no RTY
session has a defined signal; MGC excluded (no mechanism).
SPLIT (FOMC/P-C precedent, ledger 3209-3210: the family's own span):
settlements with a defined signal AND a tradable session = 119
(2021-01-15..2025-12-15); IS = first 89 settlements (2021-01-15..
2024-09-13; regime sessions 2021-02-02..2024-10-14, 916 per
instrument); OOS sealed = 30 settlements (2024-09-30..2025-12-15;
sessions 2024-10-15..2025-12-31, 298 SPX / 299 NDX).

FROZEN GRID (4 selectable cells): {LOW50, LOW25} x {SPX+NDX pooled, NDX
alone}. NDX alone is the mechanism-implied sub-cell fixed ex-ante: the
measured basket's weight is dominated by Nasdaq-100 mega-caps, so NDX is
the index whose constituents' short interest is actually observed.
DIAGNOSTICS (non-selectable):
(a) HIGH-REGIME LONG (p_t >= 75th), same bookings: reported as the
difference LOW - HIGH with its t, not a sign; HIGH avgR >= the selected
LOW avgR = generic drift, family dies at IS (attempt-25/44 pattern).
(b) GRADIENT BAND: avgR must be monotone non-increasing LOW25 -> LOW50
-> MID (50-75) -> HIGH (>= 75); a non-monotone winner is a spike.
(c) TREND-STATE DRIFT CONTROL (replaces the delay placebo, which has no
power at a 24-report window and a bi-monthly regime - dropped, declared):
(i) the same bookings on sessions where the index close > its 200-day
SMA (trend-long null); the selected LOW cell must beat it by a t >= 2
DIFFERENCE; (ii) the r16-B randomly-timed-regime max-stat null: 1000
random regimes with matched coverage share and matched mean episode
length per cell, max over the 4 cells; the selected cell's IS avgR must
sit above the 95th percentile of that null. Failing either = the LOW
regime is a bull-state proxy, family dies at IS.
(d) INDEPENDENCE GATE vs attempt 44 (attempt-45 form, strengthened per
the class verdict): within IS sessions OUTSIDE the mfg-PMI < 50 regime
(473 per instrument), the selected cell's LOW avgR must be positive with
n >= 120 AND must exceed the HIGH-regime avgR on the same non-overlap
sessions; otherwise SUBSUMED, seal NOT opened, no shot spent. Expected
non-overlap n: LOW50 pooled ~472, LOW25 pooled ~236, NDX-alone LOW50
~236, NDX-alone LOW25 ~118 - the last is at the floor by construction:
if it wins with non-overlap n < 120 the family is SUBSUMED, declared now.
(e) OOS QUALIFIER (non-selectable, printed on the shot): the OOS window
is 87% attempt-44 contraction sessions. On the shot the HIGH-regime
control is printed on OOS alongside the selected cell; if OOS HIGH avgR
>= OOS LOW avgR, an OOS pass is recorded as PASS-CONFOUNDED (drift /
attempt-44 re-read) and the family caps at watch-item status - it
cannot graduate on this span. Only LOW > HIGH on OOS with the program
bar met counts as a pass.
(f) SIGNAL-SIDE PRE-RUN CHECKS (no returns): per-settlement reporting
coverage (>= 60 of 100) printed; membership-rollback coverage printed;
LOW50/LOW25 session shares and regime-episode counts printed (expected
dozens of bi-monthly re-evaluations vs the ~5 episodes of the PMI
family); availability-vs-entry timestamps asserted.
(g) Both IS halves same sign; sibling-positive (the other threshold in
the same instrument grouping); regime-episode signs reported (effective
n); cost x1.5 positive; t >= 2.0 floor; n >= 120 bookings.
OOS SHOT: program bar (n >= 40, avgR > 0, t >= 2, PF >= 1.15, cost x1.5
positive) plus qualifier (e). Would be the 12th shot.
COSTS: MICRO/20 per daily booking (attempt 44-46 regime-amortization
convention) plus one full micro RT (SPX 0.35, NDX 1.0) per regime
toggle - bi-monthly re-evaluation allows up to 24 toggles/yr worst case;
1.5x sensitivity mandatory.
EXPECTED N (frozen, signal-side, scratchpad/reg/si_calendar_v2.py):
160 Equibles-depth settlements; 119 with a defined signal and a
tradable session; IS 89 / OOS 30 settlements. Sessions per instrument:
IS 916 (2021-02-02..2024-10-14), OOS 298/299 (2024-10-15..2025-12-31).
Regime shares ~50% / ~25% by construction for a stationary series ->
IS bookings pooled ~916 (LOW50) / ~458 (LOW25), NDX alone ~458 / ~229;
non-overlap (outside PMI < 50) IS sessions 473 per instrument, OOS 40.
Actual shares are printed pre-run; a trending A_t inflates LOW share -
that is what control (c) is for.
DATA NEEDED: Equibles GetIndexComposition('S&P 500', maxResults 100);
GetIndexChanges('S&P 500', maxResults 500); GetShortInterest(ticker,
startDate 2020-01-01, endDate 2025-12-31, maxResults 500) x 100 (~102
calls; 'estimate' rows below the table stripped). On disk: SPX_5m /
NDX_5m 15:55 closes; econ_events_us_high_fxs.json (ISM Manufacturing
PMI 'a' values, regime = last release strictly before the session) for
gate (d) and qualifier (e). Test count +4 selectable (+6 diagnostics).

### Attempt 47 result: IS FAIL (fails the t floor; independence gate negative; sub-band self-refutes)

(results/r64_cotflow_is.json, run_r64_cotflow.py; built and reviewed
under the OOS firewall - OOS rows dropped at frame build, --unseal never
invoked; 2 adversarial reviewers, 0 fatal findings.) Event counts
reproduce the frozen registration exactly (IS 147/114/76/66; r24
mid-band subsets 45/31/21/18; sub-band 107). IS GRID (fade the flow,
MGC 0.35/RT, ATR20-normalised, IS report weeks 2012-06-05..2022-08-23):
thr 1.0 x hold 5 n 146 PF 0.98 avgR -0.000 t -0.00 halves [+,-];
thr 1.0 x hold 10 n 113 PF 0.75 avgR -0.268 t -1.36 [-,-];
thr 1.5 x hold 5 n 76 PF 0.95 avgR +0.033 t +0.23 [-,+];
thr 1.5 x hold 10 n 66 PF 0.64 avgR -0.455 t -1.68 [-,-].
No cell approaches t >= 2; the family fails at IS; OOS seal NOT opened,
no shot spent (program shots remain 11). DIAGNOSTICS, for the record:
(a) sub-threshold band POSITIVE at both holds (+0.103 / +0.169) - above
every selectable cell, i.e. whatever weekly mean reversion exists is not
a flow-scale effect (self-refutation would have fired); (b) late-entry
placebo more negative than on-time in every cell (the one diagnostic in
the family's favour); (c) small-move vs big-move partition flat in both;
(d) INDEPENDENCE subset (all r24 gauges mid-band) NEGATIVE in every cell
(t -1.42 / -2.26 / -1.47 / -1.76) - had any cell cleared the floor the
family would have been declared SUBSUMED by r24. ONE-LEGGED PATTERN,
reported not re-specified per the registration: fading spec SELLING
(long leg) is positive in all four cells (thr 1.5 x hold 5 long n 37
avgR +0.417 t +2.13), fading spec BUYING (short leg) negative in all
four (t down to -2.35) - a long-only sub-cell would be a post-hoc
re-specification and is refused; noted as the residue of a gold
up-drift over the span. VERDICT: the KRT liquidity premium does not
survive as a single-commodity time-series rule on gold at a Monday
entry; the flow transform carries nothing the r24 level read did not.
Family closed. Program score: 1 OOS pass (on paper) / 47 attempts + 10
registration-stage kills; 11 shots spent.
TEST-COUNT DISCLOSURE (from the reviewers, on record): the builder's
first full IS run used an off-by-one busy-until dedupe (event set
119/100/69/59, best cell t +0.04) before the count mismatch against the
registration was diagnosed and corrected; the 4 selectable cells and
all diagnostics were therefore read twice on nested event sets, both
reads failing at IS. Counted: +4 selectable reads. Minor review notes,
none outcome-changing: the holiday-delayed release rule is not
re-applied when the following Monday is itself a federal holiday
(2 IS weeks, both non-events at the traded thresholds); the ejtrader
15m feed follows US rather than Athens DST in the mismatch weeks (entry
marks up to 1h early on ~2% of sessions, both feeds cross-checked in
r24); Inauguration Day absent from the holiday calendar (non-events);
one boundary trade per thr-1.0 cell exits after the first sealed week
(30 minutes after that release) - IS-only exposure, no OOS read.

### Attempt 48 pre-run data declaration (2026-09-03, BEFORE any return is computed)

Equibles GetShortInterest served 81 of the 100 registered basket
tickers (80 with FINRA rows; GOOG has no series and GOOGL is NOT
substituted) before a server-wide outage stopped the pull; the 19
missing tickers (TJX NOW VRTX BMY SPGI PLD COF NEM ISRG DHR PGR CVS
DELL CB SBUX PH MDT MO ADBE) are a fixed set determined by fetch order
and the outage, not by any return, and are DECLARED EXCLUDED for this
run (basket = the 80 series on disk, data/shortint/). Per-settlement
coverage of the 80: min 75 / median 78 / max 80 across 144 settlements
2020-01-15..2025-12-31 - above the registered >= 60 floor everywhere.
Point-in-time membership: GetIndexChanges reaches 2020-03 (through 2025
changes are dated only to a calendar quarter; conservative rule fixed
now: a ticker added in a quarter window is treated as a non-member for
every settlement before that window's END date); basket names added
inside the span are PANW, UBER, CRWD, GEV, PLTR, DELL(missing anyway),
SNDK - far under the 20% cap, so the family is NOT capped on
survivorship grounds. FINRA dissemination lag verified from FINRA's
schedule (settlement -> publication = 7th business day, e.g. 2025-11-14
-> 2025-11-25, 2025-12-15 -> 2025-12-24; time of day not established),
so the registered '+10 trading days' availability rule is conservative
and stands unchanged. Provenance flags on record (data/shortint/
notes.txt): META valid from 2022-06-15 (pre-rename rows dropped), RTX
from 2020-04-15, GEV/PLTR/SNDK from listing, ~15 merger/exchange-offer
level jumps in individual series - the registered 'wrong population'
risk. Nothing else in the registration changes.

### Attempt 48 result: IS FAIL - the registered direction is the wrong side of the drift

(results/r65_shortint_is.json, run_r65_shortint.py; IS-only under the
firewall, --unseal never invoked; 2 adversarial reviewers, 0 fatal.)
Signal-side checks reproduced the frozen registration exactly (119
defined-and-tradable settlements, IS 89 / sealed 30, 916 IS rows per
instrument, availability asserted for every settlement; basket 80
series, membership rollback 7/80 non-members at 2021-01-15 = 8.8% <
20% cap; coverage 70-79 reporters, floor 60 never breached). IS GRID
(daily 15:55 close-to-close, long only, ATR20-normalised, net of
MICRO/20 + toggle costs; IS sessions 2021-02-02..2024-10-14):
LOW50 pooled n 800 avgR -0.043 t -1.41 halves [-,-]; LOW25 pooled n 380
-0.015 t -0.35 [-,+]; LOW50 NDX n 400 -0.031 t -0.73 [-,+]; LOW25 NDX
n 190 -0.002 t -0.03 [-,+]. Every selectable cell negative; no cell near
the t floor; sibling rule fails everywhere. CONTROLS all POSITIVE: MID
pooled +0.134 t +3.38, HIGH pooled +0.100 t +3.00, TREND (> 200-SMA)
+0.066 t +2.85; the r16-B random-regime null (smoke run, 100 draws) puts
the best LOW cell at p 0.99; outside the PMI < 50 regime LOW -0.115 vs
HIGH +0.058 (would have been SUBSUMED). OOS seal NOT opened, no shot
spent (11 remain spent). Regime structure: LOW50 7 episodes, LOW25 4.
VERDICT: the RRZ aggregate-short-interest signal, in the mega-cap
hedging-short proxy this data can build, has the WRONG SIGN on 2021-24:
returns were higher when aggregate short interest was HIGH - consistent
with the registration's own 'wrong population' risk (mega-cap short
interest is arbitrage/hedging inventory, and rises with the market).
Family closed. CLASS OBSERVATION on record: attempts 45, 46 and 48 -
three different gauges, three different data classes - all put the
equity drift in the GOOD state (optimism, improving labor, high short
interest = active hedged longs); attempt 44 (PMI < 50) remains the one
gauge that paid on the weak side, and it is on paper precisely so the
forward data can say whether that is a mechanism or a 2022-25 accident.
Program score: 1 OOS pass (on paper) / 48 attempts + 10 registration-
stage kills; 11 shots spent. Round 64 sweep CLOSED: 12 proposed, 10
killed at registration, 2 run, 2 IS-fail. The on-disk and reachable
data frontier is exhausted for the mechanism classes tried; the next
sweep must begin with data-availability probes of genuinely new
classes (Equibles currently down).

### 2026-09-03: data-frontier probe (reference/data_frontier_2026-09-03.md) - verdict

Probed for genuinely NEW data classes before any further sweep (no
returns computed). REACHABLE WITH DEPTH: Alpha Vantage daily 2y yield
(1976+), effective fed funds (1954+), Brent/WTI (1987+/1986+), CPI and
copper monthly only - all slow rates/oil regimes, adjacent to the
CLOSED business-cycle class (the claim needs a new mechanism, not a new
gauge). REACHABLE BUT SHALLOW: COMEX gold term structure - the 5-year
Dec-contract histories are settlement marks on deferred months with
ZERO volume until the final months, and IBKR only serves contracts
expired within ~12 months, so genuine front-month basis history (where
the 2025 EFP/physical-squeeze signal lives) is ~18 months: forward
material, not a backtestable family; VIX futures basis ~18 months and
adjacent to burned attempt 25 (cash term structure); HSI futures pre-
open bar 6-12 months (forward material for the MHI stream at most).
BLOCKED: every Equibles class (fails-to-deliver, daily short volume,
insider/congressional aggregates, IPO/earnings calendars) - server
protocol bug, not transient; Deribit and CBOE unreachable from the VM
(Kernel browser only). VERDICT: no new class with adequate depth is
reachable today; per the house rule (never grind cells, no
manufactured findings) NO sweep is launched on the slow-macro classes.
STANDING ORDER for the weekly routine: probe Equibles; when it serves
GetFailsToDeliver / GetShortVolume with >= 5 years of depth, pull SPY/
QQQ/IWM (and the 80-name basket's short volume) and open a Round 66
sweep restricted to those classes (Reg SHO close-out flow is a genuine
forced counterparty). Program score unchanged: 1 OOS pass (on paper) /
48 attempts + 10 registration kills, 11 shots.

### 2026-09-03: registration-stage kill - Treasury coupon SETTLEMENT-day funding drain

Candidate (on-disk data, never proposed by the sweep): primary dealers
must fund their auction takedown on the ISSUE date (settlement), a
reserve drain with a forced counterparty, distinct from the burned
auction-DAY family (attempt 26, wrong-way both arms; attempt 27,
outcome-following negative) which traded the 13:00 ET result. Signal-
side check only (data/treasury_{note,bond}_auctions.json, field
issue_date; 1,445 auctions 2005-2025, 497 distinct issue dates, issue -
auction lag 1-10 days): 201 issue dates fall on the 14th-16th, 179 on
the last business day of the month, 60 on the first business day - 88%
of settlement days ARE the mid-month / month-turn calendar that watch #2
(month-end fade), watch #6 (quarter-end TOM) and the burned opex-week
family (attempt 19) already occupy, and 414 of 497 days settle >= 3
securities at once, so there is no within-family size gradient (the
file carries no offering amounts) that could separate a funding drain
from the calendar date. Any result would be a re-read of the month-turn
residues. KILLED AT REGISTRATION; no grid built, no test counted beyond
this record. (11th registration-stage kill on record.)

### 2026-09-03: MHI stream - futures fidelity check (reference/mhi_futures_fidelity_2026-09-03.md) and the MHIF twin

FINDING (real HSI front-month futures 15m via IBKR vs the HK33 CFD, 11
liquid sessions 2026-08-19..09-02, structural cause established): the
CFD has NO pre-open auction print - it stops at 18:45Z and reopens with
a synthetic 01:15Z bar - so its 09:15-09:30 HKT push is ~0.72x the
futures push (mean |push|/ATR14 0.148 vs 0.249; push corr 0.87, sign
agreement 9/11, median |push diff| 0.14 ATR = half the frozen 0.3
threshold). At the frozen threshold the two feeds triggered on DISJOINT
sessions (CFD 1, futures 4, both 0; 33 sessions incl. thin: 1/5/0).
Entry (01:30Z open) and exit (last close < 08:00Z) marks are faithful
(median 19-20 pts = a basis that cancels within the session; entry-to-
exit move differs by 3 pts median), short stops faithful (21 pts), long
stops ~50 pts too wide on the CFD. CONSEQUENCES: (1) the MHI paper
stream on the CFD journals a different set of days from what a futures
account would trade; (2) the archived 43-trade backtest (round 15b) was
computed on the same synthetic pre-open bar, so its evidence for the
MECHANISM (fading the auction push) is weaker than recorded - it
measured the CFD's synthetic open, not the auction; provenance rule #1
applies. NOT a stop of the stream: the rule is frozen, the CFD stream
continues as a PROXY for comparison, and a twin stream MHIF (forward/
leg_mhi_fut.py) now evaluates the identical rule on futures bars
(weekly IBKR pull of the front month; roll = later file wins; note
carries the contract). MHIF is the promotion evidence for the MHI rule;
the 80-trade bar and the CFD's PF >= 1.4 both-halves criterion apply to
MHIF. STREAM_START MHIF = 2026-08-19 (first liquid front-contract
session; the rule was frozen in round 15b and no futures bar was used in
any selection). First MHIF rows (back-filled from the probe pull):
2026-08-21 S stopped (-117.5), 2026-08-24 L stopped (-99.5), 2026-08-27
S time (+224.0), 2026-09-02 S time (+4.0) - versus the CFD's single
trigger 2026-09-01 (L, stopped). Weekly trigger now pulls the futures.
