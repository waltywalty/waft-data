"""Round 11-A: the three requested filters on the NY opening-range breakout.

Base cells (fixed before filtering): the 15m and 30m NY ORB, follow direction,
5m close confirm within 120 min, stop at the far side, exit at the close - the
same construction the round-9 grid scored. Filters, each with terciles or a
median split and the 2020s-era sign check:

  1. impulse: opening-range width / prior ATR14 (high-low range filter)
  2. relative volume: range-window tick volume vs its 14-session average
     (tick volume on CFDs - the caveat from rounds 9/10 stands)
  3. ATR regime: prior ATR14 vs its own 1-year percentile (high/low vol)
"""
import pandas as pd, numpy as np, warnings, json
import mkts
warnings.filterwarnings("ignore")

OUT = {"cells": []}


def orb_trades(M, R, feat):
    rows = []
    vols = {}
    for d in M.days:
        day = pd.Timestamp(d)
        t0, t1 = M.nyt(day, 9, 30), M.nyt(day, 9, 30) + pd.Timedelta(minutes=R)
        j0, j1 = M.rng(t0, t1)
        if j1 - j0 < R // 5:
            continue
        rh, rl = float(M.h[j0:j1].max()), float(M.l[j0:j1].min())
        if rh <= rl:
            continue
        vols[day] = float(M.v[j0:j1].sum())
        k0, k1 = M.rng(t1, t1 + pd.Timedelta(minutes=120))
        brk = (M.c[k0:k1] > rh) | (M.c[k0:k1] < rl)
        if not brk.any():
            continue
        k = k0 + int(np.argmax(brk))
        side = 1 if M.c[k] > rh else -1
        entry = float(M.c[k])
        stop = rl if side == 1 else rh
        t_fill = M.ix[k] + pd.Timedelta(minutes=5)
        t_eod = M.nyt(day, 16)
        px, why, t_out = mkts.hit(M, M.ix.searchsorted(t_fill), M.ix.searchsorted(t_eod),
                                  side, stop, None)
        if px is None:
            px = M.at(t_eod)
            if px is None:
                continue
        f = feat.reindex([day])
        rows.append(dict(day=day, side=side, entry=entry, why=why,
                         pnl=side * (px - entry) - M.cost,
                         rsize=rh - rl, p_atr=float(f.p_atr.iloc[0])))
    df = pd.DataFrame(rows)
    vs = pd.Series(vols).sort_index()
    rvol = vs / vs.rolling(14).mean().shift(1)
    df["rvol"] = df.day.map(rvol)
    df["ratr"] = df.rsize / df.p_atr
    # ATR regime: prior ATR14 vs its rolling 1-year median (causal)
    atr = feat.p_atr.dropna()
    reg = atr / atr.rolling(252, min_periods=60).median()
    df["atr_reg"] = df.day.map(reg)
    return df


for M in mkts.load_mkts():
    feat = mkts.rth_features(M)
    print(f"\n================ {M.name} ================")
    for R in (15, 30):
        d = orb_trades(M, R, feat)
        d = d.dropna(subset=["p_atr"])
        base = d.to_dict("records")
        mkts.show(M, f"ORB {R}m follow/eod - unfiltered", base, OUT["cells"], "base")
        # 1. impulse terciles (range width / ATR)
        q = d.ratr.quantile([1 / 3, 2 / 3])
        for lbl, m in (("impulse T1 (quiet range)", d.ratr <= q.iloc[0]),
                       ("impulse T2", (d.ratr > q.iloc[0]) & (d.ratr <= q.iloc[1])),
                       ("impulse T3 (impulsive range)", d.ratr > q.iloc[1])):
            mkts.show(M, f"ORB {R}m + {lbl}", d[m].to_dict("records"), OUT["cells"], "impulse")
        # 2. relative volume terciles
        dv = d.dropna(subset=["rvol"])
        q = dv.rvol.quantile([1 / 3, 2 / 3])
        for lbl, m in (("rvol T1 (weak)", dv.rvol <= q.iloc[0]),
                       ("rvol T2", (dv.rvol > q.iloc[0]) & (dv.rvol <= q.iloc[1])),
                       ("rvol T3 (strong breakout)", dv.rvol > q.iloc[1])):
            mkts.show(M, f"ORB {R}m + {lbl}", dv[m].to_dict("records"), OUT["cells"], "rvol")
        # 3. ATR regime median split
        dr = d.dropna(subset=["atr_reg"])
        for lbl, m in (("low-vol regime (ATR < 1yr median)", dr.atr_reg < 1),
                       ("high-vol regime (ATR > 1yr median)", dr.atr_reg >= 1)):
            mkts.show(M, f"ORB {R}m + {lbl}", dr[m].to_dict("records"), OUT["cells"], "atr_regime")

print("\n=== HONEST OOS across all filtered cells ===")
sc = pd.DataFrame([c for c in OUT["cells"] if np.isfinite(c.get("os_pf", np.nan)) and c["is_n"] > 40])
top = sc.sort_values("is_t", ascending=False).head(8)
for _, r in top.iterrows():
    print(f"   {r['mkt']} {r['label']:52s} IS PF={r['is_pf']:.3f} t={r['is_t']:+.2f} | OS PF={r['os_pf']:.3f}")
print(f"   top-8 median OS PF {top.os_pf.median():.3f}; population ({len(sc)}) {sc.os_pf.median():.3f}")
OUT["isos"] = {"top8": top.to_dict("records"), "honest_median": float(top.os_pf.median()),
               "population_median": float(sc.os_pf.median()), "n_cells": int(len(sc))}
json.dump(OUT, open("results/orb_filters.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} cells. written: results/orb_filters.json")
