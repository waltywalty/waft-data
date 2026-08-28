# Strategy repair taxonomy and the repair protocol

Adopted 2026-08-28 (round 41b) in answer to the question: "instead of mining
the data for what makes a backtest perfect, can we learn what KINDS of
additions make strategies work, reason from mechanism about why a given
strategy fails, and fix that - without looking at the data?"

Yes. That is how legitimate quant repair works. This file is the knowledge
base: the repair classes that exist, the failure mechanism each one targets,
and what our own ledger already knows about each. A repair is only allowed
into a test when it is TIED to a diagnosed failure mechanism - "try adding
an RSI filter" is mining with extra steps; "this strategy's losses cluster
in high-vol regimes, so a vol gate targets its actual failure" is a
hypothesis.

## The repair classes

**1. Regime / trend gates** (fixes: strategy only works in one market state)
   - Tools: HTF trend filters, vol-regime splits, correlation-state gates.
   - Mechanism required: the strategy's losses must CLUSTER in an
     identifiable state; the gate must change conditional expectation, not
     just trade count.
   - Our evidence: the deployed gold rule's corr(gold,AUD) gate is a
     working example (both halves, smooth gradient). The r39 SMA20 HTF
     bias gate is a failed example: removed 45% of trades, changed
     per-trade expectation not at all. Sources describe regime failure as
     the #1 live-vs-backtest gap (strategies fitted to one vol state).

**2. Volatility normalization** (fixes: fixed-point parameters are
   volatility-blind)
   - Tools: ATR- or range-scaled stops/targets, ATR position sizing.
   - Our evidence: r36 showed fixed 10-pt brackets destroy all three
     deployed systems while their range-scaled exits survive; MHI's
     cost=target arithmetic. This class is close to a free lunch: it makes
     one parameter set portable across instruments and years. Any future
     intraday system should be specified in ATR/range units from birth.

**3. Time-of-day / session concentration** (fixes: edge exists only in a
   window, diluted by trading all day)
   - Mechanism required: the window must be identified by mechanism (open
     auction, settlement, session handoff), not by scanning 26 half-hours.
   - Our evidence: r34 session atlas (volatility highly structured,
     direction flat); NY-PM displacement logged as a watch hypothesis with
     a dedicated pre-registered test still owed. The gold rule's
     no-entry-after-London-08:00 clause is a working member of this class.

**4. Cost engineering** (fixes: real gross edge smaller than round trip)
   - Tools: cheaper instrument, fewer trades (higher-conviction subset),
     passive/limit execution, longer holding per signal.
   - Our evidence: r37b identified FP5 displacement as exactly this
     failure (+0.2..+0.5 gross, dies inside one RT). r38 showed the naive
     passive fix (retracement limits) is adversely selected - the repair
     class is real but the queue-position version is untestable on OHLC.
     Signal-frequency reduction (trade only the best decile) is the
     testable member.

**5. Exit asymmetry / trade management** (fixes: right-tail amputation,
   drawdown harvesting)
   - Tools: trailing stops, partial exits, time stops matched to the
     signal's measured decay horizon.
   - Our evidence: r36/r37 - the failure is usually the TARGET (capping
     winners), not the stop. An exit must be matched to WHERE the
     expectation lives (gold rule: trend-day holds to 16:00). Exit changes
     multiply expectation; they never create it (r35d principle).

**6. Confirmation stacking / confluence** (claimed fix: filter out "bad"
   signals by requiring more indicators)
   - Our evidence: consistently the WEAKEST class. r39 (bias alignment),
     r34b/r40 (delta confirmation), r27 (FVG confluence) all null; the
     footprint program's confluence-cap rule exists for this reason.
     Stacked confirmations mostly shrink n and inflate the search space.
     Treat any proposed member of this class with maximum suspicion.

**7. Signal-horizon matching** (fixes: measuring/exiting a signal at the
   wrong timescale)
   - Tools: hold to the horizon where the event study showed the effect;
     enter at the TF where the signal is defined (r35d: signal-TF vs
     entry-TF separation is legitimate only after event-level expectation
     is proven).
   - Our evidence: r30 (overnight drift is a daily-scale effect), r39c
     (EOD hold of an intraday signal - correctly sized the horizon, effect
     still zero, but the TEST design was the right member of this class).

## The repair protocol (binding for all repair rounds)

1. One failed strategy at a time, named before any new data work, with a
   WRITTEN diagnosis: which failure mechanism above, and what evidence
   from the original round supports that diagnosis.
2. The repair grid is written down before running, every knob tied to the
   diagnosis, bounded (<= ~50 variants), and run on IN-SAMPLE ONLY
   (everything except the last 25% of that instrument's data).
3. Selection on IS by a pre-stated metric, gradient inspected (a spiky
   winner whose neighbors disagree is discarded as noise regardless of
   its numbers).
4. ONE selected spec goes to the out-of-sample block, evaluated ONCE,
   against a pre-stated pass bar: same sign, t >= 2, PF >= 1.15, and a
   cost-sensitivity pass. The OOS block for that strategy is then BURNED -
   pass or fail, no second attempt for that repair family. Iterating
   repair->OOS->repair converts the holdout into training data
   (holdout contamination; see sources below).
5. An OOS pass does NOT mean deployment: it graduates to the paper/SPRT
   stage (the second, truly live out-of-sample), like every other
   candidate. Under this bar a null strategy passes OOS by luck ~2-5% of
   the time; the program tracks attempts so the expected number of false
   graduates stays visible (N attempts x ~3% each).
6. Every attempt is counted in the goal ledger, including abandoned grids.

## Why "keep testing until something passes IS+OOS" needs the counter

Each honest one-shot OOS attempt has a small false-pass rate (~2-5% at the
bar above). Run 30 repair attempts and the expected false graduates
approach one - WITHOUT any real edge existing. The ledger's attempt count
plus the paper-trade stage is what keeps that survivor from being trusted
on the OOS pass alone. This is the program-level analogue of the max-stat
correction inside a single round.

## Sources (surveyed 2026-08-28)

- Out-of-sample honesty and holdout contamination: algotrader.ch
  "Out-of-Sample Testing: Where It Breaks, How To Do It Honestly";
  mbrenndoerfer.com "Backtesting & Simulation" (test-set conversion).
- Multiple testing and selection bias: Bailey & Lopez de Prado, Deflated
  Sharpe Ratio (overfit strategies systematically underperform OOS; a
  strategy that does BETTER OOS than IS is itself a contamination flag).
- Walk-forward methodology: Pardo (1992) via IBKR Quant campus and
  Wikipedia "Walk forward optimization".
- Regime dependence as the primary live-failure mode: buildalpha.com
  robustness-testing guide; quantifiedstrategies.com backtest-vs-live.
- ATR-based sizing/stops as the standard volatility-normalization tools:
  TradersPost, NinjaTrader, LuxAlgo ATR guides.
