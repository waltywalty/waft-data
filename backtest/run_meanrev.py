"""The 2.6-standard-deviation pullback, judged the house way: on a gradient
across band width, not at the single advertised point.

Panels:
 1. gradient: k in {1.5, 2.0, 2.6, 3.0, 3.5} x timeframe {5m, 15m, 60m}
    x trigger {close_out, close_back}
 2. sessions at the 2.6-sigma point
 3. variations on a FIXED default cell (15m, n=20, k=2.6, close_back)
 4. gold/AUD correlation overlay on the fixed cell
 5. honest OOS: rank panels 1+2 on pre-2024 t only, read 2024-25
"""
import pandas as pd, numpy as np, warnings, json, pickle
import engine, meanrev, trades
warnings.filterwarnings("ignore")

bars = engine.load_bars()
CORR = trades.corr_series(bars, 20)
OUT = {}
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def line(lbl, d):
    s = meanrev.stats(d)
    if s:
        print(f"   {lbl:42s} n={s['n']:>5} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
              f"exp={s['exp']:+.2f} t={s['t']:+.2f} tgt={s['tgt']*100:.0f}%")
    else:
        print(f"   {lbl:42s} too few trades")
    return s


print("=== 1. THE GRADIENT: band width x timeframe x trigger ===")
grid_logs, rows = {}, []
for tf in (5, 15, 60):
    for trig in ("close_out", "close_back"):
        for k in (1.5, 2.0, 2.6, 3.0, 3.5):
            d = meanrev.run(bars, tf=tf, k=k, trigger=trig)
            grid_logs[(tf, trig, k)] = d
            s = line(f"{tf:>2}m  k={k:.1f}  {trig}", d)
            if s:
                rows.append({"tf": tf, "trigger": trig, "k": k, **s})
res = pd.DataFrame(rows)
res.to_csv("results/meanrev_grid.csv", index=False)
OUT["grid"] = res.to_dict("records")

print("\n=== 2. SESSIONS at k=2.6, 15m ===")
sess_rows = []
for trig in ("close_out", "close_back"):
    for sess in ("asia", "london", "ny"):
        d = meanrev.run(bars, tf=15, k=2.6, trigger=trig, session=sess)
        grid_logs[(15, trig, 2.6, sess)] = d
        s = line(f"{sess:6s} {trig}", d)
        if s:
            sess_rows.append({"session": sess, "trigger": trig, **s})
OUT["sessions"] = sess_rows

print("\n=== 3. VARIATIONS (fixed: 15m, n=20, k=2.6, close_back, stop 1 sigma) ===")
VAR = {}


def var(lbl, key, **kw):
    d = meanrev.run(bars, tf=15, k=2.6, trigger="close_back", **kw)
    s = line(lbl, d)
    if s:
        VAR.setdefault(key, []).append({"label": lbl, **s})


for n in (14, 20, 30):
    var(f"lookback n={n}", "lookback", n=n)
for sk in (0.5, 1.0, 2.0, None):
    var(f"stop at {sk} sigma" if sk else "no stop", "stop", stop_k=sk)
for mh in (60, 120, 240, 480):
    var(f"max hold {mh} min", "hold", max_hold_min=mh)
var("target: halfway to mean", "target", target="half")
dref = meanrev.run(bars, tf=15, k=2.6, trigger="close_back")
for c in (0.0, 0.15, 0.30, 0.60):
    p = dref.pnl_oz + 0.30 - c
    print(f"   round trip ${c:.2f}: PF={pfx(p):.3f}  exp=${p.mean():+.2f}/oz")
    VAR.setdefault("costs", []).append({"cost": c, "pf": pfx(p), "exp": float(p.mean())})
OUT["variations"] = VAR

print("\n=== 4. GOLD/AUD CORRELATION OVERLAY (fixed cell) ===")
x = dref.copy()
x["corr"] = pd.to_datetime(pd.Series(x.t_fill.dt.date.values, index=x.index)).map(CORR)
x = x.dropna(subset=["corr"])
ov = []
for lbl, msk in (("all", None), ("corr<=0.5", x["corr"] <= 0.5), ("corr>0.5", x["corr"] > 0.5)):
    y = x if msk is None else x[msk]
    s = line(lbl, y)
    if s:
        ov.append({"filter": lbl, **s})
OUT["corr_overlay"] = ov

print("\n=== 5. HONEST OUT-OF-SAMPLE (rank on pre-2024 t, read 2024-25) ===")
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")
scored = []
for key, d in grid_logs.items():
    if len(d) < 80:
        continue
    osm = d.t_fill >= SPLIT
    a, b = d[~osm], d[osm]
    if len(a) < 50 or len(b) < 30:
        continue
    pct = a.pnl_oz / a.entry * 100
    scored.append({"cell": " / ".join(str(v) for v in key),
                   "is_n": len(a), "is_pf": pfx(a.pnl_oz),
                   "is_t": float(pct.mean() / pct.std() * np.sqrt(len(a))) if pct.std() else 0.0,
                   "os_n": len(b), "os_pf": pfx(b.pnl_oz)})
sc = pd.DataFrame(scored)
top5 = sc.sort_values("is_t", ascending=False).head(5)
print("   top 5 by in-sample t, then read out-of-sample:")
for _, r in top5.iterrows():
    print(f"     {r['cell']:28s} IS n={r['is_n']:>5} PF={r['is_pf']:.3f} t={r['is_t']:+.2f} | "
          f"OS n={r['os_n']:>4} PF={r['os_pf']:.3f}")
print(f"   honest top-5 median OS PF: {top5.os_pf.median():.3f}; "
      f"population ({len(sc)} cells) median OS PF: {sc.os_pf.median():.3f}")
OUT["isos"] = {"honest_top5": top5.to_dict("records"),
               "honest_median_os_pf": float(top5.os_pf.median()),
               "population_median_os_pf": float(sc.os_pf.median()),
               "n_cells": int(len(sc))}

pickle.dump(grid_logs, open("results/meanrev_logs.pkl", "wb"))
json.dump(OUT, open("results/meanrev.json", "w"), indent=1, default=str)
print("\nwritten: results/meanrev_grid.csv, meanrev_logs.pkl, meanrev.json")
