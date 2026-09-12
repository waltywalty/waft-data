"""Round 72A step 3, attempt 15 (r42o_asiatone): REVERSED cell at IS ONLY.
Reversed = fade the concordant Asia move (short US if Asia up, long if Asia down).
Reuses run_r42o_asiatone.py build logic verbatim (asia_daily, frames, cut); OOS rows are
dropped the moment the cut is computed. Never opens any *oos* file. Run from backtest/.
"""
import pandas as pd, numpy as np, json, warnings, os, sys
warnings.filterwarnings("ignore")
os.chdir("/home/user/waft-data/backtest"); sys.path.insert(0, "/home/user/waft-data/backtest")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}   # runner's cost, index points per round trip

def asia_daily(name):   # verbatim from the runner (corrected 08:00 UTC cutoff)
    df = pd.read_csv(f"data/{name}")
    ts = pd.to_datetime(df.datetime, utc=True)
    s = pd.Series(df.close.values, index=ts).sort_index()
    s = s[s.index.hour <= 8]
    d = s.groupby(s.index.date).last()
    r = pd.Series(d).pct_change()
    sig = r.rolling(20).std()
    return r, sig

rj, sj = asia_daily("JP225_H1.csv")
rh, sh = asia_daily("HK33_H1.csv")

def st(pnl, atr):
    p = np.asarray(pnl, float); r = p / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 2: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avgR=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else float("nan"),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se)

frames = {}
for idx in MICRO:
    rth = rth_of(load_frame(idx))
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        if len(g) < 50 or hm[0] > 935: continue
        m12 = np.where(hm < 1200)[0]
        rows_d.append(dict(skey=skey, o=g.open.values[0],
                           c12=g.close.values[m12[-1]] if len(m12) else np.nan,
                           cEnd=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    for col, ser in (("rj", rj), ("rh", rh), ("sj", sj), ("sh", sh)):
        d[col] = pd.to_numeric(d.index.map(lambda k: ser.get(k, np.nan)), errors="coerce")
    d = d[np.isfinite(d.rj) & np.isfinite(d.rh) & np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]     # runner's IS cut, identical formula
    print(f"IS CUT {idx}: {cutd}  (joined sessions {len(d)}, IS rows {int((d.index < cutd).sum())})")
    d = d[d.index < cutd].copy()                     # OOS FIREWALL: drop holdout now
    # stale-signal placebo: previous joined session's Asia returns (shifted one session)
    for col in ("rj", "rh", "sj", "sh"):
        d[col + "_lag"] = d[col].shift(1)
    d["idx"] = idx
    d["year"] = [k.year for k in d.index]
    frames[idx] = d

HOLDS = (("c12", "0930-1200"), ("cEnd", "0930-close"))

def cell(k, xcol, mult=None, lag=False, band=None, sign_src="agree", cost_x=1.0):
    """Reversed-direction trades pooled across indices. mult: both |ret|>=mult*sigma
    (None = any). band=(lo,hi): concordant AND lo<=min(|z|)<hi ... uses both-z-in-band.
    sign_src: 'agree' (concordant, direction=-common sign), 'disagree_j' (discordant,
    direction=-sign(Nikkei)), 'disagree_h' (discordant, direction=-sign(HSI))."""
    out = []
    for idx, d in frames.items():
        a, b, sa, sb = (d.rj_lag, d.rh_lag, d.sj_lag, d.sh_lag) if lag else (d.rj, d.rh, d.sj, d.sh)
        fin = np.isfinite(a) & np.isfinite(b) & np.isfinite(d[xcol])
        if sign_src == "agree":
            m = fin & (np.sign(a) == np.sign(b)) & (np.sign(a) != 0)
            side_reg = np.sign(a)
        else:
            m = fin & (np.sign(a) != np.sign(b)) & (np.sign(a) != 0) & (np.sign(b) != 0)
            side_reg = np.sign(a) if sign_src == "disagree_j" else np.sign(b)
        if mult is not None:
            m &= (a.abs() >= mult * sa) & (b.abs() >= mult * sb)
        if band is not None:
            za, zb = a.abs() / sa, b.abs() / sb
            m &= (za >= band[0]) & (za < band[1]) & (zb >= band[0]) & (zb < band[1])
        side = -side_reg[m]                                   # REVERSED
        pnl = side * (d[xcol][m] - d.o[m]) - cost_x * MICRO[idx]
        out.append(pd.DataFrame(dict(pnl=pnl, atr=d.atr20[m], idx=idx, year=d.year[m], side=side,
                                     ctl_long=(d[xcol][m] - d.o[m]) - cost_x * MICRO[idx])))
    return pd.concat(out)

def control(xcol, cost_x=1.0):
    out = []
    for idx, d in frames.items():
        m = np.isfinite(d[xcol])
        out.append(pd.DataFrame(dict(pnl=(d[xcol][m] - d.o[m]) - cost_x * MICRO[idx], atr=d.atr20[m],
                                     idx=idx, year=d.year[m])))
    return pd.concat(out)

def yearsigns(df):
    g = (df.pnl / df.atr).groupby(df.year).mean()
    return " ".join(f"{y}:{'+' if v > 0 else '-'}" for y, v in g.items())

res = {"is_cut": {}, "cells": {}, "control": {}, "gradient": {}, "placebo": {}}
print("\n=== REVERSED cells at IS (fade concordant Asia move), costs subtracted ===")
print(f"{'filt':>7} {'hold':>11} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR1x':>8} {'t1x':>6} {'avgR1.5':>8} {'avgR2x':>8} {'t2x':>6} {'halves':>12} fracLong")
for mult, fname in ((None, "any"), (0.5, "0.5sig")):
    for xcol, hname in HOLDS:
        c1, c15, c2 = (cell(None, xcol, mult, cost_x=x) for x in (1.0, 1.5, 2.0))
        s1, s15, s2 = st(c1.pnl, c1.atr), st(c15.pnl, c15.atr), st(c2.pnl, c2.atr)
        ctl = control(xcol)
        sc = st(ctl.pnl, ctl.atr)
        dW, tW = welch(c1.pnl / c1.atr, ctl.pnl / ctl.atr)
        pr = (c1.pnl - c1.ctl_long) / c1.atr                       # paired on cell days vs always-long
        tP = float(pr.mean() / pr.std(ddof=1) * np.sqrt(len(pr)))
        cS = control(xcol); sS = st(-cS.pnl - 2 * cS.idx.map(MICRO), cS.atr)  # always-short (pnl=-(x-o)-cost)
        dWs, tWs = welch(c1.pnl / c1.atr, (-(cS.pnl + cS.idx.map(MICRO)) - cS.idx.map(MICRO)) / cS.atr)
        key = f"{fname}|{hname}"
        res["cells"][key] = dict(x1=s1, x15=s15, x2=s2, frac_long=float((c1.side > 0).mean()),
                                 per_year=yearsigns(c1), per_idx={i: st(g.pnl, g.atr) for i, g in c1.groupby("idx")},
                                 ctl_long=sc, ctl_short=sS,
                                 diff_vs_long_welch=dict(avgR=dW, t=tW), diff_vs_long_paired=dict(avgR=float(pr.mean()), t=tP, n=int(len(pr))),
                                 diff_vs_short_welch=dict(avgR=dWs, t=tWs))
        print(f"{fname:>7} {hname:>11} | {s1['n']:>5} {s1['wr']*100:>5.1f}% {s1['pf']:>5.2f} {s1['avgR']:>+8.4f} {s1['t']:>+6.2f} "
              f"{s15['avgR']:>+8.4f} {s2['avgR']:>+8.4f} {s2['t']:>+6.2f} {str(s1['halves']):>12} {res['cells'][key]['frac_long']:.2f}")
        print(f"          per-year: {res['cells'][key]['per_year']}")
        print(f"          per-idx : " + "  ".join(f"{i} n{v['n']} avgR{v['avgR']:+.3f} t{v['t']:+.2f}" for i, v in res["cells"][key]["per_idx"].items()))
        print(f"          CONTROL always-long {hname}: n {sc['n']} avgR {sc['avgR']:+.4f} t {sc['t']:+.2f} | always-short: avgR {sS['avgR']:+.4f} t {sS['t']:+.2f}")
        print(f"          reversed - always-long: Welch d {dW:+.4f} t {tW:+.2f}; paired(cell days) d {pr.mean():+.4f} t {tP:+.2f} n {len(pr)}")
        print(f"          reversed - always-short: Welch d {dWs:+.4f} t {tWs:+.2f}")

print("\n=== GRADIENT: sigma-threshold ladder (both |ret| >= k x own 20d sigma), REVERSED, 1x cost ===")
for xcol, hname in HOLDS:
    print(f"  hold {hname}:")
    for k in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
        c = cell(None, xcol, k if k > 0 else None)
        s = st(c.pnl, c.atr)
        res["gradient"][f"{hname}|k={k}"] = s
        print(f"    k={k:<4} n {s['n']:>5} avgR {s['avgR']:+.4f} t {s['t']:+.2f} PF {s['pf']:.2f} halves {s['halves']}")

print("\n=== PLACEBOS (reversed) ===")
for xcol, hname in HOLDS:
    for mult, fname in ((None, "any"), (0.5, "0.5sig")):
        c = cell(None, xcol, mult, lag=True); s = st(c.pnl, c.atr)
        res["placebo"][f"stale-1session|{fname}|{hname}"] = s
        print(f"  stale (t-1 session) signal, {fname:>6} {hname}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
    c = cell(None, xcol, None, band=(0.0, 0.5)); s = st(c.pnl, c.atr)
    res["placebo"][f"subthreshold-band-0to0.5sig|{hname}"] = s
    print(f"  sub-threshold band (both |z|<0.5), {hname}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
    for ss in ("disagree_j", "disagree_h"):
        c = cell(None, xcol, None, sign_src=ss); s = st(c.pnl, c.atr)
        res["placebo"][f"discordant-{ss}|{hname}"] = s
        print(f"  discordant days, fade {'Nikkei' if ss.endswith('j') else 'HSI'} sign, {hname}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")

json.dump(res, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_15.json", "w"), indent=1, default=float)
print("\nIS-only. No OOS rows were used; no *oos* file opened.")
