"""Round 73: provenance check of a 1-minute index CFD frame (Dukascopy) against TRUE ES futures.

Question (data limit #7, Round 70): the MT5-era CFD's overnight path is not the futures' path
(+0.8 bp vs +12.6 bp per night on 124 overlap nights, corr 0.48). Does the Dukascopy CFD track
ES overnight? Checks, all descriptive, no strategy returns:
  A. per-night 18:00 -> 07:00 NY move, CFD vs true ES 2h/1h bars (the Round 70 test, same code path)
  B. per-night move on the 5m overlap week (es_5m_2026-09-09.json), 18:00 -> 09:25 NY
  C. RTH 09:30 -> 16:00 move, CFD vs the existing SPX CFD 5m frame (index_data) where both exist
  D. the 16:00 -> 18:00 post-close block and the Sunday 18:00 reopen gap, CFD vs ES 5m (overlap week)
  E. trading-hours profile of the CFD (active bars by NY hour)
Usage: python3 check_idx_provenance.py data/idx/dukascopy/USA500IDXUSD_1m.csv  -> results/r73_idx_provenance.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import index_data  # noqa: E402

NY = "America/New_York"
path = sys.argv[1] if len(sys.argv) > 1 else "data/idx/dukascopy/USA500IDXUSD_1m.csv"
cfd = pd.read_csv(path, parse_dates=["time"]).set_index("time").tz_convert(NY)
cfd = cfd[cfd.volume > 0]
cfd["skey"] = (cfd.index + pd.Timedelta(hours=8)).date
print(f"CFD {path}: {len(cfd)} active bars {cfd.index.min()} -> {cfd.index.max()}")
res = dict(file=path, active_bars=int(len(cfd)), first=str(cfd.index.min()), last=str(cfd.index.max()))


def mv(px, t0, t1, col_o="open", col_c="close"):
    w = px[(px.index >= t0) & (px.index < t1)]
    if len(w) < 5:
        return np.nan
    return float((w[col_c].iloc[-1] / w[col_o].iloc[0] - 1) * 1e4)


def paired(rows, a, b):
    fd = pd.DataFrame(rows)
    if not len(fd):
        return dict(n=0)
    d = fd[a] - fd[b]
    return dict(n=int(len(fd)), mean_a_bp=float(fd[a].mean()), mean_b_bp=float(fd[b].mean()), mean_diff_bp=float(d.mean()),
                t_diff=float(d.mean() / d.std(ddof=1) * np.sqrt(len(d))) if d.std(ddof=1) > 0 else None,
                corr=float(fd[a].corr(fd[b])), mad_bp=float(d.abs().mean()))


# A. true ES 2h/1h bars
es = []
for fn in ("ES_Z5_2h_ibkr.json", "ES_H6_2h_ibkr.json", "ES_M6_2h_ibkr.json", "ES_U6_1h_ibkr.json"):
    j = json.load(open("data/" + fn)); t = pd.to_datetime(j["time"], utc=True).tz_convert(NY)
    es.append(pd.DataFrame(dict(open=j["open"], close=j["close"]), index=t))
es = pd.concat(es).sort_index(); es = es[~es.index.duplicated()]
es["skey"] = (es.index + pd.Timedelta(hours=8)).date; es["h"] = es.index.hour
rows = []
for k, g in es.groupby("skey"):
    e = g[(g.h >= 17) & (g.h < 19)]; x = g[(g.h >= 5) & (g.h < 7)]
    if not len(e) or not len(x):
        continue
    t0 = e.index[0]; t1 = x.index[-1] + pd.Timedelta(hours=2 if (x.index[-1] in es.index and True) else 1)
    c = mv(cfd, t0, t1)
    if np.isnan(c):
        continue
    rows.append(dict(date=str(k), es=(x.close.iloc[-1] / e.open.iloc[0] - 1) * 1e4, cfd=c))
res["A_overnight_vs_ES_2h"] = paired(rows, "es", "cfd")
print("A overnight CFD vs ES 2h/1h:", res["A_overnight_vs_ES_2h"])

# B/D. 5m overlap week
j = json.load(open("data/forward/es_5m_2026-09-09.json")); t = pd.to_datetime(j["time"], utc=True).tz_convert(NY)
e5 = pd.DataFrame(dict(open=j["open"], close=j["close"]), index=t); e5["skey"] = (e5.index + pd.Timedelta(hours=8)).date
rows_b, rows_d = [], []
for k, g in e5.groupby("skey"):
    d0 = pd.Timestamp(k, tz=NY)
    for name, (t0, t1) in dict(night=(d0 - pd.Timedelta(hours=6), d0 + pd.Timedelta(hours=9, minutes=25)),
                              postclose=(d0 - pd.Timedelta(hours=8), d0 - pd.Timedelta(hours=7, minutes=45)),
                              rth=(d0 + pd.Timedelta(hours=9, minutes=30), d0 + pd.Timedelta(hours=16))).items():
        a, b = mv(e5, t0, t1), mv(cfd, t0, t1)
        if not (np.isnan(a) or np.isnan(b)):
            (rows_b if name == "night" else rows_d).append(dict(date=str(k), window=name, es=a, cfd=b))
res["B_overnight_vs_ES_5m_week"] = paired(rows_b, "es", "cfd")
res["D_postclose_and_rth_vs_ES_5m_week"] = [dict(r, diff=r["es"] - r["cfd"]) for r in rows_d]
sun = e5[(e5.index.dayofweek == 6) & (e5.index.hour == 18) & (e5.index.minute == 0)]
res["D_sunday_reopen"] = []
for ts in sun.index:
    prev_es = e5[e5.index < ts].close.iloc[-1]; gap_es = (sun.loc[ts, "open"] / prev_es - 1) * 1e4
    c = cfd[(cfd.index >= ts) & (cfd.index < ts + pd.Timedelta(minutes=5))]
    pc = cfd[cfd.index < ts]
    if len(c) and len(pc):
        res["D_sunday_reopen"].append(dict(ts=str(ts), es_gap_bp=float(gap_es), cfd_gap_bp=float((c.open.iloc[0] / pc.close.iloc[-1] - 1) * 1e4),
                                           cfd_first_bar=str(c.index[0]), cfd_last_before=str(pc.index[-1])))
print("B night (5m week):", res["B_overnight_vs_ES_5m_week"]); print("D:", res["D_postclose_and_rth_vs_ES_5m_week"], res["D_sunday_reopen"])

# C. RTH vs the existing CFD SPX 5m frame
spx = index_data.load("SPX").tz_convert(NY); spx = spx[spx.index >= cfd.index.min()]
rows = []
for k in sorted(set(cfd.skey)):
    d0 = pd.Timestamp(k, tz=NY); t0, t1 = d0 + pd.Timedelta(hours=9, minutes=30), d0 + pd.Timedelta(hours=16)
    a, b = mv(spx, t0, t1), mv(cfd, t0, t1)
    if not (np.isnan(a) or np.isnan(b)):
        rows.append(dict(date=str(k), mt5=a, duka=b))
res["C_rth_vs_mt5_cfd"] = paired(rows, "mt5", "duka")
print("C RTH MT5-CFD vs Dukascopy-CFD:", res["C_rth_vs_mt5_cfd"])

# E. hours profile
wk = cfd[cfd.index.dayofweek < 5]
prof = wk.groupby(wk.index.hour).size() / max(1, wk.index.normalize().nunique())
res["E_active_bars_per_NY_hour_weekday"] = {int(h): round(float(v), 1) for h, v in prof.items()}
sund = cfd[cfd.index.dayofweek == 6]
res["E_sunday_bars"] = int(len(sund)); res["E_sunday_first"] = str(sund.index.min()) if len(sund) else None
print("E hours:", res["E_active_bars_per_NY_hour_weekday"], "sunday bars", res["E_sunday_bars"])
json.dump(res, open("results/r73_idx_provenance.json", "w"), indent=1, default=str)
print("wrote results/r73_idx_provenance.json")
