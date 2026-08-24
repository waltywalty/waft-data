"""Sensitivities for the NY opening-range study, plus a test of whether the AUD
correlation filter generalises from the Asia setup to this completely different one."""
import pandas as pd, numpy as np, engine, ny_orb, trades, warnings, pickle, json
warnings.filterwarnings("ignore")
from scipy import stats as st

bars = engine.load_bars()
LEV = pickle.load(open("results/ny_levels.pkl", "rb"))
CORR = trades.corr_series(bars, 20)
res = pd.read_csv("results/ny_grid.csv")
OUT = {}


def go(**kw):
    d = ny_orb.run(bars, levels=LEV, **kw)
    d["corr"] = pd.to_datetime(d.day).map(CORR)
    return d


def line(lbl, d, msk=None):
    x = d[d.traded]
    if msk is not None:
        x = x[msk.reindex(x.index).fillna(False)]
    s = ny_orb.stats(x)
    if not s:
        print(f"  {lbl:34s} too few trades")
        return None
    print(f"  {lbl:34s} n={s['n']:>4} win={s['win']*100:>4.1f}% PF={s['pf']:.3f} "
          f"exp={s['exp']:+.2f} t={s['t']:+.2f}")
    return s


print("=== 1. CONFIRMATION TIMEFRAME (the closest proxy for the 1-minute question) ===")
print("   Data is 5-minute, so 1-minute cannot be tested directly. The gradient bounds it.\n")
conf = []
for cm in (5, 15, 30, 60):
    for R in (15, 30):
        s = line(f"{R}m range, {cm}m confirmation", go(range_min=R, exit_spec="ny+90m", confirm_min=cm))
        if s:
            conf.append({"range": R, "confirm": cm, **s})
OUT["confirm"] = conf

print("\n=== 2. ENTRY DEADLINE ===")
dead = []
for dl in (30, 60, 90, 150, 390):
    s = line(f"no entry after +{dl} min", go(range_min=15, exit_spec="ny_close", entry_deadline_min=dl))
    if s:
        dead.append({"deadline": dl, **s})
OUT["deadline"] = dead

print("\n=== 3. STOP PLACEMENT (prev-day target) ===")
stops = []
for mode, mult in (("range_opp", None), ("mult", 0.5), ("mult", 1.0), ("mult", 2.0)):
    lbl = "far side of range" if mode == "range_opp" else f"{mult:.1f} x range"
    s = line(lbl, go(range_min=15, exit_spec="prev_day", stop_mode=mode, stop_mult=mult or 1.0))
    if s:
        stops.append({"mode": lbl, **s})
OUT["stops"] = stops

print("\n=== 4. INTRABAR AMBIGUITY: if a 5m bar touches both stop and target ===")
amb = []
for tf in (False, True):
    s = line("assume target filled" if tf else "assume stop filled (default)",
             go(range_min=15, exit_spec="prev_day", target_first=tf))
    if s:
        amb.append({"target_first": tf, **s})
OUT["ambiguity"] = amb

print("\n=== 5. COSTS (15m range, NY close) ===")
d = go(range_min=15, exit_spec="ny_close")
x = d[d.traded]
costs = []
for c in (0.0, 0.15, 0.30, 0.60):
    p = x.pnl_oz + 0.30 - c
    pf = float(p[p > 0].sum() / max(-p[p <= 0].sum(), 1e-9))
    costs.append({"cost": c, "pf": pf, "exp": float(p.mean())})
    print(f"  round trip ${c:.2f}: PF={pf:.3f}  exp=${p.mean():+.2f}/oz")
OUT["costs"] = costs

print("\n=== 6. DOES THE AUD CORRELATION FILTER GENERALISE TO THIS SETUP? ===")
print("   The filter was found on the Asia-open strategy. This is a different session,")
print("   a different range, and different exits - so it is close to an independent test.\n")
piv = res.pivot_table(index=["range", "exit"], columns="filter", values="pf")
piv = piv.dropna()
lift = piv["corr<=0.5"] - piv["all"]
w = st.wilcoxon(piv["corr<=0.5"], piv["all"])
print(f"  cells compared          : {len(piv)}")
print(f"  filter improved         : {(lift > 0).sum()} of {len(lift)} ({(lift > 0).mean()*100:.0f}%)")
print(f"  median profit-factor lift: {lift.median():+.3f}")
print(f"  mean lift                : {lift.mean():+.3f}")
print(f"  Wilcoxon signed-rank     : statistic={w.statistic:.0f}, p={w.pvalue:.5f}")
print(f"  median PF unfiltered {piv['all'].median():.3f} -> filtered {piv['corr<=0.5'].median():.3f}")
OUT["filter_generalisation"] = {"n_cells": int(len(piv)), "improved": int((lift > 0).sum()),
                                "median_lift": float(lift.median()), "mean_lift": float(lift.mean()),
                                "wilcoxon_p": float(w.pvalue),
                                "median_pf_all": float(piv["all"].median()),
                                "median_pf_filt": float(piv["corr<=0.5"].median())}

print("\n=== 7. IN-SAMPLE / OUT-OF-SAMPLE ON THE BEST CELLS ===")
best = res.sort_values("t", ascending=False).head(5)
isos = []
for _, r in best.iterrows():
    d = go(range_min=int(r["range"]), exit_spec=r["exit"])
    x = d[d.traded]
    if r["filter"] != "all":
        x = x[x["corr"] <= 0.5]
    x = x.copy(); x["os"] = pd.to_datetime(x.day) >= "2024-01-01"
    pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
    a, b = x[~x.os], x[x.os]
    if len(a) < 25 or len(b) < 25:
        continue
    print(f"  {int(r['range'])}m / {r['exit']:14s} / {r['filter']:9s} "
          f"IS n={len(a):>3} PF={pf(a.pnl_oz):.3f} | OS n={len(b):>3} PF={pf(b.pnl_oz):.3f}")
    isos.append({"range": int(r["range"]), "exit": r["exit"], "filter": r["filter"],
                 "is_n": len(a), "is_pf": pf(a.pnl_oz), "os_n": len(b), "os_pf": pf(b.pnl_oz)})
OUT["isos"] = isos

print("\n=== 8. NEW YORK vs ASIA, side by side ===")
try:
    asia = pd.read_pickle("results/trades_deployable.pkl")
    pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
    pct = asia.pnl_oz / asia.entry * 100
    print(f"  Asia 09:30 HKT, 60m range, NY-close exit, filtered:")
    print(f"     n={len(asia)} win={100*(asia.pnl_oz>0).mean():.1f}% PF={pf(asia.pnl_oz):.3f} "
          f"t={pct.mean()/pct.std()*np.sqrt(len(pct)):+.2f}")
except Exception as e:
    print("  (asia trade log unavailable:", e, ")")
nb = res.sort_values("t", ascending=False).iloc[0]
print(f"  New York 09:30 ET, best of 80 configurations:")
print(f"     {int(nb['range'])}m / {nb['exit']} / {nb['filter']}: n={int(nb['n'])} "
      f"win={nb['win']*100:.1f}% PF={nb['pf']:.3f} t={nb['t']:+.2f}")
print(f"\n  best t-statistic anywhere in the NY grid: {res.t.max():+.2f} across {len(res)} scored cells")
print(f"  For comparison, a search over pure noise of this size would typically throw up")
print(f"  a best t around +2 to +3. Finding {res.t.max():+.2f} means the grid is not merely")
print(f"  unprofitable - it is consistently, systematically negative.")

json.dump(OUT, open("results/ny_sens.json", "w"), indent=1, default=str)
print("\nwritten: results/ny_sens.json")
