"""Opening-range breakout engine for XAUUSD, anchored to 09:30 HKT.

Strategy (as specified):
  * At 09:30 HKT (= 01:30 UTC, HKT has no DST) form an opening range candle of
    length L minutes (5 / 15 / 30).
  * Watch subsequent L-minute candles. The first candle to CLOSE above the range
    high goes long; the first to CLOSE below the range low goes short.
  * Hold until a fixed clock time in the London session, then exit at market.
  * One trade per day, first breakout only, no stop unless requested.
"""
from __future__ import annotations
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")
LONDON = ZoneInfo("Europe/London")
HK = ZoneInfo("Asia/Hong_Kong")

# London-session exit anchors, expressed in London local time
EXITS = {
    "pre_london":   (7, 0),    # 07:00 London — one hour before the open
    "london_open":  (8, 0),    # 08:00 London — session start
    "london_mid":   (12, 0),   # 12:00 London — middle
    "london_close": (16, 30),  # 16:30 London — session end
}
RANGE_START_HKT = (9, 30)


def load_bars(path: str = "data/XAUUSD_5m.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df.Date.astype(str) + " " + df.Time, format="%Y%m%d %H:%M:%S", utc=True)
    df = df.set_index("ts").sort_index()
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["open", "high", "low", "close", "volume"]
    return df[~df.index.duplicated()]


def resample(bars: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregate to `minutes` candles, with the bin grid anchored on 01:30 UTC
    (the 09:30 HKT session start) so the opening candle is always a bin edge."""
    if minutes == 5:
        return bars
    anchor = (RANGE_START_HKT[0] - 8) % 24 * 60 + RANGE_START_HKT[1]   # 01:30 UTC -> 90 min
    return bars.resample(f"{minutes}min", offset=f"{anchor % minutes}min").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"), volume=("volume", "sum")
    ).dropna(subset=["open"])


def session_start_utc(day: pd.Timestamp) -> pd.Timestamp:
    """09:30 Hong Kong on `day`, in UTC. HKT is UTC+8 year-round."""
    local = pd.Timestamp(day.year, day.month, day.day, *RANGE_START_HKT, tz=HK)
    return local.tz_convert(UTC)


def exit_utc(day: pd.Timestamp, anchor: str) -> pd.Timestamp:
    """London-session exit time for the *same* calendar day, in UTC (handles BST)."""
    h, m = EXITS[anchor]
    local = pd.Timestamp(day.year, day.month, day.day, h, m, tz=LONDON)
    return local.tz_convert(UTC)


def price_at(bars5: pd.DataFrame, t: pd.Timestamp, tol_min: int = 30):
    """Traded price at wall-clock time t: open of the 5m bar starting at t,
    else the last close within `tol_min` before t."""
    if t in bars5.index:
        return float(bars5.at[t, "open"])
    prior = bars5.loc[:t]
    if len(prior) and (t - prior.index[-1]) <= pd.Timedelta(minutes=tol_min):
        return float(prior.iloc[-1]["close"])
    return None


def backtest(bars5: pd.DataFrame, range_min: int, exit_anchor: str,
             cost_usd: float = 0.30, fill: str = "close",
             stop_at_range: bool = False, breakout_deadline: str | None = None) -> pd.DataFrame:
    """Run one configuration. Returns a trade log (one row per trading day attempted).

    fill: "close" -> filled at the breakout candle's close (market-on-close of that candle)
          "next_open" -> filled at the next candle's open (strictly conservative)
    breakout_deadline: None -> breakout must occur before the exit time.
                       otherwise an EXITS key used as the cutoff.
    """
    barsL = resample(bars5, range_min)
    days = pd.Series(bars5.index.date, index=bars5.index).unique()
    rows = []

    for d in days:
        day = pd.Timestamp(d)
        t0 = session_start_utc(day)                    # 01:30 UTC
        t_range_end = t0 + pd.Timedelta(minutes=range_min)
        t_exit = exit_utc(day, exit_anchor)
        t_deadline = t_exit if breakout_deadline is None else exit_utc(day, breakout_deadline)
        if t_deadline > t_exit:
            t_deadline = t_exit

        if t0 not in barsL.index:                      # weekend / holiday / gap
            continue
        rng = barsL.loc[t0]
        # require the range window to be fully populated at 5m granularity
        window5 = bars5.loc[t0:t_range_end - pd.Timedelta(minutes=1)]
        if len(window5) < range_min // 5:
            continue

        rhigh, rlow = float(rng.high), float(rng.low)
        rec = dict(day=day.date(), t0=t0, range_min=range_min, exit_anchor=exit_anchor,
                   range_high=rhigh, range_low=rlow, range_size=rhigh - rlow,
                   range_open=float(rng.open), range_close=float(rng.close))

        fwd = barsL.loc[t_range_end:t_deadline]
        fwd = fwd[fwd.index < t_deadline]
        side, t_entry, entry = 0, None, None
        for ts, b in fwd.iterrows():
            if b.close > rhigh:
                side, t_entry = 1, ts
                break
            if b.close < rlow:
                side, t_entry = -1, ts
                break

        if side == 0:
            rows.append({**rec, "side": 0, "traded": False})
            continue

        if fill == "close":
            entry = float(fwd.at[t_entry, "close"])
            t_fill = t_entry + pd.Timedelta(minutes=range_min)
        else:
            t_fill = t_entry + pd.Timedelta(minutes=range_min)
            entry = price_at(bars5, t_fill)
        if entry is None:
            rows.append({**rec, "side": 0, "traded": False})
            continue

        # path between fill and exit, for MFE/MAE and optional stop
        path = bars5.loc[t_fill:t_exit]
        exit_px, exit_reason, t_out = None, "time", t_exit
        if stop_at_range and len(path):
            stop = rlow if side == 1 else rhigh
            hit = path[(path.low <= stop) if side == 1 else (path.high >= stop)]
            if len(hit):
                exit_px, exit_reason, t_out = stop, "stop", hit.index[0]
                path = bars5.loc[t_fill:t_out]
        if exit_px is None:
            exit_px = price_at(bars5, t_exit)
            if exit_px is None:
                rows.append({**rec, "side": 0, "traded": False})
                continue

        pnl = side * (exit_px - entry) - cost_usd
        mfe = mae = np.nan
        if len(path):
            if side == 1:
                mfe, mae = path.high.max() - entry, entry - path.low.min()
            else:
                mfe, mae = entry - path.low.min(), path.high.max() - entry

        rows.append({**rec, "side": side, "traded": True, "t_entry": t_entry, "t_fill": t_fill,
                     "entry": entry, "t_out": t_out, "exit": exit_px, "exit_reason": exit_reason,
                     "pnl_usd": pnl, "pnl_pct": pnl / entry * 100,
                     "hold_min": (t_out - t_fill).total_seconds() / 60,
                     "mfe": mfe, "mae": mae,
                     "brk_delay_min": (t_entry - t_range_end).total_seconds() / 60})

    return pd.DataFrame(rows)


def metrics(trades: pd.DataFrame, label: str = "") -> dict:
    t = trades[trades.traded].copy()
    if not len(t):
        return {"label": label, "n": 0}
    wins, losses = t[t.pnl_usd > 0], t[t.pnl_usd <= 0]
    gross_w, gross_l = wins.pnl_pct.sum(), -losses.pnl_pct.sum()
    eq = t.sort_values("t_fill").pnl_pct.cumsum()
    dd = (eq.cummax() - eq).max()
    yrs = (t.t_fill.max() - t.t_fill.min()).days / 365.25
    sd = t.pnl_pct.std()
    return {
        "label": label,
        "days": len(trades), "n": len(t), "trade_rate": len(t) / max(len(trades), 1),
        "long": int((t.side == 1).sum()), "short": int((t.side == -1).sum()),
        "win_rate": (t.pnl_usd > 0).mean(),
        "profit_factor": gross_w / gross_l if gross_l > 0 else np.inf,
        "exp_usd": t.pnl_usd.mean(), "exp_pct": t.pnl_pct.mean(),
        "avg_win_usd": wins.pnl_usd.mean() if len(wins) else 0,
        "avg_loss_usd": losses.pnl_usd.mean() if len(losses) else 0,
        "payoff": (wins.pnl_usd.mean() / -losses.pnl_usd.mean()) if len(losses) and losses.pnl_usd.mean() != 0 else np.inf,
        "total_pct": t.pnl_pct.sum(), "max_dd_pct": dd,
        "sharpe_ann": (t.pnl_pct.mean() / sd * np.sqrt(len(t) / yrs)) if sd and yrs else np.nan,
        "t_stat": (t.pnl_pct.mean() / sd * np.sqrt(len(t))) if sd else np.nan,
    }
