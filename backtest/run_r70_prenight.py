"""Round 70 attempt 50: pre-announcement night LONG before NFP and GDP (HPWZ 2022).

Frozen per reference/goal_ledger.md ("Attempt 50 registration"). Entry = OPEN of the first 5m
bar in [18:00, 19:00) ET the evening before an NFP/GDP 08:30 release; exit = CLOSE of the
08:20 bar; LONG; SPX+NDX pooled (RTY read-only); micro costs 1x/1.5x/2x plus an ES-carry
line; hard-death controls (same window on non-release nights; trading-day-matched control);
placebos, horizon checks, anchors, per-instrument and per-year prints.

OOS FIREWALL: OOS sessions are dropped at frame build (intraday_engine.sessions) unless the
integrator runs `UNSEAL_OK=1 python3 run_r70_prenight.py --unseal`. `--signal-only` stops
after the pre-checks and counts. Output results/r70_prenight_is.json (+ _oos when unsealed).
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday_engine as E  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
SIGNAL_ONLY = "--signal-only" in sys.argv
NY = "America/New_York"
SEL = ["SPX", "NDX"]            # selectable instruments; RTY read-only
DIV_YIELD = 0.018

# ---------------------------------------------------------------- calendars
raw = open("data/econ_events_us_high_fxs.json").read()
ev = json.loads(raw[raw.find("{"):])
ev = ev.get("result", ev)["events"]
def rel_dates(name):
    out = set()
    for e in ev:
        if e.get("n") != name: continue
        t = pd.Timestamp(e["d"]).tz_convert(NY)
        if t.hour * 100 + t.minute == 830:
            out.add(t.date())
    return out
NFP, GDP = rel_dates("Nonfarm Payrolls"), rel_dates("Gross Domestic Product Annualized")
ISM = {pd.Timestamp(e["d"]).tz_convert(NY).date() for e in ev if e.get("n") == "ISM Manufacturing PMI"}
fsrc = open("run_r42l_fomc.py").read()
FOMC = set(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', fsrc, re.S).group(1).split()).date)
dgs = pd.read_csv("data/fred_DGS2.csv")
dgs.columns = [c.lower() for c in dgs.columns]
dcol = [c for c in dgs.columns if "date" in c or c == "observation_date"][0]
vcol = [c for c in dgs.columns if c != dcol][0]
RATE = pd.Series(pd.to_numeric(dgs[vcol], errors="coerce").values, index=pd.to_datetime(dgs[dcol]).dt.date).dropna()


def rate_on(d):
    s = RATE[RATE.index <= d]
    return float(s.iloc[-1]) / 100 if len(s) else 0.0


# ---------------------------------------------------------------- frames
frames = {}
for idx in ("SPX", "NDX", "RTY"):
    d, b, cut = E.sessions(idx, UNSEAL)
    keys = list(d.index)
    nxt = {keys[i]: keys[i + 1] for i in range(len(keys) - 1)}
    prv = {keys[i + 1]: keys[i] for i in range(len(keys) - 1)}
    # trading day of month (position of the session within its calendar month)
    tdm = {}
    for k in keys:
        tdm[k] = 1 if (k not in prv or prv[k].month != k.month) else tdm[prv[k]] + 1
    frames[idx] = dict(d=d, b=b, cut=cut, keys=keys, nxt=nxt, prv=prv, tdm=tdm, groups=dict(tuple(b.groupby("skey"))))

FOMC_EXCL = set(FOMC)
for idx in ("SPX",):
    for k in FOMC:
        if k in frames[idx]["nxt"]: FOMC_EXCL.add(frames[idx]["nxt"][k])
UNION = (NFP | GDP) - FOMC_EXCL


def window_trade(idx, key, entry_lo, entry_hi, exit_hm, stop_atr=None, entry_prev_close=False):
    """One long trade in session `key`: entry = open of first bar with entry_lo <= hm < entry_hi
    (the hm test treats the wrapped evening as < the morning), exit = close of bar `exit_hm`.
    Returns dict or None. Costs applied later."""
    f = frames[idx]; d = f["d"]
    if key not in f["groups"] or key not in d.index: return None
    day = f["groups"][key]
    atr = d.atr20.get(key, np.nan)
    if not (np.isfinite(atr) and atr > 0): return None
    if entry_prev_close:
        if key not in f["prv"]: return None
        entry, fill = float(d.c[f["prv"][key]]), 1555
        path = day[day.hm < exit_hm] if exit_hm < 1600 else day[(day.hm >= 1800) | (day.hm < exit_hm)]
        if not len(path): return None
    else:
        ebars = day[(day.hm >= entry_lo) & (day.hm < entry_hi)]
        if not len(ebars): return None
        eb = ebars.iloc[0]; entry, fill = float(eb.open), int(eb.hm)
        if entry_lo >= 1800:
            path = day[(day.hm >= fill) | (day.hm < exit_hm)]
        else:
            path = day[(day.hm >= fill) & (day.hm < exit_hm)]
    xb = day[day.hm == exit_hm]
    if not len(xb): return None
    exit_px, how = float(xb.close.iloc[0]), "time"
    if stop_atr:
        stop_px = entry - stop_atr * atr
        for _, bar in path.iterrows():
            if bar.low <= stop_px:
                exit_px, how = stop_px, "stop"; break
    prevc = float(d.c[f["prv"][key]]) if key in f["prv"] else np.nan
    carry = (rate_on(key) - DIV_YIELD) / 252 * entry
    pnl = exit_px - entry
    c = E.MICRO[idx]
    return dict(date=key, instr=idx, entry=entry, exit=exit_px, fill=fill, how=how, atr=atr, pnl=pnl,
                gap=abs(entry - prevc) / atr if np.isfinite(prevc) else np.nan,
                R=(pnl - c) / atr, R15=(pnl - 1.5 * c) / atr, R20=(pnl - 2 * c) / atr,
                R20c=(pnl - 2 * c - carry) / atr, tdm=f["tdm"].get(key), wd=key.weekday())


def collect(dates, instrs, **kw):
    rows = [t for idx in instrs for k in sorted(dates) for t in [window_trade(idx, k, **kw)] if t]
    return pd.DataFrame(rows)


def S(df, col="R"):
    if isinstance(df, pd.Series):
        return E.stats(df) if len(df) else dict(n=0)
    return E.stats(df[col]) if len(df) else dict(n=0)


def by_date(df, col="R"):
    return df.groupby("date")[col].mean().sort_index() if len(df) else pd.Series(dtype=float)


def halves_diff(ev_s, ct_s):
    """Sign of (event mean - control mean) in each chronological half of the event series."""
    if len(ev_s) < 10 or len(ct_s) < 10: return None
    m = len(ev_s) // 2; out = []
    for part in (ev_s.iloc[:m], ev_s.iloc[m:]):
        cm = ct_s[(ct_s.index >= part.index[0]) & (ct_s.index <= part.index[-1])]
        out.append(float(np.sign(part.mean() - (cm.mean() if len(cm) else ct_s.mean()))))
    return out


def fmt(s):
    return E.fmt(s)


# ---------------------------------------------------------------- pre-checks (signal side)
allkeys = {idx: set(frames[idx]["keys"]) for idx in frames}
print(f"calendar: NFP {len(NFP)} GDP {len(GDP)} union {len(NFP | GDP)} FOMC-excluded union {len(UNION)}; "
      f"IS/OOS: {'UNSEALED' if UNSEAL else 'sealed (OOS dropped at build)'}; cuts "
      + ", ".join(f"{i} {frames[i]['cut']}" for i in frames))
C1 = dict(entry_lo=1800, entry_hi=1900, exit_hm=820)
pre = {}
for idx in ("SPX", "NDX", "RTY"):
    ks = sorted(k for k in UNION if k in allkeys[idx])
    tr = collect(ks, [idx], **C1)
    fills = tr.fill.value_counts().to_dict() if len(tr) else {}
    gaps = int((tr.gap > 0.5).sum()) if len(tr) else 0
    pre[idx] = dict(release_sessions=len(ks), with_evening_bar=int(len(tr)), fill_clock=fills, roll_gap_gt_half_atr=gaps,
                    gap_dates=[str(x) for x in tr[tr.gap > 0.5].date] if len(tr) else [])
    print(f"  {idx}: release sessions in frame {len(ks)}, with an evening entry bar {len(tr)}; fill clocks {fills}; "
          f"roll-gap > 0.5 ATR: {gaps} {pre[idx]['gap_dates'][:5]}")
if SIGNAL_ONLY:
    json.dump(dict(prechecks=pre), open("results/r70_prenight_pre.json", "w"), indent=1, default=str)
    print("--signal-only: stopping before any return is read."); raise SystemExit

# ---------------------------------------------------------------- grid (IS only unless unsealed)
def excl_gap(df):
    return df[~(df.gap > 0.5)] if len(df) else df

cells = {
    "C1": dict(dates=UNION, entry_lo=1800, entry_hi=1900, exit_hm=820),
    "C2": dict(dates=UNION, entry_lo=200, entry_hi=205, exit_hm=820),
    "C3": dict(dates=UNION, entry_lo=500, entry_hi=505, exit_hm=820),
    "C4": dict(dates=NFP - FOMC_EXCL, entry_lo=1800, entry_hi=1900, exit_hm=820),
}
res = dict(prechecks=pre, cells={}, controls={}, diagnostics={})
trades = {}
print("\n=== IS GRID (LONG, SPX+NDX pooled by leg; ATR20 units; costs 1x/1.5x/2x; +carry) ===")
for name, c in cells.items():
    kw = {k: v for k, v in c.items() if k != "dates"}
    df = excl_gap(collect(c["dates"], SEL, **kw)); trades[name] = df
    st = dict(x1=S(df), x15=S(df, "R15"), x2=S(df, "R20"), x2_carry=S(df, "R20c"), by_date=S(by_date(df)),
              per_instr={i: S(df[df.instr == i]) for i in SEL},
              per_year={int(y): round(float(g.R.mean()), 3) for y, g in df.groupby(pd.to_datetime(df.date).dt.year)} if len(df) else {})
    res["cells"][name] = st
    pi = ", ".join("%s: avgR %+.3f t %+.2f n %d" % (i, v.get("avg_R", float("nan")), v.get("t", float("nan")), v.get("n", 0))
                   for i, v in st["per_instr"].items())
    print(f"  {name}: legs {fmt(st['x1'])}\n       x1.5 {fmt(st['x15'])}\n       x2   {fmt(st['x2'])}\n       x2+c {fmt(st['x2_carry'])}\n       dates {fmt(st['by_date'])}"
          f"\n       per-instr {{{pi}}}\n       per-year {st['per_year']}")

# controls
nonrel = {idx: [k for k in frames[idx]["keys"] if k not in (NFP | GDP | ISM) and k not in FOMC_EXCL] for idx in SEL}
ctrl = pd.concat([excl_gap(collect(nonrel[i], [i], **C1)) for i in SEL], ignore_index=True)
res["controls"]["same_window_nonrelease"] = dict(x1=S(ctrl), x2=S(ctrl, "R20"), by_date=S(by_date(ctrl)))
print(f"\n  CONTROL same window, non-release non-FOMC nights: {fmt(S(ctrl))} | x2 {fmt(S(ctrl,'R20'))}")
c1 = trades["C1"]
# trading-day-matched control differential
if len(c1) and len(ctrl):
    cm = ctrl.groupby("tdm").R.mean()
    c1 = c1.assign(diff_tdm=c1.R - c1.tdm.map(cm))
    res["controls"]["tdm_matched_diff"] = S(c1, "diff_tdm")
    print(f"  C1 minus trading-day-matched control: {fmt(S(c1,'diff_tdm'))}")
    nfp = c1[c1.date.isin(NFP)]
    res["controls"]["nfp_td_split"] = {"td<=3": S(nfp[nfp.tdm <= 3]), "td>=4": S(nfp[nfp.tdm >= 4])}
    print(f"  NFP td<=3: {fmt(S(nfp[nfp.tdm<=3]))}\n  NFP td>=4: {fmt(S(nfp[nfp.tdm>=4]))}")
    wdc = ctrl.groupby("wd").R.mean().round(4).to_dict(); res["controls"]["control_by_weekday"] = wdc
    print(f"  control by weekday (Mon=0): {wdc}")
    res["controls"]["halves_diff_vs_control"] = halves_diff(by_date(c1), by_date(ctrl))
    print(f"  event-minus-control halves: {res['controls']['halves_diff_vs_control']}")

# diagnostics
diag = {}
after = excl_gap(collect(UNION, SEL, entry_lo=835, entry_hi=840, exit_hm=920)); diag["placebo_after_0835_0925"] = S(after)
sevn = {k - dt.timedelta(days=7) for k in UNION}
sev = excl_gap(collect(sevn, SEL, **C1)); diag["placebo_7days_earlier"] = S(sev)
diag["horizon_exit_0755"] = S(excl_gap(collect(UNION, SEL, entry_lo=1800, entry_hi=1900, exit_hm=750)))
diag["horizon_exit_0725"] = S(excl_gap(collect(UNION, SEL, entry_lo=1800, entry_hi=1900, exit_hm=720)))
anchor = collect(UNION, SEL, entry_lo=0, entry_hi=0, exit_hm=820, entry_prev_close=True); diag["anchor_1555_to_0825"] = S(anchor)
ism = excl_gap(collect(ISM - FOMC_EXCL, SEL, entry_lo=1800, entry_hi=1900, exit_hm=950)); diag["ism_night_1800_0955_readonly"] = S(ism)
stopc = excl_gap(collect(UNION, SEL, entry_lo=1800, entry_hi=1900, exit_hm=820, stop_atr=1.0)); diag["C1_stop_1atr"] = dict(**S(stopc), how=stopc.how.value_counts().to_dict() if len(stopc) else {})
if len(trades["C1"]):
    sc = trades["C1"].copy(); sc["Rs"] = (-sc.pnl - E.MICRO["SPX"]) / sc.atr
    diag["short_C1_mirror"] = S(sc, "Rs")
rty = excl_gap(collect(UNION, ["RTY"], **C1)); diag["RTY_readonly_C1"] = S(rty)
res["diagnostics"] = diag
print("\n--- diagnostics (read-only) ---")
for k, v in diag.items():
    print(f"  {k:<32} {fmt(v) if 'n' in v else v}")

# selection
sel = None
ranked = sorted(cells, key=lambda n: -(res["cells"][n]["x1"].get("t") or -99))
c123_pos = all((res["cells"][n]["x1"].get("avg_R") or -1) > 0 for n in ("C1", "C2", "C3"))
for n in ranked:
    st = res["cells"][n]
    if (st["by_date"].get("n", 0) >= 40 and (st["x1"].get("t") or -9) >= 2 and st["x1"].get("halves") == [1.0, 1.0]
            and (st["x2"].get("avg_R") or -1) > 0 and c123_pos):
        sel = n; break
gates = {}
if sel:
    st = res["cells"][sel]; cs = res["controls"]["same_window_nonrelease"]
    gates = dict(control_below=(cs["x1"].get("avg_R") or 9) < st["x1"]["avg_R"],
                 halves_diff=(res["controls"].get("halves_diff_vs_control") == [1.0, 1.0]),
                 tdm_diff_positive=(res["controls"].get("tdm_matched_diff", {}).get("avg_R") or -1) > 0,
                 nfp_not_td3_only=not ((res["controls"]["nfp_td_split"]["td<=3"].get("avg_R") or 0) > 0 and (res["controls"]["nfp_td_split"]["td>=4"].get("avg_R") or 0) <= 0),
                 placebo_after_below=(diag["placebo_after_0835_0925"].get("avg_R") or 9) < st["x1"]["avg_R"],
                 placebo_7d_below=(diag["placebo_7days_earlier"].get("avg_R") or 9) < st["x1"]["avg_R"])
res["selected"] = sel; res["gates"] = gates
res["is_pass"] = bool(sel and all(gates.values()))
print(f"\nSELECTION: {sel or 'none clears n>=40 dates / t>=2 / halves / 2x-cost / C1-C3>0'}; gates {gates}; "
      f"IS {'PASS - OOS sealed, integrator only' if res['is_pass'] else 'FAIL - family closes'}")
json.dump(res, open("results/r70_prenight_is.json", "w"), indent=1, default=str)

# fidelity: true ES 2h bars vs CFD on overlap nights (non-gating)
try:
    es = []
    for fn in ("ES_Z5_2h_ibkr.json", "ES_H6_2h_ibkr.json", "ES_M6_2h_ibkr.json"):
        j = json.load(open("data/" + fn)); t = pd.to_datetime(j["time"], utc=True).tz_convert(NY)
        es.append(pd.DataFrame(dict(o=j["open"], c=j["close"]), index=t))
    es = pd.concat(es).sort_index(); es = es[~es.index.duplicated()]
    es["skey"] = (es.index + pd.Timedelta(hours=8)).date; es["h"] = es.index.hour
    spx = E.load_frame("SPX"); spx = spx[spx.index >= es.index.min()]
    rows = []
    for k, g in es.groupby("skey"):
        e = g[(g.h >= 17) & (g.h < 19)]; x = g[(g.h >= 5) & (g.h < 7)]
        if not len(e) or not len(x): continue
        t0, t1 = e.index[0], x.index[-1] + pd.Timedelta(hours=2)
        cb = spx[(spx.index >= t0) & (spx.index < t1)]
        if len(cb) < 10: continue
        rows.append(dict(date=k, es=(x.c.iloc[-1] / e.o.iloc[0] - 1) * 1e4, cfd=(cb.close.iloc[-1] / cb.open.iloc[0] - 1) * 1e4,
                         rel=k in (NFP | GDP)))
    fd = pd.DataFrame(rows)
    if len(fd):
        d_ = fd.es - fd.cfd
        fid = dict(overlap_nights=int(len(fd)), mean_es_bp=float(fd.es.mean()), mean_cfd_bp=float(fd.cfd.mean()),
                   mean_diff_bp=float(d_.mean()), t_diff=float(d_.mean() / d_.std(ddof=1) * np.sqrt(len(d_))) if d_.std() > 0 else None,
                   corr=float(fd.es.corr(fd.cfd)), release_nights_in_overlap=int(fd.rel.sum()),
                   es_release_mean_bp=float(fd[fd.rel].es.mean()) if fd.rel.any() else None,
                   es_nonrelease_mean_bp=float(fd[~fd.rel].es.mean()))
        res["fidelity_es"] = fid
        print(f"\nFIDELITY true ES 2h vs CFD (~18:00->~07/08:00 NY, overlap nights): {fid}")
        json.dump(res, open("results/r70_prenight_is.json", "w"), indent=1, default=str)
except Exception as e:
    print("fidelity check skipped:", e)
