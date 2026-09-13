"""Attempt 54 (Round 74): post-fix reversal of the pre-fix drift at the daily WMR 16:00-London fix.

P1: EURUSD 1m (Dukascopy, UTC), every weekday excluding the attempt-52 month-ends; pre-move =
log(close 15:59 London / open 15:45 London); direction -sign(pre-move); enter open 16:00,
exit close 16:14; cost 1 pip RT, 1.5x / 2x. IS = first 75% of eligible days; OOS sealed unless
UNSEAL_OK=1 --unseal. Diagnostics: mirror, placebo clocks, dose terciles, per-year, USDJPY,
pre-fix drift statistics. Outputs results/r74_dailyfix_is.json (or _oos.json).
"""
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
LDN = ZoneInfo("Europe/London")
PIP = {"EURUSD": 1e-4, "USDJPY": 1e-2}


def load(sym):
    df = pd.read_csv(f"data/fx/dukascopy/{sym}_1m.csv", parse_dates=["time"]).set_index("time")
    df = df[df.volume > 0]
    l = df.index.tz_convert(LDN)
    df["d"] = l.date; df["hm"] = l.hour * 100 + l.minute; df["dow"] = l.dayofweek
    return df


me = set(pd.to_datetime(pd.read_csv("results/r72b_monthend_map.csv").date).dt.date)


def day_table(df, a0, a1, e0, e1):
    """Per day: pre-move over [a0,a1) London and post-move over [e0,e1) London (log, bp)."""
    rows = []
    for d, g in df[df.dow < 5].groupby("d"):
        if d in me:
            continue
        pre = g[(g.hm >= a0) & (g.hm < a1)]; post = g[(g.hm >= e0) & (g.hm < e1)]
        if len(pre) < 10 or len(post) < 10:
            continue
        rows.append(dict(date=d, pre=np.log(pre.close.iloc[-1] / pre.open.iloc[0]) * 1e4,
                         post=np.log(post.close.iloc[-1] / post.open.iloc[0]) * 1e4, px=float(post.open.iloc[0])))
    t = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    cut = int(len(t) * 0.75)
    t["oos"] = t.index >= cut
    return t[t.oos] if UNSEAL else t[~t.oos]


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def cell(t, sym, sign=-1.0, mult=1.0):
    t = t[t.pre != 0]
    cost_bp = PIP[sym] / t.px * 1e4 * mult
    return sign * np.sign(t.pre) * t.post - cost_bp


res = {"unsealed": UNSEAL}
for sym in ("EURUSD", "USDJPY"):
    df = load(sym)
    t = day_table(df, 1545, 1600, 1600, 1615)
    tag = "P1" if sym == "EURUSD" else "USDJPY_readonly"
    r = {"x1": stats(cell(t, sym)), "x15": stats(cell(t, sym, mult=1.5)), "x2": stats(cell(t, sym, mult=2.0)),
         "gross": stats(cell(t, sym, mult=0.0)), "mirror_x1": stats(cell(t, sym, sign=+1.0)),
         "per_year_net": {int(y): round(float(v), 2) for y, v in cell(t, sym).groupby(pd.to_datetime(t[t.pre != 0].date).dt.year).mean().items()},
         "pre_drift": dict(mean_abs_bp=float(t.pre.abs().mean()), mean_bp=float(t.pre.mean()),
                           corr_pre_post=float(t.pre.corr(t.post)), n=int(len(t))),
         "last_is_day": str(t.date.max())}
    tt = t[t.pre != 0].copy(); tt["dose"] = tt.pre.abs(); q = tt.dose.quantile([1 / 3, 2 / 3]).values
    r["dose_terciles_net"] = {k: stats(cell(tt[m], sym)) for k, m in
                              (("low", tt.dose <= q[0]), ("mid", (tt.dose > q[0]) & (tt.dose <= q[1])), ("high", tt.dose > q[1]))}
    r["dose_cuts_bp"] = [float(x) for x in q]
    if sym == "EURUSD":
        for name, (a0, a1, e0, e1) in {"placebo_1530_1545": (1515, 1530, 1530, 1545), "placebo_1630_1645": (1615, 1630, 1630, 1645),
                                       "placebo_1500_1515": (1445, 1500, 1500, 1515)}.items():
            tp = day_table(df, a0, a1, e0, e1)
            r[name + "_net"] = stats(cell(tp, sym)); r[name + "_corr_pre_post"] = float(tp.pre.corr(tp.post))
    res[tag] = r
    print(f"=== {tag} ({'OOS' if UNSEAL else 'IS'}) ===")
    for k, v in r.items():
        print(f"  {k}: {json.dumps(v, default=float)}")

s = res["P1"]["x1"]
PASS = (s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2 and s.get("pf", 0) >= 1.15
        and s.get("halves") == [1.0, 1.0] and res["P1"]["x2"]["mean_bp"] > 0)
res["P1_pass"] = bool(PASS)
print(f"\nATTEMPT 54 {'OOS' if UNSEAL else 'IS'} VERDICT: {'PASS' if PASS else 'FAIL'}")
json.dump(res, open(f"results/r74_dailyfix_{'oos' if UNSEAL else 'is'}.json", "w"), indent=1, default=float)
