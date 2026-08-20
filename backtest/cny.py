"""Does the Chinese yuan work as a correlation-regime reference the way AUD did?

FRED's DEXCHUS is yuan per dollar, so it is INVERTED here to CNYUSD (dollars per
yuan). That puts it in the same orientation as AUDUSD: higher = weaker dollar,
which is the direction gold usually likes. Using log returns makes the inversion
an exact sign flip.
"""
import pandas as pd, numpy as np, engine, trades, audusd

def cny_returns(path="data/CNY_daily_fred.csv"):
    d = pd.read_csv(path)
    d["dt"] = pd.to_datetime(d.observation_date).dt.normalize()
    v = pd.to_numeric(d.DEXCHUS, errors="coerce")
    s = pd.Series(v.values, index=d.dt).dropna()
    return -np.log(s).diff().rename("cny")      # sign flip -> CNYUSD log returns

def gold_returns(gold):
    gd = gold.close.resample("1D").last().dropna()
    gd.index = gd.index.tz_localize(None).normalize()
    return np.log(gd).diff().rename("g")

def aud_returns():
    a = audusd.daily_from_fred()
    a.index = pd.to_datetime(a.index).normalize()
    return np.log(a).diff().rename("aud")       # DEXUSAL is already USD per AUD

def build_corr(gold, window=20):
    j = pd.concat([gold_returns(gold), cny_returns(), aud_returns()],
                  axis=1, join="inner").dropna()
    out = pd.DataFrame({
        "cny": j.g.rolling(window).corr(j.cny),
        "aud": j.g.rolling(window).corr(j.aud),
    }, index=j.index)
    full = pd.date_range(j.index.min(), j.index.max(), freq="D")
    return out.reindex(full).ffill().shift(1), j
