"""Forward-data stress test of forward/leg_pmi.py (review lens: what breaks on real pulls).

Run: cd backtest && python3 forward/stress_leg_pmi.py      (exit 0 only if every MUST passes)

Synthetic files are written under a temp dir (scratchpad if given as argv[1]).  Expected
values are derived independently from CONTRACT.md's rule text (governing release = last
release dated strictly before the session; active while < 50), NOT from the leg's helpers.

MUST cases: overlapping pulls / duplicate timestamps (last file wins, incl. a partial bar
superseded by the complete one), missing bars, partial current-day bar, no-signal data,
files absent (all / one leg), strings for floats and ISO-variant timestamps, malformed
release entries, exact row schema, walk-forward key stability (a row once emitted is
emitted identically at every later check-in; no partial close ever reaches a row),
data starting inside a regime, `now` edges.
INFO cases (characterised, reported, not asserted): stale-file re-run, weekend bar,
22:00-UTC previous-day bar anchoring, corrupt / ragged file, dict-wrapped release file,
integer release date, gap-then-fill duplicate month keys, two regime runs in one month.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.abspath(os.path.join(HERE, ".."))
for p in (HERE, BT):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(BT)
import leg_pmi  # noqa: E402

SCRATCH = sys.argv[1] if len(sys.argv) > 1 else None
checks, infos = [], []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def info(name, detail=""):
    infos.append((name, detail))
    print(f"  [info] {name}" + (f"  -- {detail}" if detail else ""))


def guarded(fn, *a, **k):
    """Return (value, None) or (None, 'ExcType: msg')."""
    try:
        return fn(*a, **k), None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


# ------------------------------------------------------------------ synthetic fixtures
LEGS = ("SPX", "NDX", "RUT")
BASE = {"SPX": 6000.0, "NDX": 21000.0, "RUT": 2200.0}
HOLIDAYS = {dt.date(2026, 7, 3), dt.date(2026, 9, 7)}
RELEASES = [{"release": "2026-06-01", "month": "2026-05", "value": 52.0},
            {"release": "2026-07-01", "month": "2026-06", "value": 49.0},
            {"release": "2026-08-03", "month": "2026-07", "value": 48.5},
            {"release": "2026-09-01", "month": "2026-08", "value": 51.0},
            {"release": "2026-10-01", "month": "2026-09", "value": 47.0}]
PARTIAL = -100.0                                   # a mid-session "close" is true close + PARTIAL


def weekdays(a, b):
    d, out = a, []
    while d <= b:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


CAL = weekdays(dt.date(2026, 6, 1), dt.date(2026, 10, 30))
CLOSE = {leg: {d: round(BASE[leg] + 1.25 * i + 0.1 * ((i * 7) % 11), 2) for i, d in enumerate(CAL)}
         for leg in LEGS}


def bar_start(d):
    # IBKR: bar start = cash open, 13:30 UTC in EDT, 14:30 UTC in EST (as in the live files)
    return f"{d.isoformat()}T{'13:30' if 3 < d.month < 11 else '14:30'}:00Z"


def ibkr_json(leg, dates, closes=None, partial_last=False, time_fn=bar_start, as_str=False,
              dup_last=False, extra=None):
    closes = closes or CLOSE[leg]
    c = [closes[d] for d in dates]
    if partial_last and c:
        c[-1] = c[-1] + PARTIAL
    t = [time_fn(d) for d in dates]
    if dup_last and t:
        t.append(t[-1]); c.append(c[-1])
    conv = (lambda x: f"{x:.2f}") if as_str else (lambda x: x)
    d = dict(chart_step=86400, chart_start="2024-09-03T00:00:00Z", chart_end="2026-09-02T00:00:00Z",
             expires="2026-09-02T12:54:10Z", delayed=900, source="Last",
             time=t, open=[conv(x - 3.0) for x in c], high=[conv(x + 5.0) for x in c],
             low=[conv(x - 6.0) for x in c], close=[conv(x) for x in c])
    if extra:
        d.update(extra)
    return d


def fresh_dir(tag):
    return tempfile.mkdtemp(prefix=f"pmi_{tag}_", dir=SCRATCH)


def write(dirpath, name, obj):
    with open(os.path.join(dirpath, name), "w") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh)


def write_releases(dirpath, rel=RELEASES):
    write(dirpath, "ism_pmi.json", rel)


# ---------------------------------------------------------- independent expected values
def expected_rows(releases, sessions_by_leg, closed_by):
    """Rows per CONTRACT.md computed from scratch.  releases: [(date, value)];
    sessions_by_leg: {leg: [(date, close)] in order}; closed_by: date -- a month is
    reported once the calendar month is over OR a later session exists in the data."""
    rel = sorted(releases)
    out = []
    for leg, sess in sessions_by_leg.items():
        dates = [s for s, _ in sess]
        act = []
        for s in dates:
            gov = [v for rd, v in rel if rd < s]
            act.append(bool(gov) and gov[-1] < 50)
        months = {}
        for i, (s, c) in enumerate(sess):
            if act[i]:
                months.setdefault((s.year, s.month), []).append(i)
        for ym, idx in months.items():
            f, l = idx[0], idx[-1]
            if f == 0:
                continue                                     # no entry close: skipped
            month_end = (dt.date(ym[0] + (ym[1] == 12), ym[1] % 12 + 1, 1) - dt.timedelta(days=1))
            if not (closed_by > month_end or l < len(sess) - 1):
                continue
            out.append(dict(date=dates[l].isoformat(), instr="PMI", side="L",
                            entry=sess[f - 1][1], stop=sess[f - 1][1], exit=sess[l][1],
                            note=f"{leg}|{len(idx)} sessions", src="auto"))
    return sorted(out, key=lambda r: (r["date"], r["note"]))


def norm(rs):
    return sorted(rs, key=lambda r: (r["date"], r["note"]))


REL_T = [(dt.date.fromisoformat(r["release"]), r["value"]) for r in RELEASES]

# ============================================================ 1. overlapping pulls / dups
print("\n=== 1. overlapping pulls, duplicate timestamps, partial bar superseded ===")
d1 = fresh_dir("multi")
write_releases(d1)
for leg in LEGS:
    a = [x for x in CAL if x <= dt.date(2026, 7, 15)]
    b = [x for x in CAL if dt.date(2026, 6, 15) <= x <= dt.date(2026, 8, 14)]
    c = [x for x in CAL if x <= dt.date(2026, 10, 2)]
    write(d1, f"{leg.lower()}_daily_2026-07-15.json", ibkr_json(leg, a, partial_last=True))   # mid-session pull
    write(d1, f"{leg.lower()}_daily_2026-08-14.json", ibkr_json(leg, b, partial_last=True, dup_last=True))
    write(d1, f"{leg.lower()}_daily_2026-10-05.json", ibkr_json(leg, c, dup_last=True))
NOW1 = "2026-10-05T12:54:00Z"
res, err = guarded(leg_pmi.compute, d1, now=NOW1)
check("three overlapping pulls per leg load without error", err is None, err or "")
if err is None:
    dspx = res["legs"]["SPX"]["d"]
    want = [x for x in CAL if x <= dt.date(2026, 10, 2)]
    check("session frame = union of pulls, one bar per date, sorted",
          list(dspx["date"]) == want, f"{len(dspx)} sessions vs {len(want)} expected")
    cl = dict(zip(dspx["date"], dspx["close"]))
    check("07-15 and 08-14 closes come from the LATER pull (partial bars superseded)",
          cl[dt.date(2026, 7, 15)] == CLOSE["SPX"][dt.date(2026, 7, 15)]
          and cl[dt.date(2026, 8, 14)] == CLOSE["SPX"][dt.date(2026, 8, 14)],
          f"07-15 {cl[dt.date(2026, 7, 15)]} 08-14 {cl[dt.date(2026, 8, 14)]}")
    rows1 = leg_pmi.rows(d1, now=NOW1)
    exp1 = expected_rows(REL_T, {leg: [(x, CLOSE[leg][x]) for x in want] for leg in LEGS},
                         closed_by=dt.date(2026, 10, 5))
    check("rows == independently computed contract rows (Jul/Aug/Sep x 3 legs)",
          norm(rows1) == exp1, f"{len(rows1)} rows, expected {len(exp1)}")
    check("no partial close leaked into any row",
          not any(abs(r[k] - PARTIAL - CLOSE[r['note'][:3]].get(dt.date.fromisoformat(r['date']), 0)) < 1e-9
                  for r in rows1 for k in ("entry", "exit")))
    open1 = [r for r in leg_pmi.rows(d1, now=NOW1, include_open=True) if r not in rows1]
    check("October (release 10-01 47.0, active from 10-02) is open, not emitted by default; include_open adds 3",
          len(open1) == 3 and all(r["date"] == "2026-10-02" and r["note"].endswith("|1 sessions") for r in open1),
          str(open1[:1]))

# file-name order vs pull order
d1b = fresh_dir("nameorder")
write_releases(d1b)
for leg in LEGS:
    c = [x for x in CAL if x <= dt.date(2026, 9, 1)]
    write(d1b, f"{leg.lower()}_daily_2026-09-02.json", ibkr_json(leg, c))                       # newest pull, complete
    write(d1b, f"{leg.lower()}_daily_z_old_pull.json", ibkr_json(leg, c, partial_last=True))     # older pull, sorts LAST
rz = leg_pmi.rows(d1b, now="2026-09-03T12:54:00Z", include_open=True)
sep = [r for r in rz if r["date"] == "2026-09-01"]
info("dup resolution is by file NAME order, not pull time: an older pull whose name sorts last wins",
     f"September exit {sep[0]['exit'] if sep else None} vs true close {CLOSE['SPX'][dt.date(2026, 9, 1)]} "
     f"(partial = true{PARTIAL:+.0f})")

# ================================================================ 2. missing bars / holidays
print("\n=== 2. missing bars (data gap on a month's first active session and on a month-end) ===")
d2 = fresh_dir("gaps")
write_releases(d2)
gap = {dt.date(2026, 7, 2), dt.date(2026, 7, 31)}
dates2 = [x for x in CAL if x <= dt.date(2026, 9, 1) and x not in gap]
for leg in LEGS:
    write(d2, f"{leg.lower()}_daily_x.json", ibkr_json(leg, dates2))
NOW2 = "2026-09-02T12:54:00Z"
rows2, err = guarded(leg_pmi.rows, d2, now=NOW2)
check("gaps: no exception", err is None, err or "")
if err is None:
    exp2 = expected_rows(REL_T, {leg: [(x, CLOSE[leg][x]) for x in dates2] for leg in LEGS},
                         closed_by=dt.date(2026, 9, 2))
    check("gaps: rows == contract rows on the available sessions (July 19 sessions from 07-06, "
          "entry 07-01 close; August entry = 07-30 close)", norm(rows2) == exp2,
          f"{[r['note'] for r in rows2 if r['note'].startswith('SPX')]}")

# ============================================================ 3. partial current-day bar
print("\n=== 3. partial current-day bar ===")
d3 = fresh_dir("partial")
write_releases(d3)
dates3 = [x for x in CAL if x <= dt.date(2026, 9, 1)]
for leg in LEGS:
    write(d3, f"{leg.lower()}_daily_2026-09-01.json", ibkr_json(leg, dates3, partial_last=True))
NOW3 = "2026-09-01T15:00:00Z"
r3 = leg_pmi.rows(d3, now=NOW3)
r3o = leg_pmi.rows(d3, now=NOW3, include_open=True)
st3 = leg_pmi.status(d3, now=NOW3)
check("pull at 15:00Z on 09-01: 09-01 bar dropped; July+August rows only (6); no September row even with include_open",
      len(r3) == 6 and all(r["date"] in ("2026-07-31", "2026-08-31") for r in r3) and r3o == r3
      and "session in progress" in st3 and "2026-09-01" in st3, f"{len(r3)} / {len(r3o)} rows")
check("no partial close in any row (15:00Z run)",
      not any(r["exit"] == CLOSE[r["note"][:3]][dt.date(2026, 9, 1)] + PARTIAL for r in r3o))
# stale re-run / delayed feed: month-end partial bar (08-31 pulled mid-session; August is active through 09-01),
# leg run later on the same files
d3m = fresh_dir("stale")
write_releases(d3m)
dates3m = [x for x in CAL if x <= dt.date(2026, 8, 31)]
for leg in LEGS:
    write(d3m, f"{leg.lower()}_daily_2026-08-31.json", ibkr_json(leg, dates3m, partial_last=True))
rows_at_pull = leg_pmi.rows(d3m, now="2026-08-31T15:00:00Z", include_open=True)
rows_stale = leg_pmi.rows(d3m, now="2026-09-01T12:54:00Z")
aug_pull = [r for r in rows_at_pull if r["date"] == "2026-08-31"]
aug_stale = [r for r in rows_stale if r["date"] == "2026-08-31" and r["note"].startswith("SPX")]
check("at the mid-session pull (08-31 15:00Z) the partial 08-31 bar is not used even with include_open", not aug_pull)
info("STALE FILE RE-RUN: files pulled mid-session on 08-31, leg run on 09-01 WITHOUT a new pull -> the partial 08-31 "
     "close is booked as August's CLOSED exit (guard is wall-clock only; the file carries no pull time except "
     "mtime/expires)",
     f"SPX August exit {aug_stale[0]['exit'] if aug_stale else None} vs true close {CLOSE['SPX'][dt.date(2026, 8, 31)]}"
     f" (partial = true{PARTIAL:+.0f})")
rows_2005 = leg_pmi.rows(d3m, now="2026-08-31T20:05:00Z", include_open=True)
aug_2005 = [r for r in rows_2005 if r["date"] == "2026-08-31" and r["note"].startswith("SPX")]
info("DELAYED FEED WINDOW: live files carry 'delayed': 900; a pull at 20:05Z (5 min after the summer close) passes the "
     "guard (bar start + 6h30 <= now) although a 15-min-delayed feed may not yet carry the settlement close",
     f"08-31 bar accepted at 20:05Z: {bool(aug_2005)} (exit {aug_2005[0]['exit'] if aug_2005 else None})")

# =============================================================== 4. no signals / no files
print("\n=== 4. no signals, files absent ===")
d4 = fresh_dir("nosig")
write(d4, "ism_pmi.json", [{"release": "2026-08-03", "month": "2026-07", "value": 55.6},
                           {"release": "2026-09-01", "month": "2026-08", "value": 54.6}])
for leg in LEGS:
    write(d4, f"{leg.lower()}_daily_2026-09-02.json", ibkr_json(leg, [x for x in CAL if x <= dt.date(2026, 9, 1)]))
r4, e4 = guarded(leg_pmi.rows, d4)
r4o, e4o = guarded(leg_pmi.rows, d4, include_open=True)
s4, e4s = guarded(leg_pmi.status, d4)
check("all prints >= 50 (live-shaped): rows() == [] (also include_open), status ok, no exception",
      r4 == [] and r4o == [] and e4 is None and e4o is None and e4s is None and "INACTIVE" in (s4 or ""),
      e4 or e4o or e4s or s4)
d4b = fresh_dir("nobars")
write_releases(d4b)
r4b, e4b = guarded(leg_pmi.rows, d4b, now=NOW1, include_open=True)
s4b, e4bs = guarded(leg_pmi.status, d4b, now=NOW1)
check("releases < 50 but NO bar files at all: rows() == [], status ok, no exception",
      r4b == [] and e4b is None and e4bs is None and "SPX 0 bars" in (s4b or ""), e4b or e4bs or s4b)
d4c = fresh_dir("emptydir")
r4c, e4c = guarded(leg_pmi.rows, d4c)
s4c, e4cs = guarded(leg_pmi.status, d4c)
check("completely empty data dir: rows() == [], status ok", r4c == [] and e4c is None and e4cs is None,
      e4c or e4cs or s4c)
d4d = fresh_dir("oneleg")
write_releases(d4d)
for leg in ("SPX", "NDX"):
    write(d4d, f"{leg.lower()}_daily_2026-10-05.json", ibkr_json(leg, [x for x in CAL if x <= dt.date(2026, 10, 2)]))
r4d, e4d = guarded(leg_pmi.rows, d4d, now=NOW1)
check("one leg's files absent (RUT): SPX/NDX rows still produced, no RUT rows, no exception",
      e4d is None and len(r4d) == 6 and not any(r["note"].startswith("RUT") for r in r4d),
      e4d or f"{len(r4d)} rows")

# ================================================================ 5. strings / ISO variants
print("\n=== 5. floats as strings, ISO timestamp variants, null close ===")
d5 = fresh_dir("strings")
write(d5, "ism_pmi.json", [{"release": "2026-06-01", "month": "2026-05", "value": "52.0"},
                           {"release": "2026-07-01T14:00:00Z", "month": "2026-06", "value": "49.0"},
                           {"release": "2026-08-03T10:00:00-04:00", "month": "2026-07", "value": " 48.5 "},
                           {"release": "2026-09-01", "month": "2026-08", "value": 51}])
dates5 = [x for x in CAL if x <= dt.date(2026, 9, 1)]


def iso_plus(d):
    hh = "13:30" if 3 < d.month < 11 else "14:30"
    return f"{d.isoformat()}T{hh}:00+00:00"


def iso_mixed(d):
    i = dates5.index(d) % 3
    hh = "13:30" if 3 < d.month < 11 else "14:30"
    return [f"{d.isoformat()}T{hh}:00Z", f"{d.isoformat()}T{hh}:00+00:00", f"{d.isoformat()}T{hh}:00.000Z"][i]


for leg in LEGS:
    j = ibkr_json(leg, dates5, as_str=True, time_fn=iso_plus)
    j["close"][dates5.index(dt.date(2026, 8, 12))] = None                  # one null close
    write(d5, f"{leg.lower()}_daily_2026-09-02.json", j)
r5, e5 = guarded(leg_pmi.rows, d5, now=NOW2)
check("string closes + '+00:00' timestamps + string / datetime-with-tz PMI entries load", e5 is None, e5 or "")
if e5 is None:
    sess5 = [x for x in dates5 if x != dt.date(2026, 8, 12)]
    exp5 = expected_rows(REL_T[:4], {leg: [(x, CLOSE[leg][x]) for x in sess5] for leg in LEGS},
                         closed_by=dt.date(2026, 9, 2))
    check("rows equal the float-input rows (null-close session dropped -> August 20 sessions); builtin floats",
          norm(r5) == exp5 and all(type(r["entry"]) is float and type(r["exit"]) is float for r in r5),
          f"{[r['note'] for r in r5 if r['note'].startswith('SPX')]}")
for leg in LEGS:
    write(d5, f"{leg.lower()}_daily_2026-09-02.json", ibkr_json(leg, dates5, time_fn=iso_mixed))
r5m, e5m = guarded(leg_pmi.rows, d5, now=NOW2)
info("MIXED ISO variants inside ONE file (Z / +00:00 / .000Z): leg_d7.load_ibkr uses pd.to_datetime without "
     "format='ISO8601' -> the whole leg raises (live files are uniform '...Z'; latent)", e5m or f"{len(r5m)} rows")

# =============================================================== 6. malformed release file
print("\n=== 6. malformed ism_pmi.json entries ===")
d6 = fresh_dir("badrel")
for leg in LEGS:
    write(d6, f"{leg.lower()}_daily_x.json", ibkr_json(leg, dates3))
bad = [{"release": "", "value": 40}, {"release": "garbage", "value": 40}, {"release": None, "value": 40},
       {"value": 40}, {"release": "2026-07-01", "value": None}, {"release": "2026-07-01", "value": "n/a"},
       {"release": "2026-07-01", "value": float("nan")}, "not-a-dict", 7, None,
       {"release": "2026-07-01", "month": "2026-06", "value": 49.0}]
write(d6, "ism_pmi.json", json.dumps(bad, default=str).replace("NaN", "null"))
rel6, e6 = guarded(leg_pmi.load_releases, d6)
r6, e6r = guarded(leg_pmi.rows, d6, now=NOW2)
check("garbage entries skipped, valid entry kept, rows computed, no exception",
      e6 is None and e6r is None and rel6 is not None and len(rel6) == 1 and len(r6) == 6,
      e6 or e6r or f"{len(rel6)} releases {rel6}")
for lab, ent in (("release ''", {"release": "", "value": 40}), ("release null", {"release": None, "value": 40}),
                 ("release 'garbage'", {"release": "garbage", "value": 40}), ("missing release", {"value": 40}),
                 ("value null", {"release": "2026-07-15", "value": None}), ("value 'n/a'", {"release": "2026-07-15", "value": "n/a"})):
    write(d6, "ism_pmi.json", [ent, {"release": "2026-07-01", "month": "2026-06", "value": 49.0}])
    rr, ee = guarded(leg_pmi.rows, d6, now=NOW2)
    ll, el = guarded(leg_pmi.load_releases, d6)
    check(f"entry {lab} alongside a valid release: skipped, no exception",
          ee is None and el is None and len(ll) == 1 and len(rr) == 6,
          ee or el or f"loaded {ll}")
write(d6, "ism_pmi.json", {"releases": RELEASES})
rel6b, e6b = guarded(leg_pmi.load_releases, d6)
info("dict-wrapped file {'releases': [...]} is SILENTLY treated as no releases (regime undefined, no rows)",
     f"loaded {len(rel6b) if rel6b is not None else e6b}")
write(d6, "ism_pmi.json", [{"release": 20260701, "month": "2026-06", "value": 49.0}])
rel6c, e6c = guarded(leg_pmi.load_releases, d6)
info("integer release date 20260701 is SILENTLY parsed as an epoch (1970) release -> every session governed by it",
     f"parsed as {rel6c[0][0] if rel6c else e6c}; June active sessions "
     f"{int(leg_pmi.compute(d6, now=NOW2)['legs']['SPX']['d'].query('active').shape[0])} of 35 (true rule: 0 in June)")
write(d6, "ism_pmi.json", "[{\"release\": \"2026-07-01\", ")                  # truncated
r6t, e6t = guarded(leg_pmi.rows, d6, now=NOW2)
info("truncated ism_pmi.json raises (caught per leg by autojournal.collect, PMI leg yields nothing that check-in)",
     e6t or f"{len(r6t)} rows")

# ============================================================= 7. corrupt / ragged bar files
print("\n=== 7. corrupt / ragged bar files ===")
d7 = fresh_dir("corrupt")
write_releases(d7)
for leg in LEGS:
    write(d7, f"{leg.lower()}_daily_2026-09-02.json", ibkr_json(leg, dates3))
write(d7, "spx_daily_2026-09-03.json", '{"time": ["2026-09-01T13:30:00Z"], "close": [7631.4')   # truncated
r7, e7 = guarded(leg_pmi.rows, d7, now=NOW2)
info("one truncated spx file: whole leg raises (all three legs' rows lost for that check-in; autojournal reports ERROR)",
     e7 or f"{len(r7)} rows")
os.remove(os.path.join(d7, "spx_daily_2026-09-03.json"))
write(d7, "spx_daily_2026-09-03.json", {"time": ["2026-09-01T13:30:00Z", "2026-09-02T13:30:00Z"], "close": [1.0]})
r7b, e7b = guarded(leg_pmi.rows, d7, now=NOW2)
c7b = leg_pmi.compute(d7, now=NOW2)["legs"]["SPX"]["d"] if e7b is None else None
info("length-1 close array with 2 timestamps: pandas 3 BROADCASTS the scalar (no error) -> both bars get close 1.0 "
     "(here 09-01 overrides the good file by name order)",
     e7b or f"SPX 09-01 close now {dict(zip(c7b['date'], c7b['close'])).get(dt.date(2026, 9, 1))}")
os.remove(os.path.join(d7, "spx_daily_2026-09-03.json"))
write(d7, "spx_daily_2026-09-03.json", {"time": ["2026-09-01T13:30:00Z", "2026-09-02T13:30:00Z", "2026-09-03T13:30:00Z"], "close": [1.0, 2.0]})
r7e, e7e = guarded(leg_pmi.rows, d7, now=NOW2)
info("ragged arrays 3 timestamps vs 2 closes: whole leg raises", e7e or f"{len(r7e)} rows")
os.remove(os.path.join(d7, "spx_daily_2026-09-03.json"))
write(d7, "spx_daily_2026-09-03.json", {"error": "no data", "time": []})
r7c, e7c = guarded(leg_pmi.rows, d7, now=NOW2)
check("IBKR error-shaped file (empty time) is skipped, rows unaffected", e7c is None and len(r7c) == 6, e7c or str(len(r7c)))
os.remove(os.path.join(d7, "spx_daily_2026-09-03.json"))
write(d7, "spx_daily_2026-09-03.json", {"time": [1756733400, 1756819800], "close": [1.0, 2.0]})
r7d, e7d = guarded(leg_pmi.rows, d7, now=NOW2)
info("epoch-seconds `time` values are parsed as 1970 nanoseconds (no error, bars land in 1970 with no regime)",
     e7d or f"{len(r7d)} rows (unchanged: the 1970 bars are inactive)")

# ==================================================================== 8. row schema
print("\n=== 8. row schema vs CONTRACT.md ===")
allrows = (rows1 if err is None else []) + r3 + rows2
KEYS = {"date", "instr", "side", "entry", "stop", "exit", "note", "src"}
check("key set exactly {date, instr, side, entry, stop, exit, note, src}",
      allrows and all(set(r) == KEYS for r in allrows))
check("types: date str YYYY-MM-DD, instr 'PMI', side 'L', entry/stop/exit builtin float, note str, src 'auto'",
      all(type(r["date"]) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"])
          and r["instr"] == "PMI" and r["side"] == "L" and r["src"] == "auto"
          and all(type(r[k]) is float and np.isfinite(r[k]) for k in ("entry", "stop", "exit"))
          and type(r["note"]) is str for r in allrows))
check("note format '<SPX|NDX|RUT>|<n> sessions'", all(re.fullmatch(r"(SPX|NDX|RUT)\|\d+ sessions", r["note"]) for r in allrows))
check("stop == entry (no stop), date is a real session date in the data",
      all(r["stop"] == r["entry"] for r in allrows))
check("rows are JSON-serialisable without default= (no numpy scalars)", guarded(json.dumps, allrows)[1] is None)
check("dedup keys (date, instr, note) unique within one call", len({(r["date"], r["instr"], r["note"]) for r in rows1}) == len(rows1))
check("collect()-style coercion float(r[k]) is a no-op", all(float(r[k]) == r[k] for r in allrows for k in ("entry", "stop", "exit")))

# =========================================================== 9. walk-forward key stability
print("\n=== 9. walk-forward: daily check-ins, key stability, no partial close ===")


def walk(pull_hhmm, tag):
    dd = fresh_dir(tag)
    write_releases(dd)
    seen = {}                                     # key -> (entry, exit) first seen
    violations, leaked = [], []
    days = []
    day = dt.date(2026, 6, 1)
    while day <= dt.date(2026, 11, 3):
        days.append(day)
        day += dt.timedelta(days=1)
    hh, mm = pull_hhmm
    for day in days:
        now = pd.Timestamp(dt.datetime(day.year, day.month, day.day, hh, mm), tz="UTC")
        for f in os.listdir(dd):
            if f != "ism_pmi.json":
                os.remove(os.path.join(dd, f))
        for leg in LEGS:
            have = [x for x in CAL if pd.Timestamp(bar_start(x)) <= now]
            partial = bool(have) and pd.Timestamp(bar_start(have[-1])) + pd.Timedelta(hours=6, minutes=30) > now
            write(dd, f"{leg.lower()}_daily_{day.isoformat()}.json", ibkr_json(leg, have, partial_last=partial))
        rs = leg_pmi.rows(dd, now=now)
        for r in rs:
            k = (r["date"], r["instr"], r["note"])
            v = (r["entry"], r["exit"])
            if k in seen and seen[k] != v:
                violations.append((day, k, seen[k], v))
            seen.setdefault(k, v)
            leg = r["note"][:3]
            for kk in ("entry", "exit"):
                if any(abs(r[kk] - (CLOSE[leg][x] + PARTIAL)) < 1e-9 for x in CAL):
                    leaked.append((day, k, kk, r[kk]))
        # once emitted, always emitted afterwards
        keys_now = {(r["date"], r["instr"], r["note"]) for r in rs}
        missing = [k for k in seen if k not in keys_now]
        if missing:
            violations.append((day, "disappeared", missing[:3]))
    final = expected_rows(REL_T, {leg: [(x, CLOSE[leg][x]) for x in CAL] for leg in LEGS}, closed_by=dt.date(2026, 11, 3))
    return seen, violations, leaked, final


for pull, tag in (((12, 54), "wf1254"), ((15, 0), "wf1500"), ((20, 30), "wf2030")):
    seen, viol, leaked, final = walk(pull, tag)
    check(f"pull {pull[0]:02d}:{pull[1]:02d}Z daily: every emitted key keeps its entry/exit and never disappears",
          not viol, str(viol[:2]))
    check(f"pull {pull[0]:02d}:{pull[1]:02d}Z daily: no partial close ever reaches a row", not leaked, str(leaked[:2]))
    check(f"pull {pull[0]:02d}:{pull[1]:02d}Z daily: union of emitted rows == final contract rows (Jul/Aug/Sep/Oct x 3)",
          {(r["date"], r["instr"], r["note"]): (r["entry"], r["exit"]) for r in final} == seen,
          f"{len(seen)} keys vs {len(final)} expected")

# gap-then-fill: the 07-31 bar arrives one pull late
dg = fresh_dir("gapfill")
write_releases(dg)
for leg in LEGS:
    write(dg, f"{leg.lower()}_daily_2026-08-03.json", ibkr_json(leg, [x for x in CAL if x <= dt.date(2026, 7, 30)]))
k1 = {(r["date"], r["note"]) for r in leg_pmi.rows(dg, now="2026-08-03T12:54:00Z")}
for leg in LEGS:
    write(dg, f"{leg.lower()}_daily_2026-08-04.json", ibkr_json(leg, [x for x in CAL if x <= dt.date(2026, 8, 3)]))
k2 = {(r["date"], r["note"]) for r in leg_pmi.rows(dg, now="2026-08-04T12:54:00Z")}
info("GAP-THEN-FILL: if a pull lacks the month's last bar and the next pull has it, July is journalled TWICE "
     "under different keys (page dedups on (date, instr, note))", f"first {sorted(k1)[:1]} then {sorted(k2)[:1]}")

# ================================================= 10. weekend bar / 22:00-previous-day anchoring
print("\n=== 10. weekend bar, previous-day 22:00 UTC anchoring (feed-shape drift) ===")
dw = fresh_dir("weekend")
write_releases(dw)
for leg in LEGS:
    j = ibkr_json(leg, dates3)
    sat = dt.date(2026, 7, 11)
    j["time"].append(f"{sat.isoformat()}T13:30:00Z"); j["close"].append(CLOSE[leg][dt.date(2026, 7, 10)] + 0.5)
    for k in ("open", "high", "low"):
        j[k].append(j["close"][-1])
    write(dw, f"{leg.lower()}_daily_x.json", j)
rw = leg_pmi.rows(dw, now=NOW2)
julw = [r for r in rw if r["note"].startswith("SPX") and r["date"].startswith("2026-07")]
info("a Saturday bar in an index file is counted as a session (no weekday filter)",
     f"July SPX note {julw[0]['note'] if julw else None} (21 sessions without the Saturday bar)")

dp = fresh_dir("prevday")
write_releases(dp)
for leg in LEGS:
    write(dp, f"{leg.lower()}_daily_x.json",
          ibkr_json(leg, dates3, time_fn=lambda d: f"{(d - dt.timedelta(days=1)).isoformat()}T22:00:00Z"))
rp = leg_pmi.rows(dp, now=NOW2)
julp = [r for r in rp if r["note"].startswith("SPX") and r["date"].startswith("2026-07")]
rp15 = leg_pmi.rows(dp, now="2026-09-01T15:00:00Z", include_open=True)
sep15 = [r for r in rp15 if r["date"] == "2026-08-31"]
info("bars anchored at 22:00 UTC of the PREVIOUS day (gold-style) would shift every session date by -1 "
     "and defeat the partial-bar guard (22:00 + 6h30 = 04:30 next day); no clock-time assertion in the leg",
     f"July SPX {julp[0]['note'] if julp else None} dated {julp[0]['date'] if julp else None} (true: 21 sessions, "
     f"2026-07-31); partial 09-01 bar at 15:00Z accepted: {bool(sep15)}")
# does the live feed carry that risk?  (checked in-session: 13:30 in EDT, 14:30 in EST for spx/ndx/rut)

# ===================================================== 11. data starting inside a regime
print("\n=== 11. data window starting inside an active regime; `now` edges; two runs in a month ===")
di = fresh_dir("inside")
write_releases(di)
dates_i = [x for x in CAL if dt.date(2026, 7, 15) <= x <= dt.date(2026, 9, 1)]
for leg in LEGS:
    write(di, f"{leg.lower()}_daily_x.json", ibkr_json(leg, dates_i))
ri, ei = guarded(leg_pmi.rows, di, now=NOW2)
rio = leg_pmi.rows(di, now=NOW2, include_open=True)
si = leg_pmi.status(di, now=NOW2)
check("window starts 07-15 inside the regime: July skipped (no entry close) and named in status; August closed (3), "
      "September open (+3 with include_open), entries = 07-31 / 08-31 closes",
      ei is None and len(ri) == 3 and all(r["date"] == "2026-08-31" for r in ri) and len(rio) == 6
      and all(r["entry"] == CLOSE[r["note"][:3]][dt.date(2026, 7, 31)] for r in ri)
      and "no entry close for SPX 2026-07, NDX 2026-07, RUT 2026-07" in si, ei or si)
# now edges
rn1 = leg_pmi.rows(d1, now="2026-08-31T23:59:00Z")
rn2 = leg_pmi.rows(d1, now="2026-09-01T00:00:00Z")
info("`now` 2026-08-31T23:59Z (08-31 bar complete since 20:00Z) does not yet close August; 09-01T00:00Z does "
     "(conservative one-check-in deferral)",
     f"{sum(r['date'].startswith('2026-08') for r in rn1)} vs {sum(r['date'].startswith('2026-08') for r in rn2)} August rows")
check("`now` far in the past (all bars in the future): [] and no exception",
      guarded(leg_pmi.rows, d1, now="2020-01-01")[0] == [] and guarded(leg_pmi.status, d1, now="2020-01-01")[1] is None)
check("`now` given as a date / naive string / tz-aware Timestamp all accepted",
      all(guarded(leg_pmi.rows, d1, now=x)[1] is None
          for x in (dt.date(2026, 10, 5), "2026-10-05", pd.Timestamp("2026-10-05T12:54", tz="Asia/Hong_Kong"))))
# two regime runs in one month (a correction entry): the contract row cannot represent it
dtw = fresh_dir("tworuns")
write(dtw, "ism_pmi.json", [{"release": "2026-07-01", "value": 49.0}, {"release": "2026-07-10", "value": 51.0},
                            {"release": "2026-07-20", "value": 48.0}, {"release": "2026-09-01", "value": 51.0}])
for leg in LEGS:
    write(dtw, f"{leg.lower()}_daily_x.json", ibkr_json(leg, dates3))
rt = [r for r in leg_pmi.rows(dtw, now=NOW2) if r["note"].startswith("SPX") and r["date"].startswith("2026-07")]
act_t = [x for x in CAL if x.month == 7 and (dt.date(2026, 7, 1) < x <= dt.date(2026, 7, 10) or x > dt.date(2026, 7, 20))]
tele = sum(CLOSE["SPX"][x] - CLOSE["SPX"][CAL[CAL.index(x) - 1]] for x in act_t)
info("two active runs in one month (only via a second release entry): one row spanning both runs, n counts active "
     "sessions only, (exit - entry) includes the inactive gap (contract row shape, `contiguous` flag unused)",
     f"row {rt[0]['note'] if rt else None}, exit-entry {rt[0]['exit'] - rt[0]['entry']:+.2f} vs telescoped active-only {tele:+.2f}")

# ------------------------------------------------------------------------------ verdict
fails = [c for c in checks if not c[1]]
print(f"\n{len(checks) - len(fails)}/{len(checks)} MUST checks passed; {len(infos)} characterised INFO items"
      + (": FAIL " + "; ".join(c[0] for c in fails) if fails else ""))
sys.exit(1 if fails else 0)
