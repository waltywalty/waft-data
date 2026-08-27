"""Round 25: the correlation-timescale battery. Pre-registered in the goal
ledger before this file ran.

A. Intraday-frequency gold/AUD correlation as a gate replacement.
B. Adjunct terciles inside the deployed daily gate.
C. Daily corr window x entry-timeframe cross grid.
"""
import pandas as pd, numpy as np, json, warnings, engine, trades, audusd
warnings.filterwarnings("ignore")
rng = np.random.default_rng(25)

gold = engine.load_bars()

# ---------------------------------------------------------------- AUD 15m, extended with the collector
a15 = audusd.build()
col = pd.read_csv("data/AUDUSD_M15_collector.csv", parse_dates=["datetime"]).set_index("datetime").sort_index()
col = col[["open", "high", "low", "close"]]
a15 = pd.concat([a15, col[col.index > a15.index.max()]]).sort_index()
a15 = a15[~a15.index.duplicated()]
print(f"AUD 15m: {a15.index.min().date()} .. {a15.index.max().date()}; "
      f"hole 2022-03..2024-04 as documented")

# ---------------------------------------------------------------- intraday corr sensors
g15 = gold.close.resample("15min").last().dropna()
a15c = a15.close

def sensor(tf, win):
    """Rolling corr of tf-bar log returns, value at each bar close."""
    g = g15.resample(tf).last().dropna() if tf != "15min" else g15
    a = a15c.resample(tf).last().dropna() if tf != "15min" else a15c
    j = pd.concat([np.log(g).diff().rename("g"), np.log(a).diff().rename("a")],
                  axis=1, join="inner").dropna()
    return j.g.rolling(win).corr(j.a)

SENSORS = {
    "H1_24":  sensor("1h", 24),   "H1_48":  sensor("1h", 48),
    "H1_120": sensor("1h", 120),  "H1_240": sensor("1h", 240),
    "M15_96": sensor("15min", 96), "M15_480": sensor("15min", 480),
}

# ---------------------------------------------------------------- base trade set (60m, deployed construction)
t60 = trades.generate(gold, 60, stop_r=2.0, entry_cutoff_ldn=8)
t60["pnl_oz"] = t60.pnl_oz - np.where(t60.reason == "stop", 0.30, 0.0)
t60["pct"] = t60.pnl_oz / t60.entry * 100
t60["day_ts"] = pd.to_datetime(t60.day)

# deployed daily corr (round-3 construction, as in thresholds.py)
cdaily = trades.corr_series(gold, 20)
t60["cd"] = t60.day_ts.map(cdaily)

# per-day sensor value at the last bar closed strictly before 01:30 UTC
def day_values(s):
    out = {}
    ss = s.dropna()
    for d in t60.day_ts.unique():
        cutoff = pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=1, minutes=25)
        i = ss.index.searchsorted(cutoff)
        if i > 0:
            v_ts = ss.index[i - 1]
            # stale guard: sensor value must be from within the last 3 days
            if cutoff - v_ts < pd.Timedelta(days=3):
                out[d] = float(ss.iloc[i - 1])
    return out

DV = {k: day_values(s) for k, s in SENSORS.items()}
for k in DV:
    t60[k] = t60.day_ts.map(DV[k])

# segments = the two AUD-coverage eras (the hole is excluded by NaN mapping)
SEG1 = t60.day_ts < "2022-03-01"
SEG2 = t60.day_ts >= "2024-04-01"
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def two_sample_t(a, b):
    if len(a) < 8 or len(b) < 8:
        return np.nan
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float((a.mean() - b.mean()) / np.sqrt(va + vb))

def cell(mask_avail, keep):
    """keep vs excluded among trades where the sensor exists."""
    a, b = t60[mask_avail & keep], t60[mask_avail & ~keep]
    d = dict(n=int(len(a)), n_ex=int(len(b)),
             pf=pf(a.pnl_oz) if len(a) > 7 else np.nan,
             exp=float(a.pnl_oz.mean()) if len(a) else np.nan,
             t2=two_sample_t(a.pct, b.pct))
    for nm, seg in (("s1", SEG1), ("s2", SEG2)):
        x, y = t60[mask_avail & keep & seg], t60[mask_avail & ~keep & seg]
        d[nm] = dict(n=int(len(x)), pf=pf(x.pnl_oz) if len(x) > 7 else np.nan,
                     t2=two_sample_t(x.pct, y.pct))
    return d

out = {"coverage": {k: int(t60[k].notna().sum()) for k in SENSORS}}

# ---------------- A: replacement gates, 6 sensors x thresholds {0.3, 0.5, 0.7}
A = {}
for k in SENSORS:
    avail = t60[k].notna()
    for th in (0.3, 0.5, 0.7):
        A[f"{k}_le{th}"] = cell(avail, t60[k] <= th)
out["A_replacement"] = A

# deployed daily gate scored on the SAME available days, for the registered bar
DEP = {}
for k in SENSORS:
    avail = t60[k].notna() & t60.cd.notna()
    DEP[k] = cell(avail, t60.cd <= 0.5)
out["deployed_on_same_days"] = DEP

# ---------------- B: adjunct terciles inside the deployed gate
from scipy.stats import spearmanr
B = {}
for k in SENSORS:
    sub = t60[(t60.cd <= 0.5) & t60[k].notna()]
    if len(sub) < 60:
        B[k] = dict(n=len(sub), note="too few"); continue
    terc = pd.qcut(sub[k], 3, labels=False, duplicates="drop")
    rho, p = spearmanr(sub[k], sub.pct)
    B[k] = dict(n=int(len(sub)), rho=float(rho), p=float(p),
                terc_pf=[pf(sub[terc == i].pnl_oz) for i in range(3)],
                terc_exp=[float(sub[terc == i].pnl_oz.mean()) for i in range(3)])
out["B_adjunct"] = B

# ---------------- C: daily window x entry-timeframe cross (threshold 0.5)
C = {}
tsets = {60: t60}
for L in (30, 90):
    tt = trades.generate(gold, L, stop_r=2.0, entry_cutoff_ldn=8)
    tt["pnl_oz"] = tt.pnl_oz - np.where(tt.reason == "stop", 0.30, 0.0)
    tt["pct"] = tt.pnl_oz / tt.entry * 100
    tt["day_ts"] = pd.to_datetime(tt.day)
    tsets[L] = tt
for w in (10, 20, 40):
    cw = trades.corr_series(gold, w)
    for L, tt in tsets.items():
        cc = tt.day_ts.map(cw)
        x = tt[cc <= 0.5]
        p = x.pct
        C[f"w{w}_L{L}"] = dict(n=int(len(x)), pf=pf(x.pnl_oz),
                               exp=float(x.pnl_oz.mean()),
                               t=float(p.mean() / p.std() * np.sqrt(len(p))))
out["C_cross"] = C

# ---------------- max-stat over the 18 A cells (shared circular day-shift)
days = sorted(t60.day_ts.unique())
day_ix = {d: i for i, d in enumerate(days)}
nd = len(days)
sens_arr = {k: np.array([DV[k].get(d, np.nan) for d in days]) for k in SENSORS}
trade_day = t60.day_ts.map(day_ix).values
pct_v = t60.pct.values

def max_t(arrs):
    best = 0.0
    for k, arr in arrs.items():
        v = arr[trade_day]
        avail = ~np.isnan(v)
        for th in (0.3, 0.5, 0.7):
            keep = avail & (v <= th)
            excl = avail & ~(v <= th)
            if keep.sum() < 8 or excl.sum() < 8:
                continue
            a, b = pct_v[keep], pct_v[excl]
            t2 = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
            best = max(best, abs(t2))
    return best

obs = max_t(sens_arr)
NPERM = 500
perm = np.empty(NPERM)
for i in range(NPERM):
    sh = rng.integers(20, nd - 20)
    perm[i] = max_t({k: np.roll(a, sh) for k, a in sens_arr.items()})
out["maxstat"] = dict(observed=float(obs), p=float((perm >= obs).mean()),
                      n_cells=18, n_perm=NPERM)

json.dump(out, open("results/r25_corrtf.json", "w"), indent=1)

# ---------------------------------------------------------------- print
print("\n=== A: INTRADAY-CORR REPLACEMENT GATES (kept-vs-excluded two-sample t) ===")
print(f"{'cell':>14} {'n':>5} {'PF':>7} {'exp$':>7} {'t2':>6} | s1 t2  s2 t2   (deployed gate on same days)")
for k in SENSORS:
    dep = DEP[k]
    for th in (0.3, 0.5, 0.7):
        c = A[f"{k}_le{th}"]
        print(f"{k+'<='+str(th):>14} {c['n']:>5} {c['pf'] if c['pf']==c['pf'] else 0:>7.3f} "
              f"{c['exp']:>7.2f} {c['t2'] if c['t2']==c['t2'] else 0:>6.2f} | "
              f"{c['s1']['t2'] if c['s1']['t2']==c['s1']['t2'] else 0:>5.2f} "
              f"{c['s2']['t2'] if c['s2']['t2']==c['s2']['t2'] else 0:>5.2f}"
              + (f"   [dep: PF {dep['pf']:.3f} t2 {dep['t2']:+.2f}]" if th == 0.3 else ""))
print("\n=== B: ADJUNCT TERCILES INSIDE THE DEPLOYED GATE (spearman rho, PF low->high corr) ===")
for k, b in out["B_adjunct"].items():
    if "rho" in b:
        print(f"{k:>9}: n={b['n']:>4} rho {b['rho']:+.3f} (p {b['p']:.2f})  "
              f"PF {b['terc_pf'][0]:.2f} / {b['terc_pf'][1]:.2f} / {b['terc_pf'][2]:.2f}")
print("\n=== C: DAILY WINDOW x ENTRY TIMEFRAME (PF / t, corr<=0.5) ===")
for w in (10, 20, 40):
    row = "  ".join(f"L{L}m: {C[f'w{w}_L{L}']['pf']:.3f}/{C[f'w{w}_L{L}']['t']:+.2f}"
                    for L in (30, 60, 90))
    print(f"  w={w:>2}d: {row}")
print(f"\nmax-stat over 18 A-cells: observed |t2| {obs:.2f}, p = {out['maxstat']['p']:.3f}")
