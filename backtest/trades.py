"""Canonical trade generator for the filtered rule, with optional stop and MAE tracking.

Rule: opening range of L minutes from 09:30 HKT; enter on the first candle to close
beyond it; hold to a session anchor; trade only when the rolling gold/AUDUSD
correlation is at or below a threshold.
"""
import pandas as pd, numpy as np, engine, audusd
from zoneinfo import ZoneInfo

def corr_series(gold, window=20):
    gd = gold.close.resample("1D").last().dropna()
    gd.index = gd.index.tz_localize(None).normalize()
    ad = audusd.daily_from_fred()
    ad.index = pd.to_datetime(ad.index).normalize()
    dj = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
                   axis=1, join="inner").dropna()
    return (dj.g.rolling(window).corr(dj.a)
            .reindex(pd.date_range(dj.index.min(), dj.index.max(), freq="D"))
            .ffill().shift(1))          # shift -> only data through yesterday

def generate(gold, L=60, exit_tz="America/New_York", exit_h=16, exit_m=0,
             stop_r=None, cost=0.30, entry_cutoff_ldn=None):
    """One row per trade.
    stop_r           = stop distance as a multiple of the range width.
    entry_cutoff_ldn = hour, London local, after which no new entry is taken. The EA
                       enforces this, so the research must too or the two are not the
                       same strategy."""
    from zoneinfo import ZoneInfo as _ZI
    bL = engine.resample(gold, L)
    rows = []
    for day, _ in gold.groupby(gold.index.date):
        t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30,
                          tz=ZoneInfo("Asia/Hong_Kong")).tz_convert("UTC")
        if t0 not in bL.index:
            continue
        hi, lo = float(bL.at[t0, "high"]), float(bL.at[t0, "low"])
        if hi <= lo:
            continue
        te = pd.Timestamp(day.year, day.month, day.day, exit_h, exit_m,
                          tz=ZoneInfo(exit_tz)).tz_convert("UTC")
        t_last = te
        if entry_cutoff_ldn is not None:
            cut = pd.Timestamp(day.year, day.month, day.day, entry_cutoff_ldn, 0,
                               tz=_ZI("Europe/London")).tz_convert("UTC")
            t_last = min(te, cut)
        fwd = bL.loc[t0 + pd.Timedelta(minutes=L):t_last]
        fwd = fwd[fwd.index + pd.Timedelta(minutes=L) <= t_last]
        sig = fwd[(fwd.close > hi) | (fwd.close < lo)]
        if not len(sig):
            continue
        t_b = sig.index[0]
        side = 1 if sig.iloc[0].close > hi else -1
        entry = float(sig.iloc[0].close)
        t_fill = t_b + pd.Timedelta(minutes=L)
        rng = hi - lo

        path = gold.loc[t_fill:te]
        exit_px, reason, t_out = None, "time", te
        stop_dist = stop_r * rng if stop_r is not None else np.nan
        if stop_r is not None and len(path):
            stop = entry - side * stop_r * rng
            hit = path[(path.low <= stop) if side == 1 else (path.high >= stop)]
            if len(hit):
                exit_px, reason, t_out = stop, "stop", hit.index[0]
                path = gold.loc[t_fill:t_out]
        if exit_px is None:
            exit_px = engine.price_at(gold, te)
            if exit_px is None:
                continue
        mae = 0.0
        if len(path):
            mae = float(max(0.0, (entry - path.low.min()) if side == 1
                                 else (path.high.max() - entry)))
        rows.append({"day": day, "t_fill": t_fill, "t_out": t_out, "side": side,
                     "entry": entry, "exit": exit_px, "range": rng, "reason": reason,
                     "stop_dist": stop_dist,
                     "pnl_oz": side * (exit_px - entry) - cost, "mae_oz": mae})
    return pd.DataFrame(rows)
