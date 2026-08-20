"""Bias -> liquidity sweep -> reclaim -> entry.

  1. Opening range of L minutes from 09:30 HKT. BIAS = direction of the first
     L-candle to close beyond it (same bias signal as before).
  2. Wait for a SWEEP: price trades through a liquidity level on the opposite
     side of the bias (a stop-run against the bias).
  3. Require a RECLAIM: within `reclaim_bars` 5-minute bars, price closes back
     on the correct side of that level - the rejection.
  4. Enter at the reclaim close, in the BIAS direction. Optional stop under the
     sweep extreme. Exit at a fixed session clock time.
"""
from __future__ import annotations
import pandas as pd, numpy as np, engine
from zoneinfo import ZoneInfo

# session exit anchors: (timezone, hour, minute) - DST handled per date
ANCHORS = {
    "pre_london":  ("Europe/London",    7,  0),
    "london_open": ("Europe/London",    8,  0),
    "asia_close":  ("Asia/Hong_Kong",  16,  0),
    "london_mid":  ("Europe/London",   12,  0),
    "pre_ny":      ("America/New_York", 9,  0),
    "london_late": ("Europe/London",   16,  0),
    "ny_close":    ("America/New_York",16,  0),
}
ANCHOR_ORDER = ["pre_london", "london_open", "asia_close", "london_mid",
                "pre_ny", "london_late", "ny_close"]

def anchor_utc(day: pd.Timestamp, name: str) -> pd.Timestamp:
    tz, h, m = ANCHORS[name]
    return pd.Timestamp(day.year, day.month, day.day, h, m, tz=ZoneInfo(tz)).tz_convert("UTC")


def swing_levels(b5: pd.DataFrame, k: int = 2):
    """Fractal swing highs/lows: extreme of the k bars either side."""
    hi, lo = b5.high.values, b5.low.values
    n = len(hi)
    is_hi = np.zeros(n, bool); is_lo = np.zeros(n, bool)
    for i in range(k, n - k):
        w_h, w_l = hi[i-k:i+k+1], lo[i-k:i+k+1]
        is_hi[i] = hi[i] == w_h.max() and (w_h.argmax() == k)
        is_lo[i] = lo[i] == w_l.min() and (w_l.argmin() == k)
    return is_hi, is_lo


def run(bars5, range_min=30, liq="dyn_swing", reclaim_bars=3, entry_cutoff="london_open",
        cost_usd=0.30, stop_at_sweep=False, invert=False, swing_k=2,
        lookback_h=6, require_hold_range=True, below_breakout=True):
    """Returns one row per day with the sweep-entry outcome and, for comparison,
    the plain breakout entry on the same day."""
    barsL = engine.resample(bars5, range_min)
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t0 = engine.session_start_utc(day)
        t_rng_end = t0 + pd.Timedelta(minutes=range_min)
        t_cut = anchor_utc(day, entry_cutoff)
        if t0 not in barsL.index or t_cut <= t_rng_end:
            continue
        if len(bars5.loc[t0:t_rng_end - pd.Timedelta(minutes=1)]) < range_min // 5:
            continue
        rng = barsL.loc[t0]
        rhigh, rlow = float(rng.high), float(rng.low)
        if rhigh <= rlow:
            continue
        rec = dict(day=day.date(), range_high=rhigh, range_low=rlow, range_size=rhigh - rlow)

        # ---- 1. bias -------------------------------------------------------
        bias, t_bias = 0, None
        for ts, b in barsL.loc[t_rng_end:t_cut].iterrows():
            if ts >= t_cut:
                break
            if b.close > rhigh:
                bias, t_bias = 1, ts; break
            if b.close < rlow:
                bias, t_bias = -1, ts; break
        if bias == 0:
            rows.append({**rec, "bias": 0, "traded": False, "reason": "no_bias"}); continue
        rec.update(bias=bias, t_bias=t_bias,
                   breakout_px=float(barsL.at[t_bias, "close"]))
        side = -bias if invert else bias

        # ---- 2. the liquidity level to be swept (counter to the bias) ------
        t_start = t_bias + pd.Timedelta(minutes=range_min)
        after = bars5.loc[t_start:t_cut]
        if not len(after):
            rows.append({**rec, "traded": False, "reason": "no_window"}); continue
        look_from = t0 - pd.Timedelta(hours=lookback_h)
        pre = bars5.loc[look_from:t_start]
        if not len(pre):
            rows.append({**rec, "traded": False, "reason": "no_prev"}); continue

        static_lvl = None
        if liq == "range_opp":
            static_lvl = rlow if bias == 1 else rhigh
        elif liq == "session_extreme":
            s = bars5.loc[t0:t_start]
            static_lvl = float(s.low.min()) if bias == 1 else float(s.high.max())
        elif liq == "prev_day":
            p = bars5.loc[t0 - pd.Timedelta(hours=23):t0]
            if not len(p):
                rows.append({**rec, "traded": False, "reason": "no_prev"}); continue
            static_lvl = float(p.low.min()) if bias == 1 else float(p.high.max())
        elif liq == "breakout_low":
            bo = bars5.loc[t_bias:t_start]
            static_lvl = float(bo.low.min()) if bias == 1 else float(bo.high.max())
        elif liq != "dyn_swing":
            raise ValueError(liq)

        # ---- 3. sweep, then reclaim ---------------------------------------
        # For dyn_swing the level is the most recent CONFIRMED fractal swing on the
        # counter side, updated bar by bar; a fractal at i is only known at i+k.
        t_fill = entry = None; sweep_ext = np.nan; used_lvl = static_lvl
        seq = bars5.loc[look_from:t_cut]
        s_hi, s_lo = swing_levels(seq, swing_k)
        s_flags = s_lo if bias == 1 else s_hi
        s_px = seq.low.values if bias == 1 else seq.high.values
        s_idx = seq.index
        start_pos = int(s_idx.searchsorted(t_start))
        vals = seq[["high", "low", "close"]].values
        i = start_pos
        while i < len(vals):
            if liq == "dyn_swing":
                known = np.where(s_flags[:max(i - swing_k + 1, 0)])[0]
                if not len(known):
                    i += 1; continue
                lvl = float(s_px[known[-1]])
            else:
                lvl = static_lvl
            if below_breakout:
                bp = rec["breakout_px"]
                if (lvl >= bp) if bias == 1 else (lvl <= bp):
                    i += 1; continue
            hi, lo, cl = vals[i]
            swept = (lo < lvl) if bias == 1 else (hi > lvl)
            if swept:
                ext = lo if bias == 1 else hi
                ok = True
                if require_hold_range:
                    ok = (ext > rlow) if bias == 1 else (ext < rhigh)
                if ok:
                    for j in range(i, min(i + reclaim_bars, len(vals))):
                        hj, lj, cj = vals[j]
                        ext = min(ext, lj) if bias == 1 else max(ext, hj)
                        if require_hold_range and ((ext <= rlow) if bias == 1 else (ext >= rhigh)):
                            break
                        reclaimed = (cj > lvl) if bias == 1 else (cj < lvl)
                        if reclaimed:
                            t_fill, entry, sweep_ext, used_lvl = (
                                s_idx[j] + pd.Timedelta(minutes=5), cj, ext, lvl)
                            break
                if t_fill is not None:
                    break
                i += reclaim_bars
                continue
            i += 1
        if t_fill is None or t_fill >= t_cut:
            rows.append({**rec, "traded": False, "reason": "no_sweep_reclaim"}); continue
        rec["liq_level"] = used_lvl

        rec.update(t_fill=t_fill, entry=entry, sweep_ext=sweep_ext,
                   sweep_depth=abs(entry - sweep_ext),
                   wait_min=(t_fill - t_bias).total_seconds() / 60)

        # ---- 4. exits at every anchor -------------------------------------
        out = {**rec, "side": side, "traded": True, "reason": "ok"}
        for a in ANCHOR_ORDER:
            t_exit = anchor_utc(day, a)
            if t_exit <= t_fill:
                out[f"pnl_{a}"] = np.nan; continue
            px = None; reason = "time"
            if stop_at_sweep:
                path = bars5.loc[t_fill:t_exit]
                stop = sweep_ext
                hit = path[(path.low <= stop) if side == 1 else (path.high >= stop)]
                if len(hit):
                    px, reason = stop, "stop"
            if px is None:
                px = engine.price_at(bars5, t_exit)
            if px is None:
                out[f"pnl_{a}"] = np.nan; continue
            out[f"pnl_{a}"] = side * (px - entry) - cost_usd
            out[f"exit_{a}"] = px
            out[f"why_{a}"] = reason
            # control: same bias, entered at the breakout close instead
            out[f"ctl_{a}"] = bias * (px - rec["breakout_px"]) - cost_usd
        rows.append(out)
    return pd.DataFrame(rows)


def stats(df, col, entry_col="entry"):
    if col not in df.columns or "traded" not in df.columns or not df.traded.any():
        return None
    x = df[df.traded & df[col].notna()]
    if len(x) < 20:
        return None
    p = x[col]
    w, l = p[p > 0].sum(), -p[p <= 0].sum()
    pct = p / x[entry_col] * 100
    return dict(n=len(x), win=(p > 0).mean(), pf=(w / l if l > 0 else np.inf),
                exp=p.mean(), total=p.sum(),
                t=pct.mean() / pct.std() * np.sqrt(len(pct)) if pct.std() else np.nan)


def _last_known_swing(seq, bias, k):
    """For each bar, the most recent CONFIRMED fractal swing on the counter side.
    A fractal at i is only confirmed at i+k, so the series is causal."""
    s_hi, s_lo = swing_levels(seq, k)
    flags = s_lo if bias == 1 else s_hi
    px = seq.low.values if bias == 1 else seq.high.values
    lvl = np.full(len(px), np.nan)
    lvl[np.where(flags)[0] + k] = px[np.where(flags)[0]] if len(np.where(flags)[0]) else []
    return pd.Series(lvl).ffill().values


def structure_stop(bars5, range_min=30, entry_cutoff="london_open", cost_usd=0.30,
                   swing_k=2, lookback_h=6, buffer_r=0.0, mode="trail"):
    """Enter at the breakout (the original signal), then use the SWEEP as an EXIT:
    leave when price takes out the most recent confirmed swing on the counter side.
    mode 'trail' updates the level as new swings form; 'fixed' keeps the first one."""
    barsL = engine.resample(bars5, range_min)
    rows = []
    for d in pd.Series(bars5.index.date, index=bars5.index).unique():
        day = pd.Timestamp(d)
        t0 = engine.session_start_utc(day)
        t_rng_end = t0 + pd.Timedelta(minutes=range_min)
        t_cut = anchor_utc(day, entry_cutoff)
        if t0 not in barsL.index or t_cut <= t_rng_end:
            continue
        if len(bars5.loc[t0:t_rng_end - pd.Timedelta(minutes=1)]) < range_min // 5:
            continue
        rng = barsL.loc[t0]
        rhigh, rlow = float(rng.high), float(rng.low)
        if rhigh <= rlow:
            continue
        bias, t_bias = 0, None
        for ts, b in barsL.loc[t_rng_end:t_cut].iterrows():
            if ts >= t_cut: break
            if b.close > rhigh: bias, t_bias = 1, ts; break
            if b.close < rlow:  bias, t_bias = -1, ts; break
        if bias == 0:
            continue
        entry = float(barsL.at[t_bias, "close"])
        t_fill = t_bias + pd.Timedelta(minutes=range_min)
        buf = buffer_r * (rhigh - rlow)

        seq = bars5.loc[t0 - pd.Timedelta(hours=lookback_h):
                        t0 + pd.Timedelta(hours=32)]
        lvl = _last_known_swing(seq, bias, swing_k)
        idx = seq.index
        start = int(idx.searchsorted(t_fill))
        if mode == "fixed":
            v = lvl[start] if start < len(lvl) else np.nan
            lvl = np.full(len(lvl), v)
        thr = lvl - buf if bias == 1 else lvl + buf
        breach = (seq.low.values <= thr) if bias == 1 else (seq.high.values >= thr)
        breach &= ~np.isnan(thr)

        rec = dict(day=day.date(), bias=bias, entry=entry, t_fill=t_fill,
                   range_size=rhigh - rlow, traded=True)
        for a in ANCHOR_ORDER:
            t_exit = anchor_utc(day, a)
            if t_exit <= t_fill:
                rec[f"pnl_{a}"] = np.nan; continue
            end = int(idx.searchsorted(t_exit))
            seg = breach[start:end]
            hit = int(np.argmax(seg)) if seg.any() else -1
            if hit >= 0:
                ex, stopped = float(thr[start + hit]), True
            else:
                ex, stopped = engine.price_at(bars5, t_exit), False
            if ex is None:
                rec[f"pnl_{a}"] = np.nan; continue
            rec[f"pnl_{a}"] = bias * (ex - entry) - cost_usd
            rec[f"stopped_{a}"] = stopped
        rows.append(rec)
    return pd.DataFrame(rows)
