"""Verification of forward/leg_xau.py against the archived deployable trade set.

What it does
  1. Converts the archived CFD feed data/XAUUSD_5m.csv (engine.load_bars) into
     IBKR-schema JSON files (one per ISO week, plus a deliberately overlapping file to
     exercise concat/dedup); builds IBKR-style daily gold from the same bars on a
     22:00-UTC-anchored day; converts data/AUDUSD_daily_fred.csv into IBKR daily bars
     (21:15 UTC bar start, labelled by close date); converts data/AUDUSD_M5.csv into
     IBKR 5m files for the XAUAUD conversion.
  2. Runs leg_xau.rows()/compute() on that directory.
  3. Compares the XAU rows with results/trades_deployable.pkl (the archived deployable
     trade set written by deployable.py) and explains every mismatch. The only
     declared difference is the gold day boundary of the corr gate (22:00 UTC instead
     of Athens midnight), so every mismatch must be a gate flip on a day where the
     two correlations straddle 0.5, and there must be none of construction.
  4. Hand-checks the XAUAUD conversion on three trades from the raw AUD 5m CSV using
     the archive's own t_fill/t_out.
  5. Daily data lagging the 5m frame: the gate index must end at the last joint daily
     label (deployable.py line 17) so later sessions map to NaN and are dropped (line
     23) - deferred to a later check-in - never gated on a forward-filled stale value.
     Measures how often a stale ffill would flip the gate on the archive, then runs the
     leg on lagged directories (fixture and the real data/forward pull).

Run:  cd backtest && LEG_XAU_TMP=<scratch dir> python forward/test_leg_xau.py
deployable.py is deliberately NOT imported: importing it re-runs the study and
overwrites results/trades_deployable.pkl. Its gate (lines 10-17) is re-implemented here.
"""
import glob, json, os, shutil, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.dirname(HERE)
for p in (BT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
import engine, audusd, leg_xau

DATA = os.path.join(BT, "data")
ARCHIVE = os.path.join(BT, "results", "trades_deployable.pkl")
AUD5_START = "2020-08-01"          # only the part of AUDUSD_M5.csv that overlaps the gold data


# ------------------------------------------------------------------ fixture builders
def _iso(idx):
    return [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in idx]


def write_ibkr(path, df, step, source="Midpoint"):
    with open(path, "w") as fh:
        json.dump({"chart_step": step, "source": source, "delayed": 0,
                   "chart_start": _iso(df.index[:1])[0], "chart_end": _iso(df.index[-1:])[0],
                   "time": _iso(df.index),
                   "open": df.open.tolist(), "high": df.high.tolist(),
                   "low": df.low.tolist(), "close": df.close.tolist()}, fh)


def weekly_files(tmp, prefix, df, step):
    """One file per ISO week; returns [(path, first ts, last ts)]."""
    ic = df.index.isocalendar()
    out = []
    for (y, w), g in df.groupby([ic.year.to_numpy(), ic.week.to_numpy()]):
        path = os.path.join(tmp, f"{prefix}_{y}-W{int(w):02d}.json")
        write_ibkr(path, g, step)
        out.append((path, g.index[0], g.index[-1]))
    return out


def build_fixture(tmp, gold):
    # 5m gold, one file per ISO week + one overlapping duplicate slice (dedup test)
    files5 = weekly_files(tmp, "xauusd_5m", gold, 300)
    n5 = len(files5)
    mid = gold.loc["2023-03-06":"2023-03-10"]
    write_ibkr(os.path.join(tmp, "xauusd_5m_overlap.json"), mid, 300)

    # daily gold on the IBKR day (22:00 UTC bar start), quarterly files + overlap
    gd = gold.resample("24h", offset="22h").agg(open=("open", "first"), high=("high", "max"),
                                                low=("low", "min"), close=("close", "last")).dropna()
    assert (gd.index.hour == 22).all() and (gd.index.minute == 0).all()
    for (y, q), g in gd.groupby([gd.index.year, gd.index.quarter]):
        write_ibkr(os.path.join(tmp, f"xauusd_daily_{y}Q{q}.json"), g, 86400)
    write_ibkr(os.path.join(tmp, "xauusd_daily_overlap.json"), gd.iloc[400:440], 86400)

    # AUDUSD daily from FRED: the FRED obs dated D becomes the IBKR bar starting D-1 21:15Z
    ad = audusd.daily_from_fred(os.path.join(DATA, "AUDUSD_daily_fred.csv"))
    ad = ad[ad.index >= "2020-06-01"]
    idx = (pd.DatetimeIndex(ad.index) - pd.Timedelta(days=1)
           + pd.Timedelta(hours=21, minutes=15)).tz_localize("UTC")
    add = pd.DataFrame({"open": ad.to_numpy(), "high": ad.to_numpy(),
                        "low": ad.to_numpy(), "close": ad.to_numpy()}, index=idx)
    for y, g in add.groupby(add.index.year):
        write_ibkr(os.path.join(tmp, f"audusd_daily_{y}.json"), g, 86400)

    # AUDUSD 5m from the validated-UTC MT5 file
    a = pd.read_csv(os.path.join(DATA, "AUDUSD_M5.csv"), header=None,
                    names=["ts", "open", "high", "low", "close", "vol"], parse_dates=["ts"])
    a = a.set_index("ts").sort_index().tz_localize("UTC")
    a = a[~a.index.duplicated()].loc[AUD5_START:]
    na = len(weekly_files(tmp, "audusd_5m", a, 300))
    return dict(n5=n5, gd=gd, ad=ad, add=add, a5=a, na=na, files5=files5)


def lag_dir(base, tmp, fx, gold, cut, end5m):
    """A data_dir whose daily files end at session label `cut` and whose gold 5m frame
    ends at `end5m` (UTC): weekly 5m files before end5m are symlinked from the fixture,
    the week containing end5m is rewritten truncated, AUD 5m files are symlinked."""
    d = tempfile.mkdtemp(prefix="leg_xau_lag_", dir=base)
    for path, first, last in fx["files5"]:
        if last <= end5m:
            os.symlink(path, os.path.join(d, os.path.basename(path)))
        elif first <= end5m:
            write_ibkr(os.path.join(d, os.path.basename(path)), gold.loc[first:end5m], 300)
    for path in glob.glob(os.path.join(tmp, "audusd_5m_*.json")):
        os.symlink(path, os.path.join(d, os.path.basename(path)))
    label = lambda idx: (idx + leg_xau.SESSION_ROLL).tz_convert(None).normalize()
    gdd = fx["gd"][label(fx["gd"].index) <= cut]
    add = fx["add"][label(fx["add"].index) <= cut]
    write_ibkr(os.path.join(d, "xauusd_daily_lag.json"), gdd, 86400)
    write_ibkr(os.path.join(d, "audusd_daily_lag.json"), add, 86400)
    return d


# ------------------------------------------------------------- deployable.py lines 10-17
def athens_gate(gold):
    loc = gold.close.tz_convert(ZoneInfo("Europe/Athens"))
    gd = loc.resample("1D").last()
    gd = pd.Series(gd.values, index=pd.to_datetime([x.date() for x in gd.index])).dropna()
    ad = audusd.daily_from_fred(os.path.join(DATA, "AUDUSD_daily_fred.csv"))
    ad.index = pd.to_datetime(ad.index).normalize()
    j = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
                  axis=1, join="inner").dropna()
    return (j.g.rolling(20).corr(j.a)
             .reindex(pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill().shift(1))


def main():
    base = os.environ.get("LEG_XAU_TMP") or tempfile.gettempdir()
    os.makedirs(base, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="leg_xau_fixture_", dir=base)
    lag_dirs = []                                   # extra data_dirs of section 7, removed in finally
    fails = []
    check = lambda ok, msg: (print(("  ok   " if ok else "  FAIL ") + msg), None if ok else fails.append(msg))
    t0 = time.time()
    try:
        gold = engine.load_bars(os.path.join(DATA, "XAUUSD_5m.csv"))
        fx = build_fixture(tmp, gold)
        print(f"fixture: {fx['n5']} weekly gold 5m files, {fx['na']} weekly AUD 5m files in {tmp} "
              f"({time.time()-t0:.0f}s)")

        # ---- 1. loader round trip -------------------------------------------------
        g5 = leg_xau.load_ibkr(tmp, "xauusd_5m_*.json")
        check(len(g5) == len(gold), f"5m loader: {len(g5)} bars == {len(gold)} archived (overlap file deduped)")
        check(g5.index.equals(gold.index), "5m loader: identical UTC index")
        check(bool(np.array_equal(g5[["open", "high", "low", "close"]].to_numpy(),
                                  gold[["open", "high", "low", "close"]].to_numpy())),
              "5m loader: OHLC bit-identical to engine.load_bars")
        check((g5.volume == 0).all() and list(g5.columns) == ["open", "high", "low", "close", "volume"],
              "5m loader: engine.load_bars column layout, zero volume")

        gdl = leg_xau.daily_close(leg_xau.load_ibkr(tmp, "xauusd_daily_*.json"))
        exp = pd.Series(fx["gd"].close.to_numpy(),
                        index=(fx["gd"].index + pd.Timedelta(days=1)).tz_convert(None).normalize())
        check(len(gdl) == len(fx["gd"]) and gdl.index.equals(exp.index)
              and np.array_equal(gdl.to_numpy(), exp.to_numpy()),
              f"daily gold: {len(gdl)} bars, labelled by close date (first {gdl.index[0].date()}, "
              f"bar start 2020-08-20T22:00Z), overlap file deduped")
        adl = leg_xau.daily_close(leg_xau.load_ibkr(tmp, "audusd_daily_*.json"))
        check(adl.index.equals(pd.DatetimeIndex(fx["ad"].index)) and np.array_equal(adl.to_numpy(), fx["ad"].to_numpy()),
              f"daily AUDUSD: {len(adl)} bars labelled back to the FRED observation dates")
        # session-date labelling on every bar-start clock time seen in the real IBKR daily
        # pulls (data/forward, 2026-09-02): regular 22:00/23:00Z gold and 21:15/22:15Z AUD
        # evening starts, plus the shortened post-holiday sessions starting 00:00Z / 05:00Z
        starts = ["2026-08-27T22:00:00Z", "2025-12-22T23:00:00Z", "2026-04-01T21:15:00Z", "2025-12-29T22:15:00Z",
                  "2025-12-26T00:00:00Z", "2026-02-16T05:00:00Z", "2026-02-16T23:00:00Z"]
        want = ["2026-08-28", "2025-12-23", "2026-04-02", "2025-12-30", "2025-12-26", "2026-02-16", "2026-02-17"]
        lab = leg_xau.daily_close(pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": range(len(starts)),
                                                "volume": 0.0}, index=pd.to_datetime(starts, utc=True)))
        check([d.strftime("%Y-%m-%d") for d in lab.index] == sorted(want) and len(lab) == len(starts),
              "daily label rule: evening starts -> next date, 00:00Z/05:00Z holiday sessions -> own date, no collision")

        # ---- 2. run the leg ----------------------------------------------------------
        t1 = time.time()
        res = leg_xau.compute(tmp)
        rows = res["rows"]
        xau = [r for r in rows if r["instr"] == "XAU"]
        aud = [r for r in rows if r["instr"] == "XAUAUD"]
        print(f"leg_xau.compute: {len(res['trades_all'])} raw trades, {len(xau)} XAU rows, "
              f"{len(aud)} XAUAUD rows ({time.time()-t1:.0f}s)")

        # row schema
        keys = {"date", "instr", "side", "entry", "stop", "exit", "note", "src"}
        check(all(set(r) == keys for r in rows), "rows: exact contract key set")
        check(all(r["src"] == "auto" and r["side"] in ("L", "S") for r in rows), "rows: src=auto, side in L/S")
        check(all(r["note"] in ("time|60m", "stop|60m") for r in xau)
              and all(r["note"] in ("half|time|60m", "half|stop|60m") for r in aud), "rows: note format")
        check(all(isinstance(r[k], float) for r in rows for k in ("entry", "stop", "exit")), "rows: float prices")
        check(len({(r["date"], r["instr"], r["note"]) for r in rows}) == len(rows), "rows: dedup key unique")
        sgn = lambda r: 1 if r["side"] == "L" else -1
        check(all((r["stop"] < r["entry"]) == (r["side"] == "L") for r in rows), "rows: stop on the loss side")
        # stop == entry - side*2*range (XAU) and same stop % (XAUAUD), pairwise
        pair = {(r["date"], r["note"].split("|", 1)[1]): r for r in aud}
        same_pct = [abs(pair[(x["date"], x["note"])]["stop"] / pair[(x["date"], x["note"])]["entry"]
                        - x["stop"] / x["entry"]) for x in xau if (x["date"], x["note"]) in pair]
        check(bool(same_pct) and max(same_pct) < 2e-5, f"XAUAUD stop %% == XAU stop %% on {len(same_pct)} pairs "
              f"(max |diff| {max(same_pct) if same_pct else float('nan'):.1e})")

        # ---- 3. archive comparison ---------------------------------------------------
        if not os.path.exists(ARCHIVE):
            raise SystemExit(f"archive {ARCHIVE} not found - nothing to compare against")
        A = pd.read_pickle(ARCHIVE)
        print(f"archive {os.path.relpath(ARCHIVE, BT)}: {len(A)} trades, columns {list(A.columns)}")
        Akey = {(str(r.day), int(r.side)): r for r in A.itertuples()}
        Rkey = {(r["date"], sgn(r)): r for r in xau}
        matched = [k for k in Akey if k in Rkey and abs(Akey[k].entry - Rkey[k]["entry"]) <= 0.05]
        exit_ok = [k for k in matched if abs(Akey[k].exit - Rkey[k]["exit"]) <= 0.05]
        stop_ok = [k for k in matched
                   if abs((Akey[k].entry - Akey[k].side * 2 * Akey[k].range) - Rkey[k]["stop"]) <= 0.05]
        note_ok = [k for k in matched if Rkey[k]["note"] == f"{Akey[k].reason}|60m"]
        max_entry_diff = max((abs(Akey[k].entry - Rkey[k]["entry"]) for k in matched), default=0.0)
        max_exit_diff = max((abs(Akey[k].exit - Rkey[k]["exit"]) for k in matched), default=0.0)
        arch_days, rep_days = {k[0] for k in Akey}, {k[0] for k in Rkey}
        arch_only = sorted(arch_days - rep_days)
        rep_only = sorted(rep_days - arch_days)
        both_diff = sorted(d for d in arch_days & rep_days
                           if not any(k[0] == d for k in matched))
        print(f"archive trades {len(A)} | reproduced (same day, same side, entry within 0.05) {len(matched)} "
              f"| max |entry diff| {max_entry_diff:.2e} | exits match {len(exit_ok)} (max {max_exit_diff:.2e}) "
              f"| stops match {len(stop_ok)} | notes match {len(note_ok)}")
        print(f"archive-only days {len(arch_only)} | forward-only days {len(rep_only)} "
              f"| same day but different side/entry {len(both_diff)}")
        check(len(both_diff) == 0, "no construction mismatch on any common day")
        check(len(exit_ok) == len(matched) and len(stop_ok) == len(matched) and len(note_ok) == len(matched),
              "every reproduced trade also matches exit, stop and exit reason")

        # ---- 4. explain every mismatch via the two gates ----------------------------
        ta = res["trades_all"].copy()                    # every raw breakout trade, c = IBKR-day gate
        C_ath = athens_gate(gold)
        ta["c_ath"] = pd.to_datetime(ta.day).dt.normalize().map(C_ath)
        ta["keep_ibkr"] = ta.c.le(0.5)
        ta["keep_ath"] = ta.c_ath.le(0.5)
        ath_set = {(str(r.day), int(r.side)) for r in ta[ta.keep_ath].itertuples()}
        check(ath_set == set(Akey), f"re-running the archived gate on the JSON-loaded frame reproduces the archive "
                                    f"exactly ({len(ath_set)} trades) -> construction is identical")
        flips = ta[ta.keep_ibkr != ta.keep_ath]
        f_lost = flips[flips.keep_ath & ~flips.keep_ibkr]
        f_gain = flips[flips.keep_ibkr & ~flips.keep_ath]
        nan_only = flips[flips.c.isna() != flips.c_ath.isna()]
        check(set(str(d) for d in f_lost.day) == set(arch_only)
              and set(str(d) for d in f_gain.day) == set(rep_only),
              "every archive-only / forward-only day is exactly a corr-gate flip")
        both = ta.dropna(subset=["c", "c_ath"])
        dc = (both.c - both.c_ath).abs()
        print(f"gate: {len(ta)} raw trade days; gate flips {len(flips)} = {len(flips)/len(ta)*100:.2f}% "
              f"(archive kept / IBKR-day closed {len(f_lost)}, IBKR-day kept / archive closed {len(f_gain)}, "
              f"NaN-on-one-side {len(nan_only)})")
        print(f"gate: corr difference on {len(both)} trade days: mean |dc| {dc.mean():.4f}, "
              f"median {dc.median():.4f}, max {dc.max():.4f}")
        for lab, fr in (("archive kept, forward closed", f_lost), ("forward kept, archive closed", f_gain)):
            for r in fr.itertuples():
                print(f"    {lab}: {r.day} side {r.side:+d} corr Athens-day {r.c_ath:.3f} vs 22:00Z-day {r.c:.3f}")
        margin = flips.dropna(subset=["c", "c_ath"])
        check(len(flips) <= 0.03 * len(A),
              f"gate flips are few ({len(flips)} vs archive {len(A)} = {len(flips)/len(A)*100:.1f}%, bar 3%)")
        check(len(nan_only) == 0, "no day where one gate is NaN and the other is not")
        if len(margin):
            check(bool(((margin.c - 0.5).abs() < 0.06).all() and ((margin.c_ath - 0.5).abs() < 0.06).all()),
                  "flip days straddle the 0.5 threshold (both correlations within 0.06 of it)")
        # why the day-boundary substitution changes nothing on THIS feed: the Athens-day close
        # and the 22:00Z-day close pick the same 5m bar whenever the feed has no bars between
        # Athens midnight (21:00Z in summer, 22:00Z in winter) and 22:00Z.
        ath_close = gold.close.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").last().dropna()
        ath_close.index = pd.to_datetime([x.date() for x in ath_close.index])
        common = ath_close.index.intersection(gdl.index)
        ndiff = int((ath_close.loc[common].to_numpy() != gdl.loc[common].to_numpy()).sum())
        off = gold.index.tz_convert(ZoneInfo("Europe/Athens")).tz_localize(None) - gold.index.tz_localize(None)
        summer = gold[off == pd.Timedelta(hours=3)]
        n21 = int((summer.index.hour == 21).sum())
        last_bar_summer = summer.groupby(summer.index.date).apply(lambda d: d.index.max().strftime("%H:%M"))
        print(f"gate mechanism: Athens-day close != 22:00Z-day close on {ndiff} of {len(common)} joint days; "
              f"5m bars in the 21:00-21:55Z hour during EEST: {n21} of {len(summer)}; last bar of an EEST day "
              f"is {last_bar_summer.value_counts().index[0]}Z on {last_bar_summer.value_counts().iloc[0]} "
              f"of {len(last_bar_summer)} days")
        check(not (ndiff == 0 and len(flips) > 0),
              f"substitution effect measured on this feed: {ndiff} differing daily closes -> {len(flips)} gate flips "
              f"(IBKR forward data with prints in 21:00-22:00Z in summer CAN differ; not measurable here)")

        # ---- 5. XAUAUD hand check on 3 trades --------------------------------------
        a = pd.read_csv(os.path.join(DATA, "AUDUSD_M5.csv"), header=None,
                        names=["ts", "open", "high", "low", "close", "vol"], parse_dates=["ts"])
        a = a.set_index("ts").sort_index().tz_localize("UTC")
        a = a[~a.index.duplicated()]

        def hand_px(t):
            if t in a.index:
                return float(a.at[t, "open"])
            return float(a[a.index < t].iloc[-1]["close"])

        aud_rows = {(r["date"], sgn(r), r["note"].split("|", 1)[1]): r for r in aud}
        cov_end = a.index.max()
        in_cov = [k for k in matched if Akey[k].t_out <= cov_end]
        picks = []
        for want in (("time", 1), ("time", -1), ("stop", None)):
            for k in in_cov:
                r = Akey[k]
                if r.reason == want[0] and (want[1] is None or r.side == want[1]) and k not in [p[0] for p in picks]:
                    picks.append((k, r)); break
        check(len(picks) == 3, "found 3 trades (long time-exit, short time-exit, stop-exit) inside AUD 5m cover")
        for k, r in picks:
            a_in, a_out = hand_px(r.t_fill), hand_px(r.t_out)
            e = r.entry / a_in
            hand = dict(entry=e, stop=e * (1 - r.side * 2 * r.range / r.entry), exit=r.exit / a_out)
            row = aud_rows.get((k[0], k[1], f"{r.reason}|60m"))
            print(f"    XAUAUD hand check {k[0]} side {r.side:+d} {r.reason}: AUD@fill {a_in:.5f} ({r.t_fill:%H:%M}Z) "
                  f"AUD@out {a_out:.5f} ({r.t_out:%H:%M}Z) | USD entry {r.entry:.2f} stop "
                  f"{r.entry - r.side*2*r.range:.2f} exit {r.exit:.2f} | hand A$ entry {hand['entry']:.2f} "
                  f"stop {hand['stop']:.2f} exit {hand['exit']:.2f} | row {row and (row['entry'], row['stop'], row['exit'])}")
            check(row is not None and all(abs(row[f] - hand[f]) <= 0.005 + 1e-9 for f in hand),
                  f"XAUAUD row {k[0]} equals the hand conversion to the cent")
        n_expected = len(in_cov)
        sk = res["skipped_aud"]
        print(f"XAUAUD coverage: AUD 5m fixture ends {cov_end:%Y-%m-%d %H:%M}Z; {n_expected} reproduced XAU trades "
              f"close inside it; {len(aud)} XAUAUD rows emitted; leg skipped {len(sk)} "
              f"(first {sk[:1]}, last {sk[-1:]}) for lack of an AUD 5m print")
        check(len(aud) == n_expected, "one XAUAUD row per XAU trade inside AUD 5m cover, none outside")

        # ---- 6. status() ----------------------------------------------------------------
        st = leg_xau.status(tmp)
        print("status():\n    " + st.replace("\n", "\n    "))
        check(isinstance(st, str) and "XAU rows" in st, "status() returns a string")

        # ---- 7. daily data lagging the 5m frame -------------------------------------------
        # deployable.py line 17: C's index ends at the last joint daily label; line 23: a
        # trade day outside it (NaN) is dropped. Forward, that is a session whose daily
        # pull has not arrived yet: it must be deferred, not gated on a stale ffill.
        C_full = res["C"]
        jl = gdl.index.intersection(adl.index)
        check(C_full.index.max() == jl.max() and C_full.index.max() == res["gate_end"],
              f"gate index ends at the last joint daily label {jl.max().date()} (deployable.py line 17), "
              f"not at the last 5m session {g5.index.max().date()}")
        check(res["deferred"] == [] and (pd.to_datetime(ta.day).dt.normalize() <= jl.max()).all(),
              "full archive: daily data covers every trade day, nothing deferred")
        # what a stale forward-fill would have done: with daily data k joint sessions behind
        # trade day D the ffilled gate on D is corr through cut_k(D), i.e. C_full[cut_k + 1 day]
        gated = ta.dropna(subset=["c"]).copy()
        gated["D"] = pd.to_datetime(gated.day).dt.normalize()
        flip_days = {}
        for k in (1, 2, 3):
            pos = jl.searchsorted(gated.D.to_numpy(), side="left") - k
            cut_k = pd.DatetimeIndex([jl[i] if i >= 0 else pd.NaT for i in pos])
            stale = pd.Series((cut_k + pd.Timedelta(days=1)).map(lambda x: C_full.get(x, np.nan)), index=gated.index)
            phantom = gated[(stale <= 0.5) & (gated.c > 0.5)]
            missed = gated[(stale > 0.5) & (gated.c <= 0.5)]
            flip_days[k] = (phantom, missed, cut_k)
            print(f"stale-ffill gate with daily data {k} joint session(s) behind: {len(phantom)} phantom "
                  f"(stale <= 0.5, rule > 0.5) + {len(missed)} missed (stale > 0.5, rule <= 0.5) "
                  f"= {(len(phantom)+len(missed))/len(gated)*100:.1f}% of {len(gated)} gated trade days")
        k = 3 if len(flip_days[3][0]) else 2
        phantom, _, cut_k = flip_days[k]
        check(len(phantom) > 0, f"the archive contains days where a {k}-session-stale ffill would emit a row the rule never does")
        i = phantom.index[0]
        Dp, cut = phantom.D.loc[i], cut_k[list(gated.index).index(i)]
        end5m = Dp + pd.Timedelta(hours=21, minutes=59)
        end5m = end5m.tz_localize("UTC")
        d1 = lag_dir(base, tmp, fx, gold, cut, end5m); lag_dirs.append(d1)
        r1 = leg_xau.compute(d1)
        st1 = leg_xau.status(d1)
        rows1 = r1["rows"]
        exp1 = [r for r in rows if r["date"] <= str(cut.date())]
        late1 = r1["trades_all"][pd.to_datetime(r1["trades_all"].day).dt.normalize() > cut]
        old_val = leg_xau.corr_gate(r1["gd"], r1["ad"], extend_to=Dp).get(Dp, np.nan)
        print(f"lag scenario A (phantom): 5m through {end5m:%Y-%m-%d %H:%M}Z, daily through {cut.date()}; trade day "
              f"{Dp.date()} side {int(phantom.side.loc[i]):+d}: rule corr {phantom.c.loc[i]:.3f} (CLOSED, not in archive: "
              f"{str(Dp.date()) not in arch_days}); stale ffill would give {old_val:.3f} (OPEN)")
        print("    status():\n        " + st1.replace("\n", "\n        "))
        check(r1["gate_end"] == cut and len(r1["C"]) and r1["C"].index.max() == cut,
              f"lag A: gate defined through {cut.date()} only")
        check(len(late1) > 0 and late1.c.isna().all(),
              f"lag A: all {len(late1)} breakout trades after {cut.date()} have NaN gate")
        check(rows1 == exp1, f"lag A: rows == full-run rows dated <= {cut.date()} ({len(rows1)} rows), nothing after")
        check(not any(r["date"] == str(Dp.date()) for r in rows1) and old_val <= 0.5,
              f"lag A: no row on {Dp.date()} although the stale ffill ({old_val:.3f}) would have emitted one")
        check(r1["deferred"] == sorted(str(d) for d in late1.day) and "DEFERRED" in st1
              and str(Dp.date()) in st1 and "NOT DEFINED YET" in st1,
              f"lag A: status() names the {len(late1)} deferred session(s) and the undefined gate")
        # scenario B: a KEPT trade after the cut is deferred, and reappears identically once the
        # daily data is restored (the full run above), i.e. the drop is self-healing
        Dk = pd.Timestamp(xau[-1]["date"])
        cutB = jl[jl.searchsorted(Dk, side="left") - 3]
        d2 = lag_dir(base, tmp, fx, gold, cutB, (Dk + pd.Timedelta(hours=21, minutes=59)).tz_localize("UTC")); lag_dirs.append(d2)
        r2 = leg_xau.compute(d2)
        rows2 = r2["rows"]
        exp2 = [r for r in rows if r["date"] <= str(cutB.date())]
        back = [r for r in rows if str(cutB.date()) < r["date"] <= str(Dk.date())]
        print(f"lag scenario B (deferral): 5m through {Dk.date()}, daily through {cutB.date()}; kept trade {Dk.date()} "
              f"{xau[-1]['side']} {xau[-1]['note']} deferred; {len(back)} row(s) between reappear with restored daily data")
        check(rows2 == exp2 and not any(r["date"] > str(cutB.date()) for r in rows2),
              f"lag B: rows == full-run rows dated <= {cutB.date()}, kept trade {Dk.date()} absent")
        check(str(Dk.date()) in r2["deferred"] and all(r in rows for r in back) and len(back) >= 1,
              f"lag B: {Dk.date()} listed as deferred; the {len(back)} deferred row(s) are exactly the full-run rows")
        # scenario C: the real data/forward pull, daily truncated 3 joint sessions behind the 5m frame
        fwd = os.path.join(DATA, "forward")
        if glob.glob(os.path.join(fwd, "xauusd_5m_*.json")) and glob.glob(os.path.join(fwd, "xauusd_daily_*.json")) \
                and glob.glob(os.path.join(fwd, "audusd_daily_*.json")):
            rr = leg_xau.compute(fwd)
            last5 = pd.Timestamp(rr["g5"].index.max().date())
            check(rr["gate_end"] >= last5 and leg_xau.corr_gate(rr["gd"], rr["ad"], extend_to=last5).equals(rr["C"]),
                  f"real pull: same-time daily pull covers the 5m frame (gate through {rr['gate_end'].date()}, "
                  f"5m through {last5.date()}), extension would be a no-op, {len(rr['deferred'])} deferred")
            jr = rr["gd"].index.intersection(rr["ad"].index)
            cutC = jr[jr.searchsorted(last5, side="left") - 3]
            d3 = tempfile.mkdtemp(prefix="leg_xau_real_lag_", dir=base); lag_dirs.append(d3)
            for f in glob.glob(os.path.join(fwd, "xauusd_5m_*.json")) + glob.glob(os.path.join(fwd, "audusd_5m_*.json")):
                os.symlink(f, os.path.join(d3, os.path.basename(f)))
            for pat in ("xauusd_daily_*.json", "audusd_daily_*.json"):
                b = leg_xau.load_ibkr(fwd, pat)
                b = b[(b.index + leg_xau.SESSION_ROLL).tz_convert(None).normalize() <= cutC]
                write_ibkr(os.path.join(d3, pat.replace("*", "lag")), b, 86400)
            r3 = leg_xau.compute(d3)
            late3 = r3["trades_all"][pd.to_datetime(r3["trades_all"].day).dt.normalize() > cutC] if len(r3["trades_all"]) else r3["trades_all"]
            st3 = leg_xau.status(d3)
            print(f"lag scenario C (real pull): daily through {cutC.date()}, 5m through {rr['g5'].index.max():%Y-%m-%d %H:%M}Z: "
                  f"{len(rr['trades_all'])} raw breakouts, full-run rows {len(rr['rows'])}, lagged rows {len(r3['rows'])}, "
                  f"deferred {r3['deferred']}")
            print("    status():\n        " + st3.replace("\n", "\n        "))
            check(r3["gate_end"] == cutC and r3["rows"] == [r for r in rr["rows"] if r["date"] <= str(cutC.date())]
                  and (late3.c.isna().all() if len(late3) else True)
                  and r3["deferred"] == sorted(str(d) for d in late3.day) and "DEFERRED" in st3,
                  f"lag C: rows restricted to <= {cutC.date()}, {len(late3)} later breakout(s) NaN-gated and listed as deferred")
        else:
            print("lag scenario C skipped: no real data/forward pull present")
    finally:
        for d in lag_dirs + [tmp]:
            shutil.rmtree(d, ignore_errors=True)
    print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED'} ({time.time()-t0:.0f}s)")
    for m in fails:
        print("  - " + m)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
