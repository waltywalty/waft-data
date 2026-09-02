"""Verification of forward/leg_d7.py against the archived backtest (CONTRACT.md, D7 leg).

Run: cd backtest && python3 forward/test_leg_d7.py        (exit 0 only if every MUST passes)

What is checked:

  1. The archive's daily frame is rebuilt EXACTLY as run_r28b_d7.py does it
     (index_data.load("SPX").resample("1D").agg(...).dropna(); note this buckets the 5m
     CFD feed by UTC calendar day, Sunday-evening sessions included), written as IBKR-
     schema daily JSON (two overlapping spx_daily_*.json pulls, 13:30 UTC bar start) into
     a temp data_dir, and leg_d7 is run on it with start=None (the whole 2005-2025
     archive predates the paper stream, so the default stream-start filter would --
     correctly -- return nothing; sections 1-6 verify the MECHANICS, section 7 the
     filter).  The loader must give back the same 6517 closes.
  2. Trade-for-trade reference: run_r28b_d7.py's own `def d7_trades` source is located by
     text markers and exec'd unmodified (the module cannot be imported: it runs every
     market at import time and rewrites results/r28b_d7.json).  Exit dates, entries, exits
     and bar counts must be identical.
  3. Archived summaries.  results/r28b_d7.json holds NO trade list, only per-market
     summaries; every scalar of SPX_cfd (cost 0.6) and SPX_fut_ES (cost 0.35) -- n, win,
     avg_win, avg_loss, payoff, avg_hold_bars, worst_trade_pct, worst_mae_pct,
     med_mae_pct, strategy.final, strategy.exposure -- is recomputed from the leg rows
     (cost applied here only) and must agree to float precision.  Likewise
     results/r28_daily.json[D7_SPX] (n, pf, win, exp, t) and results/r28_d7_null.json
     [SPX] (n, real = total net points).
  4. The same leg code on NDX (data/NDX_5m.csv, same resample) must reproduce
     r28b_d7.json NDX_cfd / NDX_fut_NQ and r28_daily.json D7_NDX the same way.
  5. Warm-up: 199 and 200 bars -> no rows and status 'insufficient history'; 201 bars ->
     evaluated (the frozen loop starts at bar index 200).
  6. Forward-only guard: with `now` mid-session on the last exit day the last row must be
     withheld and status must say so; after the session end it must be back; the guard
     must be a no-op on the finished archive.
  7. Paper-trial scope (STREAM_START = 2026-08-27, the ledger's Round 28b registration):
     the default rows() on the archive is []; on the archive SHIFTED in time so that
     known trades straddle the boundary, a trade entered before and exited after the
     stream start is NOT journalled, one entered exactly on the start date IS, the
     journalled trades are identical to the full-history run (the state machine is not
     restarted at the boundary), an open position entered before the start is flagged in
     status() and never produces a row, one entered after it is reported normally.
  8. Informational (not MUST): the same rule on weekday-only closes (what the forward
     RTH feed will actually deliver), and rows()/status() on the live data/forward dir.
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
sys.path.insert(0, HERE)
sys.path.insert(0, BT)
os.chdir(BT)
import index_data  # noqa: E402
import leg_d7  # noqa: E402

R28B = os.path.join(BT, "results", "r28b_d7.json")
R28D = os.path.join(BT, "results", "r28_daily.json")
R28N = os.path.join(BT, "results", "r28_d7_null.json")
RUN = os.path.join(BT, "run_r28b_d7.py")
LEDGER = os.path.join(BT, "reference", "goal_ledger.md")
FORWARD = os.path.join(BT, "data", "forward")
SKIP_KEYS = {"OOS_sealed", "oos"}
FUTURE = "2040-01-01T00:00:00Z"      # `now` for shifted histories that run past today

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


# ------------------------------------------------------------------- archive helpers
def archive_daily(mkt):
    """run_r28b_d7.py lines 25-27 verbatim in effect."""
    b = index_data.load(mkt)
    return b.resample("1D").agg(open=("open", "first"), high=("high", "max"),
                                low=("low", "min"), close=("close", "last")).dropna()


def write_ibkr(d, path, hm="13:30:00"):
    """IBKR price-history schema: parallel arrays, ISO-8601 Z bar start = session date."""
    obj = dict(chart_step=86400, source="Last", delayed=900,
               chart_start=f"{d.index[0]:%Y-%m-%d}T00:00:00Z",
               chart_end=f"{d.index[-1]:%Y-%m-%d}T00:00:00Z",
               time=[f"{ts:%Y-%m-%d}T{hm}Z" for ts in d.index],
               open=[float(x) for x in d.open], high=[float(x) for x in d.high],
               low=[float(x) for x in d.low], close=[float(x) for x in d.close])
    with open(path, "w") as fh:
        json.dump(obj, fh)


def make_dir(root, name, d, split=True):
    td = os.path.join(root, name)
    os.makedirs(td, exist_ok=True)
    if split and len(d) > 4000:
        write_ibkr(d.iloc[:4000], os.path.join(td, "spx_daily_2000-01-01.json"))
        write_ibkr(d.iloc[3000:], os.path.join(td, "spx_daily_2020-01-01.json"))
    else:
        write_ibkr(d, os.path.join(td, "spx_daily_all.json"))
    return td


def ref_d7_trades():
    """exec run_r28b_d7.py's `def d7_trades` (up to `def curves`) as-is."""
    src = open(RUN).read()
    i = src.index("def d7_trades(")
    j = src.index("def curves(", i)
    ns = dict(pd=pd, np=np, index_data=index_data)
    exec(src[i:j], ns)
    return ns["d7_trades"]


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def summarize(trades, cost, nbars):
    """The r28b_d7.json per-market scalars, recomputed the way run_r28b_d7.py does."""
    t = pd.DataFrame(trades)
    ret = (t.exit - t.entry - cost) / t.entry
    pnl = t.exit - t.entry - cost
    p = pnl / t.entry * 100
    return dict(
        n=int(len(t)), win=float((ret > 0).mean()),
        avg_win=float(ret[ret > 0].mean() * 100), avg_loss=float(ret[ret <= 0].mean() * 100),
        payoff=float(-ret[ret > 0].mean() / ret[ret <= 0].mean()),
        avg_hold_bars=float(t.bars.mean()), worst_trade_pct=float(ret.min() * 100),
        worst_mae_pct=float(t.mae_pct.max() * 100), med_mae_pct=float(t.mae_pct.median() * 100),
        final=float(np.prod(1 + ret.values)), exposure=float(t.bars.sum() / nbars),
        pf=float(pnl[pnl > 0].sum() / max(-pnl[pnl <= 0].sum(), 1e-9)),
        exp=float(pnl.mean()), t=float(p.mean() / p.std() * np.sqrt(len(p))),
        real=float(pnl.sum()))


def cmp_scalar(label, mine, arch, exact=False):
    ok = (mine == arch) if exact else bool(np.isclose(mine, arch, rtol=1e-9, atol=1e-9))
    check(label, ok, f"leg {mine:.10g} vs archived {arch:.10g}")


def cmp_r28b(entry, mine, tag):
    cmp_scalar(f"{tag} n", mine["n"], entry["n"], exact=True)
    for k in ("win", "avg_win", "avg_loss", "payoff", "avg_hold_bars", "worst_trade_pct",
              "worst_mae_pct", "med_mae_pct"):
        cmp_scalar(f"{tag} {k}", mine[k], entry[k])
    cmp_scalar(f"{tag} strategy.final", mine["final"], entry["strategy"]["final"])
    cmp_scalar(f"{tag} strategy.exposure", mine["exposure"], entry["strategy"]["exposure"])


def rows_of(trades):
    """The contract rows leg_d7 builds from a trade list (same expression as compute())."""
    return [dict(date=t["date_out"].isoformat(), instr="D7", side="L", entry=t["entry"],
                 stop=t["entry"], exit=t["exit"], note=f"d7|{t['bars']} bars", src="auto")
            for t in trades]


def same_trades(a, b):
    """Trade lists equal on entry/exit dates, prices and bar counts."""
    ks = ("date_in", "date_out", "entry", "exit", "bars")
    return len(a) == len(b) and all(all(x[k] == y[k] for k in ks) for x, y in zip(a, b))


def fmt(m):
    return f"n={m['n']} win={m['win']:.4f} PF={m['pf']:.4f} hold={m['avg_hold_bars']:.3f}"


# ----------------------------------------------------------------------------- main
def main():
    print("leg_d7 verification (costs applied in this test only)\n")
    r28b = load_json(R28B)
    r28d = load_json(R28D)
    r28n = load_json(R28N)
    S = leg_d7.STREAM_START

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as root:
        # ---- 1. archive daily frame -> IBKR JSON -> leg (mechanics: start=None)
        d_spx = archive_daily("SPX")
        wd = d_spx.index.dayofweek
        print(f"1. archive daily frame (run_r28b_d7.py resample): {len(d_spx)} bars "
              f"{d_spx.index[0]:%Y-%m-%d} .. {d_spx.index[-1]:%Y-%m-%d}; weekday bars "
              f"{int((wd < 5).sum())}, Saturday {int((wd == 5).sum())}, Sunday {int((wd == 6).sum())} "
              f"(UTC calendar-day buckets of the CFD feed); leg run with start=None "
              f"(sections 1-6 = mechanics; the stream-start filter is section 7)")
        td = make_dir(root, "spx", d_spx)
        res = leg_d7.compute(td, start=None)
        dl = res["d"]
        check("loader: 2 overlapping pulls -> one frame with the archive's bar count",
              len(dl) == len(d_spx), f"{len(dl)} vs {len(d_spx)}")
        check("loader: closes identical to the archive resample",
              len(dl) == len(d_spx) and np.array_equal(dl.close.values, d_spx.close.values)
              and list(dl["date"]) == [ts.date() for ts in d_spx.index])
        check("loader: lows identical (MAE input)",
              len(dl) == len(d_spx) and np.array_equal(dl.low.values, d_spx.low.values))
        check("completeness guard is a no-op on the finished archive", not res["incomplete"])

        rs = res["rows"]
        R = pd.DataFrame(rs)
        print(f"   leg_d7.rows(start=None): {len(rs)} rows, {R.date.min()} .. {R.date.max()}")
        check("row schema", all(set(r) == {"date", "instr", "side", "entry", "stop", "exit",
                                           "note", "src"} for r in rs)
              and all(r["instr"] == "D7" and r["src"] == "auto" and r["side"] == "L"
                      and r["stop"] == r["entry"]
                      and isinstance(r["entry"], float) and isinstance(r["exit"], float)
                      and r["note"].startswith("d7|") and r["note"].endswith(" bars")
                      and r["note"][3:-5].isdigit() for r in rs))
        check("dedup key (date, instr, note) unique",
              not R.duplicated(subset=["date", "instr", "note"]).any())
        check("date is an ISO date (YYYY-MM-DD)",
              all(len(r["date"]) == 10 and pd.Timestamp(r["date"]) is not None for r in rs))
        check("rows are built from the `stream` subset (== all trades when start=None)",
              res["stream"] == res["trades"] and rs == rows_of(res["trades"]) and res["start"] is None)

        # ---- 2. trade-for-trade reference: exec'd d7_trades
        d7_trades = ref_d7_trades()
        tr_ref, d_ref = d7_trades("SPX", 0.6)
        print(f"\n2. exec'd run_r28b_d7.d7_trades('SPX', 0.6): n={len(tr_ref)} on {len(d_ref)} bars")
        check("trade count equals exec'd reference", len(rs) == len(tr_ref), f"{len(rs)} vs {len(tr_ref)}")
        same_n = len(rs) == len(tr_ref)
        if same_n:
            ref_dates = [ts.date().isoformat() for ts in tr_ref.t_out]
            check("exit dates identical", list(R.date) == ref_dates)
            check("entries identical", np.array_equal(R.entry.values, tr_ref.entry.values))
            check("exits identical", np.array_equal(R.exit.values, tr_ref.exit.values))
            check("bar counts identical",
                  [int(n[3:-5]) for n in R.note] == [int(b) for b in tr_ref.bars])
            mine_mae = np.array([t["mae_pct"] for t in res["trades"]])
            check("MAE identical", np.allclose(mine_mae, tr_ref.mae_pct.values, rtol=0, atol=1e-12))
            check("entry dates identical",
                  [t["date_in"].isoformat() for t in res["trades"]]
                  == [ts.date().isoformat() for ts in tr_ref.t_in])

        # ---- 3. archived summaries (r28b_d7.json holds no trade list)
        print(f"\n3. archived results/r28b_d7.json (per-market summaries only; keys {SKIP_KEYS} never read)")
        m06 = summarize(res["trades"], 0.6, len(dl))
        m035 = summarize(res["trades"], 0.35, len(dl))
        a_cfd, a_es = r28b["SPX_cfd"], r28b["SPX_fut_ES"]
        print(f"   SPX_cfd archived : n={a_cfd['n']} win={a_cfd['win']:.6f} hold={a_cfd['avg_hold_bars']:.6f} "
              f"worst={a_cfd['worst_trade_pct']:.4f}% worstMAE={a_cfd['worst_mae_pct']:.4f}% "
              f"final={a_cfd['strategy']['final']:.6f}x exposure={a_cfd['strategy']['exposure']:.6f}")
        print(f"   SPX_cfd leg      : n={m06['n']} win={m06['win']:.6f} hold={m06['avg_hold_bars']:.6f} "
              f"worst={m06['worst_trade_pct']:.4f}% worstMAE={m06['worst_mae_pct']:.4f}% "
              f"final={m06['final']:.6f}x exposure={m06['exposure']:.6f}")
        cmp_r28b(a_cfd, m06, "SPX_cfd(0.6)")
        cmp_r28b(a_es, m035, "SPX_fut_ES(0.35)")
        a_d = r28d["D7_SPX"]
        print(f"   r28_daily D7_SPX archived: n={a_d['n']} pf={a_d['pf']:.6f} win={a_d['win']:.6f} "
              f"exp={a_d['exp']:.6f} t={a_d['t']:.6f}; leg: {fmt(m06)} exp={m06['exp']:.6f} t={m06['t']:.6f}")
        cmp_scalar("r28_daily D7_SPX n", m06["n"], a_d["n"], exact=True)
        for k in ("pf", "win", "exp", "t"):
            cmp_scalar(f"r28_daily D7_SPX {k}", m06[k], a_d[k])
        a_n = r28n["SPX"]
        cmp_scalar("r28_d7_null SPX n", m06["n"], a_n["n"], exact=True)
        cmp_scalar("r28_d7_null SPX real (total net pts, cost 0.6)", m06["real"], a_n["real"])

        # ---- 4. same code on NDX
        ndx_csv = os.path.join(BT, "data", "NDX_5m.csv")
        if os.path.exists(ndx_csv):
            d_ndx = archive_daily("NDX")
            tdn = make_dir(root, "ndx", d_ndx)
            resn = leg_d7.compute(tdn, start=None)
            n20 = summarize(resn["trades"], 2.0, len(resn["d"]))
            n075 = summarize(resn["trades"], 0.75, len(resn["d"]))
            print(f"\n4. NDX daily written as spx_daily_*.json ({len(resn['d'])} bars): leg {fmt(n20)}")
            cmp_r28b(r28b["NDX_cfd"], n20, "NDX_cfd(2.0)")
            cmp_r28b(r28b["NDX_fut_NQ"], n075, "NDX_fut_NQ(0.75)")
            a_dn = r28d["D7_NDX"]
            cmp_scalar("r28_daily D7_NDX n", n20["n"], a_dn["n"], exact=True)
            for k in ("pf", "win", "exp", "t"):
                cmp_scalar(f"r28_daily D7_NDX {k}", n20[k], a_dn[k])
        else:
            print("\n4. data/NDX_5m.csv not present: NDX cross-check skipped")

        # ---- 5. warm-up
        print("\n5. warm-up")
        for n in (50, 199, 200):
            tdw = make_dir(root, f"warm{n}", d_spx.iloc[:n], split=False)
            st = leg_d7.status(tdw, start=None)
            check(f"{n} bars -> no rows and 'insufficient history'",
                  leg_d7.rows(tdw, start=None) == [] and "insufficient history" in st, st)
        tdw = make_dir(root, "warm201", d_spx.iloc[:201], split=False)
        st = leg_d7.status(tdw, start=None)
        check("201 bars -> evaluated (no 'insufficient history')",
              "insufficient history" not in st and ("flat" in st or "open since" in st), st)
        tde = os.path.join(root, "empty")
        os.makedirs(tde)
        check("empty dir -> no rows, 'insufficient history' (default and start=None)",
              leg_d7.rows(tde) == [] and leg_d7.rows(tde, start=None) == []
              and "insufficient history" in leg_d7.status(tde)
              and "insufficient history" in leg_d7.status(tde, start=None))
        # first bar the archive evaluates is index 200: a signal on bar 199 must NOT enter
        first_ref = tr_ref.t_in.min().date() if len(tr_ref) else None
        check("first entry is on/after the 201st archive bar",
              first_ref is not None and first_ref >= d_spx.index[200].date(),
              f"first entry {first_ref}, bar 201 = {d_spx.index[200].date()}")

        # ---- 6. forward-only guard
        print("\n6. completeness guard")
        last = rs[-1]
        d_last = pd.Timestamp(last["date"], tz="UTC")
        mid = d_last + pd.Timedelta(hours=15)          # 15:00 UTC, session runs 13:30-20:00 UTC
        end = d_last + pd.Timedelta(hours=20)
        # a data_dir cut at the last exit day, so that bar is the file's final bar
        cut = d_spx[d_spx.index <= d_last.tz_convert("UTC")]
        tdg = make_dir(root, "guard", cut, split=False)
        g_mid = leg_d7.rows(tdg, now=mid, start=None)
        g_end = leg_d7.rows(tdg, now=end, start=None)
        g_off = leg_d7.rows(tdg, now=mid, require_complete=False, start=None)
        st_mid = leg_d7.status(tdg, now=mid, start=None)
        check("mid-session pull: the exit row of the in-progress bar is withheld",
              all(r["date"] != last["date"] for r in g_mid) and g_mid == rs[:-1],
              f"{len(g_mid)} rows vs {len(rs)} on the finished file")
        check("status reports the withheld bar", "session in progress" in st_mid, st_mid)
        check("after the session end the row is emitted", g_end == rs)
        check("require_complete=False disables the guard", g_off == rs)
        check("unguarded rows == guarded rows on the finished archive",
              leg_d7.rows(td, require_complete=False, start=None) == rs)
        print(f"   status(now=mid-session): {st_mid}")
        print(f"   status(now=after close): {leg_d7.status(tdg, now=end, start=None)}")

        # ---- 7. paper-trial scope: the stream-start filter
        print(f"\n7. stream start (paper-trial scope): STREAM_START = {S}")
        check("STREAM_START is 2026-08-27 (goal_ledger.md Round 28b registration)",
              S == dt.date(2026, 8, 27))
        ledger = open(LEDGER).read() if os.path.exists(LEDGER) else ""
        check("goal_ledger.md registers the D7 paper stream on that date",
              re.search(r"Round 28b: Double Seven becomes paper stream 4 \(user decision, "
                        + S.isoformat().replace("-", r"\-") + r"\)", ledger) is not None)
        res_def = leg_d7.compute(td)
        check("default rows() on the 2005-2025 archive -> [] (nothing pre-registration is journalled)",
              leg_d7.rows(td) == [] and res_def["rows"] == [])
        check("default compute() still runs the state machine over the whole history",
              same_trades(res_def["trades"], res["trades"]) and res_def["stream"] == []
              and res_def["start"] == S)
        st_def = leg_d7.status(td)
        check("default status() reports the stream bookkeeping",
              f"stream since {S.isoformat()}: 0 closed trade(s) journalled, {len(rs)} earlier" in st_def,
              st_def)
        check("start='YYYY-MM-DD' string is accepted",
              leg_d7.rows(td, start=S.isoformat()) == [] and
              leg_d7.rows(td, start=rs[-1]["date"]) == [] and
              len(leg_d7.rows(td, start="2005-01-01")) == len(rs))

        # shifted archive: trade k (span >= 4 calendar days) lands 3 days BEFORE the stream
        # start so it straddles the boundary; everything after it is post-start data.
        trades_all = res["trades"]
        k = next(i for i in range(len(trades_all) - 60, len(trades_all))
                 if (trades_all[i]["date_out"] - trades_all[i]["date_in"]).days >= 4)
        tk = trades_all[k]
        shift = (S - tk["date_in"]).days - 3
        d_sh = d_spx.copy()
        d_sh.index = d_spx.index + pd.Timedelta(days=shift)
        tds = make_dir(root, "shifted", d_sh)
        full = leg_d7.compute(tds, now=FUTURE, start=None)
        flt = leg_d7.compute(tds, now=FUTURE)
        exp = [t for t in full["trades"] if t["date_in"] >= S]
        tk_sh = full["trades"][k]
        print(f"   archive shifted +{shift} d: trade {k} enters {tk_sh['date_in']} exits {tk_sh['date_out']} "
              f"(straddles {S}); {len(full['trades'])} trades in total, {len(exp)} entered on/after the start")
        check("shifted history: full-history run reproduces the archive's trades (shifted)",
              len(full["trades"]) == len(trades_all)
              and all(a["entry"] == b["entry"] and a["exit"] == b["exit"] and a["bars"] == b["bars"]
                      and (a["date_in"] - b["date_in"]).days == shift for a, b in zip(full["trades"], trades_all)))
        check("straddling trade (entered before, exited after the start) exists in the shifted history",
              tk_sh["date_in"] == S - dt.timedelta(days=3) and tk_sh["date_out"] >= S)
        check("straddling trade is NOT journalled",
              tk_sh["date_out"].isoformat() not in {r["date"] for r in flt["rows"]}
              and not any(t["date_in"] == tk_sh["date_in"] for t in flt["stream"]))
        check("every journalled trade was entered on/after the stream start; none missing",
              same_trades(flt["stream"], exp) and len(exp) > 0 and flt["rows"] == rows_of(exp),
              f"{len(flt['stream'])} journalled vs {len(exp)} expected")
        check("journalled trades identical to the full-history run (no restart at the boundary)",
              same_trades(flt["stream"], full["trades"][len(full["trades"]) - len(exp):]))
        check("pre-start trades in the shifted history == archive trades before the cut",
              len(full["trades"]) - len(exp) == k + 1)
        st_sh = leg_d7.status(tds, now=FUTURE)
        check("status on the shifted history reports journalled vs pre-stream counts",
              f"stream since {S.isoformat()}: {len(exp)} closed trade(s) journalled, {k + 1} earlier" in st_sh,
              st_sh)

        # a trade entered exactly ON the start date is journalled (inclusive boundary)
        j = k + 1
        tj = trades_all[j]
        shift_j = (S - tj["date_in"]).days
        d_sj = d_spx.copy()
        d_sj.index = d_spx.index + pd.Timedelta(days=shift_j)
        tdj = make_dir(root, "shifted_on", d_sj)
        rj = leg_d7.rows(tdj, now=FUTURE)
        fj = leg_d7.compute(tdj, now=FUTURE)
        check("trade entered exactly on STREAM_START is journalled (inclusive boundary)",
              fj["stream"] and fj["stream"][0]["date_in"] == S and fj["stream"][0]["entry"] == tj["entry"]
              and rj[0]["entry"] == tj["entry"] and rj[0]["note"] == f"d7|{tj['bars']} bars"
              and len(rj) == len(trades_all) - j,
              f"first journalled entry {fj['stream'][0]['date_in'] if fj['stream'] else None}, "
              f"{len(rj)} rows vs {len(trades_all) - j} expected")
        check("the trade before it (entered one session earlier) is not",
              not any(t["date_in"] < S for t in fj["stream"]) and len(fj["trades"]) - len(fj["stream"]) == j)

        # open position entered BEFORE the start: cut the shifted history inside trade k
        pre_cut = d_sh[[ts.date() < S for ts in d_sh.index]]
        tdp = make_dir(root, "open_pre", pre_cut)
        rp = leg_d7.compute(tdp, now=FUTURE)
        stp = leg_d7.status(tdp, now=FUTURE)
        check("open position entered before the start: no rows, pos reported, not in stream",
              rp["rows"] == [] and rp["pos"] is not None and not rp["pos_in_stream"]
              and rp["d"]["date"].iloc[rp["pos"][1]] == tk_sh["date_in"])
        check("status flags the pre-stream open position",
              "open since" in stp and "entered before the stream start" in stp
              and "will not be journalled" in stp, stp)
        # ... and once that trade closes it still does not produce a row
        post_cut = d_sh[[ts.date() <= tk_sh["date_out"] for ts in d_sh.index]]
        tdq = make_dir(root, "closed_pre", post_cut)
        check("after the pre-stream position closes: still no rows (its exit is not forward evidence)",
              leg_d7.rows(tdq, now=FUTURE) == [] and leg_d7.compute(tdq, now=FUTURE)["pos"] is None
              and len(leg_d7.compute(tdq, now=FUTURE, start=None)["rows"]) == k + 1)

        # open position entered AFTER the start: cut inside the longest post-start trade
        tm = max(exp, key=lambda t: t["bars"])
        in_cut = d_sh[[ts.date() < tm["date_out"] for ts in d_sh.index]]
        tdi = make_dir(root, "open_post", in_cut)
        ri = leg_d7.compute(tdi, now=FUTURE)
        sti = leg_d7.status(tdi, now=FUTURE)
        check("open position entered after the start: reported as in-stream",
              ri["pos"] is not None and ri["pos_in_stream"]
              and ri["d"]["date"].iloc[ri["pos"][1]] == tm["date_in"]
              and f"open since {tm['date_in'].isoformat()}" in sti
              and "entered before the stream start" not in sti, sti)
        check("rows before that open trade == the journalled trades that closed before it",
              ri["rows"] == rows_of([t for t in exp if t["date_out"] < tm["date_in"]]))
        # the completeness guard and the stream filter compose
        tm_end = pd.Timestamp(tm["date_out"], tz="UTC") + pd.Timedelta(hours=20)
        tm_mid = pd.Timestamp(tm["date_out"], tz="UTC") + pd.Timedelta(hours=15)
        upto = d_sh[[ts.date() <= tm["date_out"] for ts in d_sh.index]]
        tdu = make_dir(root, "guard_stream", upto)
        check("guard + stream filter: the in-stream exit is withheld mid-session, emitted after",
              [r["date"] for r in leg_d7.rows(tdu, now=tm_mid)] == [r["date"] for r in ri["rows"]]
              and leg_d7.rows(tdu, now=tm_end)[-1]["date"] == tm["date_out"].isoformat())
        # module-level switch (used by stress_leg_d7.py)
        saved = leg_d7.STREAM_START
        try:
            leg_d7.STREAM_START = None
            check("STREAM_START = None disables the filter for default calls",
                  leg_d7.rows(td) == rs and "no stream-start filter" in leg_d7.status(td))
        finally:
            leg_d7.STREAM_START = saved
        check("STREAM_START restored", leg_d7.rows(td) == [])
        n_def = len(leg_d7.rows(td))

        # ---- 8. informational
        print("\n8. informational (no MUST)")
        d_wk = d_spx[d_spx.index.dayofweek < 5]
        tdk = make_dir(root, "weekday", d_wk)
        resk = leg_d7.compute(tdk, start=None)
        mk = summarize(resk["trades"], 0.6, len(resk["d"]))
        print(f"   weekday-only closes ({len(resk['d'])} bars, Sat/Sun CFD buckets removed; what the "
              f"RTH forward feed delivers): {fmt(mk)} final={mk['final']:.4f}x exposure={mk['exposure']:.4f}")
        print(f"   archive (Sunday buckets included)                          : {fmt(m06)} "
              f"final={m06['final']:.4f}x exposure={m06['exposure']:.4f}")
        if os.path.isdir(FORWARD):
            try:
                fr = leg_d7.rows(FORWARD)
                fa = leg_d7.compute(FORWARD, start=None)
                fs = leg_d7.status(FORWARD)
                print(f"   live data/forward: {len(fr)} journalled rows (default); state machine found "
                      f"{len(fa['trades'])} closed trades in the pull, "
                      f"{sum(1 for t in fa['trades'] if t['date_in'] < S)} entered before {S}")
                for t in fa["trades"][-3:]:
                    print(f"     pre/post? {'post' if t['date_in'] >= S else 'pre '}  {t['date_in']} -> "
                          f"{t['date_out']}  {t['entry']:.2f} -> {t['exit']:.2f}  {t['bars']} bars")
                for r in fr[-5:]:
                    print(f"     {r}")
                print(f"   status: {fs}")
                check("live data/forward: rows()/status() run without error", True)
                check("live data/forward: no journalled row was entered before the stream start",
                      all(t["date_in"] >= S for t in leg_d7.compute(FORWARD)["stream"]))
            except Exception as e:  # noqa: BLE001
                check("live data/forward: rows()/status() run without error", False, f"{type(e).__name__}: {e}")

    nfail = sum(1 for _, ok, _ in checks if not ok)
    print(f"\nSUMMARY: {len(checks) - nfail}/{len(checks)} checks passed")
    print(f"  archived SPX_cfd n={a_cfd['n']} win={a_cfd['win']:.4f} hold={a_cfd['avg_hold_bars']:.4f}; "
          f"leg reproduced (start=None) n={m06['n']} win={m06['win']:.4f} hold={m06['avg_hold_bars']:.4f}; "
          f"default rows() on the archive: {n_def} (all pre-{S})")
    return nfail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
