"""The daily-structure Judas-sweep strategy, gridded and stress-tested.

Panels:
 1. main grid: session {asia,london,ny} x bias {sma20,mom20,hhll}
    x target {1R,2R,3R,opp,session_end}  (45 cells)
 2. entry diagnostics: how often each stage of the setup fires
 3. variations on a FIXED default cell (london / sma20 / 2R - chosen before any
    results were seen: the classic Judas story is the London open sweeping Asia)
 4. gold/AUD correlation overlay on the fixed cell
 5. honest OOS: rank the 45 cells on pre-2024 t only, read 2024-25
"""
import pandas as pd, numpy as np, warnings, json, pickle
import engine, structure, judas, trades
warnings.filterwarnings("ignore")

bars = engine.load_bars()
LV = structure.build_levels(bars)
DAILY = structure.fx_daily(bars)
BIAS = {m: structure.daily_bias(DAILY, m) for m in ("sma20", "mom20", "hhll")}
CORR = trades.corr_series(bars, 20)
OUT = {}
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
print(f"levels: {len(LV)} ({LV.t_swept.isna().sum()} never swept)")


def line(lbl, d):
    s = judas.stats(d)
    if s:
        print(f"   {lbl:44s} n={s['n']:>4} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
              f"exp={s['exp']:+.2f} avgR={s['avg_r']:+.2f} t={s['t']:+.2f}")
    else:
        x = d[d.traded] if "traded" in d else d
        print(f"   {lbl:44s} too few trades (n={len(x)})")
    return s


print("\n=== 1. MAIN GRID ===")
logs, rows = {}, []
for sess in ("asia", "london", "ny"):
    for bm in ("sma20", "mom20", "hhll"):
        for tgt in ("1R", "2R", "3R", "opp", "session_end"):
            d = judas.run(bars, LV, BIAS[bm], session=sess, target=tgt)
            logs[(sess, bm, tgt)] = d
            s = line(f"{sess:6s} / {bm:5s} / {tgt}", d)
            if s:
                rows.append({"session": sess, "bias": bm, "target": tgt, **s})
res = pd.DataFrame(rows)
res.to_csv("results/judas_grid.csv", index=False)
OUT["grid"] = res.to_dict("records")
if len(res):
    print(f"\n   scored cells: {len(res)}, median PF {res.pf.median():.3f}, "
          f"best t {res.t.max():+.2f}, cells PF>1: {(res.pf > 1).sum()}/{len(res)}")
    OUT["grid_summary"] = {"n_cells": int(len(res)), "median_pf": float(res.pf.median()),
                           "best_t": float(res.t.max()), "n_above_1": int((res.pf > 1).sum())}

print("\n=== 2. WHERE THE SETUP DIES (funnel, per session, sma20 bias, 2R) ===")
funnel = {}
for sess in ("asia", "london", "ny"):
    d = logs[(sess, "sma20", "2R")]
    f = d.reason.value_counts().to_dict()
    tot = len(d)
    funnel[sess] = {"days": tot, **f}
    print(f"   {sess:6s}: days={tot}  " + "  ".join(f"{k}={v}" for k, v in f.items()))
x = logs[("london", "sma20", "2R")]
x = x[x.traded]
if len(x):
    print(f"   london swept-level kinds: {x.level_kind.value_counts().to_dict()}")
    print(f"   median stop distance ${x.r_dollars.median():.2f} on ~${x.entry.median():.0f} gold "
          f"-> cost $0.30 is {0.30 / x.r_dollars.median():.0%} of one R")
    funnel["median_r_dollars"] = float(x.r_dollars.median())
    funnel["cost_frac_of_r"] = float(0.30 / x.r_dollars.median())
OUT["funnel"] = funnel

print("\n=== 3. VARIATIONS (fixed: london / sma20 / 2R) ===")
VAR = {}


def var(lbl, key, **kw):
    d = judas.run(bars, LV, BIAS[kw.pop("bias_mode", "sma20")], session="london", target="2R", **kw)
    s = line(lbl, d)
    if s:
        VAR.setdefault(key, []).append({"label": lbl, **s})


for sw in (60, 120, 240):
    var(f"sweep window {sw} min", "sweep_window", sweep_window_min=sw)
for cw in (30, 60, 120):
    var(f"confirm within {cw} min", "confirm", confirm_within_min=cw)
for ag in (3, 5, 10):
    var(f"levels up to {ag} days old", "age", max_age_days=ag)
for wd in (1.0, 1.5, 2.0):
    var(f"stop widened x{wd:.1f}", "widen", widen=wd)
var("stop at the level (aggressive)", "stop", stop_at_level=True)
for mr in (0.25, 0.5, 1.0):
    var(f"min stop distance ${mr:.2f}", "min_r", min_r=mr)
dref = judas.run(bars, LV, BIAS["sma20"], session="london", target="2R")
xr = dref[dref.traded]
for c in (0.0, 0.15, 0.30, 0.60):
    p = xr.pnl_oz + 0.30 - c
    print(f"   round trip ${c:.2f}: PF={pfx(p):.3f}  exp=${p.mean():+.2f}/oz")
    VAR.setdefault("costs", []).append({"cost": c, "pf": pfx(p), "exp": float(p.mean())})
OUT["variations"] = VAR

print("\n=== 4. GOLD/AUD CORRELATION OVERLAY (fixed cell) ===")
xc = xr.copy()
xc["corr"] = pd.to_datetime(xc.day).map(CORR)
xc = xc.dropna(subset=["corr"])
ov = []
for lbl, msk in (("all", None), ("corr<=0.5", xc["corr"] <= 0.5), ("corr>0.5", xc["corr"] > 0.5)):
    y = xc if msk is None else xc[msk]
    s = line(lbl, y)
    if s:
        ov.append({"filter": lbl, **s})
OUT["corr_overlay"] = ov

print("\n=== 5. HONEST OUT-OF-SAMPLE (rank on pre-2024 t, read 2024-25) ===")
SPLIT = pd.Timestamp("2024-01-01")
scored = []
for key, d in logs.items():
    x = d[d.traded]
    if not len(x):
        continue
    osm = pd.to_datetime(x.day) >= SPLIT
    a, b = x[~osm], x[osm]
    if len(a) < 40 or len(b) < 20:
        continue
    pct = a.pnl_oz / a.entry * 100
    scored.append({"cell": " / ".join(key),
                   "is_n": len(a), "is_pf": pfx(a.pnl_oz),
                   "is_t": float(pct.mean() / pct.std() * np.sqrt(len(a))) if pct.std() else 0.0,
                   "os_n": len(b), "os_pf": pfx(b.pnl_oz)})
sc = pd.DataFrame(scored)
if len(sc):
    top5 = sc.sort_values("is_t", ascending=False).head(5)
    print("   top 5 by in-sample t, then read out-of-sample:")
    for _, r in top5.iterrows():
        print(f"     {r['cell']:30s} IS n={r['is_n']:>4} PF={r['is_pf']:.3f} t={r['is_t']:+.2f} | "
              f"OS n={r['os_n']:>3} PF={r['os_pf']:.3f}")
    print(f"   honest top-5 median OS PF: {top5.os_pf.median():.3f}; "
          f"population ({len(sc)} cells) median OS PF: {sc.os_pf.median():.3f}")
    OUT["isos"] = {"honest_top5": top5.to_dict("records"),
                   "honest_median_os_pf": float(top5.os_pf.median()),
                   "population_median_os_pf": float(sc.os_pf.median()),
                   "n_cells": int(len(sc))}
else:
    print("   too few trades per cell for a split")
    OUT["isos"] = None

pickle.dump(logs, open("results/judas_logs.pkl", "wb"))
json.dump(OUT, open("results/judas.json", "w"), indent=1, default=str)
print("\nwritten: results/judas_grid.csv, judas_logs.pkl, judas.json")
