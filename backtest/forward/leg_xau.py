"""Forward auto-journal leg: XAU (gold Asia-open range breakout, corr-gated) and the
XAUAUD half-leg. The frozen rule is backtest/forward/CONTRACT.md; the construction is
the repo's own trades.generate + the deployable.py corr gate, nothing re-implemented.

Inputs (all IBKR price-history JSON in data_dir, see CONTRACT.md):
  xauusd_5m_*.json     5m midpoint, UTC bar start   -> the trades.generate frame
  xauusd_daily_*.json  daily, 22:00 UTC bar start   -> gate: gold daily close
  audusd_daily_*.json  daily, 21:15 UTC bar start   -> gate: AUDUSD daily close
  audusd_5m_*.json     5m midpoint                  -> XAUAUD conversion

Daily-bar date label: a daily bar is labelled with the UTC calendar date on which its
session CLOSES (UTC date of bar start + 6 h: starts at/after 18:00Z roll to the next
date). The gold bar starting 2026-08-27T22:00Z (23:00Z in winter) is therefore the
2026-08-28 close, which is the label deployable.py gives the Athens-day close (Athens
midnight = 22:00 UTC in winter, 21:00 UTC in summer). The AUDUSD bar starting 21:15Z
(22:15Z in winter) on the 27th is likewise the 28th; IBKR's shortened post-holiday
sessions (start 00:00Z or 05:00Z) keep their own date. Measured on the archived CFD
feed and on the first real IBKR pull, gold has no prints between 21:00Z and 22:00Z in
summer, so the 22:00Z-boundary close is the same print as the Athens-midnight close
and the declared gate substitution changes nothing.

Gate index end (deployable.py line 17 and 23, kept exactly): the lagged correlation
exists only through the last JOINT daily label (gold AND AUDUSD). A session later than
that - the daily pull lagged the 5m pull - maps to NaN and is dropped, never gated on a
forward-filled stale value (which, one day behind, would even be a correlation computed
on a partial daily bar). Because the journal merge is add-only, a row emitted on such a
value would be permanent, whereas a dropped session is merely DEFERRED: rows()
recomputes everything at each check-in from the persisted files, so the session is
emitted at the first check-in whose daily files cover it. status() names the deferred
sessions and the lag. With same-time pulls IBKR's daily history already holds the
current session's (partial) bar, so the last joint label is the current session and
nothing is deferred; the current session's own gate value is shift(1) = data through
yesterday, untouched by the partial bar.

Public API:
  rows(data_dir)   -> list[dict]  XAU and XAUAUD journal rows (contract schema)
  status(data_dir) -> str
  compute(data_dir)-> dict of the intermediate frames (used by the test)
"""
from __future__ import annotations
import glob, json, os, sys
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

_HERE = os.path.dirname(os.path.abspath(__file__))
_BT = os.path.dirname(_HERE)
if _BT not in sys.path:
    sys.path.insert(0, _BT)
import engine, trades  # noqa: E402  (repo modules, imported unmodified)

NY = ZoneInfo("America/New_York")
L, STOP_R, COST, CUTOFF_LDN = 60, 2.0, 0.30, 8          # trades.generate arguments (frozen)
CORR_WINDOW, CORR_MAX = 20, 0.5                          # deployable.py gate (frozen)
AUD_TOL = pd.Timedelta(minutes=120)                      # max staleness of the AUDUSD 5m print
_COLS = ["open", "high", "low", "close", "volume"]


# ----------------------------------------------------------------------------- loaders
def load_ibkr(data_dir: str, pattern: str) -> pd.DataFrame:
    """Every IBKR price-history JSON matching pattern, concatenated into one UTC-indexed
    open/high/low/close/volume frame (engine.load_bars format). Files are read in sorted
    name order; on duplicate timestamps the LAST file read wins, so a later pull
    supersedes a partial bar from an earlier one. Volume is zero (midpoint bars)."""
    frames = []
    for f in sorted(glob.glob(os.path.join(data_dir, pattern))):
        with open(f) as fh:
            d = json.load(fh)
        t = d.get("time") or []
        if not t:
            continue
        df = pd.DataFrame({k: pd.to_numeric(d[k], errors="coerce") for k in ("open", "high", "low", "close")},
                          index=pd.to_datetime(t, utc=True))
        df["volume"] = 0.0
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=_COLS, index=pd.DatetimeIndex([], tz="UTC"), dtype=float)
    df = pd.concat(frames)
    df = df[~df.index.isna()].dropna(subset=["open", "high", "low", "close"])
    df = df.sort_index(kind="stable")
    df = df[~df.index.duplicated(keep="last")]
    df.index.name = "ts"
    return df[_COLS]


SESSION_ROLL = pd.Timedelta(hours=6)   # a daily bar starting at/after 18:00Z closes on the NEXT UTC date


def daily_close(bars: pd.DataFrame) -> pd.Series:
    """Daily close series labelled by the (tz-naive) UTC date on which each session
    closes: gold/FX sessions close 21:00-22:15Z, so a bar starting at/after 18:00Z
    (regular 22:00/23:00Z gold, 21:15/22:15Z AUD.USD) is the next date's close and a
    bar starting earlier (IBKR's shortened post-holiday sessions start 00:00Z or 05:00Z)
    is its own date's close."""
    if bars.empty:
        return pd.Series(dtype=float)
    lab = (bars.index + SESSION_ROLL).tz_convert(None).normalize()
    s = pd.Series(bars.close.to_numpy(dtype=float), index=lab)
    return s[~s.index.duplicated(keep="last")].sort_index()


# ---------------------------------------------------------------------------- corr gate
def corr_gate(gd: pd.Series, ad: pd.Series, window: int = CORR_WINDOW,
              extend_to: pd.Timestamp | None = None) -> pd.Series:
    """deployable.py lines 13-17: rolling `window`-day correlation of daily log returns,
    reindexed to calendar days, forward-filled, lagged one day (only data through
    yesterday). The index ends at the last joint daily observation, as in the rule;
    `extend_to` is for status()'s next-session PREVIEW only (never for gating rows)."""
    j = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
                  axis=1, join="inner").dropna()
    if j.empty:
        return pd.Series(dtype=float)
    end = j.index.max()
    if extend_to is not None and extend_to > end:
        end = extend_to
    return (j.g.rolling(window).corr(j.a)
             .reindex(pd.date_range(j.index.min(), end, freq="D")).ffill().shift(1))


# ------------------------------------------------------------------------- conversion
def _px_at(bars: pd.DataFrame, t: pd.Timestamp, tol: pd.Timedelta = AUD_TOL):
    """Price at wall-clock t: open of the bar starting at t, else the close of the last
    bar before t, provided that bar is within `tol` of t. None when unavailable."""
    if bars.empty:
        return None
    if t in bars.index:
        return float(bars.at[t, "open"])
    prior = bars.loc[:t]
    if len(prior) and (t - prior.index[-1]) <= tol:
        return float(prior.iloc[-1]["close"])
    return None


# ------------------------------------------------------------------------------- core
def compute(data_dir: str) -> dict:
    """Run the whole leg once and return the intermediates plus the journal rows."""
    g5 = load_ibkr(data_dir, "xauusd_5m_*.json")
    res = dict(g5=g5, gd=pd.Series(dtype=float), ad=pd.Series(dtype=float),
               C=pd.Series(dtype=float), trades_all=pd.DataFrame(), trades_kept=pd.DataFrame(),
               a5=pd.DataFrame(columns=_COLS), rows=[], skipped_aud=[], deferred=[], gate_end=pd.NaT)
    if g5.empty:
        return res
    gd = daily_close(load_ibkr(data_dir, "xauusd_daily_*.json"))
    ad = daily_close(load_ibkr(data_dir, "audusd_daily_*.json"))
    C = corr_gate(gd, ad)                # index ends at the last joint daily label (deployable.py line 17)
    gate_end = C.index.max() if len(C) else pd.NaT
    res.update(gd=gd, ad=ad, C=C, gate_end=gate_end)

    t = trades.generate(g5, L=L, stop_r=STOP_R, cost=COST, entry_cutoff_ldn=CUTOFF_LDN)
    if t.empty:
        return res
    days = pd.to_datetime(t.day).dt.normalize()
    t["c"] = days.map(C)                                           # deployable.py line 22
    res["trades_all"] = t
    # sessions after the gate's last label: NaN -> dropped now, emitted once daily data covers them
    later = (days > gate_end) if len(C) else pd.Series(True, index=t.index)
    res["deferred"] = sorted(str(d) for d in t.day[later & t.c.isna()])
    f = t.dropna(subset=["c"])                                     # line 23 (also drops the deferred)
    f = f[f.c <= CORR_MAX].reset_index(drop=True)                  # line 24
    res["trades_kept"] = f
    if f.empty:
        return res

    a5 = load_ibkr(data_dir, "audusd_5m_*.json")
    res["a5"] = a5
    rows, skipped = [], []
    for r in f.to_dict("records"):
        side, entry, exit_px, rng = int(r["side"]), float(r["entry"]), float(r["exit"]), float(r["range"])
        note = f"{r['reason']}|{L}m"
        base = dict(date=str(r["day"]), side="L" if side == 1 else "S", src="auto")
        rows.append(dict(base, instr="XAU", entry=round(entry, 2),
                         stop=round(entry - side * STOP_R * rng, 2), exit=round(exit_px, 2), note=note))
        a_in, a_out = _px_at(a5, r["t_fill"]), _px_at(a5, r["t_out"])
        if a_in is None or a_out is None:
            skipped.append(str(r["day"]))
            continue
        e_aud = entry / a_in
        rows.append(dict(base, instr="XAUAUD", entry=round(e_aud, 2),
                         stop=round(e_aud * (1 - side * STOP_R * rng / entry), 2),
                         exit=round(exit_px / a_out, 2), note="half|" + note))
    res.update(rows=rows, skipped_aud=skipped)
    return res


def rows(data_dir: str) -> list[dict]:
    """Journal rows for every gated XAU trade in data_dir and its XAUAUD conversion.
    Schema: date, instr ('XAU'|'XAUAUD'), side ('L'|'S'), entry, stop, exit, note, src."""
    return compute(data_dir)["rows"]


def status(data_dir: str) -> str:
    r = compute(data_dir)
    g5 = r["g5"]
    if g5.empty:
        return "XAU: no xauusd_5m_*.json bars"
    last = g5.index.max()
    day = pd.Timestamp(last.date())
    C, gd, ad, gate_end = r["C"], r["gd"], r["ad"], r["gate_end"]
    lines = [f"XAU 5m bars {g5.index.min():%Y-%m-%d %H:%M}Z -> {last:%Y-%m-%d %H:%M}Z ({len(g5)} bars)"]
    gate = lambda c: "n/a" if pd.isna(c) else ("OPEN" if c <= CORR_MAX else "CLOSED")
    if gd.empty or ad.empty or C.empty:
        lines.append("corr gate: MISSING daily data (gold %s, AUDUSD %s) - no trades pass, all breakouts deferred"
                     % ("ok" if not gd.empty else "none", "ok" if not ad.empty else "none"))
    else:
        lag = (day - gate_end).days
        lines.append(f"daily gold through {gd.index.max():%Y-%m-%d}, AUDUSD daily through {ad.index.max():%Y-%m-%d}; "
                     f"gate defined through {gate_end:%Y-%m-%d} (last joint daily label), "
                     + (f"{lag} day(s) BEHIND the 5m frame" if lag > 0 else "covers the 5m frame"))
        if day > gate_end:
            lines.append(f"corr gate on {day:%Y-%m-%d}: NOT DEFINED YET (frozen rule drops sessions after "
                         f"{gate_end:%Y-%m-%d}; they are emitted once a daily pull covers them)")
        else:
            c_day = C.get(day, np.nan)
            lines.append(f"corr gate (20d, lagged) on {day:%Y-%m-%d}: {c_day:.3f} {gate(c_day)}")
        nxt = day + pd.Timedelta(days=1)
        c_next = corr_gate(gd, ad, extend_to=nxt).get(nxt, np.nan)
        lines.append(f"preview for {nxt:%Y-%m-%d}: {c_next:.3f} {gate(c_next)} (latest available corr, "
                     f"possibly on a partial bar; binding only once the daily pull covers that session)")
    if r["deferred"]:
        dd = r["deferred"]
        lines.append(f"{len(dd)} breakout session(s) DEFERRED, no joint daily bar yet: {', '.join(dd[:6])}"
                     + (" +%d more" % (len(dd) - 6) if len(dd) > 6 else ""))
    n_xau = sum(1 for x in r["rows"] if x["instr"] == "XAU")
    n_aud = sum(1 for x in r["rows"] if x["instr"] == "XAUAUD")
    n_all = len(r["trades_all"])
    sk = r["skipped_aud"]
    lines.append(f"{n_all} raw breakout trades, {n_xau} pass the gate -> {n_xau} XAU rows, {n_aud} XAUAUD rows"
                 + (f" ({len(sk)} not converted, no AUDUSD 5m print within {int(AUD_TOL.total_seconds() // 60)} "
                    f"min: {', '.join(sk[:6])}{' +%d more' % (len(sk) - 6) if len(sk) > 6 else ''})"
                    if sk else ""))
    te = pd.Timestamp(day.year, day.month, day.day, 16, 0, tz=NY).tz_convert("UTC")
    if last < te - pd.Timedelta(minutes=30):
        lines.append(f"last session {day:%Y-%m-%d} INCOMPLETE (frame ends {last:%H:%M}Z, exit is "
                     f"{te:%H:%M}Z): a trade that day is emitted only once a later pull covers the exit")
    else:
        lines.append(f"last session {day:%Y-%m-%d} complete")
    return "\n".join(lines)


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_BT, "data", "forward")
    print(status(d))
    for x in rows(d):
        print(x)
