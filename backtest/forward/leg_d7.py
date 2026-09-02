"""D7 leg of the forward auto-journal (see CONTRACT.md).

Frozen rule: run_r28b_d7.py d7_trades (Connors/Alvarez "Double Seven", 7/200, long only,
no stop, as published) on the SPX daily closes in <data_dir>/spx_daily_*.json.  The state
machine in _run() is a transcription of run_r28b_d7.py lines 24-40 with one change of
INPUT only: the archive resampled the 5m CFD feed into UTC calendar-day bars, whereas the
forward feed already arrives as IBKR daily RTH bars (one bar per US session, bar start
13:30 UTC in summer / 14:30 UTC in winter = the session date).  Everything else is as
archived:

  * SMA200 on closes; 7-bar rolling closing low / high, both windows INCLUDING the
    current close (so "close <= low7" is a new 7-bar closing low);
  * the loop starts at bar index 200, i.e. the 201st bar is the first one evaluated
    (SMA200 already exists on the 200th bar, but the frozen code never acts on it);
  * enter at the signal close when close > SMA200 and close <= low7;
  * while in a position (from the next bar on) exit at the first close >= high7;
  * long only, no stop, one position at a time, no same-bar re-entry.

Rows: one per CLOSED trade; date = exit session date; side "L"; stop = entry (no stop);
note "d7|<bars> bars" where bars = exit index - entry index (the archive's `bars`).
Costs are NOT subtracted (the page / monthly review applies the stream's cost model).

Paper-trial scope (STREAM_START): the D7 paper stream was registered on 2026-08-27
(reference/goal_ledger.md, "Round 28b: Double Seven becomes paper stream 4 (user
decision, 2026-08-27)").  The IBKR pull is a year of history, so the state machine
finds closed trades from 2025 onwards; those are backtest-window / pre-registration
data, not forward evidence, and MUST NOT reach the journal or the SPRT.  A trade is
journalled only if its ENTRY signal fired on a session on/after STREAM_START (the
2026-08-27 close came after the registration decision that day).  A trade entered
before the stream start is not journalled even if it closes after it.  The state
machine still runs over the whole history, so a position carried into the stream
blocks new entries until it exits exactly as the frozen rule would, and the SMA200
warm-up is the real one.  `start=None` disables the filter (the archive verification
in test_leg_d7.py uses it); setting the module attribute STREAM_START = None does the
same for every default call.

Forward-only guard: an IBKR daily bar pulled during the session is a partial bar whose
"close" is just the last print.  A bar is used only once its RTH session has ended
(bar start + 6h30m <= now).  `now` defaults to the wall clock and can be overridden
(the test does this); on the archived data the guard is a no-op.  A bar dropped this
way is reported by status().

Public API:
  rows(data_dir, now=None, require_complete=True, start=STREAM)  -> list[dict]
      contract-schema journal rows: closed trades entered on/after the stream start
  status(data_dir, now=None, start=STREAM)                       -> str
      open position / regime state / stream-start bookkeeping
  compute(data_dir, now=None, require_complete=True, start=STREAM) -> dict
      intermediates: bars, d (sessions), incomplete, trades (ALL closed trades of the
      state machine), stream (the journalled subset), pos, pos_in_stream, ind, start, rows
`start`: STREAM (the default sentinel) -> the module's STREAM_START read at call time;
None -> no filter; a date / "YYYY-MM-DD" -> that boundary.
Verified against the archived backtest by test_leg_d7.py.
"""
from __future__ import annotations
import datetime as dt
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

INSTR = "D7"
PATTERN = "spx_daily_*.json"
SMA_N = 200                                  # c.rolling(200).mean()
WIN_N = 7                                    # c.rolling(7).min() / .max()
FIRST_BAR = 200                              # run_r28b_d7.py: for i in range(200, len(d))
MIN_BARS = FIRST_BAR + 1                     # fewer bars -> the loop evaluates nothing
RTH_LEN = pd.Timedelta(hours=6, minutes=30)  # 09:30-16:00 ET; bar start + RTH_LEN = session end
# goal_ledger.md Round 28b: "Double Seven becomes paper stream 4 (user decision, 2026-08-27)".
# Only trades ENTERED on/after this session date are forward evidence.
STREAM_START = dt.date(2026, 8, 27)
STREAM = "stream"                            # `start` sentinel: use STREAM_START at call time
_COLS = ["open", "high", "low", "close"]


# ----------------------------------------------------------------------------- loaders
def load_ibkr(data_dir: str, pattern: str = PATTERN) -> pd.DataFrame:
    """Every IBKR price-history JSON matching pattern (parallel `time`/`open`/`high`/
    `low`/`close` arrays, UTC bar start), concatenated into one UTC-indexed OHLC frame.
    Files are read in sorted name order; on duplicate timestamps the LAST file read
    wins, so a later pull supersedes an earlier one.  Rows without a close are dropped."""
    frames = []
    for f in sorted(glob.glob(os.path.join(data_dir, pattern))):
        with open(f) as fh:
            d = json.load(fh)
        t = d.get("time") or []
        if not t:
            continue
        df = pd.DataFrame({k: pd.to_numeric(d.get(k, [np.nan] * len(t)), errors="coerce")
                           for k in _COLS},
                          index=pd.to_datetime(t, utc=True))
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=_COLS, index=pd.DatetimeIndex([], tz="UTC"), dtype=float)
    df = pd.concat(frames)
    df = df[~df.index.isna()].dropna(subset=["close"])
    df = df.sort_index(kind="stable")
    df = df[~df.index.duplicated(keep="last")]
    df.index.name = "ts"
    return df[_COLS].astype(float)


def _now(now) -> pd.Timestamp:
    if now is None:
        return pd.Timestamp.now(tz="UTC")
    t = pd.Timestamp(now)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def _start(start):
    """Resolve the `start` argument to a datetime.date or None (no filter)."""
    if isinstance(start, str) and start == STREAM:
        start = STREAM_START
    if start is None:
        return None
    return pd.Timestamp(start).date()


def sessions(bars: pd.DataFrame, now=None, require_complete: bool = True) -> pd.DataFrame:
    """One row per US session: adds `date` (UTC calendar date of the bar start, which for
    a 13:30/14:30 UTC RTH bar is the session date), keeps the last bar per date, and --
    unless require_complete is False -- drops bars whose session has not ended by `now`
    (bar start + RTH_LEN > now), i.e. a partial bar from a mid-session pull."""
    d = bars.copy()
    d["date"] = d.index.date
    d = d[~d["date"].duplicated(keep="last")]
    if require_complete and len(d):
        d = d[d.index + RTH_LEN <= _now(now)]
    return d


# ------------------------------------------------------------------------------- core
def _run(d: pd.DataFrame):
    """run_r28b_d7.py lines 27-40 in effect, on the session frame `d` (needs `close`,
    uses `low` only for the archive's MAE statistic).  Returns (closed trades, open
    position or None, indicator frame).  A trade dict carries t_in/t_out (bar starts),
    date_in/date_out, entry, exit, bars, mae_pct."""
    c = d["close"]
    sma200 = c.rolling(SMA_N).mean()
    low7, high7 = c.rolling(WIN_N).min(), c.rolling(WIN_N).max()
    low = d["low"] if "low" in d else pd.Series(np.nan, index=d.index)
    tr, pos, mae = [], None, 0.0
    for i in range(FIRST_BAR, len(d)):
        if pos is None:
            if c.iloc[i] > sma200.iloc[i] and c.iloc[i] <= low7.iloc[i]:
                pos = (float(c.iloc[i]), i)
                mae = 0.0
        else:
            e, i0 = pos
            lo = float(low.iloc[i])
            if np.isfinite(lo):
                mae = max(mae, (e - lo) / e)
            if c.iloc[i] >= high7.iloc[i]:
                tr.append(dict(t_in=d.index[i0], t_out=d.index[i],
                               date_in=d["date"].iloc[i0], date_out=d["date"].iloc[i],
                               entry=e, exit=float(c.iloc[i]), bars=i - i0, mae_pct=mae))
                pos = None
    ind = pd.DataFrame(dict(close=c, sma200=sma200, low7=low7, high7=high7))
    return tr, pos, ind


def compute(data_dir: str, now=None, require_complete: bool = True, start=STREAM) -> dict:
    """Run the whole leg once and return the intermediates plus the journal rows.
    `trades` = every closed trade of the state machine over the whole history;
    `stream` = those entered on/after `start` (the journalled ones, rows built from
    them); `pos_in_stream` = the open position (if any) was entered on/after `start`."""
    s = _start(start)
    bars = load_ibkr(data_dir)
    dated = sessions(bars, now, require_complete=False)
    d = sessions(bars, now, require_complete)
    res = dict(bars=bars, d=d, incomplete=list(dated.index[~dated.index.isin(d.index)]),
               trades=[], stream=[], pos=None, pos_in_stream=False, ind=None, start=s, rows=[])
    if len(d) < MIN_BARS:
        return res
    tr, pos, ind = _run(d)
    kept = [t for t in tr if s is None or t["date_in"] >= s]
    res.update(trades=tr, stream=kept, pos=pos, ind=ind,
               pos_in_stream=pos is not None and (s is None or d["date"].iloc[pos[1]] >= s))
    res["rows"] = [dict(date=t["date_out"].isoformat(), instr=INSTR, side="L",
                        entry=t["entry"], stop=t["entry"], exit=t["exit"],
                        note=f"d7|{t['bars']} bars", src="auto") for t in kept]
    return res


def rows(data_dir: str, now=None, require_complete: bool = True, start=STREAM) -> list[dict]:
    """Journal rows per CONTRACT.md: every CLOSED trade in data_dir whose entry session is
    on/after the stream start (STREAM_START unless `start` says otherwise).  Empty when
    fewer than MIN_BARS (201) complete daily bars are available."""
    return compute(data_dir, now, require_complete, start)["rows"]


def status(data_dir: str, now=None, start=STREAM) -> str:
    """One line for the monthly report: 'open since <date> at <entry>' or 'flat', the last
    close vs SMA200 and the 7-day closing low/high, data extent, dropped partial bar,
    and the stream-start bookkeeping (journalled vs pre-stream closed trades)."""
    r = compute(data_dir, now, start=start)
    d = r["d"]
    if d.empty:
        return f"{INSTR}: insufficient history (no complete {PATTERN} bars)"
    span = f"{len(d)} daily bars {d['date'].iloc[0].isoformat()} .. {d['date'].iloc[-1].isoformat()}"
    drop = ("; last bar %s not used: session in progress" % r["incomplete"][-1].date().isoformat()
            if r["incomplete"] else "")
    if len(d) < MIN_BARS:
        return (f"{INSTR}: insufficient history ({len(d)} bars; the frozen loop first evaluates "
                f"bar {MIN_BARS}); {span}{drop}")
    ind, s = r["ind"], r["start"]
    i = len(d) - 1
    c, sm, lo, hi = (float(ind[k].iloc[i]) for k in ("close", "sma200", "low7", "high7"))
    if r["pos"] is not None:
        e, i0 = r["pos"]
        pre = ("" if r["pos_in_stream"] else
               f" [entered before the stream start {s.isoformat()}: its exit will not be journalled]")
        head = (f"open since {d['date'].iloc[i0].isoformat()} at {e:.2f}{pre} ({i - i0} bars held, "
                f"{c - e:+.2f} pts open); exit at the first close >= 7-day closing high {hi:.2f}")
    else:
        head = "flat; entry needs a close > SMA200 and <= the 7-day closing low"
    regime = (f"last close {d['date'].iloc[i].isoformat()} {c:.2f} "
              f"{'above' if c > sm else 'at/below'} SMA200 {sm:.2f}; "
              f"7-day closing low {lo:.2f} / high {hi:.2f}")
    n_pre = len(r["trades"]) - len(r["stream"])
    stream = (f"stream since {s.isoformat()}: {len(r['stream'])} closed trade(s) journalled, "
              f"{n_pre} earlier closed trade(s) (entry before the stream start) not journalled"
              if s is not None else
              f"no stream-start filter: {len(r['trades'])} closed trade(s) journalled")
    return f"{INSTR}: {head}; {regime}; {span}{drop}; {stream}"


if __name__ == "__main__":
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "forward")
    for x in rows(dd):
        print(x)
    print(status(dd))
