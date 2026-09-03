# MHI stream: does the HK33 CFD reproduce the HSI futures marks? — 2026-09-03

Data-fidelity check only. **No strategy returns, hit rates or P&L were computed.** The
question is whether the paper trades the MHI leg journals from the HK33 CFD 15m feed
(`forward/leg_mhi.py`, CONTRACT.md leg MHI) would have been the same trades, at the same
marks, on the HKFE Hang Seng futures a real account would fill on.

## 1. Data

| feed | source | file | bars | first | last | sessions with a 01:15Z bar |
|---|---|---|---|---|---|---|
| HK33 CFD 15m | broker feed already on disk | `backtest/data/forward/hk33_m15.csv` | 36,779 | 2024-04-19 | 2026-09-02 08:15Z | all |
| HSIU6 (exp 2026-09-29, conid 810760513) | IBKR `get_price_history(FUT, HKFE, FIFTEEN_MINS, step_count=2200, outside_rth)` | `backtest/data/probe/hsi_fut_15m_HSIU6_sc2200.json` | 2,197 | 2026-07-17 14:00Z | 2026-09-03 11:30Z | 34 |
| HSIU6 (same, `period=ONE_MONTH`) | superseded, kept as the period-form sample | `backtest/data/probe/hsi_fut_15m_HSIU6_1month.json` | 1,375 | 2026-08-05 | 2026-09-03 | 21 |
| HSIQ6 EXPIRED 2026-08-28 (conid 878716631) | IBKR, `step_count=800` (served 530) | `backtest/data/probe/hsi_fut_15m_HSIQ6.json` | 530 | 2026-08-18 06:00Z | 2026-08-28 08:15Z | 8 |

What the IBKR endpoint would and would not serve for HKFE 15m (all with `outside_rth=true`):

- HSIU6: `ONE_MONTH` ok (1,375 bars); `THREE_MONTHS` rejected by the 3,500-point cap;
  `step_count` 1500 / 2000 / 2200 ok, **2500 / 3000 / 3400 all error** ("An error occurred.
  Please try again later", repeatable). Intraday depth on the live front is therefore
  ~2,200 bars ≈ 7 weeks, not the 3,500 the cap suggests.
- HSIQ6 (expired 6 days ago): `ONE_WEEK` served an empty series (window anchored to now),
  `TWO_WEEKS` ok, `ONE_MONTH` errors, `step_count` 800 ok (530 bars, i.e. everything from
  2026-08-18), `step_count` 1000 / 1200 / 1500 error. Daily `ONE_MONTH` ok (control).
- HSIN6 (expired 2026-07-30) and HSIM6 (expired 06-29): every form tried errors. So the
  front-contract history reachable today starts 2026-08-19; nothing older is addressable
  from this session.
- HSIV6 (Oct, next-out): served, but 0–63 lots per bar until 08-28 — useless as a mark.

Call log: `search_futures` x1, `get_price_history` x26 (10 served incl. 1 empty and 1
daily control, 1 cap rejection, 15 errors).

Contract selection per session: the contract with the larger 01:15–08:15Z volume that
day. That is HSIQ6 for 08-19..08-27 (37k–87k lots/day) and HSIU6 from 08-28 (on the
expiry day itself HSIU6 did 75k vs HSIQ6 4k, so the roll is 08-28, not 08-31). For
07-20..08-18 only HSIU6 exists in what was served, and it was then the thin second month
(75–685 lots/day, 5–156 in the pre-open bar). Those 22 sessions are reported separately as
"thin"; the **11 liquid sessions 08-19..09-02 are the evidence**.

## 2. Method

Both feeds are cut exactly as `leg_mhi.py` cuts the CFD: pre bar = the 01:15Z 15m bar,
push = its close − open, ATR14 = mean of the prior 14 CFD daily high−low ranges (shift 1;
the CFD's ATR is used for both feeds, per the brief), trigger = |push|/ATR14 ≥ 0.3, entry
mark = 01:30Z bar open, exit mark = close of the last bar before 08:00Z (07:45Z on both
feeds), stops = pre_hi + 0.5·pre_rng (short) / pre_lo − 0.5·pre_rng (long), checked on 15m
highs/lows of the 01:30–07:45Z bars. Stop outcomes are evaluated four ways: each feed's own
stop on its own bars, and each feed's stop on the other feed's bars.

Alignment was verified before anything else: both feeds stamp bars at bar start, have the
same 22 session bars (01:30..07:45Z with the 04:00–05:00Z lunch gap), and the correlation
of 15m close changes over the 11 liquid sessions is **0.993 at lag 0** vs 0.04 / 0.03 at
±1 bar (n = 242). There is no timestamp offset to explain away.

## 3. Numbers

### 3.1 Levels: entry, exit, stops (futures minus CFD)

| mark | liquid n=11: median diff | median \|diff\| | as ATR14 | max \|diff\| | corr of levels | all 33: median \|diff\| |
|---|---|---|---|---|---|---|
| 01:30Z open (entry) | −18.9 | 18.9 | 0.053 | 60.8 | 0.9967 | 64.8 |
| last close < 08:00Z (exit) | −20.0 | 20.0 | 0.056 | 64.7 | 0.9920 | 72.9 |
| short stop pre_hi + 0.5·rng | +16.5 | 21.0 | 0.064 | 71.2 | 0.9938 | 71.2 |
| long stop pre_lo − 0.5·rng | −49.8 | 49.8 | 0.158 | 143.0 | 0.9858 | 63.5 |

The level differences are a **basis**, not noise: the futures trade below the CFD by ~19
points while HSIQ6 was front (08-19..08-27) and by 28–65 points on HSIU6 (08-28 onwards;
the CFD tracks the cash/front level, and the Sept contract carries the larger dividend
discount). Across the 11 sessions the entry basis has std 25 points, but **within a
session it cancels**: the entry-to-exit move differs by a median 3.0 points (max 10.5).
On the thin second-month sessions the basis is −60..−75 for the same reason (HSIU6 was
then two months out), and the move still differs by only 4.8 points median.

The one level that is not just basis is the **long stop**: −49.8 median, −143 on 08-21,
because the CFD's pre-open bar low is 45.6 points (median) above the futures' auction
low once the basis is removed. See 3.2.

### 3.2 The pre-open bar and the push (the trigger)

Pre-open bar, liquid sessions, median |futures − CFD| in points: open **43.5**, high 18.5,
low 45.6, close 19.0. High and close are the basis; open and low are not.

| | liquid n=11 | all n=33 |
|---|---|---|
| push correlation | 0.874 | 0.872 |
| sign agreement | 9 / 11 | 28 / 33 |
| median \|push_fut − push_cfd\| | 47.5 pts = **0.144 ATR14** | 24.0 pts = 0.061 ATR14 |
| max \|push diff\| | 79.5 | 95.0 |
| regression push_fut on push_cfd | slope **1.38**, intercept −5 | 1.02 |
| mean \|push\| ratio fut / CFD | **1.69** | 1.17 |
| mean \|push\|/ATR14 | CFD 0.148, futures 0.249 | |
| median pre-bar range | CFD 79.5, futures **114** | 101.5 vs 99 |
| pre-range correlation | 0.64 | 0.65 |

So on the sessions that matter the futures' pre-open push is about 1.4–1.7x the CFD's,
and the disagreement (0.14 ATR) is half the trigger threshold. Where it comes from: the
CFD quotes 01:15Z–08:15Z and 09:15Z–18:45Z (it follows the HKFE day and after-hours
sessions) and then prints a fresh **01:15Z open that is neither the futures' 09:15 HKT
auction first print nor the previous 18:45Z close** — after removing the basis, the CFD
01:15 open is 44 points (median) from the futures' auction open and 58 points from the
futures' prior night close. The broker's opening mark absorbs part of the auction move,
so the CFD's pre-open bar is narrower (80 vs 114 points) and its push is damped. The
CFD's `volume` on that bar (3.3k–4.4k every day, including the day the futures printed
657) is a tick count, not lots, and says nothing about the auction.

### 3.3 Trigger agreement, |push|/ATR14 ≥ 0.3

| sample | CFD fires | futures fire | both | CFD-only | futures-only |
|---|---|---|---|---|---|
| liquid 08-19..09-02 (n=11) | 1 | 4 | **0** | 1 | 4 |
| all 07-20..09-02 (n=33) | 1 | 5 | **0** | 1 | 5 |

Threshold ladder (the gradient, not a re-fit): CFD / futures / both, all 33 sessions —
t=0.15: 14/18/11; 0.20: 11/13/9; 0.25: 5/10/4; **0.30: 1/5/0**; 0.35: 0/3/0; 0.40: 0/1/0.
Agreement is decent when the bar is allowed to fire often and collapses exactly at the
frozen threshold, which sits on the steep part of both distributions.

### 3.4 Per-session detail, liquid sessions

| date | contract | ATR14 | push CFD | push fut | pn CFD | pn fut | trig CFD | trig fut | entry CFD | entry fut | exit CFD | exit fut |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 08-19 | HSIQ6 | 358 | +18.0 | −49 | +0.05 | −0.14 | – | – | 25303.9 | 25285 | 25483.0 | 25463 |
| 08-20 | HSIQ6 | 367 | +58.0 | +40 | +0.16 | +0.11 | – | – | 25790.0 | 25773 | 25741.0 | 25721 |
| 08-21 | HSIQ6 | 357 | +32.5 | +112 | +0.09 | **+0.31** | – | **S** | 25803.0 | 25785 | 26016.0 | 25997 |
| 08-24 | HSIQ6 | 355 | −87.5 | −150 | −0.25 | **−0.42** | – | **L** | 25717.5 | 25698 | 25485.7 | 25459 |
| 08-25 | HSIQ6 | 347 | +39.0 | +60 | +0.11 | +0.17 | – | – | 25650.0 | 25657 | 25495.5 | 25501 |
| 08-26 | HSIQ6 | 343 | −7.0 | +26 | −0.02 | +0.08 | – | – | 25654.3 | 25664 | 25641.3 | 25648 |
| 08-27 | HSIQ6 | 335 | +68.5 | +123 | +0.20 | **+0.37** | – | **S** | 25767.8 | 25776 | 25555.3 | 25574 |
| 08-28 | HSIU6 | 325 | −15.0 | −84 | −0.05 | −0.26 | – | – | 25355.3 | 25295 | 25578.9 | 25515 |
| 08-31 | HSIU6 | 330 | −42.5 | −90 | −0.13 | −0.27 | – | – | 25368.8 | 25308 | 25518.7 | 25454 |
| 09-01 | HSIU6 | 315 | −97.5 | −84 | **−0.31** | −0.27 | **L** | – | 25322.6 | 25278 | 25302.6 | 25257 |
| 09-02 | HSIU6 | 321 | +84.0 | +109 | +0.26 | **+0.34** | – | **S** | 25270.2 | 25242 | 25271.0 | 25238 |

Thin second-month sessions (07-20..08-18, HSIU6 at 5–156 lots in the pre bar): push
sign agreed on 19/22, no CFD trigger, one futures-only trigger on **07-31** (CFD −0.30
rounds up but is −0.296, futures −0.38). Not evidence about the front contract.

### 3.5 Stop-hit outcomes on the six sessions where either feed triggers

| date | rule from | side | stop | on CFD bars | on futures bars | outcome same? |
|---|---|---|---|---|---|---|
| 07-31 (thin) | CFD / fut | L / L | 25701 / 25624 | hit 01:30 / hit 01:30 | hit 01:30 / hit 01:30 | yes |
| 08-21 | CFD / fut | S / S | 25886 / 25909 | hit 01:30 / hit 01:45 | hit 01:30 / hit **06:00** | yes (stop), different bar |
| 08-24 | CFD / fut | L / L | 25639 / 25590 | hit 01:30 / hit 01:30 | hit 01:30 / hit 01:30 | yes |
| 08-27 | CFD / fut | S / S | 25814 / 25853 | time / time | time / time | yes |
| 09-01 | **CFD** (the journalled trade) | L | 25259 | hit 02:00 | hit 01:45 | yes (stop) |
| 09-01 | fut | L | 25210 | **time** | **hit 02:00** | **no** |
| 09-02 | CFD / fut | S / S | 25314 / 25301 | time / time | time / time | yes |

When each feed's own stop is checked on its own bars the stop/time outcome never differs in
this sample. The one cross-feed disagreement is 09-01: the futures-defined stop (50 points
lower, from the wider auction bar) is not reached on CFD bars but is on futures bars.
Entry-to-exit moves on the time-exit sessions differ by 3–10 points (08-27: 10.5).

## 4. Verdict

- **Entry and exit marks: faithful.** The 01:30Z open and the last close before 08:00Z
  track the futures with correlation > 0.99, differ by a basis of ~20 points (HSIQ6) to
  ~60 points (HSIU6 after the roll) that is common to both ends of the trade, and the
  entry-to-exit move differs by 3 points median, 10.5 max. A CFD-journalled time-exit
  trade would have produced essentially the same points on futures.
- **Stops: faithful for shorts, not for longs.** The short stop sits within the basis
  (21 points); the long stop is 50 points (0.16 ATR) further from the market on the CFD
  than on the futures because the CFD's pre-open low is too high. In the sample this did
  not flip a journalled outcome, but it means CFD long trades carry a wider stop than the
  futures rule specifies.
- **The trigger is not faithful, and this is the finding that matters.** The CFD's 01:15Z
  bar is not the HKFE 09:15–09:30 pre-open auction bar: its open is a broker mark ~44
  points off the auction's first print, its range is ~30% narrower, and its push is ~1.4x
  smaller (0.15 vs 0.25 ATR on average). At the frozen threshold the two feeds selected
  **disjoint** session sets: 0 common triggers out of 5 (liquid) / 6 (all). The MHI
  paper stream is therefore journalling a different set of days from the one a futures
  account running the same rule would trade, and its trades cannot be read as a proxy for
  futures fills on the days a futures trader would actually have been in.
- Sessions that would have differed **in trigger**: 08-21, 08-24, 08-27, 09-02 (futures
  fire, CFD does not — all four are futures-rule trades the journal missed), 09-01 (CFD
  fires, futures do not — a journal trade the futures would not have taken), plus 07-31
  on the thin contract. Sessions that differ **in stop-hit outcome**: none when each
  feed's stop is applied to its own bars; 09-01 if the futures' stop is evaluated on CFD
  bars (time on CFD, stop on futures).
- Caveats. n = 11 liquid sessions over three weeks (22 more on a thin second-month
  contract that only supports the basis and alignment findings); the IBKR endpoint will
  not serve older expired HSI months, so this cannot be extended from this session. The
  finding on the pre-open bar is structural (the CFD has no auction to print), not a
  sampling issue, but the magnitudes (1.38x, 0.14 ATR) are three-week estimates. This
  is a fidelity result, not a re-parametrisation: the threshold ladder in 3.3 is shown
  as a gradient, not as a proposal to move the frozen 0.3.

Scripts (scratchpad, not committed): `fid.py` (join and stats), `diag.py` (alignment,
pre-open decomposition, ladder, basis). Nothing outside `backtest/data/probe/` and this
file was written; nothing was committed.
