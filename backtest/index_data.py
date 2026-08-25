"""Load, verify, and harmonize the index CFD feeds into 5-minute UTC frames.

Feeds:
  - Oanda 1-minute (FutureSharks), 2005-2020: timestamps claimed UTC
  - MT5 5-minute (ts4blader), 2020/2021-2025: timestamps claimed FIXED UTC+2

House rule: establish the timezone empirically before trusting it. The NY cash
open (09:30 ET) produces the sharpest intraday volatility spike in these
indices, and ET shifts against UTC at the US DST boundary. So in a UTC feed
the spike sits at 14:30 (winter) / 13:30 (summer); in a fixed UTC+2 feed at
16:30 / 15:30. verify() measures both seasons' peaks and refuses the feed if
they land anywhere else.

build() writes cached data/<IDX>_5m.csv (UTC) joining the two feeds:
  SPX: Oanda to 2019-12-31, MT5 from 2020-01-02
  NDX: Oanda to 2020-05-14, MT5 from 2021-01-04  (7.5-month hole, unavoidable)
  RTY: Oanda only, 2005-2020
"""
import pandas as pd, numpy as np, os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_oanda_5m(name):
    df = pd.read_csv(os.path.join(DATA, name))
    df["ts"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("ts")[["open", "high", "low", "close", "volume"]].sort_index()
    df = df[~df.index.duplicated()]
    return df.resample("5min").agg(open=("open", "first"), high=("high", "max"),
                                   low=("low", "min"), close=("close", "last"),
                                   volume=("volume", "sum")).dropna(subset=["open"])


def load_mt5(name):
    df = pd.read_csv(os.path.join(DATA, name))
    df.columns = [c.lower() for c in df.columns]
    df["ts"] = pd.to_datetime(df["datetime"]) - pd.Timedelta(hours=2)  # fixed UTC+2 -> UTC
    df["ts"] = df["ts"].dt.tz_localize("UTC")
    return (df.set_index("ts")[["open", "high", "low", "close", "volume"]]
            .sort_index().pipe(lambda d: d[~d.index.duplicated()]))


def _open_step(bars, months, slot_open):
    """Volatility at the claimed 09:30-ET slot vs the 5 minutes before it.
    The cash open is a step discontinuity - the cleanest fingerprint there is."""
    x = bars[bars.index.month.isin(months)]
    r = (np.log(x.close) - np.log(x.open)).abs()
    slot = x.index.hour * 60 + x.index.minute
    prof = r.groupby(slot).mean()
    return float(prof.get(slot_open, np.nan) / prof.get(slot_open - 5, np.nan))


def verify(bars, label, winter_open):
    """winter_open: minutes-of-day (UTC) of the 09:30-ET open in winter; in
    summer the same event sits 60 minutes earlier. Both must show a sharp
    volatility step (>=1.5x the preceding bar) at exactly those slots."""
    w = _open_step(bars, (1, 2, 12), winter_open)
    s = _open_step(bars, (6, 7), winter_open - 60)
    ok = w >= 1.5 and s >= 1.5
    print(f"  {label:28s} open-step winter x{w:.2f}, summer (-60min) x{s:.2f} "
          f"-> {'OK' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(f"timezone verification failed for {label}")


def build():
    out = {}
    print("=== timezone fingerprints (09:30 ET volatility spike) ===")
    ospx = load_oanda_5m("SPX500_1m_oanda_futuresharks.csv")
    ondx = load_oanda_5m("NAS100_1m_oanda_futuresharks.csv")
    orty = load_oanda_5m("US2000_1m_oanda_futuresharks.csv")
    mspx = load_mt5("US500_5m_ts4blader.csv")
    mndx = load_mt5("US100_5m_ts4blader.csv")
    verify(ospx, "Oanda SPX500 (claim UTC)", 14 * 60 + 30)
    verify(ondx, "Oanda NAS100 (claim UTC)", 14 * 60 + 30)
    verify(orty, "Oanda US2000 (claim UTC)", 14 * 60 + 30)
    verify(mspx, "MT5 US500 (claim UTC+2)", 14 * 60 + 30)   # already shifted to UTC here
    verify(mndx, "MT5 US100 (claim UTC+2)", 14 * 60 + 30)

    print("\n=== feed agreement in the 2020 overlap (SPX) ===")
    both = ospx.close.resample("1h").last().dropna().to_frame("o").join(
        mspx.close.resample("1h").last().dropna().to_frame("m"), how="inner")
    both = both["2020-01":"2020-05"]
    diff = (both.o - both.m)
    print(f"  {len(both)} overlapping hours: median offset {diff.median():+.2f} pts "
          f"({diff.median()/both.m.median()*100:+.3f}%), IQR {diff.quantile(.25):+.2f}..{diff.quantile(.75):+.2f}")

    joins = {"SPX": (ospx.loc[:"2019-12-31"], mspx),
             "NDX": (ondx.loc[:"2020-05-14"], mndx),
             "RTY": (orty, None)}
    print("\n=== cached 5m frames ===")
    for k, (a, b) in joins.items():
        df = a if b is None else pd.concat([a, b[b.index > a.index.max()]])
        df = df.sort_index()
        df = df[~df.index.duplicated()]
        path = os.path.join(DATA, f"{k}_5m.csv")
        df.to_csv(path)
        out[k] = df
        print(f"  {k}: {len(df):,} bars  {df.index[0]:%Y-%m-%d} .. {df.index[-1]:%Y-%m-%d}")
    return out


def load(idx):
    df = pd.read_csv(os.path.join(DATA, f"{idx}_5m.csv"), index_col=0, parse_dates=[0])
    df.index = pd.to_datetime(df.index, utc=True)
    return df


if __name__ == "__main__":
    build()
