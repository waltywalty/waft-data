"""Consolidate every result into results/summary.json for the report."""
import pandas as pd, numpy as np, engine, entries, json

bars = engine.load_bars()
out = {}

# core grid (the 12 combinations actually specified)
grid = []
for L in (5, 15, 30):
    for a in ("pre_london", "london_open", "london_mid", "london_close"):
        t = engine.backtest(bars, L, a)
        m = engine.metrics(t, "")
        grid.append({"range": L, "exit": a, "n": m["n"], "win": m["win_rate"],
                     "pf": m["profit_factor"], "exp_usd": m["exp_usd"],
                     "total_pct": m["total_pct"], "dd": m["max_dd_pct"], "t": m["t_stat"],
                     "long": m["long"], "short": m["short"]})
out["grid"] = grid

# extended range lengths at the best exit
ext = []
for L in (5, 15, 30, 45, 60, 90, 120):
    m = engine.metrics(engine.backtest(bars, L, "london_close"), "")
    ext.append({"range": L, "pf": m["profit_factor"], "win": m["win_rate"],
                "exp_usd": m["exp_usd"], "t": m["t_stat"], "n": m["n"]})
out["range_sweep"] = ext

# bias decomposition
ref = {}
for d, grp in bars.groupby(bars.index.date):
    t0 = engine.session_start_utc(pd.Timestamp(d))
    s = grp[grp.index >= t0]
    if len(s):
        ref[d] = (float(s.iloc[0].open), float(s.iloc[-1].close))
ref = pd.DataFrame(ref, index=["open0130", "close2100"]).T
bias = []
for L in (5, 15, 30, 60):
    t = engine.backtest(bars, L, "london_close")
    t = t[t.traded].join(ref, on="day").dropna(subset=["open0130"])
    bias.append({"range": L,
                 "hit_from_open": float((np.sign(t.close2100 - t.open0130) == t.side).mean()),
                 "hit_from_entry": float((np.sign(t.close2100 - t.entry) == t.side).mean()),
                 "already_moved": float((t.side * (t.entry - t.open0130)).mean()),
                 "range_size": float(t.range_size.mean()),
                 "whipsaw": float(np.nanmean(np.where(t.side == 1,
                        t.mae >= (t.entry - t.range_low), t.mae >= (t.range_high - t.entry))))})
out["bias"] = bias
out["always_long_hit"] = float((ref.close2100 > ref.open0130).mean())

# equity curves for the report
curves = {}
for L, a in [(30, "london_close"), (60, "london_close"), (15, "pre_london"), (5, "london_open")]:
    t = engine.backtest(bars, L, a)
    t = t[t.traded].sort_values("t_fill")
    eq = t.pnl_pct.cumsum()
    idx = np.linspace(0, len(eq) - 1, min(len(eq), 260)).astype(int)
    curves[f"{L}m_{a}"] = {"x": [str(t.t_fill.iloc[i].date()) for i in idx],
                           "y": [round(float(eq.iloc[i]), 2) for i in idx]}
# passive benchmark on the 60m entry/exit times
t = engine.backtest(bars, 60, "london_close"); t = t[t.traded].sort_values("t_fill")
eqp = ((t.exit - t.entry) / t.entry * 100).cumsum()
idx = np.linspace(0, len(eqp) - 1, min(len(eqp), 260)).astype(int)
curves["passive_long"] = {"x": [str(t.t_fill.iloc[i].date()) for i in idx],
                          "y": [round(float(eqp.iloc[i]), 2) for i in idx]}
out["curves"] = curves

# per-year for 30m and 60m
yrs = {}
for L in (30, 60):
    t = engine.backtest(bars, L, "london_close"); t = t[t.traded].copy()
    t["yr"] = t.t_fill.dt.year
    yrs[L] = [{"yr": int(y), "n": len(x), "win": float((x.pnl_usd > 0).mean()),
               "pf": float(x.pnl_usd[x.pnl_usd > 0].sum() / max(-x.pnl_usd[x.pnl_usd <= 0].sum(), 1e-9)),
               "pct": float(x.pnl_pct.sum()),
               "passive": float(((x.exit - x.entry) / x.entry * 100).sum())}
              for y, x in t.groupby("yr")]
out["years"] = yrs

# risk overlay grid
risk = []
for stop in (None, 0.5, 1.0, 2.0):
    for targ in (None, 1.0, 2.0, 3.0):
        m = engine.metrics(entries.backtest_entry(bars, 30, "london_close",
                                                  stop_mult=stop, target_mult=targ), "")
        risk.append({"stop": stop, "target": targ, "pf": m["profit_factor"],
                     "win": m["win_rate"], "exp": m["exp_usd"], "dd": m["max_dd_pct"]})
out["risk"] = risk

# entry mechanics
ent = []
for L in (30, 60):
    for mode, pb in [("confirm_close", 0), ("touch", 0), ("retest", 0.0), ("pullback", 0.5)]:
        m = engine.metrics(entries.backtest_entry(bars, L, "london_close", mode=mode, pullback=pb), "")
        ent.append({"range": L, "mode": mode if mode != "pullback" else f"pullback{pb}",
                    "n": m["n"], "fill": m["trade_rate"], "pf": m["profit_factor"],
                    "win": m["win_rate"], "exp": m["exp_usd"]})
out["entries"] = ent

out["meta"] = {"bars": int(len(bars)), "start": str(bars.index.min().date()),
               "end": str(bars.index.max().date()), "cost": 0.30}
json.dump(out, open("results/summary.json", "w"), indent=1)
print("written:", len(json.dumps(out)), "bytes")
print(json.dumps(out["bias"], indent=1))
print(json.dumps(out["years"][60], indent=1))

# --- appended: consistent %-based cost sensitivity for the 60m config --------
import engine as _e
_t = _e.backtest(bars, 60, "london_close"); _t = _t[_t.traded]
cs = []
for c in (0.0, 0.15, 0.30, 0.50, 0.75, 1.00):
    p = _t.pnl_usd + 0.30 - c
    pct = p / _t.entry * 100
    cs.append({"cost": c, "pf_pct": float(pct[pct > 0].sum() / -pct[pct <= 0].sum()),
               "exp_usd": float(p.mean())})
S2 = json.load(open("results/summary.json")); S2["cost_sens_60"] = cs
S2["n_losing"] = int(sum(1 for g in S2["grid"] if g["pf"] < 1.0))
json.dump(S2, open("results/summary.json", "w"), indent=1)
print("cost sensitivity (%-based):", [(c["cost"], round(c["pf_pct"],3)) for c in cs])
print("configs with PF<1:", S2["n_losing"], "of", len(S2["grid"]))
