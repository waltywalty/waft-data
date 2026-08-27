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
