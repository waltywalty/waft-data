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
