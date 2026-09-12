"""Round 72A step 3, attempt 9 (VIX term-structure dip-buy) REVERSED, IS ONLY.
Reuses run_r42i_vixdip.py's frame-build logic (copied verbatim), filters to ~oos
(sessions before each instrument's own IS cut = keys[int(len*0.75)]), and scores
the -1 x registered direction (SHORT the noon dip, hold to close) with 1x/1.5x/2x
micro costs subtracted, the always-short 12:00->close control, gradient, placebo.
Never touches OOS rows. Run from /home/user/waft-data/backtest/."""
import sys, os, json, warnings
import pandas as pd, numpy as np
warnings.filterwarnings("ignore")
os.chdir("/home/user/waft-data/backtest"); sys.path.insert(0, ".")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}   # runner's 1x round-trip micro cost (pts)

def loadvix(name):
    df = pd.read_csv(f"data/{name}")
    d = pd.to_datetime(df.DATE, format="mixed")
    return pd.Series(df.CLOSE.values, index=d.dt.date)
vix, vix3 = loadvix("VIX_daily_github.csv"), loadvix("VIX3M_daily_github.csv")
common = vix.index.intersection(vix3.index)
ratio = (vix[common] / vix3[common]); ratio_prior = ratio.shift(1).dropna()
ratio_stale = ratio.shift(21).dropna()   # placebo: month-stale term structure

frames = {}
for idx in MICRO:
    rth = rth_of(load_frame(idx)); rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        if len(g) < 50 or hm[0] > 935: continue
        m12 = np.where(hm < 1200)[0]
        if not len(m12): continue
        rows_d.append(dict(skey=skey, o=g.open.values[0], c12=g.close.values[m12[-1]],
                           cEnd=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["ratio"] = pd.Series(d.index.map(lambda k: ratio_prior.get(k, np.nan)), index=d.index)
    d["ratio_stale"] = pd.Series(d.index.map(lambda k: ratio_stale.get(k, np.nan)), index=d.index)
    d = d[np.isfinite(d.ratio) & np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    print(f"{idx}: {len(d)} joined sessions; IS cut = {cutd} (IS n={int((~d.oos).sum())}); OOS rows DROPPED")
    d = d[~d.oos].copy()                      # ---- OOS FIREWALL: IS rows only from here on
    d["idx"] = idx; d["cost"] = MICRO[idx]
    d["dipR"] = (d.c12 - d.o) / d.atr20       # morning move in ATR units
    d["gross_short"] = -(d.cEnd - d.c12)      # reversed direction: SHORT 12:00 close -> session close
    d["year"] = [k.year for k in d.index]
    d["prev_dipR"] = d.dipR.shift(1)          # placebo: yesterday's dip
    frames[idx] = d
allis = pd.concat(frames.values()).sort_index()

def R(df, mult=1.0): return (df.gross_short - mult * df.cost) / df.atr20
def stats(df, mult=1.0):
    r = R(df, mult).values; p = (df.gross_short - mult * df.cost).values
    n = len(r)
    if n < 2: return dict(n=n)
    m = n // 2; w, l = p[p > 0], p[p <= 0]
    return dict(n=n, avgR=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(n)),
                wr=float((p > 0).mean()), pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])
def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a.mean() - b.mean(); se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se)
def yearsigns(df, mult=1.0):
    r = R(df, mult); g = r.groupby(df.year.values).mean()
    return " ".join(f"{y}:{'+' if v > 0 else '-'}" for y, v in g.items()), int((g > 0).sum()), int(len(g))

GATES = {"none": lambda d: np.ones(len(d), bool),
         "contango": lambda d: d.ratio.values <= 0.95,
         "backwd": lambda d: d.ratio.values >= 1.0}
def cell(k, gate, d=allis, col="dipR"):
    return d[(d[col].values <= -k) & GATES[gate](d)]

out = {}
print("\n=== REVERSED grid (SHORT the noon dip -> close), IS only, pooled ATR-normalized ===")
print(f"{'k':>4} {'gate':>9} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR1x':>8} {'t1x':>6} {'avgR1.5':>8} {'avgR2x':>8} {'t2x':>6} {'halves':>12}  yearsigns")
for k in (0.3, 0.5):
    for g in GATES:
        c = cell(k, g); s1, s15, s2 = stats(c), stats(c, 1.5), stats(c, 2.0)
        ys, npos, ny = yearsigns(c)
        out[f"k{k}_{g}"] = dict(x1=s1, x15=s15, x2=s2, years=ys, years_pos=f"{npos}/{ny}")
        print(f"{k:>4} {g:>9} | {s1['n']:>5} {s1['wr']*100:>5.1f}% {s1['pf']:>5.2f} {s1['avgR']:>+8.4f} {s1['t']:>+6.2f} "
              f"{s15['avgR']:>+8.4f} {s2['avgR']:>+8.4f} {s2['t']:>+6.2f} {str(s1['halves']):>12}  {ys}")

print("\n=== UNCONDITIONAL CONTROL: always-SHORT 12:00 close -> session close, every eligible IS session, 1x cost ===")
ctl = allis; cs = stats(ctl); ys, npos, ny = yearsigns(ctl)
print(f"control pooled: n {cs['n']} avgR {cs['avgR']:+.4f} t {cs['t']:+.2f} WR {cs['wr']*100:.1f}% PF {cs['pf']:.2f} halves {cs['halves']} years {ys}")
for idx, d in frames.items():
    s = stats(d); print(f"  {idx}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f}")
out["control"] = cs

print("\n=== DIFFERENCE reversed - control (Welch, two-sample) ===")
for key in ("k0.5_contango", "k0.3_contango", "k0.5_none", "k0.3_none"):
    k = float(key.split("_")[0][1:]); g = key.split("_")[1]
    c = cell(k, g); comp = allis.drop(c.index.intersection(allis.index), errors="ignore")
    comp = allis[~((allis.dipR.values <= -k) & GATES[g](allis))]
    dA, tA = welch(R(c), R(ctl))     # vs full control (cell is a subset -> conservative, shared rows)
    dB, tB = welch(R(c), R(comp))    # vs complement (disjoint samples)
    out[key]["diff_vs_control_all"] = dict(avgR=dA, t=tA); out[key]["diff_vs_complement"] = dict(avgR=dB, t=tB)
    print(f"{key:>14}: vs all-sessions control d={dA:+.4f} t={tA:+.2f} | vs complement (disjoint) d={dB:+.4f} t={tB:+.2f}")

print("\n=== GRADIENT: k ladder reversed (1x cost), contango gate and ungated ===")
for g in ("contango", "none"):
    for k in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        c = cell(k, g); s = stats(c)
        if s["n"] < 10: print(f"  {g:>8} k={k:.1f}: n {s['n']} (too few)"); continue
        print(f"  {g:>8} k={k:.1f}: n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
print("--- ratio-threshold ladder at k=0.5 (reversed, 1x): ratio <= x ---")
for x in (0.80, 0.85, 0.90, 0.95, 1.00, 9.9):
    c = allis[(allis.dipR.values <= -0.5) & (allis.ratio.values <= x)]; s = stats(c)
    print(f"  ratio<={x:.2f}: n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
print("--- ratio bands at k=0.5 (reversed, 1x) ---")
for lo, hi in ((0, 0.85), (0.85, 0.90), (0.90, 0.95), (0.95, 1.0), (1.0, 9)):
    c = allis[(allis.dipR.values <= -0.5) & (allis.ratio.values > lo) & (allis.ratio.values <= hi)]; s = stats(c)
    print(f"  ratio in ({lo},{hi}]: n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f}")

print("\n=== PLACEBO (reversed, 1x) ===")
band = allis[(allis.dipR.values > -0.3) & (allis.dipR.values <= 0) & GATES["contango"](allis)]; s = stats(band)
print(f"sub-threshold band (-0.3 < dipR <= 0, contango) short: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
up = allis[(allis.dipR.values >= 0.5) & GATES["contango"](allis)]; s = stats(up)
print(f"mirror-signal (morning UP >= 0.5 ATR, contango) SHORT: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
pv = allis[(allis.prev_dipR.values <= -0.5) & GATES["contango"](allis)]; s = stats(pv)
print(f"shifted-day (YESTERDAY's dip <= -0.5, contango) short today: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
st = allis[(allis.dipR.values <= -0.5) & (allis.ratio_stale.values <= 0.95)]; s = stats(st)
print(f"stale gate (ratio lagged 21d <= 0.95, k=0.5) short: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
print("\n=== per-instrument, primary reversed cell k0.5 contango, 1x ===")
for idx, d in frames.items():
    s = stats(cell(0.5, "contango", d)); print(f"  {idx}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s.get('halves')}")
json.dump(out, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_9.json", "w"), indent=1, default=float)
