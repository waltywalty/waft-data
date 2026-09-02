"""Forward-data robustness stress test for forward/leg_d7.py (synthetic files, temp dir).

Run: cd backtest && python3 forward/stress_leg_d7.py        (exit 0 only if every MUST passes)

Reference for "right" = run_r28b_d7.py's own state machine (the text from `c = d.close`
to `return pd.DataFrame(tr), d`) exec'd unmodified on a daily frame, so every scenario
is judged against the frozen code, not against leg_d7 itself.

Scenarios (each writes IBKR-schema spx_daily_*.json files into its own temp dir):
  1  clean single pull                       -> rows == reference; exact CONTRACT schema
  2  three overlapping pulls (weekly + yearly)-> identical rows; dedup key unique
  3  duplicate timestamps inside a file, and a stale partial close in an EARLIER pull
     superseded by the finished bar in a LATER pull -> later pull wins
  4  holidays / a random missing session      -> rule is bar-indexed, matches reference
  5  partial current-day bar (summer 13:30Z and winter 14:30Z) -> withheld until 16:00 ET
  6  week with no signals / series with no trades at all -> [] or unchanged, no crash
  7  weekend bars injected (gold-style feed)  -> counted as sessions (documented)
  8  timestamps at 22:00Z / 21:15Z of the PREVIOUS calendar day (gold/AUD daily style)
                                              -> session date off by one (documented)
  9  files absent / dir absent / other legs' files only -> [] and 'insufficient history'
 10  floats as strings, ints, whitespace, null close, "+00:00" and "-04:00" offsets
 11  warm-up boundary 200 / 201 bars
 12  check-in idempotence: rows() on a truncated dir is a prefix of rows() on the full dir
 13  stale mid-session pull never superseded (no later file) -> trusted by wall clock
 14  corrupt / short-array / list-payload files -> exception (autojournal isolates the leg)
 15  live data/forward: reference loop on the real pull == leg rows
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile
import zoneinfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, BT)
os.chdir(BT)
import leg_d7  # noqa: E402
# leg_d7 journals only trades ENTERED on/after leg_d7.STREAM_START (2026-08-27, the paper
# stream's registration).  The synthetic histories here are 2024-09..2026-09, so the
# MECHANICS are compared with the frozen loop over the whole history with the filter off;
# the filter itself is verified by test_leg_d7.py section 7.
leg_d7.STREAM_START = None

RUN = os.path.join(BT, "run_r28b_d7.py")
FORWARD = os.path.join(BT, "data", "forward")
TMP = os.environ.get("TMPDIR") or None
NY = zoneinfo.ZoneInfo("America/New_York")
NYSE_HOL = {"2024-09-02", "2024-11-28", "2024-12-25", "2025-01-01", "2025-01-09", "2025-01-20",
            "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
            "2025-11-27", "2025-12-25", "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
            "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07"}
ROW_KEYS = {"date", "instr", "side", "entry", "stop", "exit", "note", "src"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NOTE_RE = re.compile(r"^d7\|\d+ bars$")

results = []


def rec(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def info(name, detail):
    print(f"  [INFO] {name}  -- {detail}")


# ------------------------------------------------------------------ frozen reference
def ref_loop_factory():
    """run_r28b_d7.py's state machine, text-extracted and exec'd unmodified."""
    src = open(RUN).read()
    i = src.index("    c = d.close")
    j = src.index("    return pd.DataFrame(tr), d") + len("    return pd.DataFrame(tr), d")
    body = src[i:j]
    ns = dict(pd=pd, np=np)
    exec("def ref_loop(d, cost=0.0):\n" + body, ns)
    return ns["ref_loop"]


ref_loop = ref_loop_factory()


def ref_rows(d):
    tr, _ = ref_loop(d)
    return [dict(date=t.t_out.date().isoformat(), instr="D7", side="L", entry=float(t.entry),
                 stop=float(t.entry), exit=float(t.exit), note=f"d7|{int(t.bars)} bars", src="auto")
            for t in tr.itertuples()]


# ------------------------------------------------------------------ synthetic sessions
def session_dates(start, end):
    out, t = [], dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    while t <= e:
        if t.weekday() < 5 and t.isoformat() not in NYSE_HOL:
            out.append(t)
        t += dt.timedelta(days=1)
    return out


def bar_start(date, hm=(9, 30)):
    """09:30 America/New_York on `date` as a UTC Timestamp (13:30Z summer, 14:30Z winter)."""
    loc = dt.datetime(date.year, date.month, date.day, *hm, tzinfo=NY)
    return pd.Timestamp(loc.astimezone(dt.timezone.utc))


def make_daily(dates, seed=6, level=5500.0):
    r = np.random.default_rng(seed)
    n = len(dates)
    lr = r.normal(0.0008, 0.009, n)
    # mild mean reversion so the series dips below its 7-day low regularly and recovers
    # (seed 6 with these parameters gives 20 D7 trades over the 501 sessions)
    for k in range(1, n):
        lr[k] -= 0.2 * lr[k - 1]
    close = level * np.exp(np.cumsum(lr))
    open_ = np.r_[level, close[:-1]] * (1 + r.normal(0, 0.002, n))
    hi = np.maximum(open_, close) * (1 + np.abs(r.normal(0, 0.004, n)))
    lo = np.minimum(open_, close) * (1 - np.abs(r.normal(0, 0.004, n)))
    idx = pd.DatetimeIndex([bar_start(d) for d in dates])
    return pd.DataFrame(dict(open=np.round(open_, 2), high=np.round(hi, 2),
                             low=np.round(lo, 2), close=np.round(close, 2)), index=idx)


def ibkr_obj(d, times=None, conv=float, extra=None):
    """IBKR price-history JSON: parallel arrays + metadata, exactly as the MCP tool returns."""
    times = times or [ts.strftime("%Y-%m-%dT%H:%M:%SZ") for ts in d.index]
    obj = dict(chart_step=86400, chart_start=f"{d.index[0]:%Y-%m-%d}T00:00:00Z",
               chart_end=f"{d.index[-1] + pd.Timedelta(days=1):%Y-%m-%d}T00:00:00Z",
               expires="2026-09-02T12:54:10Z", delayed=900, source="Last",
               time=times, open=[conv(x) for x in d.open], close=[conv(x) for x in d.close],
               high=[conv(x) for x in d.high], low=[conv(x) for x in d.low])
    if extra:
        obj.update(extra)
    return obj


def write(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh)
    return path


def mkdir(root, name):
    p = os.path.join(root, name)
    os.makedirs(p, exist_ok=True)
    return p


def same_rows(a, b):
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def schema_ok(rows):
    problems = []
    for r in rows:
        if set(r) != ROW_KEYS:
            problems.append(f"keys {sorted(r)}")
        if not (isinstance(r["date"], str) and DATE_RE.match(r["date"])):
            problems.append(f"date {r['date']!r}")
        try:
            dt.date.fromisoformat(r["date"])
        except Exception:
            problems.append(f"date unparsable {r['date']!r}")
        if r["instr"] != "D7" or r["side"] != "L" or r["src"] != "auto":
            problems.append(f"instr/side/src {r['instr']}/{r['side']}/{r['src']}")
        for k in ("entry", "stop", "exit"):
            if type(r[k]) is not float:
                problems.append(f"{k} type {type(r[k]).__name__}")
        if r["stop"] != r["entry"]:
            problems.append("stop != entry")
        if not (isinstance(r["note"], str) and NOTE_RE.match(r["note"])):
            problems.append(f"note {r['note']!r}")
    try:
        json.dumps(rows)
    except Exception as e:
        problems.append(f"not JSON-serializable: {e}")
    return problems


# ------------------------------------------------------------------------------ main
def main():
    print("leg_d7 forward-data stress test (reference = run_r28b_d7.py loop exec'd verbatim)\n")
    dates = session_dates("2024-09-03", "2026-09-01")
    d = make_daily(dates)
    ref = ref_rows(d)
    NOW_AFTER = pd.Timestamp("2026-09-02T11:54:00Z")       # the real check-in pull time
    print(f"synthetic SPX sessions: {len(d)} bars {d.index[0]:%Y-%m-%d} .. {d.index[-1]:%Y-%m-%d}; "
          f"reference trades: {len(ref)}")
    rec("synthetic series produces enough trades to be a meaningful test", len(ref) >= 8, f"{len(ref)}")

    with tempfile.TemporaryDirectory(dir=TMP) as root:
        # ---- 1. clean single pull + schema
        print("\n1. clean single pull")
        p1 = mkdir(root, "s1")
        write(ibkr_obj(d), os.path.join(p1, "spx_daily_2026-09-02.json"))
        r1 = leg_d7.rows(p1, now=NOW_AFTER)
        rec("rows == frozen reference (dates, entries, exits, bar counts)", same_rows(r1, ref),
            f"{len(r1)} vs {len(ref)}")
        pr = schema_ok(r1)
        rec("CONTRACT row schema exact (keys, str date YYYY-MM-DD, float entry/stop/exit, "
            "note 'd7|<n> bars', side L, src auto, stop==entry, JSON-serializable)", not pr, "; ".join(pr[:5]))
        rec("dedup key (date, instr, note) unique",
            len({(r["date"], r["instr"], r["note"]) for r in r1}) == len(r1))
        rec("status() runs and names the regime", "D7:" in leg_d7.status(p1, now=NOW_AFTER))
        rec("rows() with default now (wall clock) == rows(now=pull time) on finished data",
            same_rows(leg_d7.rows(p1), r1))

        # ---- 2. overlapping pulls
        print("\n2. three overlapping pulls: yearly + two weekly, different file names")
        p2 = mkdir(root, "s2")
        write(ibkr_obj(d.iloc[:420]), os.path.join(p2, "spx_daily_2026-05-01.json"))
        write(ibkr_obj(d.iloc[400:470]), os.path.join(p2, "spx_daily_2026-07-15.json"))
        write(ibkr_obj(d.iloc[450:]), os.path.join(p2, "spx_daily_2026-09-02.json"))
        r2 = leg_d7.rows(p2, now=NOW_AFTER)
        rec("overlapping pulls -> identical rows", same_rows(r2, ref), f"{len(r2)} vs {len(ref)}")
        rec("overlapping pulls -> exactly one bar per session", len(leg_d7.compute(p2, now=NOW_AFTER)["d"]) == len(d))

        # ---- 3. duplicates inside a file; stale partial close in earlier pull
        print("\n3. duplicate timestamps; earlier pull holds a stale mid-session close")
        p3 = mkdir(root, "s3")
        dup = pd.concat([d.iloc[:300], d.iloc[250:320], d.iloc[:]])       # in-file duplicates, unsorted
        write(ibkr_obj(dup), os.path.join(p3, "spx_daily_2026-09-02.json"))
        r3 = leg_d7.rows(p3, now=NOW_AFTER)
        rec("in-file duplicate + unsorted timestamps -> identical rows", same_rows(r3, ref))
        p3b = mkdir(root, "s3b")
        k = 480                                        # a session that sits inside a trade
        stale = d.iloc[:k + 1].copy()
        stale.iloc[-1, stale.columns.get_loc("close")] = float(d.close.iloc[k]) * 0.97   # partial print
        write(ibkr_obj(stale), os.path.join(p3b, "spx_daily_2026-07-30.json"))          # earlier pull
        write(ibkr_obj(d), os.path.join(p3b, "spx_daily_2026-09-02.json"))              # later pull
        r3b = leg_d7.rows(p3b, now=NOW_AFTER)
        rec("stale close in the EARLIER pull is superseded by the LATER pull (keep-last by file name)",
            same_rows(r3b, ref))
        # and the reverse: if the later-named file carried the stale value it would win
        p3c = mkdir(root, "s3c")
        write(ibkr_obj(d), os.path.join(p3c, "spx_daily_2026-07-30.json"))
        write(ibkr_obj(stale), os.path.join(p3c, "spx_daily_2026-09-02.json"))
        c3c = leg_d7.compute(p3c, now=NOW_AFTER)["d"]
        info("precedence is by FILE NAME order, not by pull recency in the data",
             f"later-named file with the stale value wins: close[{d.index[k]:%Y-%m-%d}] = "
             f"{float(c3c.close.iloc[k]):.2f} vs true {float(d.close.iloc[k]):.2f}")

        # ---- 4. holidays / missing session
        print("\n4. holidays and a missing session (rule is bar-indexed)")
        gap = d.drop(d.index[[310, 311, 412]])
        p4 = mkdir(root, "s4")
        write(ibkr_obj(gap), os.path.join(p4, "spx_daily_2026-09-02.json"))
        r4 = leg_d7.rows(p4, now=NOW_AFTER)
        rec("gapped series -> rows == reference on the same gapped frame", same_rows(r4, ref_rows(gap)))
        rec("holiday-free synthetic calendar has no NYSE holiday bars (fixture sanity)",
            not any(x.isoformat() in NYSE_HOL for x in dates))

        # ---- 5. partial current-day bar, summer and winter
        print("\n5. partial current-day bar")
        for label, day, mid, end in (
                ("summer 13:30Z bar", dt.date(2026, 9, 2), "2026-09-02T15:00:00Z", "2026-09-02T20:00:00Z"),
                ("winter 14:30Z bar", dt.date(2026, 1, 15), "2026-01-15T20:30:00Z", "2026-01-15T21:00:00Z")):
            base = d[d.index < bar_start(day)]
            part = base.iloc[-1:].copy()
            part.index = pd.DatetimeIndex([bar_start(day)])
            part.iloc[0, part.columns.get_loc("close")] = float(base.close.iloc[-1]) * 1.03
            full = pd.concat([base, part])
            p5 = mkdir(root, f"s5_{day}")
            write(ibkr_obj(full), os.path.join(p5, "spx_daily_x.json"))
            r_mid = leg_d7.rows(p5, now=mid)
            r_end = leg_d7.rows(p5, now=end)
            st_mid = leg_d7.status(p5, now=mid)
            rec(f"{label}: mid-session pull ignores the partial bar (rows == reference on the bars before it)",
                same_rows(r_mid, ref_rows(base)))
            rec(f"{label}: status names the withheld bar",
                f"last bar {day.isoformat()} not used: session in progress" in st_mid, st_mid[-80:])
            rec(f"{label}: at 16:00 ET the bar is used (rows == reference including it)",
                same_rows(r_end, ref_rows(full)))
            one_sec_early = pd.Timestamp(end) - pd.Timedelta(seconds=1)
            rec(f"{label}: one second before 16:00 ET still withheld",
                same_rows(leg_d7.rows(p5, now=one_sec_early), ref_rows(base)))
        # the guard on an OPEN position: a mid-session close above high7 must not close the trade
        rec("an open position is not closed by a partial bar (status uses complete bars only)",
            "session in progress" in leg_d7.status(p5, now=mid))

        # ---- 6. no signals
        print("\n6. weeks with no signals")
        flat_end = None
        for cut in range(len(d) - 1, 200, -1):
            if same_rows(leg_d7.rows(p1, now=NOW_AFTER), ref) and len(ref_rows(d.iloc[:cut])) == len(ref):
                flat_end = cut
            else:
                break
        rec("trailing sessions with no closed trade -> rows unchanged, no crash",
            flat_end is not None and flat_end < len(d), f"last {len(d) - flat_end} sessions add no row")
        rising = d.copy()
        rising["close"] = np.linspace(5000, 6000, len(d))
        rising["high"] = rising.close * 1.001
        rising["low"] = rising.close * 0.999
        p6 = mkdir(root, "s6")
        write(ibkr_obj(rising), os.path.join(p6, "spx_daily_a.json"))
        r6 = leg_d7.rows(p6, now=NOW_AFTER)
        st6 = leg_d7.status(p6, now=NOW_AFTER)
        rec("series with no trades at all -> [] (not None, no crash) and status 'flat'",
            r6 == [] and "flat" in st6, st6[:60])
        p6b = mkdir(root, "s6b")
        write(ibkr_obj(d.iloc[-5:]), os.path.join(p6b, "spx_daily_week.json"))
        rec("a lone one-week pull (5 bars) -> [] and 'insufficient history'",
            leg_d7.rows(p6b, now=NOW_AFTER) == [] and "insufficient history" in leg_d7.status(p6b, now=NOW_AFTER))

        # ---- 7. weekend bars
        print("\n7. weekend bars injected (what a gold-style feed carries)")
        wk = d.copy()
        extra_rows = []
        for ts in d.index[10:-10:20]:                    # never past `now` (the guard would drop it)
            sat = ts + pd.Timedelta(days=(5 - ts.dayofweek) % 7 or 7)
            row = d.loc[ts].copy()
            row["close"] = row["close"] * 0.999
            extra_rows.append((sat, row))
        wk = pd.concat([wk, pd.DataFrame({t: r for t, r in extra_rows}).T]).sort_index()
        wk.index = pd.DatetimeIndex(wk.index)
        p7 = mkdir(root, "s7")
        write(ibkr_obj(wk), os.path.join(p7, "spx_daily_a.json"))
        r7 = leg_d7.rows(p7, now=NOW_AFTER)
        n_wk = int((leg_d7.compute(p7, now=NOW_AFTER)["d"].index.dayofweek >= 5).sum())
        rec("weekend bars are NOT filtered: they are counted as sessions (faithful to the archive's "
            "Sunday buckets; an SPX RTH pull never carries them)",
            n_wk == len(extra_rows) and same_rows(r7, ref_rows(wk)), f"{n_wk} weekend bars kept")
        info("weekend bars change the rows vs the weekday-only reference",
             f"{len(r7)} rows with weekend bars vs {len(ref)} without")

        # ---- 8. previous-day 22:00Z / 21:15Z timestamps
        print("\n8. daily bars stamped 22:00Z / 21:15Z of the PREVIOUS calendar day (gold/AUD style)")
        for hm in ("22:00:00", "21:15:00"):
            times = [f"{(ts - pd.Timedelta(days=1)):%Y-%m-%d}T{hm}Z" for ts in d.index]
            p8 = mkdir(root, f"s8_{hm[:2]}")
            write(ibkr_obj(d, times=times), os.path.join(p8, "spx_daily_a.json"))
            r8 = leg_d7.rows(p8, now=NOW_AFTER)
            shifted = [dict(r, date=(dt.date.fromisoformat(r["date"]) - dt.timedelta(days=1)).isoformat())
                       for r in ref]
            rec(f"{hm}Z-previous-day stamps -> trades identical but every row date is the day BEFORE "
                f"the session (documented; contract pins 13:30Z bar start)", same_rows(r8, shifted))
            # completeness guard would trust such a bar at 04:30Z / 03:45Z, hours before the open
            last_stamp = pd.Timestamp(times[-1])
            trusted_at = last_stamp + leg_d7.RTH_LEN
            info(f"{hm}Z stamp: guard trusts the last bar from", f"{trusted_at:%Y-%m-%d %H:%M}Z "
                 f"(real session {d.index[-1]:%Y-%m-%d %H:%M}Z-{d.index[-1] + leg_d7.RTH_LEN:%H:%M}Z)")
        tods = {ts.strftime("%H:%M") for ts in d.index}
        rec("fixture sanity: synthetic bar starts are 13:30Z/14:30Z only", tods == {"13:30", "14:30"}, str(tods))

        # ---- 9. absent files
        print("\n9. absent files")
        p9 = mkdir(root, "s9_empty")
        rec("empty dir -> [] and 'insufficient history'",
            leg_d7.rows(p9) == [] and "insufficient history" in leg_d7.status(p9))
        p9n = os.path.join(root, "does_not_exist")
        try:
            ok = leg_d7.rows(p9n) == [] and "insufficient history" in leg_d7.status(p9n)
            rec("non-existent dir -> [] and 'insufficient history' (no exception)", ok)
        except Exception as e:  # noqa: BLE001
            rec("non-existent dir -> [] and 'insufficient history' (no exception)", False, f"{type(e).__name__}: {e}")
        p9o = mkdir(root, "s9_other")
        write(ibkr_obj(d), os.path.join(p9o, "ndx_daily_2026-09-02.json"))
        write(ibkr_obj(d), os.path.join(p9o, "xauusd_daily_2026-09-02.json"))
        with open(os.path.join(p9o, "hk33_m15.csv"), "w") as fh:
            fh.write("time,open,high,low,close\n")
        rec("only other legs' files present -> [] (glob is spx_daily_*.json only)",
            leg_d7.rows(p9o) == [] and "insufficient history" in leg_d7.status(p9o))
        p9e = mkdir(root, "s9_emptyarrays")
        write(dict(time=[], open=[], high=[], low=[], close=[], chart_step=86400), os.path.join(p9e, "spx_daily_a.json"))
        rec("file with empty arrays -> [] (skipped)", leg_d7.rows(p9e) == [])

        # ---- 10. numeric / time formats
        print("\n10. floats as strings, ints, whitespace, nulls, offsets")
        p10 = mkdir(root, "s10_str")
        write(ibkr_obj(d, conv=lambda x: f"{x:.2f}"), os.path.join(p10, "spx_daily_a.json"))
        r10 = leg_d7.rows(p10, now=NOW_AFTER)
        rec("all prices as strings -> identical rows, entry/exit still Python floats",
            same_rows(r10, ref) and not schema_ok(r10))
        p10b = mkdir(root, "s10_mixed")
        obj = ibkr_obj(d)
        obj["close"] = [(" %s " % v if i % 3 == 0 else (int(v) if float(v).is_integer() else v))
                        for i, v in enumerate(obj["close"])]
        obj["open"] = [str(v) for v in obj["open"]]
        write(obj, os.path.join(p10b, "spx_daily_a.json"))
        rec("mixed str/int/float with whitespace -> identical rows", same_rows(leg_d7.rows(p10b, now=NOW_AFTER), ref))
        p10c = mkdir(root, "s10_null")
        obj = ibkr_obj(d)
        obj["close"][330] = None                         # a null close (IBKR holiday placeholder)
        obj["low"][331] = None                           # a null low: MAE only, close kept
        write(obj, os.path.join(p10c, "spx_daily_a.json"))
        c10c = leg_d7.compute(p10c, now=NOW_AFTER)
        rec("null close -> that bar dropped (rule then runs on the remaining bars == reference on them); "
            "null low keeps the bar",
            len(c10c["d"]) == len(d) - 1 and same_rows(c10c["rows"], ref_rows(d.drop(d.index[[330]]))))
        info("a null close silently removes a session (shifts the 7-bar window)",
             f"bar {d.index[330]:%Y-%m-%d} gone; rows {len(c10c['rows'])} vs clean {len(ref)}")
        p10d = mkdir(root, "s10_offsets")
        times = [ts.strftime("%Y-%m-%dT%H:%M:%S+00:00") for ts in d.index]
        write(ibkr_obj(d.iloc[:300], times=times[:300]), os.path.join(p10d, "spx_daily_a.json"))
        times_ny = [ts.tz_convert(NY).strftime("%Y-%m-%dT%H:%M:%S%z") for ts in d.index]
        times_ny = [t[:-2] + ":" + t[-2:] for t in times_ny]                     # -04:00 form
        write(ibkr_obj(d.iloc[280:], times=times_ny[280:]), os.path.join(p10d, "spx_daily_b.json"))
        rec("'+00:00' in one file and '-04:00/-05:00' local offsets in another -> identical rows",
            same_rows(leg_d7.rows(p10d, now=NOW_AFTER), ref))
        p10e = mkdir(root, "s10_naiveZ")
        times_mixed = [t if i % 2 else t[:-1] for i, t in enumerate(ibkr_obj(d)["time"])]
        write(ibkr_obj(d, times=times_mixed), os.path.join(p10e, "spx_daily_a.json"))
        try:
            leg_d7.rows(p10e, now=NOW_AFTER)
            rec("naive and 'Z' strings mixed in ONE file -> parsed", True)
        except Exception as e:  # noqa: BLE001
            info("naive and 'Z' strings mixed in ONE file raise (pandas 3 strict format inference)",
                 f"{type(e).__name__}: {str(e)[:90]}")
        p10f = mkdir(root, "s10_epoch")
        write(ibkr_obj(d, times=[int(ts.timestamp()) for ts in d.index]), os.path.join(p10f, "spx_daily_a.json"))
        c10f = leg_d7.compute(p10f, now=NOW_AFTER)
        info("epoch-second ints in `time` are silently parsed as nanoseconds (1970) and then all dropped by the "
             "completeness guard? ->", f"{len(c10f['d'])} bars kept, first {c10f['bars'].index[0] if len(c10f['bars']) else None}")

        # ---- 11. warm-up boundary
        print("\n11. warm-up boundary")
        for n, expect_eval in ((200, False), (201, True)):
            pw = mkdir(root, f"s11_{n}")
            write(ibkr_obj(d.iloc[:n]), os.path.join(pw, "spx_daily_a.json"))
            st = leg_d7.status(pw, now=NOW_AFTER)
            rec(f"{n} bars -> {'evaluated' if expect_eval else 'insufficient history'}",
                ("insufficient history" not in st) == expect_eval, st[:70])
        rec("frozen loop starts at index 200 (201st bar), same as run_r28b_d7.py",
            leg_d7.FIRST_BAR == 200 and leg_d7.MIN_BARS == 201)

        # ---- 12. idempotence across check-ins
        print("\n12. check-in idempotence")
        ok = True
        for cut in (260, 320, 380, 440, 480, len(d) - 1):
            pc = mkdir(root, f"s12_{cut}")
            write(ibkr_obj(d.iloc[:cut]), os.path.join(pc, "spx_daily_a.json"))
            rc = leg_d7.rows(pc, now=NOW_AFTER)
            ok &= rc == ref[:len(rc)]
        rec("rows() on every truncation is a prefix of rows() on the full data (no retroactive changes)", ok)
        # a later pull that starts LATER than the first (window rolled forward) must not alter history
        pc2 = mkdir(root, "s12_roll")
        write(ibkr_obj(d.iloc[:450]), os.path.join(pc2, "spx_daily_2026-05-01.json"))
        write(ibkr_obj(d.iloc[100:]), os.path.join(pc2, "spx_daily_2026-09-02.json"))
        rec("rolled-forward 1-year window on top of the older file -> identical rows",
            same_rows(leg_d7.rows(pc2, now=NOW_AFTER), ref))
        pc3 = mkdir(root, "s12_late_only")
        write(ibkr_obj(d.iloc[100:]), os.path.join(pc3, "spx_daily_2026-09-02.json"))
        r_late = leg_d7.rows(pc3, now=NOW_AFTER)
        info("if the OLDER file were deleted, warm-up moves and the early rows change",
             f"{len(r_late)} rows from the late-only window vs {len(ref)}; suffix identical: "
             f"{r_late[-5:] == ref[-5:]}")

        # ---- 13. stale mid-session pull never superseded
        print("\n13. stale mid-session pull, never superseded")
        p13 = mkdir(root, "s13")
        day = dt.date(2026, 8, 20)
        base = d[d.index < bar_start(day)]
        part = base.iloc[-1:].copy()
        part.index = pd.DatetimeIndex([bar_start(day)])
        part.iloc[0, part.columns.get_loc("close")] = float(base.close.iloc[-1]) * 1.03   # mid-session print
        write(ibkr_obj(pd.concat([base, part]), extra=dict(expires="2026-08-20T16:00:00Z")),
              os.path.join(p13, "spx_daily_2026-08-20.json"))
        os.utime(os.path.join(p13, "spx_daily_2026-08-20.json"),
                 (pd.Timestamp("2026-08-20T15:00:00Z").timestamp(),) * 2)
        used_now = leg_d7.compute(p13, now="2026-08-27T11:54:00Z")["d"]
        rec("guard is wall-clock only: a bar pulled mid-session (file expires/mtime 15:00Z that day) is "
            "TRUSTED a week later with its partial close", float(used_now.close.iloc[-1]) == float(part.close.iloc[0]))
        info("fix", "judge completeness against the file's own as-of time (mtime, or `expires` - 1h) "
                    "rather than the wall clock; a later pull normally supersedes, a failed pull does not")

        # ---- 14. corrupt files
        print("\n14. corrupt / short / list payloads (autojournal isolates a raising leg)")
        for label, content in (("truncated JSON", '{"time": ["2026-09-01T13:30:00Z"], "close": [7'),
                               ("arrays of different length", json.dumps(dict(time=["2026-09-01T13:30:00Z", "2026-09-02T13:30:00Z"],
                                                                              open=[1.0], high=[1.0], low=[1.0], close=[1.0]))),
                               ("list payload", json.dumps([1, 2, 3])),
                               ("error payload {\"error\": ...}", json.dumps(dict(error="rate limited")))):
            pc = mkdir(root, "s14_" + re.sub(r"\W+", "_", label))
            write(ibkr_obj(d), os.path.join(pc, "spx_daily_2026-08-01.json"))
            with open(os.path.join(pc, "spx_daily_2026-09-02.json"), "w") as fh:
                fh.write(content)
            try:
                rr = leg_d7.rows(pc, now=NOW_AFTER)
                info(f"{label} alongside a good file", f"no exception; rows {len(rr)} (good file still used: {same_rows(rr, ref)})")
            except Exception as e:  # noqa: BLE001
                info(f"{label} alongside a good file", f"raises {type(e).__name__} -> the WHOLE leg contributes nothing "
                                                      f"that check-in (good file ignored too)")

        # ---- 15. live data/forward
        print("\n15. live data/forward")
        if os.path.isdir(FORWARD) and any(f.startswith("spx_daily_") for f in os.listdir(FORWARD)):
            bars = leg_d7.load_ibkr(FORWARD)
            live = leg_d7.rows(FORWARD, require_complete=False)
            rr = ref_rows(bars)
            rec("live pull: reference loop on the real IBKR frame == leg rows (guard off)", same_rows(live, rr),
                f"{len(live)} vs {len(rr)}")
            rec("live pull: guard is a no-op now (pull time is after the last session end)",
                same_rows(leg_d7.rows(FORWARD), live))
            tods = {ts.strftime("%H:%M") for ts in bars.index}
            rec("live pull: bar starts are 13:30Z (EDT) / 14:30Z (EST) only", tods <= {"13:30", "14:30"}, str(tods))
            rec("live pull: no weekend bars", int((bars.index.dayofweek >= 5).sum()) == 0)
            rec("live pull: no NYSE holiday bars", not any(ts.date().isoformat() in NYSE_HOL for ts in bars.index))
            rec("live pull: no o=h=l=c phantom bars",
                not bool(((bars.open == bars.high) & (bars.high == bars.low) & (bars.low == bars.close)).any()))
            rec("live pull: schema exact", not schema_ok(live))
        else:
            info("live data/forward", "no spx_daily_*.json present, skipped")

    nfail = sum(1 for _, ok, _ in results if not ok)
    print(f"\nSUMMARY: {len(results) - nfail}/{len(results)} checks passed")
    for name, ok, detail in results:
        if not ok:
            print(f"  FAILED: {name} -- {detail}")
    return nfail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
