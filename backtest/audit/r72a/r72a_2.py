"""Round 72A step 3, attempt 2 (late-day intraday momentum) REVERSED, IS ONLY.
Reuses run_r37_scalps.py load_frame/rth_of and a verbatim copy of run_r42b_pm.py
build_days (extra columns c1030/c1400 added for the placebo only). Per-instrument IS
cut = days[int(len(days)*0.75)] exactly as the runner; rows on/after the cut are dropped
before any return is computed. Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, warnings, sys, os
sys.path.insert(0, "/home/user/waft-data/backtest"); os.chdir("/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's dict, full RT, points

def build_days(idx):
    b = load_frame(idx); rth = rth_of(b); rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values; c = g.close.values; o = g.open.values
        if len(g) < 50 or hm[0] > 935: continue
        def last_before(t):
            m = np.where(hm < t)[0]; return c[m[-1]] if len(m) else np.nan
        rows.append(dict(skey=skey, o930=o[0], c1000=last_before(1000), c1030=last_before(1030),
                         c1400=last_before(1400), c1500=last_before(1500), c1530=last_before(1530),
                         cEnd=c[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["rng"] = d.hi - d.lo
    d["atr20"] = d.rng.rolling(20).mean().shift(1)
    d["p_first"] = d.c1000 - d.o930
    d["p_day"] = d.c1500 - d.o930
    return d

frames = []
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d = build_days(idx); days = d.index.tolist(); cutd = days[int(len(days) * 0.75)]
    print(f"IS cut {idx}: {cutd}  (sessions before cut: {(d.index < cutd).sum()}, dropped: {(d.index >= cutd).sum()})")
    d = d[d.index < cutd].copy()          # OOS FIREWALL: drop cut and after
    d["idx"] = idx; d["cost"] = MICRO[idx]
    # previous-session predictor for the shifted-day placebo (same instrument, IS rows only)
    d["p_first_prev"] = d.p_first.shift(1)
    frames.append(d)
big = pd.concat(frames)
big["date"] = pd.to_datetime(big.index)
big["year"] = big.date.dt.year

def st(r, dates=None):
    r = np.asarray(r, float); ok = np.isfinite(r); r = r[ok]
    n = len(r); m = n // 2
    w, l = r[r > 0], r[r <= 0]
    out = dict(n=n, avgR=r.mean(), t=r.mean() / r.std() * np.sqrt(n) if n > 1 and r.std() > 0 else np.nan,
               wr=(r > 0).mean(), pf=w.sum() / abs(l.sum()) if len(l) and l.sum() < 0 else np.inf,
               halves_runner=[int(np.sign(r[:m].mean())), int(np.sign(r[m:].mean()))])
    if dates is not None:
        dd = np.asarray(dates)[ok]; o = np.argsort(dd, kind="stable"); rc = r[o]
        out["halves_chrono"] = [int(np.sign(rc[:m].mean())), int(np.sign(rc[m:].mean()))]
    return out

PREDS = {"first30": lambda d: d.p_first, "day": lambda d: d.p_day,
         "agree": lambda d: pd.Series(np.where(np.sign(d.p_first) == np.sign(d.p_day), d.p_day, np.nan), index=d.index)}
ENTRIES = {"15:00": "c1500", "15:30": "c1530"}
FILTS = {"none": lambda P, d: np.isfinite(P), "0.25atr": lambda P, d: np.isfinite(P) & (np.abs(P) >= 0.25 * d.atr20)}

def cell(pname, ename, thr=None, P=None, sign_mult=-1.0, base=None):
    """REVERSED direction = -sign(P). Returns dict of R arrays at 1x/1.5x/2x + mask."""
    d = big if base is None else base
    P = PREDS[pname](d) if P is None else P
    ecol = ENTRIES[ename]
    m = np.isfinite(P) & np.isfinite(d.atr20) & (d.atr20 > 0) & np.isfinite(d[ecol]) & np.isfinite(d.cEnd) & (np.sign(P) != 0)
    if thr is not None: m &= (np.abs(P) >= thr * d.atr20)
    side = sign_mult * np.sign(P[m]); gross = side * (d.cEnd[m] - d[ecol][m]); c = d.cost[m]; a = d.atr20[m]
    return dict(mask=m, gross=gross / a, x1=(gross - c) / a, x15=(gross - 1.5 * c) / a, x2=(gross - 2 * c) / a,
                dates=d.date[m].values, years=d.year[m].values, side=side)

def fmt(s): return f"n {s['n']:5d} avgR {s['avgR']:+.4f} t {s['t']:+6.2f} WR {s['wr']:.3f} PF {s['pf']:.3f} halves(runner) {s['halves_runner']} halves(chrono) {s.get('halves_chrono')}"

print("\n=== 12-cell grid REVERSED (direction = -sign(P)), IS only, net at 1x / 1.5x / 2x micro RT ===")
for pname in PREDS:
    for ename in ENTRIES:
        for fname, thr in (("none", None), ("0.25atr", 0.25)):
            r = cell(pname, ename, thr)
            s1, s15, s2, sg = st(r["x1"], r["dates"]), st(r["x15"]), st(r["x2"]), st(r["gross"])
            print(f"{pname:>8} {ename:>6} {fname:>8} | 1x: {fmt(s1)} | 1.5x avgR {s15['avgR']:+.4f} | 2x avgR {s2['avgR']:+.4f} t {s2['t']:+.2f} | gross avgR {sg['avgR']:+.4f} t {sg['t']:+.2f}")

print("\n=== BASE CELL first30 / 15:00 / none REVERSED ===")
r = cell("first30", "15:00", None)
s1, s15, s2, sg = st(r["x1"], r["dates"]), st(r["x15"]), st(r["x2"]), st(r["gross"])
print("1x  :", fmt(s1)); print("1.5x:", fmt(s15)); print("2x  :", fmt(s2)); print("gross:", fmt(sg))
ys = pd.Series(r["x1"].values, index=r["years"]).groupby(level=0).agg(["mean", "count"])
print("per-year sign (1x):", " ".join(f"{y}:{'+' if v>0 else '-'}({int(n)})" for y, (v, n) in ys.iterrows()))
print("years positive:", int((ys["mean"] > 0).sum()), "of", len(ys))
pi = pd.Series(r["x1"].values, index=big.idx[r["mask"]].values).groupby(level=0).agg(["mean", "count"])
print("per-instrument (1x):", {k: (round(v, 4), int(n)) for k, (v, n) in pi.iterrows()})

print("\n=== UNCONDITIONAL CONTROL: same window 15:00 close -> session close, every eligible IS session, 1x cost ===")
me = np.isfinite(big.atr20) & (big.atr20 > 0) & np.isfinite(big.c1500) & np.isfinite(big.cEnd)
long_ctl = ((big.cEnd - big.c1500) - big.cost)[me] / big.atr20[me]
short_ctl = (-(big.cEnd - big.c1500) - big.cost)[me] / big.atr20[me]
sL, sS = st(long_ctl, big.date[me].values), st(short_ctl, big.date[me].values)
print("always-LONG :", fmt(sL)); print("always-SHORT:", fmt(sS))
# The reversed cell's direction varies by day (-sign(P)); the beta risk is the long-drift leg, so
# primary control = always-long; always-short reported too; the harder comparison is the one with
# the higher control avgR.
rev = pd.Series(r["x1"].values, index=r["dates"]); rev.index = pd.MultiIndex.from_arrays([big.idx[r["mask"]].values, r["dates"]])
for nm, ctl in (("always-long", long_ctl), ("always-short", short_ctl)):
    c = pd.Series(ctl.values, index=pd.MultiIndex.from_arrays([big.idx[me].values, big.date[me].values]))
    j = pd.concat([rev.rename("rev"), c.rename("ctl")], axis=1, join="inner"); dif = j.rev - j.ctl
    sd = st(dif)
    # Welch
    a, b = rev.values, ctl.values
    tw = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    print(f"reversed minus {nm}: paired-by-date n {sd['n']} diff avgR {sd['avgR']:+.4f} t(paired) {sd['t']:+.2f} | Welch t {tw:+.2f}")
# leg-wise: reversed long leg (P<0 days) vs always-long; reversed short leg (P>0) vs always-short (Welch, subsets)
for leg, sgn, ctl, nm in (("long leg (P<0)", 1, long_ctl, "always-long"), ("short leg (P>0)", -1, short_ctl, "always-short")):
    a = r["x1"][r["side"] == sgn].values; b = ctl.values
    tw = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    print(f"reversed {leg}: n {len(a)} avgR {a.mean():+.4f} t {a.mean()/a.std(ddof=1)*np.sqrt(len(a)):+.2f} | minus {nm} diff {a.mean()-b.mean():+.4f} Welch t {tw:+.2f}")

print("\n=== GRADIENT: |P| >= k x ATR20 threshold ladder, base cell first30/15:00 REVERSED, 1x ===")
for k in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5):
    rr = cell("first30", "15:00", k if k > 0 else None); s = st(rr["x1"]); sg = st(rr["gross"])
    print(f"k={k:<4} n {s['n']:5d} net avgR {s['avgR']:+.4f} t {s['t']:+6.2f} | gross avgR {sg['avgR']:+.4f} t {sg['t']:+.2f}")

print("\n=== PLACEBOS (reversed, 1x) ===")
rr = cell("first30", "15:00", None, P=big.p_first_prev); s = st(rr["x1"]); sg = st(rr["gross"])
print(f"shifted-day (previous session's first30 as P): n {s['n']} net avgR {s['avgR']:+.4f} t {s['t']:+.2f} | gross {sg['avgR']:+.4f} t {sg['t']:+.2f}")
# shifted clock: same first30 predictor, trade 14:00 -> 15:00 instead of 15:00 -> close
P = big.p_first; m = np.isfinite(P) & np.isfinite(big.atr20) & (big.atr20 > 0) & np.isfinite(big.c1400) & np.isfinite(big.c1500) & (np.sign(P) != 0)
g = -np.sign(P[m]) * (big.c1500[m] - big.c1400[m]); s = st((g - big.cost[m]) / big.atr20[m]); sg = st(g / big.atr20[m])
print(f"shifted-clock (14:00->15:00 window): n {s['n']} net avgR {s['avgR']:+.4f} t {s['t']:+.2f} | gross {sg['avgR']:+.4f} t {sg['t']:+.2f}")
# shifted predictor clock: 10:00->10:30 return as P, same 15:00->close window
P2 = big.c1030 - big.c1000; rr = cell("first30", "15:00", None, P=P2); s = st(rr["x1"]); sg = st(rr["gross"])
print(f"shifted-predictor (10:00->10:30 as P): n {s['n']} net avgR {s['avgR']:+.4f} t {s['t']:+.2f} | gross {sg['avgR']:+.4f} t {sg['t']:+.2f}")
# sub-threshold band |P| < 0.25 ATR
P = big.p_first; m = np.isfinite(P) & np.isfinite(big.atr20) & (big.atr20 > 0) & np.isfinite(big.c1500) & np.isfinite(big.cEnd) & (np.sign(P) != 0) & (np.abs(P) < 0.25 * big.atr20)
g = -np.sign(P[m]) * (big.cEnd[m] - big.c1500[m]); s = st((g - big.cost[m]) / big.atr20[m]); sg = st(g / big.atr20[m])
print(f"sub-threshold band |P|<0.25 ATR: n {s['n']} net avgR {s['avgR']:+.4f} t {s['t']:+.2f} | gross {sg['avgR']:+.4f} t {sg['t']:+.2f}")
print("\nDONE - IS only; no OOS rows were loaded past the cut.")
