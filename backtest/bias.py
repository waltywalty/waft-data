"""Does the 09:30-HKT opening-range breakout identify the day's true direction?

Decomposes the result into (a) is the DIRECTION right, and (b) is the ENTRY PRICE
good — a signal can call the day correctly and still lose if you buy the extreme.
"""
import pandas as pd, numpy as np, engine, pickle

bars = engine.load_bars()
logs = pickle.load(open("results/grid_logs.pkl", "rb"))

# reference prices per trading day
day_ref = {}
for d, grp in bars.groupby(bars.index.date):
    day = pd.Timestamp(d)
    t0 = engine.session_start_utc(day)
    sess = grp[grp.index >= t0]                      # 01:30 UTC onward = "the trading day"
    if not len(sess):
        continue
    close_2100 = grp[grp.index <= t0.normalize() + pd.Timedelta(hours=21)]
    day_ref[d] = dict(open0130=float(sess.iloc[0].open),
                      close2100=float(sess.iloc[-1].close),
                      hi=float(sess.high.max()), lo=float(sess.low.min()))
ref = pd.DataFrame(day_ref).T

print("=== A. DIRECTIONAL ACCURACY: does the breakout side match the day's actual direction? ===")
print("   'day direction' = sign(21:00 UTC close - 01:30 UTC open), i.e. the whole trading day\n")
rows = []
for L in (5, 15, 30):
    t = logs[(L, "london_close")].copy()
    t = t[t.traded]
    t = t.join(ref, on="day")
    t = t.dropna(subset=["open0130"])
    day_dir = np.sign(t.close2100 - t.open0130)
    hit = (np.sign(t.side) == day_dir)
    # base rate: what if you were always long?
    base_long = (day_dir > 0).mean()
    # close location within the day's range, in the direction traded
    loc = np.where(t.side == 1,
                   (t.close2100 - t.lo) / (t.hi - t.lo),
                   (t.hi - t.close2100) / (t.hi - t.lo))
    rows.append({"range": f"{L}m", "n": len(t),
                 "dir_hit_rate": round(hit.mean(), 3),
                 "always_long_hit": round(base_long, 3),
                 "long_share": round((t.side == 1).mean(), 3),
                 "close_loc_in_dir": round(np.nanmean(loc), 3)})
print(pd.DataFrame(rows).to_string(index=False))
print("\n   dir_hit_rate    = % of days the breakout direction matched the day's close direction")
print("   always_long_hit = % of days gold simply closed up (the benchmark to beat)")
print("   close_loc_in_dir= where the day closed inside its range, 1.0 = perfectly in your favour, 0.5 = coin flip")

print("\n=== B. DECOMPOSITION: direction vs entry price (30m range, London-close exit) ===")
t = logs[(30, "london_close")].copy(); t = t[t.traded].join(ref, on="day").dropna(subset=["open0130"])
perfect_entry = t.side * (t.exit - t.open0130)        # same signal, but filled at 01:30 open
actual        = t.side * (t.exit - t.entry)
print(f"  actual entry (breakout close)   : avg ${actual.mean():+.3f}/trade   PF={actual[actual>0].sum()/-actual[actual<=0].sum():.3f}")
print(f"  same direction, filled at 01:30 : avg ${perfect_entry.mean():+.3f}/trade   PF={perfect_entry[perfect_entry>0].sum()/-perfect_entry[perfect_entry<=0].sum():.3f}")
print(f"  cost of chasing the breakout    : ${(perfect_entry-actual).mean():.3f}/trade "
      f"(= avg distance from 01:30 open to entry: ${(t.side*(t.entry-t.open0130)).mean():.2f})")

print("\n=== C. WHIPSAW: how often does the day break the OTHER side after your entry? ===")
for L in (5, 15, 30):
    t = logs[(L, "london_close")]; t = t[t.traded]
    opp = np.where(t.side == 1, t.mae >= (t.entry - t.range_low), t.mae >= (t.range_high - t.entry))
    print(f"  {L:2d}m range: {np.nanmean(opp)*100:.1f}% of trades later traded back through the opposite side of the range")

print("\n=== D. MFE / MAE: was there ever a good exit on the table? ===")
for L in (5, 15, 30):
    for anchor in ("pre_london", "london_close"):
        t = logs[(L, anchor)]; t = t[t.traded]
        print(f"  {L:2d}m/{anchor:12s} avg MFE ${t.mfe.mean():5.2f} | avg MAE ${t.mae.mean():5.2f} | "
              f"MFE/MAE {t.mfe.mean()/t.mae.mean():.2f} | avg realised ${t.pnl_usd.mean():+.2f} | "
              f"avg range ${t.range_size.mean():.2f}")

print("\n=== E. BENCHMARK: passive exposure over the identical window ===")
for anchor in engine.EXITS:
    t = logs[(30, anchor)]; t = t[t.traded]
    bh = (t.exit - t.entry)                       # always-long, same entry/exit times
    print(f"  30m/{anchor:12s} always-long over same window: avg ${bh.mean():+.3f}/day "
          f"| strategy avg ${t.pnl_usd.mean():+.3f}/day")
