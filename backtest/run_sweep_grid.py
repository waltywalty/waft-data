"""Full parameter grid for the bias -> sweep -> reclaim strategy."""
import pandas as pd, numpy as np, engine, sweep, warnings, pickle
warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

bars = engine.load_bars()
LIQ = {"dyn_swing": True, "breakout_low": True, "session_extreme": False, "range_opp": False}

print("=== A. RANGE LENGTH x LIQUIDITY LEVEL (reclaim<=3 bars, exit London mid) ===")
rows = []
cache = {}
for L in (5, 15, 30, 60):
    for liq, hold in LIQ.items():
        d = sweep.run(bars, L, liq, 3, require_hold_range=hold)
        cache[(L, liq, 3, False)] = d
        s = sweep.stats(d, "pnl_london_mid")
        if not s: continue
        c = sweep.stats(d, "ctl_london_mid", "breakout_px")
        rows.append({"range": f"{L}m", "liquidity": liq, "fills": s["n"],
                     "fill_rate": round(d.traded.sum() / max((d.bias != 0).sum(), 1), 2),
                     "win%": round(s["win"] * 100, 1), "PF": round(s["pf"], 3),
                     "exp_$": round(s["exp"], 2), "t": round(s["t"], 2),
                     "breakout_PF": round(c["pf"], 3)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== B. EXIT ANCHOR SWEEP (30m range, dynamic swing low, reclaim<=3) ===")
d = cache[(30, "dyn_swing", 3, False)]
rows = []
for a in sweep.ANCHOR_ORDER:
    s = sweep.stats(d, f"pnl_{a}"); c = sweep.stats(d, f"ctl_{a}", "breakout_px")
    if not s: continue
    rows.append({"exit": a, "n": s["n"], "win%": round(s["win"] * 100, 1),
                 "PF": round(s["pf"], 3), "exp_$": round(s["exp"], 2),
                 "total_$": round(s["total"], 0), "t": round(s["t"], 2),
                 "breakout_PF": round(c["pf"], 3)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== C. RECLAIM WINDOW + STOP AT THE SWEEP EXTREME (30m, dyn_swing, London mid) ===")
rows = []
for rb in (1, 2, 3, 6):
    for stop in (False, True):
        d2 = sweep.run(bars, 30, "dyn_swing", rb, stop_at_sweep=stop)
        s = sweep.stats(d2, "pnl_london_mid")
        if not s: continue
        rows.append({"reclaim_bars": rb, "stop_at_sweep": stop, "n": s["n"],
                     "win%": round(s["win"] * 100, 1), "PF": round(s["pf"], 3),
                     "exp_$": round(s["exp"], 2), "t": round(s["t"], 2)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== D. THE SELECTION EFFECT: what happens on days that never sweep? ===")
d = cache[(30, "dyn_swing", 3, False)]
bd = d[d.bias != 0].copy()
swept, nosweep = bd[bd.traded], bd[~bd.traded]
plain = engine.backtest(bars, 30, "london_mid")
plain = plain[plain.traded].set_index("day")
for label, sub in (("swept back (tradeable by this method)", swept), ("never swept", nosweep)):
    idx = [x for x in sub.day if x in plain.index]
    p = plain.loc[idx]
    pf = p.pnl_usd[p.pnl_usd > 0].sum() / max(-p.pnl_usd[p.pnl_usd <= 0].sum(), 1e-9)
    print(f"  {label:40s} n={len(p):4d}  breakout-entry PF={pf:.3f}  exp=${p.pnl_usd.mean():+.2f}")
print("  -> the sweep condition selects, after the fact, the days the bias failed.")

print("\n=== E. INVERTED: after a sweep and reclaim, trade AGAINST the bias ===")
rows = []
for L in (15, 30, 60):
    d2 = sweep.run(bars, L, "dyn_swing", 3, invert=True)
    for a in ("london_open", "london_mid", "pre_ny", "ny_close"):
        s = sweep.stats(d2, f"pnl_{a}")
        if s:
            rows.append({"range": f"{L}m", "exit": a, "n": s["n"], "win%": round(s["win"]*100, 1),
                         "PF": round(s["pf"], 3), "exp_$": round(s["exp"], 2), "t": round(s["t"], 2)})
print(pd.DataFrame(rows).to_string(index=False))
pickle.dump(cache, open("results/sweep_cache.pkl", "wb"))
