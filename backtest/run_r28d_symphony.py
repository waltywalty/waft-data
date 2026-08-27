"""Round 28d: the four-stream portfolio ("symphony") on the common window
2020-11 .. 2025-08. Sleeves as daily return series on allocated capital:

  GOLD - deployed 652-trade set, 1% equity risk per trade (risk / stop dist);
         stands in for the dual-denominator pair (the 50/50 split further
         lowers this sleeve's variance - documented, not modeled here).
  D7   - SPX sleeve fully invested during a Double Seven position, else cash;
         CFD cost at entry+exit days.
  MHI  - HSI pre-open fade, 1% risk per trade (risk = |entry - stop|);
         data begins 2022-02, sleeve is cash before that. WATCH ITEM (n=43).

Portfolios are daily-rebalanced weighted sums of sleeve returns, compounded.
The "optimal" split is an IN-SAMPLE max-Sharpe grid (5% steps) - shown for
illustration, never a promise. "Always-invested" = 100% S&P buy-and-hold base
PLUS the optimal strategy mix as a margin overlay (near-100%+ exposure).
"""
import pandas as pd, numpy as np, json, warnings, engine, index_data
warnings.filterwarnings("ignore")

START, END = pd.Timestamp("2020-11-10"), pd.Timestamp("2025-08-01")

# ---------------------------------------------------------------- GOLD sleeve
g = pd.read_pickle("results/trades_deployable.pkl")
g["ret"] = 0.01 * g.pnl_oz / g.stop_dist
g["day"] = pd.to_datetime(g.t_out.dt.date)
gold_daily = g.groupby("day").ret.sum()

# ---------------------------------------------------------------- D7 sleeve
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
        pos = True            # enter at close: earns from next day
        continue
    if pos:
        inpos.iloc[i] = True
        if c.iloc[i] >= high7.iloc[i]:
            pos = False
spx_ret = c.pct_change().fillna(0)
d7_daily = spx_ret.where(inpos, 0.0)
exit_days = inpos & ~inpos.shift(-1).fillna(False)
d7_daily[exit_days] -= 0.6 / c[exit_days]          # round-trip cost at exit

# ---------------------------------------------------------------- MHI sleeve
a = pd.read_csv("data/HK50_PT15M_yuan.csv")
a["ts"] = pd.to_datetime(a.time, utc=True)
a = a.set_index("ts")[["open", "high", "low", "close"]].sort_index()
b = pd.read_csv("data/HK33_M15.csv")
b["ts"] = pd.to_datetime(b.iloc[:, 0], utc=True)
b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()
H = pd.concat([a[a.index < b.index.min()], b]).sort_index()
H = H[~H.index.duplicated()]
H["d"] = H.index.date
H["hm"] = H.index.hour * 100 + H.index.minute
drng = H.groupby("d").high.max() - H.groupby("d").low.min()
atr14 = drng.rolling(14).mean().shift(1)
mhi_rows = []
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
    rng_ = pre.high.iloc[0] - pre.lo if False else pre.high.iloc[0] - pre.low.iloc[0]
    stop = (pre.high.iloc[0] + 0.5 * rng_) if sgn < 0 else (pre.low.iloc[0] - 0.5 * rng_)
    px = None
    for _, bb in sess.iterrows():
        if (sgn < 0 and bb.high >= stop) or (sgn > 0 and bb.low <= stop):
            px = stop; break
    if px is None:
        px = sess.close.iloc[-1]
    pnl = sgn * (px - e) - 10.0
    risk = abs(e - stop)
    mhi_rows.append(dict(day=pd.Timestamp(d), ret=0.01 * pnl / max(risk, 1.0)))
mhi = pd.DataFrame(mhi_rows).set_index("day").ret
print(f"MHI regenerated: {len(mhi)} trades {mhi.index.min().date()}..{mhi.index.max().date()}")

# ---------------------------------------------------------------- common frame
idx = pd.date_range(START, END, freq="D")
F = pd.DataFrame(index=idx)
F["gold"] = gold_daily.reindex(idx).fillna(0.0)
F["d7"] = d7_daily.reindex(idx).fillna(0.0)
F["mhi"] = mhi.reindex(idx).fillna(0.0)
F["spx"] = spx_ret.reindex(idx).fillna(0.0)
F = F[F.index.dayofweek < 5]

def stats(r, label):
    eq = (1 + r).cumprod()
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = ((eq.cummax() - eq) / eq.cummax()).max()
    x = r[r != 0] if (r != 0).sum() > 50 else r
    vol = r.std() * np.sqrt(252)
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    return dict(label=label, final=float(eq.iloc[-1]), cagr=float(cagr),
                max_dd=float(dd), vol=float(vol), sharpe=float(sharpe),
                mar=float(cagr / dd) if dd > 0 else np.nan), eq

# in-sample max-Sharpe grid over (gold, d7, mhi), 5% steps, sum = 1
best = None
for wg in np.arange(0, 1.01, 0.05):
    for wd in np.arange(0, 1.01 - wg + 1e-9, 0.05):
        wm = 1 - wg - wd
        if wm < -1e-9 or wm > 0.25 + 1e-9:      # cap the n=43 watch item at 25%
            continue
        r = wg * F.gold + wd * F.d7 + max(wm, 0) * F.mhi
        s = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else -9
        if best is None or s > best[0]:
            best = (s, round(wg, 2), round(wd, 2), round(max(wm, 0), 2))
_, WG, WD, WM = best
r_opt = WG * F.gold + WD * F.d7 + WM * F.mhi
r_alw = F.spx + r_opt                              # 100% B&H base + overlay

out = {"weights_opt": {"gold": WG, "d7": WD, "mhi": WM},
       "note": "weights are IN-SAMPLE max-Sharpe on 2020-11..2025-08; MHI capped at 25% (n=43 watch item)"}
curves = {}
for key, r, lbl in (("opt", r_opt, f"optimal mix {int(WG*100)}/{int(WD*100)}/{int(WM*100)}"),
                    ("opt2x", 2 * r_opt, "optimal mix, 2x levered"),
                    ("always", r_alw, "always-invested (B&H + mix overlay)"),
                    ("gold100", F.gold, "100% gold strategy"),
                    ("d7100", F.d7, "100% Double Seven"),
                    ("spx", F.spx, "S&P buy & hold")):
    st, eq = stats(r, lbl)
    out[key] = st
    w = eq.resample("W").last().dropna()
    curves[key] = [round(float(v), 4) for v in w]
    curves.setdefault("dates", [str(x.date()) for x in w.index])
out["curves"] = curves
cm = F[["gold", "d7", "mhi"]].corr().round(3)
out["sleeve_corr"] = cm.to_dict()
json.dump(out, open("results/r28d_symphony.json", "w"), indent=1, default=float)

print(f"\noptimal in-sample weights: gold {WG*100:.0f}% / D7 {WD*100:.0f}% / MHI {WM*100:.0f}%")
print(f"{'portfolio':>34} {'final':>7} {'CAGR':>7} {'maxDD':>7} {'vol':>6} {'Sharpe':>7} {'MAR':>6}")
for key in ("opt", "opt2x", "always", "gold100", "d7100", "spx"):
    s = out[key]
    print(f"{s['label']:>34} {s['final']:>6.2f}x {s['cagr']*100:>+6.1f}% {s['max_dd']*100:>6.1f}% "
          f"{s['vol']*100:>5.1f}% {s['sharpe']:>7.2f} {s['mar']:>6.2f}")
print("\nsleeve daily-return correlations:")
print(cm)
