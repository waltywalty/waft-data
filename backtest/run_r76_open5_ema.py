"""Round 76 commissioned audit: first 5-minute candle of the 09:30 NY session + 12 EMA filter.

User spec (2026-09-13): after the 09:30-09:35 candle closes, if it closes up (close > open) AND
above the 12-period EMA of 5m closes -> long; closes down AND below the EMA -> short; else no
trade. Entry = open of the 09:35 bar. Stops / targets grid (frozen):
  SL = the candle's opposite extreme (low for longs, high for shorts) minus a buffer b x range,
       b in {0, 0.5, 1.0};  TP = k x risk (risk = entry - stop), k in {1, 2, 3, none};
  time exit = close of the 15:55 bar if neither hits; worst-case stop-first on each bar.
12 cells per instrument; instruments SPX / NDX / RTY / GOLD (MES/MNQ/M2K/MGC micro costs),
pooled in R = (pnl - cost)/ATR20 (the intraday-engine convention) and in net risk units ((pnl - cost)/risk).
Sessions without the 15:55 bar (holidays, half days) are VOIDED; a stop touch (<= / >=) fills at the stop
price, including an exact re-touch of the candle extreme on the entry bar with b = 0 (tagged stop_entry).
EMA12 is computed on the 5m close series of the 24h frame (a chart's EMA); the RTH-only EMA is a
read-only variant. IS = the engine's stored cuts (Oanda-era frames); the 2020+ MT5 block is
attempt-1-seen (read-only, never a shot); the SEALED holdout is the 2026 block of the Dukascopy
1m frames (USA500 / USATECH / XAUUSD), opened only by the integrator (UNSEAL_OK=1 --unseal).
Multiple testing: max-|t| sign-flip randomisation over the 12 pooled cells (2,000 draws) and
Bonferroni x12. Outputs results/r76_open5_ema_is.json (or _oos.json).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday_engine as E  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
BUFFERS = (0.0, 0.5, 1.0)
TPS = (1.0, 2.0, 3.0, None)
EMA_N = 12
RNG = np.random.default_rng(76)


def ema12(close):
    return close.ewm(span=EMA_N, adjust=False).mean()


VOID = {}


def trades_for_frame(b5, d, cost, label, ema_rth_only=False, require_ema=True, require_sign=True):
    """b5: 5m frame (NY tz, cols open/high/low/close, skey, hm); d: session table with atr20."""
    src = b5[(b5.hm >= 930) & (b5.hm <= 1555)] if ema_rth_only else b5
    ema = ema12(src.close)
    b5 = b5.assign(ema=ema.reindex(b5.index))
    rows = []
    for key, day in b5.groupby("skey"):
        if key not in d.index:
            continue
        atr = d.atr20.get(key, np.nan)
        if not (np.isfinite(atr) and atr > 0):
            continue
        c0 = day[day.hm == 930]; e0 = day[day.hm == 935]
        if len(c0) != 1 or len(e0) != 1:
            continue
        c0 = c0.iloc[0]
        if not np.isfinite(c0.ema):
            continue
        rng = float(c0.high - c0.low)
        if rng <= 0:
            continue
        up_sign, dn_sign = c0.close > c0.open, c0.close < c0.open
        up_ema, dn_ema = c0.close > c0.ema, c0.close < c0.ema
        ok_up = (up_sign or not require_sign) and (up_ema or not require_ema)
        ok_dn = (dn_sign or not require_sign) and (dn_ema or not require_ema)
        if require_sign and require_ema:
            side = 1 if (up_sign and up_ema) else (-1 if (dn_sign and dn_ema) else 0)
        elif require_sign:
            side = 1 if up_sign else (-1 if dn_sign else 0)
        else:
            side = 1 if up_ema else (-1 if dn_ema else 0)
        if side == 0:
            continue
        entry = float(e0.open.iloc[0])
        path = day[(day.hm >= 935) & (day.hm <= 1555)]
        if len(path) < 2 or int(path.hm.iloc[-1]) != 1555:
            VOID["no_1555_bar"] = VOID.get("no_1555_bar", 0) + 1       # holidays / half days: voided (spec: exit = 15:55 close)
            continue
        if "nmin" in day.columns and int(c0.nmin) < 5:
            VOID["partial_0930_bin"] = VOID.get("partial_0930_bin", 0) + 1
            continue
        for bfr in BUFFERS:
            stop = (c0.low - bfr * rng) if side == 1 else (c0.high + bfr * rng)
            risk = side * (entry - stop)
            if risk <= 0:
                continue
            for k in TPS:
                tgt = entry + side * k * risk if k else None
                exit_px, how = float(path.close.iloc[-1]), "time"
                for i_bar, (_, bar) in enumerate(path.iterrows()):
                    # a touch of the stop level (<= / >=) is a stop fill at the stop price - a resting stop order;
                    # with b = 0 an exact re-touch of the candle extreme on the 09:35 bar counts (tagged stop_entry)
                    if (side == 1 and bar.low <= stop) or (side == -1 and bar.high >= stop):
                        exit_px, how = stop, ("stop_entry" if i_bar == 0 else "stop"); break
                    if tgt is not None and ((side == 1 and bar.high >= tgt) or (side == -1 and bar.low <= tgt)):
                        exit_px, how = tgt, "target"; break
                pnl = side * (exit_px - entry)
                rows.append(dict(date=str(key), instr=label, side=side, b=bfr, tp=(k or 0), how=how, pnl=pnl, risk=risk, atr=atr,
                                 R0=pnl / atr, R=(pnl - cost) / atr, R15=(pnl - 1.5 * cost) / atr, R20=(pnl - 2 * cost) / atr,
                                 Rr=(pnl - cost) / risk))
    return pd.DataFrame(rows)


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), wr=float((x > 0).mean()), pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                mean=float(x.mean()), t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def cell_table(t):
    out = {}
    for (bfr, k), g in t.groupby(["b", "tp"]):
        g = g.sort_values("date")
        out[f"b{bfr}_tp{int(k) if k else 'none'}"] = dict(x0_gross=stats(g.R0), x1=stats(g.R), x15=stats(g.R15), x2=stats(g.R20), risk_units_net=stats(g.Rr),
                                                          how=g.how.value_counts().to_dict(), n_days=int(g.date.nunique()),
                                                          long_share=float((g.side > 0).mean()),
                                                          per_year_sign={int(y): float(np.sign(gg.R.mean())) for y, gg in g.groupby(pd.to_datetime(g.date).dt.year)})
    return out


def maxstat(t, draws=2000):
    """Sign-flip randomisation of the TRADE-LEVEL per-cell t (the same statistic as cell_table): one sign per
    date, applied to every trade of that date across instruments and cells, so same-day cross-instrument
    correlation is preserved under the null. Returns the distribution of the max |t| over the 12 cells."""
    t = t.copy(); t["cell"] = t.b.astype(str) + "_" + t.tp.astype(str)
    dates = np.array(sorted(t.date.unique())); di = {d: i for i, d in enumerate(dates)}
    t["di"] = t.date.map(di)
    cells = sorted(t.cell.unique())
    R = {c: (t.loc[t.cell == c, "R"].values, t.loc[t.cell == c, "di"].values) for c in cells}
    def tstat(x):
        return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 and x.std(ddof=1) > 1e-12 else 0.0
    obs = {c: tstat(R[c][0]) for c in cells}
    mx = []
    for _ in range(draws):
        sgn = RNG.choice([-1.0, 1.0], size=len(dates))
        mx.append(max(abs(tstat(R[c][0] * sgn[R[c][1]])) for c in cells))
    mx = np.array(mx); best = max(obs, key=lambda c: abs(obs[c]))
    return dict(observed_max_abs_t=float(abs(obs[best])), p_max=float((np.sum(mx >= abs(obs[best])) + 1) / (draws + 1)), best_cell=best,
                best_cell_t=float(obs[best]), draws=draws, statistic="trade-level t, per-date sign flips shared across instruments and cells",
                obs_t={c: float(v) for c, v in obs.items()}), mx


def run_is():
    res = {"unsealed": False, "instruments": {}}
    allt = []
    for idx in ("SPX", "NDX", "RTY", "GOLD"):
        d, b, cut = E.sessions(idx, unseal=False)
        t = trades_for_frame(b, d, E.MICRO[idx], idx)
        assert not d.oos.any() and (pd.to_datetime(t.date) < pd.Timestamp(cut)).all()   # firewall = the frame cut in sessions()
        allt.append(t)
        res["instruments"][idx] = dict(cut=str(cut), cells=cell_table(t), n_signal_days=int(t.date.nunique()))
        print(f"{idx}: IS to {cut}, signal days {t.date.nunique()}")
    T = pd.concat(allt)
    res["voided_sessions"] = dict(VOID)
    res["pooled_cells"] = cell_table(T)
    res["pooled_maxstat"], MX = maxstat(T)
    res["pooled_bonferroni_t_floor"] = 2.86   # two-sided 5% / 12 -> z 2.86
    # read-only variants on the pooled base cell b0/tp none: RTH-only EMA; no EMA filter (candle sign only); EMA-only (ignore candle sign)
    d, b, cut = E.sessions("SPX", unseal=False)
    res["variant_rth_ema_SPX_b0_tpnone"] = stats(trades_for_frame(b, d, E.MICRO["SPX"], "SPX", ema_rth_only=True).query("b == 0 and tp == 0").R)
    res["variant_sign_only_SPX_b0_tpnone"] = stats(trades_for_frame(b, d, E.MICRO["SPX"], "SPX", require_ema=False).query("b == 0 and tp == 0").R)
    res["variant_ema_only_SPX_b0_tpnone"] = stats(trades_for_frame(b, d, E.MICRO["SPX"], "SPX", require_sign=False).query("b == 0 and tp == 0").R)
    # per-cell printout
    print("\nPOOLED IS cells (R = (pnl - micro cost)/ATR20):")
    for k, v in res["pooled_cells"].items():
        x1 = v["x1"]; print(f"  {k:12s} n {x1.get('n',0):5d} WR {x1.get('wr',0)*100:5.1f}% PF {x1.get('pf',0):5.2f} gross {v['x0_gross'].get('mean',0):+.4f} net {x1.get('mean',0):+.4f} t {x1.get('t') or 0:+6.2f} halves {x1.get('halves')} | x2 {v['x2'].get('mean',0):+.4f} | risk-units {v['risk_units_net'].get('mean',0):+.3f}R | exits {v['how']}")
    print("max-stat:", res["pooled_maxstat"])
    best = max(res["pooled_cells"].items(), key=lambda kv: (kv[1]["x1"].get("t") or -99))
    bx = best[1]; t_best = bx["x1"].get("t") or 0.0
    p_best = float((np.sum(MX >= abs(t_best)) + 1) / (len(MX) + 1))      # single-step max-stat adjusted p for the bar cell
    res["bar_cell_maxstat_p"] = p_best
    # gradient marginals: mean net R by buffer and by target; lone-spike flag = best exceeds every neighbour by > 1 SE
    marg_b = {str(bfr): float(T[T.b == bfr].R.mean()) for bfr in BUFFERS}
    marg_k = {str(k or "none"): float(T[T.tp == (k or 0)].R.mean()) for k in TPS}
    se = bx["x1"]["mean"] / t_best if t_best else float("nan")
    others = [v["x1"]["mean"] for k2, v in res["pooled_cells"].items() if k2 != best[0]]
    res["gradient"] = dict(by_buffer=marg_b, by_target=marg_k, best_minus_next=float(bx["x1"]["mean"] - max(others)) if others else None,
                           best_se=float(se), lone_spike=bool(others and (bx["x1"]["mean"] - max(others)) > se))
    PASS = (bx["x1"].get("n", 0) >= 40 and bx["x1"].get("mean", -1) > 0 and t_best >= 2.86 and bx["x1"].get("pf", 0) >= 1.15
            and bx["x1"].get("halves") == [1.0, 1.0] and bx["x2"].get("mean", -1) > 0 and p_best < 0.05 and not res["gradient"]["lone_spike"])
    res["best_cell"] = best[0]; res["IS_pass"] = bool(PASS)
    print("gradient:", res["gradient"]); print("bar-cell max-stat p:", p_best)
    print(f"\nROUND 76 IS VERDICT: {'PASS' if PASS else 'FAIL'} (best cell {best[0]} t {t_best:+.2f}; needs n>=40, t>=2.86 Bonferroni, bar-cell max-stat p<0.05, PF>=1.15, halves [+,+], positive at 2x, no lone spike)")
    json.dump(res, open("results/r76_open5_ema_is.json", "w"), indent=1, default=float)


def load_duka_5m(path, label):
    """Dukascopy 1m -> NY-time 5m bars with the engine's session key and ATR20 (RTH range)."""
    d = pd.read_csv(path, parse_dates=["time"]).set_index("time"); d = d[d.volume > 0].tz_convert("America/New_York")
    b5 = d.resample("5min", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), nmin=("close", "size")).dropna()
    b5 = b5[b5.index.dayofweek < 5].copy()
    b5["skey"] = (b5.index + pd.Timedelta(hours=8)).date; b5["hm"] = b5.index.hour * 100 + b5.index.minute
    rth = b5[(b5.hm >= 930) & (b5.hm <= 1555)]
    dd = rth.groupby("skey").agg(hi=("high", "max"), lo=("low", "min"))
    dd["atr20"] = (dd.hi - dd.lo).rolling(20).mean().shift(1)
    return b5, dd


def run_oos():
    """SEALED 2026 holdout on the Dukascopy 1m frames (S&P, Nasdaq, gold), the single best IS cell only."""
    is_res = json.load(open("results/r76_open5_ema_is.json"))
    if not is_res.get("IS_pass"):
        sys.exit("IS bar not cleared; the holdout stays sealed")
    cell = is_res["best_cell"]; bfr = float(cell.split("_")[0][1:]); tpk = cell.split("_tp")[1]; k = None if tpk == "none" else float(tpk)
    res = {"unsealed": True, "cell": cell, "instruments": {}, "RTY": "no 2026 Dukascopy frame; no holdout (ledger Round 76)"}
    allt = []
    for path, label, cost in (("data/idx/dukascopy/USA500IDXUSD_1m.csv", "SPX", E.MICRO["SPX"]), ("data/idx/dukascopy/USATECHIDXUSD_1m.csv", "NDX", E.MICRO["NDX"]),
                              ("data/fx/dukascopy/XAUUSD_1m.csv", "GOLD", E.MICRO["GOLD"])):
        b5, dd = load_duka_5m(path, label)
        t = trades_for_frame(b5, dd, cost, label)
        t = t[(t.b == bfr) & (t.tp == (k or 0)) & (pd.to_datetime(t.date) >= "2026-01-01")]
        allt.append(t); res["instruments"][label] = stats(t.sort_values("date").R)
    T = pd.concat(allt).sort_values("date")
    res["pooled"] = dict(x1=stats(T.R), x15=stats(T.R15), x2=stats(T.R20), risk_units=stats(T.Rr), how=T.how.value_counts().to_dict())
    print(json.dumps(res, indent=1, default=float))
    json.dump(res, open("results/r76_open5_ema_oos.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    run_oos() if UNSEAL else run_is()
