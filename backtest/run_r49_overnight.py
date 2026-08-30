"""Round 49 attempt 29: full overnight close-to-open premium (frozen per
reference/goal_ledger.md, adjacency diagnosis on record). 2 selectable
cells + day-session self-refutation diagnostic, single OOS evaluation.
Outputs results/r49_overnight.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    keys = d.index.tolist()
    d["adjacent"] = [False] + [(keys[i] - keys[i - 1]).days == 1 for i in range(1, len(keys))]
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd


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


data, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    data[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} sessions, {int(d.adjacent.sum())} adjacent, OOS from {cutd}")

CELLS = [("night", "all"), ("night", "adjacent"), ("day_diag", "all"), ("day_diag", "adjacent")]

rows = []
for kind, scope in CELLS:
    pnls, atrs, ooss, idxs = [], [], [], []
    for idx, d in data.items():
        m = np.isfinite(d.atr20) & (d.atr20 > 0)
        if kind == "night":
            m &= np.isfinite(d.prevc)
            if scope == "adjacent":
                m &= d.adjacent
            s = d[m]
            pnl = s.o - s.prevc - MICRO[idx]
        else:
            if scope == "adjacent":
                m &= d.adjacent
            s = d[m]
            pnl = s.c - s.o - MICRO[idx]
        pnls += list(pnl); atrs += list(s.atr20); ooss += list(s.oos); idxs += [idx] * len(s)
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
    sidx = sub[sub.idx != "GOLD"]
    g = sub[sub.idx == "GOLD"]
    rows.append(dict(kind=kind, scope=scope, selectable=(kind == "night"),
                     IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                     IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                     OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                     _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; day cells are the self-refutation diagnostic) ===")
print(f"{'kind':>9} {'scope':>9} | {'n':>6} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    print(f"{r['kind']:>9} {r['scope']:>9} | {a['n']:>6} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = None
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    other = [r for r in sel if r is not cand][0]
    if (other["IS"].get("avg_R") or -1) > 0:
        winner = cand
        break

if winner is not None:
    day = [r for r in rows if r["kind"] == "day_diag" and r["scope"] == winner["scope"]][0]
    if (day["IS"].get("avg_R") or -9) >= (winner["IS"].get("avg_R") or -9):
        print(f"\nNight cell passes floor but day diagnostic matches it "
              f"({day['IS'].get('avg_R'):+.3f} vs {winner['IS'].get('avg_R'):+.3f}): "
              "generic drift, family self-refutes at IS; OOS not opened.")
        json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                       winner=None, gate_pass=False, self_refuted=True),
                  open("results/r49_overnight.json", "w"), indent=1, default=float)
        raise SystemExit

if winner is None:
    print("\nNo night cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r49_overnight.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: night {winner['scope']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (indices pooled, burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in ("SPX", "NDX", "RTY"):
    s = oos[oos.idx == idx]
    per[idx] = stats(s.pnl, s.atr)
    v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("kind", "scope", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r49_overnight.json", "w"), indent=1, default=float)
