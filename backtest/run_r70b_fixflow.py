"""Round 70B attempt 51: month-end WM/Reuters 4pm-London fix flow -> gold, STAGED.

Stage 1 (this file, --stage1): the USD gate on the r35 synthetic-DXY 15m frame
(0.809 x -dlog EURUSD + 0.191 x dlog USDJPY, ejtrader m15, ET = feed - 7h; the feed's 08:30-ET
release spike sits at feed slot 15:30 in both seasons - tick-volume fingerprint 2026-09-09).
Rule: on each month-end session, USD direction D_usd = -sign(SPX month-to-date at the 10:00 ET
print) over the window [fix - 30 min, fix] where fix = 16:00 Europe/London converted to New
York per event (12:00 ET on the 16 DST-mismatch month-ends). Gate: mean signed USD move in the
mechanism direction with t >= 2 on IS month-ends (2012-11 .. 2022-03, entirely inside the gold
splice's IS block). If the gate fails the gold family dies unrun.
Stage 2 (--stage2, only after a stage-1 pass): the frozen gold cells C1-C4 on the spliced frame.
Outputs results/r70b_fixflow_stage1.json (and _stage2.json).
"""
import json
import sys

import numpy as np
import pandas as pd

STAGE1 = "--stage1" in sys.argv or "--stage2" not in sys.argv
NY = "America/New_York"


def load_ej(name):
    df = pd.read_csv(f"data/{name}", parse_dates=["Date"])
    ts = (df.Date - pd.Timedelta(hours=7)).dt.tz_localize(NY, ambiguous="NaT", nonexistent="shift_forward")
    px = pd.DataFrame(dict(o=df.open.values, c=df.close.values), index=ts).sort_index()
    px = px[~px.index.isna()]
    lo, hi = (0.8, 1.6) if name.startswith("EURUSD") else (60.0, 200.0)   # descale x1e5 / x1e3 feeds
    for _ in range(8):
        if lo <= px.c.median() <= hi: break
        px = px / 10.0
    assert lo <= px.c.median() <= hi, (name, px.c.median())
    return px[~px.index.duplicated()]


eur, jpy = load_ej("EURUSD_m15_ejtrader.csv"), load_ej("USDJPY_m15_ejtrader.csv")
print(f"EURUSD {eur.index.min()} .. {eur.index.max()} median {eur.c.median():.4f}; USDJPY median {jpy.c.median():.2f}")
ev = pd.read_csv("results/r70b_monthend_map.csv", parse_dates=["date"])


def usd_move(t0, t1):
    """Synthetic-DXY log move from the open of the bar at t0 to the close of the last bar before t1."""
    e = eur[(eur.index >= t0) & (eur.index < t1)]; j = jpy[(jpy.index >= t0) & (jpy.index < t1)]
    if len(e) < 2 or len(j) < 2: return np.nan
    de, dj = np.log(e.c.iloc[-1] / e.o.iloc[0]), np.log(j.c.iloc[-1] / j.o.iloc[0])
    return 0.809 * (-de) + 0.191 * dj


def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 10: return dict(n=int(len(r)))
    m = len(r) // 2
    return dict(n=int(len(r)), mean_bp=float(r.mean() * 1e4), wr=float((r > 0).mean()),
                t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def cell(offsets, dsign, dates=None):
    """offsets = (minutes before fix at entry, minutes before fix at exit); dsign maps D_gold -> USD sign."""
    out = []
    for _, r in ev.iterrows():
        d = r.date.date()
        if dates is not None and d not in dates: continue
        fix = pd.Timestamp(f"{d} {r.fix_ny}", tz=NY)
        t0, t1 = fix - pd.Timedelta(minutes=offsets[0]), fix - pd.Timedelta(minutes=offsets[1])
        if t0 < eur.index.min() or t1 > eur.index.max(): continue
        mv = usd_move(t0, t1)
        if np.isnan(mv): continue
        out.append(dsign(int(r.D_gold)) * mv)
    return np.array(out)


if STAGE1:
    D_usd = lambda dg: -dg          # USD sold after a US up-month -> USD down; gold long <-> USD short
    res = {}
    res["gate_C1_fix-30_to_fix"] = stats(cell((30, 0), D_usd))
    res["C2_fix-60_to_fix"] = stats(cell((60, 0), D_usd))
    res["post_fix_reversal_fix_to_+30 (opposite sign)"] = stats(cell((0, -30), lambda dg: dg))
    res["placebo_fix-90_to_-60"] = stats(cell((90, 60), D_usd))
    res["placebo_fix-120_to_-90"] = stats(cell((120, 90), D_usd))
    res["placebo_fix+30_to_+60"] = stats(cell((-30, -60), D_usd))
    # control days: same clock and D on T-3 / T+3 sessions around each month-end (flow absent)
    bdays = pd.bdate_range("2012-01-01", "2026-12-31").date
    idx = {d: i for i, d in enumerate(bdays)}
    ctrl = []
    for _, r in ev.iterrows():
        d = r.date.date()
        if d not in idx: continue
        for k in (-3, 3):
            dd = bdays[idx[d] + k]
            fix = pd.Timestamp(f"{dd} {r.fix_ny}", tz=NY)
            t0, t1 = fix - pd.Timedelta(minutes=30), fix
            if t0 < eur.index.min() or t1 > eur.index.max(): continue
            mv = usd_move(t0, t1)
            if not np.isnan(mv): ctrl.append(-int(r.D_gold) * mv)
    res["control_T-3_T+3_same_D"] = stats(np.array(ctrl))
    res["events_window"] = dict(first=str(ev.date.min().date()), last_in_frame=str(eur.index.max().date()))
    print("=== STAGE 1: USD gate on synthetic DXY 15m (IS month-ends 2012-11..2022-03) ===")
    for k, v in res.items():
        print(f"  {k:<48} {v}")
    g = res["gate_C1_fix-30_to_fix"]
    passed = g.get("n", 0) >= 40 and (g.get("mean_bp") or -1) > 0 and (g.get("t") or -9) >= 2
    res["gate_pass"] = bool(passed)
    print(f"\nSTAGE-1 GATE: {'PASS - stage 2 (gold cells) may be read' if passed else 'FAIL - the gold family dies unrun'}")
    json.dump(res, open("results/r70b_fixflow_stage1.json", "w"), indent=1, default=float)
