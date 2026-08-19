"""Is the negative result an artefact of costs/fills, or is the signal itself wrong?"""
import pandas as pd, numpy as np, engine, pickle

bars = engine.load_bars()
logs = pickle.load(open("results/grid_logs.pkl", "rb"))

# ---------- 1. cost sensitivity (gross vs net) --------------------------------
print("=== 1. COST SENSITIVITY: profit factor at different round-trip costs ===")
rows = []
for L in (5, 15, 30):
    for anchor in engine.EXITS:
        t = logs[(L, anchor)]
        t = t[t.traded]
        r = {"range": f"{L}m", "exit": anchor}
        for c in (0.0, 0.15, 0.30, 0.60):
            pnl = t.pnl_usd + 0.30 - c          # logs were built at $0.30
            w, l = pnl[pnl > 0].sum(), -pnl[pnl <= 0].sum()
            r[f"PF@${c:.2f}"] = round(w / l, 3)
        rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

# ---------- 2. fill assumption ------------------------------------------------
print("\n=== 2. FILL ASSUMPTION (30m range) ===")
for anchor in ("pre_london", "london_close"):
    for fill in ("close", "next_open"):
        m = engine.metrics(engine.backtest(bars, 30, anchor, fill=fill), "")
        print(f"  30m/{anchor:12s} fill={fill:9s} PF={m['profit_factor']:.3f} "
              f"WR={m['win_rate']*100:.1f}% exp=${m['exp_usd']:+.3f}")

# ---------- 3. long vs short, and the drift benchmark -------------------------
print("\n=== 3. LONG vs SHORT (breakout direction), and buy&hold over the same window ===")
for L in (5, 15, 30):
    for anchor in ("pre_london", "london_close"):
        t = logs[(L, anchor)]; t = t[t.traded]
        lo, sh = t[t.side == 1], t[t.side == -1]
        # benchmark: hold long from range close to the same exit, every day
        bh = t.side * 0 + 1
        print(f"  {L:2d}m/{anchor:12s} LONG n={len(lo):4d} PF={lo.pnl_usd[lo.pnl_usd>0].sum()/max(-lo.pnl_usd[lo.pnl_usd<=0].sum(),1e-9):.2f} "
              f"exp=${lo.pnl_usd.mean():+.2f} | SHORT n={len(sh):4d} "
              f"PF={sh.pnl_usd[sh.pnl_usd>0].sum()/max(-sh.pnl_usd[sh.pnl_usd<=0].sum(),1e-9):.2f} exp=${sh.pnl_usd.mean():+.2f}")

# ---------- 4. the inverse strategy (fade the breakout) -----------------------
print("\n=== 4. INVERSE: fade the breakout (same entries, opposite side, $0.30 cost) ===")
rows = []
for L in (5, 15, 30):
    for anchor in engine.EXITS:
        t = logs[(L, anchor)].copy(); t = t[t.traded]
        pnl = -(t.pnl_usd + 0.30) - 0.30          # flip gross, re-apply cost
        pct = pnl / t.entry * 100
        w, l = pnl[pnl > 0].sum(), -pnl[pnl <= 0].sum()
        sd = pct.std()
        rows.append({"range": f"{L}m", "exit": anchor, "n": len(t),
                     "win_rate": round((pnl > 0).mean(), 3),
                     "PF": round(w / l, 3), "exp_usd": round(pnl.mean(), 3),
                     "total_pct": round(pct.sum(), 1),
                     "t_stat": round(pct.mean() / sd * np.sqrt(len(pct)), 2)})
print(pd.DataFrame(rows).to_string(index=False))

# ---------- 5. per-year stability of the best raw config ----------------------
print("\n=== 5. PER-YEAR (30m range) ===")
for anchor in ("pre_london", "london_close"):
    t = logs[(30, anchor)]; t = t[t.traded].copy()
    t["yr"] = t.t_fill.dt.year
    g = t.groupby("yr").apply(lambda x: pd.Series({
        "n": len(x), "win%": round((x.pnl_usd > 0).mean() * 100, 1),
        "PF": round(x.pnl_usd[x.pnl_usd > 0].sum() / max(-x.pnl_usd[x.pnl_usd <= 0].sum(), 1e-9), 2),
        "tot_$": round(x.pnl_usd.sum(), 1)}), include_groups=False)
    print(f"  -- 30m / {anchor} --"); print(g.to_string())
