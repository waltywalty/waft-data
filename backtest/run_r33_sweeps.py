"""Round 33 Phase 4a: index sweep-failure validation (footprint #6).

Frozen design per the pre-registration in reference/goal_ledger.md:
first breach per level per session; failure = 5m close back inside within
6 bars; descriptive forward stats for all six level classes, tradeable sim
(failure-close entry, sweep-extreme stop, EOD exit, house costs) for
PDH/PDL/ONH/ONL. Instruments SPX/NDX 2005-2025, RTY 2005-2020.
Outputs results/r33_sweeps.json.
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

COST = {"SPX": 0.6, "NDX": 2.0, "RTY": 0.4}
K = 6            # failure window, bars
FWD = 6          # descriptive forward window, bars


def sessions(idx):
    b = index_data.load(idx).tz_convert("America/New_York")
    b = b[b.index.dayofweek < 5].copy()
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date
    b["hm"] = b.index.hour * 100 + b.index.minute
    return b.groupby("skey")


def scan(idx):
    desc_rows, trade_rows = [], []
    prev_rth = None
    for skey, g in sessions(idx):
        on = g[(g.hm >= 1600) | (g.hm < 930)]
        rth = g[(g.hm >= 930) & (g.hm <= 1555)]
        if len(rth) < 40:
            prev_rth = rth if len(rth) else prev_rth
            continue
        levels = {}
        if prev_rth is not None and len(prev_rth) > 40:
            levels["PDH"] = (prev_rth.high.max(), +1, 0)
            levels["PDL"] = (prev_rth.low.min(), -1, 0)
        if len(on) > 20:
            levels["ONH"] = (on.high.max(), +1, 0)
            levels["ONL"] = (on.low.min(), -1, 0)
        levels["ORH"] = (rth.high.iloc[:6].max(), +1, 6)
        levels["ORL"] = (rth.low.iloc[:6].min(), -1, 6)
        prev_rth = rth
        arr = rth[["open", "high", "low", "close"]].values
        n = len(arr)
        for lname, (lvl, up, start) in levels.items():
            if not np.isfinite(lvl):
                continue
            bi = None
            for i in range(start, n):
                if (up > 0 and arr[i][1] > lvl) or (up < 0 and arr[i][2] < lvl):
                    bi = i; break
            if bi is None:
                continue
            fj = None
            for j in range(bi, min(bi + K + 1, n)):
                if (up > 0 and arr[j][3] < lvl) or (up < 0 and arr[j][3] > lvl):
                    fj = j; break
            failed = fj is not None
            row = dict(skey=str(skey), level=lname, failed=failed)
            if failed and fj + 1 < n:
                d = -up                        # reversal direction
                e = arr[fj][3]
                seg = arr[bi:fj + 1]
                ext = seg[:, 1].max() if up > 0 else seg[:, 2].min()
                f30 = arr[min(fj + FWD, n - 1)][3]
                row["fwd30"] = d * (f30 - e) / e * 1e4
                row["fwdEOD"] = d * (arr[-1][3] - e) / e * 1e4
                if lname in ("PDH", "PDL", "ONH", "ONL"):
                    px = None
                    for op, h, l, c in arr[fj + 1:]:
                        if (d > 0 and l <= ext) or (d < 0 and h >= ext):
                            px = ext; break
                    if px is None:
                        px = arr[-1][3]
                    trade_rows.append(dict(skey=str(skey), level=lname,
                                           pnl=d * (px - e) - COST[idx],
                                           risk=abs(e - ext) + 1e-9))
            desc_rows.append(row)
    return pd.DataFrame(desc_rows), pd.DataFrame(trade_rows)


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan


out = {}
for idx in ("SPX", "NDX", "RTY"):
    D, T = scan(idx)
    res = {}
    for lname, sub in D.groupby("level"):
        f = sub[sub.failed]
        r = dict(breaches=int(len(sub)), fail_rate=float(sub.failed.mean()))
        if "fwd30" in f and f.fwd30.notna().sum() > 10:
            v30, veod = f.fwd30.dropna(), f.fwdEOD.dropna()
            r |= dict(fwd30_bps=float(v30.mean()), fwd30_t=tstat(v30),
                      fwdEOD_bps=float(veod.mean()), fwdEOD_t=tstat(veod))
        res[lname] = r
    tr = {}
    for lname, sub in T.groupby("level"):
        p = sub.pnl
        m = len(p) // 2
        h1, h2 = p.iloc[:m], p.iloc[m:]
        w, l = p[p > 0], p[p <= 0]
        tr[lname] = dict(n=int(len(p)), wr=float((p > 0).mean()),
                         pf=float(w.sum() / abs(l.sum())) if len(l) else np.inf,
                         avg_pts=float(p.mean()), t=tstat(p),
                         r_mult=float((sub.pnl / sub.risk).mean()),
                         halves_sign=[float(np.sign(h1.mean())), float(np.sign(h2.mean()))])
    out[idx] = dict(descriptive=res, tradeable=tr)

json.dump(out, open("results/r33_sweeps.json", "w"), indent=1, default=float)

for idx in out:
    print(f"\n=== {idx} ===")
    print(f"{'level':>5} {'breach':>7} {'fail%':>6} {'fwd30':>7} {'t':>6} {'fwdEOD':>8} {'t':>6}")
    for ln, r in sorted(out[idx]["descriptive"].items()):
        if "fwd30_bps" in r:
            print(f"{ln:>5} {r['breaches']:>7} {r['fail_rate']*100:>5.1f}% {r['fwd30_bps']:>+6.1f}b "
                  f"{r['fwd30_t']:>+6.2f} {r['fwdEOD_bps']:>+7.1f}b {r['fwdEOD_t']:>+6.2f}")
        else:
            print(f"{ln:>5} {r['breaches']:>7} {r['fail_rate']*100:>5.1f}%   (n too small)")
    print(f"{'trade':>5} {'n':>7} {'WR':>6} {'PF':>6} {'avg pts':>8} {'t':>6} {'halves':>10}")
    for ln, r in sorted(out[idx]["tradeable"].items()):
        print(f"{ln:>5} {r['n']:>7} {r['wr']*100:>5.1f}% {r['pf']:>6.2f} {r['avg_pts']:>+8.2f} "
              f"{r['t']:>+6.2f} {str(r['halves_sign']):>10}")
