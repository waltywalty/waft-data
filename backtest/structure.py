"""Causal building blocks for the daily-structure / liquidity-sweep strategy:

  - fx_daily      : daily OHLC on the FX-session day (17:00 ET to 17:00 ET),
                    labelled by the session END date - the same convention,
                    for the same lookahead reason, as ny_orb.build_levels.
  - daily_bias    : a +1/0/-1 trend gate per trading day, shifted so the value
                    for day D is computable strictly from sessions that ended
                    on or before D-1 (i.e. before day D begins at 17:00 ET D-1).
  - build_levels  : every session high/low as a liquidity level with its
                    creation time and the time it was first traded through.
                    "Unswept at time t" is then a pure lookup: created before t
                    and first crossing not before t.
"""
from __future__ import annotations
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")


def fx_daily(bars5: pd.DataFrame) -> pd.DataFrame:
    ny_idx = bars5.index.tz_convert(NY)
    sess_id = pd.Series((ny_idx + pd.Timedelta(hours=7)).date, index=bars5.index)
    g = bars5.groupby(sess_id)
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(),
                      "low": g.low.min(), "close": g.close.last(), "n": g.size()})
    d = d[d.n > 50]
    d.index = pd.to_datetime(d.index)
    return d


def daily_bias(daily: pd.DataFrame, mode: str = "sma20") -> pd.Series:
    """Bias usable ON day D (index = FX-day date): +1 bullish, -1 bearish, 0 flat.
    Computed from closes up to and including D-1, then shifted onto D."""
    c = daily.close
    if mode == "sma20":
        s = c.rolling(20).mean()
        raw = pd.Series(np.where(c > s, 1, np.where(c < s, -1, 0)), index=c.index)
    elif mode == "mom20":
        raw = pd.Series(np.sign(c - c.shift(20)), index=c.index).fillna(0)
    elif mode == "hhll":
        # structure proper: the last 10 completed days put in both a higher high
        # and a higher low than the 10 before them (or lower for a downtrend)
        h1, l1 = daily.high.rolling(10).max(), daily.low.rolling(10).min()
        h0, l0 = h1.shift(10), l1.shift(10)
        raw = pd.Series(np.where((h1 > h0) & (l1 > l0), 1,
                        np.where((h1 < h0) & (l1 < l0), -1, 0)), index=c.index)
    else:
        raise ValueError(mode)
    return raw.shift(1).fillna(0).astype(int)


# session windows that generate liquidity levels, as (label, start_fn, end_fn)
def _asia_win(day):        # Tokyo cash hours, no DST
    a0 = day.tz_localize(UTC)
    return a0, a0 + pd.Timedelta(hours=6)


def _ldn_win(day):
    f = lambda h, m=0: pd.Timestamp(day.year, day.month, day.day, h, m, tz=LDN).tz_convert(UTC)
    return f(8), f(16, 30)


def _ny_win(day):
    f = lambda h, m=0: pd.Timestamp(day.year, day.month, day.day, h, m, tz=NY).tz_convert(UTC)
    return f(9, 30), f(16)


def build_levels(bars5: pd.DataFrame) -> pd.DataFrame:
    """One row per liquidity level: kind, side (+1 high / -1 low), price,
    t_created (the session's end - the level does not exist before the session
    is over), t_swept (open time of the first bar at or after t_created that
    trades through it; NaT if never)."""
    hi, lo = bars5.high.values, bars5.low.values
    idx = bars5.index
    rows = []

    def emit(kind, day, t0, t1):
        w = bars5.loc[t0:t1 - pd.Timedelta(minutes=5)]
        if len(w) < 30:
            return
        rows.append(dict(kind=kind + "H", side=1, price=float(w.high.max()), t_created=t1, day=day))
        rows.append(dict(kind=kind + "L", side=-1, price=float(w.low.min()), t_created=t1, day=day))

    days = pd.Series(bars5.index.date, index=bars5.index).unique()
    for d in days:
        day = pd.Timestamp(d)
        emit("asia", day, *_asia_win(day))
        emit("ldn", day, *_ldn_win(day))
        emit("ny", day, *_ny_win(day))

    # previous-FX-day high/low: created when the session ends at 17:00 ET
    ny_idx = bars5.index.tz_convert(NY)
    sess_id = pd.Series((ny_idx + pd.Timedelta(hours=7)).date, index=bars5.index)
    g = bars5.groupby(sess_id)
    sess = pd.DataFrame({"h": g.high.max(), "l": g.low.min(), "n": g.size()})
    sess = sess[sess.n > 50]
    for d, r in sess.iterrows():
        day = pd.Timestamp(d)
        t_end = pd.Timestamp(day.year, day.month, day.day, 17, tz=NY).tz_convert(UTC)
        rows.append(dict(kind="pdH", side=1, price=float(r.h), t_created=t_end, day=day))
        rows.append(dict(kind="pdL", side=-1, price=float(r.l), t_created=t_end, day=day))

    lv = pd.DataFrame(rows).sort_values("t_created").reset_index(drop=True)

    swept = []
    for _, r in lv.iterrows():
        i0 = idx.searchsorted(r.t_created)               # first bar opening at/after creation
        if i0 >= len(idx):
            swept.append(pd.NaT)
            continue
        m = (hi[i0:] >= r.price) if r.side == 1 else (lo[i0:] <= r.price)
        j = int(np.argmax(m))
        swept.append(idx[i0 + j] if m[j] else pd.NaT)
    lv["t_swept"] = swept
    return lv


def unswept_at(lv: pd.DataFrame, t: pd.Timestamp, side: int | None = None,
               max_age_days: float | None = None) -> pd.DataFrame:
    m = (lv.t_created <= t) & (lv.t_swept.isna() | (lv.t_swept >= t))
    if side is not None:
        m &= lv.side == side
    if max_age_days is not None:
        m &= lv.t_created >= t - pd.Timedelta(days=max_age_days)
    return lv[m]
