"""Round 72A step 3, attempt 45 (r62_mich) REVERSED: SHORT indices while
consumer-pessimism regime active. IS ONLY. Reuses run_r62_mich.py build
functions (source split before `frames =` so the runner's grid/JSON/OOS
tail never executes). Never touches oos=True rows."""
import numpy as np, pandas as pd, json, warnings, sys, os
os.chdir("/home/user/waft-data/backtest"); sys.path.insert(0, "/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")
src = open("run_r62_mich.py").read().split("frames = {idx:")[0]
ns = {}
exec(src, ns)
build_days, MICRO, mich = ns["build_days"], ns["MICRO"], ns["mich"]

frames = {idx: build_days(idx) for idx in MICRO}
print("\n=== IS cut per instrument (rows with oos=True are DROPPED before anything else) ===")
IS = {}
for idx, d in frames.items():
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]
    dd = d[~d.oos].copy()
    assert (dd.index < cutd).all() and not dd.oos.any()
    dd["idx"] = idx
    IS[idx] = dd
    print(f"{idx}: {len(d)} sessions, IS cut date {cutd} (first OOS session), IS n {len(dd)} "
          f"{dd.index[0]}..{dd.index[-1]}")
del frames

# eligible pooled IS sessions (runner's mask, minus the regime clause)
rows = []
for idx, dd in IS.items():
    m = np.isfinite(dd.sent) & np.isfinite(dd.prevc) & np.isfinite(dd.atr20) & (dd.atr20 > 0)
    s = dd[m]
    rows.append(pd.DataFrame(dict(date=s.index, idx=idx, sent=s.sent.values, mfg=s.mfg.values,
                                  move=(s.c - s.prevc).values, atr=s.atr20.values,
                                  cost=MICRO[idx] / 20)))
E = pd.concat(rows).sort_values(["date", "idx"]).reset_index(drop=True)
E["year"] = pd.to_datetime(E.date).dt.year
print(f"\nEligible pooled IS sessions: {len(E)}; last date {E.date.max()}")


def R_short(df, k=1.0):
    """reversed direction: SHORT close-to-close, k x micro cost SUBTRACTED, ATR20-normalised"""
    return (-df.move - k * df.cost) / df.atr


def stats(r, label=""):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    n = len(r)
    if n == 0:
        return dict(n=0)
    m = n // 2
    w, l = r[r > 0], r[r <= 0]
    pf = w.sum() / abs(l.sum()) if len(l) and l.sum() < 0 else np.inf
    t = r.mean() / r.std(ddof=1) * np.sqrt(n) if n > 1 and r.std(ddof=1) > 0 else np.nan
    return dict(n=n, avgR=r.mean(), t=t, wr=(r > 0).mean(), pf=pf,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return (a.mean() - b.mean()) / se


def show(lbl, st, extra=""):
    if st["n"] == 0:
        print(f"{lbl:>34}: n 0"); return
    print(f"{lbl:>34}: n {st['n']:>5} avgR {st['avgR']:+.4f} t {st['t']:+.2f} WR {st['wr']*100:.1f}% "
          f"PF {st['pf']:.3f} halves {st['halves']} {extra}")


out = {}
print("\n=== REVERSED CELLS (SHORT while Michigan sentiment < thr), pooled SPX/NDX/RTY, IS ===")
for thr in (65, 70):
    c = E[E.sent < thr].sort_values(["date", "idx"])
    res = {}
    for k in (1.0, 1.5, 2.0):
        st = stats(R_short(c, k)); res[k] = st
        show(f"thr<{thr} short, cost x{k}", st)
    # runner-style ordering (instrument concatenation) halves for comparison
    c_run = pd.concat([c[c.idx == i] for i in MICRO])
    st_run = stats(R_short(c_run, 1.0))
    print(f"{'':>34}  (runner-ordering halves, x1: {st_run['halves']})")
    r1 = R_short(c, 1.0)
    yrs = c.assign(R=r1.values).groupby("year").R.agg(["count", "mean"])
    yrs["t"] = c.assign(R=r1.values).groupby("year").R.apply(lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 else np.nan)
    print(f"{'':>34}  per-year: " + ", ".join(f"{y}:{'+' if m > 0 else '-'}(n{int(n)},{m:+.3f})" for y, (n, m, t) in yrs.iterrows()))
    print(f"{'':>34}  per-instrument x1: " + ", ".join(
        f"{i}: n {stats(R_short(c[c.idx == i]))['n']} avgR {stats(R_short(c[c.idx == i])).get('avgR', float('nan')):+.4f}"
        for i in MICRO))
    # episodes: contiguous runs of regime-active dates
    dates = sorted(c.date.unique())
    alld = sorted(E.date.unique()); pos = {d: i for i, d in enumerate(alld)}
    ep, start = [], dates[0]
    for a, b in zip(dates, dates[1:]):
        if pos[b] - pos[a] > 1:
            ep.append((start, a)); start = b
    ep.append((start, dates[-1]))
    ep_signs = []
    for a, b in ep:
        rr = R_short(c[(c.date >= a) & (c.date <= b)], 1.0)
        ep_signs.append(f"{a}..{b}: n{len(rr)} {rr.mean():+.3f}")
    print(f"{'':>34}  episodes ({len(ep)}): " + " | ".join(ep_signs))
    out[thr] = dict(res=res, yrs=yrs, r1=r1, cell=c)

print("\n=== UNCONDITIONAL CONTROL: ALWAYS-SHORT every eligible pooled IS session, cost x1 ===")
ctrl = stats(R_short(E, 1.0)); show("always-short control x1", ctrl)
show("always-short control x1.5", stats(R_short(E, 1.5)))
show("always-short control x2", stats(R_short(E, 2.0)))
print("\n=== REVERSED minus CONTROL (beta test) ===")
for thr in (65, 70):
    c = out[thr]["cell"]; r1 = out[thr]["r1"]
    comp = E[~(E.sent < thr)]
    rc = R_short(comp, 1.0); rall = R_short(E, 1.0)
    d_full = r1.mean() - rall.mean()
    print(f"thr<{thr}: reversed avgR {r1.mean():+.4f} - control(all) {rall.mean():+.4f} = {d_full:+.4f}; "
          f"Welch t vs ALL control days (overlapping) {welch(r1, rall):+.2f}; "
          f"Welch t vs COMPLEMENT (non-regime days, n {len(rc)}, avgR {rc.mean():+.4f}) {welch(r1, rc):+.2f}")

print("\n=== GRADIENT: threshold ladder, SHORT while sent < thr, pooled IS, cost x1 ===")
for thr in (50, 55, 58, 60, 62, 65, 68, 70, 72, 75, 80, 85, 90, 95, 101):
    c = E[E.sent < thr]
    show(f"short if sent < {thr}", stats(R_short(c, 1.0)))
print("\n--- disjoint bands (short), pooled IS, cost x1 ---")
for lo, hi in ((0, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95), (95, 200)):
    c = E[(E.sent >= lo) & (E.sent < hi)]
    show(f"band [{lo},{hi})", stats(R_short(c, 1.0)))

print("\n=== PLACEBOS (reversed) ===")
show("optimism >=85 SHORT (family diag rev.)", stats(R_short(E[E.sent >= 85], 1.0)))
show("sub-threshold band [70,80) SHORT", stats(R_short(E[(E.sent >= 70) & (E.sent < 80)], 1.0)))
show("band [70,75) SHORT", stats(R_short(E[(E.sent >= 70) & (E.sent < 75)], 1.0)))
# shifted clock: regime signal lagged / led by one release (~21 sessions) per instrument
for shift, lbl in ((21, "regime LAGGED 21 sessions"), (-21, "regime LED 21 sessions (lookahead)")):
    parts = []
    for idx, dd in IS.items():
        m = np.isfinite(dd.prevc) & np.isfinite(dd.atr20) & (dd.atr20 > 0)
        s = dd.copy(); s["sent_sh"] = s.sent.shift(shift)
        s = s[m & np.isfinite(s.sent_sh)]
        parts.append(pd.DataFrame(dict(date=s.index, idx=idx, sent=s.sent_sh.values,
                                       move=(s.c - s.prevc).values, atr=s.atr20.values, cost=MICRO[idx] / 20)))
    P = pd.concat(parts)
    for thr in (65, 70):
        show(f"{lbl}, thr<{thr} SHORT", stats(R_short(P[P.sent < thr], 1.0)))
# monthly-shuffled placebo: random regime blocks of equal size (seeded), 200 draws
rng = np.random.default_rng(72045)
alld = np.array(sorted(E.date.unique()))
for thr in (65, 70):
    nd = len(set(out[thr]["cell"].date))
    sims = []
    for _ in range(200):
        st = rng.integers(0, len(alld) - nd + 1)
        blk = set(alld[st:st + nd])
        rr = R_short(E[E.date.isin(blk)], 1.0)
        sims.append(rr.mean())
    sims = np.array(sims)
    obs = out[thr]["r1"].mean()
    print(f"random contiguous block placebo thr<{thr}: {nd} dates; obs avgR {obs:+.4f}; "
          f"block-placebo mean {sims.mean():+.4f} sd {sims.std():.4f}; share of blocks >= obs {np.mean(sims >= obs):.2f}")

print("\nDONE (IS only; no oos rows used).")
