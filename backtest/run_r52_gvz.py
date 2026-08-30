"""Round 52 attempt 33: gold vol-shock reversal via GVZ (frozen per
reference/goal_ledger.md). 4 selectable cells + crush diagnostics, gold
only, scarce-event floors. Outputs results/r52_gvz.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
COST = 0.35

gv = pd.read_csv("data/GVZ_history_cboe.csv")
gvz = pd.Series(gv.GVZ.values, index=pd.to_datetime(gv.DATE).dt.date)
dlog = np.log(gvz).diff()
z = dlog / dlog.rolling(63).std().shift(1)
print(f"GVZ: {len(gvz)} days {gvz.index[0]}..{gvz.index[-1]}; "
      f"z>=1.5: {(z >= 1.5).sum()}, z>=2: {(z >= 2).sum()}, crush z<=-1.5: {(z <= -1.5).sum()}")

rth = rth_of(load_frame("GOLD"))
d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                            hi=("high", "max"), lo=("low", "min"))
d = d[np.isfinite(d.o) & np.isfinite(d.c)]
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
keys = d.index.tolist()
kpos = {k: i for i, k in enumerate(keys)}
cutd = keys[int(len(keys) * 0.75)]
d["oos"] = np.array([k >= cutd for k in keys])
print(f"GOLD: {len(d)} sessions {keys[0]}..{keys[-1]}, OOS from {cutd}")


def stats(pnl, atr, min_n=10):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < min_n: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


CELLS = [("shock", thr, hold) for thr in (1.5, 2.0) for hold in (1, 3)] + \
        [("crush_diag", -1.5, hold) for hold in (1, 3)]

rows = []
for kind, thr, hold in CELLS:
    pnls, atrs, ooss = [], [], []
    busy = -1
    for k, zv in z.items():
        if not np.isfinite(zv) or k not in kpos:
            continue
        trig = zv >= thr if kind == "shock" else zv <= thr
        if not trig:
            continue
        i, j = kpos[k] + 1, kpos[k] + hold
        if j >= len(keys) or i <= busy:
            continue
        ek, xk = keys[i], keys[j]
        e, xp, a = d.o[ek], d.c[xk], d.atr20[ek]
        if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
            continue
        pnls.append(xp - e - COST)
        atrs.append(a); ooss.append(bool(d.oos[ek]))
        busy = j
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss))
    rows.append(dict(kind=kind, thr=thr, hold=hold, selectable=(kind == "shock"),
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]),
                     _sub=sub))

print("\n=== IS grid (GOLD, ATR-normalized; crush cells diagnostic) ===")
print(f"{'kind':>11} {'thr':>5} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>11} {r['thr']:>5} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel if sum(r[x] == cand[x] for x in ("thr", "hold")) == 1
          and r["IS"].get("n", 0) >= 20]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo shock cell passes the IS floor (n>=40, t>=2, neighbors); family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r52_gvz.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: shock z>={winner['thr']} hold={winner['hold']}d (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 25 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("kind", "thr", "hold", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r52_gvz.json", "w"), indent=1, default=float)
