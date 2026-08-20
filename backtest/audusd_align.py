"""Establish the UTC offset of each AUDUSD feed empirically, by maximising the
correlation of its 15-minute returns against XAUUSD (gold and AUD are strongly
positively correlated intraday, so the true offset shows up as a sharp peak)."""
import pandas as pd, numpy as np, engine

gold = engine.load_bars()
g15 = gold.close.resample("15min").last().dropna()
gr = np.log(g15).diff()

def load_ej(path="data/AUDUSD_m15_ejtrader.csv"):
    d = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    return (d["close"] / 1e5).rename("aud")

def load_m5(path="data/AUDUSD_M5.csv"):
    d = pd.read_csv(path, header=None,
                    names=["ts", "open", "high", "low", "close", "vol"], parse_dates=["ts"])
    d = d.set_index("ts").sort_index()
    return d.close.resample("15min").last().dropna().rename("aud")

for name, s in [("ejtrader m15", load_ej()), ("jaxontn M5->15m", load_m5())]:
    print(f"\n=== {name}: {s.index.min()} -> {s.index.max()} ({len(s):,} bars) ===")
    best = None
    for off in range(-6, 7):
        x = s.copy()
        x.index = x.index.tz_localize("UTC") - pd.Timedelta(hours=off)
        ar = np.log(x).diff()
        j = pd.concat([gr.rename("g"), ar.rename("a")], axis=1, join="inner").dropna()
        j = j[(j.g != 0) & (j.a != 0)]
        if len(j) < 2000:
            continue
        c = j.g.corr(j.a)
        flag = ""
        if best is None or c > best[1]:
            best, flag = (off, c, len(j)), ""
        print(f"  offset {off:+d}h  n={len(j):7,}  corr(gold,aud) = {c:+.4f}")
    print(f"  -> best offset {best[0]:+d}h, correlation {best[1]:+.4f} on {best[2]:,} bars")

# --- DST-aware test: MT4/MT5 broker feeds are usually EET/EEST -----------------
print("\n=== ejtrader feed under a DST-aware broker-time hypothesis ===")
s = load_ej()
for tzname in ("Europe/Athens", "Europe/Berlin", "Europe/London", "UTC"):
    x = s.copy()
    try:
        x.index = x.index.tz_localize(tzname, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    except Exception as e:
        print(f"  {tzname}: {e}"); continue
    x = x[x.index.notna()]
    ar = np.log(x).diff()
    j = pd.concat([gr.rename("g"), ar.rename("a")], axis=1, join="inner").dropna()
    j = j[(j.g != 0) & (j.a != 0)]
    print(f"  interpreted as {tzname:15s} n={len(j):7,}  corr = {j.g.corr(j.a):+.4f}")

# cross-check the two AUD feeds against each other where they overlap
a = load_ej(); a.index = a.index.tz_localize("Europe/Athens", ambiguous="NaT",
                                             nonexistent="NaT").tz_convert("UTC")
a = a[a.index.notna()]
b = load_m5()
b.index = b.index.tz_localize("UTC")
j = pd.concat([a.rename("ej"), b.rename("jx")], axis=1, join="inner").dropna()
print(f"\n=== the two AUDUSD feeds against each other, {len(j):,} overlapping 15m bars ===")
print(f"  median |difference| = {(j.ej - j.jx).abs().median()*1e4:.2f} pips   corr of returns = "
      f"{np.log(j.ej).diff().corr(np.log(j.jx).diff()):+.4f}")
