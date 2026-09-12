"""Round 72B attempt 52: post-fix USD move after the month-end WMR 4pm-London fix, signed by the
month's equity return - ONE SEALED SHOT on the independent 2022-04..2026-08 sample.

Origin: attempt 51's read-only residue (2012-11..2022-03, 112 month-ends): the 30 minutes AFTER
the fix moved the USD UP after a US up-month, +2.74 bp, t +3.49, halves [+,+], while the
registered pre-fix window was null. Mechanism (registered): Melvin & Prins (JFM 2015) fix the
SIGN - hedged foreign holders of US equity are under-hedged after a US up-month and SELL USD at
the fix; Evans et al. (JIMF 2018) document post-fix REVERSAL of fix-window price pressure; the
dealers who absorbed the hedgers' USD selling inside the five-minute fix window unwind after it,
so the USD moves UP after up-months (and down after down-months) in the half hour after the fix.
Data: Dukascopy 1m BID (data/fx/dukascopy/, UTC-pinned by the NFP spike in both seasons;
MANIFEST.md); SPX closes = IBKR official (2024-09+) / CFD RTH 15:55 close before, cross-checked.
Event map: results/r72b_monthend_map.csv (built BEFORE this file runs; fix = 16:00 London
converted per event; D = sign of SPX log return from the prior month-end close to the T-1 close,
known before the session starts).
FROZEN CELLS: primary (the only selectable cell) P1 = EURUSD, direction -D (short EURUSD after a
US up-month), enter at the open of the 1m bar starting at the fix, exit at the close of the bar
ending fix+30; cost 1.0 pip per round trip (retail micro lot), sensitivities 1.5x / 2x.
Read-only: B1 = synthetic-DXY basket 0.809(-dlog EURUSD)+0.191 dlog USDJPY over the same window
(comparability with the attempt-51 residue; no cost); placebos P1 on fix-30->fix (the attempt-51
gate window), fix+30->+60, fix+60->+90, fix-60->-30; control days T-3 / T+3 with the same D;
dose split |MTD| >= 2%; quarter-end split; per-year signs; DST-mismatch events listed.
Stage 2 (gold, read ONLY if P1 passes): G1 = XAUUSD, direction -D (short gold after a US
up-month), same window, cost 0.35 $/oz RT; reported in bp of price.
BAR (the house OOS bar): n >= 40, mean net > 0, t >= 2, PF >= 1.15, halves [+,+], positive at
1.5x and 2x cost. This is the family's one shot; it burns after this run, pass or fail.
Outputs results/r72b_postfix.json.
"""
import json
import sys

import numpy as np
import pandas as pd

PIP = 1e-4
COST_PIPS = 1.0
GOLD_COST = 0.35


def load(sym):
    df = pd.read_csv(f"data/fx/dukascopy/{sym}_1m.csv", parse_dates=["time"]).set_index("time")
    return df[df.volume > 0]


eur, jpy, xau = load("EURUSD"), load("USDJPY"), load("XAUUSD")
ev = pd.read_csv("results/r72b_monthend_map.csv", parse_dates=["date"])
print(f"EURUSD {eur.index.min()} .. {eur.index.max()} ({len(eur)} active bars); events {len(ev)}")


def move(px, t0, t1):
    """log move from the open of the first bar >= t0 to the close of the last bar < t1; NaN if thin."""
    w = px[(px.index >= t0) & (px.index < t1)]
    if len(w) < 10:
        return np.nan
    return float(np.log(w.close.iloc[-1] / w.open.iloc[0]))


def fix_ts(r):
    return pd.Timestamp(f"{r.date.date()} {r.fix_utc}", tz="UTC")


def cell(px, off0, off1, dsign, dates=None, cost_bp=0.0, scale=1.0):
    """Signed returns in bp per event; off = minutes relative to the fix; dsign(D) = trade sign
    applied to the instrument's log move; cost in bp subtracted (times scale for sensitivity)."""
    out = []
    for _, r in ev.iterrows():
        if dates is not None and r.date.date() not in dates:
            continue
        f = fix_ts(r)
        mv = move(px, f + pd.Timedelta(minutes=off0), f + pd.Timedelta(minutes=off1))
        if np.isnan(mv):
            continue
        out.append(dict(date=str(r.date.date()), D=int(r.D), ret_bp=dsign(int(r.D)) * mv * 1e4 - scale * cost_bp,
                        gross_bp=dsign(int(r.D)) * mv * 1e4))
    return pd.DataFrame(out)


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 5:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 0 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def basket(off0, off1, dsign):
    out = []
    for _, r in ev.iterrows():
        f = fix_ts(r); t0, t1 = f + pd.Timedelta(minutes=off0), f + pd.Timedelta(minutes=off1)
        de, dj = move(eur, t0, t1), move(jpy, t0, t1)
        if np.isnan(de) or np.isnan(dj):
            continue
        out.append(dsign(int(r.D)) * (0.809 * (-de) + 0.191 * dj) * 1e4)
    return np.array(out)


# EURUSD pip cost in bp of price: 1 pip / price
px_med = float(eur.close.median()); cost_bp = COST_PIPS * PIP / px_med * 1e4
print(f"EURUSD median {px_med:.4f}; 1 pip RT = {cost_bp:.2f} bp")
short_after_up = lambda D: -D          # EURUSD down when USD up after a US up-month
res = {"cost_bp_per_RT": cost_bp, "events": len(ev), "map": "results/r72b_monthend_map.csv"}

p1 = cell(eur, 0, 30, short_after_up, cost_bp=cost_bp)
res["P1_EURUSD_fix_to_+30"] = dict(x1=stats(p1.ret_bp), x15=stats(p1.gross_bp - 1.5 * cost_bp), x2=stats(p1.gross_bp - 2.0 * cost_bp),
                                  gross=stats(p1.gross_bp),
                                  per_year={int(y): round(float(g.ret_bp.mean()), 2) for y, g in p1.groupby(pd.to_datetime(p1.date).dt.year)},
                                  trades=p1.round(3).to_dict("records"))
s1 = res["P1_EURUSD_fix_to_+30"]["x1"]
PASS = (s1.get("n", 0) >= 40 and s1.get("mean_bp", -1) > 0 and (s1.get("t") or -9) >= 2 and s1.get("pf", 0) >= 1.15
        and s1.get("halves") == [1.0, 1.0] and res["P1_EURUSD_fix_to_+30"]["x15"]["mean_bp"] > 0 and res["P1_EURUSD_fix_to_+30"]["x2"]["mean_bp"] > 0)
res["P1_pass"] = bool(PASS)

# read-only diagnostics (gross, no cost, except where noted)
res["B1_basket_fix_to_+30_gross"] = stats(basket(0, 30, lambda D: D))
for name, (a, b) in {"placebo_fix-30_to_fix": (-30, 0), "placebo_fix+30_to_+60": (30, 60), "placebo_fix+60_to_+90": (60, 90),
                     "placebo_fix-60_to_-30": (-60, -30)}.items():
    res[name + "_EURUSD_gross"] = stats(cell(eur, a, b, short_after_up).gross_bp)
# control days T-3 / T+3 (same D, same clock) - use the calendar of active days
act_days = sorted(set(eur.index.date))
pos = {d: i for i, d in enumerate(act_days)}
ctrl = []
for _, r in ev.iterrows():
    d = r.date.date()
    if d not in pos: continue
    for k in (-3, 3):
        dd = act_days[pos[d] + k]
        f = pd.Timestamp(f"{dd} {r.fix_utc}", tz="UTC")
        mv = move(eur, f, f + pd.Timedelta(minutes=30))
        if not np.isnan(mv): ctrl.append(short_after_up(int(r.D)) * mv * 1e4)
res["control_T-3_T+3_EURUSD_gross"] = stats(np.array(ctrl))
dose = set(ev[ev.dose2pct].date.dt.date); res["dose_|MTD|>=2%_EURUSD_x1"] = stats(cell(eur, 0, 30, short_after_up, dose, cost_bp=cost_bp).ret_bp)
nodose = set(ev[~ev.dose2pct].date.dt.date); res["dose_|MTD|<2%_EURUSD_x1"] = stats(cell(eur, 0, 30, short_after_up, nodose, cost_bp=cost_bp).ret_bp)
qe = set(ev[ev.quarter_end].date.dt.date); res["quarter_end_EURUSD_x1"] = stats(cell(eur, 0, 30, short_after_up, qe, cost_bp=cost_bp).ret_bp)
nqe = set(ev[~ev.quarter_end].date.dt.date); res["non_quarter_end_EURUSD_x1"] = stats(cell(eur, 0, 30, short_after_up, nqe, cost_bp=cost_bp).ret_bp)
res["dst_mismatch_events"] = [str(d.date()) for d in ev[ev.fix_ny == "12:00"].date]

if PASS:
    g_med = float(xau.close.median()); gcost_bp = GOLD_COST / g_med * 1e4
    g1 = cell(xau, 0, 30, short_after_up, cost_bp=gcost_bp)      # short gold after a US up-month
    res["G1_XAUUSD_fix_to_+30"] = dict(cost_bp=gcost_bp, x1=stats(g1.ret_bp), x2=stats(g1.gross_bp - 2 * gcost_bp), gross=stats(g1.gross_bp))
else:
    res["G1_XAUUSD_fix_to_+30"] = "NOT READ (stage 1 failed)"

print("\n=== ATTEMPT 52: post-fix USD move signed by SPX MTD, sealed shot 2022-04..2026-08 ===")
for k, v in res.items():
    if k in ("map", "cost_bp_per_RT", "events"): continue
    if isinstance(v, dict) and "trades" in v:
        vv = {kk: v[kk] for kk in v if kk != "trades"}; print(f"  {k}: {json.dumps(vv, default=float)}")
    else:
        print(f"  {k}: {json.dumps(v, default=float)}")
print(f"\nSHOT: {'PASS - watch-list candidate, report for sign-off' if PASS else 'FAIL - family burned'}")
json.dump(res, open("results/r72b_postfix.json", "w"), indent=1, default=float)
