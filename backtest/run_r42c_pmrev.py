"""Round 42 attempt 2b: late-day reversal (mirror of 2's grid, per ledger).
Outputs results/r42c_pmrev.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

def build_days(idx):
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm, c, o = g.hm.values, g.close.values, g.open.values
        if len(g) < 50 or hm[0] > 935:
            continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        rows.append(dict(skey=skey, o930=o[0], c1000=lb(1000), c1500=lb(1500),
                         c1530=lb(1530), cEnd=c[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["p_first"] = d.c1000 - d.o930
    d["p_day"] = d.c1500 - d.o930
    return d

def stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r)
    p, r = p[ok], r[ok]
    if len(p) < 10:
        return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]
    m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

frames, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d = build_days(idx)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"], d["idx"], d["cost"] = d.index >= cutd, idx, MICRO[idx]
    frames[idx], split[idx] = d, str(cutd)
big = pd.concat(frames.values())

PREDS = {"first30": lambda d: d.p_first, "day": lambda d: d.p_day,
         "agree": lambda d: np.where(np.sign(d.p_first) == np.sign(d.p_day), d.p_day, np.nan)}
ENTRIES = {"15:00": "c1500", "15:30": "c1530"}
FILTS = {"none": lambda P, d: np.isfinite(P),
         "0.25atr": lambda P, d: np.isfinite(P) & (np.abs(P) >= 0.25 * d.atr20)}

rows = []
for pname, pfn in PREDS.items():
    for ename, ecol in ENTRIES.items():
        for fname, ffn in FILTS.items():
            P = pfn(big)
            m = ffn(P, big) & np.isfinite(big.atr20) & (big.atr20 > 0) & \
                np.isfinite(big[ecol]) & np.isfinite(big.cEnd) & (np.sign(P) != 0)
            side = -np.sign(P[m])                      # REVERSAL
            pnl = side * (big.cEnd[m] - big[ecol][m]) - big.cost[m]
            sub = pd.DataFrame(dict(pnl=pnl, atr=big.atr20[m], oos=big.oos[m], idx=big.idx[m]))
            rows.append(dict(pred=pname, entry=ename, filt=fname,
                             IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                             OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = None
for cand in ranked:
    nb = [r for r in rows if sum(r[k] == cand[k] for k in ("pred", "entry", "filt")) == 2
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

print("=== IS ranking (reversal, pooled ATR-normalized) ===")
for r in ranked:
    a = r["IS"]
    print(f"{r['pred']:>8} {r['entry']:>6} {r['filt']:>8} | n {a['n']:>5} WR {a['wr']*100:>5.1f}% "
          f"PF {a['pf']:>5.2f} avgR {a['avg_R']:>+7.3f} t {a['t']:>+6.2f} {a['halves']}")

if winner is None:
    print("\nNo variant selectable (no IS-positive spec passing the rule); family fails at IS, OOS not opened.")
    json.dump(dict(split=split,
                   grid=[{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42c_pmrev.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['pred']} {winner['entry']} {winner['filt']} (neighbors positive {npos})")
sub = winner["_sub"]
oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
    s = oos[oos.idx == idx]
    per[idx] = stats(s.pnl, s.atr)
    v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
extra = oos.idx.map(MICRO) * 0.5
c15 = stats(oos.pnl - extra, oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split,
               grid=[{k: v for k, v in r.items() if k != "_sub"} for r in rows],
               winner={k: winner[k] for k in ("pred", "entry", "filt", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42c_pmrev.json", "w"), indent=1, default=float)
