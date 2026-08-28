"""Round 38: HTF signal -> LTF pullback-limit entry on the scalp families.
Frozen per pre-registration in reference/goal_ledger.md. Signal logic identical
to r37 (displacement 15m + new 1H frame; sweep-reclaim 5m), each signal now
emitting its bar range R. Entry: limit at E - d*0.5*R valid 2 signal periods of
LTF bars, worst-case fill at the limit; SL may fire on the fill bar (SL-first),
TP only from the next bar; session-end backstop; one open trade per family.
Scored at micro best-case and zero cost. Outputs results/r38_mtf.json."""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
TP, SLS = ns["TP"], ns["SLS"]
load_frame, rth_of, resample_15m, score = (ns[k] for k in
                                           ("load_frame", "rth_of", "resample_15m", "score"))
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
K = 6


def load_1m(idx):
    name = {"SPX": "SPX500_1m_oanda_futuresharks.csv",
            "NDX": "NAS100_1m_oanda_futuresharks.csv",
            "RTY": "US2000_1m_oanda_futuresharks.csv"}[idx]
    df = pd.read_csv(os.path.join("data", name))
    df["ts"] = pd.to_datetime(df["time"], utc=True)
    b = df.set_index("ts")[["open", "high", "low", "close"]].sort_index()
    b = b[~b.index.duplicated()].tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5].copy()
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date
    b["hm"] = b.index.hour * 100 + b.index.minute
    return b


def resample_1h(b):
    rth = rth_of(b)
    q = rth.resample("60min", offset="30min").agg(open=("open", "first"), high=("high", "max"),
                                                  low=("low", "min"), close=("close", "last"),
                                                  volume=("volume", "sum")).dropna(subset=["open"])
    hm = q.index.hour * 100 + q.index.minute
    return q[(hm >= 930) & (hm < 1600)]


# ---- signal generators: r37 logic + range emission ----------------------------
def sig_disp_r(q, bar_minutes):
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    disp = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    d = np.sign(q.close - q.open)
    m = disp & (d != 0)
    return sorted(zip(q.index[m] + pd.Timedelta(minutes=bar_minutes),
                      q.close[m].astype(float), d[m].astype(int),
                      (q.high - q.low)[m].astype(float)))


def sig_sweep_r(b):
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
                    # +5min: the 5m label is the bar START; the reclaim close is
                    # only knowable at bar END. Without this, 1m execution bars
                    # inside the signal bar leak lookahead fills.
                    sigs.append((rth.index[j] + pd.Timedelta(minutes=5),
                                 float(arr[j][3]), -up,
                                 float(arr[j][1] - arr[j][2])))
                    break
    return sorted(sigs)


# ---- execution ----------------------------------------------------------------
def run_mtf(sigs, ltf_by_day, valid_bars, span=None):
    """Per SL cell: {cell: (n_signals_considered, pnl_gross_list)}."""
    res = {}
    for s in SLS:
        pnls, nsig, busy_until = [], 0, None
        for t, e, side, r in sigs:
            if span is not None and not (span[0] <= t <= span[1]):
                continue
            if busy_until is not None and t <= busy_until:
                continue
            day = (t + pd.Timedelta(hours=8)).date()
            sess = ltf_by_day.get(day)
            if sess is None:
                continue
            seg = sess[sess.index > t]
            if len(seg) < 1:
                continue
            nsig += 1
            L = e - side * 0.5 * r
            arr = seg[["open", "high", "low", "close"]].values
            fk = None
            for k in range(min(valid_bars, len(arr))):
                if (side > 0 and arr[k][2] <= L) or (side < 0 and arr[k][1] >= L):
                    fk = k; break
            if fk is None:
                continue
            sl_px = (L - s * side) if s else None
            tp_px = L + TP * side
            px, xk = None, len(arr) - 1
            for k in range(fk, len(arr)):
                o, h, l, c = arr[k]
                if sl_px is not None and ((side > 0 and l <= sl_px) or (side < 0 and h >= sl_px)):
                    px, xk = sl_px, k; break
                if k > fk and ((side > 0 and h >= tp_px) or (side < 0 and l <= tp_px)):
                    px, xk = tp_px, k; break
            if px is None:
                px = arr[-1][3]
            pnls.append(side * (px - L))
            busy_until = seg.index[xk]
        res[f"SL {s if s else 'none'}"] = (nsig, pnls)
    return res


out = {}
frames_5m, frames_1m = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    frames_5m[idx] = load_frame(idx)
for idx in ("SPX", "NDX", "RTY"):
    frames_1m[idx] = load_1m(idx)

COMBOS = []
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    COMBOS.append(("disp 15m->5m", idx, "disp15", "5m", 6))
    COMBOS.append(("disp 1H->15m", idx, "disp1h", "15m", 8))
for idx in ("SPX", "NDX", "RTY"):
    COMBOS.append(("disp 15m->1m", idx, "disp15", "1m", 30))
    COMBOS.append(("sweep 5m->1m", idx, "sweep", "1m", 10))

sig_cache, ltf_cache = {}, {}
for name, idx, sigkind, ltf, valid in COMBOS:
    b = frames_5m[idx]
    if (idx, sigkind) not in sig_cache:
        if sigkind == "disp15":
            sig_cache[(idx, sigkind)] = sig_disp_r(resample_15m(b), 15)
        elif sigkind == "disp1h":
            sig_cache[(idx, sigkind)] = sig_disp_r(resample_1h(b), 60)
        else:
            sig_cache[(idx, sigkind)] = sig_sweep_r(b)
    if (idx, ltf) not in ltf_cache:
        f = rth_of(b if ltf != "1m" else frames_1m[idx])
        ltf_cache[(idx, ltf)] = ({k: g for k, g in f.groupby("skey")},
                                 (f.index.min(), f.index.max()))
    ltf_by_day, span = ltf_cache[(idx, ltf)]
    cells = run_mtf(sig_cache[(idx, sigkind)], ltf_by_day, valid,
                    span=span if ltf == "1m" else None)
    out.setdefault(name, {})[idx] = {
        cell: dict(n_signals=nsig, fill_rate=float(len(p) / nsig) if nsig else 0.0,
                   micro=score(np.asarray(p) - MICRO[idx]), zero=score(np.asarray(p)))
        for cell, (nsig, p) in cells.items()}
    print(f"{name:>13} {idx}: done")

json.dump(out, open("results/r38_mtf.json", "w"), indent=1, default=float)
for name, byidx in out.items():
    print(f"\n=== {name} (limit at 50% retrace; avg pts/filled trade) ===")
    print(f"{'idx':>5} {'cell':>9} {'sigs':>6} {'fill%':>6} {'n':>6} | {'micro':>7} {'t':>6} | {'zero':>7} {'t':>6} {'halves(zero)':>13}")
    for idx, cells in byidx.items():
        for cell, v in cells.items():
            m, z = v["micro"], v["zero"]
            if m["n"] == 0:
                print(f"{idx:>5} {cell:>9} {v['n_signals']:>6} {v['fill_rate']*100:>5.1f}%      0")
                continue
            print(f"{idx:>5} {cell:>9} {v['n_signals']:>6} {v['fill_rate']*100:>5.1f}% {m['n']:>6} | "
                  f"{m['avg']:>+7.2f} {m['t']:>+6.2f} | {z['avg']:>+7.2f} {z['t']:>+6.2f} {str(z['halves']):>13}")
