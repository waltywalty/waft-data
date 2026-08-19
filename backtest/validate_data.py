"""Data integrity + timezone identification for the XAUUSD 5-minute dataset.

The strategy is anchored to a wall-clock time (09:30 HKT), so the dataset's UTC
offset has to be established from the data itself, not assumed.
"""
import pandas as pd, numpy as np

df = pd.read_csv('data/XAUUSD_5m.csv')
df['ts'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'], format='%Y%m%d %H:%M:%S')
df = df.sort_values('ts').reset_index(drop=True)

print(f"rows           : {len(df):,}")
print(f"range          : {df.ts.min()} -> {df.ts.max()}")
print(f"duplicate stamps: {df.ts.duplicated().sum()}")
print(f"NaNs           : {df[['Open','High','Low','Close']].isna().sum().sum()}")
bad = df[(df.High < df.Low) | (df.High < df.Open) | (df.High < df.Close) |
         (df.Low > df.Open) | (df.Low > df.Close)]
print(f"OHLC violations: {len(bad)}")
print(f"zero/neg prices: {(df[['Open','High','Low','Close']] <= 0).sum().sum()}")

# --- session structure -------------------------------------------------------
df['dow'] = df.ts.dt.dayofweek          # 0=Mon
df['tod'] = df.ts.dt.strftime('%H:%M')
print("\nbars per weekday:")
print(df.groupby('dow').size().rename(lambda d: 'Mon Tue Wed Thu Fri Sat Sun'.split()[d]).to_string())

# first/last bar of each weekday tells us where the weekly session boundary sits
for d, name in [(6, 'Sun'), (0, 'Mon'), (4, 'Fri')]:
    sub = df[df.dow == d]
    if len(sub):
        print(f"{name}: first bar {sub.tod.min()}  last bar {sub.tod.max()}  n={len(sub):,}")

# --- where does the daily break sit? ----------------------------------------
cnt = df.groupby('tod').size()
print("\nleast-populated times of day (daily rollover break):")
print(cnt.nsmallest(8).to_string())

# --- volatility by time of day, split by US DST ------------------------------
df['ret'] = df.Close.pct_change().abs() * 1e4          # basis points
def us_dst(ts):
    # US DST: 2nd Sun Mar -> 1st Sun Nov
    y = ts.year
    mar = pd.Timestamp(year=y, month=3, day=1)
    start = mar + pd.Timedelta(days=(6 - mar.dayofweek) % 7 + 7)
    nov = pd.Timestamp(year=y, month=11, day=1)
    end = nov + pd.Timedelta(days=(6 - nov.dayofweek) % 7)
    return start <= ts < end
df['dst'] = df.ts.map(us_dst)

for label, sub in [('US DST (EDT, UTC-4)', df[df.dst]), ('US standard (EST, UTC-5)', df[~df.dst])]:
    prof = sub.groupby('tod')['ret'].mean()
    print(f"\n{label} — 6 most volatile 5m slots (stamp time):")
    print(prof.nlargest(6).round(2).to_string())
