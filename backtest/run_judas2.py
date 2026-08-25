"""Canonical-ICT addendum to the Judas study, prompted by the online research:

 - bias by the PDH/PDL 4-scenario logic (the most codifiable ICT variant)
 - the true killzone windows: London Judas opens 02:00 ET, NY killzone 08:30 ET
 - the gold "deep sweep" claim: a MINIMUM sweep depth as an entry filter,
   cut post-hoc on recorded sweep_depth (known at entry time, so causal)

The base grid already showed take-everything sweeps lose at zero cost with a
27% win rate - almost exactly the 29.6% the one independent mechanical ICT
test (OffBeatForex) reported. This addendum asks whether the canonical
refinements rescue it.

Limitation stated up front: the level tracker only carries COMPLETED sessions,
so the NY-killzone variant can sweep yesterday's London/NY levels, today's
completed Asia levels and PDH/PDL, but not "London so far today".
"""
import pandas as pd, numpy as np, warnings, json, pickle
import engine, structure, judas, trades
warnings.filterwarnings("ignore")

bars = engine.load_bars()
LV = structure.build_levels(bars)
DAILY = structure.fx_daily(bars)
CORR = trades.corr_series(bars, 20)
OUT = {}
SPLIT = pd.Timestamp("2024-01-01")
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def line(lbl, d):
    x = d[d.traded] if "traded" in d else d
    s = judas.stats(d)
    if s:
        dd = pd.to_datetime(x.day)
        a, b = x[dd < SPLIT], x[dd >= SPLIT]
        halves = ""
        if len(a) >= 15 and len(b) >= 15:
            halves = f" | 20-23 PF={pfx(a.pnl_oz):.3f} 24-25 PF={pfx(b.pnl_oz):.3f}"
        print(f"   {lbl:44s} n={s['n']:>4} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
              f"exp={s['exp']:+.2f} t={s['t']:+.2f}{halves}")
    else:
        print(f"   {lbl:44s} too few trades (n={len(x)})")
    return s


print("=== 1. CANONICAL WINDOWS AND BIAS ===")
BIAS = {m: structure.daily_bias(DAILY, m) for m in ("pdhl", "sma20")}
nb = BIAS["pdhl"]
print(f"   pdhl bias distribution: {nb.value_counts().to_dict()}\n")
rows, logs = [], {}
for sess in ("london", "ldnkz", "nykz"):
    for bm in ("pdhl", "sma20"):
        for tgt in ("2R", "opp"):
            d = judas.run(bars, LV, BIAS[bm], session=sess, target=tgt)
            logs[(sess, bm, tgt)] = d
            s = line(f"{sess:6s} / {bm:5s} / {tgt}", d)
            if s:
                rows.append({"session": sess, "bias": bm, "target": tgt, **s})
res = pd.DataFrame(rows)
OUT["canonical"] = res.to_dict("records") if len(res) else []

print("\n=== 2. THE DEEP-SWEEP FILTER (minimum sweep depth, known at entry) ===")
DS = {}
for key in ((("london", "sma20", "2R")), (("ldnkz", "pdhl", "2R"))):
    src = logs.get(key)
    if src is None:
        base_logs = pickle.load(open("results/judas_logs.pkl", "rb"))
        src = base_logs[key]
    x = src[src.traded]
    print(f"   cell {' / '.join(key)}:")
    for dmin in (0.0, 0.5, 1.0, 2.0):
        s = line(f"     sweep depth >= ${dmin:.1f}", x[x.sweep_depth >= dmin])
        if s:
            DS.setdefault("/".join(key), []).append({"dmin": dmin, **s})
OUT["deep_sweep"] = DS

print("\n=== 3. CORRELATION OVERLAY on the canonical cell (ldnkz / pdhl / 2R) ===")
x = logs[("ldnkz", "pdhl", "2R")]
x = x[x.traded].copy()
x["corr"] = pd.to_datetime(x.day).map(CORR)
x = x.dropna(subset=["corr"])
ov = []
for lbl, msk in (("all", None), ("corr<=0.5", x["corr"] <= 0.5), ("corr>0.5", x["corr"] > 0.5)):
    y = x if msk is None else x[msk]
    s = line(lbl, y)
    if s:
        ov.append({"filter": lbl, **s})
OUT["corr_overlay"] = ov

json.dump(OUT, open("results/judas2.json", "w"), indent=1, default=str)
print("\nwritten: results/judas2.json")
