"""Round 42 attempt 14: conditional month-end rebalancing flow (frozen per
goal_ledger.md). Outputs results/r42n_monthend.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

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
    daily = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                    hi=("high", "max"), lo=("low", "min"))
    daily["atr20"] = (daily.hi - daily.lo).rolling(20).mean().shift(1)
    daily.index = pd.to_datetime(pd.Series(daily.index).astype(str))
    daily["ym"] = daily.index.to_period("M")
    cutd = daily.index[int(len(daily) * 0.75)]
    daily["oos"] = daily.index >= cutd
    frames[idx] = daily
    split[idx] = str(cutd.date())

rows = []
for thr in (0.015, 0.03):
    for ent, ename in ((-3, "T-3"), (-2, "T-2")):
        subs = []
        for idx, daily in frames.items():
            pnls, atrs, ooss = [], [], []
            for ym, g in daily.groupby("ym"):
                if len(g) < 8:
                    continue
                mopen = g.o.iloc[0]
                t3c = g.c.iloc[-3]                      # MTD measured to T-3 close
                mtd = t3c / mopen - 1
                if abs(mtd) < thr:
                    continue
                e = g.c.iloc[ent]                       # entry close (T-3 or T-2)
                x = g.c.iloc[-1]                        # month-end close
                a20 = g.atr20.iloc[ent]
                if not np.isfinite(a20) or a20 <= 0:
                    continue
                side = -np.sign(mtd)
                pnls.append(side * (x - e) - MICRO[idx])
                atrs.append(a20)
                ooss.append(bool(g.oos.iloc[-1]))
            subs.append(pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idx)))
        sub = pd.concat(subs, ignore_index=True)
        rows.append(dict(thr=thr, entry=ename,
                         IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("=== IS grid (indices pooled, ATR-normalized) ===")
print(f"{'thr':>5} {'entry':>5} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['thr']:>5} {r['entry']:>5} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 100],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("thr", "entry")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42n_monthend.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: thr {winner['thr']} entry {winner['entry']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("thr", "entry", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42n_monthend.json", "w"), indent=1, default=float)
