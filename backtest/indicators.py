"""Shared indicator library for the recipe-replication rounds (r28+).

All functions take/return pandas Series aligned to the input index and use
only closed-bar information (no lookahead). Wilder smoothing where the
published form uses it.
"""
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def sma(s, n):
    return s.rolling(n).mean()


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def true_range(df):
    pc = df.close.shift(1)
    return pd.concat([df.high - df.low, (df.high - pc).abs(),
                      (df.low - pc).abs()], axis=1).max(axis=1)


def atr(df, n=14):
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()


def bollinger(close, n=20, k=2.0):
    m = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return m, m + k * sd, m - k * sd


def keltner(df, n=20, k=1.5):
    m = ema(df.close, n)
    a = atr(df, n)
    return m, m + k * a, m - k * a


def adx(df, n=14):
    up = df.high.diff()
    dn = -df.low.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    a = true_range(df).ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def session_vwap(df, tz=NY, session_start_min=570):
    """VWAP anchored to each session open (default 09:30 ET). Needs volume."""
    et = df.index.tz_convert(tz)
    mins = et.hour * 60 + et.minute
    day = pd.Series(et.date, index=df.index)
    new_sess = (mins == session_start_min) | (day != day.shift())
    grp = new_sess.cumsum()
    tp = (df.high + df.low + df.close) / 3
    v = df.volume if "volume" in df else pd.Series(1.0, index=df.index)
    return (tp * v).groupby(grp).cumsum() / v.groupby(grp).cumsum()


def swing_pivots(df, k=2):
    """Confirmed swing highs/lows: bar t is a swing high if its high exceeds
    the k bars either side; value becomes known k bars AFTER t (shifted so a
    strategy can only see confirmed pivots)."""
    hi, lo = df.high, df.low
    sh = hi[(hi == hi.rolling(2 * k + 1, center=True).max())]
    sl = lo[(lo == lo.rolling(2 * k + 1, center=True).min())]
    last_sh = sh.reindex(df.index).shift(k).ffill()
    last_sl = sl.reindex(df.index).shift(k).ffill()
    return last_sh, last_sl


def nr_n(df_daily, n=7):
    rng = df_daily.high - df_daily.low
    return rng == rng.rolling(n).min()


def inside_day(df_daily):
    return (df_daily.high < df_daily.high.shift(1)) & (df_daily.low > df_daily.low.shift(1))
