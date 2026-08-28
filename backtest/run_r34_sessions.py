"""Round 34: per-session behaviour atlas for the footprint families.

Frozen per the pre-registration in reference/goal_ledger.md. Sessions (ET):
Asia 20:00-00:00, London 02:00-05:00, NY AM 09:30-11:00, lunch 12:00-13:00,
NY PM 13:30-16:00. Definitions identical to r33/r33b; sweeps extended to all
sessions (registered). Outputs results/r34_sessions.json.
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

SESS = {"Asia": (2000, 2400), "London": (200, 500), "NYAM": (930, 1100),
        "Lunch": (1200, 1300), "NYPM": (1330, 1600)}


def sess_of(hm):
    out = np.full(len(hm), "", dtype=object)
    for name, (a, b) in SESS.items():
        m = (hm >= a) & (hm < b) if a < b else (hm >= a)
        out[m] = name
    return out


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 5 and x.std() > 0 else np.nan


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def load(idx):
    b = index_data.load(idx).tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5].copy()
    b["hm"] = b.index.hour * 100 + b.index.minute
    b["sess"] = sess_of(b.hm.values)
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date
    return b


out = {}
for idx in ("SPX", "NDX", "RTY"):
    res = {"sweeps": {}, "rvol": {}, "disp": {}}
    b5 = load(idx)

    # ---------------- A: sweep failures, all sessions --------------------------
    rows = []
    prev_rth = None
    for skey, g in b5.groupby("skey"):
        rth = g[(g.hm >= 930) & (g.hm <= 1555)]
        if prev_rth is not None and len(prev_rth) > 40 and len(g) > 60:
            arr = g[["open", "high", "low", "close"]].values
            svec = g.sess.values
            for lname, lvl, up in (("PDH", prev_rth.high.max(), 1),
                                   ("PDL", prev_rth.low.min(), -1)):
                bi = None
                for i in range(len(arr)):
                    if (up > 0 and arr[i][1] > lvl) or (up < 0 and arr[i][2] < lvl):
                        bi = i; break
                if bi is None or svec[bi] == "":
                    continue
                fj = None
                for j in range(bi, min(bi + 7, len(arr))):
                    if (up > 0 and arr[j][3] < lvl) or (up < 0 and arr[j][3] > lvl):
                        fj = j; break
                r = dict(sess=svec[bi], failed=fj is not None)
                if fj is not None and fj + 6 < len(arr):
                    d = -up
                    e = arr[fj][3]
                    r["fwd30"] = d * (arr[fj + 6][3] - e) / e * 1e4
                rows.append(r)
        prev_rth = rth if len(rth) else prev_rth
    S = pd.DataFrame(rows)
    for sname, sub in S.groupby("sess"):
        f = sub[sub.failed].get("fwd30", pd.Series(dtype=float)).dropna()
        res["sweeps"][sname] = dict(breaches=int(len(sub)),
                                    fail_rate=float(sub.failed.mean()),
                                    fwd30_bps=float(f.mean()) if len(f) > 10 else np.nan,
                                    t=tstat(f))

    # ---------------- B: RVOL >= 2.5 per session (2010+) -----------------------
    w = b5["2010":].copy()
    w["bkt"] = w.index.hour * 60 + w.index.minute
    w["day"] = w.index.date
    piv = w.pivot_table(index="day", columns="bkt", values="volume")
    base = piv.rolling(20, min_periods=10).mean().shift(1)
    w["rvol"] = (piv / base).stack().reindex(
        pd.MultiIndex.from_arrays([w.day, w.bkt])).values
    w = w.reset_index(drop=True)
    w["dir"] = np.sign(w.close - w.open)
    fwd6 = w.close.shift(-6) / w.close - 1
    rng6 = (w.high.rolling(6).max().shift(-6) - w.low.rolling(6).min().shift(-6)) / w.close
    same = w.skey.values == pd.Series(w.skey).shift(-6).values
    w["cont"] = (w.dir * fwd6).where(same)
    w["arange"] = rng6.where(same)
    for sname in SESS:
        seg = w[w.sess == sname]
        ev = seg[seg.rvol >= 2.5].dropna(subset=["arange"])
        cv = seg[seg.rvol < 1.25].dropna(subset=["arange"])
        if len(ev) < 30:
            res["rvol"][sname] = dict(n=int(len(ev)))
            continue
        res["rvol"][sname] = dict(
            n=int(len(ev)), per_year=float(len(ev) / 15.5),
            range_ratio=float(ev.arange.mean() / cv.arange.mean()),
            range_t=welch(ev.arange, cv.arange),
            cont_diff_bps=float((ev.cont.mean() - cv.cont.mean()) * 1e4),
            cont_t=welch(ev.cont.dropna(), cv.cont.dropna()))

    # ---------------- C: displacement per session (15m) ------------------------
    q = b5.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                                 low=("low", "min"), close=("close", "last")).dropna(subset=["open"])
    q["hm"] = q.index.hour * 100 + q.index.minute
    q["sess"] = sess_of(q.hm.values)
    q["skey"] = (q.index + pd.Timedelta(hours=8)).date
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    q["disp"] = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    d = np.sign(q.close - q.open)
    fwd4 = q.close.shift(-4) / q.close - 1
    same4 = q.skey.values == pd.Series(q.skey).shift(-4).values
    q["cont4"] = (d * fwd4).where(same4)
    for sname in SESS:
        seg = q[q.sess == sname]
        ev = seg[seg.disp].cont4.dropna()
        cv = seg[~seg.disp].cont4.dropna()
        res["disp"][sname] = dict(n=int(len(ev)),
                                  ev_bps=float(ev.mean() * 1e4) if len(ev) > 10 else np.nan,
                                  ctrl_bps=float(cv.mean() * 1e4) if len(cv) > 10 else np.nan,
                                  t=welch(ev, cv))
    out[idx] = res

json.dump(out, open("results/r34_sessions.json", "w"), indent=1, default=float)

ORDER = ["Asia", "London", "NYAM", "Lunch", "NYPM"]
for idx in out:
    print(f"\n=== {idx} ===")
    print(f"{'':>7} | {'sweeps: n':>9} {'fail%':>6} {'fwd30':>7} {'t':>6} | "
          f"{'rvol/yr':>8} {'rng x':>6} {'cont':>6} {'t':>6} | {'disp n':>7} {'diff':>6} {'t':>6}")
    for sn in ORDER:
        sw = out[idx]["sweeps"].get(sn, {})
        rv = out[idx]["rvol"].get(sn, {})
        dp = out[idx]["disp"].get(sn, {})
        sws = (f"{sw.get('breaches',0):>9} {sw.get('fail_rate',np.nan)*100:>5.1f}% "
               f"{sw.get('fwd30_bps',np.nan):>+6.1f}b {sw.get('t',np.nan):>+6.2f}") if sw else " " * 32
        rvs = (f"{rv.get('per_year',np.nan):>8.0f} {rv.get('range_ratio',np.nan):>6.2f} "
               f"{rv.get('cont_diff_bps',np.nan):>+5.1f}b {rv.get('cont_t',np.nan):>+6.2f}") if rv.get("n", 0) >= 30 else f"{rv.get('n',0):>8} (thin)" + " " * 14
        dps = (f"{dp.get('n',0):>7} {dp.get('ev_bps',np.nan)-dp.get('ctrl_bps',np.nan):>+5.1f}b "
               f"{dp.get('t',np.nan):>+6.2f}") if dp else ""
        print(f"{sn:>7} | {sws} | {rvs} | {dps}")
