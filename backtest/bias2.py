"""Is the directional 'bias capture' real forecasting power, or just the move
that has already happened by the time you are filled?"""
import pandas as pd, numpy as np, engine
from scipy import stats

bars = engine.load_bars()

ref = {}
for d, grp in bars.groupby(bars.index.date):
    t0 = engine.session_start_utc(pd.Timestamp(d))
    sess = grp[grp.index >= t0]
    if len(sess):
        ref[d] = (float(sess.iloc[0].open), float(sess.iloc[-1].close))
ref = pd.DataFrame(ref, index=["open0130", "close2100"]).T

print("=== DIRECTIONAL ACCURACY, measured two ways (exit at London close) ===")
print("  from 01:30 : does the day close on the breakout side of the 01:30 OPEN?  <- includes the move already made")
print("  from ENTRY : does the day close on the breakout side of YOUR FILL?       <- the only one you can trade\n")
rows = []
for L in (5, 15, 30, 45, 60, 90):
    t = engine.backtest(bars, L, "london_close")
    t = t[t.traded].join(ref, on="day").dropna(subset=["open0130"])
    from_open = (np.sign(t.close2100 - t.open0130) == t.side).mean()
    from_entry = (np.sign(t.close2100 - t.entry) == t.side).mean()
    fwd = t.side * (t.close2100 - t.entry)                      # gross forward $ move
    # unconditional drift over the same window, direction-blind
    uncond = (t.close2100 - t.entry)
    up, dn = t[t.side == 1], t[t.side == -1]
    fu = (up.close2100 - up.entry)
    fd = (dn.close2100 - dn.entry)
    tt = stats.ttest_ind(fu / up.entry * 100, fd / dn.entry * 100, equal_var=False)
    rows.append({"range": f"{L}m", "n": len(t),
                 "hit_from_0130": round(from_open, 3),
                 "hit_from_entry": round(from_entry, 3),
                 "already_moved_$": round((t.side * (t.entry - t.open0130)).mean(), 2),
                 "fwd_gross_$": round(fwd.mean(), 3),
                 "E[fwd|up]$": round(fu.mean(), 2), "E[fwd|dn]$": round(fd.mean(), 2),
                 "diff_t": round(tt.statistic, 2), "diff_p": round(tt.pvalue, 3)})
res = pd.DataFrame(rows)
print(res.to_string(index=False))
print("""
  already_moved_$ = distance from the 01:30 open to your fill (the move you paid for, not captured)
  E[fwd|up] / E[fwd|dn] = forward $ move to 21:00 UTC after an up-break vs a down-break.
  If the breakout genuinely forecasts the day, E[fwd|up] should be clearly > E[fwd|dn].
  diff_p = p-value of that difference (Welch t-test on % returns).""")

print("\n=== Range length sweep, net of $0.30 costs (does a longer opening candle help?) ===")
rows = []
for L in (5, 15, 30, 45, 60, 90, 120):
    for anchor in ("pre_london", "london_open", "london_close"):
        m = engine.metrics(engine.backtest(bars, L, anchor), "")
        rows.append({"range": f"{L}m", "exit": anchor, "n": m["n"],
                     "win%": round(m["win_rate"] * 100, 1), "PF": round(m["profit_factor"], 3),
                     "exp_$": round(m["exp_usd"], 3), "t": round(m["t_stat"], 2)})
print(pd.DataFrame(rows).to_string(index=False))
