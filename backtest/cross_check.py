"""Cross-validate the 5m feed against an independent broker feed + known history."""
import pandas as pd, numpy as np

a = pd.read_csv('data/XAUUSD_5m.csv')
a['ts'] = pd.to_datetime(a.Date.astype(str) + ' ' + a.Time, format='%Y%m%d %H:%M:%S')
a = a.set_index('ts').sort_index()

# --- known-history spot checks (public record of gold's major levels) --------
daily = a.resample('1D').agg(o=('Open','first'), h=('High','max'), l=('Low','min'), c=('Close','last')).dropna()
checks = {
    '2020-08-21': 'Aug 2020, post-ATH consolidation ~1930-1950',
    '2022-03-08': 'Ukraine invasion spike, intraday high ~2070',
    '2023-10-06': 'pre-Oct-2023 low ~1810-1830',
    '2024-10-30': 'Oct 2024 record ~2790',
    '2025-04-22': 'Apr 2025 record ~3500',
}
print("known-history spot checks:")
for d, note in checks.items():
    if pd.Timestamp(d) in daily.index:
        r = daily.loc[pd.Timestamp(d)]
        print(f"  {d}  O={r.o:8.2f} H={r.h:8.2f} L={r.l:8.2f} C={r.c:8.2f}   [{note}]")
print(f"\ndataset all-time high {daily.h.max():.2f} on {daily.h.idxmax().date()}"
      f" | all-time low {daily.l.min():.2f} on {daily.l.idxmin().date()}")

# --- independent feed comparison (ejtrader m15, unknown tz) ------------------
b = pd.read_csv('data/XAUUSD_m15_ejtrader.csv', parse_dates=['Date']).set_index('Date').sort_index()
b = b[['open','high','low','close']] / 100.0          # that feed stores price*100
a15 = a['Close'].resample('15min').last().dropna()

print("\nalignment of independent feed (ejtrader m15) at candidate UTC offsets:")
best = None
for off in range(-6, 7):
    shifted = b['close'].copy()
    shifted.index = shifted.index - pd.Timedelta(hours=off)
    j = pd.concat([a15.rename('mine'), shifted.rename('other')], axis=1, join='inner').dropna()
    if len(j) < 500:
        continue
    mad = (j.mine - j.other).abs().median()
    if best is None or mad < best[1]:
        best = (off, mad, len(j))
    print(f"  offset {off:+d}h  n={len(j):6,}  median |diff| = ${mad:6.2f}")
print(f"\n-> best alignment at offset {best[0]:+d}h, median difference ${best[1]:.2f} on {best[2]:,} overlapping bars")
