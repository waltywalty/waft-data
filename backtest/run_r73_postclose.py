"""Attempt 53 (Round 73): post-close reversal of the closing-auction push, 16:00 -> 16:15 ET.

Frozen cell C1: SPX/NDX/RTY 5m CFD frames pooled, entry = open of the 16:00 bar, exit = 16:15
print (close of the 16:10 bar), direction = -sign(close(15:55 bar) - open(15:50 bar)); costs
MICRO at 1x/1.5x/2x; R = (pnl - cost)/ATR20. IS only (engine cuts); OOS sealed unless
UNSEAL_OK=1 --unseal by the integrator. Diagnostics: unconditional controls, mirror, placebo
clocks (15:30->15:45 on the 15:20->15:30 push; 16:30->16:45 on the 16:20->16:30 push), dose
terciles, per-instrument, per-year, true-ES 5m forward week (descriptive).
Outputs results/r73_postclose_is.json (or _oos.json when unsealed).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday_engine as E  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
IDX = ("SPX", "NDX", "RTY")


def push_dir(a, b):
    """callable(pre, key) -> -sign(close of bar b minus open of bar a)."""
    def f(pre, key):
        x, y = pre[pre.hm == a], pre[pre.hm == b]
        if len(x) != 1 or len(y) != 1:
            return None
        p = float(y.close.iloc[0] - x.open.iloc[0])
        return None if p == 0 else int(-np.sign(p))
    return f


def push_val(a, b):
    def f(pre, key):
        x, y = pre[pre.hm == a], pre[pre.hm == b]
        return float(y.close.iloc[0] - x.open.iloc[0]) if len(x) == 1 and len(y) == 1 else np.nan
    return f


def run(entry, exit_, days, direction=0):
    parts = []
    for idx in IDX:
        t = E.run_cell(dict(instr=idx, entry=entry, exit=exit_, days=days, direction=direction), unseal=UNSEAL)
        if len(t):
            parts.append(t)
    if not parts:
        return pd.DataFrame()
    t = pd.concat(parts)
    return t[t.oos] if UNSEAL else t[~t.oos]


res = {"unsealed": UNSEAL}
c1 = run("16:00", "16:15", push_dir(1550, 1555))
res["C1"] = E.summarize(c1, "C1 post-close reversal 16:00->16:15, -sign(15:50->16:00 push)")
E.print_summary(res["C1"])
res["C1_per_instr"] = {i: E.summarize(c1[c1.instr == i], i) for i in IDX if (c1.instr == i).any()}
for i, s in res["C1_per_instr"].items():
    print(f"  {i}: {E.fmt(s['x1'])}")
# mirror
def mirror_dir(pre, key):
    d = push_dir(1550, 1555)(pre, key)
    return None if d is None else -d


res["mirror_+sign"] = E.summarize(run("16:00", "16:15", mirror_dir), "mirror: +sign(push)")
E.print_summary(res["mirror_+sign"])
# unconditional controls
for d, name in ((1, "control_always_long"), (-1, "control_always_short")):
    res[name] = E.summarize(run("16:00", "16:15", None, direction=d), name)
    E.print_summary(res[name])
# placebo clocks
res["placebo_1530_1545_on_1520_1530_push"] = E.summarize(run("15:30", "15:45", push_dir(1520, 1525)), "placebo 15:30->15:45")
E.print_summary(res["placebo_1530_1545_on_1520_1530_push"])
res["placebo_1630_1645_on_1620_1630_push"] = E.summarize(run("16:30", "16:45", push_dir(1620, 1625)), "placebo 16:30->16:45")
E.print_summary(res["placebo_1630_1645_on_1620_1630_push"])
# dose terciles of |push|/ATR20
if len(c1):
    pv = {}
    for idx in IDX:
        d, b, cut = E.sessions(idx, UNSEAL)
        f = push_val(1550, 1555)
        for key, day in b.groupby("skey"):
            pv[(idx, key)] = f(day[day.hm < 1600], key)
    c1 = c1.assign(push=[abs(pv.get((i, k), np.nan)) for i, k in zip(c1.instr, c1.date)])
    c1["dose"] = c1.push / c1.atr
    q = c1.dose.quantile([1 / 3, 2 / 3]).values
    res["dose_terciles"] = {}
    for name, m in (("low", c1.dose <= q[0]), ("mid", (c1.dose > q[0]) & (c1.dose <= q[1])), ("high", c1.dose > q[1])):
        res["dose_terciles"][name] = E.summarize(c1[m], name)
        print(f"  dose {name:4s}: {E.fmt(res['dose_terciles'][name]['x1'])}")
    res["dose_cuts_push_over_atr"] = [float(x) for x in q]
# true ES 5m forward week, descriptive
try:
    j = json.load(open("data/forward/es_5m_2026-09-09.json")); t = pd.to_datetime(j["time"], utc=True).tz_convert("America/New_York")
    e = pd.DataFrame(dict(open=j["open"], close=j["close"]), index=t); e["d"] = e.index.date; e["hm"] = e.index.hour * 100 + e.index.minute
    rows = []
    for d, g in e.groupby("d"):
        a, b, c, x = g[g.hm == 1550], g[g.hm == 1555], g[g.hm == 1600], g[g.hm == 1610]
        if len(a) and len(b) and len(c) and len(x):
            p = b.close.iloc[0] - a.open.iloc[0]
            if p != 0:
                rows.append(dict(date=str(d), push=float(p), pnl=float(-np.sign(p) * (x.close.iloc[0] - c.open.iloc[0]))))
    res["true_ES_5m_week"] = rows
    print("  true ES 5m week:", rows)
except Exception as ex:
    res["true_ES_5m_week"] = f"skipped: {ex}"
passed = E.clears_intraday_bar(res["C1"])
res["C1_pass"] = bool(passed)
print(f"\nATTEMPT 53 {'OOS' if UNSEAL else 'IS'} VERDICT: {'PASS' if passed else 'FAIL'} (n>=40, avgR>0, t>=2, PF>=1.15, halves [+,+], positive at 2x)")
json.dump(res, open(f"results/r73_postclose_{'oos' if UNSEAL else 'is'}.json", "w"), indent=1, default=float)
