"""Round 42 attempt 10: gold 08:30 macro-impulse continuation (frozen per
goal_ledger.md). Outputs results/r42j_goldnews.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST = 0.35

b = load_frame("GOLD")
rows_d = []
for skey, g in b.groupby("skey"):
    hm = g.hm.values
    c, o = g.close.values, g.open.values
    def px_at(t, kind="c"):
        m = np.where(hm < t)[0]
        return (c if kind == "c" else o)[m[-1]] if len(m) else np.nan
    m830 = np.where(hm == 830)[0]
    if not len(m830):
        continue
    rows_d.append(dict(skey=skey, o830=o[m830[0]], c835=px_at(840), c845=px_at(850),
                       c915=px_at(920), c930=px_at(935), c945=px_at(950),
                       c1100=px_at(1105), hi=g.high.max(), lo=g.low.min()))
d = pd.DataFrame(rows_d).set_index("skey")
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
cutd = d.index.tolist()[int(len(d) * 0.75)]
d["oos"] = d.index >= cutd
print(f"GOLD: {len(d)} sessions with 08:30 bar, OOS from {cutd}")

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

WINS = {"5m": ("c835", {"30m": "c915", "60m": "c945", "to11": "c1100"}),
        "15m": ("c845", {"30m": "c930", "60m": "c945", "to11": "c1100"})}
rows = []
for wname, (ecol, holds) in WINS.items():
    for th in (0.15, 0.25):
        for hname, xcol in holds.items():
            imp = d[ecol] - d.o830
            m = np.isfinite(imp) & (imp.abs() >= th * d.atr20) & np.isfinite(d[xcol])
            side = np.sign(imp[m])
            pnl = side * (d[xcol][m] - d[ecol][m]) - COST
            sub = pd.DataFrame(dict(pnl=pnl, atr=d.atr20[m], oos=d.oos[m]))
            rows.append(dict(win=wname, th=th, hold=hname,
                             IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                             OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (gold, ATR-normalized) ===")
print(f"{'win':>4} {'th':>5} {'hold':>5} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['win']:>4} {r['th']:>5} {r['hold']:>5} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("win", "th", "hold")) == 2
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42j_goldnews.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['win']} th{winner['th']} hold {winner['hold']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("win", "th", "hold", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42j_goldnews.json", "w"), indent=1, default=float)
