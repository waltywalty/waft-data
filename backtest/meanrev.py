"""Band mean-reversion on XAUUSD: fade a close that stretches k standard
deviations from a rolling mean, target the mean.

The "2.6 standard deviation pullback" the user asked about is a band strategy;
this engine parameterises the family so the specific 2.6-sigma variant and its
neighbours can be compared on a gradient rather than at a single point.

Signal timeframe is resampled from 5-minute bars; execution walks the 5-minute
path. Entries happen at the CLOSE of a signal bar (a price that existed); the
mean and sigma used for entry, stop and target are FROZEN at the entry bar -
they are fully known at fill time, and freezing them keeps the exits honest
(a trailing mean would need bar-by-bar re-evaluation, tested separately).

Positions: one at a time, flat by the session close (17:00 ET) of every day,
and never held longer than max_hold_min.
"""
from __future__ import annotations
import pandas as pd, numpy as np, engine
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

# entry-hour sessions, in UTC hours (gold day: Asia ~00-07, London 07-12, NY 13-21)
SESSIONS = {"all": range(24), "asia": range(0, 7), "london": range(7, 13), "ny": range(13, 21)}


def day_end_utc(ts: pd.Timestamp) -> pd.Timestamp:
    """17:00 New York on the FX day that contains ts."""
    loc = ts.tz_convert(NY)
    d = loc.normalize() + pd.Timedelta(hours=17)
    if loc >= d:
        d += pd.Timedelta(days=1)
    return d.tz_convert(UTC)


def run(bars5: pd.DataFrame, tf: int = 15, n: int = 20, k: float = 2.6,
        trigger: str = "close_back", target: str = "mean", stop_k: float | None = 1.0,
        max_hold_min: int = 240, session: str = "all", cost: float = 0.30) -> pd.DataFrame:
    """tf        : signal timeframe in minutes (5-minute data resampled).
       n, k      : rolling window and band width in standard deviations.
       trigger   : 'close_out'  - enter on the first close beyond the k-sigma band;
                   'close_back' - price must close beyond, then close back inside:
                                  enter on the re-entry close (the practitioners'
                                  "confirmation" variant).
       target    : 'mean' (the frozen rolling mean) or 'half' (halfway back).
       stop_k    : stop this many FROZEN sigmas beyond the entry, against the
                   trade; None = no stop (timeout / day end only).
       session   : restrict ENTRIES to these UTC hours; exits run to completion.
    """
    tfb = bars5.resample(f"{tf}min").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    m = tfb.close.rolling(n).mean()
    sd = tfb.close.rolling(n).std()
    z = (tfb.close - m) / sd
    hours = set(SESSIONS[session])

    idx = tfb.index
    rows = []
    busy_until = idx[0]
    zv, zp = z.values, z.shift(1).values
    cv, mv, sdv = tfb.close.values, m.values, sd.values
    ok = np.isfinite(zv) & np.isfinite(zp) & (sdv > 0)
    if trigger == "close_out":
        sides = np.where(ok & (zv <= -k) & (zp > -k), 1,
                np.where(ok & (zv >= k) & (zp < k), -1, 0))
    else:  # close_back
        sides = np.where(ok & (zp <= -k) & (zv > -k) & (zv < 0), 1,
                np.where(ok & (zp >= k) & (zv < k) & (zv > 0), -1, 0))
    for i in np.nonzero(sides)[0]:
        if i <= n:
            continue
        ts = idx[i]
        t_close = ts + pd.Timedelta(minutes=tf)          # bars are open-stamped
        if t_close < busy_until:
            continue
        if t_close.hour not in hours:
            continue
        side = int(sides[i])

        # how many consecutive closes sat beyond the band before this signal -
        # the practitioners' band-walk veto needs it (1 = a single poke)
        exc = 0
        j = i - 1
        while j > n and np.isfinite(zv[j]) and (zv[j] <= -k if side == 1 else zv[j] >= k):
            exc += 1
            j -= 1

        entry = float(cv[i])
        mu, sig = float(mv[i]), float(sdv[i])
        tgt = mu if target == "mean" else (entry + mu) / 2
        if side * (tgt - entry) <= 0:
            continue                                     # already through the mean
        stop = entry - side * stop_k * sig if stop_k is not None else None

        t_exit = min(t_close + pd.Timedelta(minutes=max_hold_min), day_end_utc(t_close))
        # 5-minute path from the first bar AFTER the signal close to one bar
        # short of t_exit (open-stamped bars; right endpoint excluded)
        path = bars5.loc[t_close:t_exit - pd.Timedelta(minutes=5)]
        px, why, t_out = None, "time", t_exit
        for pts, b in path.iterrows():
            hit_s = stop is not None and ((b.low <= stop) if side == 1 else (b.high >= stop))
            hit_t = (b.high >= tgt) if side == 1 else (b.low <= tgt)
            if hit_s and hit_t:
                px, why, t_out = stop, "stop", pts       # conservative: stop first
                break
            if hit_s:
                px, why, t_out = stop, "stop", pts
                break
            if hit_t:
                px, why, t_out = tgt, "target", pts
                break
        if px is None:
            px = engine.price_at(bars5, t_exit)
            if px is None:
                continue
        busy_until = t_out + pd.Timedelta(minutes=5)

        rows.append(dict(t_signal=ts, t_fill=t_close, side=side, entry=entry,
                         mean=mu, sigma=sig, z=float(zv[i]), exc_len=exc,
                         stop=stop, target=tgt,
                         exit=px, t_out=t_out, why=why,
                         pnl_oz=side * (px - entry) - cost,
                         hold_min=(t_out - t_close).total_seconds() / 60))
    return pd.DataFrame(rows)


def stats(df: pd.DataFrame):
    if len(df) < 25:
        return None
    p = df.pnl_oz
    pct = p / df.entry * 100
    w, l = p[p > 0].sum(), -p[p <= 0].sum()
    return dict(n=len(df), win=float((p > 0).mean()), pf=float(w / l) if l > 0 else np.inf,
                exp=float(p.mean()), total=float(p.sum()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else np.nan,
                hold=float(df.hold_min.mean()),
                tgt=float((df.why == "target").mean()), stp=float((df.why == "stop").mean()))
