"""R72A step-3 reversed scoring, attempt 40 (r58_funding). IS ONLY.
Copies run_r58_funding.py data build; filters to k < cut (never touches OOS rows).
Reversed cell = LONG BTC on >= 90th pct funding (hi_short x -1), holds 1 and 3."""
import pandas as pd, numpy as np, warnings
from scipy import stats as st
warnings.filterwarnings("ignore")
COST_BPS = 5.0   # runner's cost, 5 bps RT

fr_lines = [l for l in open("data/BTC_funding_binance.csv").read().splitlines()
            if l and not l.startswith("calc_time")]
fr = pd.DataFrame([l.split(",") for l in fr_lines], columns=["t", "iv", "r"])
fr["t"] = pd.to_datetime(pd.to_numeric(fr.t), unit="ms"); fr["r"] = pd.to_numeric(fr.r)
daily_f = fr.groupby(fr.t.dt.date).r.sum()
pct = daily_f.rolling(252).rank(pct=True).shift(0)
d = pd.read_csv("data/BTCUSD_daily_av.csv", parse_dates=["timestamp"]).set_index("timestamp").sort_index()
c = d.close; ret = np.log(c).diff(); sig63 = ret.rolling(63).std().shift(1)
kpos = {k.date(): i for i, k in enumerate(c.index)}
joined = [k for k in daily_f.index if k in kpos and np.isfinite(pct.get(k, np.nan))]
cut = joined[int(len(joined) * 0.75)]
print(f"IS CUT DATE (runner rule keys[int(0.75*n)]): {cut}  -> using signal days strictly < cut")
IS_DAYS = [k for k in joined if k < cut]
print(f"IS signal days: {len(IS_DAYS)}  {IS_DAYS[0]}..{IS_DAYS[-1]}")

def run(lo, hi, side, hold, days=IS_DAYS, sig_shift=0):
    """side=+1 long, -1 short. Returns gross bps, sigma, date. sig_shift lags the signal by N days (placebo)."""
    rows = []; busy = -1
    for j, k in enumerate(days):
        kk = days[j - sig_shift] if sig_shift and j - sig_shift >= 0 else (k if not sig_shift else None)
        if kk is None: continue
        p = pct[kk]
        if not (lo <= p <= hi): continue
        i = kpos[k]
        if i <= busy or i + hold >= len(c): continue
        if c.index[i + hold].date() >= cut and sig_shift == 0 and False: pass
        s = sig63.iloc[i]
        if not np.isfinite(s) or s <= 0: continue
        fwd = np.log(c.iloc[i + hold] / c.iloc[i])
        rows.append((k, side * fwd * 1e4, s)); busy = i + hold
    df = pd.DataFrame(rows, columns=["date", "gross", "sig"])
    return df

def R(df, hold, mult):  # normalized R after cost x mult
    return (df.gross - mult * COST_BPS) / (df.sig * np.sqrt(hold) * 1e4)

def summ(df, hold, mult=1.0):
    r = R(df, hold, mult).values; p = (df.gross - mult * COST_BPS).values
    if len(r) < 2: return dict(n=len(r))
    m = len(r) // 2
    w, ls = p[p > 0], p[p <= 0]
    return dict(n=len(r), avgR=r.mean(), avg_bps=p.mean(), t=r.mean() / r.std(ddof=1) * np.sqrt(len(r)),
                wr=(p > 0).mean(), pf=(w.sum() / abs(ls.sum())) if len(ls) else np.inf,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

def show(label, df, hold):
    a, b, cc = summ(df, hold, 1.0), summ(df, hold, 1.5), summ(df, hold, 2.0)
    print(f"{label:>34} n {a['n']:>4} | x1 avgR {a['avgR']:+.4f} ({a['avg_bps']:+.1f}bps) t {a['t']:+.2f} WR {a['wr']*100:.1f}% PF {a['pf']:.2f} halves {a['halves']}"
          f" | x1.5 avgR {b['avgR']:+.4f} | x2 avgR {cc['avgR']:+.4f} t {cc['t']:+.2f}")
    return a, b, cc

print("\n=== REGISTERED cells (IS, net 1x) - sanity vs JSON ===")
for hold in (1, 3):
    show(f"hi_short/{hold}d (registered)", run(0.9, 1.01, -1, hold), hold)
show("lo_long/1d (registered)", run(-0.01, 0.1, +1, 1), 1)

print("\n=== REVERSED cell: hi_LONG (LONG BTC on funding >= 90th pct) ===")
rev = {}
for hold in (1, 3):
    df = run(0.9, 1.01, +1, hold)
    rev[hold] = (df,) + show(f"REV hi_long/{hold}d", df, hold)
    yr = df.assign(r=R(df, hold, 1.0)).groupby(pd.to_datetime(df.date).dt.year).r.agg(["count", "mean"])
    print(f"      per-year (x1 net, avgR): " + "  ".join(f"{y}:{'+' if m>0 else '-'}(n{int(n)},{m:+.3f})" for y, (n, m) in yr.iterrows()))

print("\n=== UNCONDITIONAL CONTROL: always-LONG every eligible IS day, same window (close->close), 1x cost ===")
ctrl = {}
for hold in (1, 3):
    dfc = run(-1.0, 2.0, +1, hold)  # every eligible day, non-overlapping same busy rule
    ctrl[hold] = (dfc,) + show(f"CTRL always-long/{hold}d", dfc, hold)
    # also one-position-at-a-time for hold 3 means every 3rd day; add overlapping version
    if hold == 3:
        rows = []
        for k in IS_DAYS:
            i = kpos[k]
            if i + hold >= len(c): continue
            s = sig63.iloc[i]
            if not np.isfinite(s) or s <= 0: continue
            rows.append((k, np.log(c.iloc[i + hold] / c.iloc[i]) * 1e4, s))
        dfo = pd.DataFrame(rows, columns=["date", "gross", "sig"])
        show("CTRL always-long/3d (overlapping)", dfo, hold)

print("\n=== DIFFERENCE reversed - control (Welch t on the two R samples at 1x; cell days are a subset of control days) ===")
diff = {}
for hold in (1, 3):
    rc = R(rev[hold][0], hold, 1.0); rk = R(ctrl[hold][0], hold, 1.0)
    tW, pW = st.ttest_ind(rc, rk, equal_var=False)
    # complement version: cell vs control days NOT in the cell (cleaner, independent samples)
    celld = set(rev[hold][0].date); comp = ctrl[hold][0][~ctrl[hold][0].date.isin(celld)]
    rk2 = R(comp, hold, 1.0); tW2, _ = st.ttest_ind(rc, rk2, equal_var=False)
    diff[hold] = dict(avgR=rc.mean() - rk.mean(), t=tW, avgR_comp=rc.mean() - rk2.mean(), t_comp=tW2)
    print(f"hold {hold}d: cell avgR {rc.mean():+.4f} (n{len(rc)}) - ctrl avgR {rk.mean():+.4f} (n{len(rk)}) = {rc.mean()-rk.mean():+.4f}, Welch t {tW:+.2f} (p {pW:.3f})"
          f" | vs complement days (n{len(rk2)}): diff {rc.mean()-rk2.mean():+.4f}, Welch t {tW2:+.2f}")

print("\n=== GRADIENT: threshold ladder, LONG on funding pct >= X, hold 1d (net 1x) ===")
for lo in (0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.975):
    df = run(lo, 1.01, +1, 1); a = summ(df, 1, 1.0)
    print(f"  pct >= {lo:.3f}: n {a['n']:>4} avgR {a['avgR']:+.4f} ({a['avg_bps']:+.1f}bps) t {a['t']:+.2f} halves {a['halves']}")
print("--- decile bands, LONG hold 1d (net 1x) ---")
for lo in np.arange(0.0, 1.0, 0.1):
    df = run(lo, lo + 0.1 if lo < 0.89 else 1.01, +1, 1); a = summ(df, 1, 1.0)
    print(f"  band [{lo:.1f},{lo+0.1:.1f}): n {a['n']:>4} avgR {a['avgR']:+.4f} ({a['avg_bps']:+.1f}bps) t {a['t']:+.2f}")
print("--- hold 3d ladder ---")
for lo in (0.0, 0.6, 0.8, 0.9, 0.95):
    df = run(lo, 1.01, +1, 3); a = summ(df, 3, 1.0)
    print(f"  pct >= {lo:.3f}: n {a['n']:>4} avgR {a['avgR']:+.4f} ({a['avg_bps']:+.1f}bps) t {a['t']:+.2f} halves {a['halves']}")

print("\n=== PLACEBO ===")
print("(a) family's sub-threshold diagnostic band reversed: LONG on 60-80th pct")
for hold in (1, 3):
    show(f"mid band 60-80 LONG/{hold}d", run(0.6, 0.8, +1, hold), hold)
print("(b) stale-signal placebo: same >=90th rule, LONG, signal lagged 5 / 10 IS days")
for lag in (5, 10):
    show(f"hi_long/1d, signal lag {lag}d", run(0.9, 1.01, +1, 1, sig_shift=lag), 1)
print("(c) mirror placebo: SHORT on <=10th pct (reverse of lo_long), 1d")
show("lo_SHORT/1d", run(-0.01, 0.1, -1, 1), 1)
