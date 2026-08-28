"""Round 42 attempt 9: VIX term-structure gated intraday dip-buy (frozen per
goal_ledger.md). Outputs results/r42i_vixdip.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

def loadvix(name):
    df = pd.read_csv(f"data/{name}")
    d = pd.to_datetime(df.DATE, format="mixed")
    return pd.Series(df.CLOSE.values, index=d.dt.date)

vix, vix3 = loadvix("VIX_daily_github.csv"), loadvix("VIX3M_daily_github.csv")
common = vix.index.intersection(vix3.index)
ratio = (vix[common] / vix3[common])
ratio_prior = ratio.shift(1).dropna()          # prior day's state

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

frames, split = {}, {}
for idx in MICRO:
    rth = rth_of(load_frame(idx))
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        if len(g) < 50 or hm[0] > 935: continue
        m12 = np.where(hm < 1200)[0]
        if not len(m12): continue
        rows_d.append(dict(skey=skey, o=g.open.values[0], c12=g.close.values[m12[-1]],
                           cEnd=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["ratio"] = pd.Series(d.index.map(lambda k: ratio_prior.get(k, np.nan)), index=d.index)
    d = d[np.isfinite(d.ratio) & np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    d["idx"] = idx
    frames[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} joined sessions, OOS from {cutd}")

GATES = {"none": lambda d: np.ones(len(d), bool),
         "contango": lambda d: d.ratio.values <= 0.95,
         "backwd": lambda d: d.ratio.values >= 1.0}
rows = []
for k in (0.3, 0.5):
    for gname, gfn in GATES.items():
        subs = []
        for idx, d in frames.items():
            dip = (d.c12 - d.o) <= -k * d.atr20
            m = dip & gfn(d)
            s = d[m]
            subs.append(pd.DataFrame(dict(pnl=s.cEnd - s.c12 - MICRO[idx],
                                          atr=s.atr20, oos=s.oos, idx=idx)))
        sub = pd.concat(subs, ignore_index=True)
        rows.append(dict(k=k, gate=gname,
                         IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (indices pooled, ATR-normalized) ===")
print(f"{'k':>4} {'gate':>9} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['k']:>4} {r['gate']:>9} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("k", "gate")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42i_vixdip.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: k{winner['k']} {winner['gate']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
    s = oos[oos.idx == idx]; per[idx] = stats(s.pnl, s.atr); v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("k", "gate", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42i_vixdip.json", "w"), indent=1, default=float)
