"""Attempt 5b: the single OOS evaluation for large-CONT/1000/eod, per the
disclosed amendment in the ledger. Outputs results/r42e_oos.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

def stats(pnl, atr):
    p = np.asarray(pnl, float); r = p / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r)//2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum()/abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean()/r.std()*np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

pnls, atrs, ooss, idxs = [], [], [], []
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    rth = rth_of(load_frame(idx))
    daily = rth.groupby("skey").agg(o=("open","first"), c=("close","last"),
                                    hi=("high","max"), lo=("low","min"))
    daily["atr20"] = (daily.hi - daily.lo).rolling(20).mean().shift(1)
    daily["prevc"] = daily.c.shift(1)
    keys = [k for k, g in rth.groupby("skey") if len(g) >= 50]
    cutd = sorted(daily.index)[int(len(daily) * 0.75)]
    for skey, g in rth.groupby("skey"):
        d = daily.loc[skey]
        if len(g) < 50 or not np.isfinite(d.atr20) or d.atr20 <= 0 or not np.isfinite(d.prevc):
            continue
        gap = d.o - d.prevc
        gn = abs(gap) / d.atr20
        if gn < 0.7: continue
        side = np.sign(gap)
        if side == 0: continue
        arr = g[["open","high","low","close"]].values; hm = g.hm.values
        pre = np.where(hm < 1000)[0]; post = np.where(hm >= 1000)[0]
        if not len(pre) or not len(post): continue
        tgt0 = d.o + side * abs(gap)
        seg = arr[pre]
        if (side > 0 and seg[:,1].max() >= tgt0) or (side < 0 and seg[:,2].min() <= tgt0):
            continue
        e = arr[pre[-1]][3]
        s_px = e - side * 0.5 * d.atr20
        px = None
        for k in range(post[0], len(arr)):
            o_, h_, l_, c_ = arr[k]
            if (side > 0 and l_ <= s_px) or (side < 0 and h_ >= s_px):
                px = s_px; break
        if px is None: px = arr[-1][3]
        pnls.append(side*(px - e) - MICRO[idx]); atrs.append(d.atr20)
        ooss.append(skey >= cutd); idxs.append(idx)
sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
is_ = sub[~sub.oos]; oos = sub[sub.oos]
print("IS check:", stats(is_.pnl, is_.atr))
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in MICRO:
    s = oos[oos.idx == idx]; per[idx] = stats(s.pnl, s.atr); v = per[idx]
    if v.get("n",0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
c15 = stats(oos.pnl - 0.5*oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n",0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(is_check=stats(is_.pnl, is_.atr), oos_pooled=o, oos_per_instrument=per,
               oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42e_oos.json", "w"), indent=1, default=float)
