"""Check 3 of 3: transliterate the EA's OnTick decision logic into Python and check it
produces the same trades as the validated backtest.

This is deliberately a re-implementation from the MQL5 control flow - it does not call the
research engine - so that agreement is evidence and not a tautology. A compiler could never
catch the errors this finds.
"""
import sys, datetime as dt
sys.path.insert(0, "/home/user/waft-data/backtest")
import os
os.chdir("/home/user/waft-data/backtest")
import pandas as pd, numpy as np, engine, audusd, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo
from test_dst import london_offset, newyork_offset

RANGE_MIN, CORR_DAYS, CORR_MAX, STOP_MULT, CUTOFF_LDN, EXIT_NY = 60, 20, 0.50, 2.0, 8, 16

bars = engine.load_bars()                       # 5-minute XAUUSD, UTC
# --- daily closes exactly as the EA reads them: broker (EET) day, closed bars only
loc = bars.close.tz_convert(ZoneInfo("Europe/Athens"))
gd = loc.resample("1D").last()
gd = pd.Series(gd.values, index=pd.to_datetime([x.date() for x in gd.index])).dropna()
ad = audusd.daily_from_fred(); ad.index = pd.to_datetime(ad.index).normalize()
daily = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
                  axis=1, join="inner").dropna()

def corr_through(day):
    """CorrelationOk(): the 20 most recent CLOSED daily returns strictly before `day`."""
    hist = daily[daily.index < pd.Timestamp(day)]
    if len(hist) < CORR_DAYS: return None
    w = hist.iloc[-CORR_DAYS:]
    sg, sa = w.g.std(), w.a.std()
    if sg <= 0 or sa <= 0: return None
    return float(w.g.corr(w.a))

idx = bars.index
rows = []
for d in pd.Series(idx.date, index=idx).unique():
    day = pd.Timestamp(d, tz="UTC")
    day_ts = int(day.timestamp())
    range_start = day + pd.Timedelta(hours=1, minutes=30)
    range_end = range_start + pd.Timedelta(minutes=RANGE_MIN)
    cutoff = day + pd.Timedelta(hours=CUTOFF_LDN - london_offset(day_ts))
    exit_t = day + pd.Timedelta(hours=EXIT_NY - newyork_offset(day_ts))

    # --- BuildRange(): M5 bars whose OPEN time is in [start, end-5m]
    w = bars.loc[range_start:range_end - pd.Timedelta(minutes=5)]
    if len(w) < RANGE_MIN // 5:
        continue
    hi, lo = float(w.high.max()), float(w.low.min())
    if hi <= lo:
        continue

    # --- CorrelationOk()
    c = corr_through(d)
    if c is None or c > CORR_MAX:
        continue

    # --- walk forward, testing only on closed 60-minute blocks anchored on range_end
    fwd = bars.loc[range_end:cutoff]
    side = 0
    for ts, b in fwd.iterrows():
        bar_end = ts + pd.Timedelta(minutes=5)
        if bar_end > cutoff:
            break
        secs = int((bar_end - range_end).total_seconds())
        if secs <= 0 or secs % (RANGE_MIN * 60) != 0:
            continue
        cl = float(b.close)
        if cl > hi: side = 1
        elif cl < lo: side = -1
        if side:
            entry, t_fill = cl, bar_end
            break
    if not side:
        continue

    # --- stop, then time exit
    width = hi - lo
    stop = entry - side * STOP_MULT * width
    path = bars.loc[t_fill:exit_t]
    px, reason, t_out = None, "time", exit_t
    if len(path):
        hit = path[(path.low <= stop) if side == 1 else (path.high >= stop)]
        if len(hit):
            px, reason, t_out = stop, "stop", hit.index[0]
    if px is None:
        px = engine.price_at(bars, exit_t)
        if px is None:
            continue
    rows.append({"day": d, "side": side, "entry": entry, "exit": px, "reason": reason,
                 "t_fill": t_fill, "corr": c, "range": width})

ea = pd.DataFrame(rows)
bt = pd.read_pickle("/home/user/waft-data/backtest/results/trades_deployable.pkl")
print(f"EA logic replay : {len(ea)} trades")
print(f"backtest        : {len(bt)} trades")

m = ea.merge(bt[["day", "side", "entry", "exit", "reason"]], on="day",
             how="outer", suffixes=("_ea", "_bt"), indicator=True)
both = m[m._merge == "both"]
print(f"\ndays in both    : {len(both)}")
print(f"only in EA      : {(m._merge == 'left_only').sum()}")
print(f"only in backtest: {(m._merge == 'right_only').sum()}")
if len(both):
    print(f"same direction  : {(both.side_ea == both.side_bt).mean()*100:.2f}%")
    de = (both.entry_ea - both.entry_bt).abs()
    dx = (both.exit_ea - both.exit_bt).abs()
    print(f"entry price     : max diff ${de.max():.4f}, {(de < 1e-6).mean()*100:.1f}% identical")
    print(f"exit price      : max diff ${dx.max():.4f}, {(dx < 1e-6).mean()*100:.1f}% identical")
    print(f"same exit reason: {(both.reason_ea == both.reason_bt).mean()*100:.2f}%")
    pnl_ea = both.side_ea * (both.exit_ea - both.entry_ea)
    pnl_bt = both.side_bt * (both.exit_bt - both.entry_bt)
    print(f"gross P&L/oz    : EA ${pnl_ea.mean():+.4f}  backtest ${pnl_bt.mean():+.4f}")
mm = m[m._merge != "both"]
if len(mm):
    print("\nmismatched days (first 10):")
    print(mm[["day", "_merge"]].head(10).to_string(index=False))
