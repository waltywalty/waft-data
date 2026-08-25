"""The daily-structure liquidity-sweep ("Judas sweep") strategy.

Rules as specified by the user, made mechanical:

  1. Daily bias from the FX-day chart (structure.daily_bias, lag-1 causal):
     bullish -> longs only, bearish -> shorts only, flat -> stand aside.
  2. Liquidity: unswept session highs/lows (Asia/London/NY) and previous-day
     highs/lows, tracked causally by structure.build_levels.
  3. At a session open, wait for a sweep AGAINST the bias: the first bar that
     trades through an unswept level on the counter-bias side, within
     sweep_window_min of the open.
  4. Watch the 5-minute chart: confirmation is the first 5m close back on the
     bias side of the swept level, within confirm_within_min of the sweep.
  5. Enter at that close, toward the daily structure. Stop beyond the sweep
     extreme. Targets: R-multiples, the nearest unswept opposite level, or the
     session close.

One trade per session per day; always flat by the session's own close.
"""
from __future__ import annotations
import pandas as pd, numpy as np, engine, structure
from zoneinfo import ZoneInfo

NY, LDN, UTC = structure.NY, structure.LDN, structure.UTC

# session open / forced-flat close, per calendar day
def _sessions(day: pd.Timestamp):
    ldn = lambda h, m=0: pd.Timestamp(day.year, day.month, day.day, h, m, tz=LDN).tz_convert(UTC)
    nyc = lambda h, m=0: pd.Timestamp(day.year, day.month, day.day, h, m, tz=NY).tz_convert(UTC)
    a0 = day.tz_localize(UTC)
    return {"asia": (a0 + pd.Timedelta(hours=1, minutes=30), ldn(8)),
            "london": (ldn(8), ldn(16, 30)),
            "ny": (nyc(9, 30), nyc(16)),
            # the canonical ICT killzones, anchored to New York local time:
            # London Judas window opens 02:00 ET, NY killzone opens 08:30 ET
            "ldnkz": (nyc(2), ldn(16, 30)),
            "nykz": (nyc(8, 30), nyc(16))}


def run(bars5: pd.DataFrame, lv: pd.DataFrame, bias: pd.Series,
        session: str = "ny", sweep_window_min: int = 120, confirm_within_min: int = 60,
        target: str = "2R", max_age_days: float = 5, cost: float = 0.30,
        min_r: float = 0.5, stop_at_level: bool = False,
        widen: float = 1.0) -> pd.DataFrame:
    """bias      : structure.daily_bias output (index = FX-day date, lag-1 causal).
       target    : '1R' | '2R' | '3R' | 'opp' (nearest unswept counter-side level)
                   | 'session_end'.
       min_r     : minimum stop distance in dollars (guards divide-by-nothing
                   trades where the sweep extreme sits at the entry).
       stop_at_level: stop at the swept level instead of the sweep extreme
                   (tighter; the practitioner "aggressive" variant).
       widen     : multiply the stop distance by this factor - practitioners
                   place stops beyond the sweep low with a buffer, not on it."""
    idx = bars5.index
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t_open, t_close = _sessions(day)[session]
        # the FX day this session belongs to (sessions here all end before 17:00 ET)
        fx_day = pd.Timestamp((t_open.tz_convert(NY) + pd.Timedelta(hours=7)).date())
        b = int(bias.get(fx_day, 0))
        rec = dict(day=d, session=session, bias=b, t_open=t_open)
        if b == 0:
            rows.append({**rec, "traded": False, "reason": "no_bias"})
            continue

        # ---- levels unswept at the session open, on the counter-bias side
        cand = structure.unswept_at(lv, t_open, side=-b, max_age_days=max_age_days)
        cand = cand[cand.t_swept.notna() & (cand.t_swept >= t_open)
                    & (cand.t_swept <= t_open + pd.Timedelta(minutes=sweep_window_min))
                    & (cand.t_swept < t_close)]
        if not len(cand):
            rows.append({**rec, "traded": False, "reason": "no_sweep"})
            continue
        t_sweep = cand.t_swept.min()
        hit = cand[cand.t_swept == t_sweep]
        # several levels can go in one bar; the reclaim that matters is the
        # shallowest one (first hit on the way down / up)
        lvrow = hit.loc[hit.price.idxmax()] if b == 1 else hit.loc[hit.price.idxmin()]
        level = float(lvrow.price)
        rec.update(level=level, level_kind=lvrow.kind, t_sweep=t_sweep)

        # ---- confirmation: first 5m close back on the bias side of the level
        t_cutoff = min(t_sweep + pd.Timedelta(minutes=confirm_within_min),
                       t_close - pd.Timedelta(minutes=5))
        w = bars5.loc[t_sweep:t_cutoff]
        conf_ts, entry = None, None
        for ts, bb in w.iterrows():
            c = float(bb.close)
            if (b == 1 and c > level) or (b == -1 and c < level):
                conf_ts, entry = ts, c
                break
        if conf_ts is None:
            rows.append({**rec, "traded": False, "reason": "no_reclaim"})
            continue
        t_fill = conf_ts + pd.Timedelta(minutes=5)
        ext_w = bars5.loc[t_sweep:conf_ts]
        extreme = float(ext_w.low.min()) if b == 1 else float(ext_w.high.max())
        stop = level if stop_at_level else extreme
        if b * (entry - stop) < min_r:
            rows.append({**rec, "traded": False, "reason": "stop_too_close"})
            continue
        stop = entry - b * widen * (b * (entry - stop))
        R = b * (entry - stop)
        rec.update(t_fill=t_fill, entry=entry, stop=stop, r_dollars=R,
                   sweep_depth=b * (level - extreme),
                   conf_min=(t_fill - t_sweep).total_seconds() / 60)

        # ---- target
        tgt = None
        if target in ("1R", "2R", "3R"):
            tgt = entry + b * float(target[0]) * R
        elif target == "opp":
            opp = structure.unswept_at(lv, t_fill, side=b, max_age_days=max_age_days)
            opp = opp[b * (opp.price - entry) >= 0.5 * R]
            if len(opp):
                tgt = float(opp.price.min()) if b == 1 else float(opp.price.max())
            # none ahead -> pure session-end hold, stop still active
        # 'session_end': no target at all

        # ---- walk the path to the session close
        path = bars5.loc[t_fill:t_close - pd.Timedelta(minutes=5)]
        px, why, t_out = None, "time", t_close
        for ts, bb in path.iterrows():
            hit_s = (bb.low <= stop) if b == 1 else (bb.high >= stop)
            hit_t = tgt is not None and ((bb.high >= tgt) if b == 1 else (bb.low <= tgt))
            if hit_s:                                    # conservative: stop first
                px, why, t_out = stop, "stop", ts
                break
            if hit_t:
                px, why, t_out = tgt, "target", ts
                break
        if px is None:
            px = engine.price_at(bars5, t_close)
            if px is None:
                rows.append({**rec, "traded": False, "reason": "no_exit_px"})
                continue

        rows.append({**rec, "traded": True, "reason": "ok", "side": b,
                     "target_px": tgt, "exit": px, "t_out": t_out, "why": why,
                     "pnl_oz": b * (px - entry) - cost,
                     "pnl_r": (b * (px - entry) - cost) / R,
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
                avg_r=float(t.pnl_r.mean()), hold=float(t.hold_min.mean()),
                tgt=float((t.why == "target").mean()), stp=float((t.why == "stop").mean()))
