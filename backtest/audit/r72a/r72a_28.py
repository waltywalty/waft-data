"""Round 72A step 3, attempt 28 (SKEW tail-risk premium) REVERSED, IS ONLY.
Reversed cell = SHORT T+1 open -> T+hold close after SKEW trailing-252 pct >= thr.
Copies build logic from backtest/run_r48c_skew.py; IS cut = keys[int(len*0.75)] per
instrument (the runner's own cut); every trade requires BOTH entry and exit session
strictly before the cut. No OOS file is opened, no UNSEAL."""
import os, sys, pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
os.chdir("/home/user/waft-data/backtest")
sys.path.insert(0, "/home/user/waft-data/backtest")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's 1x micro RT cost

sk = pd.read_csv("data/SKEW_history_cboe.csv")
skew = pd.Series(sk.SKEW.values, index=pd.to_datetime(sk.DATE).dt.date)
pct = skew.rolling(252).rank(pct=True)

def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd

def tstat(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std(ddof=1) > 0 else np.nan

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float(a.mean() - b.mean()), float((a.mean() - b.mean()) / np.sqrt(va + vb))

def summ(df, mult=1.0):
    """df has gross (short) pnl, atr, cost, year. R = (gross - mult*cost)/atr."""
    if len(df) == 0: return dict(n=0)
    p = df.gross - mult * df.cost; r = p / df.atr
    m = len(r) // 2
    w, l = p[p > 0], p[p <= 0]
    return dict(n=int(len(r)), avgR=float(r.mean()), t=tstat(r), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else np.inf,
                halves=[float(np.sign(r.iloc[:m].mean())), float(np.sign(r.iloc[m:].mean()))])

data = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    data[idx] = (d, {k: i for i, k in enumerate(d.index)}, d.index.tolist(), cutd)
    isd = d[~d.oos]
    print(f"{idx}: {len(d)} sessions; IS cut used = {cutd} (IS sessions {len(isd)}, {isd.index[0]}..{isd.index[-1]})")

def cell(kind, thr, hold, sig=pct, lo=None):
    """Reversed cell: SHORT. kind 'high': pct>=thr ; 'low': pct<=thr ; 'band': lo<pct<thr."""
    recs = []
    for idx, (d, kpos, keys, cutd) in data.items():
        busy = -1
        for k, p in sig.items():
            if not np.isfinite(p) or k not in kpos: continue
            trig = (p >= thr) if kind == "high" else (p <= thr) if kind == "low" else (lo <= p < thr)
            if not trig: continue
            i, j = kpos[k] + 1, kpos[k] + hold
            if j >= len(keys) or i <= busy: continue
            ek, xk = keys[i], keys[j]
            if ek >= cutd or xk >= cutd: continue                  # IS only, entry AND exit before cut
            e, xp, a = d.o[ek], d.c[xk], d.atr20[ek]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0): continue
            recs.append(dict(idx=idx, ek=ek, gross=-(xp - e), cost=MICRO[idx], atr=a, year=ek.year))
            busy = j
    df = pd.DataFrame(recs).sort_values("ek").reset_index(drop=True) if recs else pd.DataFrame(columns=["idx","ek","gross","cost","atr","year"])
    return df

def control(hold):
    """Unconditional ALWAYS-SHORT, every eligible IS session as entry day (open T -> close T+hold-1),
    non-overlapping (busy-until) to match the cell's trade structure for hold>1."""
    recs = []
    for idx, (d, kpos, keys, cutd) in data.items():
        busy = -1
        for i in range(1, len(keys)):
            j = i + hold - 1
            if j >= len(keys) or i <= busy: continue
            ek, xk = keys[i], keys[j]
            if ek >= cutd or xk >= cutd: continue
            e, xp, a = d.o[ek], d.c[xk], d.atr20[ek]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0): continue
            recs.append(dict(idx=idx, ek=ek, gross=-(xp - e), cost=MICRO[idx], atr=a, year=ek.year))
            busy = j
    return pd.DataFrame(recs).sort_values("ek").reset_index(drop=True)

def R(df, mult=1.0): return ((df.gross - mult * df.cost) / df.atr).values

def report(name, df, ctl=None):
    s1, s15, s2 = summ(df, 1.0), summ(df, 1.5), summ(df, 2.0)
    if s1.get("n", 0) == 0: print(f"{name}: n=0"); return s1
    line = (f"{name:<42} n {s1['n']:>5} avgR x1 {s1['avgR']:+.4f} t {s1['t']:+.2f} | x1.5 {s15['avgR']:+.4f} "
            f"| x2 {s2['avgR']:+.4f} t {s2['t']:+.2f} | WR {s1['wr']*100:.1f}% PF {s1['pf']:.3f} halves {s1['halves']}")
    if ctl is not None:
        dm, dt = welch(R(df), R(ctl))
        line += f" | vs ctl diff {dm:+.4f} t {dt:+.2f}"
    print(line); return s1

POOL = ("SPX", "NDX", "RTY")
def pool(df): return df[df.idx.isin(POOL)]
def gold(df): return df[df.idx == "GOLD"]

print("\n=== REVERSED HEADLINE: SHORT T+1 open->T+1 close after SKEW pct >= 0.80 (SPX/NDX/RTY pooled, IS) ===")
h = pool(cell("high", 0.8, 1)); c1 = pool(control(1))
s = report("REV 80th/1d SHORT", h, c1)
print("per-year (avgR x1, sign):")
yr = h.assign(R=R(h)).groupby("year").R.agg(["count", "mean"])
print("  " + "  ".join(f"{y}:{'+' if m > 0 else '-'}({n})" for y, (n, m) in yr.iterrows()))
signs = "".join("+" if m > 0 else "-" for m in yr["mean"])
print("  per-year sign string:", signs, f"({(yr['mean']>0).sum()} of {len(yr)} years positive)")
print("per-instrument:")
for ix in POOL: report(f"  {ix} REV 80th/1d", h[h.idx == ix], c1[c1.idx == ix])

print("\n=== UNCONDITIONAL CONTROL: always-SHORT open->close, every eligible IS session, 1x cost ===")
cs = report("CTL always-short 1d (pooled)", c1)
for ix in POOL: report(f"  {ix} CTL always-short 1d", c1[c1.idx == ix])
dm, dt = welch(R(h), R(c1))
print(f"\nDIFF reversed - control (Welch, two independent samples; cell days are a subset of control days,"
      f" paired diff on shared dates is identically 0 so pairing is degenerate): avgR {dm:+.4f}  t {dt:+.2f}")
# complement version: cell days vs NON-signal days
comp = c1[~c1.set_index(["idx", "ek"]).index.isin(h.set_index(["idx", "ek"]).index)]
dm2, dt2 = welch(R(h), R(comp))
print(f"DIFF reversed - complement (non-signal IS days, n {len(comp)}, avgR {R(comp).mean():+.4f}): avgR {dm2:+.4f} t {dt2:+.2f}")

print("\n=== FAMILY GRID REVERSED (short), pooled IS, with matching always-short control per hold ===")
c5 = pool(control(5))
for thr in (0.8, 0.9):
    for hold in (1, 5):
        report(f"REV high>={thr} hold {hold}d SHORT", pool(cell("high", thr, hold)), c1 if hold == 1 else c5)
report("CTL always-short 5d non-overlap (pooled)", c5)

print("\n=== GRADIENT: threshold ladder reversed (short), hold 1d, pooled IS ===")
for thr in (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95):
    report(f"REV pct>={thr:.2f} hold 1d SHORT", pool(cell("high", thr, 1)), c1)
print("--- band ladder (disjoint percentile bands, short 1d) ---")
for lo, hi in ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 0.9), (0.9, 1.01)):
    report(f"REV band [{lo:.1f},{hi:.2f}) SHORT 1d", pool(cell("band", hi, 1, lo=lo)), c1)

print("\n=== PLACEBOS (reversed) ===")
report("sub-threshold band 60-80th SHORT 1d", pool(cell("band", 0.8, 1, lo=0.6)), c1)
for lag in (5, 10, 21):
    shifted = pd.Series(pct.values, index=pct.index).shift(lag)   # signal from `lag` SKEW-days earlier
    report(f"shifted-clock lag {lag}d pct>=0.8 SHORT 1d", pool(cell("high", 0.8, 1, sig=shifted)), c1)
report("regime contrast: low-SKEW <=20th SHORT 1d", pool(cell("low", 0.2, 1)), c1)
report("regime contrast: low-SKEW <=20th SHORT 5d", pool(cell("low", 0.2, 5)), c5)

print("\n=== GOLD diagnostic reversed (IS) ===")
g = gold(cell("high", 0.8, 1)); gc = gold(control(1))
report("GOLD REV 80th/1d SHORT", g, gc); report("GOLD CTL always-short 1d", gc)

print("\n=== SANITY: registered-direction LONG 80th/1d at 1x, recomputed (should match ledger -0.0398 t -2.97, n 2701) ===")
hl = h.copy(); hl["gross"] = -hl.gross
report("LONG 80th/1d (recomputed)", hl)
