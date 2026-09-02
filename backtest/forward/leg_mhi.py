"""MHI leg of the forward auto-journal (see CONTRACT.md).

Frozen rule: run_hsi.py H-A fade, cell t0.3_s0.5_c1600.  This module is a line-for-line
transcription of run_hsi.py lines 59-118 (daily range / ATR14 with shift(1), the 01:15 UTC
pre bar, the 01:30..08:00 UTC session, the per-15m-bar stop check, else the last close
before 08:00 UTC), restricted to the one frozen cell and emitting journal rows instead of
P&L.  Costs are NOT subtracted here (the page / monthly review applies them).

Input: <data_dir>/hk33_m15.csv, same format as backtest/data/HK33_M15.csv -- first column
a UTC timestamp, then open, high, low, close[, volume].  Verified against the archived
backtest by test_leg_mhi.py.
"""
import os

import numpy as np
import pandas as pd

INSTR = "MHI"
TRIG = 0.3        # |push| / ATR14 threshold
STOP_K = 0.5      # stop = pre_hi + STOP_K*pre_rng (short) / pre_lo - STOP_K*pre_rng (long)
PRE_HM = 115      # 01:15 UTC 15m bar = 09:15 HKT derivatives open
OPEN_HM = 130     # 01:30 UTC = 09:30 HKT cash open (entry bar)
END_HM = 800      # session bars are hm >= OPEN_HM and hm < END_HM (exit "c1600")
C1030_HM = 230    # run_hsi.py drops days with no bar before 02:30 UTC (c1030 NaN)
MIN_SESS_BARS = 15
ATR_N = 14
HKT = pd.Timedelta(hours=8)


def load(data_dir):
    """run_hsi.py lines 31-33, 42: first column -> UTC index, OHLC, sorted, deduped."""
    path = os.path.join(data_dir, "hk33_m15.csv")
    b = pd.read_csv(path)
    b["ts"] = pd.to_datetime(b.iloc[:, 0], utc=True)
    b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()
    b = b[~b.index.duplicated()]
    return b


def _prepare(H):
    """run_hsi.py lines 46-47, 61-62."""
    H = H.copy()
    H["d"] = H.index.date
    H["hm"] = H.index.hour * 100 + H.index.minute
    daily_rng = H.groupby("d").high.max() - H.groupby("d").low.min()
    atr14 = daily_rng.rolling(ATR_N).mean().shift(1)
    return H, atr14


def _session_complete(H, d):
    """Forward-only guard: the file is live-updated, so a session whose 08:00 UTC has not
    yet been reached must not be journalled (its 'last close before 08:00' is unknown).
    On a finished history every day passes, so this is a no-op on the archived data."""
    return H.index.max() >= pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=END_HM // 100,
                                                                     minutes=END_HM % 100)


def _trades(H, require_complete=True):
    """Yield one dict per triggered day, following run_hsi.py lines 69-118 exactly."""
    H, atr14 = _prepare(H)
    for d, day in H.groupby("d"):
        pre = day[day.hm == PRE_HM]
        if not len(pre) or d not in atr14 or not np.isfinite(atr14[d]):
            continue
        sess = day[(day.hm >= OPEN_HM) & (day.hm < END_HM)]
        if len(sess) < MIN_SESS_BARS:
            continue
        if not len(sess[sess.hm < C1030_HM]):      # A.dropna(subset=["c1030", "c1600"])
            continue
        if require_complete and not _session_complete(H, d):
            continue
        push = pre.close.iloc[0] - pre.open.iloc[0]
        pre_hi, pre_lo = pre.high.iloc[0], pre.low.iloc[0]
        pre_rng = pre_hi - pre_lo
        push_n = push / atr14[d]                   # A["push_n"] = A.push / A.atr
        if not (np.abs(push_n) >= TRIG):           # sub = A[np.abs(A.push_n) >= trig]
            continue
        sgn = -np.sign(push)
        e = sess.open.iloc[0]                      # o930 = 01:30 UTC bar open
        stop = (pre_hi + STOP_K * pre_rng) if sgn < 0 else (pre_lo - STOP_K * pre_rng)
        res = None
        for _, bb in sess.iterrows():              # day[day.hm < 800] == sess
            if (sgn < 0 and bb.high >= stop) or (sgn > 0 and bb.low <= stop):
                res = stop
                break
        px = res if res is not None else sess.close.iloc[-1]   # c1600
        yield dict(d=d, t_entry=sess.index[0], sgn=int(sgn), push=float(push),
                   push_n=float(push_n), atr=float(atr14[d]), entry=float(e),
                   stop=float(stop), exit=float(px), stopped=res is not None)


def rows(data_dir, require_complete=True):
    """Journal rows per CONTRACT.md for every triggered, completed session in the file."""
    H = load(data_dir)
    out = []
    for t in _trades(H, require_complete=require_complete):
        out.append(dict(
            date=(t["t_entry"] + HKT).date().isoformat(),
            instr=INSTR,
            side="S" if t["push"] > 0 else "L",
            entry=t["entry"],
            stop=t["stop"],
            exit=t["exit"],
            note="fade|" + ("stop" if t["stopped"] else "time"),
            src="auto",
        ))
    return out


def status(data_dir):
    """One line for the monthly report: data extent and the latest session's trigger state.
    The leg is intraday only, so there is never an open position to carry."""
    H = load(data_dir)
    Hp, atr14 = _prepare(H)
    last = H.index.max()
    d = last.date()
    pre = Hp[(Hp.d == d) & (Hp.hm == PRE_HM)]
    line = f"MHI: data to {last.isoformat()}; no overnight position (intraday leg)"
    if len(pre) and d in atr14 and np.isfinite(atr14[d]):
        push = pre.close.iloc[0] - pre.open.iloc[0]
        pn = push / atr14[d]
        line += (f"; last session {d.isoformat()} push {push:+.1f} = {pn:+.2f} ATR14 "
                 f"({'TRIGGER' if abs(pn) >= TRIG else 'no trigger'})"
                 f"{'' if _session_complete(Hp, d) else ' [session incomplete]'}")
    return line


if __name__ == "__main__":
    import sys
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "forward")
    for r in rows(dd):
        print(r)
    print(status(dd))
