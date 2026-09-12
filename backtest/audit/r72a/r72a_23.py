"""Round 72A step 3, attempt 23 (equity P/C contrarian gate), REVERSED, IS ONLY.
Reuses run_r46_putcall.py's build functions (via run_r37_scalps.py prefix) verbatim.
Never reads any *oos* file, never computes on entry sessions >= the runner's IS cut.
Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, warnings, os, sys
sys.path.insert(0, "/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")
os.chdir("/home/user/waft-data/backtest")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

# --- CBOE equity P/C (identical parse to runner) ---
lines = open("data/cboe_equitypc.csv").read().splitlines()
recs = []
for ln in lines:
    parts = [p.strip() for p in ln.split(",")]
    if len(parts) == 5 and "/" in parts[0]:
        try:
            recs.append((pd.Timestamp(parts[0]).date(), float(parts[4])))
        except Exception:
            pass
pc = pd.Series(dict(recs)).sort_index()
pc_pct = pc.rolling(252).rank(pct=True)
print(f"CBOE equity P/C: {len(pc)} days {pc.index[0]}..{pc.index[-1]}")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    return d


data = {}
for idx in MICRO:
    d = build_days(idx)
    keys = d.index.tolist()
    kpos = {k: i for i, k in enumerate(keys)}
    span = [k for k in keys if pc.index[0] <= k <= pc.index[-1]]
    cutd = span[int(len(span) * 0.75)]
    data[idx] = (d, keys, kpos, cutd)
    print(f"{idx}: {len(span)} joined sessions, IS CUT = {cutd} (entries >= cut EXCLUDED)")


def trades(thr, hold, side, sgn, lag=0, band=None):
    """side: 'fear' (pct >= thr) or 'greed' (pct <= thr); band=(lo,hi) -> lo <= pct < hi.
    sgn: +1 long, -1 short. lag: use pct from lag sessions earlier (placebo).
    Returns IS-only DataFrame with gross pnl, atr, idx, entry date."""
    out = []
    for idx, (d, keys, kpos, cutd) in data.items():
        busy = -1
        for k, pct in pc_pct.items():
            if not np.isfinite(pct) or k not in kpos:
                continue
            if band is not None:
                trig = band[0] <= pct < band[1]
            else:
                trig = pct >= thr if side == "fear" else pct <= thr
            if not trig:
                continue
            i = kpos[k] + 1 + lag
            j = kpos[k] + hold + lag
            if i >= len(keys) or j >= len(keys) or i <= busy:
                continue
            ek, xk = keys[i], keys[j]
            if ek >= cutd:              # OOS FIREWALL
                continue
            e, xp, a = d.o.get(ek, np.nan), d.c.get(xk, np.nan), d.atr20.get(ek, np.nan)
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            out.append(dict(gross=sgn * (xp - e), atr=a, idx=idx, ek=ek, cost=MICRO[idx]))
            busy = j
    return pd.DataFrame(out)


def control(hold, sgn):
    """Unconditional: EVERY eligible IS session (prior-day pct available), same window, same sgn.
    Non-overlapping via busy-until, same as the cell."""
    out = []
    for idx, (d, keys, kpos, cutd) in data.items():
        busy = -1
        for k, pct in pc_pct.items():
            if not np.isfinite(pct) or k not in kpos:
                continue
            i = kpos[k] + 1; j = kpos[k] + hold
            if i >= len(keys) or j >= len(keys) or i <= busy:
                continue
            ek, xk = keys[i], keys[j]
            if ek >= cutd:
                continue
            e, xp, a = d.o.get(ek, np.nan), d.c.get(xk, np.nan), d.atr20.get(ek, np.nan)
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            out.append(dict(gross=sgn * (xp - e), atr=a, idx=idx, ek=ek, cost=MICRO[idx]))
            busy = j
    return pd.DataFrame(out)


def R(df, mult):
    return (df.gross - mult * df.cost) / df.atr


def tstat(r):
    r = np.asarray(r, float)
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else float("nan")


def summarize(df, label):
    if len(df) < 10:
        print(f"{label}: n={len(df)} (<10)"); return None
    df = df.sort_values("ek").reset_index(drop=True)
    r1, r15, r2 = R(df, 1.0), R(df, 1.5), R(df, 2.0)
    p1 = df.gross - df.cost
    w, l = p1[p1 > 0], p1[p1 <= 0]
    pf = float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf")
    m = len(df) // 2
    halves = [float(np.sign(r1[:m].mean())), float(np.sign(r1[m:].mean()))]
    yrs = df.assign(r=r1).groupby(df.ek.map(lambda x: x.year)).r.agg(["mean", "count"])
    ysign = " ".join(f"{y}:{'+' if v > 0 else '-'}({int(n)})" for y, (v, n) in yrs.iterrows())
    res = dict(n=int(len(df)), avgR_x1=float(r1.mean()), t_x1=tstat(r1), avgR_x15=float(r15.mean()),
               avgR_x2=float(r2.mean()), t_x2=tstat(r2), wr=float((p1 > 0).mean()), pf=pf,
               halves=halves, per_year=ysign, gross_avgR=float((df.gross / df.atr).mean()))
    print(f"{label}: n {res['n']} gross avgR {res['gross_avgR']:+.4f} | x1 avgR {res['avgR_x1']:+.4f} t {res['t_x1']:+.2f} "
          f"| x1.5 {res['avgR_x15']:+.4f} | x2 {res['avgR_x2']:+.4f} t {res['t_x2']:+.2f} | WR {res['wr']*100:.1f}% PF {pf:.3f} halves {halves}")
    print(f"    per-year: {ysign}")
    return res


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(a.mean() - b.mean()), float((a.mean() - b.mean()) / se)


print("\n=== REVERSED headline: fear >= 90th pct, SHORT T+1 open -> T+1 close (IS only) ===")
cell = trades(0.9, 1, "fear", -1)
rev = summarize(cell, "REV 90/1d short")
for idx in MICRO:
    summarize(cell[cell.idx == idx], f"  {idx}")
# runner-order halves (instrument-sequential, as the runner's stats() computed them)
r_runner = R(cell, 1.0).values; m = len(r_runner) // 2
print(f"  runner-order halves (SPX,NDX,RTY sequential): [{np.sign(r_runner[:m].mean()):+.0f},{np.sign(r_runner[m:].mean()):+.0f}]")

print("\n=== CONTROL: always-SHORT T+1 open -> close on every eligible IS session ===")
ctl = control(1, -1)
ctl_s = summarize(ctl, "CTL always-short 1d")
# cell is a subset of control days (per instrument); paired-by-date is degenerate (identical
# rows), so: Welch cell vs ALL control days (diff = beta test) and Welch cell vs COMPLEMENT.
key = set(zip(cell.idx, cell.ek))
mask = np.array([(i, k) in key for i, k in zip(ctl.idx, ctl.ek)])
print(f"  cell rows {len(cell)}, matched in control {mask.sum()}, complement {(~mask).sum()}")
rc, rall, rcomp = R(cell, 1.0), R(ctl, 1.0), R(ctl[~mask], 1.0)
d_all, t_all = welch(rc, rall)
d_comp, t_comp = welch(rc, rcomp)
print(f"  diff vs ALL control:        {d_all:+.4f}  Welch t {t_all:+.2f}")
print(f"  diff vs COMPLEMENT (indep): {d_comp:+.4f}  Welch t {t_comp:+.2f}")

print("\n=== REVERSED family grid (short on fear; long on greed) ===")
for thr, hold in [(0.8, 1), (0.8, 3), (0.9, 1), (0.9, 3)]:
    summarize(trades(thr, hold, "fear", -1), f"REV fear {int(thr*100)}th/{hold}d SHORT")
for hold in (1, 3):
    summarize(trades(0.1, hold, "greed", +1), f"REV greed <=10th/{hold}d LONG")
print("  control always-short 3d:")
summarize(control(3, -1), "CTL always-short 3d")

print("\n=== GRADIENT: threshold ladder, SHORT T+1 open->close, pct >= thr (IS) ===")
grad = {}
for thr in (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975):
    s = summarize(trades(thr, 1, "fear", -1), f"  >= {thr:.3f}")
    if s: grad[thr] = s
print("\n=== GRADIENT (disjoint bands), SHORT 1d ===")
for lo, hi in [(0.0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.01)]:
    summarize(trades(None, 1, "fear", -1, band=(lo, hi)), f"  band [{lo:.2f},{hi:.2f})")

print("\n=== PLACEBO (reversed) ===")
summarize(trades(None, 1, "fear", -1, band=(0.5, 0.8)), "sub-threshold band [50th,80th) SHORT 1d")
summarize(trades(None, 1, "fear", -1, band=(0.6, 0.9)), "sub-threshold band [60th,90th) SHORT 1d")
for lag in (1, 5, 20):
    summarize(trades(0.9, 1, "fear", -1, lag=lag), f"shifted signal: >=90th pct from {lag} session(s) earlier, SHORT 1d")

print("\nIS cut dates used:", {k: str(v[3]) for k, v in data.items()})
