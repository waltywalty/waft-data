"""Verification of forward/leg_pmi.py (CONTRACT.md, PMI leg).

Run: cd backtest && python3 forward/test_leg_pmi.py        (exit 0 only if every MUST passes)

What is checked:

  1. Synthetic regime.  ism_pmi.json with releases 2026-06-01 52.0, 2026-07-01 49.0,
     2026-08-03 48.5, 2026-09-01 51.0 and weekday daily bars June-September 2026 (US
     holidays 2026-07-03 and 2026-09-07 omitted, two overlapping pulls per leg) whose closes
     are known by construction.  MUST: the regime is active exactly for the sessions
     2026-07-02 .. 2026-09-01 (first session after the 07-01 release, through the session ON
     the 09-01 release date); July row entry = 07-01 close, exit = 07-31 close, 21 sessions;
     August row entry = 07-31 close (prior month's last close), exit = 08-31 close,
     21 sessions; September row entry = 08-31 close, exit = 09-01 close, 1 session; three
     legs x three months = 9 rows, unique dedup keys, contract schema.
  2. Journal timing.  `now` mid-August: only the July rows; include_open adds August
     month-to-date; status reports the month-to-date position and the days in regime.
     `now` during the 07-31 session: the partial bar is dropped, the July row withheld and
     status says so; `now` after the month end: the July row is back, complete.
  3. Real-shaped current file (single release 2026-09-01 value 54.6): no rows, status
     inactive.  The live data/forward dir must also give no rows while every stored print
     is >= 50 (its status is printed).
  4. Empty list, empty file, missing file: no rows, status "no releases", no exception.
  5. Archived comparison.  The archived release list and session frames are produced by
     run_r61_pmi.py's OWN code: the segment from `ev = json.loads(` through `def build_days`
     is located by text markers and exec'd unmodified (with run_r37_scalps.py's
     load_frame / rth_of, as that script does); nothing below `def stats` is executed and
     the `oos` column is dropped on return.  The archived session closes are written as
     IBKR-schema daily JSON (13:30 UTC bar start) plus the archived releases as ism_pmi.json
     into a temp data_dir.  MUST, per index (SPX, NDX, RTY->RUT): the leg's per-session
     regime level equals build_days' `pmi`; the set of active sessions is identical; for
     every calendar month the row's session count, date and (exit - entry) equal the count,
     last date and telescoped sum of the archive's close-to-close bookings (c - prevc) over
     that month's active sessions; pooled totals agree.  SKIPPED (stated, not faked) when
     data/econ_events_us_high_fxs.json or the *_5m.csv frames are absent.
"""
import datetime as dt
import json
import os
import sys
import tempfile
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.abspath(os.path.join(HERE, ".."))
for p in (HERE, BT):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(BT)
import leg_pmi  # noqa: E402

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def info(name, detail=""):
    print(f"  [info] {name}" + (f"  -- {detail}" if detail else ""))


# ------------------------------------------------------------------- synthetic fixtures
LEGS = ("SPX", "NDX", "RUT")
BASE = {"SPX": 6000.0, "NDX": 21000.0, "RUT": 2200.0}
HOLIDAYS = {dt.date(2026, 7, 3), dt.date(2026, 9, 7)}
RELEASES = [{"release": "2026-06-01", "month": "2026-05", "value": 52.0},
            {"release": "2026-07-01", "month": "2026-06", "value": 49.0},
            {"release": "2026-08-03", "month": "2026-07", "value": 48.5},
            {"release": "2026-09-01", "month": "2026-08", "value": 51.0}]


def calendar_2026():
    d, out = dt.date(2026, 6, 1), []
    while d <= dt.date(2026, 9, 30):
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def closes_for(leg, cal):
    """Known closes: distinct per session and per leg, nothing to reverse-engineer."""
    return {d: round(BASE[leg] + 1.25 * i + 0.1 * ((i * 7) % 11), 2) for i, d in enumerate(cal)}


def write_ibkr(path, cal, closes):
    t = [f"{d.isoformat()}T13:30:00Z" for d in cal]
    c = [closes[d] for d in cal]
    json.dump(dict(chart_step=86400, source="Last", delayed=900, time=t,
                   open=[x - 3.0 for x in c], high=[x + 5.0 for x in c],
                   low=[x - 6.0 for x in c], close=c), open(path, "w"))


def make_dir(tmp, cal, releases):
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    if releases is not None:
        with open(os.path.join(tmp, "ism_pmi.json"), "w") as fh:
            fh.write(releases if isinstance(releases, str) else json.dumps(releases))
    allc = {}
    for leg in LEGS:
        cl = closes_for(leg, cal)
        allc[leg] = cl
        k = len(cal) * 2 // 3                     # two overlapping pulls, dedup on load
        write_ibkr(os.path.join(tmp, f"{leg.lower()}_daily_a.json"), cal[:k], cl)
        write_ibkr(os.path.join(tmp, f"{leg.lower()}_daily_b.json"), cal[k - 10:], cl)
    return allc


def by_leg_month(rs):
    out = {}
    for r in rs:
        leg, n = r["note"].split("|")
        out[(leg, r["date"][:7])] = dict(r, n=int(n.split()[0]))
    return out


tmpdir = tempfile.mkdtemp(prefix="leg_pmi_")
cal = calendar_2026()
print("\n=== 1. synthetic regime (releases 52.0 / 49.0 / 48.5 / 51.0, bars 2026-06..09) ===")
closes = make_dir(tmpdir, cal, RELEASES)
NOW_END = "2026-10-01T00:00:00Z"
res = leg_pmi.compute(tmpdir, now=NOW_END)
d = res["legs"]["SPX"]["d"]
check("all synthetic sessions loaded, duplicates collapsed",
      list(d["date"]) == cal, f"{len(d)} sessions {cal[0]} .. {cal[-1]}")
act = dict(zip(d["date"], d["active"]))
exp_active = {x for x in cal if dt.date(2026, 7, 1) < x <= dt.date(2026, 9, 1)}
check("regime active exactly 2026-07-02 .. 2026-09-01",
      {x for x, a in act.items() if a} == exp_active,
      f"{sum(act.values())} active sessions; 07-01 {act[dt.date(2026, 7, 1)]}, "
      f"07-02 {act[dt.date(2026, 7, 2)]}, 09-01 {act[dt.date(2026, 9, 1)]}, "
      f"09-02 {act[dt.date(2026, 9, 2)]}")
check("first active session is the first session after the 2026-07-01 release",
      min(x for x, a in act.items() if a) == dt.date(2026, 7, 2))
check("last active session is the 2026-09-01 release-day session; inactive after",
      max(x for x, a in act.items() if a) == dt.date(2026, 9, 1)
      and not any(a for x, a in act.items() if x > dt.date(2026, 9, 1)))
check("no regime before the first release / while >= 50 (June all inactive)",
      not any(a for x, a in act.items() if x.month == 6))
lvl = dict(zip(d["date"], d["pmi"]))
check("governing level: 07-01 -> 52.0, 07-02 -> 49.0, 08-03 -> 49.0, 08-04 -> 48.5, 09-01 -> 48.5, 09-02 -> 51.0",
      (lvl[dt.date(2026, 7, 1)], lvl[dt.date(2026, 7, 2)], lvl[dt.date(2026, 8, 3)],
       lvl[dt.date(2026, 8, 4)], lvl[dt.date(2026, 9, 1)], lvl[dt.date(2026, 9, 2)])
      == (52.0, 49.0, 49.0, 48.5, 48.5, 51.0))

rows = leg_pmi.rows(tmpdir, now=NOW_END)
check("9 rows (3 legs x July/August/September)", len(rows) == 9, f"{len(rows)} rows")
keys = {(r["date"], r["instr"], r["note"]) for r in rows}
check("dedup keys unique", len(keys) == len(rows))
check("schema: keys, instr PMI, side L, stop == entry, src auto, floats",
      all(set(r) == {"date", "instr", "side", "entry", "stop", "exit", "note", "src"}
          and r["instr"] == "PMI" and r["side"] == "L" and r["src"] == "auto"
          and r["stop"] == r["entry"] and all(isinstance(r[k], float) for k in ("entry", "stop", "exit"))
          for r in rows))
bm = by_leg_month(rows)
jul = [x for x in cal if x.month == 7 and x > dt.date(2026, 7, 1)]
aug = [x for x in cal if x.month == 8]
check("expected session counts by calendar: July 21, August 21, September 1",
      (len(jul), len(aug)) == (21, 21), f"July {len(jul)}, August {len(aug)}")
for leg in LEGS:
    cl = closes[leg]
    j, a, s = bm[(leg, "2026-07")], bm[(leg, "2026-08")], bm[(leg, "2026-09")]
    check(f"{leg} July: entry = 07-01 close {cl[dt.date(2026, 7, 1)]}, exit = 07-31 close "
          f"{cl[dt.date(2026, 7, 31)]}, 21 sessions, date 2026-07-31",
          (j["entry"], j["exit"], j["n"], j["date"], j["note"])
          == (cl[dt.date(2026, 7, 1)], cl[dt.date(2026, 7, 31)], 21, "2026-07-31", f"{leg}|21 sessions"),
          f"got entry {j['entry']} exit {j['exit']} note {j['note']} date {j['date']}")
    check(f"{leg} August: entry = prior month's last close (07-31) {cl[dt.date(2026, 7, 31)]}, "
          f"exit = 08-31 close {cl[dt.date(2026, 8, 31)]}, 21 sessions",
          (a["entry"], a["exit"], a["n"], a["date"])
          == (cl[dt.date(2026, 7, 31)], cl[dt.date(2026, 8, 31)], 21, "2026-08-31"),
          f"got entry {a['entry']} exit {a['exit']} note {a['note']} date {a['date']}")
    check(f"{leg} September: entry = 08-31 close, exit = 09-01 close (release-day session), 1 session",
          (s["entry"], s["exit"], s["n"], s["date"])
          == (cl[dt.date(2026, 8, 31)], cl[dt.date(2026, 9, 1)], 1, "2026-09-01"),
          f"got entry {s['entry']} exit {s['exit']} note {s['note']} date {s['date']}")
# telescoping identity on the synthetic data: sum of daily bookings == exit - entry
for leg in LEGS:
    cl = closes[leg]
    seq = [x for x in cal]
    tele = sum(cl[seq[i]] - cl[seq[i - 1]] for i in range(1, len(seq)) if seq[i] in exp_active)
    tot = sum(r["exit"] - r["entry"] for r in rows if r["note"].startswith(leg))
    check(f"{leg}: sum of month rows == sum of daily close-to-close bookings over active sessions",
          abs(tele - tot) < 1e-9, f"{tot:+.2f} vs {tele:+.2f}")
st = leg_pmi.status(tmpdir, now=NOW_END)
info("status at 2026-10-01", st)
sep_after = [x for x in cal if x > dt.date(2026, 9, 1)]
check("status: latest print 51.0 released 2026-09-01, INACTIVE, flat since 2026-09-02, "
      f"{len(sep_after)} sessions in regime",
      "51.0" in st and "2026-09-01" in st and "INACTIVE" in st
      and "flat since 2026-09-02" in st and f"{len(sep_after)} sessions" in st)

print("\n=== 2. journal timing / partial-bar guard ===")
NOW_MID = "2026-08-20T12:00:00Z"
r_mid = leg_pmi.rows(tmpdir, now=NOW_MID)
r_mid_open = leg_pmi.rows(tmpdir, now=NOW_MID, include_open=True)
check("now 2026-08-20 12:00Z: rows() = the 3 closed July rows only",
      len(r_mid) == 3 and all(r["date"] == "2026-07-31" for r in r_mid), f"{len(r_mid)} rows")
mtd = [x for x in aug if x < dt.date(2026, 8, 20)]
bo = by_leg_month([r for r in r_mid_open if r["date"] != "2026-07-31"])
check(f"include_open adds August month-to-date: {len(mtd)} sessions, exit = 08-19 close, entry = 07-31 close",
      len(r_mid_open) == 6 and all(
          bo[(leg, "2026-08")]["n"] == len(mtd) and bo[(leg, "2026-08")]["date"] == "2026-08-19"
          and bo[(leg, "2026-08")]["exit"] == closes[leg][dt.date(2026, 8, 19)]
          and bo[(leg, "2026-08")]["entry"] == closes[leg][dt.date(2026, 7, 31)] for leg in LEGS),
      f"{len(r_mid_open)} rows with include_open")
st_mid = leg_pmi.status(tmpdir, now=NOW_MID)
info("status at 2026-08-20", st_mid)
n_in = len(jul) + len(mtd)
check(f"status: latest print 48.5 (released 2026-08-03), ACTIVE, active since 2026-07-02 (release "
      f"2026-07-01 = 49.0), {n_in} sessions, month-to-date for 3 legs, releases dated after now ignored",
      "latest print 48.5" in st_mid and "released 2026-08-03" in st_mid
      and "ACTIVE (< 50" in st_mid and "active since 2026-07-02" in st_mid and "49.0" in st_mid
      and f"{n_in} sessions" in st_mid and st_mid.count("month-to-date") == 3
      and "1 release(s) dated after 2026-08-20 ignored" in st_mid
      and "session in progress" not in st_mid)   # 12:00Z: the 08-20 cash session has not opened
NOW_PART = "2026-07-31T15:00:00Z"
r_part = leg_pmi.rows(tmpdir, now=NOW_PART)
r_part_open = leg_pmi.rows(tmpdir, now=NOW_PART, include_open=True)
st_part = leg_pmi.status(tmpdir, now=NOW_PART)
check("now during the 07-31 session: partial bar dropped, July row withheld",
      r_part == [] and len(r_part_open) == 3
      and all(r["date"] == "2026-07-30" and r["note"].endswith("|20 sessions") for r in r_part_open)
      and "session in progress, bar not used" in st_part and "2026-07-31" in st_part,
      f"rows {len(r_part)}, include_open {len(r_part_open)}")
r_next = leg_pmi.rows(tmpdir, now="2026-08-01T00:00:00Z")
check("now 2026-08-01 00:00Z (month over, no August session yet): July rows complete",
      len(r_next) == 3 and all(r["date"] == "2026-07-31" and r["note"].endswith("|21 sessions")
                                and r["exit"] == closes[r["note"][:3]][dt.date(2026, 7, 31)] for r in r_next))
r_flip = leg_pmi.rows(tmpdir, now="2026-09-02T21:00:00Z")
check("now after the 09-02 session (first inactive): September row closed by the regime end, not the calendar",
      any(r["date"] == "2026-09-01" and r["note"].endswith("|1 sessions") for r in r_flip)
      and len(r_flip) == 9, f"{len(r_flip)} rows")

print("\n=== 3. real-shaped current file / live data dir ===")
make_dir(tmpdir, cal, [{"release": "2026-09-01", "month": "2026-08", "value": 54.6}])
r_real = leg_pmi.rows(tmpdir, now=NOW_END, include_open=True)
st_real = leg_pmi.status(tmpdir, now=NOW_END)
info("status", st_real)
check("single release 2026-09-01 54.6: rows() empty (also with include_open), status INACTIVE with 54.6",
      r_real == [] and leg_pmi.rows(tmpdir, now=NOW_END) == []
      and "INACTIVE" in st_real and "54.6" in st_real and "2026-09-01" in st_real)
live = os.path.join(BT, "data", "forward")
try:
    live_rel = leg_pmi.load_releases(live)
    live_rows = leg_pmi.rows(live, include_open=True)
    live_st = leg_pmi.status(live)
    info("live data/forward releases", str([(r[0].isoformat(), r[1]) for r in live_rel]))
    info("live status", live_st)
    if live_rel and all(v >= 50 for _, v, _ in live_rel):
        check("live data/forward: every stored print >= 50 -> no rows, status INACTIVE",
              live_rows == [] and "INACTIVE" in live_st, f"{len(live_rows)} rows")
    else:
        info("live data/forward has a sub-50 print or no releases; rows", str(live_rows))
except Exception as e:  # noqa: BLE001
    check("live data/forward readable", False, f"{type(e).__name__}: {e}")

print("\n=== 4. empty / missing ism_pmi.json ===")
for label, payload in (("empty list", "[]"), ("empty file", ""), ("missing file", None)):
    make_dir(tmpdir, cal, payload)
    try:
        rr = leg_pmi.rows(tmpdir, now=NOW_END, include_open=True)
        ss = leg_pmi.status(tmpdir, now=NOW_END)
        check(f"{label}: no rows, status says no releases",
              rr == [] and ss.startswith("PMI: no releases"), ss)
    except Exception as e:  # noqa: BLE001
        check(f"{label}: no exception", False, f"{type(e).__name__}: {e}")

# ------------------------------------------------------------------ archived comparison
print("\n=== 5. archived comparison: run_r61_pmi.py build_days (exec'd) vs leg_pmi ===")
EV = os.path.join(BT, "data", "econ_events_us_high_fxs.json")
R61 = os.path.join(BT, "run_r61_pmi.py")
R37 = os.path.join(BT, "run_r37_scalps.py")
ARCH = {"SPX": "SPX", "NDX": "NDX", "RTY": "RUT"}          # archive index -> forward leg
missing = [p for p in [EV, R61, R37] + [os.path.join(BT, "data", f"{i}_5m.csv") for i in ARCH]
           if not os.path.exists(p)]
if missing:
    info("SKIPPED: archived inputs absent, nothing compared", ", ".join(missing))
else:
    t0 = time.time()
    src37 = open(R37).read().split('if __name__ != "__main__"')[0]
    ns37 = {}
    exec(compile(src37, R37, "exec"), ns37)                   # defs + constants only
    _cache = {}

    def cached_load_frame(idx):                              # build_days reloads otherwise
        if idx not in _cache:
            _cache[idx] = ns37["load_frame"](idx)
        return _cache[idx]

    src61 = open(R61).read()
    seg = src61[src61.index("ev = json.loads("):src61.index("\ndef stats(")]
    ns61 = dict(pd=pd, np=np, json=json, load_frame=cached_load_frame, rth_of=ns37["rth_of"])
    exec(compile(seg, R61 + "[ev..build_days]", "exec"), ns61)
    pmi = ns61["pmi"]
    info("archived releases", f"{len(pmi)} ({pmi[0][0]} .. {pmi[-1][0]}), "
                              f"{sum(1 for _, v in pmi if v < 50)} below 50")
    arch_dir = tempfile.mkdtemp(prefix="leg_pmi_arch_")
    json.dump([dict(release=d0.isoformat(), month="", value=v) for d0, v in pmi],
              open(os.path.join(arch_dir, "ism_pmi.json"), "w"))
    refs = {}
    for idx, leg in ARCH.items():
        ref = ns61["build_days"](idx)
        ref = ref.drop(columns=["oos"])                       # not used, not looked at
        refs[idx] = ref
        full = ns37["rth_of"](cached_load_frame(idx)).groupby("skey").agg(
            o=("open", "first"), c=("close", "last"), hi=("high", "max"), lo=("low", "min"))
        full = full[np.isfinite(full.o) & np.isfinite(full.c)]
        json.dump(dict(chart_step=86400, source="Last",
                       time=[f"{k.isoformat()}T13:30:00Z" for k in full.index],
                       open=[float(x) for x in full.o], high=[float(x) for x in full.hi],
                       low=[float(x) for x in full.lo], close=[float(x) for x in full.c]),
                  open(os.path.join(arch_dir, f"{leg.lower()}_daily_archive.json"), "w"))
        info(f"{idx}: archived sessions", f"{len(full)} total, {len(ref)} from the first release "
                                          f"({full.index[0]} .. {full.index[-1]})")
    info("archive rebuilt", f"{time.time() - t0:.0f} s")
    mine = leg_pmi.compute(arch_dir)
    mrows = leg_pmi.rows(arch_dir, include_open=True)
    pooled_ref, pooled_mine, n_ref, n_mine, worst = 0.0, 0.0, 0, 0, 0.0
    for idx, leg in ARCH.items():
        ref, md = refs[idx], mine["legs"][leg]["d"]
        mlvl = dict(zip(md["date"], md["pmi"]))
        common = [k for k in ref.index if k in mlvl]
        same_lvl = len(common) == len(ref) and all(
            (np.isnan(ref.pmi[k]) and np.isnan(mlvl[k])) or ref.pmi[k] == mlvl[k] for k in common)
        check(f"{idx}: per-session governing release value equals build_days pmi on all {len(ref)} sessions",
              same_lvl, f"{len(common)} common sessions")
        ref_act = ref[ref.pmi < 50]
        mine_act = {k for k, a in zip(md["date"], md["active"]) if a}
        check(f"{idx}: active-session set identical ({len(ref_act)} sessions)",
              set(ref_act.index) == mine_act, f"leg {len(mine_act)}")
        booked = ref_act[np.isfinite(ref_act.prevc) & np.isfinite(ref_act.atr20) & (ref_act.atr20 > 0)]
        if len(booked) != len(ref_act):
            info(f"{idx}: archive run() mask drops {len(ref_act) - len(booked)} active sessions (no prevc/atr20)")
        pnl = (ref_act.c - ref_act.prevc)
        ym = pd.Series([(k.year, k.month) for k in ref_act.index], index=ref_act.index)
        g = pd.DataFrame(dict(pnl=pnl, ym=ym)).groupby("ym")
        ref_m = {k: (float(v.pnl.sum()), len(v), v.index[-1]) for k, v in g}
        my_m = {}
        for r in mrows:
            if r["note"].startswith(leg + "|"):
                kd = dt.date.fromisoformat(r["date"])
                my_m[(kd.year, kd.month)] = (r["exit"] - r["entry"], int(r["note"].split("|")[1].split()[0]), kd)
        skipped = [m for l_, m in mine["skipped"] if l_ == leg]
        check(f"{idx}: same set of months with active sessions ({len(ref_m)} months; leg rows {len(my_m)}, "
              f"skipped for missing entry {len(skipped)})",
              set(ref_m) == set(my_m), f"only-archive {sorted(set(ref_m) - set(my_m))[:5]}, "
                                       f"only-leg {sorted(set(my_m) - set(ref_m))[:5]}")
        diffs, bad = [], []
        for k in sorted(set(ref_m) & set(my_m)):
            (rp, rn, rd), (mp, mn, mdt) = ref_m[k], my_m[k]
            diffs.append(abs(rp - mp))
            if rn != mn or rd != mdt or abs(rp - mp) > 1e-6 * max(1.0, abs(rp)):
                bad.append((k, rn, mn, rd, mdt, rp, mp))
        wd = max(diffs) if diffs else 0.0
        worst = max(worst, wd)
        check(f"{idx}: every month's session count, date and (exit - entry) == telescoped archive bookings",
              not bad and set(ref_m) == set(my_m), f"max |diff| {wd:.3e} pts over {len(diffs)} months"
              + (f"; first mismatch {bad[0]}" if bad else ""))
        pooled_ref += float(pnl.sum()); pooled_mine += sum(v[0] for v in my_m.values())
        n_ref += len(ref_act); n_mine += sum(v[1] for v in my_m.values())
    check(f"pooled: {n_ref} archived active sessions == {n_mine} journalled sessions; gross points agree",
          n_ref == n_mine and abs(pooled_ref - pooled_mine) <= 1e-6 * max(1.0, abs(pooled_ref)),
          f"archive {pooled_ref:+.2f} vs leg {pooled_mine:+.2f} pts (gross, no cost), worst month diff {worst:.3e}")
    info("archived status", leg_pmi.status(arch_dir))
    info("archived rows", f"{len(mrows)} month rows; first {mrows[0] if mrows else None}; last {mrows[-1] if mrows else None}")

# -------------------------------------------------------------------------- verdict
fails = [c for c in checks if not c[1]]
print(f"\n{len(checks) - len(fails)}/{len(checks)} MUST checks passed"
      + (": FAIL " + "; ".join(c[0] for c in fails) if fails else ""))
sys.exit(1 if fails else 0)
