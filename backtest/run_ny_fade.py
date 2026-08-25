"""Grid + sensitivities for fading the NY open, and the honest OOS panel.

Sections:
 0. symmetry self-test - the fade engine must mirror the follow engine exactly
 1. main grid: 4 ranges x 11 exits x 3 correlation regimes (stop = 1.0 x range)
 2. parameter variations on a FIXED default cell (15m / range_mid) - chosen before
    looking at the grid, so the panel is not a victory lap for the best cell
 3. honest out-of-sample: rank on pre-2024 t only, then read 2024-25
"""
import pandas as pd, numpy as np, warnings, pickle, json
import engine, ny_orb, ny_fade, trades
warnings.filterwarnings("ignore")

bars = engine.load_bars()
LEV = pickle.load(open("results/ny_levels.pkl", "rb"))
CORR = trades.corr_series(bars, 20)
OUT = {}

pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def fstats(x):
    s = ny_orb.stats(x)
    return s


print("=== 0. SYMMETRY SELF-TEST ===")
fol = ny_orb.run(bars, range_min=15, exit_spec="ny_close", use_stop=False, cost=0.0)
fad = ny_fade.run(bars, range_min=15, exit_spec="ny_close", use_stop=False, cost=0.0)
a = fol[fol.traded].set_index("day")
b = fad[fad.traded].set_index("day")
common = a.index.intersection(b.index)
assert len(common) == len(a) == len(b), f"trade sets differ: {len(a)} vs {len(b)}"
mx = (a.loc[common].pnl_oz + b.loc[common].pnl_oz).abs().max()
assert mx < 1e-9, f"fade is not the mirror of follow: max |sum| = {mx}"
assert (a.loc[common].entry - b.loc[common].entry).abs().max() < 1e-9
print(f"   {len(common)} trades: fade pnl == -follow pnl to {mx:.2e}. Engine verified.\n")
OUT["symmetry"] = {"n": int(len(common)), "max_abs_sum": float(mx)}

print("=== 1. MAIN GRID (stop = entry + 1.0 x range against the fade, cost $0.30) ===")
EXITS = ["ny+30m", "ny+60m", "ny+90m", "ny+2h", "ny_lunch", "ny_close",
         "range_mid", "range_far", "prev_day", "asia", "london"]
logs, rows = {}, []
for R in (5, 15, 30, 60):
    for ex in EXITS:
        d = ny_fade.run(bars, range_min=R, exit_spec=ex, stop_mult=1.0, levels=LEV)
        d["corr"] = pd.to_datetime(d.day).map(CORR)
        logs[(R, ex)] = d
        x = d[d.traded].dropna(subset=["corr"])
        for fname, msk in (("all", None), ("corr<=0.5", x["corr"] <= 0.5), ("corr>0.5", x["corr"] > 0.5)):
            y = x if msk is None else x[msk]
            s = fstats(y)
            if s:
                rows.append({"range": R, "exit": ex, "filter": fname, **s})
res = pd.DataFrame(rows)
res.to_csv("results/ny_fade_grid.csv", index=False)
pickle.dump(logs, open("results/ny_fade_logs.pkl", "wb"))
print(f"   scored cells: {len(res)}")
for fname in ("all", "corr<=0.5", "corr>0.5"):
    sub = res[res["filter"] == fname]
    print(f"   {fname:10s}: median PF {sub.pf.median():.3f}, best t {sub.t.max():+.2f}, "
          f"cells PF>1: {(sub.pf > 1).sum()}/{len(sub)}")
best = res.sort_values("t", ascending=False).head(8)
print("\n   top 8 by t:")
for _, r in best.iterrows():
    print(f"     {int(r['range']):2d}m / {r['exit']:9s} / {r['filter']:9s} "
          f"n={int(r['n']):>4} win={r['win']*100:4.1f}% PF={r['pf']:.3f} t={r['t']:+.2f}")
OUT["grid"] = {"n_cells": int(len(res)),
               "by_filter": {f: {"median_pf": float(res[res["filter"] == f].pf.median()),
                                 "best_t": float(res[res["filter"] == f].t.max()),
                                 "n_above_1": int((res[res["filter"] == f].pf > 1).sum()),
                                 "n": int((res["filter"] == f).sum())}
                             for f in ("all", "corr<=0.5", "corr>0.5")},
               "top8": best.to_dict("records")}

print("\n=== 2. PARAMETER VARIATIONS (fixed cell: 15m range, range_mid target) ===")
VAR = {}


def var_line(lbl, key, **kw):
    d = ny_fade.run(bars, range_min=15, exit_spec="range_mid", levels=LEV, **kw)
    x = d[d.traded]
    s = fstats(x)
    if s:
        print(f"   {lbl:36s} n={s['n']:>4} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
              f"exp={s['exp']:+.2f} t={s['t']:+.2f} tgt={s['tgt']*100:.0f}%")
        VAR.setdefault(key, []).append({"label": lbl, **s})
    else:
        print(f"   {lbl:36s} too few trades")
    return d


print("   stop distance:")
for m in (0.5, 1.0, 2.0):
    var_line(f"stop at {m:.1f} x range beyond entry", "stop", stop_mult=m)
d0 = ny_fade.run(bars, range_min=15, exit_spec="range_mid", levels=LEV, use_stop=False)
s = fstats(d0[d0.traded])
print(f"   {'no stop at all':36s} n={s['n']:>4} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
      f"exp={s['exp']:+.2f} t={s['t']:+.2f}")
VAR.setdefault("stop", []).append({"label": "no stop", **s})

print("   minimum overshoot of the break:")
for ov in (0.0, 0.10, 0.25, 0.50):
    var_line(f"fade only closes >= {ov:.2f} x range out", "overshoot", min_over=ov)

print("   confirmation timeframe:")
for cm in (5, 15, 30):
    var_line(f"{cm}m confirmation candle", "confirm", confirm_min=cm)

print("   entry deadline:")
for dl in (30, 60, 90, 150):
    var_line(f"no entry after +{dl} min", "deadline", entry_deadline_min=dl)

print("   intrabar ambiguity:")
for tf in (False, True):
    var_line("target first" if tf else "stop first (default)", "ambiguity", target_first=tf)

print("   costs:")
dref = ny_fade.run(bars, range_min=15, exit_spec="range_mid", levels=LEV)
x = dref[dref.traded]
for c in (0.0, 0.15, 0.30, 0.60):
    p = x.pnl_oz + 0.30 - c
    print(f"   round trip ${c:.2f}: PF={pfx(p):.3f}  exp=${p.mean():+.2f}/oz")
    VAR.setdefault("costs", []).append({"cost": c, "pf": pfx(p), "exp": float(p.mean())})
OUT["variations"] = VAR

print("\n=== 3. HONEST OUT-OF-SAMPLE (rank on pre-2024 only, read 2024-25) ===")
SPLIT = pd.Timestamp("2024-01-01")
scored = []
for (R, ex), d in logs.items():
    x0 = d[d.traded].dropna(subset=["corr"]).copy()
    for fname, msk in (("all", None), ("corr<=0.5", x0["corr"] <= 0.5), ("corr>0.5", x0["corr"] > 0.5)):
        x = x0 if msk is None else x0[msk]
        osm = pd.to_datetime(x.day) >= SPLIT
        a, b = x[~osm], x[osm]
        if len(a) < 40 or len(b) < 25:
            continue
        pct = a.pnl_oz / a.entry * 100
        scored.append({"range": R, "exit": ex, "filter": fname,
                       "is_n": len(a), "is_pf": pfx(a.pnl_oz),
                       "is_t": float(pct.mean() / pct.std() * np.sqrt(len(a))) if pct.std() else 0.0,
                       "os_n": len(b), "os_pf": pfx(b.pnl_oz)})
sc = pd.DataFrame(scored)
top5 = sc.sort_values("is_t", ascending=False).head(5)
print("   top 5 by in-sample t, then read out-of-sample:")
for _, r in top5.iterrows():
    print(f"     {r['range']:2d}m / {r['exit']:9s} / {r['filter']:9s} "
          f"IS n={r['is_n']:>4} PF={r['is_pf']:.3f} t={r['is_t']:+.2f} | "
          f"OS n={r['os_n']:>3} PF={r['os_pf']:.3f}")
print(f"   honest top-5 median OS PF: {top5.os_pf.median():.3f}; "
      f"population ({len(sc)} cells) median OS PF: {sc.os_pf.median():.3f}")
OUT["isos"] = {"honest_top5": top5.to_dict("records"),
               "honest_median_os_pf": float(top5.os_pf.median()),
               "population_median_os_pf": float(sc.os_pf.median()),
               "n_cells": int(len(sc))}

json.dump(OUT, open("results/ny_fade.json", "w"), indent=1, default=str)
print("\nwritten: results/ny_fade_grid.csv, ny_fade_logs.pkl, ny_fade.json")
