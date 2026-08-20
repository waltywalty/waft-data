"""Build a single UTC AUDUSD 15-minute series by splicing the two validated feeds."""
import pandas as pd, numpy as np

def build(m5_path="data/AUDUSD_M5.csv", ej_path="data/AUDUSD_m15_ejtrader.csv"):
    a = pd.read_csv(m5_path, header=None,
                    names=["ts", "open", "high", "low", "close", "vol"], parse_dates=["ts"])
    a = a.set_index("ts").sort_index().tz_localize("UTC")          # verified UTC
    a15 = a.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                                  low=("low", "min"), close=("close", "last")).dropna()
    b = pd.read_csv(ej_path, parse_dates=["Date"]).set_index("Date").sort_index()
    b = b[["open", "high", "low", "close"]] / 1e5
    b.index = b.index.tz_localize("Europe/Athens", ambiguous="NaT",
                                  nonexistent="NaT").tz_convert("UTC")  # verified EET/EEST
    b = b[b.index.notna()]
    cut = a15.index.max()
    out = pd.concat([a15, b[b.index > cut]]).sort_index()
    return out[~out.index.duplicated()]

def daily_from_fred(path="data/AUDUSD_daily_fred.csv"):
    d = pd.read_csv(path, parse_dates=["observation_date"])
    d = d.rename(columns={"observation_date": "date", "DEXUSAL": "aud"}).set_index("date")
    return pd.to_numeric(d.aud, errors="coerce").dropna()

if __name__ == "__main__":
    s = build()
    print(f"AUDUSD 15m (UTC): {s.index.min()} -> {s.index.max()}  {len(s):,} bars")
    print(f"  gap check: {(s.index.to_series().diff() > pd.Timedelta('3D')).sum()} multi-day gaps")
    f = daily_from_fred()
    print(f"AUDUSD daily (FRED): {f.index.min().date()} -> {f.index.max().date()}  {len(f):,} obs")
