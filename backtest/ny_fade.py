"""Fading the New York open on XAUUSD.

Round 7 established that the first NY-open break holds its direction (only 45%
whipsaw) but leaves nothing on the table after the fill (+$0.10 vs Asia's +$1.56).
This module tests the mirror hypothesis: the break IS the move, so enter against
it and harvest the reversion.

Trigger : identical to ny_orb.run - first confirmation candle to CLOSE beyond the
          opening range - but the position taken is AGAINST the break.
Stop    : beyond the break (stop_mult x range past the entry, in the break
          direction), never on the profit side.
Targets : the range midpoint, the far side of the range, the round-7 liquidity
          levels (in the fade direction), or a clock time.

All level construction is ny_orb.build_levels - already audited for lookahead.
The path walk keeps the right-endpoint discipline (slice ends one bar before
t_exit; bars are open-stamped).
"""
from __future__ import annotations
import pandas as pd, numpy as np, engine, ny_orb

TIME_EXITS = {"ny+30m": 30, **ny_orb.TIME_EXITS}
# fade targets computed from the range itself, plus the audited liquidity levels
RANGE_TARGETS = ["range_mid", "range_far"]
LEVEL_TARGETS = ["prev_day", "asia", "london"]


def run(bars5: pd.DataFrame, range_min: int = 15, exit_spec: str = "range_mid",
        stop_mult: float = 1.0, entry_deadline_min: int = 90, cost: float = 0.30,
        target_first: bool = False, min_target_r: float = 0.25,
        levels: dict | None = None, confirm_min: int = 5,
        use_stop: bool = True, min_over: float = 0.0) -> pd.DataFrame:
    """exit_spec : a key of TIME_EXITS, 'range_mid', 'range_far', or a level name.
       stop_mult : stop distance in range widths beyond the entry, in the BREAK
                   direction (i.e. against the fade).
       min_over  : require the confirmation close to overshoot the range boundary
                   by at least this fraction of the range width. 0 fades any break;
                   0.25 only fades stretched ones.
       Everything else matches ny_orb.run semantics."""
    if levels is None and exit_spec in LEVEL_TARGETS:
        levels = ny_orb.build_levels(bars5)
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t_open = ny_orb.ny_time(day, 9, 30)
        t_rend = t_open + pd.Timedelta(minutes=range_min)
        t_dead = t_open + pd.Timedelta(minutes=entry_deadline_min)
        t_sess_end = ny_orb.ny_time(day, 16)

        win = bars5.loc[t_open:t_rend - pd.Timedelta(minutes=5)]
        if len(win) < range_min // 5:
            continue
        rhigh, rlow = float(win.high.max()), float(win.low.min())
        rsize = rhigh - rlow
        if rsize <= 0:
            continue

        rec = dict(day=d, t_open=t_open, range_high=rhigh, range_low=rlow, range_size=rsize)

        # ---- the break, exactly as in ny_orb.run
        brk, t_fill, entry = 0, None, None
        step = pd.Timedelta(minutes=confirm_min)
        for ts, b in bars5.loc[t_rend:t_dead].iterrows():
            t_close = ts + pd.Timedelta(minutes=5)
            if t_close > t_dead:
                break
            if int((t_close - t_rend).total_seconds()) % int(step.total_seconds()) != 0:
                continue
            blk = bars5.loc[t_close - step:ts]
            if not len(blk):
                continue
            c = float(blk.iloc[-1].close)
            if c > rhigh:
                brk = 1
            elif c < rlow:
                brk = -1
            if brk:
                entry, t_fill = c, t_close
                break
        if not brk:
            rows.append({**rec, "side": 0, "traded": False, "reason": "no_break"})
            continue

        # overshoot: how far beyond the boundary the confirmation actually closed
        over = brk * (entry - (rhigh if brk == 1 else rlow)) / rsize
        rec["overshoot"] = over
        if over < min_over:
            rows.append({**rec, "side": 0, "traded": False, "reason": "break_too_small"})
            continue

        side = -brk                                    # the fade

        # ---- exits
        stop = entry + brk * stop_mult * rsize if use_stop else None
        target, t_exit, kind = None, t_sess_end, "time"
        if exit_spec in TIME_EXITS:
            t_exit = t_open + pd.Timedelta(minutes=TIME_EXITS[exit_spec])
            if t_exit <= t_fill:
                rows.append({**rec, "side": side, "traded": False, "reason": "exit_before_fill"})
                continue
        else:
            kind = "target"
            if exit_spec == "range_mid":
                target = (rhigh + rlow) / 2
            elif exit_spec == "range_far":
                target = rlow if brk == 1 else rhigh
            else:
                lv = levels.get(d, {}).get(exit_spec)
                if lv is None:
                    rows.append({**rec, "side": side, "traded": False, "reason": "no_level"})
                    continue
                target = lv[0] if side == 1 else lv[1]
            if side * (target - entry) < min_target_r * rsize:
                rows.append({**rec, "side": side, "traded": False, "reason": "target_behind"})
                continue

        # ---- walk the path (right endpoint excluded: bars are open-stamped)
        path = bars5.loc[t_fill:t_exit - pd.Timedelta(minutes=5)]
        px, why, t_out = None, "time", t_exit
        for ts, b in path.iterrows():
            hit_s = stop is not None and ((b.low <= stop) if side == 1 else (b.high >= stop))
            hit_t = target is not None and ((b.high >= target) if side == 1 else (b.low <= target))
            if hit_s and hit_t:
                px, why, t_out = (target, "target", ts) if target_first else (stop, "stop", ts)
                break
            if hit_s:
                px, why, t_out = stop, "stop", ts
                break
            if hit_t:
                px, why, t_out = target, "target", ts
                break
        if px is None:
            px = engine.price_at(bars5, t_exit)
            if px is None:
                rows.append({**rec, "side": side, "traded": False, "reason": "no_exit_px"})
                continue

        rows.append({**rec, "side": side, "traded": True, "reason": "ok", "kind": kind,
                     "t_fill": t_fill, "entry": entry, "stop": stop, "target": target,
                     "exit": px, "t_out": t_out, "why": why,
                     "pnl_oz": side * (px - entry) - cost,
                     "hold_min": (t_out - t_fill).total_seconds() / 60})
    return pd.DataFrame(rows)
