"""Round 72A step 3, attempt 2b reversed (= attempt-2 momentum, direction +sign(P)).
IS ONLY. Reuses run_r42c_pmrev.py build functions; OOS rows dropped right after build.
Run from /home/user/waft-data/backtest."""
import pandas as pd, numpy as np, json, warnings, sys
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's cost dict, full RT

def build_days(idx):   # copied verbatim from run_r42c_pmrev.py
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm, c, o = g.hm.values, g.close.values, g.open.values
        if len(g) < 50 or hm[0] > 935:
            continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        rows.append(dict(skey=skey, o930=o[0], c1000=lb(1000), c1300=lb(1300), c1400=lb(1400),
                         c1500=lb(1500), c1530=lb(1530), cEnd=c[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["p_first"] = d.c1000 - d.o930
    d["p_day"] = d.c1500 - d.o930
    d["p_first_lag"] = d.p_first.shift(1)      # placebo: previous session's predictor
    return d

frames = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d = build_days(idx)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    print(f"IS cut {idx}: {cutd}  (sessions >= cut dropped)")
    d = d[d.index < cutd].copy()                # ---- OOS FIREWALL: IS rows only from here on
    d["idx"], d["cost"] = idx, MICRO[idx]
    frames[idx] = d
big = pd.concat(frames.values()).reset_index()
big["year"] = pd.to_datetime(big.skey).dt.year

def tstat(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else np.nan

def stats(gross, atr, cost, years=None, k=1.0):
    net = np.asarray(gross, float) - k * np.asarray(cost, float)
    r = net / np.asarray(atr, float)
    ok = np.isfinite(r); r, net = r[ok], net[ok]
    w, l = net[net > 0], net[net <= 0]
    m = len(r) // 2
    out = dict(n=int(len(r)), avgR=float(r.mean()), t=tstat(r), wr=float((net > 0).mean()),
               pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else np.inf,
               halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])
    if years is not None:
        y = np.asarray(years)[ok]
        out["per_year"] = {int(yy): float(np.sign(r[y == yy].mean())) for yy in sorted(set(y))}
    return out

PREDS = {"first30": lambda d: d.p_first, "day": lambda d: d.p_day,
         "agree": lambda d: np.where(np.sign(d.p_first) == np.sign(d.p_day), d.p_day, np.nan)}
ENTRIES = {"15:00": "c1500", "15:30": "c1530"}

def cell(d, P, ecol, thr, exit_col="cEnd"):
    P = np.asarray(P, float)
    m = np.isfinite(P) & np.isfinite(d.atr20.values) & (d.atr20.values > 0) & np.isfinite(d[ecol].values) \
        & np.isfinite(d[exit_col].values) & (np.sign(P) != 0) & (np.abs(P) >= thr * d.atr20.values)
    side = np.sign(P[m])                       # REVERSED (= attempt-2 momentum direction)
    gross = side * (d[exit_col].values[m] - d[ecol].values[m])
    return m, gross

# ---- registered cell reversed: first30 / 15:00 / none ----
m, gross = cell(big, PREDS["first30"](big), "c1500", 0.0)
atr, cost, yrs = big.atr20.values[m], big.cost.values[m], big.year.values[m]
rev = {f"x{k}": stats(gross, atr, cost, yrs, k) for k in (1.0, 1.5, 2.0)}
print("\n=== REVERSED (momentum, +sign(P)) first30/15:00/none, IS ===")
for k, v in rev.items(): print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items() if a != "per_year"})
print("per-year signs (1x):", rev["x1.0"]["per_year"])
print("gross avgR:", round(float((gross / atr).mean()), 5), "t", round(tstat(gross / atr), 2))

# ---- unconditional control: same window (15:00 -> close), every eligible IS session ----
mc = np.isfinite(big.atr20.values) & (big.atr20.values > 0) & np.isfinite(big.c1500.values) & np.isfinite(big.cEnd.values)
g_long = big.cEnd.values[mc] - big.c1500.values[mc]
ctl_long = stats(g_long, big.atr20.values[mc], big.cost.values[mc], big.year.values[mc], 1.0)
ctl_short = stats(-g_long, big.atr20.values[mc], big.cost.values[mc], big.year.values[mc], 1.0)
print("\n=== CONTROL always-long 15:00->close, 1x ===", {a: (round(b, 4) if isinstance(b, float) else b) for a, b in ctl_long.items() if a != "per_year"})
print("=== CONTROL always-short 15:00->close, 1x ===", {a: (round(b, 4) if isinstance(b, float) else b) for a, b in ctl_short.items() if a != "per_year"})
# paired by date: cell days are a subset of control days
key = list(zip(big.idx.values, big.skey.values))
cellR = pd.Series((gross - cost) / atr, index=pd.MultiIndex.from_tuples([key[i] for i in np.where(m)[0]]))
ctlR_long = pd.Series((g_long - big.cost.values[mc]) / big.atr20.values[mc], index=pd.MultiIndex.from_tuples([key[i] for i in np.where(mc)[0]]))
ctlR_short = -pd.Series(g_long / big.atr20.values[mc], index=ctlR_long.index) - big.cost.values[mc] / big.atr20.values[mc]
dl = (cellR - ctlR_long.reindex(cellR.index)).dropna()
ds = (cellR - ctlR_short.reindex(cellR.index)).dropna()
print(f"diff vs always-long (paired by date): n {len(dl)} avgR {dl.mean():+.4f} t {tstat(dl):+.2f}")
print(f"diff vs always-short (paired by date): n {len(ds)} avgR {ds.mean():+.4f} t {tstat(ds):+.2f}")
# Welch as a cross-check
from scipy import stats as sst
print("Welch vs always-long:", sst.ttest_ind(cellR.values, ctlR_long.values, equal_var=False))

# ---- gradient: the 12-cell grid reversed (1x net) ----
print("\n=== GRADIENT: 12-cell grid reversed, IS net 1x ===")
grid = []
for pname, pfn in PREDS.items():
    for ename, ecol in ENTRIES.items():
        for fname, thr in (("none", 0.0), ("0.25atr", 0.25)):
            mm, gg = cell(big, pfn(big), ecol, thr)
            s = stats(gg, big.atr20.values[mm], big.cost.values[mm], None, 1.0)
            s2 = stats(gg, big.atr20.values[mm], big.cost.values[mm], None, 2.0)
            grid.append(dict(pred=pname, entry=ename, filt=fname, **{k: s[k] for k in ("n", "avgR", "t", "halves")}, avgR_x2=s2["avgR"]))
            print(f"{pname:>8} {ename:>6} {fname:>8} | n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']} x2 {s2['avgR']:+.4f}")
print("\n=== GRADIENT: |P| >= k*ATR20 ladder, first30/15:00 and day/15:00, reversed, IS net 1x ===")
ladder = {}
for pname in ("first30", "day"):
    for k in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0):
        mm, gg = cell(big, PREDS[pname](big), "c1500", k)
        s = stats(gg, big.atr20.values[mm], big.cost.values[mm], None, 1.0)
        ladder[f"{pname}_k{k}"] = s
        print(f"{pname:>8} k={k:<4} | n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")

# ---- placebos, reversed ----
print("\n=== PLACEBO A: previous-session predictor (first30 lagged 1 day), entry 15:00 -> close, +sign(P_lag) ===")
mm, gg = cell(big, big.p_first_lag, "c1500", 0.0)
pa = stats(gg, big.atr20.values[mm], big.cost.values[mm], None, 1.0)
print({a: (round(b, 4) if isinstance(b, float) else b) for a, b in pa.items()})
print("=== PLACEBO B: shifted clock, first30 predictor, entry 13:00 -> 14:00 close, +sign(P) ===")
mm, gg = cell(big, PREDS["first30"](big), "c1300", 0.0, exit_col="c1400")
pb = stats(gg, big.atr20.values[mm], big.cost.values[mm], None, 1.0)
print({a: (round(b, 4) if isinstance(b, float) else b) for a, b in pb.items()})

json.dump(dict(reversed=rev, control_long=ctl_long, control_short=ctl_short,
               diff_long=dict(n=int(len(dl)), avgR=float(dl.mean()), t=tstat(dl)),
               diff_short=dict(n=int(len(ds)), avgR=float(ds.mean()), t=tstat(ds)),
               grid=grid, ladder=ladder, placebo_lag=pa, placebo_clock=pb),
          open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_2b.json", "w"), indent=1, default=float)
