"""Round 36: fixed 10-point TP x stop sweep on the live/paper strategies.
Frozen per pre-registration in reference/goal_ledger.md. Entries unchanged;
exits replaced by TP +10 pts, SL in {5, 10, 20, none}, each system's time/
signal exit as backstop. Worst-case intrabar ordering (SL before TP when
both touch in one bar). Outputs results/r36_brackets.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

TP = 10.0
SLS = [5.0, 10.0, 20.0, None]


def walk(o, h, l, c, side, entry, sl_px, tp_px):
    """Walk bars after entry; return exit price + reason. Worst-case: SL first."""
    for k in range(len(c)):
        if side > 0:
            if sl_px is not None and l[k] <= sl_px:
                return sl_px, "SL"
            if h[k] >= tp_px:
                return tp_px, "TP"
        else:
            if sl_px is not None and h[k] >= sl_px:
                return sl_px, "SL"
            if l[k] <= tp_px:
                return tp_px, "TP"
    return c[-1], "time"


def score(pnls):
    p = np.asarray(pnls, float)
    w, l = p[p > 0], p[p <= 0]
    pf = w.sum() / abs(l.sum()) if len(l) and l.sum() < 0 else np.inf
    return dict(n=int(len(p)), wr=float((p > 0).mean()), pf=float(pf),
                avg=float(p.mean()), total=float(p.sum()), worst=float(p.min()))


out = {}

# ------------------------------- GOLD ------------------------------------------
g5 = pd.read_csv("data/XAUUSD_5m.csv")
g5["ts"] = pd.to_datetime(g5.Date.astype(str) + g5.Time, format="%Y%m%d%H:%M:%S", utc=True)
g5 = g5.set_index("ts")[["Open", "High", "Low", "Close"]].sort_index()
tr = pd.read_pickle("results/trades_deployable.pkl")
COST_G = 0.30 + 0.30          # RT cost + slippage convention on stop-outs (flat, conservative)
res_g = {f"SL {s if s else 'none'}": [] for s in SLS}
for _, t in tr.iterrows():
    seg = g5[(g5.index > t.t_fill) & (g5.index <= t.t_out)]
    if len(seg) < 2:
        continue
    for s in SLS:
        sl_px = (t.entry - s * t.side) if s else None
        tp_px = t.entry + TP * t.side
        px, why = walk(seg.Open.values, seg.High.values, seg.Low.values,
                       seg.Close.values, t.side, t.entry, sl_px, tp_px)
        res_g[f"SL {s if s else 'none'}"].append(t.side * (px - t.entry) - COST_G)
out["GOLD (652 deployable entries)"] = {k: score(v) for k, v in res_g.items()}
out["GOLD (652 deployable entries)"]["baseline (2xrange stop, EOD)"] = score(
    (tr.pnl_oz).tolist())

# ------------------------------- MHI -------------------------------------------
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
COST_M = 10.0
res_m = {f"SL {s if s else 'none'}": [] for s in SLS}
base_m = []
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
    stop0 = (pre.high.iloc[0] + 0.5 * rng_) if sgn < 0 else (pre.low.iloc[0] - 0.5 * rng_)
    px0, _ = walk(sess.open.values, sess.high.values, sess.low.values, sess.close.values,
                  sgn, e, stop0, np.inf * sgn if sgn > 0 else -np.inf)
    base_m.append(sgn * (px0 - e) - COST_M)
    for s in SLS:
        sl_px = (e - s * sgn) if s else None
        tp_px = e + TP * sgn
        px, why = walk(sess.open.values, sess.high.values, sess.low.values,
                       sess.close.values, sgn, e, sl_px, tp_px)
        res_m[f"SL {s if s else 'none'}"].append(sgn * (px - e) - COST_M)
out["MHI (43-trade fade, HSI pts)"] = {k: score(v) for k, v in res_m.items()}
out["MHI (43-trade fade, HSI pts)"]["baseline (0.5xrange stop, EOD)"] = score(base_m)

# ------------------------------- D7 --------------------------------------------
import index_data
spxb = index_data.load("SPX").tz_convert("America/New_York")
hm = spxb.index.hour * 100 + spxb.index.minute
spx5 = spxb[(hm >= 930) & (hm < 1600)]
spxd = spx5.resample("1D").agg(open=("open", "first"), close=("close", "last")).dropna()
c = spxd.close
sma200 = c.rolling(200).mean()
low7, high7 = c.rolling(7).min(), c.rolling(7).max()
COST_S = 0.6
sigs = []
pos = False
for i in range(200, len(spxd)):
    if not pos and c.iloc[i] > sma200.iloc[i] and c.iloc[i] <= low7.iloc[i]:
        pos = True
        t_in = spxd.index[i]
        e = c.iloc[i]
        continue
    if pos and c.iloc[i] >= high7.iloc[i]:
        pos = False
        sigs.append((t_in, e, spxd.index[i], c.iloc[i]))
res_s = {f"SL {s if s else 'none'}": [] for s in SLS}
base_s = []
for t_in, e, t_out, x in sigs:
    base_s.append(x - e - COST_S)
    seg = spx5[(spx5.index > t_in + pd.Timedelta(hours=16)) & (spx5.index <= t_out + pd.Timedelta(hours=16))]
    if len(seg) < 10:
        continue
    for s in SLS:
        sl_px = e - s if s else None
        px, why = walk(seg.open.values, seg.high.values, seg.low.values,
                       seg.close.values, 1, e, sl_px, e + TP)
        res_s[f"SL {s if s else 'none'}"].append(px - e - COST_S)
out["D7 (SPX pts, long only)"] = {k: score(v) for k, v in res_s.items()}
out["D7 (SPX pts, long only)"]["baseline (7-day-high exit, no stop)"] = score(base_s)

json.dump(out, open("results/r36_brackets.json", "w"), indent=1, default=float)
for strat, cells in out.items():
    print(f"\n=== {strat} ===")
    print(f"{'cell':>34} {'n':>5} {'WR':>7} {'PF':>6} {'avg':>8} {'total':>9} {'worst':>8}")
    for k, v in cells.items():
        print(f"{k:>34} {v['n']:>5} {v['wr']*100:>6.1f}% {v['pf']:>6.2f} {v['avg']:>+8.2f} "
              f"{v['total']:>+9.0f} {v['worst']:>+8.1f}")
