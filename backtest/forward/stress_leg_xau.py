"""Forward-data robustness stress test for forward/leg_xau.py (synthetic IBKR files).

Builds a fully synthetic data_dir (gold 5m, gold daily, AUDUSD daily, AUDUSD 5m in the
IBKR price-history JSON schema of CONTRACT.md) with PLANTED sessions whose trades are
known by construction, computes the expected journal rows and the expected corr gate
independently of leg_xau, and then perturbs the files the way real forward pulls do:
overlapping weekly files, duplicate timestamps, revised bars in a later pull, missing
bars / holidays, a partial current day, weeks with no signal, weekend bars, daily bars
stamped 21:15Z / 22:00Z / 23:00Z of the previous calendar day, absent files, numbers as
strings, odd timestamp formats and degenerate files. Also checks the row schema.

Run:  python3 forward/stress_leg_xau.py [scratch_dir]      (from any cwd)
"""
import json, os, shutil, sys, tempfile, traceback, re
HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.dirname(HERE)
for p in (BT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np, pandas as pd
import leg_xau

FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


# ------------------------------------------------------------------ synthetic sessions
LEVEL0 = 4500.0
SCEN_CLOSE = dict(long_time=20.0, short_stop=15.0, none=5.0, late=30.0, flat=0.0)


def session_path(D, scen, level):
    """5m bars of gold session D (22:00Z D-1 .. 20:55Z D, UTC). Returns DataFrame OHLC.
    open=close=p, high=p+0.1, low=p-0.1 with p a step/ramp function of minutes since
    midnight D (m), so the 60m closes and the range are known exactly:
      opening range 01:30-02:25 alternates level / level+10 -> hi=level+10.1, lo=level-0.1, rng=10.2
      long_time : 03:30 bin ramps to level+15 (close > hi) -> long at level+15, fill 04:30, no stop
                  hit (p=level+12), time exit at 20:00Z open = level+20
      short_stop: 02:30 bin ramps to level-10 (close < lo) -> short at level-10, fill 03:30,
                  p jumps to level+15 at 06:00Z -> high level+15.1 >= stop level-10+20.4 -> stop at 06:00Z
      none      : p=level+5 all day (inside the range)
      late      : breakout only at 07:00Z (after the 08:00 London cutoff in summer) -> no trade
      flat      : p=level all day -> range hi==lo -> no session
    """
    D = pd.Timestamp(D)
    idx = pd.date_range(D - pd.Timedelta(hours=2), D + pd.Timedelta(hours=20, minutes=55), freq="5min", tz="UTC")
    m = ((idx - D.tz_localize("UTC")).total_seconds() // 60).astype(int).to_numpy()
    p = np.full(len(idx), level + 5.0)
    if scen == "flat":
        p[:] = level
    else:
        rng_mask = (m >= 90) & (m < 150)
        p[rng_mask] = np.where(((m[rng_mask] - 90) // 5) % 2 == 0, level, level + 10.0)
        if scen == "long_time":
            r = (m >= 210) & (m < 270)
            p[r] = level + 5.0 + 10.0 * ((m[r] - 210) / 55.0)          # close at 265 = level+15
            p[(m >= 270) & (m < 1200)] = level + 12.0
            p[m >= 1200] = level + 20.0
        elif scen == "short_stop":
            r = (m >= 150) & (m < 210)
            p[r] = level + 5.0 - 15.0 * ((m[r] - 150) / 55.0)          # close at 205 = level-10
            p[(m >= 210) & (m < 360)] = level - 10.0
            p[m >= 360] = level + 15.0
        elif scen == "late":
            p[m >= 420] = level + 30.0
        elif scen == "none":
            pass
        else:
            raise ValueError(scen)
    return pd.DataFrame({"open": p, "high": p + 0.1, "low": p - 0.1, "close": p}, index=idx)


def expected_trade(D, scen, level):
    """The trade trades.generate must find on a planted day, by construction."""
    D = pd.Timestamp(D, tz="UTC")
    rng = 10.2
    if scen == "long_time":
        entry = level + 15.0
        return dict(day=D, side=1, entry=entry, stop=entry - 2 * rng, exit=level + 20.0, reason="time", rng=rng,
                    t_fill=D + pd.Timedelta(hours=4, minutes=30), t_out=D + pd.Timedelta(hours=20))
    if scen == "short_stop":
        entry = level - 10.0
        return dict(day=D, side=-1, entry=entry, stop=entry + 2 * rng, exit=entry + 2 * rng, reason="stop", rng=rng,
                    t_fill=D + pd.Timedelta(hours=3, minutes=30), t_out=D + pd.Timedelta(hours=6))
    return None


def aud5_price(idx):
    """Deterministic AUDUSD 5m path (open=close=p) over a UTC DatetimeIndex."""
    x = (idx.asi8 // 10**9 // 300).astype(float)
    p = 0.65 + 0.004 * np.sin(x / 37.0) + 0.002 * np.cos(x / 101.0)
    return pd.DataFrame({"open": p, "high": p + 1e-5, "low": p - 1e-5, "close": p}, index=idx)


def build(plan, daily_start="2026-06-01", gate="open", winter=False, holiday00=None):
    """plan: ordered dict session date -> scenario (weekdays only).
    Returns dict with the synthetic frames and the expected rows / gate.
    gate='open'  -> AUD daily log-returns = -gold log-returns (corr -1, every day passes)
    gate='closed'-> AUD daily log-returns = +gold log-returns (corr +1, nothing passes)
    winter=True  -> daily bars start 23:00Z / 22:15Z instead of 22:00Z / 21:15Z
    holiday00    -> a session date whose daily bars start at 00:00Z of the same date"""
    days = list(plan)
    levels = {d: LEVEL0 + 3.0 * i + (7.0 if i % 3 == 0 else 0.0) for i, d in enumerate(days)}
    g5 = pd.concat([session_path(d, s, levels[d]) for d, s in plan.items()]).sort_index()

    # daily gold: random-walk history before the 5m span, session closes inside it
    pre = pd.bdate_range(daily_start, pd.Timestamp(days[0]) - pd.Timedelta(days=1))
    rs = np.random.RandomState(7)
    hist = LEVEL0 * np.exp(np.cumsum(rs.normal(0, 0.006, len(pre))))
    hist = hist * (LEVEL0 / hist[-1])
    gd = pd.Series(list(hist) + [levels[d] + SCEN_CLOSE[s] for d, s in plan.items()],
                   index=pd.DatetimeIndex(list(pre) + [pd.Timestamp(d) for d in days]))
    rg = np.log(gd).diff().fillna(0.0)
    sign = -1.0 if gate == "open" else 1.0
    ad = pd.Series(0.65 * np.exp(np.cumsum(sign * rg.to_numpy())), index=gd.index)

    # IBKR daily bars: start at 22:00Z/21:15Z (23:00Z/22:15Z winter) of the PREVIOUS calendar day
    gh, ah = ((23, 0), (22, 15)) if winter else ((22, 0), (21, 15))
    g_start = pd.DatetimeIndex([d - pd.Timedelta(days=1) + pd.Timedelta(hours=gh[0], minutes=gh[1]) for d in gd.index]).tz_localize("UTC")
    a_start = pd.DatetimeIndex([d - pd.Timedelta(days=1) + pd.Timedelta(hours=ah[0], minutes=ah[1]) for d in ad.index]).tz_localize("UTC")
    if holiday00 is not None:
        h = pd.Timestamp(holiday00)
        k = list(gd.index).index(h)
        g_start = g_start.delete(k).insert(k, h.tz_localize("UTC"))
        a_start = a_start.delete(k).insert(k, h.tz_localize("UTC"))
    gdd = pd.DataFrame({"open": gd.to_numpy(), "high": gd.to_numpy() + 1, "low": gd.to_numpy() - 1, "close": gd.to_numpy()}, index=g_start)
    add = pd.DataFrame({"open": ad.to_numpy(), "high": ad.to_numpy() + 1e-4, "low": ad.to_numpy() - 1e-4, "close": ad.to_numpy()}, index=a_start)

    # AUD 5m over the gold 5m span (Sunday 21:15Z .. Friday 20:55Z, every 5 min)
    a_idx = pd.date_range(g5.index.min() - pd.Timedelta(minutes=45), g5.index.max(), freq="5min", tz="UTC")
    a5 = aud5_price(a_idx)

    # expected corr gate (deployable.py lines 13-17 on the session-date-labelled series)
    j = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")], axis=1, join="inner").dropna()
    C = (j.g.rolling(20).corr(j.a).reindex(pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill().shift(1))

    rows, trades_exp = [], []
    for d, s in plan.items():
        tr = expected_trade(d, s, levels[d])
        if tr is None:
            continue
        c = C.get(pd.Timestamp(d), np.nan)
        tr["c"] = c
        trades_exp.append(tr)
        if pd.isna(c) or c > 0.5:
            continue
        side = "L" if tr["side"] == 1 else "S"
        note = f"{tr['reason']}|60m"
        rows.append(dict(date=str(pd.Timestamp(d).date()), side=side, src="auto", instr="XAU",
                         entry=round(tr["entry"], 2), stop=round(tr["stop"], 2), exit=round(tr["exit"], 2), note=note))
        a_in, a_out = float(a5.at[tr["t_fill"], "open"]), float(a5.at[tr["t_out"], "open"])
        e = tr["entry"] / a_in
        rows.append(dict(date=str(pd.Timestamp(d).date()), side=side, src="auto", instr="XAUAUD",
                         entry=round(e, 2), stop=round(e * (1 - tr["side"] * 2 * tr["rng"] / tr["entry"]), 2),
                         exit=round(tr["exit"] / a_out, 2), note="half|" + note))
    return dict(g5=g5, gdd=gdd, add=add, a5=a5, gd=gd, ad=ad, C=C, rows=rows, trades=trades_exp, levels=levels, plan=plan)


# ------------------------------------------------------------------ IBKR JSON writers
def iso(idx, fmt="%Y-%m-%dT%H:%M:%SZ"):
    return [t.strftime(fmt) for t in idx]


def write(path, df, step=300, conv=None, fmt="%Y-%m-%dT%H:%M:%SZ", extra=None):
    conv = conv or (lambda v: v)
    d = {"chart_step": step, "source": "MidPoint", "chart_start": iso(df.index[:1], fmt)[0] if len(df) else "",
         "chart_end": iso(df.index[-1:], fmt)[0] if len(df) else "", "expires": "2026-09-02T12:54:05Z",
         "time": iso(df.index, fmt),
         "open": [conv(v) for v in df.open.tolist()], "close": [conv(v) for v in df.close.tolist()],
         "high": [conv(v) for v in df.high.tolist()], "low": [conv(v) for v in df.low.tolist()]}
    if extra:
        d.update(extra)
    with open(path, "w") as fh:
        json.dump(d, fh)


def write_all(tmp, fx, g5=None, gdd=None, add=None, a5=None, which=("g5", "gdd", "add", "a5"), **kw):
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    if "g5" in which:
        write(os.path.join(tmp, "xauusd_5m_2026-09-02.json"), fx["g5"] if g5 is None else g5, 300, **kw)
    if "gdd" in which:
        write(os.path.join(tmp, "xauusd_daily_2026-09-02.json"), fx["gdd"] if gdd is None else gdd, 86400, **kw)
    if "add" in which:
        write(os.path.join(tmp, "audusd_daily_2026-09-02.json"), fx["add"] if add is None else add, 86400, **kw)
    if "a5" in which:
        write(os.path.join(tmp, "audusd_5m_2026-09-02.json"), fx["a5"] if a5 is None else a5, 300, **kw)


def same_rows(a, b):
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def diff_rows(a, b):
    return [(x, y) for x, y in zip(a, b) if x != y] + [("extra", r) for r in a[len(b):]] + [("missing", r) for r in b[len(a):]]


# ------------------------------------------------------------------------------ tests
def main():
    base = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()
    os.makedirs(base, exist_ok=True)
    root = tempfile.mkdtemp(prefix="stress_leg_xau_", dir=base)
    tmp = os.path.join(root, "d")
    try:
        # three weeks, 10-14 Aug (Mon-Fri), 17-21 Aug, 24-28 Aug 2026 (BST/EDT: cutoff 07:00Z, exit 20:00Z)
        plan = {"2026-08-10": "long_time", "2026-08-11": "none", "2026-08-12": "short_stop", "2026-08-13": "late",
                "2026-08-14": "flat", "2026-08-17": "short_stop", "2026-08-18": "long_time", "2026-08-19": "none",
                "2026-08-20": "none", "2026-08-21": "long_time", "2026-08-24": "none", "2026-08-25": "short_stop",
                "2026-08-26": "long_time", "2026-08-27": "none", "2026-08-28": "long_time"}
        fx = build(plan)
        E = fx["rows"]
        print(f"fixture: {len(fx['g5'])} gold 5m bars {fx['g5'].index.min()} .. {fx['g5'].index.max()}, "
              f"{len(fx['gdd'])} daily gold, {len(fx['add'])} daily AUD, {len(fx['a5'])} AUD 5m; "
              f"expected {len(E)} rows ({len(E)//2} trades); expected gate on trade days: "
              f"{[round(t['c'], 3) for t in fx['trades']]}")
        check(len(E) == 2 * sum(1 for s in plan.values() if s in ("long_time", "short_stop")) and len(E) == 16,
              "fixture: every planted trade day passes the (corr=-1) gate -> 8 XAU + 8 XAUAUD expected rows")

        # ---- T1 baseline ----------------------------------------------------------
        write_all(tmp, fx)
        R = leg_xau.rows(tmp)
        check(same_rows(R, E), f"T1 baseline: rows == expected by construction ({len(R)} rows)")
        if not same_rows(R, E):
            for x in diff_rows(R, E)[:6]:
                print("        ", x)
        res = leg_xau.compute(tmp)
        cs = {str(r.day): r.c for r in res["trades_all"].itertuples()}
        exp_c = {str(t["day"].date()): t["c"] for t in fx["trades"]}
        check(set(cs) == set(exp_c) and all(abs(cs[k] - exp_c[k]) < 1e-12 for k in cs),
              f"T1 gate: trades_all.c equals the independently computed lagged 20d corr on all {len(cs)} trade days")
        check(len(res["trades_all"]) == 8 and set(str(d) for d in res["trades_all"].day) == set(exp_c),
              "T1 trades.generate finds exactly the 8 planted trades (none on 'none'/'late'/'flat' days)")
        st = leg_xau.status(tmp)
        check(isinstance(st, str) and "8 raw breakout trades, 8 pass" in st and "complete" in st, "T1 status(): string, counts, last session complete")

        # ---- T14 schema (on the baseline rows) ----------------------------------------
        keys = ["date", "instr", "side", "entry", "stop", "exit", "note", "src"]
        check(all(set(r) == set(keys) for r in R), "schema: exact key set {date, instr, side, entry, stop, exit, note, src}")
        check(all(isinstance(r["date"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]) for r in R), "schema: date is 'YYYY-MM-DD' str")
        check(all(r["instr"] in ("XAU", "XAUAUD") and r["side"] in ("L", "S") and r["src"] == "auto" for r in R), "schema: instr/side/src values")
        check(all(type(r[k]) is float for r in R for k in ("entry", "stop", "exit")), "schema: entry/stop/exit are Python float (not numpy)")
        check(all(re.fullmatch(r"(time|stop)\|60m", r["note"]) for r in R if r["instr"] == "XAU")
              and all(re.fullmatch(r"half\|(time|stop)\|60m", r["note"]) for r in R if r["instr"] == "XAUAUD"), "schema: note format")
        check(all(R[i + 1]["instr"] == "XAUAUD" and R[i + 1]["date"] == R[i]["date"] and R[i + 1]["note"] == "half|" + R[i]["note"]
                  for i in range(0, len(R), 2) if R[i]["instr"] == "XAU"), "schema: XAUAUD row directly follows its XAU row")
        check(len({(r["date"], r["instr"], r["note"]) for r in R}) == len(R), "schema: dedup key (date, instr, note) unique")
        check(all(json.dumps(r) for r in R), "schema: rows JSON-serialisable")
        check(all(r["date"] == pd.Timestamp(r["date"]).tz_localize("Asia/Hong_Kong").strftime("%Y-%m-%d") for r in R)
              and all(r["date"] in plan for r in R), "schema: date is the HKT session date (== UTC date of the 01:30Z range bar)")

        # ---- T2 overlapping weekly files + full duplicate ------------------------------
        g5 = fx["g5"]
        write_all(tmp, fx, which=("gdd", "add", "a5"))
        weeks = [("2026-08-09", "2026-08-16"), ("2026-08-14", "2026-08-23"), ("2026-08-21", "2026-08-31")]   # overlapping
        for i, (a, b) in enumerate(weeks):
            write(os.path.join(tmp, f"xauusd_5m_2026-08-{16 + 7 * i:02d}.json"), g5.loc[a:b], 300)
        write(os.path.join(tmp, "xauusd_5m_2026-09-01_full.json"), g5, 300)
        for i, (a, b) in enumerate(weeks):
            write(os.path.join(tmp, f"audusd_5m_2026-08-{16 + 7 * i:02d}.json"), fx["a5"].loc[a:b], 300)
        gdd = fx["gdd"]
        write(os.path.join(tmp, "xauusd_daily_2026-07-01.json"), gdd.iloc[:40], 86400)
        write(os.path.join(tmp, "xauusd_daily_2026-08-01.json"), gdd.iloc[20:], 86400)
        write(os.path.join(tmp, "audusd_daily_2026-07-01.json"), fx["add"].iloc[:45], 86400)
        check(same_rows(leg_xau.rows(tmp), E), "T2 overlapping weekly files + duplicate full file + overlapping daily files -> same rows")
        lg = leg_xau.load_ibkr(tmp, "xauusd_5m_*.json")
        check(len(lg) == len(g5) and lg.index.equals(g5.index) and not lg.index.has_duplicates, "T2 loader: no duplicate timestamps, index identical")

        # ---- T3 revised bar in a later pull wins; older file loses -------------------------
        write_all(tmp, fx)
        d18 = pd.Timestamp("2026-08-18", tz="UTC")
        rev = g5.loc[d18 + pd.Timedelta(hours=19):d18 + pd.Timedelta(hours=20, minutes=55)].copy()
        rev.loc[d18 + pd.Timedelta(hours=20), "open"] = fx["levels"]["2026-08-18"] + 25.0        # exit print revised
        write(os.path.join(tmp, "xauusd_5m_2026-09-09.json"), rev, 300)                            # later pull
        old = rev.copy(); old.loc[d18 + pd.Timedelta(hours=20), "open"] = 1.0
        write(os.path.join(tmp, "xauusd_5m_2026-01-01_old.json"), old, 300)                        # earlier pull, must lose
        R3 = leg_xau.rows(tmp)
        x18 = [r for r in R3 if r["date"] == "2026-08-18" and r["instr"] == "XAU"]
        check(len(x18) == 1 and x18[0]["exit"] == round(fx["levels"]["2026-08-18"] + 25.0, 2)
              and same_rows([r for r in R3 if r["date"] != "2026-08-18"], [r for r in E if r["date"] != "2026-08-18"]),
              "T3 duplicate timestamp across pulls: the later-named file's bar wins, earlier loses, other rows unchanged")

        # ---- T4 duplicate timestamps inside one file -------------------------------------
        bad = g5.copy(); bad[["open", "high", "low", "close"]] = 1.0
        both = pd.concat([bad, g5])                       # garbage first, correct copy last
        write_all(tmp, fx, g5=both)
        check(same_rows(leg_xau.rows(tmp), E), "T4 duplicate timestamps inside a file: last occurrence wins, rows unchanged")

        # ---- T5 missing bars / holiday --------------------------------------------------
        hol = pd.Timestamp("2026-08-19", tz="UTC")           # a 'none' day -> remove the whole session + its daily bars
        g5h = g5[(g5.index < hol - pd.Timedelta(hours=2)) | (g5.index > hol + pd.Timedelta(hours=21))]
        rs = np.random.RandomState(1)
        none_days = [pd.Timestamp(d, tz="UTC") for d, s in plan.items() if s == "none"]
        drop = np.zeros(len(g5h), dtype=bool)
        for d in none_days:
            m = (g5h.index >= d) & (g5h.index < d + pd.Timedelta(days=1))
            drop |= m & (rs.rand(len(g5h)) < 0.3)
        g5h = g5h[~drop]
        gdh = fx["gdd"][fx["gdd"].index != hol - pd.Timedelta(hours=2)]
        adh = fx["add"][fx["add"].index != hol - pd.Timedelta(hours=2, minutes=45)]
        write_all(tmp, fx, g5=g5h, gdd=gdh, add=adh)
        check(same_rows(leg_xau.rows(tmp), E), f"T5 holiday (whole session + daily bars removed) and {int(drop.sum())} random 5m bars missing on no-signal days -> rows unchanged")
        # missing exit print at 20:00Z on a long_time day -> engine.price_at falls back to the last close within 30 min
        d21 = pd.Timestamp("2026-08-21", tz="UTC")
        g5m = g5[g5.index != d21 + pd.Timedelta(hours=20)]
        write_all(tmp, fx, g5=g5m)
        r21 = [r for r in leg_xau.rows(tmp) if r["date"] == "2026-08-21" and r["instr"] == "XAU"]
        check(len(r21) == 1 and r21[0]["exit"] == round(fx["levels"]["2026-08-21"] + 12.0, 2),
              "T5 missing 20:00Z exit bar: exit = last close within 30 min (trades.generate/engine.price_at rule), row still emitted")
        g5m = g5[(g5.index < d21 + pd.Timedelta(hours=19, minutes=25)) | (g5.index > d21 + pd.Timedelta(hours=20, minutes=30))]
        write_all(tmp, fx, g5=g5m)
        r21 = [r for r in leg_xau.rows(tmp) if r["date"] == "2026-08-21"]
        check(len(r21) == 0 and len(leg_xau.rows(tmp)) == len(E) - 2, "T5 >30 min gap around the exit print: that day's trade is dropped (no exit price), others intact")

        # ---- T6 partial current day ------------------------------------------------------
        last = pd.Timestamp("2026-08-28", tz="UTC")           # long_time day
        for cut, want, lab in ((last + pd.Timedelta(hours=11, minutes=50), 0, "11:50Z (trade open, exit at 20:00Z not covered)"),
                               (last + pd.Timedelta(hours=20), 2, "20:00Z (exit bar is the last bar)"),
                               (last + pd.Timedelta(hours=19, minutes=55), 2, "19:55Z (exit bar missing, last close within 30 min -> emitted with fallback price)"),
                               (last + pd.Timedelta(hours=2, minutes=10), 0, "02:10Z (range bar partial)")):
            g5p = g5[g5.index <= cut]
            write_all(tmp, fx, g5=g5p, a5=fx["a5"][fx["a5"].index <= cut])
            Rp = leg_xau.rows(tmp)
            n_last = sum(1 for r in Rp if r["date"] == "2026-08-28")
            others_ok = same_rows([r for r in Rp if r["date"] != "2026-08-28"], [r for r in E if r["date"] != "2026-08-28"])
            check(n_last == want and others_ok, f"T6 frame truncated at {lab}: {n_last} rows for the partial day (want {want}), earlier rows intact")
            if cut.hour < 19:
                check("INCOMPLETE" in leg_xau.status(tmp), "T6 status() flags the partial session INCOMPLETE")
        d25 = pd.Timestamp("2026-08-25", tz="UTC")           # short_stop day, stop hit at 06:00Z
        for cut, want, lab in ((d25 + pd.Timedelta(hours=6, minutes=30), 2, "06:30Z after the 06:00Z stop bar"),
                               (d25 + pd.Timedelta(hours=6), 2, "06:00Z, the stop bar itself is the last bar"),
                               (d25 + pd.Timedelta(hours=5, minutes=50), 0, "05:50Z before the stop")):
            g5p = g5[g5.index <= cut]
            write_all(tmp, fx, g5=g5p, a5=fx["a5"][fx["a5"].index <= cut])
            Rp = leg_xau.rows(tmp)
            n25 = [r for r in Rp if r["date"] == "2026-08-25"]
            check(len(n25) == want and (want == 0 or n25[0]["note"] == "stop|60m") and (want == 0 or n25[0] == [r for r in E if r["date"] == "2026-08-25"][0]),
                  f"T6 short_stop day truncated at {lab}: {len(n25)} rows (want {want})")
        # a trailing PARTIAL 5m bar in an early pull, superseded by the complete bar in the next pull
        p1 = g5[g5.index <= d25 + pd.Timedelta(hours=6)].copy()
        p1.loc[d25 + pd.Timedelta(hours=6), ["open", "high", "close"]] = fx["levels"]["2026-08-25"] - 10.0   # bar not yet fully formed
        write_all(tmp, fx)
        write(os.path.join(tmp, "xauusd_5m_2026-08-25.json"), p1, 300)       # earlier pull name
        check(same_rows(leg_xau.rows(tmp), E), "T6 partial trailing bar in an earlier pull is superseded by the later pull's complete bar")

        # ---- T7 weeks with no signal ------------------------------------------------------
        for scen, lab in (("none", "every day inside the range"), ("flat", "every day flat (hi==lo)"), ("late", "breakouts only after the London cutoff")):
            fxn = build({d: scen for d in plan})
            write_all(tmp, fxn)
            Rn = leg_xau.rows(tmp)
            check(Rn == [], f"T7 {lab}: rows() == [] ({type(Rn).__name__})")
            check(isinstance(leg_xau.status(tmp), str), f"T7 {lab}: status() is a str")
        fxc = build(plan, gate="closed")
        write_all(tmp, fxc)
        check(leg_xau.rows(tmp) == [] and len(leg_xau.compute(tmp)["trades_all"]) == 8, "T7 corr gate CLOSED (corr=+1): 8 raw trades, rows() == []")
        write_all(tmp, fx, gdd=fx["gdd"].iloc[-3:], add=fx["add"].iloc[-3:])
        check(leg_xau.rows(tmp) == [] and "n/a" in leg_xau.status(tmp), "T7 fewer than 20 joint daily obs: corr NaN -> rows() == [], status says n/a")

        # ---- T8 weekend bars ---------------------------------------------------------------
        sat = pd.Timestamp("2026-08-15", tz="UTC")
        satbars = pd.DataFrame({"open": LEVEL0, "high": LEVEL0, "low": LEVEL0, "close": LEVEL0},
                               index=pd.date_range(sat, sat + pd.Timedelta(hours=23, minutes=55), freq="5min", tz="UTC"))
        sun = pd.Timestamp("2026-08-16", tz="UTC")
        sun_idx = pd.date_range(sun, sun + pd.Timedelta(hours=21, minutes=55), freq="5min", tz="UTC")
        sunbars = pd.DataFrame({"open": LEVEL0, "high": LEVEL0, "low": LEVEL0, "close": LEVEL0}, index=sun_idx)
        write_all(tmp, fx, g5=pd.concat([g5, satbars, sunbars]).sort_index())
        check(same_rows(leg_xau.rows(tmp), E), "T8 flat Saturday + Sunday-daytime bars: rows unchanged (flat range -> no session)")
        satmove = session_path("2026-08-15", "long_time", LEVEL0)                  # a full fake moving Saturday session
        write_all(tmp, fx, g5=pd.concat([g5, satmove[satmove.index >= sat]]).sort_index())
        R8 = leg_xau.rows(tmp)
        sat_rows = [r for r in R8 if r["date"] == "2026-08-15"]
        print(f"        moving Saturday session -> {len(sat_rows)} Saturday rows (trades.generate has no weekday filter; "
              f"IBKR gold has no Saturday bars, informational)")
        check(same_rows([r for r in R8 if r["date"] != "2026-08-15"], E), "T8 moving Saturday bars do not disturb the weekday rows")

        # ---- T9 daily bars stamped on the previous calendar day ---------------------------------
        for winter, lab in ((False, "22:00Z gold / 21:15Z AUD"), (True, "23:00Z gold / 22:15Z AUD (winter clock)")):
            fxw = build(plan, winter=winter, holiday00="2026-08-13")
            write_all(tmp, fxw)
            gdl = leg_xau.daily_close(leg_xau.load_ibkr(tmp, "xauusd_daily_*.json"))
            adl = leg_xau.daily_close(leg_xau.load_ibkr(tmp, "audusd_daily_*.json"))
            check(gdl.index.equals(fxw["gd"].index) and np.allclose(gdl.to_numpy(), fxw["gd"].to_numpy())
                  and adl.index.equals(fxw["ad"].index) and np.allclose(adl.to_numpy(), fxw["ad"].to_numpy()),
                  f"T9 daily bars starting {lab} of D-1 (+ one 00:00Z holiday session) are labelled session date D")
            check(same_rows(leg_xau.rows(tmp), fxw["rows"]), f"T9 rows with {lab} daily bars == expected")
        # daily files lag the 5m frame: deployable.py line 17/23 - the gate index ends at the
        # last joint daily label, later sessions are NaN and dropped (deferred), never ffilled
        write_all(tmp, fx, gdd=fx["gdd"].iloc[:-1], add=fx["add"].iloc[:-1])       # no daily bar for the last session
        res9 = leg_xau.compute(tmp)
        c28 = res9["trades_all"].set_index("day").c.loc[pd.Timestamp("2026-08-28").date()]
        check(pd.isna(c28) and res9["gate_end"] == pd.Timestamp("2026-08-27") and res9["deferred"] == ["2026-08-28"]
              and same_rows(res9["rows"], [r for r in E if r["date"] != "2026-08-28"]),
              "T9 daily files end at D-1: session D gate NaN, its rows absent (deferred), all other rows unchanged")
        write_all(tmp, fx, gdd=fx["gdd"].iloc[:-3], add=fx["add"].iloc[:-3])       # daily stale by 3 sessions
        res9 = leg_xau.compute(tmp)
        st9 = leg_xau.status(tmp)
        late = res9["trades_all"][pd.to_datetime(res9["trades_all"].day) > pd.Timestamp("2026-08-25")]
        print(f"        daily stale by 3 sessions: gate defined through {res9['gate_end'].date()}, breakouts after it "
              f"{sorted(str(d) for d in late.day)} -> gate {late.c.tolist()}; deferred {res9['deferred']}; status: "
              f"{[l for l in st9.splitlines() if 'BEHIND' in l][0]}")
        check(res9["gate_end"] == pd.Timestamp("2026-08-25") and late.c.isna().all()
              and res9["deferred"] == sorted(str(d) for d in late.day) and "DEFERRED" in st9
              and same_rows(res9["rows"], [r for r in E if r["date"] <= "2026-08-25"]),
              "T9 stale daily data: sessions after the last joint daily label are dropped (NaN) and listed as deferred, earlier rows unchanged")
        write_all(tmp, fx)                                                          # daily restored -> deferred rows appear
        check(same_rows(leg_xau.rows(tmp), E), "T9 daily data restored: the deferred rows reappear, rows == expected (self-healing)")

        # ---- T10 absent files ---------------------------------------------------------------
        check(leg_xau.rows(os.path.join(root, "does_not_exist")) == [], "T10 data_dir missing: rows() == []")
        check("no xauusd_5m" in leg_xau.status(os.path.join(root, "does_not_exist")), "T10 data_dir missing: status() str")
        write_all(tmp, fx, which=())
        check(leg_xau.rows(tmp) == [], "T10 empty dir: []")
        write_all(tmp, fx, which=("g5",))
        check(leg_xau.rows(tmp) == [] and "MISSING daily" in leg_xau.status(tmp), "T10 only 5m gold: [] and status says daily MISSING")
        write_all(tmp, fx, which=("g5", "gdd"))
        check(leg_xau.rows(tmp) == [], "T10 no AUD daily: []")
        write_all(tmp, fx, which=("g5", "add"))
        check(leg_xau.rows(tmp) == [], "T10 no gold daily: []")
        write_all(tmp, fx, which=("g5", "gdd", "add"))
        R10 = leg_xau.rows(tmp)
        check(same_rows(R10, [r for r in E if r["instr"] == "XAU"]) and "not converted" in leg_xau.status(tmp),
              "T10 no AUD 5m: XAU rows only, XAUAUD skipped and reported by status()")
        write_all(tmp, fx, which=("gdd", "add", "a5"))
        check(leg_xau.rows(tmp) == [], "T10 no gold 5m: []")

        # ---- T11 numbers as strings / ints / None ---------------------------------------------
        write_all(tmp, fx, conv=str)
        check(same_rows(leg_xau.rows(tmp), E), "T11 every price serialised as a string -> same rows")
        write_all(tmp, fx, conv=lambda v: int(v) if float(v).is_integer() else v)
        check(same_rows(leg_xau.rows(tmp), E), "T11 integral prices serialised as int -> same rows")
        g5n = g5.copy().astype(object)
        k = g5n.index.get_loc(pd.Timestamp("2026-08-19 05:00", tz="UTC"))
        g5n.iloc[k, 0] = None; g5n.iloc[k + 1, 3] = "n/a"; g5n.iloc[k + 2, 1] = "NaN"
        write_all(tmp, fx, g5=g5n)
        check(same_rows(leg_xau.rows(tmp), E) and len(leg_xau.load_ibkr(tmp, "xauusd_5m_*.json")) == len(g5) - 3,
              "T11 None / 'n/a' / 'NaN' prices: those bars dropped, no crash, rows unchanged")
        gz = fx["gdd"].copy(); gz.iloc[5, :] = 0.0
        write_all(tmp, fx, gdd=gz)
        try:
            Rz = leg_xau.rows(tmp)
            check(True, f"T11 a zero daily close (log -> -inf): no crash, {len(Rz)} rows (corr windows touching it are NaN/inf -> those days dropped)")
        except Exception as e:
            check(False, f"T11 zero daily close crashes: {e!r}")

        # ---- T12 timestamp formats -------------------------------------------------------------
        write_all(tmp, fx, fmt="%Y-%m-%dT%H:%M:%S+00:00")
        check(same_rows(leg_xau.rows(tmp), E), "T12 '+00:00' offset instead of 'Z' -> same rows")
        write_all(tmp, fx, fmt="%Y-%m-%dT%H:%M:%S")
        check(same_rows(leg_xau.rows(tmp), E), "T12 naive ISO timestamps (assumed UTC) -> same rows")
        write_all(tmp, fx, fmt="%Y-%m-%d %H:%M:%S")
        check(same_rows(leg_xau.rows(tmp), E), "T12 'YYYY-MM-DD HH:MM:SS' -> same rows")
        write_all(tmp, fx, g5=g5.iloc[::-1])
        check(same_rows(leg_xau.rows(tmp), E), "T12 time array in reverse order -> same rows")
        write_all(tmp, fx)
        mix = g5.loc["2026-08-24":]
        write(os.path.join(tmp, "xauusd_5m_2026-09-02.json"), g5.loc[:"2026-08-23"], 300)
        write(os.path.join(tmp, "xauusd_5m_2026-09-03.json"), mix, 300, fmt="%Y-%m-%dT%H:%M:%S+00:00")
        try:
            check(same_rows(leg_xau.rows(tmp), E), "T12 'Z' in one file and '+00:00' in another -> same rows")
        except Exception as e:
            check(False, f"T12 mixed timestamp formats across files crash: {e!r}")
        d = json.load(open(os.path.join(tmp, "xauusd_5m_2026-09-02.json")))
        d["time"][0] = d["time"][0].replace("Z", "+00:00")
        json.dump(d, open(os.path.join(tmp, "xauusd_5m_2026-09-02.json"), "w"))
        try:
            check(same_rows(leg_xau.rows(tmp), E), "T12 'Z' and '+00:00' mixed inside one file -> same rows")
        except Exception as e:
            check(False, f"T12 mixed timestamp formats inside one file crash: {e!r}")

        # ---- T13 degenerate files --------------------------------------------------------------
        write_all(tmp, fx)
        for name, content, lab in (("xauusd_5m_2026-09-03.json", "{}", "empty object {}"),
                                   ("xauusd_5m_2026-09-04.json", '{"time": [], "open": [], "high": [], "low": [], "close": []}', "time: []"),
                                   ("xauusd_5m_2026-09-05.json", '{"error": "rate limited"}', "error object"),
                                   ("xauusd_daily_2026-09-05.json", '{"error": "rate limited"}', "error object (daily)")):
            with open(os.path.join(tmp, name), "w") as fh:
                fh.write(content)
            try:
                check(same_rows(leg_xau.rows(tmp), E), f"T13 extra file {lab}: ignored")
            except Exception as e:
                check(False, f"T13 extra file {lab} crashes: {e!r}")
            os.remove(os.path.join(tmp, name))
        for name, content, lab in (("xauusd_5m_2026-09-03.json", "", "0-byte file"),
                                   ("xauusd_5m_2026-09-03.json", '{"time": ["2026-08-28T2', "truncated JSON"),
                                   ("xauusd_5m_2026-09-03.json", json.dumps({"time": ["2026-08-28T21:00:00Z", "2026-08-28T21:05:00Z"], "open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]}), "time/price arrays of different length"),
                                   ("xauusd_5m_2026-09-03.json", json.dumps({"time": ["2026-08-28T21:00:00Z"], "open": [1.0], "high": [1.0], "low": [1.0]}), "missing 'close' key"),
                                   ("xauusd_5m_2026-09-03.json", json.dumps({"time": ["garbage"], "open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]}), "unparseable timestamp")):
            with open(os.path.join(tmp, name), "w") as fh:
                fh.write(content)
            try:
                Rd = leg_xau.rows(tmp)
                print(f"        degenerate file ({lab}): no exception, {len(Rd)} rows ({'same' if same_rows(Rd, E) else 'DIFFERENT'})")
            except Exception as e:
                print(f"        degenerate file ({lab}): raises {type(e).__name__}: {str(e)[:80]}")
            os.remove(os.path.join(tmp, name))

        # ---- T15 AUD 5m gaps around t_fill / t_out ----------------------------------------------
        a5 = fx["a5"]
        d26 = pd.Timestamp("2026-08-26", tz="UTC")     # long_time: t_fill 04:30Z, t_out 20:00Z
        a_gap = a5[(a5.index < d26 + pd.Timedelta(hours=19, minutes=30)) | (a5.index > d26 + pd.Timedelta(hours=20, minutes=30))]
        write_all(tmp, fx, a5=a_gap)
        r26 = [r for r in leg_xau.rows(tmp) if r["date"] == "2026-08-26" and r["instr"] == "XAUAUD"]
        a_last = float(a5.loc[:d26 + pd.Timedelta(hours=19, minutes=25)].iloc[-1]["close"])
        exp_exit = round((fx["levels"]["2026-08-26"] + 20.0) / a_last, 2)
        check(len(r26) == 1 and r26[0]["exit"] == exp_exit, "T15 AUD 5m gap of 60 min around t_out: exit converted at the last AUD close before t_out (within 120 min)")
        a_gap = a5[(a5.index < d26 + pd.Timedelta(hours=17)) | (a5.index > d26 + pd.Timedelta(hours=20, minutes=30))]
        write_all(tmp, fx, a5=a_gap)
        R15 = leg_xau.rows(tmp)
        check(sum(1 for r in R15 if r["date"] == "2026-08-26") == 1 and len(R15) == len(E) - 1 and "2026-08-26" in leg_xau.status(tmp),
              "T15 AUD 5m gap > 120 min before t_out: XAU row kept, XAUAUD row skipped and named in status()")

        # ---- T16 the real forward pull (read-only) ----------------------------------------------
        real = os.path.join(BT, "data", "forward")
        if os.path.isdir(real):
            Rr = leg_xau.rows(real)
            check(isinstance(Rr, list) and all(set(r) == set(keys) for r in Rr) and all(type(r[k]) is float for r in Rr for k in ("entry", "stop", "exit")),
                  f"T16 real data/forward: {len(Rr)} rows, contract schema")
    except Exception:
        traceback.print_exc()
        FAILS.append("exception: " + traceback.format_exc().splitlines()[-1])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(f"\n{N[0]} checks, {len(FAILS)} failed")
    for m in FAILS:
        print("  - " + m)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
