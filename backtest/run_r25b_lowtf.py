"""Round 25b: the lower-timeframe extension of the entry-timeframe grid.
Pre-registered in the goal ledger. Judged as a gradient with the 30/60/90m
cells from round 25, not cell by cell."""
import pandas as pd, numpy as np, json, warnings, engine, trades
warnings.filterwarnings("ignore")

gold = engine.load_bars()
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

out = {}
tsets = {}
for L in (5, 10, 15, 20):
    tt = trades.generate(gold, L, stop_r=2.0, entry_cutoff_ldn=8)
    tt["pnl_gross"] = tt.pnl_oz + 0.30                # generate() already took $0.30 cost
    tt["pnl_oz"] = tt.pnl_oz - np.where(tt.reason == "stop", 0.30, 0.0)
    tt["day_ts"] = pd.to_datetime(tt.day)
    tsets[L] = tt

grid = {}
for w in (10, 20, 40):
    cw = trades.corr_series(gold, w)
    for L, tt in tsets.items():
        x = tt[tt.day_ts.map(cw) <= 0.5]
        p = x.pnl_oz / x.entry * 100
        grid[f"w{w}_L{L}"] = dict(
            n=int(len(x)), pf=pf(x.pnl_oz), exp=float(x.pnl_oz.mean()),
            t=float(p.mean() / p.std() * np.sqrt(len(p))) if len(p) > 2 else np.nan,
            stopped=float((x.reason == "stop").mean()),
            med_range=float(x["range"].median()),
            pf_gross=pf(x.pnl_gross))
out["grid"] = grid

# halves for the deployed-window column (w=20), for the gradient read
halves = {}
cw = trades.corr_series(gold, 20)
for L, tt in tsets.items():
    x = tt[tt.day_ts.map(cw) <= 0.5]
    for nm, m in (("h1", x.day_ts < "2024-01-01"), ("h2", x.day_ts >= "2024-01-01")):
        y = x[m]; p = y.pnl_oz / y.entry * 100
        halves[f"L{L}_{nm}"] = dict(n=int(len(y)), pf=pf(y.pnl_oz),
                                    t=float(p.mean() / p.std() * np.sqrt(len(p))) if len(p) > 2 else np.nan)
out["halves_w20"] = halves

# cost sensitivity on the best low-TF cell at w=20 (registered regardless of outcome)
best_L = max((5, 10, 15, 20), key=lambda L: grid[f"w20_L{L}"]["pf"])
x = tsets[best_L][tsets[best_L].day_ts.map(cw) <= 0.5]
sens = {}
for mult in (0.0, 1.0, 2.0):
    adj = x.pnl_gross - mult * 0.30 - np.where(x.reason == "stop", mult * 0.30, 0.0)
    sens[f"x{mult}"] = dict(pf=pf(adj), exp=float(adj.mean()))
out["cost_sens"] = {"cell": f"w20_L{best_L}", **sens}

json.dump(out, open("results/r25b_lowtf.json", "w"), indent=1)

print("=== LOWER-TIMEFRAME GRID (corr<=0.5; PF net / t / stopped% / med range $) ===")
for w in (10, 20, 40):
    row = "  ".join(f"L{L}m: {grid[f'w{w}_L{L}']['pf']:.3f}/{grid[f'w{w}_L{L}']['t']:+.2f}"
                    f"/{grid[f'w{w}_L{L}']['stopped']*100:.0f}%/${grid[f'w{w}_L{L}']['med_range']:.1f}"
                    for L in (5, 10, 15, 20))
    print(f"  w={w:>2}d: {row}")
print("\n  gross-vs-net at w=20:",
      {f"L{L}": f"{grid[f'w20_L{L}']['pf_gross']:.3f}->{grid[f'w20_L{L}']['pf']:.3f}"
       for L in (5, 10, 15, 20)})
print("\n  halves at w=20:")
for L in (5, 10, 15, 20):
    a, b = halves[f"L{L}_h1"], halves[f"L{L}_h2"]
    print(f"    L{L:>2}m: 2020-23 PF {a['pf']:.3f} t {a['t']:+.2f} (n={a['n']})   "
          f"2024-25 PF {b['pf']:.3f} t {b['t']:+.2f} (n={b['n']})")
print(f"\n  cost sensitivity {out['cost_sens']['cell']}:",
      {k: f"PF {v['pf']:.3f}" for k, v in sens.items()})
