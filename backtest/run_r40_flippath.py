"""Round 40: extreme delta-flip path study (user chart observation).
Frozen per pre-registration in reference/goal_ledger.md.
Outputs results/r40_flippath.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]

W = 8  # path window, bars (2h on 15m)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))] if m > 4 else None


def prop_z(k1, n1, k0, n0):
    if min(n1, n0) < 10:
        return np.nan
    p1, p0 = k1 / n1, k0 / n0
    p = (k1 + k0) / (n1 + n0)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n0))
    return (p1 - p0) / se if se > 0 else np.nan


def path_measures(o, h, l, c, ii, side):
    """Per event i (side +1 bull flip / -1 bear): MFE8 (favorable excursion, bps),
    rise8 (any favorable close within W), diprise8 (adverse break of the event
    bar's extreme FIRST, then a favorable close)."""
    n = len(c)
    mfe, rise, diprise = [], [], []
    for i in ii:
        j2 = min(i + W, n - 1)
        if j2 <= i:
            continue
        hs, ls, cs = h[i + 1:j2 + 1], l[i + 1:j2 + 1], c[i + 1:j2 + 1]
        if side > 0:
            mfe.append((hs.max() / c[i] - 1) * 1e4)
            rise.append((cs > c[i]).any())
            kd = np.argmax(ls < l[i]) if (ls < l[i]).any() else -1
            diprise.append(kd >= 0 and (cs[kd:] > c[i]).any())
        else:
            mfe.append((1 - ls.min() / c[i]) * 1e4)
            rise.append((cs < c[i]).any())
            kd = np.argmax(hs > h[i]) if (hs > h[i]).any() else -1
            diprise.append(kd >= 0 and (cs[kd:] < c[i]).any())
    return np.array(mfe), np.array(rise, bool), np.array(diprise, bool)


out = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b5 = load_frame(idx)
    d5 = np.sign(b5.close - b5.open) * b5.volume
    q = b5.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                                 low=("low", "min"), close=("close", "last")).dropna(subset=["open"])
    q["delta"] = d5.resample("15min").sum().reindex(q.index)
    pct = q.delta.abs().rolling(100).rank(pct=True) * 100
    red, grn = (q.close < q.open).values, (q.close > q.open).values
    dpos, dneg = (q.delta > 0).values, (q.delta < 0).values
    prior8 = (q.close.shift(1) / q.close.shift(9) - 1).values   # trend to the PREVIOUS bar
    o, h, l, c = (q[k].values for k in ("open", "high", "low", "close"))
    fwd = {k: (np.roll(c, -k) / c - 1) * 1e4 for k in (1, 4, 8)}
    for k in fwd:
        fwd[k][-k:] = np.nan
    res = {}
    for side, sname in ((1, "bull"), (-1, "bear")):
        cand = (red if side > 0 else grn)
        dok = (dpos if side > 0 else dneg)
        for ctx, cname in ((np.ones(len(q), bool), "all"),
                           ((prior8 * side < 0), "trend")):
            base = cand & ctx & np.isfinite(pct.values)
            for th in (70, 90, 97):
                ev = base & dok & (pct.values >= th)
                cv = base & ~ev
                ei, ci = np.where(ev)[0], np.where(ci_ := cv)[0]
                r = {"n_ev": int(len(ei)), "n_ctrl": int(len(ci))}
                for k in (1, 4, 8):
                    a = side * fwd[k][ei]
                    b_ = side * fwd[k][ci]
                    a, b_ = a[np.isfinite(a)], b_[np.isfinite(b_)]
                    r[f"fwd{k}"] = dict(ev=float(a.mean()) if len(a) else np.nan,
                                        ctrl=float(b_.mean()) if len(b_) else np.nan,
                                        t=welch(a, b_), halves=halves(a))
                em, er, ed = path_measures(o, h, l, c, ei, side)
                cm, cr, cd = path_measures(o, h, l, c, ci, side)
                r["MFE8"] = dict(ev=float(em.mean()) if len(em) else np.nan,
                                 ctrl=float(cm.mean()) if len(cm) else np.nan,
                                 t=welch(em, cm), halves=halves(em))
                r["pRise8"] = dict(ev=float(er.mean()) if len(er) else np.nan,
                                   ctrl=float(cr.mean()) if len(cr) else np.nan,
                                   z=prop_z(er.sum(), len(er), cr.sum(), len(cr)))
                r["pDipRise8"] = dict(ev=float(ed.mean()) if len(ed) else np.nan,
                                      ctrl=float(cd.mean()) if len(cd) else np.nan,
                                      z=prop_z(ed.sum(), len(ed), cd.sum(), len(cd)))
                res[f"{sname} {cname} th{th}"] = r
    out[idx] = res
    print(f"{idx} done")

json.dump(out, open("results/r40_flippath.json", "w"), indent=1, default=float)
for idx, res in out.items():
    print(f"\n=== {idx} (event vs control; bps or probability) ===")
    print(f"{'cell':>16} {'n_ev':>6} | {'fwd1':>11} {'fwd4':>11} {'fwd8':>11} | {'MFE8':>13} | {'pRise8':>13} | {'pDipRise8':>13}")
    for k, v in res.items():
        f1, f4, f8, m8 = v["fwd1"], v["fwd4"], v["fwd8"], v["MFE8"]
        pr, pd_ = v["pRise8"], v["pDipRise8"]
        print(f"{k:>16} {v['n_ev']:>6} | "
              f"{f1['ev']:>+5.1f}/{f1['t']:>+4.1f} {f4['ev']:>+5.1f}/{f4['t']:>+4.1f} {f8['ev']:>+5.1f}/{f8['t']:>+4.1f} | "
              f"{m8['ev']:>5.1f}v{m8['ctrl']:>5.1f}/{m8['t']:>+4.1f} | "
              f"{pr['ev']*100:>4.1f}v{pr['ctrl']*100:>4.1f}/{pr['z']:>+4.1f} | "
              f"{pd_['ev']*100:>4.1f}v{pd_['ctrl']*100:>4.1f}/{pd_['z']:>+4.1f}")
