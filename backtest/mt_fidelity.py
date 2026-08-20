"""Would this survive being implemented on MT4/MT5?

The filter is the part carrying the edge, and it is computed from DAILY closes.
An MT4/MT5 chart's "day" ends at broker midnight - normally 00:00 EET/EEST, i.e.
21:00 or 22:00 UTC - not at UTC midnight, and not at the Fed's noon-New-York fix
that the FRED series uses. If the filter only works under the exact convention
used in the research, it is not deployable.
"""
import pandas as pd, numpy as np, engine, audusd, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

gold = engine.load_bars()
t0 = pd.read_pickle("results/trades_60_ny_cut.pkl").drop(columns=["corr"])
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
def stat(x):
    p = x.pnl_oz; pct = p / x.entry * 100
    return dict(n=len(x), pf=pf(p), win=float((p > 0).mean()), exp=float(p.mean()),
                t=float(pct.mean()/pct.std()*np.sqrt(len(p))) if len(p) > 2 else np.nan)

def daily_close(bars, how):
    """Daily close series under different 'end of day' conventions."""
    s = bars.close
    if how == "utc":
        d = s.resample("1D").last()
        idx = d.index.tz_localize(None).normalize()
    elif how in ("eet", "ny"):
        tz = "Europe/Athens" if how == "eet" else "America/New_York"
        loc = s.tz_convert(ZoneInfo(tz))
        if how == "ny":                       # FX day ends 17:00 New York
            loc.index = loc.index + pd.Timedelta(hours=7)   # 17:00 -> local midnight
        d = loc.resample("1D").last()
        idx = pd.to_datetime([x.date() for x in d.index])
    d = pd.Series(d.values, index=idx).dropna()
    return d[~d.index.duplicated()]

aud = audusd.daily_from_fred(); aud.index = pd.to_datetime(aud.index).normalize()
ar = np.log(aud).diff().rename("a")

print("=== A. DOES THE FILTER SURVIVE A DIFFERENT DAILY-CLOSE CONVENTION? ===")
print("   (AUD side held at the FRED series throughout; only the gold day changes)\n")
print(f"{'gold day ends':<28}{'kept':>6}{'PF':>8}{'win%':>7}{'exp$':>8}{'t':>7}"
      f"{'':>4}{'excluded':>9}{'PF':>8}")
res = {}
for how, label in (("utc", "00:00 UTC (research)"), ("eet", "00:00 EET/EEST (MT4/MT5)"),
                   ("ny", "17:00 New York (FX day)")):
    gr = np.log(daily_close(gold, how)).diff().rename("g")
    j = pd.concat([gr, ar], axis=1, join="inner").dropna()
    C = (j.g.rolling(20).corr(j.a)
         .reindex(pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill().shift(1))
    t = t0.copy()
    t["c"] = pd.to_datetime(t.day).dt.normalize().map(C)
    t = t.dropna(subset=["c"])
    k, e = stat(t[t.c <= .5]), stat(t[t.c > .5])
    res[how] = (k, e, t)
    print(f"{label:<28}{k['n']:>6}{k['pf']:>8.3f}{k['win']*100:>7.1f}{k['exp']:>8.2f}"
          f"{k['t']:>7.2f}{'':>4}{e['n']:>9}{e['pf']:>8.3f}")

agree = pd.concat([(res[h][2].set_index("day").c <= .5).rename(h) for h in res], axis=1).dropna()
print(f"\n  the three conventions agree on {(agree.nunique(axis=1) == 1).mean()*100:.0f}% of days")

print("\n=== A2. HOW FRESH DOES THE CORRELATION HAVE TO BE? ===")
print("   An EA that reads a not-yet-closed bar, or lags a day, gets a different number.\n")
gr = np.log(daily_close(gold, "eet")).diff().rename("g")
j = pd.concat([gr, ar], axis=1, join="inner").dropna()
raw = j.g.rolling(20).corr(j.a).reindex(
    pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill()
for lag in (0, 1, 2, 3, 5, 10):
    C = raw.shift(lag)
    t = t0.copy(); t["c"] = pd.to_datetime(t.day).dt.normalize().map(C)
    t = t.dropna(subset=["c"])
    k = stat(t[t.c <= .5])
    note = "  <- lookahead, not tradeable" if lag == 0 else ("  <- the deployable version" if lag == 1 else "")
    print(f"  correlation lagged {lag:>2} day(s): kept n={k['n']:>4} PF={k['pf']:.3f} "
          f"exp=${k['exp']:+.2f} t={k['t']:+.2f}{note}")

print("\n=== B. BROKER FX BARS INSTEAD OF THE FRED FIX ===")
print("   MT5 would compute the AUD side from its own daily bars, not from FRED.")
a15 = audusd.build()
def fx_daily(s, how="eet"):
    tz = "Europe/Athens"
    loc = s.tz_convert(ZoneInfo(tz))
    d = loc.resample("1D").last()
    return pd.Series(d.values, index=pd.to_datetime([x.date() for x in d.index])).dropna()
ab = fx_daily(a15.close)
gb = daily_close(gold, "eet")
j = pd.concat([np.log(gb).diff().rename("g"), np.log(ab).diff().rename("a")],
              axis=1, join="inner").dropna()
C = (j.g.rolling(20).corr(j.a)
     .reindex(pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill().shift(1))
t = t0.copy(); t["c"] = pd.to_datetime(t.day).dt.normalize().map(C)
t = t.dropna(subset=["c"])
k, e = stat(t[t.c <= .5]), stat(t[t.c > .5])
print(f"  both sides from broker EET daily bars, {j.index.min().date()}..{j.index.max().date()}")
print(f"    kept n={k['n']} PF={k['pf']:.3f} exp=${k['exp']:+.2f} t={k['t']:+.2f}  |  "
      f"excluded n={e['n']} PF={e['pf']:.3f} exp=${e['exp']:+.2f}")
# same window, research convention, for a like-for-like comparison
gr = np.log(daily_close(gold, "utc")).diff().rename("g")
j2 = pd.concat([gr, ar], axis=1, join="inner").dropna()
C2 = (j2.g.rolling(20).corr(j2.a)
      .reindex(pd.date_range(j2.index.min(), j2.index.max(), freq="D")).ffill().shift(1))
t2 = t0.copy(); t2["c"] = pd.to_datetime(t2.day).dt.normalize().map(C2)
t2 = t2[(pd.to_datetime(t2.day) >= j.index.min()) & (pd.to_datetime(t2.day) <= j.index.max())]
t2 = t2.dropna(subset=["c"])
k2, e2 = stat(t2[t2.c <= .5]), stat(t2[t2.c > .5])
print(f"  research convention over the SAME window, for comparison")
print(f"    kept n={k2['n']} PF={k2['pf']:.3f} exp=${k2['exp']:+.2f}  |  "
      f"excluded n={e2['n']} PF={e2['pf']:.3f} exp=${e2['exp']:+.2f}")

print("\n=== C. WHAT TIME IS 09:30 HKT ON A BROKER CLOCK? ===")
for d in ("2024-01-15", "2024-07-15"):
    u = pd.Timestamp(d + " 01:30", tz="UTC")
    print(f"  {d}: 01:30 UTC = {u.tz_convert('Europe/Athens'):%H:%M} broker (EET/EEST), "
          f"{u.tz_convert('America/New_York'):%H:%M} New York, "
          f"{u.tz_convert('Asia/Hong_Kong'):%H:%M} Hong Kong")
print("  -> the server-time hour MOVES with European DST. Hardcoding it is wrong for half the year.")

print("\n=== D. DOES THE HOLD CROSS THE BROKER ROLLOVER (i.e. is swap charged)? ===")
for d, lbl in (("2024-01-15", "winter"), ("2024-07-15", "summer")):
    ex = pd.Timestamp(d + " 16:00", tz="America/New_York").tz_convert("UTC")
    roll = pd.Timestamp(d + " 00:00", tz="Europe/Athens").tz_convert("UTC") + pd.Timedelta(days=1)
    print(f"  {lbl}: exit {ex:%H:%M} UTC, broker rollover {roll:%H:%M} UTC -> "
          f"{'NO swap' if ex < roll else 'SWAP CHARGED'}")
