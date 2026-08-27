# Project Footprint — Phase 1 concept map (institutional footprints on ES/NQ/RTY/GC)

Working document for the smart-money-alignment arc (opened round 33). Scope: what is
*actually* detectable with price + volume in TradingView/Pine v5, ranked by evidence,
with the microstructure logic and this repo's own test results attached. House rule:
nothing on this map gets strategy weight until it passes the Phase 4 pipeline
(pre-registration, both-halves, drift null where long-biased, costs, multiplicity).

## The core inversion (read first)

Institutional execution is engineered to be INVISIBLE. Parent orders are sliced by
VWAP/TWAP/POV/IS algos across hours precisely so no candle carries their signature;
icebergs exist to hide size even from the visible book. So the retail-SMC story —
"this candle is where institutions placed orders" — is backwards. What price+volume
bars CAN show is not hidden intent but **auction outcomes**: participation anomalies
(volume where none is scheduled), effort-vs-result divergences (absorption), failed
breaks of salient levels (rejection), and where on the clock persistent pressure
lives (session drift decomposition). We are not tracking whales; we are measuring
auction failures. Those are real, testable, and occasionally tradeable.

## Evidence grades

A = literature + our own positive/structural results. B = sound mechanism, not yet
tested by us in this form. C = mechanism partly real, our own tests NEGATIVE in
adjacent form. D = folklore causation, no credible empirical support anywhere.

## Ranked footprints

| # | Footprint | Grade | Pine | Role | Microstructure logic / our evidence |
|---|---|---|---|---|---|
| 1 | Session architecture (RTH/Globex, opens, closes, settle, auction times) | A | full | chassis | Intraday vol/volume U-shape is the most replicated fact in microstructure; informed + forced flow concentrate at opens/closes. Our MHI stream and gold rule are session-structured; r26 SGE auction candle p=0.004 descriptive. |
| 2 | Relative volume vs time-of-day baseline (RVOL curve) | A- | full | filter/confirm | Execution algos benchmark to historical volume curves; deviation = non-routine participation (Easley–O'Hara lineage). Requires REAL CME volume (ES1! etc.), never CFD symbols. |
| 3 | Overnight/intraday flow decomposition as HTF bias | A | full | bias | Our r30: index drift lives close→open (SPX +2.3, NDX +3.8 bps/night gross, halves same-sign); intraday ~nothing. Gold clock differs (London morning). This is the honest "institutional flow" read. |
| 4 | Absorption proxy (effort vs result at extremes) | B | partial | confirm | Passive interest soaking aggression = high volume + small progress + close off extreme. Real in book studies; bars only shadow it. CVD proxy via lower-TF up/down split feeds this (noisy, stated as such). |
| 5 | Displacement / range-expansion regime | B | full | regime/trigger | Initiative vs rotational auction; cousin of intraday-momentum literature (first-30m → last-30m, weakened post-publication). Range vs ATR percentile + follow-through stats. |
| 6 | Liquidity sweep / failed break of salient levels (PDH/PDL, ON H/L, OR) | C+ | full | candidate setup | Stops do cluster at salient levels and a failed break IS auction information; the "hunting" narrative is folklore. OUR TESTS: Judas sweep on gold DEAD (r8); sweep-and-reclaim added nothing (AUDUSD). Index RTH variants = the one open question; must earn Phase 4 pass. |
| 7 | MOC / rebalance / calendar flow | B- | partial | context/avoid | Index funds MUST trade the close (published MOC imbalances are real institutional flow) but Pine sees only calendar + price/volume shadows. Our r15 TOM/calendar cells on indices: negative at our bar. Use to AVOID fading forced-flow windows. |
| 8 | Order blocks / breakers | D | full | visual only | No microstructure basis: sliced parent orders do not live at one candle; resting liquidity is invisible without DOM. Renamed supply/demand zones. No credible empirical support; adjacent cells dead in our r27/r31 work. Drawn for education, zero strategy weight. |
| 9 | FVG / imbalance | D | full | visual only | Our r27: 0/12 runnable cells (gold + indices). Circulating "70% fill" claims are base rates without time-stops or opportunity cost. Descriptive fill stats ≠ edge. |
| 10 | Delta/CVD proxy (lower-TF up/down volume) | proxy | proxy | instrument | Best available shadow of true aggressor delta; moderate fidelity at best; feeds #4. Never presented as real delta. |

## What Pine cannot see (say it plainly)

- DOM / L2: resting liquidity, spoofing, icebergs (designed to be invisible even in L2).
- True delta: needs per-trade aggressor tagging; bar volume has no side.
- MBO order-by-order data, auction imbalance feeds (MOC/MOO), block/EFP prints.
- Options flow (the actual telegraph for much "smart money") and dealer hedging.
- COT: weekly + delayed; our r24 replication on gold: max-stat p 0.76 at daily horizon.
- Intrabar event order (H before L?) — affects both signals and the strategy tester;
  bar-magnifier only partially repairs it.
- TradingView practicals: CFD symbols carry synthetic volume (use CME ES1!/NQ1!/RTY1!/GC1!);
  continuous-contract roll method changes level-based logic; intraday history depth is
  plan-limited, so the Pine tester window is short — validation happens on OUR data.

## Instrument notes

- **ES**: deepest book of the four; footprints smallest, efficiency highest; sweeps of
  salient levels mostly noise; absorption stats cleanest (lowest noise floor).
  Clock: 09:30 open, 10:00 data, 15:50–16:00 MOC window.
- **NQ**: ~1/5 ES depth, higher vol, trendier; displacement carries further; strongest
  overnight drift in our r30. Sweep-failure statistics likely differ from ES in sign.
- **RTY**: thinnest; wider effective spread taxes confirmation-lag entries hardest;
  rate/breadth regime beta. Data note: our own RTY intraday feed ends 2020-05 —
  Phase 4 on RTY runs on the shorter window or a refreshed source.
- **GC**: different clock (London AM/PM fixes, COMEX settle ~13:30 ET, Asia overnight,
  SGE 10:15 HKT auction — r26: strongest descriptive signal in the repo, unmonetizable
  at 50.8% hit) and different participants (hedgers, CBs, ETF creation). Volume curve
  bimodal London/NY. London-open sweep folklore tested on gold: dead (r8).

## Phase 2 shortlist (proposed, pending agreement)

M1 Session Map (chassis) · M2 RVOL engine · M3 HTF Bias (overnight/intraday + trend
state) · M4 Absorption proxy (+CVD-proxy submodule) · M5 Displacement meter ·
M6 Liquidity Levels & Sweep detector (PDH/PDL/ONH/ONL/OR + failure-swing logic) ·
M7 SMC Visuals (OB/FVG, tagged visualization-only until validated).

Phase 3 rule, registered now: confluence gates are capped and pre-registered before
any backtest — the r27 noise demonstration (264 coin-flip combos → "best" PF 1.53)
is the standing reason unstructured stacking is refused.
