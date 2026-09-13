# INTRADAY BURNED-FAMILY INVENTORY (waft-data, rounds 1-68 / attempts 1-49)

Compiled 2026-09-09 from `backtest/README.md`, `backtest/reference/goal_ledger.md` (5,594 lines),
the generated round reports under `backtest/results/`, the round-12/15/15b pre-registrations and
runner headers, and the data-acquisition notes in `backtest/reference/`. Read-only; nothing in the
repo was modified. Scope = INTRADAY families: hold inside a session, or entry/exit at defined clock
times, on gold (XAUUSD spot/CFD as the MGC proxy), SPX/NDX/RTY (24h CFD frames as the MES/MNQ/M2K
proxies), HSI/HK33 (MHI proxy), JP225, plus the few multi-day calendar families whose LEGS are
clock-anchored (they occupy specific clock cells and are listed for that reason).

Purpose: so that no future proposal can re-parameterise a cell that is already inside a scanned range.
The rule of the house (round 41b / round 42 protocol): a family whose one-shot OOS was SPENT is closed
for good on that holdout (forward accrual only); a family that FAILED AT IS has its holdout sealed and
is closed unless a written, mechanism-grounded repair (one per family) is registered; a family KILLED
AT REGISTRATION was never run but the adjacency reason is binding; and "a new cell inside a scanned
range" is not a new family.

---------------------------------------------------------------------------------------------------

## 0. Conventions used throughout this inventory

**Status codes.** `DEPLOYED` (live/paper stream) · `CANDIDATE` (forward-test/paper candidate, frozen) ·
`WATCH` (frozen spec accruing forward data; no re-search) · `BURNED-OOS` (one-shot holdout spent,
family closed) · `BURNED-IS` (failed in-sample floor; holdout sealed, closed; one repair may remain) ·
`DEAD` (pre-protocol rounds 1-41: failed the house bar on the full sample) · `KILLED-REG` (killed at
registration by adversarial critics, never run) · `RETRACTED`.

**Clock conventions.** ET = America/New_York unless stated. Gold Asia open = 09:30 HKT = 01:30 UTC
(HK has no DST). RTH indices = 09:30-15:55 ET bar starts. "EOD"/"session close" = 15:55/16:00 ET.

**Cost models (every intraday cell was scored with one of these).**
- House CFD costs (rounds 1-36, per round trip): gold $0.30/oz (+$0.30 stop slippage on stopped
  exits from round 3 on); SPX 0.6 pts; NDX 2.0 pts; RTY 0.4 pts; HSI/MHI 10 index pts.
- Micro best-case (round 37b onward, per RT = cheap-broker commission + exchange fees + one tick of
  spread each way): SPX/MES 0.35, NDX/MNQ 1.0, RTY/M2K 0.35, GOLD/MGC 0.35 pts. Regime families
  amortise as MICRO/20 per daily booking plus one full RT per regime toggle.
- Point values used for the "micro" framing: MGC $10/pt, MES $5/pt, MNQ $2/pt, M2K $5/pt.
- Unger floor (adopted round 24): a candidate must show average net trade >= 2x round-trip cost
  before any other statistic is read (deployed gold rule: $1.60/oz vs $1.20 bar).

**Evidence bars.**
- House bar (rounds 1-41): same sign in both halves (gold 2020-23 / 2024-25; SPX 2020+, NDX 2021+,
  RTY 2017+ or 2005-15/2016-25 depending on round), smooth parameter gradient, max-stat
  randomisation survival, explicit costs with sensitivity, pre-registration.
- r42 program bar (attempts 1-49): IS = first 75% of each instrument's sessions (holdout = last 25%,
  sealed); selection by pooled ATR20-normalised per-trade t with min 120 pooled IS trades (40 IS / 25
  OOS for scarce-event families), IS t >= 2.0 floor (amendment after attempt 7), neighbour-majority
  gradient check (scoped to the mechanism subspace, amendment after attempt 5), self-refutation
  diagnostics; ONE OOS shot judged at same sign, t >= 2, PF >= 1.15, cost x1.5 still positive,
  n >= 40 (25 scarce). ~2-5% of null attempts pass by luck; 11 shots spent so far.
- Adopted protocol notes that bind future intraday work: every cross-market/multi-feed signal must
  print its availability timestamp vs the entry timestamp before a grid is read (attempt 15 leak);
  5m bar labels are bar STARTS, so a lower-TF fill window must begin strictly after the signal bar's
  END (round 38 leak); volatility-detected event sets are invalid for directional claims (attempt 11);
  any strongly one-sided net result gets a gross decomposition (attempt 2b); mirror runs of a failed
  direction are forbidden without an independent mechanism (attempts 6, 26, 27).

---------------------------------------------------------------------------------------------------

## 1. OCCUPIED TERRITORY: the deployed gold Asia ORB and everything scanned around it

### 1.1 The deployed rule (round 6 deployable configuration; MT5 EA `AsiaOpenGold.mq5` v1.20)
- Instrument: spot XAUUSD (CFD); MGC needs >= ~$25k to express (round 4).
- Gate (this IS the edge): 20-day rolling correlation of gold and AUDUSD DAILY log returns using
  closed daily bars through yesterday; trade only when corr <= 0.5 (keeps ~60% of days); skip the
  day if the AUD feed is missing (unfiltered PF 0.85).
- Range: high/low of the first 60 minutes from 09:30 HKT (01:30 UTC).
- Entry: first subsequent 60-minute candle to CLOSE beyond the range, at its close, in that
  direction; one trade/day, first break only; no entry after 08:00 London (late entries PF 0.951).
- Stop: 2x range width from entry (drawdown-control choice; no stop backtests better).
- Exit: flat 16:00 New York same day.
- Size: flat 1% of equity off the actual stop distance.
- Record: 745 trades / 158 per yr (round 6 count) or the frozen 652-trade "deployable" set used by
  every later study: win 40.2%, PF 1.320, t +2.54, +$1.62/oz avg net; halves 1.178 / 1.500;
  correlation-aware max-stat p 0.036; FAILS Bonferroni at any plausible test count; ICIR +0.340 vs
  +0.041 for raw breakout direction; signal half-life ~27 days. Planning CAGR +12.8% (2020-23 half).
- Live: paper streams XAU + XAUAUD (auto-journalled from 2026-08-27), SPRT alpha=beta=0.10,
  promote LLR >= +2.20 / kill <= -2.20; ~160 trades median to any decision (~1.1 yr).

### 1.2 Parameter cells already scanned on this family (do not re-propose inside these ranges)
| Axis | Cells scanned | Where | Result shape |
|---|---|---|---|
| Opening-range length (09:30 HKT anchor) | 5, 10, 15, 20, 30, 45, 60, 90, 120 min | r1, r25b | smooth slope: net PF 5m 1.028 -> 10m 1.064 -> 15m 1.113 -> 20m 1.110 -> 30m 1.224 -> 60m 1.329 -> 90m 1.413 (90m tip is a 2024-25 era artefact; 120m decays). Nothing below 30m survives costs or halves. |
| Confirmation candle = range length | 5..90m (r25b/r25c); 5m/15m/30m/60m confirm on 15m/30m ranges (r7, NY) | r1, r7, r25 | 60m confirmed at every corr window; no window x TF interaction |
| Session start sweep | 08:00 HKT .. 09:30 HKT peak | r1 | 09:30 HKT sits at the peak (1.16 vs 0.95 at 08:00) - flagged as suspiciously sharp in r1 |
| Exit clock | 07:00 / 08:00 / 12:00 / 16:00 / 16:30 London; 16:00 HKT; 09:00 ET; 09:30 / 11:00 / 13:00 / 16:00 NY; overnight hold | r1, r2, r9 | every earlier exit loses to 16:00 NY (PF 1.381 walker); overnight PF 1.05 halves disagree; hold curve underwater 3h then monotone |
| Targets | 1x, 2x, 3x, 4x, 6x range; none | r1, r9 | none beats no-target (6x ties) |
| Trails / breakeven | trail 1.0/1.5/2.0/3.0x range; armed-after-+1-range variants; stop-to-entry after +0.5/+1.0/+1.5 range | r9 | two beat PF (BE at +1R 1.498; 2x trail 1.440) but compound to ~60% of the clock's equity |
| Stop width | none; 0.5x, 1x, 2x, 3x range; 0.05/0.10/0.25/0.50/1.00 x ATR14; 2N (Turtle); far side of range | r1, r3, r8, r24 | smooth monotone: tighter = worse (0.05xATR PF 1.155 -> no stop 1.450); 1x range stop hit 72%; slippage sensitivity kills tight stops |
| Fixed brackets on the 652 entries | +/-15 and +/-20 MGC pts x RR 1:1/1:2/1:3 (r11); TP +10 x SL {5,10,20,none} (r36) | r11, r36 | +20pt RR1:1 PF 1.374 t +3.46 = re-derives the wide-stop result (56% still exit on clock); TP10 amputates the edge (best cell keeps 38% of baseline P&L) |
| Corr window | 10, 20, 30, 40, 60, 90 days | r3, r25 | plateau 10-30d; every cell PF > 1 |
| Corr threshold | -0.4 .. 0.9 in 0.1 steps (0.0/0.2/0.4/0.5/0.6/0.8 grid) | r2, r3 | monotone from 0.6 down to 0.0; marginal 0.5-0.6 band PF 1.07 t +0.04; 0.6-0.7 net negative |
| Corr computed intraday | H1 returns windows {24,48,120,240} bars; M15 {96,480} bars; thresholds {0.3,0.5,0.7} | r25 | dead (max-stat p 0.948); no residual info inside the daily gate |
| Corr lag / staleness | lag 1-3 days OK, sags ~5 | r6 | |
| Corr partners | silver, synthetic DXY, EUR, JPY, GBP, CHF, CAD, CNY, WTI, SPX, UST10Y; 416 cells; stacking AUD AND partner | r5, r13 | no partner beats AUD (re-selects 88-92% of AUD days); stacked gates matched by circular-shift null (p 0.30) |
| Same-day AUD agreement | Asia-session AUD direction agree/disagree | r2 | p 0.20, nothing |
| VIX level terciles | calm/mid/stressed | r16D | descriptive gradient 1.45/1.40/1.13, all positive, halves mixed |
| TSMOM overlay | trend sign lookbacks 63/126/189/252d agree vs against | r15 F3 | no gradient |
| 21 confluence filters | range/ATR, EMA-trend alignment, 5d momentum, prior-day direction, overnight gap, PDH/PDL break, vol regime, open position in prior range, direction, weekday | r1 | 1-3 of 21 survive both halves on any range (chance ~5) |
| Practitioner adaptations (50 tests on the 652 set) | NR7, inside-day, range/ATR quintiles, relative tick-volume quintiles, first-post-range-candle vs later, prior-day-range veto, ATR-fraction stops, first-bar-direction entry (5m/15m, stops at bar extreme / 0.10 / 0.25 ATR) | r8 | survivors: rvol q5 (PF 1.843 t +2.54, halves 1.73/1.98) and inside-day (PF 1.616 n 94); NR7 disagrees; first-bar entry dead (PF 0.66-0.98) |
| Entry mechanics | stop order at boundary (no close confirm); limit back at boundary; deeper pullback limits (to 1.0 range) | r1 | same or worse; pullback fill rate 70%, PF 0.87 (adverse selection) |
| Sweep-and-reclaim entry | bias -> counter-sweep of {swing L/H, breakout-candle low, Asia extreme, far side of OR} -> reclaim in 1-6 bars; 4 ranges x 4 levels x 7 exits | r2 | better fill, still loses (best PF 1.096); sweep days PF 0.61 vs never-swept 1.93 |
| Sizing | flat 1%/2%; x1.5/x2 per loss caps 4%/8%; +0.5%/loss; x1.5 per win; halve after loss; N-sizing; DD throttle; intraday pyramiding max-units 1-4 | r9, r24 | flat wins; pyramiding gradient monotone NEGATIVE (t +2.50 -> -5.23) |
| Denominator | XAUUSD/XAUAUD 50/50 (UPGRADE #1); +EUR/+JPY 4-way basket; silver instrument | r18B, r19, r20 | 50/50 USD/AUD is the closed final form; basket fails; silver dead (PF 0.778 t -3.57) |
| Trading the high-corr days | breakout (r13), fade (r8/r13), tether residual-fade |z|>={1,1.5} enter 07:00 UTC exits 12:00 UTC/16:00 NY (r21) | | dead through three lenses (residual CONTINUES, hardest on low-corr days) |
| Session split of the 652 trades | entry->07:00 UTC 17% / 07:00->14:00 UTC 70% / 14:00->exit 13% | r15 F4 | Asia sets direction; London/NY pays it |
| SGE auction interaction | 02:15 UTC AM fix drift into/after; post-auction 15m candle sign; 01:30 vs 02:15 candle agreement; auction-hour (02:15-03:15) value-zone fade vs 03:15-04:15 control | r17, r26, r26b | drift +0.76 bps/day t +2.56 sub-cost (MONITOR yearly); candle sign real (max-stat p 0.004) but hit rate 50.8%, t +1.22 at ZERO cost, non-additive to the rule (agree PF 1.43 / disagree 1.29); value zone PF 0.625 worse than control 0.733 |
| Gold 2012+ Asia premium on extended data | refused at diagnosis (adjacent to spent attempt 7) | r56 | KILLED-REG |

### 1.3 Candidates and upgrades that are "occupied" (frozen specs; forward data decides)
- **Opening-range relative volume >= 1.25 (top quintile)** - r8 B4; PF 1.843 vs 1.320, halves
  agree; fires ~20% of trades; EA logs it; promote if gated subset beats base after 6-12 months / SPRT.
- **Prior session inside day (Crabel)** - r8 A2; PF 1.616 n 94 halves 1.49/1.78; ~14% of trades; same bar.
- **London 08:00 add-to-a-winner** - r12 (pre-registered): on deployed-filter days where the Asia
  break fired and is in profit at 08:00 London, re-enter in the Asia direction, exit 16:00 NY;
  variants no stop / 2R. Standalone PF 1.592, t +2.98, halves 1.238/2.265, n 323. Strongest derived
  result; forward-test candidate #3; EA v1.20 logs it. Portfolio stacking (r18C) adds return 1.56x
  mechanically but Sharpe gain flips sign across eras (leg corr 0.73/0.50) - legs stay candidates.
- **NY 09:30 re-entry** - r12: on deployed days, enter 09:30 NY in the Asia-break direction, exit
  16:00 NY; variants all / in-profit x no stop / 2R. Best in-profit + 2R: PF 1.333, t +1.80, halves
  1.088/1.670 (the only NY-session construction in 12 rounds with positive full-sample t). r17b
  trend-day conditioner (09:30 price position in day-so-far range >= 0.7 / 0.8) FAILS (PF 1.324 t +1.52;
  >= 0.8 kills it). Recorded, not for capital.
- **Dual-denominator split (UPGRADE #1, deployed as paper stream XAUAUD)** - r18B: same signals,
  half size on XAUUSD and XAUAUD; paired quality t -0.21; P&L corr +0.40 era-stable; 50/50 Sharpe
  2.21/2.17 vs singles 1.47->2.46 / 2.28->1.10; XAUAUD survives 3x costs (PF 1.33). Basket (EUR/JPY)
  and silver extensions closed (r19/r20).
- **MGC bracket expression** - r11: +/-15-20 pt RR 1:1 with 16:00 NY fallback (PF 1.15-1.37 across
  the family) - an expression of the rule, not an upgrade; re-check width yearly vs 0.5-0.8% of spot.
- Portfolio reference split (r28e, adopted): gold 35 / D7 40 / MHI 25 (plateau gold 15-40 / D7 40-70 /
  MHI 0-25); never re-optimised on a rolling window.

---------------------------------------------------------------------------------------------------

## 2. BURNED FAMILIES, GROUPED BY MECHANISM CLASS

Format per entry: **Name** - round/attempt - instruments & TF - construction - cells scanned -
verdict (one-line reason) - status.

### 2.A Opening auction / opening-range breakout (ORB) and its fades

1. **Gold Asia ORB, raw (no gate)** - r1 - XAUUSD 5m - ranges 5/15/30 (and 45/60/90/120) min from
   09:30 HKT, same-TF close beyond, exits 07:00/08:00/12:00/16:30 London, no stop - 12 specified +
   extensions - 11 of 12 lose; best 30m->16:30 London PF 1.026; breakout calls day direction 60-63% from
   the open but 51% from the fill (confirmation costs the whole range width; 71-87% of days trade
   back through the far side) - DEAD as an unfiltered rule; the gated version is the deployed rule.
2. **Gold NY 09:30 ET ORB follow** - r7 - XAUUSD 5m - ranges 5/15/30/60 min from 09:30 ET; first 5m
   close beyond; one trade/day, no entry after 90 min (deadlines 30/60/90/150/390 also run); exits =
   5 clock (first hour, 90 min, 2h, NY lunch, NY close) + 5 liquidity targets (prev-day H/L, Asia H/L,
   London H/L, prior-hour H/L, measured move 1x range); stop {far side of range, none, 0.5x/1x/2x
   range}; filter {none, corr <= 0.5}; confirmation TF 5/15/30/60m on 15m/30m ranges; costs
   $0/0.15/0.30/0.60 - 117 scored cells - with stop 1/39 clear PF 1.0 (median 0.899); no stop 0/39
   (median 0.847); filtered 12/39 (median 0.974); best t +0.70; zero-cost PF 1.030 = coin flip gross;
   NY breaks HOLD (45% whipsaw vs 79% Asia) but leave +$0.10/oz after a $4.74 move already made;
   honest OOS (rank pre-2024) median 0.954 vs population 0.930 - DEAD (cost-dominated, no gross edge).
3. **Gold NY ORB fade** - r8 - XAUUSD 5m - mirror engine (proven exact negation on 1,174 trades);
   ranges 5/15/30/60; exits incl. NY lunch, NY close, far side of range, London H/L, first 2h, range
   midpoint, prev-day H/L, first 90 min; stops 0.5/1/2x range/none; fade only closes >= 0/0.10/0.25/
   0.50 x range beyond; filters all / corr <= 0.5 / corr > 0.5 - 123 cells - loses $0.13/oz BEFORE
   costs (zero-cost PF 0.945); corr ordering inverts as the gate's mechanism predicts; corr > 0.5 IS
   cells (PF to 1.27) collapse honest-OOS to median 0.655 - DEAD (both directions of the NY open lose
   gross).
4. **NY ORB volatility/volume filters** - r11 - XAU/SPX/NDX/RTY 5m - fixed 15m and 30m NY ORB
   follow/EOD gated by impulse (range/ATR) terciles, relative-volume terciles, ATR regime (below/above
   1-yr median) - 72 cells - gold strong-volume/impulsive 30m cells IS PF 1.474 t +2.32 -> OS 0.771/
   0.725 ("sharpest in-sample mirage in the repo"); on indices the surviving direction inverts (quiet,
   weak-volume opens break better, Crabel compression) and still loses net - DEAD (selection mirage).
5. **30m-range / 10m-confirm / EMA-pullback continuation entry** - r11 - XAU/SPX/NDX/RTY 5m - 30m
   NY range, 10m close outside, pullback to 8-EMA-on-5m (2m-20 equivalent) or 20-EMA-on-5m, entry on
   continuation close; exits prev_day / prev_hour / 2R / EOD - 32 cells - better fills than raw break
   (zero-cost PF ~1.1 in half the cells) and nothing survives costs; prior-hour exit worst of all
   (PF 0.62-0.86) - DEAD (cost-dominated).
6. **Fixed 15/20-point micro brackets on NY entries** - r11 - 30m ORB break and EMA pullback on
   XAU/SPX/NDX/RTY as MGC/MES/MNQ/M2K: +15/+20 pt x RR 1:1/1:2/1:3, flat at close - 48 cells - dead on
   every NY entry; MNQ structurally terrible (15 pt = 0.35% vs 2-pt spread; PF 0.56-0.75, t to -13) -
   DEAD (volatility-blind brackets).
7. **Index NY-open families** - r9 - SPX/NDX/RTY 5m 2005-2025 (RTY to 2020) - Zarattini first-bar
   (09:30 5m bar direction, stop at bar extreme, EOD or 10R), ORB follow (15m/60m ranges; exits EOD,
   prev_day ...), ORB fade, Judas sweep (open and pre-open), open-hours mean reversion - 84 cells +
   15 filter cuts - 0 of 84 cells with t > 0 (best t -0.81); Zarattini first-bar replicates GROSS
   (zero-cost PF 1.12-1.17 on n ~4-5k each) and is fully consumed by 0.6/2.0/0.4 pts; rescue filters:
   rvol top quintile (>= 1.29/1.27) makes SPX/NDX worse; gap-aligned vs gap-against best t +0.48
   (against folklore); honest OOS top-10 median 0.886 vs population 0.945 - DEAD (real gross, dead net).
8. **Asia-session (01:30 UTC) ORB transplanted to SPX/NDX** - r16A - SPX/NDX 5m - 60m range from
   01:30 UTC, first 60m close beyond, stop 2x, exits {London open ~08:00 UTC, NY open ~14:30 UTC},
   gates {none, realised-vol tercile, VIX level}; plus derived fade - 12 + 6 cells - breakout t to
   -12, fade t to -9.7, both halves; away-session chop taxes both directions - DEAD (slow-session
   structure is gold-specific).
9. **London-open (08:00 London) ORB on gold** - r12 - XAUUSD - exact Asia construction moved to
   08:00 London: 60m range, first 60m close beyond, corr gate on/off, stop on/off, exit 16:00 NY -
   4 cells - PF 0.82-0.91 both halves - DEAD (price-discovery gradient Asia works / London dead / NY
   dead).
10. **HSI home-session range (09:30-10:30 HKT)** - r15b H-B - HK33/HK50 15m - 60m range, first 60m
    close beyond, breakout arm AND fade arm, stop 2x, flat 16:00 HKT; cost 10 pts - 2 cells + H-C
    correlation gates (Nikkei/A50/HSCEI/CSI300, 20d, lag-1) - break PF 0.868 t -1.11, fade 0.755
    t -2.84; gates rescue nothing (best t -0.19) - DEAD (home-session fast discovery).
11. **Unger previous-session breakout on JP225** - r16 I - JP225 - dead raw (t -2.58); "profits live
    in mined filters" - DEAD.
12. **edgeful 5-minute ES ORB claim** - r23 - ES proxy (SPX 5m) 20 yrs - 09:30-09:35 range, by-close
    entry, opposite-edge stop, 50%-range target; "no Tuesdays" variant; rolling 6-month windows -
    win rate 74% gross reproduces their 72.17%; expectancy -0.06 pts gross / -0.66 net; no-Tuesdays
    makes it worse; net of one tick the median 6-month window is -$3,663 - DEAD (cost-blind claim).
13. **TradeAlgo NQ 30m ORB claim (74.5% WR / PF 2.51)** - r32b - NDX 5m 2005-2025 - RTH 09:30-10:00
    range, first break, entry {touch, close-beyond} x target {1.5x, 2x, none/EOD 15:55} x filter
    {none, overnight-gap-align}; house 2.0 pts + zero-cost - 14 cells - WR 37.9-47.1%, PF 0.87-1.04,
    best t +0.94 at ZERO cost; the claimed WR/PF pair is arithmetically impossible from its own
    geometry - DEAD (manufactured/folklore claim).
14. **Zarattini/Concretum noise-area intraday momentum** - r28 #6 - SPX/NDX/RTY 5m RTH + XAU port
    (01:30 UTC session open, flat 16:00 NY) - sigma(t) = 14-day mean |open->t| per minute-of-day;
    bands open x (1 +/- sigma(t)) gap-adjusted; entries only at HH:00/HH:30 beyond a band; trail
    max(band, session VWAP) at 30m marks; flat at close; reversals allowed; costs x0/x1/x2 - SPX
    gross PF 1.148 t +3.28 (direction consistent with the paper); at CFD costs all four dead (PF
    0.88-1.05); 2x costs t -6.5 - DEAD net (a futures-cost re-run was noted as the one legitimate
    follow-up; never run).
15. **ORB repaired by participation gates (Attempt 1, r42a)** - SPX/NDX/RTY/GOLD 5m, micro costs -
    OR window W {15, 30, 60} min x gate {none; RVOL30 >= 1.5 vs 20-day mean; |gap| >= 0.5 x ATR20d;
    NR7} x stop {opposite OR level; 0.5 x OR range} x target {2 x OR range; none/EOD}; stop order at
    the level, first break after window, both-levels-in-one-bar days skipped - 48 IS variants - gap
    gate occupied all top-8 IS slots (t to +3.33, halves [+,+], smooth); selected W60/gap/half-range
    stop/EOD; OOS pooled n 960: avgR +0.014, PF 1.10, t +0.93, halves [+,-] (SPX +0.027 / NDX +0.011 /
    RTY +0.022 / GOLD -0.019) - **BURNED-OOS** (gap-day participation is a weak real tilt, too small to
    clear the bar; may reappear only as a filter inside a differently-motivated family).
16. **Gold first-bar (Zarattini 09:30-bar) direction entry at the Asia open** - r8 D - 5m/15m bar,
    stops at bar extreme / 0.10 / 0.25 x ATR; filtered and unfiltered - 12 cells - PF 0.66-0.98
    unfiltered, filtered at best breakeven, 8/12 halves disagree - DEAD.

### 2.B Session transition / pre-open auction / futures-before-cash

17. **HSI pre-open push fade (H-A)** - r15b - HK50/HK33 15m spliced 2022-02..2026 (two brokers,
    3.1 bps splice) - push = 09:15->09:30 HKT bar return / ATR14; fade at the 09:30 cash open when
    |push| >= {0.3, 0.5} x ATR14; stop {0.5, 1.0} x pre-open range beyond its extreme; exits {10:30,
    12:00, 16:00 HKT}; cost 10 pts (5/15 sensitivity) - 12 economic cells + descriptive (rho push vs
    next hour -0.059, quintile gradient +6.4/+8.1/-6.3/-8.4/-6.5 pts; NOT a day-direction signal, rho
    -0.024 to close) - frozen cell |push| >= 0.3, stop 0.5x, exit 16:00: n 43, PF 2.02, t +1.60, both
    halves positive in every cell, max-stat p 0.030, cost-robust to 15 pts - **WATCH #3 / paper streams
    MHI (CFD) and MHIF (true HSI futures via IBKR, from 2026-08-19)**; re-test bar 80+ trades, promote
    PF >= 1.4 with both halves positive, no parameter may move. Fidelity caveat (2026-09-03): the
    HK33 CFD has NO auction print (its 01:15Z bar is a synthetic broker open, push ~0.72x the
    futures'); at the frozen threshold CFD and futures triggered on DISJOINT sessions (0 common of
    5-6), so the archived 43-trade evidence measured the CFD's synthetic open; MHIF is the promotion
    evidence. MHIF after 6 trades: LLR -1.50 (four stops), trending toward the kill line.
18. **JP225 pre-open fade (mechanism transfer)** - r18A - JP225 1m 2011-2020 + 5m 2024-26 - push =
    23:45-00:00 UTC (08:45-09:00 JST futures-before-cash), |push| >= 0.3 x ATR14, fade at 00:00 UTC,
    stop 0.5 x pre-open range, hold to 07:00 UTC; continuation arm also run - PF 0.42 / t -3.56,
    continuation also negative - DEAD (the futures-before-cash reversal does not generalise; HSI item
    stands on its own numbers only).
19. **Nikkei open conditional on prior-day SPX** - r16F - JP225 1m 2005-2020 - prior-day SPX return
    terciles -> fade JP225 at Tokyo open on extreme prior-SPX days, hold 30m - 2 cells + descriptive -
    rho -0.097 p < 1e-4 replicates; inside the spread - DEAD net (descriptive only).
20. **Asia-close risk tone -> US RTH (Attempt 15, r42o)** - SPX/NDX/RTY - JP225 and HSI session
    returns (cutoff 08:00 UTC HK cash close) must agree; direction = common sign; filter {any; both
    |ret| >= 0.5 x own 20d sigma}; hold {09:30->12:00, 09:30->close} - 4 cells - first run "passed"
    absurdly (IS t +21.4) from a 24h-feed date-group LOOKAHEAD; corrected: best -0.008R, leans fade -
    **BURNED-IS** (lookahead caught; honest version null).
21. **ICT CISD reversals (Venom / Silver Bullet / TJR windows)** - r10 - XAU/SPX/NDX/RTY 5m - break
    of an opening range then entry AGAINST the break on a close back through the open of the driving
    candle run (<= 5 bars), stop at session extreme, first break side only; windows: Venom OR
    08:00-09:30 ET traded to close; Silver Bullet 09:00-10:00 range traded 10:00-11:00 and to-EOD; TJR
    = NY AM vs London-session levels; targets 2R / OR-opposite / EOD; corr overlay on gold - 72 cells
    incl. Supertrend - dead net everywhere; TJR is the 4th independent session-sweep construction to
    fail; the one gold cell Silver-Bullet-to-EOD/EOD PF 1.068 t +0.52 zero-cost 1.20 (shorts PF 1.247
    post-hoc) - **DEAD except playbook WATCH #1** (gold CISD-to-EoD; re-test when 2026 gold data
    accumulates; fails both-halves today).
22. **Judas sweep / killzone sweep-reclaim on gold** - r8 - XAUUSD 5m - daily-structure bias (sma20,
    mom20, PDH/PDL 4-scenario) -> session-open counter-bias sweep of causally-tracked unswept levels
    -> first 5m close back through = entry, stop beyond sweep extreme, one trade/session; sessions
    asia/london/ny + canonical killzones ldnkz 02:00 ET / nykz 08:30 ET; targets 1R/2R/3R/opposite/
    session_end; sweep windows 60/120/240 min; stops x1.0/1.5/2.0 and at-the-level; min sweep depth
    $0/0.5/1/2 - 45 + 12 + variations (~100 tests) - loses at ZERO cost (PF 0.735 gross, London cell
    -$0.38/oz); grid median PF 0.613; honest OOS median 0.201 with two Asia cells at 0.000; win rate
    27.1% at 2R matches the one independent mechanical ICT test (29.6%) - DEAD (adverse selection).
23. **Index Judas sweeps (open and pre-open)** - r9 (inside item 7) - SPX/NDX/RTY - PF 0.79-0.81,
    t -1.6..-3.9 - DEAD.
24. **Sweep-failure (FP6) at RTH levels** - r33 Phase 4a - SPX/NDX 5m 2005-2025, RTY 2005-2020 -
    levels PDH/PDL, ONH/ONL, OR30 H/L; first breach per level per session; failure = 5m close back
    inside within 6 bars; fwd 30m/EOD reversal return; TRADE (PDH/PDL/ONH/ONL): enter failure close
    toward reversal, stop at sweep extreme, EOD exit - 18 descriptive + 12 tradeable cells, ~36k
    events - 54-80% of breaches close back inside (the folklore base rate) worth +0.3..+1.6 bps gross
    at 30m (best t +2.16 on 18 cells, dead under max-stat); all 12 trade cells lose net (PF 0.79-0.99,
    WR 17-23%, halves both-negative 9/12) - DEAD (stop-at-the-extreme geometry gets run by the same
    noise). FP6 demoted to on-chart context.

### 2.C Clock-window drift / session-concentration families

25. **Gold session-clock split (Asia LONG / London SHORT) (Attempt 7, r42g)** - XAUUSD 5m, cost
    0.35/leg, ATR20(24h)-normalised - legs {Asia long only; London short only; both} x windows
    {A: Asia 19:00-03:00 ET, London 03:00-11:00 ET; B: Asia 20:00-02:00, London 03:00-10:00}; enter
    first bar open in window, exit last bar close - 6 cells - IS best (B London short) avgR +0.010
    t +0.56; OOS avgR -0.034 t -1.23 halves [-,-] - **BURNED-OOS** (the celebrated Lucey/O'Connor
    clock split barely exists 2020-24; the shot was spent on an IS-null spec, which produced the
    IS t >= 2 floor amendment). Gold "Asia premium on 2012+ data" refused later as adjacent (r56).
26. **London PM fix windows on gold (Attempt 36, r55)** - XAUUSD m15 2012-2022 + 5m 2020+ spliced -
    S1 SHORT 09:00->10:00 ET; S2 SHORT 09:30->10:00; L1 LONG 10:00->10:30; L2 LONG 10:00->11:00;
    diagnostics = same shapes shifted -2h (07:00-08:00, 07:30-08:00, 08:00-08:30, 08:00-09:00); cost
    0.35 - 4 + 4 cells - ALL eight cluster at avgR -0.024..-0.033, t -4.4..-9.9 (flat-cost signature:
    gross ~0 in every 30-60 min window either direction) - **BURNED-IS**. Calibration on record: on
    gold at 0.35/RT any sub-hour window family needs |gross| > ~0.025R/day.
27. **Overnight-drift window (European open) on indices (Attempt 6, r42f)** - SPX/NDX/RTY 5m (24h
    CFD), GOLD diagnostic, micro costs - LONG windows {01:00-04:00, 02:00-03:30, 02:30-03:30 ET} x
    filter {all; prior 24h return < 0}; enter first bar open, exit last bar close - 6 cells - all
    IS-negative; narrow 02:30-03:30 worst (avgR -0.022, t -17.4, gross ~ -0.016R) - **BURNED-IS**;
    r43 cross-checked vs TRUE CME ES (IBKR, 70 sessions): euro-open mean ES -0.95 bps vs CFD -0.87,
    diff t -0.10, corr 0.859 -> CFD overnight feeds exonerated; the inverted drift is real market
    behaviour (post-publication inversion). Mirror (short the euro open) deliberately not registered.
28. **Full overnight close-to-open premium (Attempt 29, r49)** - SPX/NDX/RTY, micro - LONG prev
    15:55 close -> 09:30 open, scope {all sessions; adjacent-only (excl. weekend/holiday holds)};
    diagnostic DAY 09:30->close - 2 + 2 cells - night-minus-day +0.018R/day in the documented
    direction (day cells t -2.9/-2.5 net) but a daily RT cost ~0.02R leaves night at -0.002R
    (t -0.38) - **BURNED-IS** (cost-dominated). Precursor r30 (daily data): SPX overnight +2.3 bps/day
    t +2.30, NDX +3.8 t +3.47, halves same-sign GROSS; SPX at 2 bps RT = 1.00x over 21 years; MU
    11.6x gross vs 16.9x B&H, edge entirely 2023-26.
29. **Late-day intraday momentum, Gao-Han-Li-Zhou analogue (Attempt 2, r42b) and its mirror
    (Attempt 2b, r42c)** - SPX/NDX/RTY/GOLD 5m, micro - predictor P {first-30m return 09:30->10:00;
    day-so-far 09:30->15:00; both-agree} x entry {15:00 close -> session close; 15:30 close -> close}
    x filter {none; |P| >= 0.25 x ATR20d}; direction sign(P), then MINUS sign(P) - 12 + 12 cells -
    momentum t -4.2..-11.8 halves [-,-]; reversal t -5.7..-17.0 halves [-,-]; decomposition
    net_mom + net_rev = -2 x cost -> cost ~0.021-0.026R, GROSS late-day serial dependence ~ +0.008R -
    **BURNED-IS both directions** (a decayed momentum remnant smaller than one RT; the r34 NY-PM
    displacement watch hypothesis overlapped this window and was disclosed).
30. **Intraday momentum, last half-hour (Gao r1 / Baltussen rest-of-day)** - r15 F1 - SPX/NDX/RTY
    5m 2005-2025 - r1 = prior 16:00 close -> 10:00 ET incl. gap; rod = prior close -> 15:30; at 15:30
    take the sign into the close; slices all / high-vol / low-vol (10d realised vol vs rolling median)
    - 18 cells - negative everywhere (SPX gao t -3.84, NDX -8.81); worst on low-vol days; the one
    literature-sign cell (RTY rod hivol) flips between halves - DEAD (sign-flipped, not decayed).
31. **VIX term-structure-gated noon dip-buy (Attempt 9, r42i)** - SPX/NDX/RTY, micro - dip = open ->
    12:00 return <= -k x ATR20(RTH), k {0.3, 0.5} x gate {none; contango VIX/VIX3M <= 0.95;
    backwardation >= 1.0}; buy 12:00 close, exit session close - 6 cells - all below floor; contango
    cells MORE negative than ungated (-0.031/-0.054R vs -0.024/-0.037R); afternoon continuation of
    morning weakness dominates - **BURNED-IS** (mechanism sign-check refuted).
32. **Gold 08:30 ET macro-impulse continuation (Attempt 10, r42j)** - XAUUSD 5m, cost 0.35 - impulse
    window {08:30-08:35, 08:30-08:45} x |impulse| >= {0.15, 0.25} x ATR20(24h) x hold {30m, 60m, to
    11:00}; direction = impulse sign, enter at window-end close - 12 cells - best +0.029R t +0.61 n 88
    - **BURNED-IS** (price-only surprise proxy carries no continuation; needs true surprise data ->
    attempts 17/18).
33. **Corr-regime conditional London -> NY gold continuation (Attempt 13, r42m)** - XAUUSD 5m,
    FRED daily AUD for the gate - regime {corr <= 0.5 follow; corr > 0.5 fade} x London move
    (03:00->08:00 ET) threshold {any; >= 0.25 x ATR20} x hold {09:30->12:00; 09:30->16:00}; entry first
    RTH bar close - 8 cells - all flat-to-negative (best +0.003R t +0.06); no regime separation -
    **BURNED-IS** (the corr gate governs the Asia-open breakout and nothing else found).
34. **SGE AM-fix drift** - r17a - XAUUSD 5m - mean 5m returns per slot 01:00-07:00 UTC; named windows
    30 min INTO and 30 min AFTER the 02:15 and 06:15 UTC auctions - 2 cells + control - into-AM-fix
    +0.76 bps/day t +2.56 halves +0.43/+3.25, SUB-COST (~$0.25/oz vs $0.30); PM fix and controls
    nothing - MONITOR (re-scored yearly; economics only if drift doubles).
35. **SGE auction-candle direction trade** - r26/r26b - enter 02:30 UTC in the 02:15-02:30 candle
    direction, flat NY close; magnitude quintiles by |candle|/ATR14; costs spot $0.60 / MGC $0.25 /
    zero - gross +$0.70/oz PF 1.105; net +$0.10 PF 1.015 t -0.04; 2020-23 net negative; hit rate 50.8%;
    magnitude gradient is a hump (-0.69/-0.47/+0.98/+0.94/-0.06 $/oz); ZERO-cost t +1.22 - DEAD
    (unmonetisable at one trade/day).

### 2.D Event release / calendar families with clock-anchored legs (indices unless stated)

36. **Macro-surprise post-announcement drift (Attempt 17, r44)** - SPX/NDX/RTY 24h 5m frames, GOLD
    diagnostic, micro; FXStreet consensus/actual 2013-2026 - event set: NFP, GDP, Retail Sales
    (+control), ISM Mfg, ISM Services, Durable Goods (equity-positive-on-beat); CPI YoY/MoM/core
    YoY/MoM (negative-on-beat); surprise = ratioDeviation; |dev| {0.5, 1.0} x hold {entry+60m; to
    16:00}; entry first 5m close >= release+5 min (08:30 releases enter pre-market 08:35; 10:00
    releases included) - 4 cells (861 events) - all under floor (best -0.002R); growth surprises
    negative in all 4 cells (2022+ good-news-is-bad-news), inflation positive in all 4 (+0.024..
    +0.045R) - **BURNED-IS**; WATCH #4 = CPI-surprise equity fade (direction -sign(dev), release+5m,
    hold to close, ~12-20 events/yr).
37. **Gold vs CPI surprise (Attempt 18, r44b; re-scored r54)** - XAUUSD, cost 0.35 - direction
    -sign(dev), |dev| {0.25, 0.5} x hold {+60m, to 16:00 NY}, entry release+5m - 4 cells - 2020+
    n 32-34 leans right (WR to 65.6%, PF to 1.35) but t <= 0.57 -> WATCH #5; extended 2013-2026 (n 112)
    primary cell avgR +0.051 PF 1.34 t +0.70 halves [-,+] (2013-19 NEGATIVE); +60m holds negative -
    **WATCH #5 DOWNGRADED** (era-specific to the post-2020 inflation regime).
38. **Announcement-day / NFP premium (Attempt 11, r42k)** - indices, micro - NFP (first Friday):
    holds {prior 15:55 -> NFP 15:55; NFP 08:00 -> 12:00; NFP 09:30 -> 15:55} vs other-Friday control;
    FOMC-DETECTED days (14:00-14:30 range >= 2.5/3.5 x 60d median) x holds {prior 14:00 -> 13:55;
    09:30 -> 13:55} - 7 cells - NFP close-to-close +0.029R t +0.72 (faint), intraday harvests
    negative; FOMC-detected -0.24..-0.56R t to -10.7 = conditioning on FUTURE vol (leverage effect) -
    **BURNED-IS** (NFP arm stands; vol-detected event sets ruled INVALID).
39. **FOMC pre-announcement drift, ex-ante calendar (Attempt 12 revived r43b; repair Attempt 34,
    r53)** - SPX/NDX/RTY pooled, 2013-2026 verified calendar (190 events), micro - original cells:
    prior-day 14:00 -> 13:55 (+0.051R t +1.27 PF 2.29); 09:30 -> 13:55 (-0.101R, t -3.29, significantly
    NEGATIVE); prev 15:55 close -> 15:55 close (+0.114R t +1.82 PF 1.72) -> WATCH #3 (later retired).
    Repair (class #7 horizon match): C1-ON prev 15:55 -> 09:30 open; C2-PM 13:55 -> 15:55 (through the
    statement); C3 ON+PM two legs; placebo = same windows 7 calendar days earlier - IS C1-ON n 190
    WR 62.1% PF 3.22 avgR +0.124 t +4.34 halves [+,+], placebo ON +0.033 (rejected as generic
    drift); OOS n 64 WR 57.8% PF 1.40 avgR +0.056 t +1.20 halves [+,+], all three instruments positive,
    cost x1.5 +0.052 - **BURNED-OOS -> WATCH #10 (FOMC-night long)**; the FOMC RTH-morning cell
    (09:30->13:55) is a recorded NEGATIVE.
40. **Treasury 10Y/30Y auction-day windows (Attempt 26, r48)** - SPX/NDX/RTY, GOLD diagnostic,
    micro; TreasuryDirect calendar 2005+ - W1 SHORT 09:30 -> 13:00 (concession); W2 LONG 13:00 ->
    close (relief); W3 LONG 13:00 -> next-session close; x {10Y, 30Y}; 2Y diagnostic - 6 + 3 cells -
    both arms significantly WRONG-WAY (concession-short t -2.63/-2.48; relief-long t -2.41): auction
    days rallied INTO 13:00 and faded after; 2Y shows the same PM fade (t -2.59) so not duration-
    specific; mirror forbidden - **BURNED-IS**.
41. **Auction-outcome direction (bid-to-cover surprise) (Attempt 27, r48b)** - same data - z =
    (btc - mean prior 8 same-bucket) / std; |z| {0, 0.5} x hold {13:05 -> RTH close; 13:05 -> next
    close}; entry first 5m bar >= 13:05 - 4 + 4 cells - following the surprise LOST (widest cell
    -0.039R t -2.52, halves [-,-]); 2Y flat - **BURNED-IS**.
42. **Options-expiration week (Attempt 19, r45)** - SPX/NDX/RTY, GOLD diagnostic, micro - W1 LONG
    opex-week Mon open -> Fri close; W2 LONG Wed close -> Fri close; W3 SHORT post-opex Mon open ->
    same-day close; W4 SHORT post-opex Mon open -> Wed close; x scope {all monthly, quarterly
    witching} - 8 cells - IS quarterly W1 n 170 WR 63.5% PF 2.08 t +5.93 (monthly t +3.92); OOS n 56
    PF 1.11 t +0.14 halves [-,+] - **BURNED-OOS** (Stivers-Sun premium decayed post-2020); side
    finding: post-opex Monday was IS significantly UP (shorting it lost, t -3.73).
43. **Expiry-day strike pinning via round levels (Attempt 22, r45d)** - indices, micro - on monthly
    opex Friday at 15:00 ET, if price within thr {0.1, 0.2} x ATR20 of nearest round level (grid G =
    SPX 25 / NDX 100 / RTY 20 pts, and G/2), trade TOWARD it, exit 15:55; non-opex-Friday diagnostic -
    4 + 4 cells - all flat-to-negative (best +0.010R t +0.28); non-opex identical - **BURNED-IS**
    (refutes the round-level proxy, not pinning per se; revival needs OI-by-strike data).
44. **Pre-holiday premium (Attempt 20, r45b)** - indices, micro - LONG {H1 open -> close; H2 12:00 ->
    close; H3 prior close -> close} x {all pre-holiday sessions (only full-closure holidays, ~3/yr
    detectable on CFD feeds); big-3} - 6 cells - H3 +0.010R t +0.17; H2 12:00->close t -2.22 both
    halves negative - **BURNED-IS**.
45. **Turn-of-month** - r15 F2 (McConnell-Xu; Etula T-3..T+2 windows; SPX/NDX/RTY daily from 5m):
    held days earn the all-days mean (SPX +4.3-5.8 bps vs +4.0) - DEAD; **Attempt 21 (r45c)** LONG
    {T1 last-day open -> +3rd close; T2 last-day open -> +1st close; T3 T-1 close -> +3rd close} x
    {all months; quarter-end} - IS quarter-end T3 PF 1.57 t +2.48; OOS n 55 PF 1.09 t +1.07 halves
    [+,+] all instruments positive - **BURNED-OOS -> WATCH #6** (quarter-end TOM long).
46. **Conditional month-end rebalancing fade (Attempt 14, r42n)** - indices, micro - MTD return
    (09:30 open of month -> close of T-3); trigger |MTD| >= {1.5%, 3%}; direction -sign(MTD); entry
    {T-3 close, T-2 close}; exit month-end close - 4 cells - IS all positive t +1.8..+2.8; OOS
    +0.040R PF 1.26 WR 52.2% n 136 t +0.61 - **BURNED-OOS -> WATCH #2** (thr 1.5%, entry T-2).
47. **Day-of-week (Attempt 32, r51)** - indices, micro - {Monday SHORT, Friday LONG} x {open->close;
    close-to-close}; Tue-Thu diagnostic - 4 + 2 cells - Monday-short lost (cc t -2.12, Mondays drift
    UP); Friday-long worst cell (oc avgR -0.059, t -4.05: Fridays systematically weak intraday) -
    **BURNED-IS**. (Note: "Friday intraday is weak" is a recorded negative for the Friday
    open->close cell.)
48. **FOMC-cycle even weeks (Attempt 24, r46b)** - indices 2013+ - LONG scope {week0 days 0-4; week2
    10-14; even} x hold {RTH open->close; prev close->close}; odd-week diagnostic - 6 + 4 cells -
    even cc +0.032 t +1.75 vs odd +0.031 t +1.59 (no distinction); week0 intraday NEGATIVE t -2.33 -
    **BURNED-IS**.
49. **Pre-FOMC drift (r15 F6)** - dropped a priori 2026-08 (documented dead 2015-19) before the
    ex-ante calendar existed; superseded by 39.

### 2.E Gap families

50. **Opening gap fill on SPX/NDX** - r15 F5 - gap = 09:30 open vs prior 16:00 close in buckets
    {0.05-0.2%, 0.2-0.5%, > 0.5%}; enter 09:35 close toward the fill, target prior close, stop 2x gap,
    time exit 12:00 - 6 cells - fill rates replicate (small 82-87% mostly by noon; large 34-40%); fade
    loses in every bucket (SPX small -2.70 bps t -5.81; NDX small -8.42 bps t -14.07) - DEAD (no-fill
    days are the trend days).
51. **Overnight gap fill vs continuation by size (Attempt 5/5b, r42e)** - SPX/NDX/RTY/GOLD 5m,
    micro - |g|/ATR20d bucket {small 0.1-0.3; mid 0.3-0.7; large >= 0.7} x {FILL: side -sign(g),
    target prior close; CONT: side +sign(g), target entry + |g|} x entry {09:30 open; 10:00 close,
    skipped if target already touched} x exit {target w/ EOD backstop; EOD}; stop 0.5 x ATR20d - 24
    cells - IS: small/mid negative both directions (small-FILL least bad -0.011..-0.023; small-CONT
    t -8.1); large-CONT positive 4/4 (best entry 10:00/EOD +0.036R t +2.08 PF 1.03); OOS large-CONT
    n 596 avgR +0.002 t +0.08 PF 0.99 halves [-,+] - **BURNED-OOS** (both directions, all sizes).
    Residue: small-gap fill exists as a tendency under costs; large-gap continuation was real
    2005-2020 and is gone.
52. **Gap-alignment filters on ORB / first-bar** - r9 (gap aligned vs against bar), r32b (overnight-
    gap-align filter on NQ ORB), r1 (overnight gap as a confluence filter on the Asia ORB; 0.82 then
    1.95 across halves) - all noise/inverted - DEAD as filters.

### 2.F Pattern / structure families (sweeps, imbalances, candle patterns, indicator recipes)

53. **Fair value gaps and inversions (27A)** - r27 - XAU (00:00-04:00 UTC formation) / SPX / NDX /
    RTY (09:30-10:30 ET formation), TFs {15m, H1}; continuation (first retrace touch into the 3-bar
    imbalance zone, stop beyond far edge, flat session end) and inversion (close through the far edge,
    stop at near edge) - 16 cells (12 runnable) - zero pass; several significantly negative (NDX 15m
    inversion t -8.21; SPX -2.8/-2.9); XAU 60m continuation PF 1.336 halves 0.712/1.827 - DEAD
    (imbalance family 0-for-7+; the RTY-iFVG mirror "fade" noted and deliberately un-run).
54. **Ping-pong and magnet (Asia-range lines)** - r14 - XAUUSD 5m - lines from the 09:30-10:30 HKT
    range; ping-pong: fade the first tap toward the other line, target other line, stop 0.5x/1.0x
    range beyond the tapped line, flat 16:00 NY, splits calm (|3d ret| <= median) / stand-aside
    (corr > 0.5); magnet: line within 0.10% of prior HKT-day or NY-session H/L, revert-to-line fade
    triggers 0.5x/0.75x width; control non-confluent - 13 cells - tap statistic real (64%; 67-68% calm/
    stand-aside; gradient jagged 68..66%) but every fade loses (best calm+stand-aside PF 1.102 t +0.54
    best-of-8); confluent lines re-crossed 5.43x = non-confluent 5.43x; magnet fade PF 0.75/0.64 -
    DEAD (base rate owns the pattern).
55. **Supertrend + RSI (TradingView script)** - r10 - XAU/SPX/NDX/RTY 5m - ST(10, 2.0/3.0) with RSI
    55/45 and 60/40 crossings, as written (inverted: Pine's ta.supertrend direction -1 = uptrend) and
    as intended; trailing stop on the line - 24 cells - loses BEFORE costs on every market (zero-cost
    PF 0.68-0.95), t to -52 on 33k-trade samples - DEAD with prejudice.
56. **Crabel NR7 / ID-NR4 next-day breakout** - r28 #2 - XAU/SPX/NDX/RTY daily patterns, intraday
    execution: stop entry 1 tick beyond the pattern-day extreme, stop at opposite extreme, exit
    same-day close; same-day double trigger resolves to STOP - 8 cells - all 8 PF > 1 (1.09-1.41, NR7
    SPX t +2.52) but published 60-76% win rates measure 26-30%; sub-bar "consistent-but-thin" - not
    deployable; logged (not a watch item).
57. **Momentum Pinball** - r28 #7 - XAU + SPX - RSI(3) of ROC(1) daily < 30 -> next-day buy stop
    above FIRST-HOUR high, stop first-hour low, exit next close (> 70 mirrored) - XAU PF 1.18 t +0.89,
    SPX 0.93 - DEAD (noise).
58. **Hikkake (Chesler + 50-EMA trend filter, 10-bar time exit)**, **Holy Grail (ADX14 > 30 rising,
    20-EMA pullback, H1 SPX PF 0.583 t -2.75)**, **TTM Squeeze (BB20/2 inside KC20/1.5 >= 5 bars,
    XAU/SPX H1 PF ~1.0)** - r28 - DEAD at frozen published parameters.
59. **pinescriptforge 12 RTY "audited" strategies** - r29/r29b - RTY 1H (and 15m/4H/D) 2005-2020 +
    2025-03..2026-04 TopstepX - all 12 lose (PF 0.63-0.91, every t negative); ZERO-cost PF 0.95-1.02;
    15m cells t to -30 - DEAD (manufactured claims).
60. **ALMA averaging grid (RTY 6H)** - r31 and **ALMA naked-signal repair (Attempt 8, r42h)** - 6H
    bars from 24h 5m feeds - r31: WR 76.3% reproduces mechanically, PF 1.10, halves 0.89/1.32, drift
    null p 0.76; attempt 8: close crosses above ALMA(50, .85, 6) with slope > 0 over s {4, 8} x gate
    {none; ATR14/ATR56 <= 1} x exit {time 6 bars; 2xATR14 stop 12-bar cap}, long only - 8 cells, best
    IS t +0.11 - **BURNED-IS** (null signal; not strictly intraday, listed for completeness).
61. **Turtle Soup daily on JP225** - r16G/r17c - PF 4.01 t +3.38 on 2016-2026 (n 33), max-stat p 0.027
    -> RETRACTED same day: 2005-2016 PF 0.579 t -0.80 - RETRACTED (era-specific; daily family).

### 2.G Mean-reversion band / value-area / relative-value families

62. **2.6-sigma pullback (band fade)** - r8 - XAUUSD - rolling-mean/SD bands (n = 20), band width
    {1.5, 2.0, 2.6, 3.0, 3.5} sigma x TF {5m, 15m, 60m} x trigger {close_out (first close beyond),
    close_back (close back inside)}; sessions asia/london/ny; gates ADX(14, 1h) < / >= 20/25/30;
    excursion length 1 / 2-3 / >= 4; news-window scrub (08:30/14:00 ET); NY-anchored VWAP bands
    k 2.0/2.6; costs $0/0.15/0.30/0.60 - ~90 cells - zero-cost PF 1.006 (reversion = exactly one
    spread); net PF 0.860; only n <= 250 tails at 3.5 sigma clear 1.0 (spikes); no gate finds a paying
    subset; honest OOS top-5 0.959 vs pop 0.835 - DEAD (spread-sized effect).
63. **Open-hours mean reversion on indices** - r9 - SPX/NDX/RTY - PF 0.66-0.73, t -10.9..-16.3 - DEAD.
64. **Volume-profile value-area reversion with absorption gates** - r11 - XAU/SPX/NDX/RTY 5m -
    profile windows {prior RTH, overnight, prior 24h}; 70% value area from POC; breakdown through an
    edge on declining volume, reclaim on growing volume (absorb+grow gates vs none); stop at extreme;
    targets {POC, opposite edge, EOD} - 72 cells - population median OS 0.990, not deployable; gates
    improve the raw fade on nearly every market (NDX 1.08->1.21, RTY 0.88->1.02, SPX 0.88->1.03); the
    ONLY both-halves survivor: gold, overnight profile, gated, opposite-edge target PF 1.045 (IS 1.065 /
    OS 1.026, t +0.31, n 271) - **DEAD except playbook WATCH #2**.
65. **Market Profile "80% rule"** - r28 #8 - SPX + XAU 5m - prior-session 70% volume value area; open
    outside VA; two consecutive 30m closes back inside -> enter at VA edge toward far edge; target far
    edge; stop 0.25 x VA width; flat session end - conditional fill rate 46% (SPX, n 1,186) / 32% (gold)
    vs claimed 80%; trade PF 0.995 / 0.907 - DEAD (busted claim).
66. **SGE auction-hour value zone** - r26 C - see item 35 - fade edges of the 02:15-03:15 UTC range
    to mid, stop 0.5 range, flat NY close: PF 0.625 t -7.49 vs control hour 0.733 - DEAD
    (anti-mean-reverting launch pad).
67. **Gold/silver one-session RV convergence (Attempt 16, r42p; repair Attempt 35, r53)** - gold 5m +
    XAGUSD H1 2016-2026; pair cost 4 bps RT - daily spread s = r_gold - r_silver (16:00 ET closes);
    |s_yesterday| >= k x sigma20, k {1.0, 1.5, 2.0}; convergence next NY RTH 09:30->16:00 / close->close;
    repair: hold H {1, 3, 5} sessions, k {1.0, 1.5}, sub-threshold diagnostics - 6 + 6 cells - all
    flat-to-negative (best -0.12 bps t -0.30; gross ~ +3.9 bps vs 4 bps cost); H=3 gross flat vs H=1 -
    **BURNED-IS, repair exhausted** (holdout sealed and unreachable).
68. **Connors RSI(2)/IBS daily mean reversion** - r16B/E - SPX/NDX/RTY, HSI/JP225/AUS200 daily -
    raw SPX IBS PF 1.62 t +3.54 but the random-long-burst drift null yields t +2.86 median (p 0.125) -
    DEAD (drift in bursts; daily family, listed because the "buy the close, sell in N days" chassis is
    the same one the regime families use).

### 2.H Momentum / continuation / displacement families

69. **FP5 displacement continuation (the longest-running gross-real/net-dead thread)** -
    r33b / r34 / r37 / r37b / r38 / r39 / Attempt 4 - SPX/NDX/RTY (2005-2025/2020) + GOLD, 15m RTH bars
    (and 1H, 5m variants) - signal: TR >= k x ATR14 (k 1.5 frozen; 1.5/2.0/2.5 in attempt 4) with
    body >= 0.6 x range, direction = bar direction; measured: next-4-bar signed continuation vs
    control (r33b: NDX +2.4 bps/h t +4.33, SPX t +2.43, RTY nothing; net 4-bar hold SPX -0.33 pts
    t -2.56, NDX -0.62); per-session (r34: NY PM NDX +4.1 bps/h t +3.07, SPX t +1.9, RTY t +1.4 -
    "afternoon displacement continues" logged as WATCH HYPOTHESIS only, never registered); TP +10 x
    SL {5, 10, 20, none} scalps at house/micro/zero cost (r37/37b: micro best-case 1 of 48 positive =
    SPX disp SL5 +0.17 pts t +2.32, siblings negative; zero-cost SL5 positive everywhere: SPX +0.52
    t +7.1, NDX +0.42 t +5.7, RTY +0.22, GOLD +0.20); 50%-retrace LIMIT entries at 15m->5m, 15m->1m,
    1H->15m (r38: adverse selection - zero-cost per-fill SPX -0.36, NDX -1.08, RTY -0.25, GOLD -0.26;
    fill rates 37-44% / 10-15%); HTF bias gates 1H/4H/D (r39: best SPX gate-1H SL5 +0.15 t +1.6 vs
    ungated +0.17); first 1H-aligned 5m displacement per session held to close (r39c: SPX +0.04 t +0.13,
    NDX +1.30 t +1.14, RTY 0.00, GOLD -0.09); magnitude/horizon repair (Attempt 4: k {1.5, 2.0, 2.5} x
    signal window {before 14:00, before 11:30} x stop {none, 1x range} x exit {EOD, 8 bars}; IS
    k-gradient monotone, k2.5 t +2.47 halves [+,+]; selected k2.5/before 14:00/1x/8-bar; OOS n 1329
    avgR -0.003 PF 0.95 t -0.28 halves [-,+], cost x1.5 negative) - **BURNED-OOS** (real gross drift
    ~0.2-0.5 pt/trade, smaller than one honest round trip, destroyed by passive entries; only fill
    engineering could attack it and that is untestable on OHLC).
70. **Metals margin-cascade continuation (Attempts 37 gold, 38 silver; r55b/r56)** - gold 2012+
    spliced; XAGUSD H1 2016+ - after a 16:00-ET close-to-close |ret| >= thr x sigma63 (thr {2.0, 3.0}),
    trade IN the move's direction from next session's first bar close >= 09:30 ET, hold {next 16:00
    close; 2nd session close}; sub-threshold (0.5-1.0 sigma) diagnostic - 4 + 4 cells each - gold all
    positive (2.0/2d n 133 PF 1.51 avgR +0.143 t +1.51; 3.0/1d n 33 PF 2.03 t +1.21), sub-threshold
    NEGATIVE; silver same shape (3.0/1d n 33 PF 2.41 t +1.33; sub-threshold t -3.56) - **BURNED-IS,
    holdouts SEALED, one repair available each** (honest revival = CME margin-change dates, currently
    paywalled). Not watch items.
71. **HTF-bias gate on LTF displacement triggers ("4-6 rule")** - r39 - see 69 - 88 + 4 cells - no
    tier shows a consistent alignment premium; 4H tiers lean the WRONG way on SPX/NDX - DEAD (TF
    hierarchies manage attention, not expectation).

### 2.I Volume / order-flow proxy / footprint families (tick-volume caveat on every cell)

72. **RVOL as a directional signal (FP2)** - r33b / r34 - SPX/NDX/RTY 5m RTH 2010+, minute-of-day
    baseline = trailing 20-session bucket mean; events RVOL >= 2.5 and >= 1.5 vs < 1.25 control -
    volatility prediction passes overwhelmingly (forward 30m range 1.7-2x control, t +48..+111, every
    session 1.5-2.2x); directional null-to-slightly-negative (NDX >= 1.5 t +3.29 as mild ANTI-
    continuation) - VALIDATED as a sizing/avoid instrument, DEAD as an entry.
73. **Absorption (FP4)** - r33b / r37 - 15m RTH, rolling-100 percentiles: volume >= 80 & range <= 40 at
    a 20-bar extreme with CLV confirmation; fade direction; forward 4-bar/EOD vs at-extreme control;
    TP10 scalps - fires 16-84 times per instrument in 15 years (2-8/yr): structurally unpowered, t
    scattered, halves disagree; scalps all negative - context only; loosening the condition explicitly
    refused.
74. **Delta-flip (user hypothesis)** - r34b / r40 / r41 - SPX/NDX/RTY/GOLD 15m from 5m sub-bar
    delta = sign(close-open) x volume - r34b: red 15m candle with delta15 > 0 after an 8-bar selloff
    (and mirror; and unconditioned; and delta >= 80th pct of |delta|) - 24 + 6 cells: diffs -0.1..+0.3
    bps, |t| < 1.1; RTY short side t -2.6 AGAINST; big-delta all six negative - DEAD. r40: thresholds
    {70, 90, 97} pct x context {all, trend} x measures fwd1/4/8, MFE8, pRise8, pDipRise8 - 288
    comparisons: pRise8 event <= control in all 48 definitions (z to -7.9), pDipRise8 42-51% vs 54-62%
    control (z to -16.9), MFE symmetric bull AND bear (a VOLATILITY marker) - DEAD (base-rate illusion
    in its cleanest form). r41 spec-mining demonstration on gold 15m: 240 variants (threshold {70, 80,
    90, 95, 97} x context {all, downtrend, at 20-bar low, both} x entry {event close, next close only
    after a deeper dip} x exit {TP5/SL5, TP10/SL5, TP10/SL10, time 4, time 8, TP10/SL20}); IS winner
    th90/wait-for-dip/TP10/SL20 WR 69.4% PF 1.72 +1.78 pts (IS t only +1.31) -> OOS WR 54.4% PF 0.94
    -0.26 pts; top-10 +0.82 IS -> -0.27 OOS, 7/10 flipped sign - DEAD (and the lesson is binding).
75. **Relative volume as an ORB gate** - r8 (gold Asia: top quintile SURVIVES -> candidate), r9
    (index NY first-bar: makes SPX/NDX worse), r11 (NY ORB terciles: gold mirage; indices inverted),
    Attempt 1 (RVOL30 >= 1.5 gate on ORB: not selected, gap gate dominated) - only the Asia-gold
    quintile is alive (as a forward candidate).
76. **Volume-profile absorption gates** - r11 - see 64 - directional improvement on every market,
    still under water.
77. **True order-book / DOM / CVD / MOC imbalance** - never testable (no depth feed; CFD volume is
    tick count; no exchange volume before 2010 at usable granularity).

### 2.J HTF-gating / regime gates on intraday triggers

78. Covered above: TSMOM overlay (r15 F3), VIX-level terciles (r16D, descriptive), ADX gates on the
    band fade (r8 B1), impulse/ATR regime on ORB (r11), 1H/4H/D SMA20 bias on displacement (r39),
    VIX term-structure on dip-buy (Attempt 9), corr regime on London->NY (Attempt 13), realised-vol /
    VIX gates on the Asia-index ORB (r16A). None changed conditional expectation except the deployed
    corr gate itself.

### 2.K Scalp-target frames / exit geometry studies

79. **TP +10 x SL {5, 10, 20, none} on validated entries** - r36 - gold 652 deployable entries
    (baseline PF 1.32 avg +1.62 total +1059 $/oz vs best bracket SL none PF 1.15 avg +0.62 total +407;
    SL5 PF 1.03), MHI 43-trade fade (WR 0% in all four cells: modelled cost IS 10 pts = target), D7 204
    signals (SL none 89.7% WR avg +1.78 vs baseline +11.6; SL20 PF 0.95) - 15 cells - DEAD (the target
    amputates the right tail; volatility-blind). Standing note: "if a scalp variant is ever wanted, the
    honest route is range- or ATR-scaled brackets re-registered as a new study".
80. **Footprint confirmations as 10-point scalps** - r37/37b - sweep-reclaim (FP6), displacement
    (FP5), absorption (FP4) x SPX/NDX/RTY/GOLD (gold adapted to NY 09:30-16:00 RTH logic) x SL {5, 10,
    20, none}, TP +10, one trade per family/instrument, worst-case intrabar; costs house / micro /
    zero - 48 cells x 3 cost levels - every cell negative at house cost; sweeps significantly lose in
    all 16 cells (t -3.4..-28.3) and stay NEGATIVE gross (NDX -0.32..-0.40 t to -3.9); displacement
    positive only at zero cost - DEAD.
81. **HTF signal -> LTF pullback limit entry** - r38 - see 69 - 56 cells - zero cells positive at
    micro cost; the pre-fix run showed +1.0..+2.2 pts/trade t +13.6 from a 5m-bar-start LOOKAHEAD
    (80% fill rates were the tell) - DEAD (adverse selection).
82. **Exit families on the deployed gold entries** - r9 - see section 1.2 - closed.
83. **Turtle risk layer (N-sizing, 2N stop, pyramiding, DD throttle)** - r24 - closed (deployed model
    wins every cell).

### 2.L Cross-market lead / intermarket intraday

84. **Gold/dollar as lag-1 signals for equity futures (27B)** - r27 - SPX/NDX/RTY 2012-2026 - signals
    {gold daily sign; gold 5d sign; synthetic-DXY daily sign; DXY 20d trend; gold/AUD corr <= 0.5 as
    risk state; gold-SPX 20d corr median split} x targets {next close-to-close; NY session 09:30->
    16:00} - 36 cells - best |t| 1.63; max-stat p 0.86 - DEAD (gold-equity link is contemporaneous).
85. **Gold/DXY intraday divergence** - r35a - XAU ejtrader 15m 2012-2022 vs synthetic DXY (0.809 x
    -EURUSD + 0.191 x USDJPY M15) - rolling 24-bar corr >= +0.3 (0.5) regime, shared 8-bar trend, DXY
    2-bar counter-flip -> gold forward 4/16 bars in the shared direction - 8 cells - regime exists ~3%
    of the time; diffs -2.6..+2.5 bps |t| <= 0.91 - DEAD.
86. **SMT divergence (three-phase) + timing objection** - r35c/35d - XAU vs synDXY 15m/1H/4H/daily;
    EURUSD vs USDCAD daily; XAU vs WTI daily - z-unit shock/non-response/flip spec; anchors trigger
    open (lookahead ceiling) / close / next close; intrabar move - 14 cells + controls - powered 15m
    frames null-to-negative; 4H h8 t +2.32 n 50 fails halves; intrabar "consumed edge" ~1 bp; lookahead
    ceiling no better - DEAD (principle recorded: entry refinement multiplies an expectation, cannot
    create one).
87. **Asia tone -> US session** - Attempt 15 (item 20) - BURNED-IS.
88. **Real-yield (DFII10) z-shock -> gold next session** - Round 66 KILL #13 - KILLED-REG (no forced
    counterparty in gold at 1-3 sessions; attempt-37 chassis with a proxy trigger; 54-63% of events on
    release days).
89. **HSI correlation gates (Nikkei/A50/HSCEI/CSI300)** - r15b H-C - DEAD.
90. **Correlation partners as gates on the gold rule** - r13 - see 1.2 - DEAD.

### 2.M Expiry / settlement / index-mechanics

91. Opex week (42), pinning (43), FOMC (39), Treasury auctions (40/41) - above.
92. **VIX settlement-auction (Wednesday 09:15 SOQ) hedging reversal** - Round 64 KILL #5 - KILLED-REG
    (half the grid re-parameterises attempt 19; the hedging footprint sits in deep-OTM puts, not ES
    delta). Never run.
93. **Index rebalance-day closing-flow reversal** - Round 64 KILL #7 - KILLED-REG (horizon
    re-parameterisation of attempt 19; rebalance flow nets to ~zero at index level).
94. **HK index-rebalance closing-auction reversal** - Round 64 KILL #9 - KILLED-REG.
95. **Treasury coupon SETTLEMENT-day funding drain** - 2026-09-03 KILL #11 - 88% of settlement days
    ARE the mid-month / month-turn calendar of watch #2/#6 and attempt 19 - KILLED-REG.
96. **Closing-auction imbalance fade (post-16:00 reversal)** - Round 64 KILL #1 - KILLED-REG (exit
    cells = burned attempt 29's window; post-close CFD prices are synthetic in the OOS block).
97. **Closing-auction pressure spread reversal (M2K-vs-MES)** and **small-cap overnight residual fade
    (M2K-vs-MES)** - Round 64 KILLS #4, #3 - KILLED-REG (no forced counterparty at index level;
    two-leg micro spread is cost-dominated; sub-cell of the spent gap family).

### 2.N Overnight-session families

98. Items 27, 28 (euro-open window; full overnight), r9 overnight hold of the gold trade (PF 1.05
    halves disagree), r30 daily decomposition, **megacap after-hours earnings -> MNQ continuation**
    (Round 64 KILL #2: sub-cell of the spent overnight-gap family; no uninformed counterparty),
    **pre-open vs post-close release clustering** (Round 68 KILL #21: post-close -> overnight is kill
    #2 / attempts 5 and 29; the pre-open RTH arm is 12.7% FOMC days on a burned negative cell).
99. **BTC weekend-move reversion** - Attempt 39 - daily UTC bars 2015+; Fri close -> Sun close move,
    fade at Sun close, exits Mon/Tue close; filter {any, >= 1.0 sigma63} - 4 + 2 cells - all flat-to-
    negative; midweek diagnostic equally null - BURNED-IS (crypto; listed as the only weekend-gap
    family ever run).

### 2.O Vendor-claim audits (for the record; nothing new to test)
edgeful ES 5m ORB (r23: reproduces descriptively, dies on costs/window); TradeAlgo NQ ORB (r32b:
refuted); Medium "Strategy 60" (r32a: unverifiable rules, risk math understates 2-5x); Scribd
32-strategy sheet (r32c: frictionless + best-of-28 selection null; its own NQ ORB row PF 1.01 refutes
TradeAlgo); pinescriptforge (r29: manufactured); ALMA Idea (r31: mechanical 76% WR); MU overnight
charts (r30: beta concentration).

---------------------------------------------------------------------------------------------------

## 3. THE CLOCK: which windows are directional and which are flat (session atlas r34 + related)

**Round 34 session atlas** (SPX/NDX 2005-2025, RTY 2005-2020; sessions in ET: Asia 20:00-00:00,
London 02:00-05:00, NY AM 09:30-11:00, NY lunch 12:00-13:00, NY PM 13:30-16:00; bars outside these
windows EXCLUDED - note the atlas is non-contiguous: 00:00-02:00, 05:00-09:30, 11:00-12:00 and
13:00-13:30 ET were never measured):
- VOLATILITY is strongly structured: RVOL >= 2.5 predicts 1.5-2.2x forward range in every session
  (weakest London ~1.6x, strongest Asia/NY PM ~2.2x); RVOL extremes are 3-6x more FREQUENT overnight
  (Asia ~500-700/yr vs NY AM ~90-230/yr) - an overnight orange bar means less than a NY-AM one.
- SWEEP-FAILURE base rate RISES through the day: Asia 59-66% -> London 68-74% -> NY AM 73-76% ->
  lunch 76-82% (overnight PDH/PDL breaches stick more often = real repricing; lunch pokes come back =
  noise). None pays: fwd30 after failures -4.8..+2.7 bps, no |t| >= 2; NY PM failures slightly
  CONTINUE against the reversal (SPX -4.8 bps t -1.9) - do not fade PM breaks.
- DIRECTION is flat everywhere except one cell: NY PM (13:30-16:00) displacement continuation, NDX
  +4.1 bps/h vs ~0 control t +3.07, SPX +2.1 t +1.9, RTY +2.4 t +1.4 - inside the expected max of a
  75-cell null; halves not computed; logged as a WATCH HYPOTHESIS, then effectively tested and burned
  via Attempt 4 (displacement horizon/magnitude, OOS PF 0.95) and Attempts 2/2b (late-day serial
  dependence ~ +0.008R gross vs ~0.02R cost).
- Verdict sentence: "session bands modulate HOW MUCH things move and how much breaches stick, not
  WHICH WAY".

**Other clock facts on record (gold unless stated):**
- Deployed-trade hold curve (r9): mean open P&L -0.05 (+1h), -0.08 (+2h), 0.00 (+3h), +0.47 (+5h),
  +1.05 (+9h), +1.75 (+10h), +2.30 (+12h), +2.47 (+14h), +2.51 at the 16:00 NY close; overnight drift
  dies (PF 1.05, halves disagree).
- Session split of the edge (r15 F4): entry->07:00 UTC 17%, 07:00->14:00 UTC 70%, 14:00->exit 13%.
- Gold's daily variance lives in the 08:30 ET release slot (r1 volatility profile; r54 feed-clock
  fingerprint peaks at 08:30 ET); but the 08:30 impulse carries no continuation (Attempt 10).
- Asia 09:30 HKT is thin and slow (the edge); London 08:00 and NY 09:30 price information within
  minutes (ORBs dead both directions).
- SGE 02:15 UTC auction hour is a trend-setting window (anti-mean-reverting), not value (r26).
- Gold 09:00-11:00 ET fix windows: gross ~0 in every 30-60 min window either direction 2012+ (Attempt 36).
- London 03:00-10:00/11:00 ET gold short and Asia 19:00/20:00-02:00/03:00 ET gold long: no clock drift
  2020-24 (Attempt 7).
- Indices: euro-open 02:30-03:30 ET is significantly NEGATIVE (Attempt 6, confirmed on true ES);
  noon dips continue into the close in every vol regime (Attempt 9); 15:00/15:30 -> close carries
  ~+0.008R gross serial dependence (Attempt 2b); FOMC statement-day 09:30 -> 13:55 is significantly
  negative (-0.101R t -3.29) while prev 15:55 -> 09:30 open is the positive segment (watch #10);
  Treasury 10Y/30Y auction days rally into 13:00 and fade after (Attempt 26; 2Y same); Friday
  open -> close is systematically weak (avgR -0.059 t -4.05, Attempt 32); Monday drifts UP
  close-to-close; overnight 16:00 -> 09:30 is gross-positive and cost-dead (Attempt 29).
- HSI: the 09:15-09:30 HKT pre-open push reverses over the next hour (open-auction effect only);
  the 09:30-10:30 home range carries mild gross follow-through under 10 pts of cost (r15b).

---------------------------------------------------------------------------------------------------

## 4. COST LESSONS (the numbers)

- **Attempt 2/2b (late-day serial dependence)**: net_mom + net_rev = -2 x cost per variant -> cost
  ~0.021-0.026R at micro rates; gross late-day effect ~ +0.008R at one trade/day. No spec in the
  family can clear ~0.02R costs on a ~0.008R gross effect.
- **Attempt 4 / r37b (displacement)**: zero-cost SL5 scalps SPX +0.52 pts/trade (t +7.1), NDX +0.42
  (t +5.7), RTY +0.22 (t +2.7), GOLD +0.20; at micro best-case only SPX SL5 survives (+0.17 pts =
  $0.85 per MES trade, t +2.32, 0/3 sibling agreement); house cost SPX 0.6 = the whole gross edge.
  "A 10-pt target pays ~9-16 gross wins per 100 trades of edge while eating 60-200 bps of
  cost-equivalent on every trade." NDX: cost 2.0 = 20% of a 10-pt target (every cell t <= -5.7).
- **Attempt 29 (overnight)**: night-minus-day +0.018R/day gross vs ~0.02R daily RT -> net -0.002R.
- **r30 (index overnight, daily)**: SPX +2.3 bps/day gross compounds to exactly 1.00x at 2 bps RT
  over 21 years; NDX 2.11x at 2 bps vs 11.5x B&H; both ruinous at 5 bps.
- **r7 / r8 (gold NY open)**: 15m range held to NY close PF 1.030 at $0, 0.985 at $0.15, 0.942 at
  $0.30, 0.863 at $0.60; average forward move after fill +$0.10 (NY 15m) vs +$1.56 (Asia 60m); the
  fade loses $0.13/oz at zero cost.
- **r8 (2.6-sigma)**: zero-cost PF 1.006 (+$0.01/oz) -> $0.30: 0.860 -> $0.60: 0.739: the reversion is
  worth exactly one spread.
- **r9 (index NY open)**: Zarattini first-bar zero-cost PF 1.12-1.17 on 4-5k trades, net 0.92-0.96
  at 0.6/2.0/0.4 pts.
- **r25b (gold low-TF ranges)**: 5m Asia range PF 1.223 gross -> 1.028 net; stop rates 67-84% when the
  range is $1.5-2.8 wide vs $0.60 RT; best low-TF cell (15m) dies at 2x costs (PF 0.998).
- **r28 (Zarattini noise area)**: SPX PF 1.148 t +3.28 gross -> 0.88-1.05 at CFD cost -> t -6.5 at 2x.
- **r32c**: one tick of RT cost (0.20 GC / 0.50 NQ pts) turns 133k-551k-trade rows at PF 1.00-1.02
  negative; implied gross edges +0.008..+0.094 pts/trade.
- **r36 (MHI)**: modelled cost 10 HSI pts = a 10-pt target; a net win cannot exist.
- **Attempt 36 calibration**: on gold at 0.35/RT any sub-hour window family needs |gross| >
  ~0.025R/day - a bar almost nothing structural clears.
- **r3 slippage**: a 1x-range gold stop (~$5) is hit 72% of the time; $0.50 of stop slippage costs
  more than half the result; a 3x stop barely notices.
- **r4 MGC**: basis $0.48 (0.011%); tick rounding $0.002/oz - contract choice does not change the
  gross-vs-spread inequality.
- Program-level: every one of the first five burned r42 families was an RTH index-micro intraday
  effect - "the most heavily arbitraged arena there is" - and the two eras (2005-2020 vs 2020-2026)
  disagreed about every candidate found.

---------------------------------------------------------------------------------------------------

## 5. REGISTRATION-STAGE KILLS AND REFUSALS (never run; the adjacency reasons bind)

Round 64 (12 proposed, 10 killed): #1 closing-auction imbalance fade; #2 megacap after-hours
earnings -> MNQ continuation; #3 small-cap overnight residual fade (M2K vs MES); #4 closing-auction
pressure spread reversal; #5 VIX settlement-auction hedging reversal; #6 buyback-blackout OPEN-window
long (long-only regime = drift); #7 index rebalance-day closing-flow reversal; #8 HKMA convertibility-
undertaking liquidity regime on HSI (counterparty in USDHKD, not HSI); #9 HK index-rebalance
closing-auction reversal; #10 ETF short-interest surge -> index long.
Later: #11 Treasury settlement-day funding drain; #12 Fed liquidity plumbing (RRP/TGA/net liquidity;
class CLOSED); #13 real-yield shock -> gold; #14 bond-vol (VXTLT) contagion short; #15 index-specific
fear (VXN/VIX) long; #16 basket fails-to-deliver breadth; #17 daily short volume; #18 leading-
announcement-session long (217/252 LEAD sessions sit inside attempt 19's opex calendar); #19 buyback-
blackout share regime (a square wave of the fiscal calendar; contains 100% of watch #6's sessions);
#20 earnings-season density regime; #21 pre-open vs post-close release clustering.
Checkpoint refusals (attempt-16 preamble): quarter-end (adjacent to month-end), CFFEX/China close
(adjacent to Asia tone), UST10Y regime gate (no base strategy), RTY-vs-SPX relative intraday (no
mechanism). Round 62: ISM Services regime (97% inside the mfg regime), Conference Board confidence
(19 releases). Round 56: gold Asia premium on 2012+ data (adjacent to spent attempt 7). Round 60/64:
dealer TFF extremes and the commercial COT-flow mirror (non-independent). Round 28: ICT Silver
Bullet/Unicorn "bias" forms and Wyckoff Spring/Anti (not mechanisable). Round 24 D: Turtle 20/55-day
entries, Williams Oops gaps (23-hour gold has no exploitable opens), Medallion-style 50.75% signals
(invisible at ~250 trades/yr), PTJ 200d gate / Minervini VCP (deferred, never run). Round 27: FVG
mirror fade (sweep-fade in costume). Attempt 6: short-the-euro-open mirror. Attempts 26/27:
auction-day mirrors. Attempt 47: long-only COT-flow sub-cell.

---------------------------------------------------------------------------------------------------

## 6. LIVE STREAMS AND WATCH ITEMS (frozen; occupied; forward data only)

Paper/auto-journalled streams (2026-09-09): XAU (deployed gold rule), XAUAUD (upgrade #1 half-leg),
MHI (HSI pre-open fade on HK33 CFD, from 2026-09-01), MHIF (same rule on true HSI futures, from
2026-08-19), D7 (Double Seven SPX, daily, frozen 7/200), PMI (ISM Mfg PMI < 50 contraction-long
regime on SPX/NDX/RUT, graduated 2026-09-02 after the program's only OOS pass; INACTIVE at the
Aug-2026 print 54.6; bar = 250 forward regime-day bookings).
Playbook watch list: (1) gold CISD-to-EoD reversal; (2) gated VP reversion on gold's overnight
profile; (3) HSI pre-open fade; (4) Double Seven SPX.
Program watch items: #1 NY-PM displacement (superseded by burned attempt 4; passive only); #2
conditional month-end rebalancing fade (thr 1.5%, entry T-2 close); #3 FOMC full-day (RETIRED,
subsumed by #10); #4 CPI-surprise equity fade (release+5m, hold to close); #5 gold CPI-surprise
(DOWNGRADED, era-specific); #6 quarter-end TOM long (T-1 close -> +3rd close); #7 VIX-shock
reversal (z >= 1.5, long next open, exit 3rd close); #8 COR1M spike reversal (>= 80th pct); #9
stress-reversal composite (a OR b; variants pooled / SPX+NDX / (c) VXN-VIX ratio shock long NDX,
ex-post-opex-day, forward-only from 2026-09-04); #10 FOMC-night long (prev 15:55 -> 09:30 open); #11
extreme lev-money net-short -> long index Monday open, 5 sessions (LOW-confidence). Items #6/#7/#8/#9
describe one economic claim (large-cap rebound after forced-flow events, RTY flat) and must never be
cited as independent confirmations; the claim does NOT generalise to gold (GVZ shock, Attempt 33) or
BTC (DVOL shock, Attempt 41).

---------------------------------------------------------------------------------------------------

## (a) CLOCK WINDOWS AND MECHANISMS NOT YET TESTED INTRADAY ON THIS DATA

Honest accounting, with the nearest burned neighbour named so adjacency can be argued rather than
assumed. "Untested" means no cell was ever computed; several of these were killed at registration
and would need a genuinely different mechanism argument to be admitted.

Clock cells never measured (any instrument):
1. **11:00-12:00 ET (Europe/London cash close 16:30 London = 11:30 ET)** - the atlas skips this hour;
   the only touch is 11:00 NY as a gold EXIT (r9, PF 1.292) and attempt 36's L2 leg ending 11:00 on
   gold. No London-close anchored construction on MES/MNQ/M2K/MGC exists. Nearest burned neighbours:
   attempt 7 (gold London short ends 10:00/11:00), attempt 36 (fix windows).
2. **13:00-13:30 ET** (atlas gap between lunch and NY PM). 13:00 itself is tested only on Treasury
   auction days for indices (attempts 26/27, both arms dead) and as a gold exit (r9 PF 1.346). On
   NON-auction days the 13:00 cell is unmeasured.
3. **13:30 ET COMEX gold futures settlement** - never anchored anywhere. The r9 hold curve shows the
   gold trade accruing +2.30 (+12h) -> +2.47 (+14h) through this window, but no settlement-specific
   family (into/after 13:30, GC-vs-spot basis behaviour at settlement) has been proposed. Data
   caveat: spot/CFD frames only; true MGC intraday is 3 days on disk (MGCZ6_30m) plus IBKR forward pulls.
4. **15:50-16:00 ET MOC-imbalance publication** - the 15:30->16:00 clock cell is BURNED (attempt 2/2b:
   ~+0.008R gross vs ~0.02R cost, both directions) and the post-close reversal was killed at
   registration (kill #1). An imbalance-CONDITIONED version has never been run because there is no
   NYSE/Nasdaq imbalance feed; without that feed it cannot be honestly distinguished from the burned
   window.
5. **VIX settlement Wednesdays 09:15 ET (SOQ)** - KILLED-REG (#5), never run. SPX 24h CFD bars exist
   for 09:15-09:30 and VX expiry dates are derivable (third Wednesday rule; IBKR VX ladder ~12
   months); the objection on record is that the hedge footprint is in deep-OTM puts, not ES delta,
   and that half of any grid re-parameterises attempt 19. Also untested: the SOQ-day 09:30 open
   itself as a vol regime (not direction).
6. **16:00-18:00 ET post-close / 17:00 Globex maintenance halt / 18:00 reopen** - never isolated.
   Attempt 29 held the whole 16:00->09:30 night; attempt 6 held 01:00-04:00 ET; kill #1 noted that
   post-close CFD prices in the OOS block are SYNTHETIC. True ES 1h/2h (IBKR, Jul-2025 onward) is the
   only honest feed for this cell and is ~14 months deep - forward material, not a backtest.
7. **Sunday 18:00 ET Globex reopen / weekend gap on MES/MNQ/MGC** - never run (the ledger queued it
   "ONLY if it can be honestly distinguished from the burned RTH-gap family"; attempt 29 EXCLUDED
   weekend holds as its adjacent-only scope; attempt 39 tested the BTC weekend on daily bars, null).
   Gold's Sunday 22:00 UTC open on the CFD feed is likewise untested as a window.
8. **London cash open 03:00 ET (08:00 London) on the INDICES as an ORB / breakout** - untested. What
   exists: attempt 6 (unconditional long drift 01:00-04:00 / 02:00-03:30 / 02:30-03:30 ET, negative),
   r34 London 02:00-05:00 session (direction flat), r16A (index ORB at 01:30 UTC = HK open, dead both
   ways), r12 (gold London-open ORB dead), r8 ldnkz 02:00 ET sweeps on gold (dead). The meta-law
   (price-discovery gradient) predicts failure; it has not been measured on MES/MNQ.
9. **Eurex/European futures open 02:00 ET and European data at 04:00-05:00 ET (10:00-11:00 London)**
   as event cells - untested (attempt 6 windows are unconditional drift, not release-anchored; the
   econ calendar on disk is US-only).
10. **05:00-08:30 ET on indices (European mid-morning / US pre-market before releases)** - no cell of
    any kind (atlas gap; attempt 6 ends 04:00).
11. **10:00 ET releases as a SEPARATE clock cell** - 10:00 ISM/consumer prints were POOLED into
    attempt 17's surprise family (growth-on-beat negative in all 4 cells, inflation positive); a
    price-only 10:00 impulse (attempt-10 style) on indices, or a 10:00-anchored gold cell other than
    the PM-fix windows (attempt 36, dead), has not been run. Attempt 10's lesson (price-only impulse
    proxies carry nothing on gold) and attempt 17's regime-poisoning lesson both apply.
12. **Non-US central-bank and data events (ECB 08:15/08:45 ET, BoE 07:00 ET, BoJ overnight, UK/EZ
    CPI at 02:00/05:00 ET)** - untested; the FXStreet pull was countries=US only (the same endpoint
    serves other countries).
13. **Pre-open earnings-cluster days (EDGAR calendar, 8,167 releases with acceptance timestamps)** -
    class CLOSED at registration (kills #18-#21): the leading-announcement sessions are 86-79% inside
    attempt 19's opex calendar; the pre-open RTH arm is 12.7% FOMC days. Never run as a DIRECTIONAL
    family. The honest untested use is as a VOLATILITY/sizing regime (the r33b FP2 lesson) or as a
    calendar LABEL for gating other families - neither has been operationalised.
14. **Gold's own expiry calendar (COMEX GC option expiry ~4th business day before month end; first
    notice day; last trade day)** - untested; attempt 19 ran gold only as a diagnostic under the
    EQUITY opex calendar.
15. **Half-day sessions (13:00 ET early closes)** - the CFD feeds trade shortened sessions on partial
    holidays (attempt 20 note); the early-close day itself has never been a clock cell.
16. **HSI/JP225 beyond the pre-open**: HSI lunch-break reopen 13:00 HKT, closing auction 16:00-16:10
    HKT, after-hours 17:15 HKT open; JP225 lunch/close/night session - untested (HK33 CFD has no
    auction prints; true HSI futures 15m is 6-12 months deep via IBKR; JP225 1m 2005-2020 exists).
17. **Bond-close 15:00 ET as a distinct anchor** - only touched as attempt 2's 15:00 entry (cost-dead).

Mechanisms never tested intraday (data permitting):
18. **Volatility-regime SIZING overlays on the deployed gold rule** (FP2-style RVOL, delta-flip MFE,
    VIX level) - every volume/flip study ended with "a sizing/avoid instrument, never an entry", and
    none was ever run as a sizing test on the 652 trades (r16D VIX terciles were descriptive; r8 rvol
    is a gate candidate, not a size dial).
19. **Range- or ATR-scaled scalp brackets on the footprint signals** - r36 named this as the honest
    scalp route; never run (the deployed gold entries already have 1-6x range targets covered by r9).
20. **Limit-order / queue-position fill engineering** for the FP5 displacement drift - identified
    twice (r37b, r38) as the only remaining lever and as untestable on OHLC.
21. **Intraday cross-asset leads at 5m: ES -> MGC, ZN/rates futures -> MES, DXY futures -> MGC** -
    only the 15m synthetic-DXY/gold divergence (r35) and daily lag-1 (r27B) exist; no intraday bond
    or dollar FUTURES frame is on disk (real yields are daily FRED).
22. **True-futures intraday validation of any burned family** - all intraday work is on CFD/spot
    proxies except: euro-open cross-check on IBKR ES (r43, 70 sessions), RTY TopstepX 1h
    2025-03..2026-04 / 5m 2026-01..04 (used only for r29's overlap check), HSI futures 15m from
    2026-08-19 (MHIF). MGC intraday history does not exist here beyond 3 days.
23. **0DTE / same-day gamma regimes (VIX1D, from 2022-05)** - data too short for the 75/25 rule; never proposed.
24. **CME margin-change dates as an ex-ante trigger for the sealed metals margin-cascade families**
    (attempts 37/38) - the registered repair route; the data class is paywalled (CME DataMine).
25. **Order-flow / DOM / imbalance families** - structurally untestable on this data (no depth feed;
    CFD volume is tick count; exchange volume usable only 2010+ at 5m).

---------------------------------------------------------------------------------------------------

## (b) DATA AVAILABLE FOR INTRADAY WORK (on disk in `backtest/data/`, gitignored; re-fetch recipes in
`fetch_data.sh`, `fetch_index_data.sh`, and the ledger's acquisition entries)

Price frames (provenance established empirically per house rules unless noted):
- **XAUUSD_5m.csv** - spot gold 5m, 2020-08-21 .. 2025-08-01, 350,903 bars, UTC (verified by the DST
  shift of the intraday vol peak); cross-checked vs a second feed (median $0.17 on 35,480 bars). This
  is the frame `load_frame("GOLD")` uses for attempts 1-49 (the ledger's "2020-08..2026-08" wording
  for attempt 7 overstates the span). IS/OOS cut for the r42 program = last 25% of sessions.
- **XAUUSD_m15_ejtrader.csv** - 15m, 2012-05-15 .. 2022-03-04, 230,400 bars, prices x100, feed clock
  = MT4 GMT+2/+3 (ET = feed - 7h); corr 0.9995 vs the 5m feed on the overlap; spliced with the 5m at
  2020-08-21 for the 2012+ gold families (attempts 36-37, 47, watch #5 re-score).
- **XAUUSD_H1_collector.csv** - H1, 2016-04-21 .. 2026-08-26, UTC (Oanda collector); used for the
  spliced daily gold series (r24) and the H1 benchmark construction (r20).
- **SPX_5m.csv / NDX_5m.csv** - 24h CFD 5m harmonised UTC caches, 2005-01-02 .. 2025-12-31 (Oanda 1m
  2005-2020 + MT5 broker export 2020/2021-2025; feeds agree to +0.007%; timezone verified by the
  09:30-ET vol step both seasons). NDX hole 2020-05-13 .. 2021-01-04. Volume = broker TICK count
  (2005 SPX median 7 ticks/5m bar - volume cells run 2010+).
- **RTY_5m.csv** - 2005-01-02 .. 2020-05-14 (Oanda); intraday hole 2020-05 .. 2025-03. Plus TopstepX
  true RTY futures: 1h 2025-03-21 .. 2026-04-15, 5m 2026-01-20 .. 2026-04-15 (real contract volume;
  snapshot URLs, not fully reproducible).
- Raw sources kept: SPX500/NAS100/US2000_1m_oanda_futuresharks.csv (1-minute, 2005-2020, ~200 MB each;
  used for the 1m execution tiers in r38), US500/US100_5m_ts4blader.csv (2020/2021-2025, UTC+2 server).
- **HK33_M15.csv** (2024-04-19 .. 2026-08-31, Oanda collector, UTC; day opens 01:15 UTC) + **HK50_
  PT15M_yuan.csv** (2022-02-18 .. 2024-04-19) spliced at 3.1 bps median diff = the 4.5-yr HSI 15m
  series; HK33_H1 2016-04 .. 2026-08; HK33_M5. CAVEAT: the CFD has NO pre-open auction print (its
  01:15Z bar is a synthetic broker open; push ~0.72x the futures'). `data/forward/hk33_m15.csv`
  refreshed weekly.
- **HSI true futures 15m (IBKR)** - `data/forward/hsi_fut_15m_*.json` from 2026-08-19 (HSIQ6/HSIU6;
  weekly pulls; expired months older than ~8 months are not served, so depth accrues forward only).
- **JP225_1m_futuresharks.csv** - 2005-01-03 .. 2020-05-14 (2.79M bars); **JP225_H1.csv** 2016-04 ..
  2026-08 (24h CFD - date-group aggregation LEAKS; use explicit clock cutoffs). AUS200_H1 2016-2026.
- **True CME ES (IBKR)** - ES_Z5/H6/M6 2h and ES_U6 1h JSONs, 2025-07-07 .. 2026-08-28 (delayed 10 min;
  Globex hours verified); re-fetchable; expired-contract reach ~12 months, so this accrues forward.
  GC daily per Dec contract >= 5 years (settlement marks when deferred); VX daily ~9 months per
  contract; HSI futures daily ~1 year.
- **MGCZ6_30m.csv** - 3 days (2026-08-17..19), the r4 basis probe only.
- FX intraday for gates: AUDUSD_M5 (2018-10 .. 2021-06), AUDUSD_m15_ejtrader (2012-11 .. 2022-03),
  AUDUSD_M15_collector (2024-04 .. 2026-08) - AUD intraday HOLE 2022-03 .. 2024-04 (the halves of
  r25); AUDUSD_daily_fred (full span; the live gate substitutes IBKR AUD.USD daily); EURUSD/USDJPY
  m15 (ejtrader 2012-2022; collector 2024+), USDJPY_H1 2016-2026 (synthetic DXY legs); FRED daily FX
  for EUR/JPY/GBP/CHF/CAD/CNY.
- **XAGUSD_H1.csv** - 2016-04-21 .. 2026-08-26 (session closes only; no 5m path).
- Forward pulls (`data/forward/`, weekly IBKR): gold 5m and AUDUSD 5m (ONE_WEEK rolling window - unobserved
  sessions age out permanently), gold/AUD daily, SPX/NDX/RUT daily, HSI futures 15m, `ism_pmi.json`.

Event / calendar / conditioning data:
- **econ_events_us_high_fxs.json** - FXStreet US high-impact calendar 2013-01 .. 2026-08: 3,067
  events, 2,030 with actual + consensus (+ revised, previous, ratioDeviation; dateUtc): NFP 164, CPI
  variants ~250, GDP 149, retail 232, ISM 258, Fed decisions 110; sanity-checked; re-fetch recipe =
  calendar-api.fxsstatic.com (Kernel browser). US only.
- **FOMC statement calendar 2013-2026** - two-source verified, frozen in `run_r42l_fomc.py`
  (statements at 14:00 ET; 2020-03 emergency action excluded).
- **Treasury auctions** - `treasury_note_auctions.json` (1,965 note auctions 1979-2026) and
  `treasury_bond_auctions.json` (392): auction_date, term, bid-to-cover, high yield, reopening flag,
  issue_date; results at 13:00 ET; dates published weeks ahead.
- **EDGAR corporate calendar** - `data/earnings/earnings_dates.csv`: 8,167 Item-2.02 earnings releases
  2004-10 .. 2026-08 for the 93-name mega-cap basket (+9 predecessor CIKs), release_date keyed on
  acceptance time in ET (pre-open 3,963 / post-close 3,480 / intraday 724), every 10-Q/10-K date; ~97%
  complete; AAPL/ABT/AMAT cross-checked vs Alpha Vantage. Class CLOSED for directional families;
  banked as a labelling asset.
- **Options-expiration / TOM / holiday / weekday calendars** - derived deterministically in the r45/
  r51 runners (third-Friday rule with holiday shift; NYSE full-closure holidays only are detectable
  on the CFD feeds).
- **CBOE index histories (daily)**: VIX 1990-2026 (OHLC), VIX9D 2011+, VIX3M 2009+, VIX6M 2008+,
  VIX1Y 2007+, VIX1D 2022-05+, VVIX 2006+, VXN/RVX/OVX 2009+ (archive start; early rows flat),
  VXTLT 2004+ (pre-2013 back-filled), SKEW 1990+, COR1M/COR3M 2006+, GVZ 2009+; equity and total
  put/call 2006-10-04 .. 2019-10-04 only (post-2019 exists only as ~1,740 per-day JSONs, not pulled).
  VIX file carries 32 holiday rows (2022+) absent from VXN - align calendars before ratios.
- **Positioning**: COT gold legacy 088691 weekly 2006-2026 (cross-feed verified; corrected CFTC
  release rule = Friday 15:30 ET, following Monday when a federal holiday falls in the report week,
  shutdown weeks non-tradable); CFTC TFF equity-index futures weekly 2010-07 .. 2026-08 (era splice
  map frozen; class CLOSED); Binance BTCUSDT perp funding 8h 2020-01 .. 2026-07; Deribit DVOL daily
  2021-03 .. 2026-08; BTCUSD daily 2010-2026 (crypto intraday is premium-gated).
- **Reg SHO (primary, verified to the row)**: SEC fails-to-deliver 2012-01-03 .. 2026-08-14 for
  SPY/QQQ/IWM + 93-name basket (351/351 half-months; publication lag 15-30 days); FINRA daily short
  volume 2019-01-02 .. 2026-09-04 (unadjusted shares; T+1 publication); FINRA bi-monthly short
  interest 2020-01 .. 2025-12 for 80 basket names (Equibles); off-exchange weekly 2021-12+. Class
  CLOSED (attempt 49 subsumed into the stress calendar at construction); banked.
- **FRED (daily unless noted)**: DFII10/DFII5 real yields, DGS10/DGS2, T10YIE/T5YIE 2003+, DTWEXBGS
  broad dollar 2006+ (~1-week lag), RRPONTSYD, WALCL/WTREGEN weekly; HY OAS unusable (capped at
  2023-09). Alpha Vantage daily: UST 2y/10y, fed funds, WTI/Brent/natgas, gold/silver (7-day calendar,
  FAILED its cross-check in r24 - do not use for returns), UNRATE monthly, CPI monthly.
- Reachable-but-not-pulled (frontier probe 2026-09-03 / acquisition 2026-09-04): VX futures term
  structure ~1.5 yrs via IBKR; GC front/second/third daily term structure 5 yrs; VXEEM/VXFXI/VXSLV
  CBOE; other-country FXStreet calendars; Deribit funding since 2018-08 (Kernel only). Blocked:
  CME historical margins (paywalled), NYSE MOC imbalances, any DOM/order-flow product, FTD before
  2012, daily short volume before 2019.

- **Round 71 (2026-09-09) - true ES / GC 5m forward pulls** (`data/forward/es_5m_*.json`, `gc_5m_*.json`,
  weekly ONE_WEEK, front/active month, Globex 18:00-17:00 ET incl. the Sunday reopen): the feed for the
  five forward-only specs F1-F5 (expiry-morning gap fade, MOC drift, 16:00-16:15, GC Sunday reopen, HSI
  16:15-16:30) scored descriptively by `forward/leg_intraday.py` -> `results/forward_intraday.json`.
  Untested clocks 4, 6, 7 and kills #22/#24/#25's route-backs are now IN THE LOG, not open.

- **Round 73 (2026-09-12) - data limit #7 REVISED, Round-70 fidelity finding WITHDRAWN.** The "true ES 2h"
  reference files were clean only inside each contract's front-month window (7-12% clean outside; the
  Round-70 overlap used 26% front-month bars). On a clean reference the CFD feeds track the ES overnight
  PATH (corr 0.89 MT5 / 0.97 Dukascopy, 242 nights) with a +1.8 to +4.3 bp/night RETURN shortfall against
  ES. Evening/overnight event windows on the CFD frames are readable with that bias disclosed; auction-print
  events (09:30 open, SOQ) still need true futures. Kill #1's "synthetic post-close prints" objection is
  refuted (two independent CFD feeds agree at corr 0.964 on 16:00-18:00). New asset: Dukascopy 1m index
  CFDs (USA500/USATECH, overlap 2025-07..2026-09 on disk; 2012-2025 history being pulled) with a fixed
  16:15-18:00 ET break and a Sunday 18:00 ET open.

- **2026-09-13 - assets #23/#24 complete.** Dukascopy 1m USA500/USATECH 2012-2026 (24h usable 2013-14 and 2018+;
  overnight absent 2015-17) and XAUUSD 1m 2003-2026 (UTC-pinned from 2008; 2003-07 clock unverified). Gold
  intraday families now have one 23-year 1-minute frame; index cells have a second independent feed.
