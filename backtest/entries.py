"""Entry-mechanics variants. The decomposition showed the direction is worth
~$4/day but the breakout-close fill hands all of it back, so test cheaper fills."""
from __future__ import annotations
import pandas as pd, numpy as np, engine

def backtest_entry(bars5, range_min, exit_anchor, mode="confirm_close",
                   cost_usd=0.30, pullback=0.0, stop_mult=None, target_mult=None):
    """mode:
         confirm_close - baseline: fill at the close of the candle that breaks out
         touch         - stop order resting at the range boundary (no close confirmation)
         retest        - wait for the confirming close, then a limit back AT the boundary
         pullback      - as retest, but the limit sits `pullback` x range INSIDE the range
       stop_mult/target_mult: stop / target as a multiple of the range size (None = time exit only)
    """
    barsL = engine.resample(bars5, range_min)
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t0 = engine.session_start_utc(day)
        t_range_end = t0 + pd.Timedelta(minutes=range_min)
        t_exit = engine.exit_utc(day, exit_anchor)
        if t0 not in barsL.index or t_exit <= t_range_end:
            continue
        rng = barsL.loc[t0]
        if len(bars5.loc[t0:t_range_end - pd.Timedelta(minutes=1)]) < range_min // 5:
            continue
        rhigh, rlow = float(rng.high), float(rng.low)
        rsize = rhigh - rlow
        if rsize <= 0:
            continue
        rec = dict(day=day.date(), range_size=rsize, range_high=rhigh, range_low=rlow,
                   range_open=float(rng.open))

        side = 0; t_fill = None; entry = None
        if mode == "touch":
            path = bars5.loc[t_range_end:t_exit]
            for ts, b in path.iterrows():
                up, dn = b.high >= rhigh, b.low <= rlow
                if up or dn:
                    # if a single 5m bar takes out both, use the open to decide which came first
                    if up and dn:
                        side = 1 if b.open <= rlow else -1
                    else:
                        side = 1 if up else -1
                    entry = rhigh if side == 1 else rlow
                    t_fill = ts
                    break
        else:
            fwd = barsL.loc[t_range_end:t_exit]
            t_brk = None
            for ts, b in fwd.iterrows():
                if ts >= t_exit:
                    break
                if b.close > rhigh:
                    side, t_brk = 1, ts; break
                if b.close < rlow:
                    side, t_brk = -1, ts; break
            if side:
                t_after = t_brk + pd.Timedelta(minutes=range_min)
                if mode == "confirm_close":
                    entry, t_fill = float(fwd.at[t_brk, "close"]), t_after
                else:
                    lvl = (rhigh - pullback * rsize) if side == 1 else (rlow + pullback * rsize)
                    path = bars5.loc[t_after:t_exit]
                    hit = path[(path.low <= lvl) if side == 1 else (path.high >= lvl)]
                    if len(hit):
                        entry, t_fill = lvl, hit.index[0]
                    else:
                        side = 0                       # limit never filled
        if not side or entry is None:
            rows.append({**rec, "side": 0, "traded": False}); continue

        path = bars5.loc[t_fill:t_exit]
        exit_px, reason, t_out = None, "time", t_exit
        if len(path) and (stop_mult or target_mult):
            stop = entry - side * stop_mult * rsize if stop_mult else None
            targ = entry + side * target_mult * rsize if target_mult else None
            for ts, b in path.iterrows():
                s_hit = stop is not None and ((b.low <= stop) if side == 1 else (b.high >= stop))
                t_hit = targ is not None and ((b.high >= targ) if side == 1 else (b.low <= targ))
                if s_hit and t_hit:                    # ambiguous bar -> assume the stop
                    exit_px, reason, t_out = stop, "stop", ts; break
                if s_hit:
                    exit_px, reason, t_out = stop, "stop", ts; break
                if t_hit:
                    exit_px, reason, t_out = targ, "target", ts; break
        if exit_px is None:
            exit_px = engine.price_at(bars5, t_exit)
            if exit_px is None:
                rows.append({**rec, "side": 0, "traded": False}); continue

        pnl = side * (exit_px - entry) - cost_usd
        rows.append({**rec, "side": side, "traded": True, "t_fill": t_fill, "entry": entry,
                     "exit": exit_px, "t_out": t_out, "exit_reason": reason,
                     "pnl_usd": pnl, "pnl_pct": pnl / entry * 100,
                     "R": pnl / rsize})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    bars = engine.load_bars()
    print("=== ENTRY MECHANICS (exit at London close; $0.30 round-trip) ===")
    print("fill_rate = share of days that produced a filled trade\n")
    rows = []
    for L in (15, 30, 60):
        for mode, pb in [("confirm_close", 0), ("touch", 0), ("retest", 0.0),
                         ("pullback", 0.25), ("pullback", 0.5), ("pullback", 1.0)]:
            t = backtest_entry(bars, L, "london_close", mode=mode, pullback=pb)
            m = engine.metrics(t, "")
            if not m.get("n"):
                continue
            name = mode if mode != "pullback" else f"pullback {pb:.2f}R"
            rows.append({"range": f"{L}m", "entry": name, "n": m["n"],
                         "fill_rate": round(m["trade_rate"], 2),
                         "win%": round(m["win_rate"] * 100, 1),
                         "PF": round(m["profit_factor"], 3),
                         "exp_$": round(m["exp_usd"], 3),
                         "total_$": round(t[t.traded].pnl_usd.sum(), 0),
                         "t": round(m["t_stat"], 2)})
    print(pd.DataFrame(rows).to_string(index=False))
