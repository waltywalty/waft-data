"""Forward-data robustness stress test for forward/leg_mhi.py (synthetic files, temp dir).

Run: cd backtest && python3 forward/stress_leg_mhi.py
Reference for "right" = run_hsi.py's own H-A code exec'd via test_leg_mhi.run_hsi_cell.
"""
import json, os, re, sys, tempfile, traceback
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE); sys.path.insert(0, BT)
import leg_mhi                                  # noqa: E402
from test_leg_mhi import run_hsi_cell, load_hk33  # noqa: E402

TMP = os.environ.get("TMPDIR") or None
results = []


def rec(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


# ------------------------------------------------------------------ synthetic feed
SLOTS = [h * 100 + m for h in range(1, 19) for m in (0, 15, 30, 45)]
SLOTS = [s for s in SLOTS if s >= 115 and not (400 <= s < 500)]     # real feed: no lunch bars


def make_feed(days, pushes, seed=0, level=25000.0, rng_pts=80.0, stop_hit=None):
    """15m bars for the given list of UTC dates.  pushes[d] = 01:15 bar close-open (pts).
    stop_hit[d] True forces a session bar to pierce the fade stop."""
    r = np.random.default_rng(seed)
    rows, px = [], level
    for d in days:
        push = pushes.get(d, r.normal(0, 4.0))
        for s in SLOTS:
            t = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=s // 100, minutes=s % 100)
            if s == 115:
                o = px; c = o + push
                hi = max(o, c) + 3.0; lo = min(o, c) - 3.0
            else:
                o = px; c = o + r.normal(0, rng_pts / 12)
                hi = max(o, c) + abs(r.normal(0, 4)); lo = min(o, c) - abs(r.normal(0, 4))
            if stop_hit and stop_hit.get(d) and s == 300:
                # push>0 -> short, stop = pre_hi + 0.5*pre_rng; go far beyond it
                sgn = 1 if push > 0 else -1
                hi = hi + sgn * 400 if sgn > 0 else hi
                lo = lo + sgn * 400 if sgn < 0 else lo
            rows.append((t.isoformat(), round(o, 1), round(hi, 1), round(lo, 1), round(c, 1), 500.0))
            px = c
    return pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])


def weekdays(start, n):
    out, t = [], pd.Timestamp(start)
    while len(out) < n:
        if t.dayofweek < 5:
            out.append(t.date())
        t += pd.Timedelta(days=1)
    return out


def write(df, d, name="hk33_m15.csv", **kw):
    os.makedirs(d, exist_ok=True)
    df.to_csv(os.path.join(d, name), index=False, **kw)
    return d


def ref_rows(path):
    """Frozen rule via run_hsi.py's exec'd code -> list of (date, side, entry, exit)."""
    f, A, met, atr = run_hsi_cell(load_hk33(path))
    sub = A[np.abs(A.push_n) >= 0.3]
    out = []
    for (_, r), (_, t) in zip(sub.iterrows(), f.iterrows()):
        sgn = -np.sign(r.push)
        px = t.pnl + 10.0   # sgn*(px-e)
        out.append((r.d.isoformat(), "S" if sgn < 0 else "L", float(t.ent), float(t.ent + px / sgn)))
    return out


def leg_tuple(rs):
    return [(r["date"], r["side"], r["entry"], r["exit"]) for r in rs]


def same(a, b, tol=1e-6):
    if len(a) != len(b):
        return False
    return all(x[0] == y[0] and x[1] == y[1] and abs(x[2] - y[2]) < tol and abs(x[3] - y[3]) < tol
               for x, y in zip(a, b))


def call(fn, *a, **k):
    try:
        return fn(*a, **k), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


SCHEMA_KEYS = ["date", "instr", "side", "entry", "stop", "exit", "note", "src"]


def schema_ok(rs):
    bad = []
    for r in rs:
        if list(r.keys()) != SCHEMA_KEYS and set(r) != set(SCHEMA_KEYS):
            bad.append(("keys", list(r)))
        if not (isinstance(r["date"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"])):
            bad.append(("date", r["date"]))
        if r["instr"] != "MHI" or r["src"] != "auto" or r["side"] not in ("L", "S"):
            bad.append(("const", r))
        for k in ("entry", "stop", "exit"):
            if type(r[k]) is not float:
                bad.append((k, type(r[k]).__name__))
        if not re.fullmatch(r"fade\|(stop|time)", r["note"]):
            bad.append(("note", r["note"]))
        try:
            json.dumps(r)
        except Exception as e:
            bad.append(("json", str(e)))
    return bad


def main():
    days = weekdays("2026-06-01", 45)
    trig = {days[20]: +150.0, days[27]: -160.0, days[33]: +140.0, days[40]: -170.0}
    base = make_feed(days, trig, seed=1, stop_hit={days[27]: True, days[40]: True})

    with tempfile.TemporaryDirectory(dir=TMP) as td:
        # ---------------------------------------------------------------- S0 baseline
        d0 = write(base, os.path.join(td, "s0"))
        R0 = leg_mhi.rows(d0); ref0 = ref_rows(os.path.join(d0, "hk33_m15.csv"))
        print("S0 baseline synthetic 45 weekdays:", leg_tuple(R0))
        rec("S0 leg == run_hsi rule on synthetic feed", same(leg_tuple(R0), ref0) and len(R0) >= 3,
            f"n={len(R0)} notes={[r['note'] for r in R0]}")
        rec("S0 row schema exact (keys/types/date/note/json)", not schema_ok(R0), str(schema_ok(R0)))

        # ---------------------------------------------------------------- S1 shuffled order
        d1 = write(base.sample(frac=1, random_state=3), os.path.join(td, "s1"))
        rec("S1 shuffled row order -> identical rows", leg_mhi.rows(d1) == R0)

        # ---------------------------------------------------------------- S2 exact duplicate rows
        d2 = write(pd.concat([base, base.tail(600), base.head(300)]), os.path.join(td, "s2"))
        rec("S2 exact duplicate rows (overlapping re-pulls) -> identical rows", leg_mhi.rows(d2) == R0)

        # ---------------------------------------------------------------- S3 conflicting duplicates
        # trigger day days[20] (short, time exit in baseline).  Add a second copy of the 03:00
        # bar whose high pierces the stop: "complete bar" vs the earlier "partial bar".
        r20 = [r for r in R0 if r["date"] == days[20].isoformat()][0]
        t300 = (pd.Timestamp(days[20], tz="UTC") + pd.Timedelta(hours=3)).isoformat()
        full = base[base.datetime == t300].copy(); full["high"] = r20["stop"] + 50
        d3a = write(pd.concat([base, full]), os.path.join(td, "s3a"))            # partial first, full appended
        d3b = write(pd.concat([full, base]), os.path.join(td, "s3b"))            # full first
        ra = [r for r in leg_mhi.rows(d3a) if r["date"] == days[20].isoformat()][0]
        rb = [r for r in leg_mhi.rows(d3b) if r["date"] == days[20].isoformat()][0]
        print(f"S3 conflicting duplicate 03:00 bar: appended-last wins? note={ra['note']}; "
              f"first-in-file wins? note={rb['note']}")
        rec("S3 later (appended) duplicate supersedes earlier partial bar", ra["note"] == "fade|stop",
            f"got {ra['note']} (keep='first' + unstable sort)")
        # S3c: is the survivor deterministic in file order at all?  Triplicate every bar of the
        # trigger day with distinct 'high' values (copy k has high+k*1000 for k=1,2) and ask
        # which copy the loader kept: with quicksort + keep='first' it is arbitrary.
        day_rows = base[base.datetime.str.startswith(days[20].isoformat())]
        cps = [day_rows] + [day_rows.assign(high=day_rows.high + k * 1000) for k in (1, 2)]
        d3c = write(pd.concat([base] + cps[1:]), os.path.join(td, "s3c"))
        H3c = leg_mhi.load(d3c).loc[days[20].isoformat()]
        kept = ((H3c.high.values - day_rows.high.values) / 1000).round().astype(int)
        print(f"S3c survivor copy per bar (0=first-in-file, 2=last-in-file): {np.bincount(kept, minlength=3).tolist()} of {len(kept)} bars")
        rec("S3c duplicate survivor is deterministic (all first or all last in file)",
            len(set(kept.tolist())) == 1, f"mix of copies kept: {sorted(set(kept.tolist()))}")

        # ---------------------------------------------------------------- S4 naive timestamps
        naive = base.copy(); naive["datetime"] = naive.datetime.str.replace("+00:00", "", regex=False)
        rec("S4 timestamps without +00:00 -> identical", leg_mhi.rows(write(naive, os.path.join(td, "s4"))) == R0)
        # Z suffix
        z = base.copy(); z["datetime"] = z.datetime.str.replace("+00:00", "Z", regex=False)
        rec("S4b timestamps with Z suffix -> identical", leg_mhi.rows(write(z, os.path.join(td, "s4b"))) == R0)

        # ---------------------------------------------------------------- S5 floats as strings
        d5 = write(base, os.path.join(td, "s5"), quoting=1)     # QUOTE_ALL -> "25000.0"
        rec("S5 quoted numeric strings -> identical", leg_mhi.rows(d5) == R0)
        s5b = base.copy()
        for c in ("open", "high", "low", "close"):
            s5b[c] = s5b[c].map(lambda v: f" {v}")               # leading space
        rec("S5b numbers with leading whitespace -> identical", leg_mhi.rows(write(s5b, os.path.join(td, "s5b"))) == R0)

        # ---------------------------------------------------------------- S6 non-numeric cell
        d6 = write(base, os.path.join(td, "s6"))
        lines = open(os.path.join(d6, "hk33_m15.csv")).read().splitlines()
        f = lines[1501].split(","); f[2] = "abc"; lines[1501] = ",".join(f)      # one junk 'high' cell
        open(os.path.join(d6, "hk33_m15.csv"), "w").write("\n".join(lines) + "\n")
        got, err = call(leg_mhi.rows, d6)
        print("S6 one non-numeric cell ->", err or f"rows n={len(got)}")
        rec("S6 non-numeric cell fails loudly (no silent rows)", err is not None or got == R0, err or "rows == baseline")

        # ---------------------------------------------------------------- S7 NaN in the pre bar
        s7 = base.copy()
        t115 = (pd.Timestamp(days[20], tz="UTC") + pd.Timedelta(hours=1, minutes=15)).isoformat()
        s7.loc[s7.datetime == t115, "close"] = np.nan
        R7 = leg_mhi.rows(write(s7, os.path.join(td, "s7")))
        rec("S7 NaN 01:15 close -> that day silently dropped, others unchanged",
            [r for r in R7 if r["date"] != days[20].isoformat()] == [r for r in R0 if r["date"] != days[20].isoformat()]
            and not any(r["date"] == days[20].isoformat() for r in R7), f"n={len(R7)} vs {len(R0)}")

        # ---------------------------------------------------------------- S8 holiday gap
        hol = days[18]
        s8 = base[~base.datetime.str.startswith(hol.isoformat())]
        d8 = write(s8, os.path.join(td, "s8"))
        rec("S8 whole-day holiday gap -> leg == run_hsi rule", same(leg_tuple(leg_mhi.rows(d8)), ref_rows(os.path.join(d8, "hk33_m15.csv"))))

        # ---------------------------------------------------------------- S9 partial current day
        last_trig = days[40]
        for cut_hm, expect_row in ((120, False), (300, False), (630, False), (750, False), (800, False), (815, True)):   # 0800 cut = last bar 07:45 (still open) -> guard waits for the 08:00 bar
            cut = pd.Timestamp(last_trig, tz="UTC") + pd.Timedelta(hours=cut_hm // 100, minutes=cut_hm % 100)
            s9 = base[pd.to_datetime(base.datetime, utc=True) < cut]
            d9 = write(s9, os.path.join(td, f"s9_{cut_hm}"))
            g = leg_mhi.rows(d9); ng = leg_mhi.rows(d9, require_complete=False)
            has = any(r["date"] == last_trig.isoformat() for r in g)
            nhas = [r for r in ng if r["date"] == last_trig.isoformat()]
            st, serr = call(leg_mhi.status, d9)
            rec(f"S9 file cut at {cut_hm:04d} UTC on trigger day -> row emitted={expect_row}",
                has == expect_row and g[:-1 if has else None] == R0[:len(g) - (1 if has else 0)] and serr is None,
                f"guarded={has} unguarded={bool(nhas)}{' exit=' + str(nhas[0]['exit']) if nhas else ''}; status: {serr or st[-60:]}")

        # ---------------------------------------------------------------- S10 no signals
        quiet = make_feed(weekdays("2026-06-01", 25), {}, seed=5)
        R10, e10 = call(leg_mhi.rows, write(quiet, os.path.join(td, "s10")))
        st10, e10s = call(leg_mhi.status, os.path.join(td, "s10"))
        rec("S10 weeks with no signal -> [] and status ok", R10 == [] and e10 is None and e10s is None, e10 or e10s or st10)
        short = make_feed(weekdays("2026-06-01", 5), {d: 300.0 for d in weekdays("2026-06-01", 5)}, seed=6)
        R10b, e10b = call(leg_mhi.rows, write(short, os.path.join(td, "s10b")))
        rec("S10b one week only (ATR warm-up) -> [] not crash", R10b == [] and e10b is None, e10b or "")

        # ---------------------------------------------------------------- S11 weekend bars
        sats = [d + pd.Timedelta(days=(5 - d.weekday())) for d in days if d.weekday() == 4]
        sat_rows = []
        for sd in sats:
            for s in (115, 130, 145, 200):
                t = pd.Timestamp(sd, tz="UTC") + pd.Timedelta(hours=s // 100, minutes=s % 100)
                sat_rows.append((t.isoformat(), 25000.0, 25002.0, 24998.0, 25001.0, 1.0))
        s11 = pd.concat([base, pd.DataFrame(sat_rows, columns=base.columns)])
        d11 = write(s11, os.path.join(td, "s11"))
        R11 = leg_mhi.rows(d11)
        rec("S11 weekend stub bars -> leg still == run_hsi rule (both polluted)",
            same(leg_tuple(R11), ref_rows(os.path.join(d11, "hk33_m15.csv"))))
        print(f"S11 weekend bars change the trade set: n={len(R11)} vs baseline {len(R0)} (ATR14 diluted by tiny Saturday ranges)")

        # ---------------------------------------------------------------- S12/13/14 absent / empty
        got, err = call(leg_mhi.rows, os.path.join(td, "nope"))
        print("S12 file absent -> rows:", err or got)
        rec("S12 file absent: rows() returns [] (contract: list) or raises", got == [] or err is not None, err or "")
        rec("S12b file absent: rows() returns [] rather than raising", got == [], err or "")
        got, err = call(leg_mhi.status, os.path.join(td, "nope"))
        rec("S12c file absent: status() returns str rather than raising", isinstance(got, str), err or got)
        d13 = write(base.iloc[0:0], os.path.join(td, "s13"))
        got, err = call(leg_mhi.rows, d13)
        rec("S13 header-only file: rows() -> []", got == [], err or "")
        got, err = call(leg_mhi.status, d13)
        rec("S13b header-only file: status() -> str", isinstance(got, str), err or got)
        os.makedirs(os.path.join(td, "s14")); open(os.path.join(td, "s14", "hk33_m15.csv"), "w").close()
        got, err = call(leg_mhi.rows, os.path.join(td, "s14"))
        rec("S14 zero-byte file: rows() -> [] or loud error", got == [] or err is not None, err or "")

        # ---------------------------------------------------------------- S15 mid-session collector gap
        tday = days[33]   # time exit in baseline
        r33 = [r for r in R0 if r["date"] == tday.isoformat()][0]
        t7 = pd.Timestamp(tday, tz="UTC") + pd.Timedelta(hours=7)
        t8 = t7 + pd.Timedelta(hours=1)
        ts = pd.to_datetime(base.datetime, utc=True)
        s15 = base[~((ts >= t7) & (ts < t8))]                     # 07:00..07:45 bars missing, later data present
        R15 = leg_mhi.rows(write(s15, os.path.join(td, "s15")))
        r15 = [r for r in R15 if r["date"] == tday.isoformat()]
        print(f"S15 07:00-07:45 bars missing on a time-exit day: baseline exit {r33['exit']} vs gap-file exit {r15[0]['exit'] if r15 else None}")
        rec("S15 collector gap at session end: row NOT emitted or exit == true 07:45 close",
            (not r15) or abs(r15[0]["exit"] - r33["exit"]) < 1e-9,
            f"emitted exit={r15[0]['exit'] if r15 else None} (06:45 close) vs true {r33['exit']}")

        # ---------------------------------------------------------------- S16 column order / extra col
        s16 = base[["datetime", "volume", "close", "low", "high", "open"]].assign(extra=1)
        rec("S16 different column order + extra column -> identical", leg_mhi.rows(write(s16, os.path.join(td, "s16"))) == R0)
        s16b = base.copy()
        write(s16b, os.path.join(td, "s16b")); s16b.to_csv(os.path.join(td, "s16b", "hk33_m15.csv"), index=True)  # leading index col
        got, err = call(leg_mhi.rows, os.path.join(td, "s16b"))
        print("S16b file with a leading unnamed index column ->", err or f"rows n={len(got)} (silent!)" )
        rec("S16b leading index column fails loudly (not silent empty)", err is not None or got == R0, err or f"n={len(got)}")
        # CRLF line endings
        with open(os.path.join(td, "s16c.csv"), "w", newline="") as fh:
            fh.write(base.to_csv(index=False, lineterminator="\r\n"))
        os.makedirs(os.path.join(td, "s16c"), exist_ok=True); os.replace(os.path.join(td, "s16c.csv"), os.path.join(td, "s16c", "hk33_m15.csv"))
        rec("S16c CRLF line endings -> identical", leg_mhi.rows(os.path.join(td, "s16c")) == R0)

        # ---------------------------------------------------------------- S17 real forward file
        fwd = os.path.join(BT, "data", "forward")
        Rf = leg_mhi.rows(fwd)
        reff = ref_rows(os.path.join(fwd, "hk33_m15.csv"))
        rec("S17 real data/forward file: leg == run_hsi rule (all rows incl. new 2026-09-01)",
            same(leg_tuple(Rf), reff), f"n={len(Rf)} last={Rf[-1] if Rf else None}")
        rec("S17b idempotent (two calls identical)", leg_mhi.rows(fwd) == Rf)
        rec("S17c real forward rows schema exact", not schema_ok(Rf), str(schema_ok(Rf)))
        rec("S17d dedup key unique", len({(r['date'], r['instr'], r['note']) for r in Rf}) == len(Rf))

    nf = sum(1 for _, ok, _ in results if not ok)
    print(f"\nSUMMARY: {len(results) - nf}/{len(results)} passed")
    for n, ok, d in results:
        if not ok:
            print("  FAIL:", n, "--", d)
    return nf


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
