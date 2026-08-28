"""Round 37: footprint confirmations traded as 10-point scalps (user commission).
Frozen per pre-registration in reference/goal_ledger.md. Signals byte-identical
to r33 (sweep-reclaim) and r33b (displacement, absorption); execution replaced
by TP +10 pts, SL in {5, 10, 20, none}, worst-case intrabar ordering (SL first),
session-end backstop, one open trade per family per instrument (per SL cell).
Instruments SPX/NDX/RTY (r33 session logic) + gold (same logic on NY hours,
documented adaptation). Outputs results/r37_scalps.json."""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

TP = 10.0
SLS = [5.0, 10.0, 20.0, None]
COST = {"SPX": 0.6, "NDX": 2.0, "RTY": 0.4, "GOLD": 0.6}
K = 6  # sweep failure window, bars


def load_frame(idx):
    if idx == "GOLD":
        g = pd.read_csv("data/XAUUSD_5m.csv")
        g["ts"] = pd.to_datetime(g.Date.astype(str) + g.Time, format="%Y%m%d%H:%M:%S", utc=True)
        b = g.set_index("ts").rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].sort_index()
    else:
        b = index_data.load(idx)
    b = b.tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5].copy()
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date
    b["hm"] = b.index.hour * 100 + b.index.minute
    return b


def rth_of(b):
    return b[(b.hm >= 930) & (b.hm <= 1555)]


# ---- signal generators (frozen definitions) -----------------------------------
def sig_sweep(b):
    """r33: first breach per session of PDH/PDL/ONH/ONL; failure = 5m close back
    inside within 6 bars; entry at failure close, direction = reversal."""
    sigs, prev_rth = [], None
    for skey, g in b.groupby("skey"):
        on = g[(g.hm >= 1600) | (g.hm < 930)]
        rth = rth_of(g)
        if len(rth) < 40:
            prev_rth = rth if len(rth) else prev_rth
            continue
        levels = {}
        if prev_rth is not None and len(prev_rth) > 40:
            levels["PDH"] = (prev_rth.high.max(), +1)
            levels["PDL"] = (prev_rth.low.min(), -1)
        if len(on) > 20:
            levels["ONH"] = (on.high.max(), +1)
            levels["ONL"] = (on.low.min(), -1)
        prev_rth = rth
        arr = rth[["open", "high", "low", "close"]].values
        n = len(arr)
        for lname, (lvl, up) in levels.items():
            if not np.isfinite(lvl):
                continue
            bi = None
            for i in range(n):
                if (up > 0 and arr[i][1] > lvl) or (up < 0 and arr[i][2] < lvl):
                    bi = i; break
            if bi is None:
                continue
            for j in range(bi, min(bi + K + 1, n)):
                if (up > 0 and arr[j][3] < lvl) or (up < 0 and arr[j][3] > lvl):
                    sigs.append((rth.index[j], float(arr[j][3]), -up))
                    break
    return sorted(sigs)


def resample_15m(b):
    rth = rth_of(b)
    q = rth.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                                  low=("low", "min"), close=("close", "last"),
                                  volume=("volume", "sum")).dropna(subset=["open"])
    hm = q.index.hour * 100 + q.index.minute
    return q[(hm >= 930) & (hm < 1600)]


def sig_disp(q):
    """r33b: 15m RTH bar, TR >= 1.5x ATR14, body >= 0.6x range; trade bar direction."""
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    disp = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    d = np.sign(q.close - q.open)
    m = disp & (d != 0)
    return sorted(zip(q.index[m] + pd.Timedelta(minutes=15), q.close[m].astype(float), d[m].astype(int)))


def sig_absorb(q):
    """r33b: 15m 2010+, vol pctile >= 80 & range pctile <= 40 (100-bar) at a
    20-bar extreme with CLV confirm; fade direction."""
    w = q["2010":].copy()
    volP = w.volume.rolling(100).rank(pct=True) * 100
    rngP = (w.high - w.low).rolling(100).rank(pct=True) * 100
    clv = (2 * w.close - w.high - w.low) / (w.high - w.low).replace(0, np.nan)
    atLow = w.low <= w.low.rolling(20).min()
    atHigh = w.high >= w.high.rolling(20).max()
    effort = (volP >= 80) & (rngP <= 40)
    buy = effort & atLow & (clv > 0)
    sell = effort & atHigh & (clv < 0)
    sigs = [(t + pd.Timedelta(minutes=15), float(c), 1) for t, c in zip(w.index[buy], w.close[buy])]
    sigs += [(t + pd.Timedelta(minutes=15), float(c), -1) for t, c in zip(w.index[sell], w.close[sell])]
    return sorted(sigs)


# ---- scalp execution ----------------------------------------------------------
def walk(arr, side, sl_px, tp_px):
    for o, h, l, c in arr:
        if side > 0:
            if sl_px is not None and l <= sl_px:
                return sl_px
            if h >= tp_px:
                return tp_px
        else:
            if sl_px is not None and h >= sl_px:
                return sl_px
            if l <= tp_px:
                return tp_px
    return arr[-1][3]


def run_family(sigs, rth_by_day, cost):
    """Per SL cell: one open trade at a time; return {cell: [pnl,...]}."""
    res = {}
    for s in SLS:
        pnls, busy_until = [], None
        for t, e, side in sigs:
            if busy_until is not None and t <= busy_until:
                continue
            day = (t + pd.Timedelta(hours=8)).date()
            sess = rth_by_day.get(day)
            if sess is None:
                continue
            seg = sess[sess.index > t]
            if len(seg) < 1:
                continue
            arr = seg[["open", "high", "low", "close"]].values
            sl_px = (e - s * side) if s else None
            px = walk(arr, side, sl_px, e + TP * side)
            pnls.append(side * (px - e) - cost)
            # exit bar: first bar that could have produced px (approximate as
            # the bar where the bracket resolved; for backstop, session end)
            k = len(arr) - 1
            for i, (o, h, l, c) in enumerate(arr):
                hit_sl = sl_px is not None and ((side > 0 and l <= sl_px) or (side < 0 and h >= sl_px))
                hit_tp = (side > 0 and h >= e + TP) or (side < 0 and l <= e - TP)
                if hit_sl or hit_tp:
                    k = i; break
            busy_until = seg.index[k]
        res[f"SL {s if s else 'none'}"] = pnls
    return res


def score(p):
    p = np.asarray(p, float)
    if len(p) == 0:
        return dict(n=0)
    w, l = p[p > 0], p[p <= 0]
    m = len(p) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else np.inf,
                avg=float(p.mean()), total=float(p.sum()), worst=float(p.min()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))) if p.std() > 0 else np.nan,
                halves=[float(np.sign(p[:m].mean())), float(np.sign(p[m:].mean()))] if m > 4 else None)


if __name__ != "__main__":
    raise SystemExit  # importable module: r37b reuses the functions above

out = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = load_frame(idx)
    rth = rth_of(b)
    rth_by_day = {k: g for k, g in rth.groupby("skey")}
    q = resample_15m(b)
    fams = {"sweep-reclaim": sig_sweep(b), "displacement": sig_disp(q),
            "absorption": sig_absorb(q)}
    out[idx] = {}
    for fam, sigs in fams.items():
        cells = run_family(sigs, rth_by_day, COST[idx])
        out[idx][fam] = {k: score(v) for k, v in cells.items()}
    print(f"{idx}: {len(fams['sweep-reclaim'])} sweep sigs, "
          f"{len(fams['displacement'])} disp sigs, {len(fams['absorption'])} absorb sigs")

json.dump(out, open("results/r37_scalps.json", "w"), indent=1, default=float)
for idx, fams in out.items():
    print(f"\n=== {idx} (TP +10 pts, cost {COST[idx]}) ===")
    print(f"{'family':>14} {'cell':>9} {'n':>6} {'WR':>7} {'PF':>6} {'avg':>7} {'total':>9} {'worst':>7} {'t':>6} {'halves':>12}")
    for fam, cells in fams.items():
        for k, v in cells.items():
            if v["n"] == 0:
                print(f"{fam:>14} {k:>9}      0")
                continue
            print(f"{fam:>14} {k:>9} {v['n']:>6} {v['wr']*100:>6.1f}% {v['pf']:>6.2f} {v['avg']:>+7.2f} "
                  f"{v['total']:>+9.0f} {v['worst']:>+7.1f} {v['t']:>+6.2f} {str(v['halves']):>12}")
