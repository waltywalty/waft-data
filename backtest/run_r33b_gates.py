"""Round 33 Phase 4b: event-study validation of the three untested gates
(FP2 RVOL, FP4 absorption, FP5 displacement) per the pre-registration in
reference/goal_ledger.md. Outputs results/r33b_gates.json."""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves_sign(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))]


def load_rth(idx, freq):
    b = index_data.load(idx).tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5]
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    if freq != "5min":
        b = b.resample(freq).agg(open=("open", "first"), high=("high", "max"),
                                 low=("low", "min"), close=("close", "last"),
                                 volume=("volume", "sum")).dropna(subset=["open"])
        hm2 = b.index.hour * 100 + b.index.minute
        b = b[(hm2 >= 930) & (hm2 < 1600)]
    return b


out = {}
for idx in ("SPX", "NDX", "RTY"):
    res = {}

    # ---------------- FP2: RVOL (5m, 2010+) ----------------
    b = load_rth(idx, "5min")["2010":].copy()
    b["day"] = b.index.date
    b["bkt"] = b.index.hour * 60 + b.index.minute
    piv = b.pivot_table(index="day", columns="bkt", values="volume")
    base = piv.rolling(20, min_periods=10).mean().shift(1)
    b["rvol"] = (piv / base).stack().reindex(
        pd.MultiIndex.from_arrays([b.day, b.bkt])).values
    b = b.reset_index(drop=True)
    b["ret"] = b.close / b.open - 1
    b["dir"] = np.sign(b.ret)
    fwd6 = b.close.shift(-6) / b.close - 1
    rng6 = (b.high.rolling(6).max().shift(-6) - b.low.rolling(6).min().shift(-6)) / b.close
    samed = b.day.values == pd.Series(b.day).shift(-6).values      # stay inside the day
    b["cont"] = (b.dir * fwd6).where(samed)
    b["arange"] = rng6.where(samed)
    ctrl = b[(b.rvol < 1.25)].dropna(subset=["cont"])
    for th in (1.5, 2.5):
        ev = b[b.rvol >= th].dropna(subset=["cont"])
        res[f"FP2 rvol>={th} contin"] = dict(
            n=len(ev), ev_bps=float(ev.cont.mean() * 1e4), ctrl_bps=float(ctrl.cont.mean() * 1e4),
            t=welch(ev.cont, ctrl.cont), halves=halves_sign(ev.cont.values))
        res[f"FP2 rvol>={th} range"] = dict(
            n=len(ev), ev_bps=float(ev.arange.mean() * 1e4), ctrl_bps=float(ctrl.arange.mean() * 1e4),
            t=welch(ev.arange.dropna(), ctrl.arange.dropna()), halves=halves_sign(ev.arange.dropna().values))

    # ---------------- FP4/FP5 shared 15m frame ----------------
    q = load_rth(idx, "15min")
    q["day"] = q.index.date
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    q["disp"] = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    q["dir"] = np.sign(q.close - q.open)
    fwd4 = q.close.shift(-4) / q.close - 1
    same4 = q.day.values == pd.Series(q.day).shift(-4).values
    q["cont4"] = (q.dir * fwd4).where(same4)
    eod = q.groupby("day").close.transform("last")
    q["toEOD"] = q.dir * (eod / q.close - 1)

    # FP5(a): displacement continuation vs all-bars control (full sample)
    ev = q[q.disp].dropna(subset=["cont4"])
    cv = q[~q.disp].dropna(subset=["cont4"])
    res["FP5 disp contin 1h"] = dict(n=len(ev), ev_bps=float(ev.cont4.mean() * 1e4),
                                     ctrl_bps=float(cv.cont4.mean() * 1e4),
                                     t=welch(ev.cont4, cv.cont4), halves=halves_sign(ev.cont4.values))
    # FP5(b): first-hour displacement -> rest of day in its direction
    fh = q[q.index.hour * 100 + q.index.minute < 1030]
    fhev = fh[fh.disp].groupby("day").first()
    rest = fhev.dir * (eod.groupby(q.day).last().reindex(fhev.index) / fhev.close - 1)
    res["FP5 first-hour disp -> EOD"] = dict(n=len(rest), ev_bps=float(rest.mean() * 1e4),
                                             ctrl_bps=0.0,
                                             t=float(rest.mean() / rest.std() * np.sqrt(len(rest))),
                                             halves=halves_sign(rest.values))

    # ---------------- FP4: absorption (15m, 2010+) ----------------
    w = q["2010":].copy()
    volP = w.volume.rolling(100).apply(lambda x: (x < x.iloc[-1]).mean() * 100, raw=False)
    # percentrank via rolling rank (vector-friendly):
    volP = w.volume.rolling(100).rank(pct=True) * 100
    rngP = (w.high - w.low).rolling(100).rank(pct=True) * 100
    clv = (2 * w.close - w.high - w.low) / (w.high - w.low).replace(0, np.nan)
    atLow = w.low <= w.low.rolling(20).min()
    atHigh = w.high >= w.high.rolling(20).max()
    effort = (volP >= 80) & (rngP <= 40)
    absBuy = effort & atLow & (clv > 0)
    absSell = effort & atHigh & (clv < 0)
    fwd4w = w.close.shift(-4) / w.close - 1
    same4w = w.day.values == pd.Series(w.day).shift(-4).values
    eodw = w.groupby("day").close.transform("last")
    for side, mask, ctrlmask, sgn in (("buy", absBuy, atLow & ~effort, 1),
                                      ("sell", absSell, atHigh & ~effort, -1)):
        e4 = (sgn * fwd4w).where(same4w)[mask].dropna()
        c4 = (sgn * fwd4w).where(same4w)[ctrlmask].dropna()
        eE = (sgn * (eodw / w.close - 1))[mask].dropna()
        cE = (sgn * (eodw / w.close - 1))[ctrlmask].dropna()
        res[f"FP4 absorb {side} 1h"] = dict(n=len(e4), ev_bps=float(e4.mean() * 1e4),
                                            ctrl_bps=float(c4.mean() * 1e4),
                                            t=welch(e4, c4), halves=halves_sign(e4.values))
        res[f"FP4 absorb {side} EOD"] = dict(n=len(eE), ev_bps=float(eE.mean() * 1e4),
                                             ctrl_bps=float(cE.mean() * 1e4),
                                             t=welch(eE, cE), halves=halves_sign(eE.values))
    out[idx] = res

json.dump(out, open("results/r33b_gates.json", "w"), indent=1, default=float)
for idx, res in out.items():
    print(f"\n=== {idx} ===")
    print(f"{'cell':>28} {'n':>6} {'event':>8} {'control':>8} {'t(diff)':>8} {'halves':>12}")
    for k, v in res.items():
        print(f"{k:>28} {v['n']:>6} {v['ev_bps']:>+7.1f}b {v['ctrl_bps']:>+7.1f}b "
              f"{v['t']:>+8.2f} {str(v['halves']):>12}")
