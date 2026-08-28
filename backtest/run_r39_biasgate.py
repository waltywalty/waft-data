"""Round 39: the 4-6 rule - HTF SMA20 bias gating LTF displacement triggers.
Frozen per pre-registration in reference/goal_ledger.md.
Part A: aligned-vs-opposed event study across five tier combos.
Part B: r37 scalp pipeline (15m trigger, TP+10, SL sweep, micro cost) gated by
1H / 4H / Daily bias, versus the r37b ungated baseline.
Outputs results/r39_biasgate.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
TP, SLS = ns["TP"], ns["SLS"]
load_frame, rth_of, resample_15m = ns["load_frame"], ns["rth_of"], ns["resample_15m"]
sig_disp, run_family, score = ns["sig_disp"], ns["run_family"], ns["score"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def resample_1h_rth(b):
    rth = rth_of(b)
    q = rth.resample("60min", offset="30min").agg(open=("open", "first"), high=("high", "max"),
                                                  low=("low", "min"), close=("close", "last"),
                                                  volume=("volume", "sum")).dropna(subset=["open"])
    hm = q.index.hour * 100 + q.index.minute
    return q[(hm >= 930) & (hm < 1600)]


def bias_series(b24, freq):
    """sign(close - SMA20) on completed HTF bars, indexed by bar END time."""
    c = b24.close.resample(freq).last().dropna()
    s = np.sign(c - c.rolling(20).mean())
    s.index = s.index + pd.Timedelta(freq)
    return s.dropna()


def daily_bias(b24):
    """Trading-day (18:00-roll) closes; bias for day k = prior day's close vs SMA20."""
    dc = b24.groupby("skey").close.last()
    s = np.sign(dc - dc.rolling(20).mean()).shift(1)
    return s.dropna(), dc


def disp_frame(q):
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    m = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    d = np.sign(q.close - q.open)
    return m & (d != 0), d


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))] if m > 4 else None


out = {"A": {}, "B": {}}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b24 = load_frame(idx)
    bias = {"1H": bias_series(b24, "1h"), "4H": bias_series(b24, "4h")}
    dbias, dclose = daily_bias(b24)
    frames = {"15m": (resample_15m(b24), 15), "5m": (rth_of(b24), 5),
              "1H": (resample_1h_rth(b24), 60)}

    # ---------------- Part A: aligned vs opposed drift -------------------------
    resA = {}
    for hf, tf in (("1H", "15m"), ("1H", "5m"), ("4H", "1H"), ("4H", "15m")):
        q, dur = frames[tf]
        m, d = disp_frame(q)
        t_sig = q.index + pd.Timedelta(minutes=dur)
        bs = bias[hf]
        bidx = np.searchsorted(bs.index.values, t_sig.values, side="right") - 1
        bval = np.where(bidx >= 0, bs.values[np.clip(bidx, 0, None)], np.nan)
        day = pd.Series(q.index.date, index=q.index)
        fwd4 = (q.close.shift(-4) / q.close - 1).where(day.eq(day.shift(-4)).values)
        eod = q.groupby(day.values).close.transform("last") / q.close - 1
        for hz, fwd in (("fwd4", d * fwd4), ("EOD", d * eod)):
            al = fwd[m & (d == bval)].dropna() * 1e4
            op = fwd[m & (d == -bval)].dropna() * 1e4
            resA[f"{hf}->{tf} {hz}"] = dict(
                n_al=int(len(al)), n_op=int(len(op)),
                al_bps=float(al.mean()) if len(al) else np.nan,
                op_bps=float(op.mean()) if len(op) else np.nan,
                t=welch(al, op), halves_al=halves(al.values))
    # swing tier: Daily bias -> 4H trigger, fwd 5 trading days
    q4 = b24.resample("4h").agg(open=("open", "first"), high=("high", "max"),
                                low=("low", "min"), close=("close", "last")).dropna(subset=["open"])
    q4["skey"] = (q4.index + pd.Timedelta(hours=8)).date
    m4, d4 = disp_frame(q4)
    skeys = list(dclose.index)
    pos = {k: i for i, k in enumerate(skeys)}
    vals, dirs = [], []
    for t, dd, sk in zip(q4.index[m4], d4[m4], q4.skey[m4]):
        bv = dbias.get(sk, np.nan)
        i = pos.get(sk)
        if i is None or i + 5 >= len(skeys) or not np.isfinite(bv):
            continue
        r = dd * (dclose.iloc[i + 5] / q4.close.loc[t] - 1) * 1e4
        vals.append(r)
        dirs.append(1 if dd == bv else (-1 if dd == -bv else 0))
    vals, dirs = np.asarray(vals), np.asarray(dirs)
    al, op = vals[dirs == 1], vals[dirs == -1]
    resA["D->4H fwd5d"] = dict(n_al=int(len(al)), n_op=int(len(op)),
                               al_bps=float(al.mean()) if len(al) else np.nan,
                               op_bps=float(op.mean()) if len(op) else np.nan,
                               t=welch(al, op), halves_al=halves(al))
    out["A"][idx] = resA

    # ---------------- Part B: gated scalp sim ----------------------------------
    rth = rth_of(b24)
    rth_by_day = {k: g for k, g in rth.groupby("skey")}
    sigs = sig_disp(frames["15m"][0])
    resB = {}
    for gname in ("1H", "4H", "D"):
        keep = []
        for t, e, d in sigs:
            if gname == "D":
                bv = dbias.get((t + pd.Timedelta(hours=8)).date(), np.nan)
            else:
                bs = bias[gname]
                i = bs.index.searchsorted(t, side="right") - 1
                bv = bs.values[i] if i >= 0 else np.nan
            if np.isfinite(bv) and d == bv:
                keep.append((t, e, d))
        cells = run_family(keep, rth_by_day, MICRO[idx])
        resB[f"gate {gname}"] = {k: dict(score(v), n_signals=len(keep)) for k, v in cells.items()}
    out["B"][idx] = resB
    print(f"{idx} done")

json.dump(out, open("results/r39_biasgate.json", "w"), indent=1, default=float)
print("\n=== Part A: displacement drift, ALIGNED vs OPPOSED to HTF bias (bps) ===")
for idx, res in out["A"].items():
    print(f"-- {idx}")
    print(f"{'tier':>16} {'n_al':>6} {'n_op':>6} {'aligned':>8} {'opposed':>8} {'t(diff)':>8} {'halves(al)':>12}")
    for k, v in res.items():
        print(f"{k:>16} {v['n_al']:>6} {v['n_op']:>6} {v['al_bps']:>+7.1f}b {v['op_bps']:>+7.1f}b "
              f"{v['t']:>+8.2f} {str(v['halves_al']):>12}")
print("\n=== Part B: gated TP+10 scalp at micro cost (vs r37b ungated) ===")
for idx, res in out["B"].items():
    print(f"-- {idx}")
    print(f"{'gate':>8} {'cell':>9} {'sigs':>6} {'n':>6} {'WR':>7} {'PF':>6} {'avg':>7} {'t':>6} {'halves':>12}")
    for g, cells in res.items():
        for k, v in cells.items():
            if v["n"] == 0:
                continue
            print(f"{g:>8} {k:>9} {v['n_signals']:>6} {v['n']:>6} {v['wr']*100:>6.1f}% {v['pf']:>6.2f} "
                  f"{v['avg']:>+7.2f} {v['t']:>+6.2f} {str(v['halves']):>12}")
