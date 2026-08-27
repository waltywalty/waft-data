"""Round 28e: the weight-space map for the symphony. Not a search for a
better split - a measurement of how much any split can be trusted.
1) full simplex at 1% steps, multiple objectives;
2) the Sharpe plateau (how flat is the surface near the top);
3) stability: re-optimized weights per calendar year + block bootstrap.
Reuses the sleeve series construction from run_r28d_symphony (inlined).
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")
rng = np.random.default_rng(28)

START, END = pd.Timestamp("2020-11-10"), pd.Timestamp("2025-08-01")

# ---- sleeves (same construction as r28d) ----
g = pd.read_pickle("results/trades_deployable.pkl")
g["ret"] = 0.01 * g.pnl_oz / g.stop_dist
g["day"] = pd.to_datetime(g.t_out.dt.date)
gold_daily = g.groupby("day").ret.sum()

spxb = index_data.load("SPX")
spxd = spxb.resample("1D").agg(open=("open", "first"), close=("close", "last")).dropna()
spxd.index = spxd.index.tz_localize(None)
c = spxd.close
sma200 = c.rolling(200).mean()
low7, high7 = c.rolling(7).min(), c.rolling(7).max()
inpos = pd.Series(False, index=spxd.index)
pos = False
for i in range(200, len(spxd)):
    if not pos and c.iloc[i] > sma200.iloc[i] and c.iloc[i] <= low7.iloc[i]:
        pos = True; continue
    if pos:
        inpos.iloc[i] = True
        if c.iloc[i] >= high7.iloc[i]:
            pos = False
spx_ret = c.pct_change().fillna(0)
d7_daily = spx_ret.where(inpos, 0.0)
exit_days = inpos & ~inpos.shift(-1).fillna(False)
d7_daily[exit_days] -= 0.6 / c[exit_days]

a = pd.read_csv("data/HK50_PT15M_yuan.csv")
a["ts"] = pd.to_datetime(a.time, utc=True)
a = a.set_index("ts")[["open", "high", "low", "close"]].sort_index()
b = pd.read_csv("data/HK33_M15.csv")
b["ts"] = pd.to_datetime(b.iloc[:, 0], utc=True)
b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()
H = pd.concat([a[a.index < b.index.min()], b]).sort_index()
H = H[~H.index.duplicated()]
H["d"] = H.index.date; H["hm"] = H.index.hour * 100 + H.index.minute
drng = H.groupby("d").high.max() - H.groupby("d").low.min()
atr14 = drng.rolling(14).mean().shift(1)
rows = []
for d, day in H.groupby("d"):
    pre = day[day.hm == 115]
    if not len(pre) or d not in atr14 or not np.isfinite(atr14[d]):
        continue
    sess = day[(day.hm >= 130) & (day.hm < 800)]
    if len(sess) < 15:
        continue
    push = pre.close.iloc[0] - pre.open.iloc[0]
    if abs(push / atr14[d]) < 0.3:
        continue
    sgn = -np.sign(push)
    e = sess.open.iloc[0]
    rng_ = pre.high.iloc[0] - pre.low.iloc[0]
    stop = (pre.high.iloc[0] + 0.5 * rng_) if sgn < 0 else (pre.low.iloc[0] - 0.5 * rng_)
    px = None
    for _, bb in sess.iterrows():
        if (sgn < 0 and bb.high >= stop) or (sgn > 0 and bb.low <= stop):
            px = stop; break
    if px is None:
        px = sess.close.iloc[-1]
    rows.append(dict(day=pd.Timestamp(d), ret=0.01 * (sgn * (px - e) - 10.0) / max(abs(e - stop), 1.0)))
mhi = pd.DataFrame(rows).set_index("day").ret

idx = pd.date_range(START, END, freq="D")
F = pd.DataFrame(index=idx)
F["gold"] = gold_daily.reindex(idx).fillna(0.0)
F["d7"] = d7_daily.reindex(idx).fillna(0.0)
F["mhi"] = mhi.reindex(idx).fillna(0.0)
F = F[F.index.dayofweek < 5]
R = F[["gold", "d7", "mhi"]].values

def metrics(r):
    eq = np.cumprod(1 + r)
    yrs = len(r) / 261
    cagr = eq[-1] ** (1 / yrs) - 1
    peak = np.maximum.accumulate(eq)
    dd = ((peak - eq) / peak).max()
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    return cagr, dd, sharpe, (cagr / dd if dd > 0 else np.nan)

# ---- 1. full simplex, 1% steps, several objectives ----
grid = []
for wg in range(0, 101):
    for wd in range(0, 101 - wg):
        wm = 100 - wg - wd
        r = (wg * R[:, 0] + wd * R[:, 1] + wm * R[:, 2]) / 100
        cagr, dd, sh, mar = metrics(r)
        grid.append((wg, wd, wm, cagr, dd, sh, mar))
G = pd.DataFrame(grid, columns=["wg", "wd", "wm", "cagr", "dd", "sharpe", "mar"])

best_sh = G.loc[G.sharpe.idxmax()]
best_sh_cap = G[G.wm <= 25].loc[G[G.wm <= 25].sharpe.idxmax()]
best_mar = G.loc[G.mar.idxmax()]
best_mar_cap = G[G.wm <= 25].loc[G[G.wm <= 25].mar.idxmax()]
# plateau: how many splits sit within 5% of the peak Sharpe
top = G[G.sharpe >= G.sharpe.max() * 0.95]
top_cap = G[(G.wm <= 25) & (G.sharpe >= best_sh_cap.sharpe * 0.95)]
# reference splits
def at(wg, wd, wm):
    r = (wg * R[:, 0] + wd * R[:, 1] + wm * R[:, 2]) / 100
    return metrics(r)
refs = {"equal 33/33/33": at(34, 33, 33), "risk parity-ish": None}
iv = 1 / F[["gold", "d7", "mhi"]].std()
w_rp = (iv / iv.sum() * 100).round().astype(int)
refs["risk parity-ish"] = at(*w_rp.tolist())
refs[f"rp weights"] = tuple(w_rp.tolist()) + (0,)

# ---- 2. stability: per-calendar-year re-optimization (MHI capped) ----
yearly = {}
for yr, sub in F.groupby(F.index.year):
    if len(sub) < 120:
        continue
    Rv = sub[["gold", "d7", "mhi"]].values
    bb = None
    for wg in range(0, 101, 5):
        for wd in range(0, 101 - wg, 5):
            wm = 100 - wg - wd
            if wm > 25:
                continue
            r = (wg * Rv[:, 0] + wd * Rv[:, 1] + wm * Rv[:, 2]) / 100
            s = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else -9
            if bb is None or s > bb[0]:
                bb = (s, wg, wd, wm)
    yearly[str(yr)] = dict(sharpe=round(bb[0], 2), gold=bb[1], d7=bb[2], mhi=bb[3])

# ---- 3. block bootstrap (3-month blocks) of the capped optimum ----
n = len(F)
block = 63
boots = []
for _ in range(400):
    starts = rng.integers(0, n - block, size=n // block + 1)
    take = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
    Rv = R[take]
    bb = None
    for wg in range(0, 101, 5):
        for wd in range(0, 101 - wg, 5):
            wm = 100 - wg - wd
            if wm > 25:
                continue
            r = (wg * Rv[:, 0] + wd * Rv[:, 1] + wm * Rv[:, 2]) / 100
            s = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else -9
            if bb is None or s > bb[0]:
                bb = (s, wg, wd, wm)
    boots.append(bb[1:])
B = pd.DataFrame(boots, columns=["gold", "d7", "mhi"])

out = dict(
    best_sharpe=dict(w=[int(best_sh.wg), int(best_sh.wd), int(best_sh.wm)],
                     sharpe=float(best_sh.sharpe), cagr=float(best_sh.cagr), dd=float(best_sh.dd)),
    best_sharpe_capped=dict(w=[int(best_sh_cap.wg), int(best_sh_cap.wd), int(best_sh_cap.wm)],
                            sharpe=float(best_sh_cap.sharpe), cagr=float(best_sh_cap.cagr), dd=float(best_sh_cap.dd)),
    best_mar=dict(w=[int(best_mar.wg), int(best_mar.wd), int(best_mar.wm)],
                  mar=float(best_mar.mar), cagr=float(best_mar.cagr), dd=float(best_mar.dd)),
    best_mar_capped=dict(w=[int(best_mar_cap.wg), int(best_mar_cap.wd), int(best_mar_cap.wm)],
                         mar=float(best_mar_cap.mar), cagr=float(best_mar_cap.cagr), dd=float(best_mar_cap.dd)),
    plateau=dict(n_within_5pct=int(len(top)), n_total=len(G),
                 wg_range=[int(top.wg.min()), int(top.wg.max())],
                 wd_range=[int(top.wd.min()), int(top.wd.max())],
                 wm_range=[int(top.wm.min()), int(top.wm.max())],
                 capped_n=int(len(top_cap))),
    equal_weight=dict(cagr=refs["equal 33/33/33"][0], dd=refs["equal 33/33/33"][1],
                      sharpe=refs["equal 33/33/33"][2]),
    risk_parity=dict(w=[int(x) for x in w_rp.tolist()], cagr=refs["risk parity-ish"][0],
                     dd=refs["risk parity-ish"][1], sharpe=refs["risk parity-ish"][2]),
    yearly_reopt=yearly,
    bootstrap=dict(gold=[int(B.gold.quantile(q)) for q in (0.1, 0.5, 0.9)],
                   d7=[int(B.d7.quantile(q)) for q in (0.1, 0.5, 0.9)],
                   mhi=[int(B.mhi.quantile(q)) for q in (0.1, 0.5, 0.9)]),
)
json.dump(out, open("results/r28e_splits.json", "w"), indent=1, default=float)

print(f"grid: {len(G)} splits (1% steps, full simplex)")
print(f"best Sharpe uncapped : {out['best_sharpe']['w']}  Sharpe {out['best_sharpe']['sharpe']:.2f}  "
      f"CAGR {out['best_sharpe']['cagr']*100:+.1f}%  DD {out['best_sharpe']['dd']*100:.1f}%")
print(f"best Sharpe (MHI<=25): {out['best_sharpe_capped']['w']}  Sharpe {out['best_sharpe_capped']['sharpe']:.2f}")
print(f"best MAR uncapped    : {out['best_mar']['w']}  MAR {out['best_mar']['mar']:.2f}  "
      f"CAGR {out['best_mar']['cagr']*100:+.1f}%  DD {out['best_mar']['dd']*100:.1f}%")
print(f"best MAR (MHI<=25)   : {out['best_mar_capped']['w']}  MAR {out['best_mar_capped']['mar']:.2f}")
print(f"plateau: {len(top)} of {len(G)} splits within 5% of peak Sharpe "
      f"(gold {out['plateau']['wg_range']}, d7 {out['plateau']['wd_range']}, mhi {out['plateau']['wm_range']})")
print(f"equal weight 33/33/33: Sharpe {out['equal_weight']['sharpe']:.2f}  "
      f"CAGR {out['equal_weight']['cagr']*100:+.1f}%  DD {out['equal_weight']['dd']*100:.1f}%")
print(f"risk parity {out['risk_parity']['w']}: Sharpe {out['risk_parity']['sharpe']:.2f}")
print("\nper-year re-optimized weights (gold/d7/mhi):")
for yr, v in yearly.items():
    print(f"  {yr}: {v['gold']}/{v['d7']}/{v['mhi']}  (Sharpe {v['sharpe']})")
print(f"\nbootstrap optimal-weight ranges (10th/50th/90th pctile over 400 resamples):")
print(f"  gold {out['bootstrap']['gold']}  d7 {out['bootstrap']['d7']}  mhi {out['bootstrap']['mhi']}")
