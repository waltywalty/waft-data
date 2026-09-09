"""Round 67 attempt 49: ETF fails-to-deliver persistence -> SHORT the mapped index.

Frozen per reference/goal_ledger.md ("Attempt 49 registration"): SPY/QQQ/IWM fails from the
primary SEC files (data/regsho/ftd/), trailing-252-C-date 90th-percentile day counts per
half-month, k >= 2 triggers, posting date on the SEC business calendar, entry at the RTH open
of the SECOND NYSE session strictly after the posting date, 2 selectable holds (H5 / HNP),
n = distinct posting dates, plus the registered diagnostics D1-D5, era, LOYO, per-instrument.

OOS FIREWALL: every leg whose posting date is >= OOS_START is dropped at frame build unless
the integrator runs `UNSEAL_OK=1 python3 run_r67_ftd.py --unseal`. Nothing in the default run
touches an OOS row. Outputs results/r67_ftd_is.json (results/r67_ftd_oos.json only unsealed).
"""
import datetime as dt
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
SIGNAL_ONLY = "--signal-only" in sys.argv   # stop before any return is read
IS_END = dt.date(2022, 11, 30)          # IS = postings P <= IS_END
OOS_START = dt.date(2022, 12, 15)       # OOS = postings P >= OOS_START (sealed)
PCT_WIN, PCT_THR, KMIN = 252, 0.90, 2
ETFS = {"SPY": "SPX", "QQQ": "NDX", "IWM": "RTY"}
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}
EXCL_HALVES = {(2019, 10, "a"), (2023, 8, "b"), (2024, 5, "b"), (2024, 6, "a")}   # _0 re-uploads, T+1 transition
FTD_DIR = "data/regsho/ftd"

# ---------------------------------------------------------------- calendars
def nth_weekday(y, m, wd, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(wd - d.weekday()) % 7)
    return d + dt.timedelta(days=7 * (n - 1))


def last_weekday(y, m, wd):
    d = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - wd) % 7)


def observed(d):
    if d.weekday() == 5: return d - dt.timedelta(days=1)
    if d.weekday() == 6: return d + dt.timedelta(days=1)
    return d


def federal_holidays(y):
    h = [observed(dt.date(y, 1, 1)), nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3), last_weekday(y, 5, 0),
         observed(dt.date(y, 7, 4)), nth_weekday(y, 9, 0, 1), nth_weekday(y, 10, 0, 2), observed(dt.date(y, 11, 11)),
         nth_weekday(y, 11, 3, 4), observed(dt.date(y, 12, 25))]
    if y >= 2021:
        h.append(observed(dt.date(y, 6, 19)))
    if observed(dt.date(y + 1, 1, 1)).year == y:            # New Year's observed on Dec 31
        h.append(observed(dt.date(y + 1, 1, 1)))
    return set(h)


FED_HOL = set().union(*[federal_holidays(y) for y in range(2011, 2028)])
COLVET = {d for y in range(2011, 2028) for d in (nth_weekday(y, 10, 0, 2), observed(dt.date(y, 11, 11)))}


def sec_bday(d):
    return d.weekday() < 5 and d not in FED_HOL


def posting_date(y, m, half):
    if half == "a":
        d = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
        while d.weekday() >= 5:
            d -= dt.timedelta(days=1)
        while not sec_bday(d):              # last weekday is a federal holiday -> NEXT SEC business day
            d += dt.timedelta(days=1)
        return d
    d = dt.date(y + (m == 12), (m % 12) + 1, 15)
    while not sec_bday(d):
        d += dt.timedelta(days=1)
    return d


def third_friday(y, m):
    return nth_weekday(y, m, 4, 3)


def half_of(d):
    return (d.year, d.month, "a" if d.day <= 15 else "b")


def next_half(h):
    y, m, s = h
    if s == "a": return (y, m, "b")
    return (y + (m == 12), (m % 12) + 1, "a")


def prev_year_half(h):
    return (h[0] - 1, h[1], h[2])


# ---------------------------------------------------------------- FTD signal side
def load_ftd():
    files = sorted(f for f in os.listdir(FTD_DIR) if f.endswith(".csv"))
    ser = {}
    for f in files:
        df = pd.read_csv(os.path.join(FTD_DIR, f))
        s = pd.Series(df.quantity.values.astype(float), index=pd.to_datetime(df.settlement_date).dt.date)
        ser[f[:-4]] = s[~s.index.duplicated(keep="last")]
    C = sorted(set().union(*[set(s.index) for s in ser.values()]))
    return ser, C


def trailing_pct(vals, win=PCT_WIN):
    out = np.full(len(vals), np.nan)
    for i in range(win, len(vals)):
        w = vals[i - win:i]
        out[i] = ((w < vals[i]).sum() + 0.5 * (w == vals[i]).sum()) / win
    return out


ser, C = load_ftd()
Cpos = {d: i for i, d in enumerate(C)}
halves_of_C = {}
for d in C:
    halves_of_C.setdefault(half_of(d), []).append(d)

etf_k, etf_F, etf_pct = {}, {}, {}
for etf in ETFS:
    v = np.array([ser[etf].get(d, 0.0) for d in C])
    p = trailing_pct(v)
    F = (p >= PCT_THR).astype(float); F[np.isnan(p)] = np.nan
    etf_pct[etf], etf_F[etf] = p, F
    etf_k[etf] = {h: (np.nan if np.isnan(F[[Cpos[d] for d in ds]]).any() else float(np.nansum(F[[Cpos[d] for d in ds]])))
                  for h, ds in halves_of_C.items()}

# non-mechanical day set (reported band): exclude days 1-6 and the 4 C-dates after the third Friday
mech = set()
ym = sorted({(d.year, d.month) for d in C})
for y, m in ym:
    tf = third_friday(y, m)
    after = [d for d in C if d > tf][:4]
    mech.update(after)
    mech.update(d for d in C if d.year == y and d.month == m and d.day <= 6)
etf_knm = {}
for etf in ETFS:
    F = etf_F[etf]
    etf_knm[etf] = {h: (np.nan if np.isnan(F[[Cpos[d] for d in ds]]).any()
                        else float(np.nansum([F[Cpos[d]] for d in ds if d not in mech])))
                    for h, ds in halves_of_C.items()}

# basket breadth per half-month (pure-demand sub-gate input): share of basket names with k >= 2
basket = [s for s in ser if s not in ETFS]
b_flag = {}
for sym in basket:
    v = np.array([ser[sym].get(d, 0.0) for d in C])
    p = trailing_pct(v)
    F = (p >= PCT_THR).astype(float); F[np.isnan(p)] = np.nan
    b_flag[sym] = F
breadth = {}
for h, ds in halves_of_C.items():
    idx = [Cpos[d] for d in ds]
    ks = [np.nansum(b_flag[s][idx]) for s in basket if not np.isnan(b_flag[s][idx]).any()]
    breadth[h] = float(np.mean([k >= 2 for k in ks])) if ks else np.nan


def defined(h):
    y, m, s = h
    if h in EXCL_HALVES or (y, m) < (2013, 1): return False
    if s == "b" and m in (3, 6, 9, 12): return False
    return len(halves_of_C.get(h, [])) >= 7


HALVES = sorted(h for h in halves_of_C if defined(h))
P_of = {h: posting_date(*h) for h in halves_of_C}      # every half posts (also excluded ones) - used for HNP exits

# ---------------------------------------------------------------- index frames (returns side)
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"), hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    return d


days = {ETFS[e]: build_days(ETFS[e]) for e in ETFS}
NYSE = sorted(set(days["SPX"].index) & (set(C) | COLVET))
NYSEpos = {d: i for i, d in enumerate(NYSE)}
FRAME_END = NYSE[-1]


def entry_session(P):
    after = [d for d in NYSE if d > P]
    return after[1] if len(after) > 1 else None


# stress labels for D4: #7 trigger days and #8 episode starts, verbatim from run_r49b / run_r50
vx = pd.read_csv("data/VIX_history_cboe.csv")
vix = pd.Series(vx.CLOSE.values, index=pd.to_datetime(vx.DATE).dt.date)
vix = vix[[d in NYSEpos for d in vix.index]]
dlog = np.log(vix).diff()
z7 = dlog / dlog.rolling(63).std().shift(1)
STRESS7 = set(z7[z7 >= 1.5].index)
cx = pd.read_csv("data/COR1M_history_cboe.csv")
cor = pd.Series(cx.CLOSE.values, index=pd.to_datetime(cx.DATE).dt.date)
cor = cor[[d in NYSEpos for d in cor.index]]
pct8 = cor.rolling(252).rank(pct=True)
STRESS8 = set(pct8[(pct8 >= 0.80) & (pct8.shift(1) < 0.80)].index)
STRESS = STRESS7 | STRESS8

fsrc = open("run_r42l_fomc.py").read()
FOMC = set(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', fsrc, re.S).group(1).split()).date)

# calendar windows for D5
TOM, OPEX = set(), set()
for y, m in ym:
    last = [d for d in NYSE if (d.year, d.month) == (y, m)]
    nxt = [d for d in NYSE if (d.year, d.month) == (y + (m == 12), (m % 12) + 1)]
    if last: TOM.add(last[-1])
    TOM.update(nxt[:3])
    tf = third_friday(y, m); mon = tf - dt.timedelta(days=4)
    OPEX.update(d for d in NYSE if mon <= d <= tf)


def stress_of(h):
    ds = halves_of_C[h]
    win = [d for d in NYSE if ds[0] <= d <= P_of[h]]
    return any(d in STRESS for d in win)


# ---------------------------------------------------------------- legs
def make_legs(select, hold, entry_shift=0):
    """select(h, etf) -> bool. Returns date-level rows; busy-until per instrument."""
    legs = []
    for etf, idx in ETFS.items():
        d = days[idx]; busy = None
        for h in HALVES:
            if not select(h, etf): continue
            P = P_of[h]
            base = P if entry_shift == 0 else P_of[next_half(h)]      # stale placebo: act one posting late
            e = entry_session(base)
            if e is None or e not in d.index: continue
            ei = NYSEpos[e]
            if busy is not None and ei <= busy: continue
            if hold == "H5":
                xi = ei + 4
            else:
                e_next = entry_session(P_of[next_half(h)] if entry_shift == 0 else P_of[next_half(next_half(h))])
                if e_next is None: continue
                xi = NYSEpos[e_next] - 1
            if xi >= len(NYSE) or xi < ei: continue
            x = NYSE[xi]
            if x not in d.index: continue
            en, xp, a = d.o[e], d.c[x], d.atr20[e]
            if not (np.isfinite(en) and np.isfinite(xp) and np.isfinite(a) and a > 0): continue
            r = (en - xp - MICRO[idx]) / a                                  # SHORT
            r15 = (en - xp - 1.5 * MICRO[idx]) / a
            hold_days = NYSE[ei:xi + 1]
            legs.append(dict(etf=etf, idx=idx, h=h, k=etf_k[etf][h], P=P, entry=e, exit=x, R=r, R15=r15,
                             stress=stress_of(h), qe_a=(h[2] == "a" and h[1] in (3, 6, 9, 12)),
                             cal=any(dd in TOM or dd in OPEX for dd in hold_days),
                             fomc=any(dd in FOMC for dd in hold_days), breadth=breadth.get(h, np.nan)))
            busy = xi
    return legs


def firewall(legs):
    return [l for l in legs if l["P"] <= IS_END or (UNSEAL and l["P"] >= OOS_START)]


def by_date(legs, key="R"):
    df = pd.DataFrame(legs)
    if df.empty: return pd.Series(dtype=float)
    return df.groupby("P")[key].mean().sort_index()


def nw_t(r, lag=2):
    r = np.asarray(r, float); n = len(r)
    if n < 3: return np.nan
    e = r - r.mean(); lrv = (e ** 2).sum() / n
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1)
        lrv += 2 * w * (e[L:] * e[:-L]).sum() / n
    return float(r.mean() / np.sqrt(lrv / n)) if lrv > 0 else np.nan


def stats(s):
    r = np.asarray(s, float); r = r[np.isfinite(r)]
    if len(r) < 5: return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]; m = len(r) // 2
    return dict(n=int(len(r)), wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avg_R=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                t_nw=nw_t(r), halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def welch_t(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 5 or len(b) < 5: return np.nan
    return float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))


def fmt(s):
    if s.get("n", 0) < 5: return f"n {s.get('n', 0)} (too few)"
    return (f"n {s['n']:>3} WR {s['wr']*100:5.1f}% PF {s['pf']:5.2f} avgR {s['avg_R']:+.3f} "
            f"t {s['t']:+.2f} tNW {s['t_nw']:+.2f} halves {s['halves']}")


# ---------------------------------------------------------------- signal-side prints (BEFORE any grid)
live = lambda h, e: (etf_k[e][h] >= KMIN) if np.isfinite(etf_k[e][h]) else False
band1 = lambda h, e: etf_k[e][h] == 1
band3 = lambda h, e: (etf_k[e][h] >= 3) if np.isfinite(etf_k[e][h]) else False
band2x = lambda h, e: etf_k[e][h] == 2
ctrl = lambda h, e: etf_k[e][h] == 0
seasonal = lambda h, e: (etf_k[e].get(prev_year_half(h), np.nan) >= KMIN) if defined(prev_year_half(h)) and np.isfinite(etf_k[e].get(prev_year_half(h), np.nan)) else False
nonmech = lambda h, e: (etf_knm[e][h] >= KMIN) if np.isfinite(etf_knm[e][h]) else False

print(f"C: {len(C)} settlement dates {C[0]}..{C[-1]}; NYSE sessions {len(NYSE)} to {FRAME_END}; "
      f"defined halves {len(HALVES)} (2013+, qe-b/excluded removed)")
print(f"IS = postings <= {IS_END}; OOS = postings >= {OOS_START} ({'UNSEALED' if UNSEAL else 'SEALED - dropped at build'})")
trig = [(h, e, etf_k[e][h]) for h in HALVES for e in ETFS if live(h, e)]
print(f"\n=== TRIGGER TABLE (k >= {KMIN}, P = {PCT_THR}): {len(trig)} legs ===")
yr = {}
for h, e, k in trig:
    P = P_of[h]; es = entry_session(P)
    seg = "IS" if P <= IS_END else ("OOS" if P >= OOS_START else "gap")
    yr.setdefault(P.year, [0, 0]); yr[P.year][0] += 1; yr[P.year][1] += seg == "IS"
    if seg == "IS":
        print(f"  {e} {h[0]}-{h[1]:02d}{h[2]} k={int(k)} P={P} avail={P} 16:00 ET  entry={es} 09:30 ET"
              f"{'  STRESS' if stress_of(h) else ''}{'  qe-a' if (h[2]=='a' and h[1] in (3,6,9,12)) else ''}")
print("  per-year legs (all / IS):", {y: tuple(v) for y, v in sorted(yr.items())})
dates_is = sorted({P_of[h] for h, e, k in trig if P_of[h] <= IS_END})
dates_oos = sorted({P_of[h] for h, e, k in trig if P_of[h] >= OOS_START})
print(f"  distinct posting dates: IS {len(dates_is)}, OOS {len(dates_oos)} (count only; OOS rows are not built)")
ns_is = [P for P in dates_is if not any(stress_of(h) for h, e, k in trig if P_of[h] == P)]
print(f"  D4: stress-labelled sessions #7 {len(STRESS7)} / #8 episode starts {len(STRESS8)}; "
      f"IS non-stress posting dates {len(ns_is)} of {len(dates_is)} ({len(ns_is)/max(1,len(dates_is))*100:.0f}%)")
if len(ns_is) < 25:
    print("  IS non-stress subset < 25 dates: SUBSUMED BY CONSTRUCTION (registered). Grid not read.")
    json.dump(dict(subsumed_by_construction=True, is_dates=len(dates_is), nonstress_is=len(ns_is)),
              open("results/r67_ftd_is.json", "w"), indent=1, default=str)
    raise SystemExit
ctrl_n = sorted({P_of[h] for h in HALVES for e in ETFS if ctrl(h, e) and P_of[h] <= IS_END})
print(f"  D3 control (k = 0) IS posting dates: {len(ctrl_n)}; frame ends {FRAME_END} (OOS beyond it is unreadable)")
if SIGNAL_ONLY:
    print("\n--signal-only: stopping before the grid.")
    raise SystemExit

# ---------------------------------------------------------------- grid
res = {"split": dict(IS_END=str(IS_END), OOS_START=str(OOS_START), frame_end=str(FRAME_END)),
       "signal": dict(legs=len(trig), is_dates=len(dates_is), oos_dates=len(dates_oos), nonstress_is=len(ns_is)),
       "cells": {}}
print("\n=== IS GRID (SHORT, indices pooled per posting date, ATR20-normalised, micro costs) ===")
cells = {}
for hold in ("H5", "HNP"):
    L = firewall(make_legs(live, hold)); s = by_date(L)
    cells[hold] = (L, s)
    st = stats(s); res["cells"][hold] = st
    print(f"  {hold:>3}: {fmt(st)}")

sel = sorted(("H5", "HNP"), key=lambda hh: -(res["cells"][hh].get("t") or -99))
win = None
for hh in sel:
    st = res["cells"][hh]
    if st.get("n", 0) >= 40 and (st.get("t") or -9) >= 2 and st.get("halves") == [1.0, 1.0]:
        other = res["cells"]["HNP" if hh == "H5" else "H5"]
        if (other.get("avg_R") or -1) > 0:
            win = hh
        break
print(f"\nSELECTION: {'cell ' + win if win else 'no cell clears n>=40 / t>=2 / halves [+,+] / neighbour>0'}")

# ---------------------------------------------------------------- diagnostics (both cells, all counted)
diag = {}
for hold in ("H5", "HNP"):
    L, s = cells[hold]
    d = {}
    d["D1_k1"] = stats(by_date(firewall(make_legs(band1, hold))))
    d["D1_k2"] = stats(by_date(firewall(make_legs(band2x, hold))))
    d["D1_k3plus"] = stats(by_date(firewall(make_legs(band3, hold))))
    d["D2_seasonal"] = stats(by_date(firewall(make_legs(seasonal, hold))))
    d["D2_stale"] = stats(by_date(firewall(make_legs(live, hold, entry_shift=1))))
    c = by_date(firewall(make_legs(ctrl, hold)))
    d["D3_control"] = stats(c); d["D3_t_diff"] = welch_t(s.values, c.values)
    df = pd.DataFrame(L)
    if not df.empty:
        nst = df[~df.stress].groupby("P").R.mean(); st_ = df[df.stress].groupby("P").R.mean()
        d["D4_nonstress"] = stats(nst); d["D4_stress"] = stats(st_)
        d["D4_nonstress_vs_control_diff"] = float(nst.mean() - c.mean()) if len(nst) and len(c) else np.nan
        pure = df[df.breadth < df.breadth.quantile(0.80)].groupby("P").R.mean()
        d["D4_pure_demand"] = stats(pure)
        d["D5_no_calendar_overlap"] = stats(df[~df.cal].groupby("P").R.mean())
        d["D5_qe_a"] = stats(df[df.qe_a].groupby("P").R.mean()); d["D5_non_qe_a"] = stats(df[~df.qe_a].groupby("P").R.mean())
        d["D5_fomc_in_hold_dates"] = int(df.fomc.sum())
        d["era_T3"] = stats(df[df.P <= dt.date(2017, 9, 1)].groupby("P").R.mean())
        d["era_T2"] = stats(df[df.P > dt.date(2017, 9, 1)].groupby("P").R.mean())
        d["per_instrument"] = {i: stats(df[df.idx == i].R) for i in ("SPX", "NDX", "RTY")}
        loyo = {}
        for y in sorted({p.year for p in df.P}):
            r = df[[p.year != y for p in df.P]].groupby("P").R.mean()
            loyo[y] = float(np.sign(r.mean())) if len(r) else np.nan
        d["LOYO_sign"] = loyo
    d["k_nonmechanical_band"] = stats(by_date(firewall(make_legs(nonmech, hold))))
    diag[hold] = d
    print(f"\n--- diagnostics {hold} ---")
    for kk, vv in d.items():
        if isinstance(vv, dict) and "n" in vv: print(f"  {kk:<28} {fmt(vv)}")
        elif isinstance(vv, dict): print(f"  {kk:<28} " + "; ".join(f"{i}: {fmt(v)}" for i, v in vv.items()))
        else: print(f"  {kk:<28} {vv}")
res["diagnostics"] = diag

# gates on the selected cell
gate = None
if win:
    d = diag[win]; st = res["cells"][win]
    g = dict(
        D1_monotone=(d["D1_k1"].get("avg_R", -9) <= d["D1_k2"].get("avg_R", -9) <= d["D1_k3plus"].get("avg_R", 9)),
        D2_placebos_below=all((d[p].get("avg_R", -9) < st["avg_R"]) and ((d[p].get("t") or 0) < 2) for p in ("D2_seasonal", "D2_stale")),
        D3_t_diff_ge2=(d["D3_t_diff"] or -9) >= 2,
        D4_nonstress=(d["D4_nonstress"].get("n", 0) >= 25 and d["D4_nonstress"].get("avg_R", -9) > 0
                      and (d.get("D4_nonstress_vs_control_diff") or -9) > 0))
    gate = g; res["gates"] = g
    print("\nGATES on", win, g)
    if all(g.values()):
        print("IS PASS on all gates. OOS remains SEALED; the integrator alone may run --unseal with UNSEAL_OK=1.")
        res["is_pass"] = True
    else:
        print("IS gate FAIL: family closes at IS; OOS not opened.")
        res["is_pass"] = False
else:
    res["is_pass"] = False
    print("Family fails at IS (no selectable cell); OOS not opened.")
res["winner"] = win
json.dump(res, open("results/r67_ftd_is.json", "w"), indent=1, default=str)

if UNSEAL and win and res.get("is_pass"):
    L, s = cells[win]
    df = pd.DataFrame(L); oo = df[df.P >= OOS_START]
    so = oo.groupby("P").R.mean(); s15 = oo.groupby("P").R15.mean()
    o = stats(so); c15 = stats(s15)
    per = {i: stats(oo[oo.idx == i].R) for i in ("SPX", "NDX", "RTY")}
    split_t1 = {"pre_T1": stats(oo[oo.P < dt.date(2024, 5, 28)].groupby("P").R.mean()),
                "post_T1": stats(oo[oo.P >= dt.date(2024, 5, 28)].groupby("P").R.mean())}
    PASS = (o.get("n", 0) >= 25 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
            and (o.get("pf") or 0) >= 1.15 and o.get("halves") == [1.0, 1.0] and (c15.get("avg_R") or -1) > 0)
    print("\n=== ONE-SHOT OOS (burned now) ===\n ", fmt(o), "\n  cost x1.5:", fmt(c15), "\n  per instrument:",
          {i: fmt(v) for i, v in per.items()}, "\n  T+1 split:", {k: fmt(v) for k, v in split_t1.items()},
          f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
    json.dump(dict(winner=win, oos=o, oos_cost15=c15, per_instrument=per, t1_split=split_t1, gate_pass=bool(PASS)),
              open("results/r67_ftd_oos.json", "w"), indent=1, default=str)
