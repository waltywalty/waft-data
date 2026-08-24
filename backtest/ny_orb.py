"""New York opening-range breakout on XAUUSD.

Range   : first R minutes after the NY open (09:30 America/New_York), DST-aware.
Entry   : first 5-minute candle to CLOSE beyond the range, in that direction.
          One trade per day, first break only, no new entry after a deadline.
Exits   : either a fixed clock time, or a liquidity level as a target with a stop.

Every liquidity level is computed from bars that closed BEFORE the NY open, so
nothing here can see the future.
"""
from __future__ import annotations
import pandas as pd, numpy as np, engine
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")


def ny_time(day: pd.Timestamp, h: int, m: int = 0) -> pd.Timestamp:
    return pd.Timestamp(day.year, day.month, day.day, h, m, tz=NY).tz_convert(UTC)


def ldn_time(day: pd.Timestamp, h: int, m: int = 0) -> pd.Timestamp:
    return pd.Timestamp(day.year, day.month, day.day, h, m, tz=LDN).tz_convert(UTC)


# time exits, expressed as minutes after the NY open
TIME_EXITS = {"ny+60m": 60, "ny+90m": 90, "ny+2h": 120, "ny_lunch": 150, "ny_close": 390}
# liquidity targets
LEVELS = ["prev_day", "asia", "london", "prev_hour", "measured_move"]


def build_levels(bars5: pd.DataFrame) -> dict:
    """Pre-compute, for every calendar day, the highs and lows of the sessions that
    completed BEFORE that day's NY open. Done once and reused across configurations.

    The previous day is the previous *trading* session, not literally 24h earlier -
    otherwise every Monday would look at an empty weekend."""
    # FX sessions run 17:00 ET to 17:00 ET. Label each bar by the date its session ENDS,
    # so that "session E" spans E-1 17:00 ET to E 17:00 ET. Labelling by session START
    # instead is a lookahead trap: the session starting on d-1 does not finish until
    # 17:00 ET on day d, hours AFTER day d's 09:30 open, so its high and low would
    # already contain the move being traded.
    ny_idx = bars5.index.tz_convert(NY)
    sess_id = pd.Series((ny_idx + pd.Timedelta(hours=7)).date, index=bars5.index)
    g = bars5.groupby(sess_id)
    sess = pd.DataFrame({"h": g.high.max(), "l": g.low.min(), "n": g.size()})
    sess = sess[sess.n > 50]                       # drop stubs (holidays, partial sessions)
    sess_dates = list(sess.index)

    out = {}
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t_open = ny_time(day, 9, 30)
        lv = {}
        # sessions ending strictly before day d have finished by 17:00 ET on d-1,
        # which is before day d's 09:30 ET open
        prev = [x for x in sess_dates if x < d]
        lv["prev_day"] = (float(sess.loc[prev[-1], "h"]), float(sess.loc[prev[-1], "l"])) if prev else None
        # Asia: Tokyo cash hours, 09:00-15:00 JST = 00:00-06:00 UTC (Japan has no DST)
        a0 = day.tz_localize(UTC)
        w = bars5.loc[a0:a0 + pd.Timedelta(hours=6)]
        lv["asia"] = (float(w.high.max()), float(w.low.min())) if len(w) > 30 else None
        # London: 08:00 London up to, but NOT including, the bar that opens the NY session.
        # A .loc slice ending at t_open would include the 09:30-09:35 bar - the first bar
        # of the opening range itself.
        w = bars5.loc[ldn_time(day, 8):t_open - pd.Timedelta(minutes=5)]
        lv["london"] = (float(w.high.max()), float(w.low.min())) if len(w) > 30 else None
        # the completed hour before the NY open
        w = bars5.loc[t_open - pd.Timedelta(hours=1):t_open - pd.Timedelta(minutes=5)]
        lv["prev_hour"] = (float(w.high.max()), float(w.low.min())) if len(w) >= 8 else None
        out[d] = lv
    return out


def run(bars5: pd.DataFrame, range_min: int = 15, exit_spec: str = "ny+90m",
        stop_mode: str = "range_opp", stop_mult: float = 1.0,
        entry_deadline_min: int = 90, cost: float = 0.30,
        target_first: bool = False, min_target_r: float = 0.25,
        levels: dict | None = None, confirm_min: int = 5) -> pd.DataFrame:
    """exit_spec: a key of TIME_EXITS, or a name in LEVELS (target + stop).
       stop_mode : 'range_opp' (far side of the opening range) or 'mult' (stop_mult x range).
       target_first: if a bar contains both stop and target, assume the target filled.
                     Default False (stop first) is the conservative choice.
       levels    : output of build_levels(); computed on demand if not supplied.
       confirm_min: confirmation-candle length in minutes (5 is the finest the data allows)."""
    if levels is None and exit_spec not in TIME_EXITS and exit_spec != "measured_move":
        levels = build_levels(bars5)
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t_open = ny_time(day, 9, 30)
        t_rend = t_open + pd.Timedelta(minutes=range_min)
        t_dead = t_open + pd.Timedelta(minutes=entry_deadline_min)
        t_sess_end = ny_time(day, 16)

        win = bars5.loc[t_open:t_rend - pd.Timedelta(minutes=5)]
        if len(win) < range_min // 5:
            continue
        rhigh, rlow = float(win.high.max()), float(win.low.min())
        rsize = rhigh - rlow
        if rsize <= 0:
            continue

        rec = dict(day=d, t_open=t_open, range_high=rhigh, range_low=rlow, range_size=rsize)

        # ---- entry: first confirmation candle to CLOSE beyond the range.
        # Confirmation candles are anchored on the range end, so a 15-minute
        # confirmation means blocks running t_rend..t_rend+15m, +15m..+30m, and so on.
        side, t_fill, entry = 0, None, None
        step = pd.Timedelta(minutes=confirm_min)
        for ts, b in bars5.loc[t_rend:t_dead].iterrows():
            t_close = ts + pd.Timedelta(minutes=5)
            if t_close > t_dead:
                break
            if int((t_close - t_rend).total_seconds()) % int(step.total_seconds()) != 0:
                continue                       # not a confirmation-candle close
            blk = bars5.loc[t_close - step:ts]
            if not len(blk):
                continue
            c = float(blk.iloc[-1].close)
            if c > rhigh:
                side = 1
            elif c < rlow:
                side = -1
            if side:
                entry, t_fill = c, t_close
                break
        if not side:
            rows.append({**rec, "side": 0, "traded": False, "reason": "no_break"})
            continue

        # ---- exit specification
        stop = (rlow if side == 1 else rhigh) if stop_mode == "range_opp" \
            else entry - side * stop_mult * rsize
        target, t_exit, kind = None, t_sess_end, "time"
        if exit_spec in TIME_EXITS:
            t_exit = t_open + pd.Timedelta(minutes=TIME_EXITS[exit_spec])
            if t_exit <= t_fill:
                rows.append({**rec, "side": side, "traded": False, "reason": "exit_before_fill"})
                continue
        else:
            kind = "target"
            if exit_spec == "measured_move":
                target = entry + side * rsize
            else:
                lv = levels.get(d, {}).get(exit_spec)
                if lv is None:
                    rows.append({**rec, "side": side, "traded": False, "reason": "no_level"})
                    continue
                target = lv[0] if side == 1 else lv[1]
            # the level must still be ahead of us by a meaningful distance
            if side * (target - entry) < min_target_r * rsize:
                rows.append({**rec, "side": side, "traded": False, "reason": "target_behind"})
                continue

        # ---- walk the path
        path = bars5.loc[t_fill:t_exit]
        px, why, t_out = None, "time", t_exit
        for ts, b in path.iterrows():
            hit_s = (b.low <= stop) if side == 1 else (b.high >= stop)
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


def stats(df: pd.DataFrame):
    t = df[df.traded] if "traded" in df else df
    if len(t) < 25:
        return None
    p = t.pnl_oz
    pct = p / t.entry * 100
    w, l = p[p > 0].sum(), -p[p <= 0].sum()
    return dict(n=len(t), win=float((p > 0).mean()), pf=float(w / l) if l > 0 else np.inf,
                exp=float(p.mean()), total=float(p.sum()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else np.nan,
                hold=float(t.hold_min.mean()),
                tgt=float((t.why == "target").mean()), stp=float((t.why == "stop").mean()))
