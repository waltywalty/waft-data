"""The two pre-registered rescue filters on the Zarattini first-bar spec.

The gross edge exists on all three indices (zero-cost PF 1.13-1.20) but costs
eat it. The research said one filter has academic-grade evidence - opening
relative volume ("Stocks in Play") - and one is folklore with a mechanism
(gap alignment). Either must concentrate the gross edge ~2x to clear costs.

Caveat stated up front: CFD volume is TICK COUNT, not exchange volume, so the
rvol test is a proxy for the published filter, not a replication of it.
"""
import pandas as pd, numpy as np, warnings, json
import run_nyidx as nx                        # reuses Frame/close_trade/stats
warnings.filterwarnings("ignore")

OUT = {}
for key in ("SPX", "NDX", "RTY"):
    F = nx.Frame(key)
    # first-bar tick volume and its 14-session same-slot average, causal
    vols, days = [], []
    for d in nx.days_of(F):
        t_open, _, _, _ = F.day_times(d)
        i = F.ix.searchsorted(t_open)
        if i < len(F.ix) and F.ix[i] == t_open:
            days.append(d)
            vols.append(0.0)                  # placeholder, filled from frame
    vb = pd.Series(index=pd.DatetimeIndex(days), dtype=float)
    b = pd.read_csv(f"data/{key}_5m.csv", index_col=0, parse_dates=[0])
    b.index = pd.to_datetime(b.index, utc=True)
    for d in vb.index:
        t_open, _, _, _ = F.day_times(d)
        if t_open in b.index:
            vb[d] = float(b.at[t_open, "volume"])
    rvol = vb / vb.rolling(14).mean().shift(1)

    rows = []
    for d in nx.days_of(F):
        t_open, t_eod, _, _ = F.day_times(d)
        i = F.ix.searchsorted(t_open)
        if i >= len(F.ix) or F.ix[i] != t_open:
            continue
        o, c = F.o[i], F.c[i]
        if c == o:
            continue
        side = 1 if c > o else -1
        entry = float(c)
        stop = float(F.l[i] if side == 1 else F.h[i])
        if side * (entry - stop) <= 0:
            continue
        gap = entry - float(F.feat.at[d, "p_c"]) if np.isfinite(F.feat.at[d, "p_c"]) else np.nan
        tr = nx.close_trade(F, d, side, entry, t_open + pd.Timedelta(minutes=5),
                            stop, None, t_eod, F.cost)
        if tr:
            tr["rvol"] = float(rvol.get(d, np.nan))
            tr["gap_aligned"] = bool(np.isfinite(gap) and np.sign(gap) == side)
            rows.append(tr)
    d = pd.DataFrame(rows).dropna(subset=["rvol"])
    d["day"] = pd.to_datetime(d.day)
    pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
    q80 = d.rvol.quantile(0.8)
    print(f"\n=== {key} first-bar EoD (n={len(d)}) - rescue filters ===")
    res = {}
    for lbl, m in (("all", None),
                   (f"rvol top quintile (>= {q80:.2f})", d.rvol >= q80),
                   ("rvol bottom 4 quintiles", d.rvol < q80),
                   ("gap aligned with bar", d.gap_aligned),
                   ("gap against bar", ~d.gap_aligned)):
        x = d if m is None else d[m]
        if len(x) < 50:
            continue
        p = x.pnl
        pct = p / x.entry * 100
        t = float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0
        a = x[x.day < nx.OS_START[key]]
        bb = x[x.day >= nx.OS_START[key]]
        print(f"   {lbl:34s} n={len(x):>5} PF={pfx(p):.3f} t={t:+.2f} "
              f"PF0={pfx(p + F.cost):.3f} | IS {pfx(a.pnl):.3f} OS {pfx(bb.pnl):.3f}")
        res[lbl] = {"n": len(x), "pf": pfx(p), "t": t, "pf0": pfx(p + F.cost),
                    "is_pf": pfx(a.pnl), "os_pf": pfx(bb.pnl)}
    OUT[key] = res

json.dump(OUT, open("results/nyidx_filters.json", "w"), indent=1)
print("\nwritten: results/nyidx_filters.json")
