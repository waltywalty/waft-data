"""Round 77 commissioned battery (5-minute candles): A volume continuation, B compression->expansion,
E VWAP deviation, D combination. Registration: goal_ledger.md "## Round 77". IS only (engine cuts);
the 2026 Dukascopy holdout is opened only by the integrator (UNSEAL_OK=1 --unseal, single cell).
Outputs results/r77_battery_is.json (+ .log). Costs MICRO; R = (pnl - cost)/ATR20-daily; the user's
R (5m-ATR14 units) is reported alongside as 'r5'.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday_engine as E  # noqa: E402

UNSEAL = "--unseal" in sys.argv
if UNSEAL:
    raise SystemExit("R77 holdout = the 2026 Dukascopy 1m->5m block; this runner has no loader for it - write run_r77_unseal.py for the single cleared cell")
HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(77)
VOL_START = pd.Timestamp("2010-01-01")
NY = "America/New_York"


# ------------------------------------------------------------------ shared helpers
def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), wr=float((x > 0).mean()), pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                mean=float(x.mean()), t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def cell_stats(g):
    g = g.sort_values("date")
    return dict(x0_gross=stats(g.R0), x1=stats(g.R), x15=stats(g.R15), x2=stats(g.R20), r5_net=stats(g.r5),
                how={k: int(v) for k, v in g.how.value_counts().items()} if "how" in g else {}, n_days=int(g.date.nunique()), long_share=float((g.side > 0).mean()),
                per_year_sign={int(y): float(np.sign(gg.R.mean())) for y, gg in g.groupby(pd.to_datetime(g.date).dt.year)},
                per_instr={i: stats(gg.R) for i, gg in g.groupby("instr")})


def maxstat(t, draws=2000):
    """Trade-level per-cell t with one sign per date shared across instruments and cells; returns (summary, null max|t|)."""
    t = t.copy(); dates = np.array(sorted(t.date.unique())); di = {d: i for i, d in enumerate(dates)}; t["di"] = t.date.map(di)
    cells = sorted(t.cell.unique()); R = {c: (t.loc[t.cell == c, "R"].values, t.loc[t.cell == c, "di"].values) for c in cells}
    tstat = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 and x.std(ddof=1) > 1e-12 else 0.0
    obs = {c: tstat(R[c][0]) for c in cells}; mx = []
    for _ in range(draws):
        sgn = RNG.choice([-1.0, 1.0], size=len(dates)); mx.append(max(abs(tstat(R[c][0] * sgn[R[c][1]])) for c in cells))
    mx = np.array(mx)
    return dict(obs_t={c: float(v) for c, v in obs.items()}, draws=draws), mx


def judge(cells, T, floor, label):
    """Bar test on the best positive-t cell: n, mean, PF, halves, 2x, Bonferroni floor, bar-cell max-stat p, lone spike."""
    ms, mx = maxstat(T)
    best = max(cells.items(), key=lambda kv: (kv[1]["x1"].get("t") or -99)); bx = best[1]; tb = bx["x1"].get("t") or 0.0
    p_best = float((np.sum(mx >= abs(tb)) + 1) / (len(mx) + 1))
    others = [v["x1"]["mean"] for k, v in cells.items() if k != best[0] and "mean" in v["x1"]]
    se = bx["x1"]["mean"] / tb if tb else float("nan")
    spike = bool(others and (bx["x1"]["mean"] - max(others)) > se)
    ok = (bx["x1"].get("n", 0) >= 40 and bx["x1"].get("mean", -1) > 0 and tb >= floor and bx["x1"].get("pf", 0) >= 1.15
          and bx["x1"].get("halves") == [1.0, 1.0] and bx["x2"].get("mean", -1) > 0 and p_best < 0.05 and not spike)
    out = dict(best_cell=best[0], best_t=float(tb), bonferroni_floor=floor, bar_cell_maxstat_p=p_best, lone_spike=spike,
               max_abs_t_over_grid=float(max(abs(v) for v in ms["obs_t"].values())), p_of_global_max=float((np.sum(mx >= max(abs(v) for v in ms["obs_t"].values())) + 1) / (len(mx) + 1)),
               obs_t=ms["obs_t"], IS_pass=bool(ok))
    print(f"\n{label} VERDICT: {'PASS' if ok else 'FAIL'} - best {best[0]} t {tb:+.2f} (floor {floor}), bar-cell p {p_best:.3f}, spike {spike}")
    return out


def scan(path, side, entry, stop, tgt):
    """Worst-case walk over path bars: the first bar touching the stop (<= / >=) fills at the stop; a target touch
    fills at the target only if no earlier-or-same bar touched the stop (stop wins ties); else time exit."""
    lo, hi = path.low.values, path.high.values; n = len(lo)
    s_hit = ((lo <= stop) if side == 1 else (hi >= stop)) if stop is not None else np.zeros(n, bool)
    t_hit = ((hi >= tgt) if side == 1 else (lo <= tgt)) if tgt is not None else np.zeros(n, bool)
    i_s = int(np.argmax(s_hit)) if s_hit.any() else n
    i_t = int(np.argmax(t_hit)) if t_hit.any() else n
    if i_s < n and i_s <= i_t:
        return float(stop), "stop"
    if i_t < n:
        return float(tgt), "target"
    return float(path.close.iloc[-1]), "time"


def row(date, instr, side, entry, exit_px, how, cost, atr_d, atr5, extra=None):
    pnl = side * (exit_px - entry)
    r = dict(date=str(date), instr=instr, side=side, how=how, pnl=pnl, R0=pnl / atr_d, R=(pnl - cost) / atr_d, R15=(pnl - 1.5 * cost) / atr_d,
             R20=(pnl - 2 * cost) / atr_d, r5=(pnl - cost) / atr5 if atr5 > 0 else np.nan)
    if extra: r.update(extra)
    return r


def prep(idx):
    """5m 24h frame with session key, hm, ATR14 (5m, shifted), same-slot RVOL (trailing 20 sessions), session ATR20-daily."""
    d, b, cut = E.sessions(idx)                                        # IS only; OOS rows never enter b
    b = b.copy()
    tr = np.maximum(b.high - b.low, np.maximum((b.high - b.close.shift(1)).abs(), (b.low - b.close.shift(1)).abs()))
    b["atr14"] = tr.rolling(14).mean().shift(1)                       # ATR of the 14 bars BEFORE this bar
    b["rng"] = b.high - b.low
    if "volume" in b.columns:
        # same-slot trailing-20-SESSION mean volume, excluding the current session (pivot over session rows only)
        pv = b[b.skey.isin(d.index)].pivot_table(index="skey", columns="hm", values="volume", aggfunc="sum")
        base = pv.rolling(20, min_periods=10).mean().shift(1)
        b = b.join(base.stack().rename("vbase"), on=["skey", "hm"])
        b["rvol"] = b.volume / b.vbase
    b["atr_d"] = b.skey.map(d.atr20)
    return d, b, cut


# ------------------------------------------------------------------ A. volume continuation
def battery_A(idx):
    d, b, cut = prep(idx)
    b = b[(b.index >= VOL_START.tz_localize(NY))] if b.index.tz is not None else b
    cost = E.MICRO[idx]; rows, meas = [], []
    hm = b.hm
    b["peak"] = ((hm >= 930) & (hm < 1100)) | ((hm >= 1500) & (hm < 1600))
    b["offpeak"] = (hm >= 1100) & (hm < 1500)
    b["overnight"] = (hm >= 1800) | (hm < 930)
    b["onhour"] = (b.index.minute % 30 == 0)
    ev = b[(b.rvol >= 2) & np.isfinite(b.atr14) & (b.atr14 > 0) & np.isfinite(b.atr_d) & (b.close != b.open)]
    keys = list(b.index)
    pos = {ts: i for i, ts in enumerate(keys)}
    for ts, e in ev.iterrows():
        i = pos[ts]
        if i + 7 >= len(keys): continue
        nxt = b.iloc[i + 1]; side = int(np.sign(e.close - e.open)); entry = float(nxt.open)
        atr5, atr_d = float(e.atr14), float(e.atr_d)
        fwd6 = b.iloc[i + 1:i + 7]
        # session-end path: bars until the session key changes
        sess = b.iloc[i + 1:i + 1 + 300]; sess = sess[sess.skey == e.skey]
        if len(fwd6) < 6 or len(sess) < 2 or (fwd6.skey != e.skey).any() or (fwd6.index[-1] - ts) != pd.Timedelta(minutes=30):
            continue                                                  # the "next 30 minutes" must be 6 contiguous bars in-session
        big = bool(e.rng >= 2 * atr5); rv3 = bool(e.rvol >= 3)
        clock = "peak" if e.peak else ("offpeak" if e.offpeak else ("overnight" if e.overnight else "other"))
        meas.append(dict(date=str(e.skey), instr=idx, rv3=rv3, big=big, clock=clock, onhour=bool(e.onhour),
                         fwd30_r5=side * (float(fwd6.close.iloc[-1]) - entry) / atr5, fwd30_abs_r5=(fwd6.high.max() - fwd6.low.min()) / atr5))
        for ex in ("t30", "tp1", "tp4"):
            if ex == "t30":
                x, how = float(fwd6.close.iloc[-1]), "time"
            else:
                k = 1.0 if ex == "tp1" else 4.0
                x, how = scan(sess, side, entry, entry - side * atr5, entry + side * k * atr5)
            rows.append(row(e.skey, idx, side, entry, x, how, cost, atr_d, atr5, dict(rv3=rv3, big=big, clock=clock, onhour=bool(e.onhour), ex=ex)))
    # control: RVOL < 1.25 same slots, forward 30-min signed move (mirror of the measure)
    ctl = b[(b.rvol < 1.25) & np.isfinite(b.atr14) & (b.atr14 > 0) & (b.close != b.open)].iloc[::7]
    cm = []
    for ts, e in ctl.iterrows():
        i = pos[ts]
        if i + 7 >= len(keys): continue
        fwd6 = b.iloc[i + 1:i + 7]; side = int(np.sign(e.close - e.open))
        if len(fwd6) < 6 or (fwd6.skey != e.skey).any() or (fwd6.index[-1] - ts) != pd.Timedelta(minutes=30): continue
        cm.append(dict(date=str(e.skey), v=side * (float(fwd6.close.iloc[-1]) - float(b.iloc[i + 1].open)) / float(e.atr14)))
    return pd.DataFrame(rows), pd.DataFrame(meas), pd.DataFrame(cm)


# ------------------------------------------------------------------ B. compression -> expansion
def battery_B(idx):
    d, b, cut = prep(idx); cost = E.MICRO[idx]; rows = []
    b = b[np.isfinite(b.atr14) & np.isfinite(b.atr_d)].copy()
    # per-session thresholds: 10th / 20th percentile of ATR14 over the previous 20 sessions' bars
    sess_keys = list(dict.fromkeys(b.skey)); atr_by = {k: g.atr14.values for k, g in b.groupby("skey")}
    thr = {}
    for j, k in enumerate(sess_keys):
        if j < 20: continue
        pool = np.concatenate([atr_by[s] for s in sess_keys[j - 20:j]])
        thr[k] = (np.nanpercentile(pool, 10), np.nanpercentile(pool, 20))
    keys = list(b.index); pos = {ts: i for i, ts in enumerate(keys)}
    for k, g in b.groupby("skey"):
        if k not in thr: continue
        p10, p20 = thr[k]
        fired = {(pc, m): False for pc in (10, 20) for m in (2.0, 1.5)}
        for ts, e in g.iterrows():
            for pc, m in fired:
                if fired[(pc, m)]: continue
                th = p10 if pc == 10 else p20
                if e.atr14 <= th and e.rng >= m * e.atr14 and e.close != e.open:
                    fired[(pc, m)] = True
                    i = pos[ts]
                    if i + 2 >= len(keys): continue
                    side = int(np.sign(e.close - e.open)); nxt = b.iloc[i + 1]; entry = float(nxt.open)
                    stop = float(e.low) if side == 1 else float(e.high)
                    p60 = b.iloc[i + 1:i + 13]; p60 = p60[p60.skey == e.skey]
                    # session end: to the end of THIS session key (RTH triggers -> 15:55; overnight triggers -> that day's 15:55)
                    ps = b.iloc[i + 1:i + 1 + 400]; ps = ps[ps.skey == e.skey]
                    if len(p60) < 2 or len(ps) < 2: continue
                    for ex, path in (("t60", p60), ("sess", ps)):
                        x, how = scan(path, side, entry, stop, None)
                        rows.append(row(e.skey, idx, side, entry, x, how, cost, float(e.atr_d), float(e.atr14),
                                        dict(pc=pc, mult=m, ex=ex, at_open=bool(e.hm == 930), clock=("rth" if 930 <= e.hm <= 1555 else "ovn"))))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ E. VWAP deviation
def battery_E(idx):
    d, b, cut = prep(idx); cost = E.MICRO[idx]; rows = []
    b = b[(b.index >= VOL_START.tz_localize(NY))]
    rth = b[(b.hm >= 930) & (b.hm <= 1555) & np.isfinite(b.atr_d)].copy()
    tp = (rth.high + rth.low + rth.close) / 3
    rth["pv"] = tp * rth.volume; rth["pv2"] = tp * tp * rth.volume
    g = rth.groupby("skey")
    rth["cv"] = g.volume.cumsum(); rth["cpv"] = g.pv.cumsum(); rth["cpv2"] = g.pv2.cumsum()
    rth["vwap"] = rth.cpv / rth.cv
    rth["sig"] = np.sqrt(np.maximum(rth.cpv2 / rth.cv - rth.vwap ** 2, 0))
    rth["nbar"] = g.cumcount()
    for k, day in rth.groupby("skey"):
        day = day.reset_index()
        atr_d = float(day.atr_d.iloc[0])
        for ks in (2.0, 2.5, 3.0):
            for side_ev in (1, -1):        # +1: price above VWAP (fade = short); -1: below (fade = long)
                cand = day[(day.nbar >= 12) & (day.sig > 0) & (side_ev * (day.close - day.vwap) >= ks * day.sig)]
                if not len(cand): continue
                i = int(cand.index[0])
                if i + 2 >= len(day): continue
                e = day.iloc[i]; entry = float(day.iloc[i + 1].open); side = -side_ev
                atr5 = float(e.atr14) if np.isfinite(e.atr14) and e.atr14 > 0 else 0.0
                vw, sg = float(e.vwap), float(e.sig)
                stop = vw + side_ev * (ks + 1) * sg
                path = day.iloc[i + 1:]
                for tg_name, tgt in (("vwap", vw), ("half", (entry + vw) / 2)):
                    x, how = scan(path, side, entry, stop, tgt)
                    rows.append(row(k, idx, side, entry, x, how, cost, atr_d, atr5, dict(k=ks, tgt=tg_name, ex="tp", cont=False)))
                # read-only mirror: continuation (same stop distance, target k+1 sigma outward) and no-stop fade
                x, how = scan(path, -side, entry, vw + side_ev * (ks - 1) * sg, vw + side_ev * (ks + 1) * sg)
                rows.append(row(k, idx, -side, entry, x, how, cost, atr_d, atr5, dict(k=ks, tgt="cont", ex="mirror", cont=True)))
                x, how = scan(path, side, entry, None, vw)
                rows.append(row(k, idx, side, entry, x, how, cost, atr_d, atr5, dict(k=ks, tgt="vwap_nostop", ex="ro", cont=False)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ D. combination
def momentum_component(idx):
    d, b, cut = prep(idx); cost = E.MICRO[idx]; rows = []
    for k, day in b.groupby("skey"):
        o = day[day.hm == 930]; t10 = day[day.hm == 1000]; x = day[day.hm == 1555]; pre = day[(day.hm >= 930) & (day.hm < 1000)]
        if len(o) != 1 or len(t10) != 1 or len(x) != 1 or not len(pre) or not np.isfinite(day.atr_d.iloc[0]): continue
        p = float(pre.close.iloc[-1] - o.open.iloc[0])                 # attempt-2 predictor: first-30-min return (09:55 close - 09:30 open)
        if p == 0: continue
        side = int(np.sign(p)); rows.append(row(k, idx, side, float(t10.open.iloc[0]), float(x.close.iloc[0]), "time", cost, float(day.atr_d.iloc[0]), 0.0))
    return pd.DataFrame(rows)


def combination(A_rows, B_rows, E_rows, mom_rows, live):
    """Equal-weight portfolio of three pre-specified components. Each component's daily series = mean R over the
    instruments live that date (0 for a live instrument without a trade); window = the common live window."""
    def daily(df, name):
        if df is None or not len(df): return pd.Series(dtype=float, name=name)
        return (df.groupby("date").R.sum() / live.reindex(df.groupby("date").R.sum().index)).rename(name)
    comps = dict(momentum=daily(mom_rows, "momentum"),
                 reversal=daily(E_rows[(E_rows.k == 2.0) & (E_rows.tgt == "vwap")], "reversal"),
                 volbreak=daily(B_rows[(B_rows.pc == 10) & (B_rows["mult"] == 2.0) & (B_rows.ex == "sess")], "volbreak"))
    start = max(c.index.min() for c in comps.values() if len(c)); end = min(c.index.max() for c in comps.values() if len(c))
    M = pd.concat(comps.values(), axis=1).reindex(live.index).fillna(0.0).sort_index()
    M = M[(M.index >= start) & (M.index <= end)]
    M["combo"] = M[["momentum", "reversal", "volbreak"]].sum(axis=1) / 3
    out = {c: dict(mean_R_per_day=float(M[c].mean()), sharpe_daily=float(M[c].mean() / M[c].std(ddof=1)) if M[c].std(ddof=1) > 0 else None,
                   ann_sharpe=float(M[c].mean() / M[c].std(ddof=1) * np.sqrt(252)) if M[c].std(ddof=1) > 0 else None,
                   active_days=int((M[c] != 0).sum())) for c in M.columns}
    out["corr"] = M[["momentum", "reversal", "volbreak"]].corr().round(3).to_dict()
    out["days"] = int(len(M)); out["window"] = [str(start), str(end)]; out["live_instruments_mean"] = float(live.reindex(M.index).mean())
    return out


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    IDX = ("SPX", "NDX", "RTY", "GOLD")
    res = {"unsealed": UNSEAL}
    A_all, A_meas, A_ctl, B_all, E_all, M_all = [], [], [], [], [], []
    for idx in IDX:
        try:
            a, m, c = battery_A(idx); A_all.append(a); A_meas.append(m); A_ctl.append(c); print(f"A {idx}: events {len(m)}, trade rows {len(a)}")
        except Exception as ex:
            print(f"A {idx}: skipped ({ex})")
        bb = battery_B(idx); B_all.append(bb); print(f"B {idx}: trade rows {len(bb)}")
        ee = battery_E(idx); E_all.append(ee); print(f"E {idx}: trade rows {len(ee)}")
        M_all.append(momentum_component(idx))
    srt = lambda df: pd.concat(df).sort_values("date", kind="stable").reset_index(drop=True)
    A = srt(A_all); AM = srt(A_meas); ACd = srt(A_ctl); AC = ACd.v.values; B = srt(B_all); EE = srt(E_all); MM = srt(M_all)
    live = pd.concat([pd.Series(1, index=[str(k) for k in E.sessions(i)[0].index]) for i in IDX]).groupby(level=0).sum()

    # ---- A: measures
    resA = {"measure_fwd30_r5": {}}
    for name, m in (("rvol>=2", AM), ("rvol>=3", AM[AM.rv3]), ("rvol>=2 & range>=2ATR", AM[AM.big]), ("rvol>=3 & range>=2ATR", AM[AM.rv3 & AM.big])):
        s = stats(m.fwd30_r5); hyp = 0.46 if "3" in name else 0.34
        s["t_vs_user_hypothesis"] = float((m.fwd30_r5.mean() - hyp) / m.fwd30_r5.std(ddof=1) * np.sqrt(len(m))) if len(m) > 10 else None
        s["user_hypothesis_r"] = hyp; s["fwd30_abs_range_r5_mean"] = float(m.fwd30_abs_r5.mean()) if len(m) else None
        resA["measure_fwd30_r5"][name] = s
    resA["control_rvol<1.25_fwd30_r5"] = stats(AC)
    resA["clock_split_fwd30_r5"] = {c: stats(g.fwd30_r5) for c, g in AM.groupby("clock")}
    resA["onhour_split_fwd30_r5"] = {str(c): stats(g.fwd30_r5) for c, g in AM.groupby("onhour")}
    # NESTED cells (the registered grid): rv2 = all RVOL >= 2 events (rv3 is a subset); any = no range condition (big is a subset)
    parts = []
    for rv, mrv in (("rv2", np.ones(len(A), bool)), ("rv3", A.rv3.values)):
        for rc, mrc in (("any", np.ones(len(A), bool)), ("big", A.big.values)):
            pp = A[mrv & mrc].copy(); pp["cell"] = f"{rv}_{rc}_" + pp.ex; parts.append(pp)
    A = pd.concat(parts).sort_values("date", kind="stable").reset_index(drop=True)
    resA["cells"] = {c: cell_stats(g) for c, g in A.groupby("cell")}
    resA["clock_split_cells_x1"] = {f"{c}|{cl}": stats(g.R) for (c, cl), g in A.groupby(["cell", "clock"])}
    base_cell = A[A.cell == "rv2_any_t30"]
    resA["mirror_x1"] = stats((-base_cell.pnl - base_cell.instr.map(E.MICRO)) / (base_cell.pnl / base_cell.R0).where(base_cell.R0 != 0))
    print("\n=== A: forward 30-min signed move in 5m-ATR14 units ==="); [print(f"  {k}: {v}") for k, v in resA["measure_fwd30_r5"].items()]
    print("  control:", resA["control_rvol<1.25_fwd30_r5"]); print("  clock:", {k: (v.get('n'), round(v.get('mean', 0), 3)) for k, v in resA["clock_split_fwd30_r5"].items()})
    print("=== A cells (net R):"); [print(f"  {k:16s} n {v['x1'].get('n')} gross {v['x0_gross'].get('mean', 0):+.4f} net {v['x1'].get('mean', 0):+.4f} t {v['x1'].get('t') or 0:+.2f} halves {v['x1'].get('halves')} x2 {v['x2'].get('mean', 0):+.4f} exits {v['how']}") for k, v in resA["cells"].items()]
    resA["judge"] = judge(resA["cells"], A, 2.86, "A VOLUME")
    res["A"] = resA

    # ---- B
    B["cell"] = "p" + B.pc.astype(str) + "_m" + B["mult"].astype(str) + "_" + B.ex
    resB = {"cells": {c: cell_stats(g) for c, g in B.groupby("cell")}}
    resB["open_trigger_split_x1"] = {f"{c}|open={o}": stats(g.R) for (c, o), g in B.groupby(["cell", "at_open"])}
    resB["clock_split_x1"] = {f"{c}|{cl}": stats(g.R) for (c, cl), g in B.groupby(["cell", "clock"])}
    print("\n=== B cells (net R):"); [print(f"  {k:16s} n {v['x1'].get('n')} gross {v['x0_gross'].get('mean', 0):+.4f} net {v['x1'].get('mean', 0):+.4f} t {v['x1'].get('t') or 0:+.2f} halves {v['x1'].get('halves')} x2 {v['x2'].get('mean', 0):+.4f} exits {v['how']}") for k, v in resB["cells"].items()]
    resB["judge"] = judge(resB["cells"], B, 2.73, "B COMPRESSION")
    res["B"] = resB

    # ---- E
    sel = EE[EE.ex == "tp"].copy(); sel["cell"] = "k" + sel.k.astype(str) + "_" + sel.tgt
    resE = {"cells": {c: cell_stats(g) for c, g in sel.groupby("cell")}}
    resE["mirror_continuation_x1"] = {f"k{k}": stats(g.R) for k, g in EE[EE.ex == "mirror"].groupby("k")}
    resE["nostop_fade_x1"] = {f"k{k}": stats(g.R) for k, g in EE[EE.ex == "ro"].groupby("k")}
    print("\n=== E cells (net R):"); [print(f"  {k:14s} n {v['x1'].get('n')} gross {v['x0_gross'].get('mean', 0):+.4f} net {v['x1'].get('mean', 0):+.4f} t {v['x1'].get('t') or 0:+.2f} halves {v['x1'].get('halves')} x2 {v['x2'].get('mean', 0):+.4f} exits {v['how']}") for k, v in resE["cells"].items()]
    print("  mirror:", {k: (v.get('n'), round(v.get('mean', 0), 4)) for k, v in resE["mirror_continuation_x1"].items()})
    resE["judge"] = judge(resE["cells"], sel, 2.64, "E VWAP")
    res["E"] = resE

    # ---- D
    res["D_combination"] = combination(A, B, EE, MM, live)
    res["notes"] = ["GOLD E: VWAP/sigma reset at 09:30 NY on a 24h instrument (overnight volume excluded); atr_d = RTH-range ATR20",
                    "A/E volume cells 2010+ (VOL_START); B full sample (price-only)",
                    "holdout NOT opened: no 2026 Dukascopy path in this runner; a cleared cell needs run_r77_unseal.py",
                    "A t30 windows = 6 contiguous in-session bars spanning exactly 30 clock minutes; others voided",
                    "E stop = (k+1) sigma with sigma frozen at the event bar; D momentum predictor = 09:55 close - 09:30 open"]
    print("\n=== D combination:", json.dumps(res["D_combination"], default=float))
    json.dump(res, open(os.path.join(HERE, "results", "r77_battery_is.json"), "w"), indent=1, default=float)
