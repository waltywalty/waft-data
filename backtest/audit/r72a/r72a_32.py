"""R72A step 3, attempt 32 (r51_weekday) REVERSED scoring, IS ONLY.
Reuses build_days() logic from backtest/run_r51_weekday.py verbatim (same load_frame/rth_of,
same ATR20, same 75% cut) and filters to ~oos before any statistic is computed.
Reversed cells: fri_SHORT (oc, cc) and mon_LONG (oc, cc). Headline = fri_short oc.
Costs: MICRO round trip subtracted at 1x/1.5x/2x. Never touches OOS rows."""
import os, sys, json, warnings
import pandas as pd, numpy as np
warnings.filterwarnings("ignore")
os.chdir("/home/user/waft-data/backtest")
sys.path.insert(0, "/home/user/waft-data/backtest")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

def build_days(idx):  # copied verbatim from run_r51_weekday.py
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d["dow"] = [k.weekday() for k in d.index]
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd

HOLDS = {"oc": ("o", "c"), "cc": ("prevc", "c")}
INSTR = ["SPX", "NDX", "RTY"]
if os.path.exists("data/XAUUSD_5m.csv"): INSTR.append("GOLD")

IS = {}
for idx in INSTR:
    d, cutd = build_days(idx)
    print(f"{idx}: IS cut {cutd} (sessions before cut = {int((~d.oos).sum())}, dropped OOS = {int(d.oos.sum())})")
    d = d[~d.oos].copy()          # ---- OOS FIREWALL: IS rows only from here on
    assert (d.index < cutd).all()
    d["idx"] = idx; d["cost"] = MICRO[idx]
    IS[idx] = d

def rows_for(dows, hold, instrs):
    ecol, xcol = HOLDS[hold]
    out = []
    for idx in instrs:
        d = IS[idx]
        m = d.dow.isin(dows) & np.isfinite(d[ecol]) & np.isfinite(d[xcol]) & np.isfinite(d.atr20) & (d.atr20 > 0)
        s = d[m]
        out.append(pd.DataFrame(dict(date=s.index, idx=idx, gross=(s[xcol] - s[ecol]).values,
                                     atr=s.atr20.values, cost=MICRO[idx])))
    return pd.concat(out, ignore_index=True)

def R(df, side, k):
    return side * df.gross.values / df.atr.values - k * df.cost.values / df.atr.values

def tstat(r):
    r = np.asarray(r, float); return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else np.nan

def st(df, side, k=1.0, label=""):
    r = R(df, side, k); ok = np.isfinite(r); r = r[ok]; dd = df[ok]
    m = len(r) // 2
    # runner-style halves: order = instrument-concatenated (as the runner does)
    halves_runner = [float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))]
    o = np.argsort(dd.date.values, kind="stable"); rc = r[o]
    halves_chrono = [float(np.sign(rc[:m].mean())), float(np.sign(rc[m:].mean()))]
    w, l = r[r > 0], r[r <= 0]
    pf = float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else np.inf
    yrs = pd.DatetimeIndex(pd.to_datetime(dd.date.values)).year
    py = pd.Series(r).groupby(np.asarray(yrs)).agg(["mean", "count"])
    per_year = {int(y): ("+" if v["mean"] > 0 else "-") for y, v in py.iterrows()}
    return dict(label=label, n=int(len(r)), avgR=float(r.mean()), t=tstat(r), wr=float((r > 0).mean()),
                pf=pf, halves_chrono=halves_chrono, halves_runner=halves_runner, per_year=per_year,
                per_year_mean={int(y): round(float(v["mean"]), 4) for y, v in py.iterrows()})

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float((a.mean() - b.mean()) / np.sqrt(va + vb))

def full_cell(name, dows, side, hold, instrs=("SPX", "NDX", "RTY")):
    df = rows_for(dows, hold, instrs)
    s1, s15, s2 = st(df, side, 1.0), st(df, side, 1.5), st(df, side, 2.0)
    s0 = st(df, side, 0.0)
    print(f"\n=== {name} [{hold}] side={side:+d} instruments={list(instrs)} ===")
    print(f" gross  : n {s0['n']} avgR {s0['avgR']:+.4f} t {s0['t']:+.2f}")
    print(f" net 1x : n {s1['n']} avgR {s1['avgR']:+.4f} t {s1['t']:+.2f} WR {s1['wr']:.3f} PF {s1['pf']:.3f} halves(chrono) {s1['halves_chrono']} halves(runner-order) {s1['halves_runner']}")
    print(f" net1.5x: avgR {s15['avgR']:+.4f} t {s15['t']:+.2f}")
    print(f" net 2x : avgR {s2['avgR']:+.4f} t {s2['t']:+.2f}")
    print(f" per-year sign (1x): {s1['per_year']}")
    print(f" per-year mean (1x): {s1['per_year_mean']}")
    # unconditional control: same hold, all weekdays, same direction, 1x cost
    ctl = rows_for((0, 1, 2, 3, 4), hold, instrs)
    c1 = st(ctl, side, 1.0)
    rc, rcell = R(ctl, side, 1.0), R(df, side, 1.0)
    comp = rows_for(tuple(x for x in range(5) if x not in dows), hold, instrs)
    rcomp = R(comp, side, 1.0)
    dW = rcell.mean() - rc.mean(); tW = welch(rcell, rc)
    dC = rcell.mean() - rcomp.mean(); tC = welch(rcell, rcomp)
    print(f" CONTROL always-{'long' if side > 0 else 'short'} {hold} all weekdays 1x: n {c1['n']} avgR {c1['avgR']:+.4f} t {c1['t']:+.2f} halves {c1['halves_chrono']}")
    print(f" diff cell-control (Welch, cell subset of control): dAvgR {dW:+.4f} t {tW:+.2f}")
    print(f" diff cell-complement (Welch, cell vs other weekdays): dAvgR {dC:+.4f} t {tC:+.2f}")
    return dict(cell=name, hold=hold, side=side, gross=s0, x1=s1, x15=s15, x2=s2,
                control=dict(n=c1["n"], avgR=c1["avgR"], t=c1["t"], halves=c1["halves_chrono"]),
                diff_vs_control=dict(avgR=float(dW), t=tW, method="Welch cell vs all-weekday control (cell is a subset)"),
                diff_vs_complement=dict(avgR=float(dC), t=tC, method="Welch cell vs other weekdays"))

out = {}
out["fri_short_oc"] = full_cell("fri_SHORT", (4,), -1, "oc")
out["fri_short_cc"] = full_cell("fri_SHORT", (4,), -1, "cc")
out["mon_long_cc"]  = full_cell("mon_LONG", (0,), +1, "cc")
out["mon_long_oc"]  = full_cell("mon_LONG", (0,), +1, "oc")

# GRADIENT / PLACEBO: the family's own parameter axis is the weekday. Reversed rule applied
# to each weekday (shifted-day placebo = neighbouring weekdays). Net 1x, indices pooled.
print("\n=== GRADIENT / SHIFTED-DAY PLACEBO: reversed rule on every weekday (net 1x, indices pooled) ===")
names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
grad = {}
for hold in ("oc", "cc"):
    for side, lab in ((-1, "SHORT"), (+1, "LONG")):
        line = []
        for dw in range(5):
            s = st(rows_for((dw,), hold, INSTR[:3]), side, 1.0)
            grad[f"{lab}_{hold}_{names[dw]}"] = dict(n=s["n"], avgR=round(s["avgR"], 4), t=round(s["t"], 2))
            line.append(f"{names[dw]} {s['avgR']:+.4f} (t {s['t']:+.2f})")
        print(f" {lab:5s} {hold}: " + " | ".join(line))

# per-instrument breakdown of the headline reversed cells
print("\n=== per-instrument, net 1x ===")
per = {}
for key, dows, side, hold in (("fri_short_oc", (4,), -1, "oc"), ("mon_long_cc", (0,), +1, "cc")):
    per[key] = {}
    for idx in INSTR:
        s = st(rows_for(dows, hold, (idx,)), side, 1.0)
        per[key][idx] = dict(n=s["n"], avgR=round(s["avgR"], 4), t=round(s["t"], 2), halves=s["halves_chrono"])
        print(f" {key} {idx}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves_chrono']}")

# sanity: reproduce registered-direction numbers from the JSON
print("\n=== sanity vs results/r51_weekday.json (registered direction, net 1x) ===")
for name, dows, side, hold in (("fri_long", (4,), +1, "oc"), ("mon_short", (0,), -1, "cc")):
    s = st(rows_for(dows, hold, INSTR[:3]), side, 1.0)
    print(f" {name} {hold}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves(runner-order) {s['halves_runner']}")

json.dump(dict(cells=out, gradient=grad, per_instrument=per),
          open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_32.json", "w"),
          indent=1, default=float)
