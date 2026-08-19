"""Risk overlays + a randomisation null for the whole search."""
import pandas as pd, numpy as np, engine, entries
rng = np.random.default_rng(7)
bars = engine.load_bars()

print("=== 1. RISK OVERLAYS (30m range, London-close exit; stop/target as multiples of the Asia range) ===")
rows = []
for stop in (None, 0.5, 1.0, 2.0):
    for targ in (None, 1.0, 2.0, 3.0):
        t = entries.backtest_entry(bars, 30, "london_close", stop_mult=stop, target_mult=targ)
        m = engine.metrics(t, "")
        tt = t[t.traded]
        rows.append({"stop": stop or "-", "target": targ or "-", "n": m["n"],
                     "win%": round(m["win_rate"]*100, 1), "PF": round(m["profit_factor"], 3),
                     "exp_$": round(m["exp_usd"], 2), "maxDD%": round(m["max_dd_pct"], 1),
                     "t": round(m["t_stat"], 2),
                     "stopped%": round((tt.exit_reason == "stop").mean()*100, 1),
                     "target%": round((tt.exit_reason == "target").mean()*100, 1)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== 2. RANDOMISATION NULL ===")
print("Keep every entry/exit TIME the strategy chose, but pick the side at random.")
print("If the breakout signal carries information, the real result should sit in the far right tail.\n")
configs = [(L, a) for L in (5, 15, 30, 45, 60, 90) for a in ("pre_london", "london_open", "london_close")]
real, sims = {}, {}
for L, a in configs:
    t = engine.backtest(bars, L, a)
    t = t[t.traded]
    gross = (t.exit.values - t.entry.values)          # per-$ move, side applied below
    real[(L, a)] = ((t.side.values * gross - 0.30) / t.entry.values * 100).sum()
    sims[(L, a)] = gross, t.entry.values

N = 5000
best_real = max(real.values())
best_cfg = max(real, key=real.get)
maxes = np.empty(N)
per_cfg_p = {}
draws = {k: np.empty(N) for k in configs}
for i in range(N):
    vals = []
    for k, (gross, entry) in sims.items():
        side = rng.choice([-1, 1], size=len(gross))
        v = ((side * gross - 0.30) / entry * 100).sum()
        draws[k][i] = v
        vals.append(v)
    maxes[i] = max(vals)
for k in configs:
    per_cfg_p[k] = (draws[k] >= real[k]).mean()

print(f"Best configuration found in the search : {best_cfg[0]}m / {best_cfg[1]}  =  {best_real:+.1f}% total")
print(f"  p-value for that config on its own                 : {per_cfg_p[best_cfg]:.3f}")
print(f"  p-value AFTER accounting for searching {len(configs)} configs : {(maxes >= best_real).mean():.3f}")
print(f"  random search would produce a best config of {np.percentile(maxes,50):+.1f}% "
      f"(median) and {np.percentile(maxes,95):+.1f}% (95th pct) with no signal at all")

print("\n  per-configuration p-values (chance of this result from random directions):")
for k in sorted(configs, key=lambda c: -real[c])[:8]:
    print(f"    {k[0]:>3}m / {k[1]:<13} {real[k]:+7.1f}%   p={per_cfg_p[k]:.3f}")

print("\n=== 3. WHY 2024-25 LOOKS BETTER: the strategy vs passive exposure, per year ===")
t = engine.backtest(bars, 30, "london_close"); t = t[t.traded].copy()
t["yr"] = t.t_fill.dt.year
g = t.groupby("yr").apply(lambda x: pd.Series({
    "n": len(x),
    "strategy_%": round(x.pnl_pct.sum(), 1),
    "always_long_%": round(((x.exit - x.entry) / x.entry * 100).sum(), 1),
    "gold_daily_range_$": round((x.range_size).mean(), 2),
    "avg_price": round(x.entry.mean(), 0)}), include_groups=False)
print(g.to_string())
