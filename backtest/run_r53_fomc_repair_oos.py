"""Round 53 attempt 34: the ONE OOS shot for the FOMC horizon-match repair.
Runs ONLY the IS-selected cell (C1_ON: prev 15:55 close -> statement-day
09:30 open, LONG, 1 RT) on the sealed last-25% rows. The FOMC family burns
permanently after this run, pass or fail.
Outputs results/r53_fomc_repair_oos.json."""
import pandas as pd, numpy as np, json, warnings, re
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

lsrc = open("run_r42l_fomc.py").read()
FOMC = set(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', lsrc, re.S).group(1).split()).date)


def stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


subs = []
for idx in MICRO:
    rth = rth_of(load_frame(idx))
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        if len(g) < 50 or hm[0] > 935 or skey < pd.Timestamp("2013-01-01").date():
            continue
        rows_d.append(dict(skey=skey, o=g.open.values[0], cEnd=g.close.values[-1],
                           hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prev_cEnd"] = d.cEnd.shift(1)
    d["fomc"] = [k in FOMC for k in d.index]
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    oos = d[d.index >= cutd]                     # the sealed rows, opened NOW, once
    m = oos.fomc & np.isfinite(oos.prev_cEnd)
    s = oos[m]
    subs.append(pd.DataFrame(dict(pnl=s.o - s.prev_cEnd - MICRO[idx], atr=s.atr20, idx=idx)))
    print(f"{idx}: OOS from {cutd}, {int(m.sum())} FOMC events in holdout")

sub = pd.concat(subs, ignore_index=True)
o = stats(sub.pnl, sub.atr)
c15 = stats(sub.pnl - 0.5 * sub.idx.map(MICRO), sub.atr)
print("\n=== ONE-SHOT OOS: C1_ON long, indices pooled (family burns now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in MICRO:
    s = sub[sub.idx == idx]
    per[idx] = stats(s.pnl, s.atr)
    v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(cell="C1_ON", oos_pooled=o, oos_per_instrument=per, oos_cost15=c15,
               gate_pass=bool(PASS)),
          open("results/r53_fomc_repair_oos.json", "w"), indent=1, default=float)
