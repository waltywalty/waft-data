"""The full New York opening-range grid: range length x exit x correlation filter."""
import pandas as pd, numpy as np, engine, ny_orb, trades, warnings, pickle, json
warnings.filterwarnings("ignore")

bars = engine.load_bars()
LEV = pickle.load(open("results/ny_levels.pkl", "rb"))
CORR = trades.corr_series(bars, 20)          # 20-day gold/AUDUSD, broker day, lagged 1

RANGES = [5, 15, 30, 60]
EXITS = list(ny_orb.TIME_EXITS) + ny_orb.LEVELS

def tag(df):
    d = df.copy()
    d["corr"] = pd.to_datetime(d.day).map(CORR)
    return d

def summarise(d, mask=None):
    x = d[d.traded].copy()
    if mask is not None:
        x = x[mask.reindex(x.index).fillna(False)]
    return ny_orb.stats(x) if len(x) >= 25 else None

rows, logs, n_tests = [], {}, 0
for R in RANGES:
    for E in EXITS:
        d = tag(ny_orb.run(bars, R, E, levels=LEV))
        logs[(R, E)] = d
        for fname, msk in (("all", None), ("corr<=0.5", d["corr"] <= 0.5)):
            s = summarise(d, msk)
            n_tests += 1
            if s:
                rows.append({"range": R, "exit": E, "filter": fname, "stop": "range_opp", **s})
        # the same configuration with NO protective stop, so the grid's treatment of the
        # stop is explicit rather than implied
        dn = tag(ny_orb.run(bars, R, E, levels=LEV, use_stop=False))
        logs[(R, E, "nostop")] = dn
        s = summarise(dn, None)
        n_tests += 1
        if s:
            rows.append({"range": R, "exit": E, "filter": "all", "stop": "none", **s})

res = pd.DataFrame(rows)
res.to_csv("results/ny_grid.csv", index=False)
pickle.dump(logs, open("results/ny_logs.pkl", "wb"))

pd.set_option("display.width", 220)
print(f"=== NEW YORK OPENING-RANGE GRID  ({n_tests} configurations tested) ===")
print("XAUUSD 5-minute bars, Aug 2020 - Aug 2025. $0.30 round trip. Entry deadline 90 min.")
print("Stop for target exits = far side of the opening range.\n")

for fname in ("all", "corr<=0.5"):
    sub = res[(res["filter"] == fname) & (res["stop"] == "range_opp")]
    print(f"--- filter: {fname} (stop at the far side of the range) ---")
    piv = sub.pivot(index="exit", columns="range", values="pf").reindex(EXITS)
    npiv = sub.pivot(index="exit", columns="range", values="n").reindex(EXITS)
    hdr = "exit".ljust(15) + "".join(f"{r}m".rjust(16) for r in RANGES)
    print(hdr)
    for e in EXITS:
        line = e.ljust(15)
        for r in RANGES:
            pf = piv.loc[e, r] if r in piv.columns else np.nan
            n = npiv.loc[e, r] if r in npiv.columns else np.nan
            line += (f"{pf:.3f} ({int(n):4d})".rjust(16)) if pd.notna(pf) else "-".rjust(16)
        print(line)
    print()

print("--- no protective stop, unfiltered ---")
sub = res[res["stop"] == "none"]
for e in EXITS:
    line = e.ljust(15)
    for r in RANGES:
        m = sub[(sub["exit"] == e) & (sub["range"] == r)]
        line += (f"{m.iloc[0]['pf']:.3f} ({int(m.iloc[0]['n']):4d})".rjust(16)) if len(m) else "-".rjust(16)
    print(line)
print()

print("=== best 12 configurations by t-statistic ===")
top = res.sort_values("t", ascending=False).head(12)
print(top[["range", "exit", "filter", "stop", "n", "win", "pf", "exp", "t", "hold", "stp"]]
      .round(3).to_string(index=False))

print("\n=== how many configurations clear a profit factor of 1.0? ===")
for fname in ("all", "corr<=0.5"):
    sub = res[(res["filter"] == fname) & (res["stop"] == "range_opp")]
    print(f"  {fname:10s}: {(sub.pf > 1).sum()} of {len(sub)}   "
          f"(median PF {sub.pf.median():.3f}, best {sub.pf.max():.3f})")
sub = res[res["stop"] == "none"]
print(f"  no stop   : {(sub.pf > 1).sum()} of {len(sub)}   "
      f"(median PF {sub.pf.median():.3f}, best {sub.pf.max():.3f})")

json.dump({"n_tests": n_tests,
           "rows": res.to_dict("records")}, open("results/ny_grid.json", "w"), indent=1, default=str)
