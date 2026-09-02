"""PMI leg of the forward auto-journal (see CONTRACT.md; goal_ledger.md "PMI stream
tracking spec (frozen)").

Frozen rule.  The regime is the LAST ISM Manufacturing PMI release STRICTLY BEFORE the
session (run_r61_pmi.py build_days: a release becomes effective from the first session
after its date; the session ON the release date is still governed by the previous
release).  The regime is active (long) while that value is < 50, flat otherwise; sessions
before the first known release have no regime.  The archived backtest booked every
active session close-to-close; the journal aggregates those bookings per calendar month
and leg (SPX / NDX / RUT cash indices standing in for MES / MNQ / M2K):

  * entry = close of the last session BEFORE the month's first active session -- the
    prior month's last close when the regime was already active at the month start;
  * exit  = close of the month's last active session;
  * side "L", stop = entry (no stop), note "<leg>|<n> sessions", date = last active
    session, src "auto".

Because the daily bookings telescope, (exit - entry) of a month row equals the sum of the
archive's close-to-close bookings over that month's active sessions (checked to float
precision in test_leg_pmi.py).  Costs are NOT subtracted (MICRO/20 per booking is applied
at review).

Inputs: <data_dir>/ism_pmi.json (list of {release, month, value}; empty or missing ->
no regime, no rows) and <data_dir>/{spx,ndx,rut}_daily_*.json (IBKR daily RTH bars,
13:30/14:30 UTC bar start = session date), loaded with leg_d7.load_ibkr / leg_d7.sessions
so the schema handling and the partial-bar guard (a bar is used only once bar start +
6h30m <= now) are the same as the D7 leg's.

Journal timing.  The dedup key is (date, instr, note); for a month still in progress both
change at every check-in, so rows() emits a month only once it is CLOSED -- the calendar
month is over, or a complete session after its last active session exists (the regime
ended inside the month).  The in-progress month is reported by status() (like D7's open
position); rows(include_open=True) adds it as a row.

Public API:
  rows(data_dir, now=None, include_open=False) -> list[dict]  contract-schema rows
  status(data_dir, now=None)                    -> str         latest print, regime, days
  compute(data_dir, now=None)                   -> dict        intermediates
  load_releases / regime_levels / month_blocks                 building blocks (tested)
"""
from __future__ import annotations
import calendar
import datetime as _dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import leg_d7  # noqa: E402  (same IBKR daily schema: load_ibkr(), sessions(), _now())

INSTR = "PMI"
THR = 50.0                                   # run_r61_pmi.py winner cell: d.pmi < 50
PMI_FILE = "ism_pmi.json"
LEGS = (("SPX", "spx_daily_*.json"), ("NDX", "ndx_daily_*.json"), ("RUT", "rut_daily_*.json"))
LEG_ORDER = {leg: i for i, (leg, _) in enumerate(LEGS)}
REF_LEG = "SPX"                              # calendar used for "days in regime"


# ----------------------------------------------------------------------------- inputs
def load_releases(data_dir: str) -> list[tuple]:
    """[(release date, value, month)] sorted by release date, from <data_dir>/ism_pmi.json.
    A missing file, an empty file, an empty list, or entries without a parseable
    `release` / finite `value` give no release (they are skipped)."""
    path = os.path.join(data_dir, PMI_FILE)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        raw = fh.read().strip()
    if not raw:
        return []
    data = json.loads(raw)
    out = []
    for e in data or []:
        try:
            rd = pd.Timestamp(e["release"]).date()
            v = float(e["value"])
        except (KeyError, TypeError, ValueError):
            continue
        if not np.isfinite(v):
            continue
        out.append((rd, v, str(e.get("month") or "")))
    out.sort(key=lambda x: x[0])                 # stable: same-day entries keep file order
    return out


def regime_levels(dates, releases) -> list[float]:
    """run_r61_pmi.py build_days, in effect verbatim: for each session date the value of
    the last release STRICTLY BEFORE it, NaN when there is none."""
    lvl, j = [], 0
    for k in dates:
        while j < len(releases) and releases[j][0] < k:
            j += 1
        lvl.append(releases[j - 1][1] if j > 0 else np.nan)
    return lvl


def leg_sessions(data_dir: str, pattern: str, releases, now=None, require_complete=True):
    """Session frame of one leg (leg_d7.sessions: one bar per session date, partial bar
    dropped) with `pmi` (governing release value) and `active` (pmi < 50; NaN -> False).
    Returns (frame, list of bar starts dropped as incomplete)."""
    bars = leg_d7.load_ibkr(data_dir, pattern)
    dated = leg_d7.sessions(bars, now, require_complete=False)
    d = leg_d7.sessions(bars, now, require_complete).copy()
    d["pmi"] = regime_levels(list(d["date"]), releases)
    d["active"] = d["pmi"].to_numpy(dtype=float) < THR
    # dropped bars whose session has STARTED (bar start <= now): a mid-session pull.
    # Bars starting after `now` (only possible with a backdated `now`) are just ignored.
    started = dated.index <= leg_d7._now(now)
    incomplete = list(dated.index[~dated.index.isin(d.index) & started])
    return d, incomplete


# ------------------------------------------------------------------------------- core
def month_blocks(d: pd.DataFrame, now=None) -> list[dict]:
    """One dict per calendar month holding >= 1 active session of frame `d` (needs
    `date`, `close`, `active`, in session order): ym, first/last active position, n,
    entry (close of the session before the first active one; None when the data starts
    inside the regime), entry_date, first_date, last_date, exit, contiguous, closed."""
    if d.empty:
        return []
    dates = list(d["date"])
    close = d["close"].to_numpy(dtype=float)
    act = d["active"].to_numpy(dtype=bool)
    today = leg_d7._now(now).date()
    blocks, seen = [], {}
    for i in np.flatnonzero(act):
        i = int(i)
        ym = (dates[i].year, dates[i].month)
        if ym not in seen:
            seen[ym] = dict(ym=ym, first=i, last=i, n=0)
            blocks.append(seen[ym])
        b = seen[ym]
        b["last"] = i
        b["n"] += 1
    for b in blocks:
        f, l = b["first"], b["last"]
        b["contiguous"] = (l - f + 1 == b["n"])   # one release per month -> always True
        b["entry"] = float(close[f - 1]) if f > 0 else None
        b["entry_date"] = dates[f - 1] if f > 0 else None
        b["first_date"], b["last_date"] = dates[f], dates[l]
        b["exit"] = float(close[l])
        month_end = _dt.date(b["ym"][0], b["ym"][1], calendar.monthrange(*b["ym"])[1])
        b["closed"] = bool(today > month_end or l < len(d) - 1)
    return blocks


def _row(leg: str, b: dict) -> dict:
    return dict(date=b["last_date"].isoformat(), instr=INSTR, side="L",
                entry=b["entry"], stop=b["entry"], exit=b["exit"],
                note=f"{leg}|{b['n']} sessions", src="auto")


def _sort(rs: list[dict]) -> list[dict]:
    return sorted(rs, key=lambda r: (r["date"], LEG_ORDER.get(r["note"].split("|")[0], 9)))


def compute(data_dir: str, now=None, require_complete: bool = True) -> dict:
    """Run the whole leg once: releases, per-leg session frames / month blocks, the
    closed-month rows, the in-progress-month rows, and months skipped for lack of an
    entry close (data starting inside an active regime)."""
    today = leg_d7._now(now).date()
    # releases dated after `now` cannot govern any complete session (the regime loop
    # needs release date < session date <= today); dropping them keeps status() honest
    # when `now` is backdated.  On live data this is a no-op.
    all_rel = load_releases(data_dir)
    releases = [x for x in all_rel if x[0] <= today]
    res = dict(releases=releases, future=[x for x in all_rel if x[0] > today],
               legs={}, rows=[], open_rows=[], skipped=[])
    for leg, pattern in LEGS:
        d, incomplete = leg_sessions(data_dir, pattern, releases, now, require_complete)
        blocks = month_blocks(d, now)
        res["legs"][leg] = dict(d=d, incomplete=incomplete, blocks=blocks)
        for b in blocks:
            if b["entry"] is None:
                res["skipped"].append((leg, b["ym"]))
                continue
            (res["rows"] if b["closed"] else res["open_rows"]).append(_row(leg, b))
    res["rows"], res["open_rows"] = _sort(res["rows"]), _sort(res["open_rows"])
    return res


def rows(data_dir: str, now=None, include_open: bool = False,
         require_complete: bool = True) -> list[dict]:
    """Journal rows per CONTRACT.md: one per leg per CLOSED calendar month with active
    sessions (include_open=True adds the month still in progress).  Empty when there is no
    release < 50 in effect for any complete session."""
    r = compute(data_dir, now, require_complete)
    return _sort(r["rows"] + (r["open_rows"] if include_open else []))


def status(data_dir: str, now=None) -> str:
    """One line for the monthly report: latest print (month, release date), regime state,
    sessions / calendar days in the current regime episode (SPX calendar), month-to-date
    of an in-progress month per leg, data extent and dropped partial bars."""
    r = compute(data_dir, now)
    rel = r["releases"]
    today = leg_d7._now(now).date()
    parts = []
    if not rel:
        parts.append(f"{INSTR}: no releases in {PMI_FILE}; regime undefined, flat")
    else:
        rd, v, m = rel[-1]
        active = v < THR
        k = len(rel) - 1                         # first release of the current same-state run
        while k > 0 and (rel[k - 1][1] < THR) == active:
            k -= 1
        ep_rd, ep_v, _ = rel[k]
        parts.append(f"{INSTR}: latest print {v:.1f} ({m or 'month ?'}, released {rd.isoformat()}); "
                     f"regime {'ACTIVE (< 50, long)' if active else 'INACTIVE (>= 50, flat)'} "
                     f"for sessions after {rd.isoformat()}")
        d = r["legs"][REF_LEG]["d"]
        since = d[[x > ep_rd for x in d["date"]]] if len(d) else d
        word = "active" if active else "flat"
        if since.empty:
            parts.append(f"no complete {REF_LEG} session yet after the {ep_rd.isoformat()} "
                         f"release ({ep_v:.1f}): 0 sessions in regime")
        else:
            first = since["date"].iloc[0]
            parts.append(f"{word} since {first.isoformat()} (release {ep_rd.isoformat()} = "
                         f"{ep_v:.1f}): {len(since)} sessions / {(today - first).days + 1} "
                         f"calendar days in regime")
    for row in r["open_rows"]:
        leg = row["note"].split("|")[0]
        parts.append(f"{leg} month-to-date {row['note'].split('|')[1]}: entry {row['entry']:.2f} "
                     f"-> last close {row['exit']:.2f} ({row['exit'] - row['entry']:+.2f} pts), "
                     f"journalled at month end")
    if r["skipped"]:
        parts.append("no entry close for " + ", ".join(f"{leg} {y}-{mo:02d}"
                                                       for leg, (y, mo) in r["skipped"]))
    ext, drop = [], []
    for leg, _ in LEGS:
        d, inc = r["legs"][leg]["d"], r["legs"][leg]["incomplete"]
        ext.append(f"{leg} {len(d)} bars" + (f" to {d['date'].iloc[-1].isoformat()}" if len(d) else ""))
        if inc:
            drop.append(f"{leg} {inc[-1].date().isoformat()}")
    parts.append("data: " + ", ".join(ext))
    if drop:
        parts.append("session in progress, bar not used: " + ", ".join(drop))
    if r["future"]:
        parts.append(f"{len(r['future'])} release(s) dated after {today.isoformat()} ignored")
    return "; ".join(parts)


if __name__ == "__main__":
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "forward")
    for x in rows(dd):
        print(x)
    print(status(dd))
