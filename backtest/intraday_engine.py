"""Generic intraday event-window engine for the intraday program (Rounds 70+).

One spec = one clock-anchored window per session on one instrument: at most one trade per
session per spec by construction (the user's 0-2 trades/day band is met by running at most
two specs per instrument). Every registered family is expressed as cells of this form:

    cell = dict(instr="SPX", entry="09:35", exit="10:30", direction=+1,   # +1 long, -1 short
                days=None,          # None = every session, or a set of datetime.date, or a
                                    # callable(session_frame, date) -> bool / direction / None
                stop=None,          # None, or ("range", k, "HH:MM", "HH:MM") = k x range of that
                                    # clock window, or ("atr", k) = k x daily ATR20; worst-case
                                    # stop-first on the 5m bars
                target=None)        # None or ("range", k, ...) / ("atr", k), touch-first fill

Returns per trade: R = direction * (exit - entry) - cost, all divided by the session's ATR20
(daily, shift(1)), costs = MICRO round trips; cost sensitivities x1.5 and x2 are always
reported (intraday bar: positive at 2x). Entry/exit prints are the OPEN of the 5m bar that
starts at the clock time (entry) and the CLOSE of the bar that ends at the exit clock; a
missing bar voids the trade (no fill assumed). Clock times are America/New_York.

OOS FIREWALL: IS = the first 75% of each instrument's sessions; OOS sessions are dropped at
frame build unless unseal=True is passed by the integrator (UNSEAL_OK=1 --unseal).

Frames: SPX/NDX/RTY 5m CFD (index_data, 2005-2025; RTY 2005-2020), GOLD 5m 2020-08+
(data/XAUUSD_5m.csv), all converted to New York time; session key = calendar date in NY for
bars from 18:00 the previous evening ("skey" = (ts + 8h).date, as in run_r37_scalps.py).
"""
import datetime as dt
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import index_data  # noqa: E402

MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
IS_FRAC = 0.75
_CACHE = {}


def load_frame(idx):
    if idx in _CACHE:
        return _CACHE[idx]
    if idx == "GOLD":
        g = pd.read_csv(os.path.join(HERE, "data", "XAUUSD_5m.csv"))
        g["ts"] = pd.to_datetime(g.Date.astype(str) + g.Time, format="%Y%m%d%H:%M:%S", utc=True)
        b = g.set_index("ts").rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].sort_index()
    else:
        b = index_data.load(idx)
    b = b.tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5].copy()
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date
    b["hm"] = b.index.hour * 100 + b.index.minute
    _CACHE[idx] = b
    return b


def sessions(idx, unseal=False):
    """Per-session table: RTH open/close/high/low, ATR20 (shift 1), is_oos; OOS rows dropped
    unless unseal. Also returns the 5m frame restricted to non-OOS sessions."""
    b = load_frame(idx)
    rth = b[(b.hm >= 930) & (b.hm <= 1555)]
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"), hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    keys = d.index.tolist()
    cut = keys[int(len(keys) * IS_FRAC)]
    d["oos"] = np.array([k >= cut for k in keys])
    if not unseal:
        d = d[~d.oos]
        b = b[[k < cut for k in b.skey]]
    return d, b, cut


def _hm(s):
    h, m = s.split(":")
    return int(h) * 100 + int(m)


def _bar_at(day, hm):
    x = day[day.hm == hm]
    return x.iloc[0] if len(x) else None


def _window_range(day, a, b):
    w = day[(day.hm >= _hm(a)) & (day.hm < _hm(b))]
    if not len(w):
        return np.nan
    return float(w.high.max() - w.low.min())


def run_cell(cell, unseal=False, cost_mult=1.0):
    """Return a DataFrame of trades (one row per session traded) for the cell."""
    idx = cell["instr"]
    d, b, cut = sessions(idx, unseal)
    ehm, xhm = _hm(cell["entry"]), _hm(cell["exit"])
    days = cell.get("days")
    rows = []
    for key, day in b.groupby("skey"):
        if key not in d.index:
            continue
        atr = d.atr20.get(key, np.nan)
        if not (np.isfinite(atr) and atr > 0):
            continue
        direction = cell.get("direction", 0)
        if days is not None:
            if callable(days):
                # the callable sees ONLY bars that closed before the entry clock (no lookahead by
                # construction; the attempt-15 / r38 rule) - for a wrapped window that is the prior
                # evening's bars up to the entry, i.e. everything with hm >= ehm is hidden as well
                r = days(day[day.hm < ehm] if ehm <= xhm else day[(day.hm < ehm) & (day.hm >= xhm)], key)
                if r is None or r is False:
                    continue
                if r in (1, -1):
                    direction = r
            elif key not in days:
                continue
        if direction not in (1, -1):
            continue
        eb = _bar_at(day, ehm)
        if eb is None:
            continue
        # exit bar = the last bar whose start < exit clock (its close is the exit print);
        # a window that crosses midnight (entry >= 18:00, exit next morning) lives inside one
        # session key because skey = (ts + 8h).date, and the frame is chronological
        path = day[(day.hm >= ehm) & (day.hm < xhm)] if ehm <= xhm else day[(day.hm >= ehm) | (day.hm < xhm)]
        if len(path) < 2:
            continue
        entry = float(eb.open)
        stop_px = tgt_px = None
        sp = cell.get("stop")
        if sp:
            if sp[0] == "range":
                rng = _window_range(day, sp[2], sp[3]); k = sp[1]
                if not np.isfinite(rng) or rng <= 0:
                    continue
                stop_px = entry - direction * k * rng
            elif sp[0] == "atr":
                stop_px = entry - direction * sp[1] * atr
        tg = cell.get("target")
        if tg:
            if tg[0] == "range":
                rng = _window_range(day, tg[2], tg[3]); k = tg[1]
                if not np.isfinite(rng) or rng <= 0:
                    continue
                tgt_px = entry + direction * k * rng
            elif tg[0] == "atr":
                tgt_px = entry + direction * tg[1] * atr
        exit_px, how = float(path.close.iloc[-1]), "time"
        for _, bar in path.iterrows():        # worst case: stop checked before target
            if stop_px is not None and ((direction > 0 and bar.low <= stop_px) or (direction < 0 and bar.high >= stop_px)):
                exit_px, how = stop_px, "stop"; break
            if tgt_px is not None and ((direction > 0 and bar.high >= tgt_px) or (direction < 0 and bar.low <= tgt_px)):
                exit_px, how = tgt_px, "target"; break
        pnl = direction * (exit_px - entry)
        rows.append(dict(date=key, instr=idx, dir=direction, entry=entry, exit=exit_px, how=how,
                         pnl=pnl, atr=atr, R=(pnl - cost_mult * MICRO[idx]) / atr,
                         R15=(pnl - 1.5 * MICRO[idx]) / atr, R20=(pnl - 2.0 * MICRO[idx]) / atr,
                         oos=bool(d.oos.get(key, False))))
    return pd.DataFrame(rows)


def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 10:
        return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]; m = len(r) // 2
    return dict(n=int(len(r)), wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avg_R=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def summarize(trades, label=""):
    """Pooled stats at 1x / 1.5x / 2x cost plus per-year sign; the intraday bar needs R20 > 0."""
    if trades is None or trades.empty:
        return dict(label=label, n=0)
    out = dict(label=label, x1=stats(trades.R), x15=stats(trades.R15), x2=stats(trades.R20),
               how=trades.how.value_counts().to_dict(),
               per_year={int(y): round(float(g.R.mean()), 3) for y, g in trades.groupby(pd.to_datetime(trades.date).dt.year)})
    return out


def fmt(s):
    if s.get("n", 0) < 10:
        return f"n {s.get('n', 0)} (too few)"
    return (f"n {s['n']:>5} WR {s['wr']*100:5.1f}% PF {s['pf']:5.2f} avgR {s['avg_R']:+.4f} "
            f"t {s['t']:+.2f} halves {s['halves']}")


def print_summary(sm):
    print(f"--- {sm.get('label','')} ---")
    if sm.get("n", 1) == 0:
        print("  no trades"); return
    for k in ("x1", "x15", "x2"):
        print(f"  cost {k:<3} {fmt(sm[k])}")
    print(f"  exits {sm['how']}  per-year avgR(x1) {sm['per_year']}")


def clears_intraday_bar(sm, n_min=40):
    x1, x2 = sm.get("x1", {}), sm.get("x2", {})
    return (x1.get("n", 0) >= n_min and (x1.get("avg_R") or -1) > 0 and (x1.get("t") or -9) >= 2
            and (x1.get("pf") or 0) >= 1.15 and x1.get("halves") == [1.0, 1.0] and (x2.get("avg_R") or -1) > 0)


if __name__ == "__main__":
    # structural self-test only: frames load, sessions count, no returns printed
    for idx in ("SPX", "NDX", "RTY", "GOLD"):
        try:
            d, b, cut = sessions(idx)
            print(f"{idx}: {len(d)} IS sessions to {d.index[-1]} (OOS from {cut} dropped); 5m bars {len(b)}")
        except Exception as e:
            print(f"{idx}: ERROR {e}")
