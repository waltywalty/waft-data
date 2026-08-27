"""Round 32c: the Scribd "Futures Strategies Performance Summary" sheet.

Source: scribd.com/document/1067645834 (retrieved 2026-08-27 via remote
browser embed viewer; 2 pages, no author, no rules - only a 32-row results
table, "backtested 2015-2026, Round 5: plateau-tuned parameters + best-fit
instrument per strategy" across 28 contracts, and an admission that the
backtests are FRICTIONLESS with "win rate" = share of profitable bars).

Nothing is runnable, so per the pre-registration this audits the sheet's
own numbers:
 1. cost arithmetic on the four high-frequency rows: implied gross edge
    per "trade" vs plausible friction (1 tick .. commission+spread);
 2. Monte Carlo selection null: 28 zero-edge return streams over 11 years,
    keep the best Sharpe per strategy - the inflation you get for free by
    "best-fit instrument" selection, before any parameter tuning.
Outputs results/r32_scribd.json.
"""
import numpy as np, json

# (name, ticker, total_return_pct, trades, pf, years, point_value, approx_price,
#  tick_size) - contract specs are CME standard; approx_price = mid-window level.
HF_ROWS = [
    ("Day Trading (5-min)", "GC", 597.56, 469_101, 1.02, 11, 100, 1900, 0.10),
    ("Scalping (5-min)", "NQ", 183.01, 133_031, 1.01, 11, 20, 12000, 0.25),
    ("Order Flow (proxy)", "NQ", 166.55, 551_528, 1.01, 11, 20, 12000, 0.25),
    ("Opening Range Breakout", "NQ", 107.51, 195_406, 1.01, 11, 20, 12000, 0.25),
]

out = {"cost_arithmetic": []}
print("=== 32c-1: cost arithmetic on the sheet's high-frequency rows ===")
print(f"{'row':>24} {'trades':>8} {'net/trade':>10} {'1-tick RT':>10} {'net after 1 tick':>16}")
for name, tk, ret, n, pf, yrs, pv, px, tick in HF_ROWS:
    # net return per trade on notional, from the sheet's own total return
    # (compounded): per-trade edge in fraction of notional
    per_trade = (1 + ret / 100) ** (1 / n) - 1
    edge_pts = per_trade * px                     # implied net points per trade
    tick_cost = 2 * tick                          # 1 tick per side, points
    after = edge_pts - tick_cost
    out["cost_arithmetic"].append(dict(
        row=name, ticker=tk, trades=n, edge_pts=float(edge_pts),
        one_tick_rt_pts=float(tick_cost), edge_after_1tick=float(after),
        dies=bool(after < 0)))
    print(f"{name:>24} {n:>8,} {edge_pts:>+9.4f}p {tick_cost:>9.2f}p {after:>+15.4f}p"
          f"  {'DEAD' if after < 0 else 'survives'}")

# --- selection null: best of 28 zero-edge instruments, 11 years daily ---
rng = np.random.default_rng(32)
YRS, NDAYS, NINSTR, NSTRAT, SIMS = 11, 252 * 11, 28, 32, 2000
best_sharpes, best_cagrs = [], []
for _ in range(SIMS):
    # daily zero-mean returns at 20% annualized vol (their own vol target)
    r = rng.normal(0, 0.20 / np.sqrt(252), size=(NINSTR, NDAYS))
    sh = r.mean(axis=1) / r.std(axis=1) * np.sqrt(252)
    j = np.argmax(sh)
    best_sharpes.append(sh[j])
    best_cagrs.append((np.prod(1 + r[j]) ** (1 / YRS) - 1))
best_sharpes, best_cagrs = np.array(best_sharpes), np.array(best_cagrs)
out["selection_null"] = dict(
    n_instruments=NINSTR, years=YRS, sims=SIMS,
    exp_max_sharpe=float(best_sharpes.mean()),
    sharpe_q10_q90=[float(np.quantile(best_sharpes, q)) for q in (0.1, 0.9)],
    exp_max_cagr=float(best_cagrs.mean()),
    note="zero-edge instruments at their stated 20% vol target; instrument "
         "selection only - parameter tuning ('Round 5 plateau-tuned') stacks "
         "on top of this")
# how much of their table is inside the null band
sheet_sharpes = [1.00, 0.96, 1.15, 0.72, 0.91, 0.69, 0.89, 0.81, 0.89, 0.92,
                 0.77, 0.79, 0.86, 0.63, 0.60, 0.60, 0.67, 0.88, 0.61, 0.56,
                 0.68, 0.60, 0.54, 0.65, 0.65, 0.70, 0.85, 0.51, 0.56, 0.81,
                 0.60, 0.05]
thr = float(np.quantile(best_sharpes, 0.9))
out["sheet_vs_null"] = dict(
    median_sheet_sharpe=float(np.median(sheet_sharpes)),
    null_q90=thr,
    rows_below_null_q90=int(np.sum(np.array(sheet_sharpes) <= thr)),
    rows_total=len(sheet_sharpes))
print(f"\n=== 32c-2: best-of-28 selection null ({SIMS} sims) ===")
print(f"expected max Sharpe from zero-edge selection: {best_sharpes.mean():.2f} "
      f"(q10..q90 {np.quantile(best_sharpes,0.1):.2f}..{thr:.2f})")
print(f"sheet median Sharpe {np.median(sheet_sharpes):.2f}; "
      f"{out['sheet_vs_null']['rows_below_null_q90']}/{len(sheet_sharpes)} rows sit at or "
      f"below the null's 90th percentile - explainable by instrument selection alone")

json.dump(out, open("results/r32_scribd.json", "w"), indent=1, default=float)
