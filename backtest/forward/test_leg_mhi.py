"""Verification of forward/leg_mhi.py against the archived backtest (CONTRACT.md, MHI leg).

What is checked (run: cd backtest && python3 forward/test_leg_mhi.py):

  1. leg_mhi.rows() on a temp copy of data/HK33_M15.csv (as hk33_m15.csv) must reproduce,
     trade for trade, the frozen cell t0.3_s0.5_c1600 recomputed on the SAME HK33-only file
     with run_hsi.py's own code.  The reference is not a re-typing: the relevant source
     segments of run_hsi.py (daily range / ATR14, the H-A day table, fade()) are located by
     text markers and exec'd as-is.  n, win rate and PF (10-pt cost, applied here only) must
     agree to floating-point precision.
  2. The archived cell results/hsi.json[ha_econ][t0.3_s0.5_c1600] covers the SPLICED
     sample (HK50 2022-02..2024-04 + HK33 2024-04..).  If data/HK50_PT15M_yuan.csv is on
     disk the splice is rebuilt exactly as run_hsi.py does and the same exec'd code must
     reproduce the archived n / pf / win (full span and h2 >= 2024-05-01).  The spliced
     trade list is then diffed against the HK33-only list so every residual is named.
  3. The forward-only completeness guard (a session whose 08:00 UTC has not been reached is
     not journalled) must be a no-op on the finished archive, and must suppress the last
     triggered session when the file is truncated mid-session.

Exit status 0 only if every MUST check passes; the report is printed regardless.
"""
import json
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, BT)
import leg_mhi  # noqa: E402

COST = 10.0
CELL = "t0.3_s0.5_c1600"
TRIG, STOP_K, EXIT_COL = 0.3, 0.5, "c1600"
MID = pd.Timestamp("2024-05-01").date()
HK33_CSV = os.path.join(BT, "data", "HK33_M15.csv")
HK50_CSV = os.path.join(BT, "data", "HK50_PT15M_yuan.csv")
RUN_HSI = os.path.join(BT, "run_hsi.py")
HSI_JSON = os.path.join(BT, "results", "hsi.json")

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


# ----------------------------------------------------------------------------- reference
def _segment(src, start, end):
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


def run_hsi_cell(H):
    """Run run_hsi.py's own H-A code (lines 15-25, 59-62, 68-88, 100-118) on frame H and
    return the per-trade DataFrame (d, pnl, ent) of the frozen cell plus the day table A."""
    src = open(RUN_HSI).read()
    code = (_segment(src, "COST = 10.0", "# ----")            # COST, pfv, met
            + _segment(src, "days = sorted(H.d.unique())", "MID = ")   # daily_rng, atr14
            + _segment(src, "rows = []", "from scipy")         # day table A, push_n
            + _segment(src, "def fade(", "ha = {}"))           # fade()
    H = H.copy()
    H["d"] = H.index.date
    H["hm"] = H.index.hour * 100 + H.index.minute
    ns = dict(pd=pd, np=np, H=H)
    exec(code, ns)
    A = ns["A"]
    sub = A[np.abs(A.push_n) >= TRIG]
    pnl, ent = ns["fade"](sub, STOP_K, EXIT_COL)
    f = pd.DataFrame(dict(pnl=pnl, ent=ent, d=sub.d.values[:len(pnl)]))
    return f, A, ns["met"], ns["atr14"]


def load_hk33(path):
    b = pd.read_csv(path)
    b["ts"] = pd.to_datetime(b.iloc[:, 0], utc=True)
    b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()
    return b[~b.index.duplicated()]


def load_spliced():
    """run_hsi.py lines 28-42 verbatim in effect."""
    a = pd.read_csv(HK50_CSV)
    a["ts"] = pd.to_datetime(a.time, utc=True)
    a = a.set_index("ts")[["open", "high", "low", "close"]].sort_index()
    b = load_hk33(HK33_CSV)
    H = pd.concat([a[a.index < (b.index.min())], b]).sort_index()
    return H[~H.index.duplicated()]


def summarize(pnl):
    x = pd.Series(np.asarray(pnl, float))
    if not len(x):
        return dict(n=0, pf=np.nan, win=np.nan)
    pf = float(x[x > 0].sum() / max(-x[x <= 0].sum(), 1e-9))
    return dict(n=int(len(x)), pf=pf, win=float((x > 0).mean()))


def fmt(m):
    return f"n={m['n']} win={m['win']:.4f} PF={m['pf']:.4f}"


def rows_to_frame(rs):
    df = pd.DataFrame(rs)
    if not len(df):
        return df
    sgn = np.where(df.side.values == "S", -1.0, 1.0)
    df["pnl"] = sgn * (df.exit.values - df.entry.values) - COST
    return df


# ----------------------------------------------------------------------------- main
def main():
    print(f"leg_mhi verification  (cost {COST} pts applied in this test only)\n")

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as td:
        shutil.copy(HK33_CSV, os.path.join(td, "hk33_m15.csv"))

        # ---- 1. leg rows on the archived HK33 file
        rs = leg_mhi.rows(td)
        R = rows_to_frame(rs)
        m_leg = summarize(R.pnl)
        span = f"{R.date.min()} .. {R.date.max()}" if len(R) else "-"
        print(f"1. leg_mhi.rows on data/HK33_M15.csv: {fmt(m_leg)}  trades {span}")
        print(f"   notes: {R.note.value_counts().to_dict()}  sides: {R.side.value_counts().to_dict()}")
        check("row schema", all(set(r) == {"date", "instr", "side", "entry", "stop", "exit",
                                           "note", "src"} for r in rs)
              and all(r["instr"] == "MHI" and r["src"] == "auto" and r["side"] in ("L", "S")
                      and r["note"] in ("fade|stop", "fade|time") for r in rs))
        check("dedup key (date, instr, note) unique",
              not R.duplicated(subset=["date", "instr", "note"]).any())
        # a 'stop' exit must be at the stop price (no side/stop ordering invariant exists:
        # the 01:30 open can already sit beyond pre_hi/pre_lo +- 0.5*pre_rng, in which case
        # the rule stops out on the entry bar itself)
        check("stop rows exit at stop",
              all((r["note"] == "fade|time") or np.isclose(r["exit"], r["stop"]) for r in rs))

        # ---- 1b. reference: run_hsi.py's own code on the same HK33-only file
        H33 = load_hk33(os.path.join(td, "hk33_m15.csv"))
        f33, A33, met, atr33 = run_hsi_cell(H33)
        m_ref = summarize(f33.pnl)
        print(f"\n1b. run_hsi.py code on the same HK33-only file: {fmt(m_ref)}")
        print(f"    run_hsi.met(): {json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in met(f33.pnl, f33.ent).items()})}")
        first_atr_day = atr33.dropna().index.min()
        print(f"    HK33 file spans {H33.index.min()} .. {H33.index.max()}; "
              f"first day with ATR14 = {first_atr_day} (14-day warm-up)")
        ref = f33.assign(date=[d.isoformat() for d in f33.d]).set_index("date")
        leg = R.set_index("date") if len(R) else R
        same_dates = len(leg) == len(ref) and list(leg.index) == list(ref.index)
        check("trade count equals reference", m_leg["n"] == m_ref["n"], f"{m_leg['n']} vs {m_ref['n']}")
        check("trade dates identical", same_dates)
        if same_dates:
            check("entry prices identical", np.allclose(leg.entry.values, ref.ent.values, atol=1e-9, rtol=0))
            check("per-trade pnl identical", np.allclose(leg.pnl.values, ref.pnl.values, atol=1e-9, rtol=0),
                  f"max |diff| {np.abs(leg.pnl.values - ref.pnl.values).max():.3g}")
        check("win rate identical", np.isclose(m_leg["win"], m_ref["win"], atol=1e-12),
              f"{m_leg['win']:.6f} vs {m_ref['win']:.6f}")
        check("PF identical", np.isclose(m_leg["pf"], m_ref["pf"], atol=1e-9),
              f"{m_leg['pf']:.6f} vs {m_ref['pf']:.6f}")

        # ---- 2. archived cell
        arch = json.load(open(HSI_JSON))["ha_econ"][CELL]
        a_all = dict(n=arch["n"], pf=arch["pf"], win=arch["win"])
        a_h2 = dict(n=arch["h2"]["n"], pf=arch["h2"]["pf"], win=arch["h2"]["win"])
        a_h1 = dict(n=arch["h1"]["n"], pf=arch["h1"]["pf"], win=arch["h1"]["win"])
        print(f"\n2. archived results/hsi.json ha_econ[{CELL}] (SPLICED HK50+HK33, 2022-02..):")
        print(f"   full span : {fmt(a_all)}")
        print(f"   h1 <{MID} : {fmt(a_h1)}")
        print(f"   h2 >={MID}: {fmt(a_h2)}   <- nearest archived proxy for the HK33 span")
        print(f"   HK33-only recompute (1b): {fmt(m_ref)}")
        print(f"   archived h2 minus HK33-only: dn={a_h2['n'] - m_ref['n']} "
              f"dwin={a_h2['win'] - m_ref['win']:+.4f} dPF={a_h2['pf'] - m_ref['pf']:+.4f}")

        if os.path.exists(HK50_CSV):
            Hs = load_spliced()
            fs, As, _, atrs = run_hsi_cell(Hs)
            m_s = summarize(fs.pnl)
            m_s2 = summarize(fs[fs.d >= MID].pnl)
            m_s1 = summarize(fs[fs.d < MID].pnl)
            print(f"\n2b. splice rebuilt from data/ (HK50 {HK50_CSV.split('/')[-1]} + HK33): "
                  f"{len(Hs)} bars {Hs.index.min()} .. {Hs.index.max()}")
            print(f"    exec'd run_hsi code, full span: {fmt(m_s)}   h1: {fmt(m_s1)}   h2: {fmt(m_s2)}")
            exact = (m_s["n"] == a_all["n"] and np.isclose(m_s["pf"], a_all["pf"], atol=1e-9)
                     and np.isclose(m_s["win"], a_all["win"], atol=1e-12))
            exact2 = (m_s2["n"] == a_h2["n"] and np.isclose(m_s2["pf"], a_h2["pf"], atol=1e-9)
                      and np.isclose(m_s2["win"], a_h2["win"], atol=1e-12))
            check("spliced rebuild reproduces archived full-span cell", exact,
                  f"{fmt(m_s)} vs archived {fmt(a_all)}")
            check("spliced rebuild reproduces archived h2", exact2,
                  f"{fmt(m_s2)} vs archived {fmt(a_h2)}")

            # trade-by-trade diff: spliced vs HK33-only
            hk33_start = H33.index.min().date()
            s_in = fs[fs.d >= hk33_start]
            s_only = s_in[~s_in.d.isin(f33.d)]
            k_only = f33[~f33.d.isin(fs.d)]
            common = s_in.d.isin(f33.d)
            cs = s_in[common].set_index("d")
            ck = f33.set_index("d").loc[cs.index]
            print(f"\n2c. spliced trades on/after HK33 start {hk33_start}: n={len(s_in)} "
                  f"({fmt(summarize(s_in.pnl))})")
            print(f"    in spliced but not HK33-only ({len(s_only)}):")
            for _, r in s_only.iterrows():
                print(f"      {r.d} pnl {r.pnl:+8.1f} ent {r.ent:.1f}   "
                      f"spliced ATR14 {atrs.get(r.d, np.nan):.1f} / HK33-only ATR14 "
                      f"{atr33.get(r.d, np.nan) if r.d in atr33.index else float('nan'):.1f}")
            print(f"    in HK33-only but not spliced ({len(k_only)}):")
            for _, r in k_only.iterrows():
                print(f"      {r.d} pnl {r.pnl:+8.1f} ent {r.ent:.1f}   "
                      f"spliced ATR14 {atrs.get(r.d, np.nan):.1f} / HK33-only ATR14 {atr33.get(r.d, np.nan):.1f}")
            same_common = np.allclose(cs.pnl.values, ck.pnl.values, atol=1e-9, rtol=0) if len(cs) else True
            print(f"    common dates: {len(cs)}, per-trade pnl identical: {same_common}")
            # Where does ATR14 stop depending on the splice?  atr14[day k] = mean(rng[k-14..k-1]).
            # HK33-only day 1 (2024-04-19) is a partial day (starts 10:15 UTC), so only the
            # HK33-only ATR of day 15 differs from the spliced ATR; days 1-14 have no ATR at
            # all in HK33-only; from day 16 the two ATR series coincide.
            days33 = sorted(set(H33.index.date))
            conv = days33[15] if len(days33) > 15 else None
            atr_same_after = (bool(np.allclose(atrs.reindex(atr33.index).loc[conv:].values,
                                               atr33.loc[conv:].values, equal_nan=True))
                              if conv else False)
            print(f"    ATR14 coincides (spliced == HK33-only) from {conv}: {atr_same_after}")
            all_resid_early = all(d < conv for d in s_only.d) and all(d < conv for d in k_only.d)
            check("all spliced-vs-HK33 residual trades fall in the ATR14 warm-up window",
                  same_common and atr_same_after and all_resid_early,
                  f"residual dates all < {conv}")
            check("HK33-only matches spliced trades from ATR convergence onward",
                  (m_after := summarize(fs[fs.d >= conv].pnl)) == summarize(f33[f33.d >= conv].pnl),
                  f"both {fmt(m_after)}")
        else:
            print("\n2b. data/HK50_PT15M_yuan.csv not present: spliced rebuild skipped; the "
                  "archived numbers cannot be reproduced exactly here, only the HK33-only "
                  "recompute (1b) is available as the comparison target.")

        # ---- 3. completeness guard
        rs_noguard = leg_mhi.rows(td, require_complete=False)
        check("completeness guard is a no-op on the finished archive", rs_noguard == rs)
        if len(rs):
            last = rs[-1]["date"]
            raw = pd.read_csv(HK33_CSV)
            ts = pd.to_datetime(raw.iloc[:, 0], utc=True)
            # cut at 07:00 UTC (15:00 HKT): the feed has no bars in the 04:00-04:45 lunch
            # slots, so this leaves 18 session bars and the >=15-bar rule alone would still
            # emit the day (with a premature 06:45 close as its "exit")
            cut = pd.Timestamp(last, tz="UTC") + pd.Timedelta(hours=7)
            trunc = raw[ts < cut]
            td2 = os.path.join(td, "trunc")
            os.makedirs(td2, exist_ok=True)
            trunc.to_csv(os.path.join(td2, "hk33_m15.csv"), index=False)
            g = leg_mhi.rows(td2)
            ng = leg_mhi.rows(td2, require_complete=False)
            check("guard suppresses an in-progress session (file cut at 07:00 UTC on last trade day)",
                  all(r["date"] != last for r in g) and any(r["date"] == last for r in ng),
                  f"guarded n={len(g)}, unguarded n={len(ng)} (unguarded exits at the 06:45 close)")
            check("guarded rows on truncated file == archive rows minus that day",
                  g == [r for r in rs if r["date"] != last])
            print(f"   status(): {leg_mhi.status(td2)}")

    # ---- summary
    nfail = sum(1 for _, ok, _ in checks if not ok)
    print(f"\nSUMMARY: {len(checks) - nfail}/{len(checks)} checks passed")
    print(f"  leg rows on HK33_M15.csv      : {fmt(m_leg)}")
    print(f"  run_hsi code, HK33-only       : {fmt(m_ref)}")
    print(f"  archived spliced cell (full)  : {fmt(a_all)}")
    print(f"  archived spliced cell (h2)    : {fmt(a_h2)}")
    return nfail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
