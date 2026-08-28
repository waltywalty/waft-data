"""Round 42 attempt 6: the overnight-drift window (European open), frozen per
reference/goal_ledger.md. 6-variant long-only IS grid, index-only selection,
single OOS evaluation. Outputs results/r42f_ondrift.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
WINDOWS = {"0100-0400": (100, 400), "0200-0330": (200, 330), "0230-0330": (230, 330)}
FILTS = ("all", "prev_down")


def build(idx):
    b = load_frame(idx)
    rows = []
    for skey, g in b.groupby("skey"):
        hm = g.hm.values
        rec = dict(skey=skey, hi=g.high.max(), lo=g.low.min(), c=g.close.values[-1])
        for wname, (a, z) in WINDOWS.items():
            m = (hm >= a) & (hm < z)
            if m.sum() >= max(3, (z - a) // 15):
                rec[f"e_{wname}"] = g.open.values[np.argmax(m)]
                rec[f"x_{wname}"] = g.close.values[len(m) - 1 - np.argmax(m[::-1])]
        rows.append(rec)
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prev_ret"] = d.c.pct_change().shift(0)          # this session vs prior close
    d["prev_down"] = d.prev_ret.shift(1) < 0           # PRIOR session was down
    return d


def stats(pnl, atr):
    p = np.asarray(pnl, float)
    r = p / np.asarray(atr, float)
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
    d = build(idx)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    d["idx"] = idx
    frames[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} sessions, OOS from {cutd}")

rows = []
for wname in WINDOWS:
    for f in FILTS:
        subs = []
        for idx, d in frames.items():
            m = np.isfinite(d.get(f"e_{wname}", np.nan)) & np.isfinite(d.get(f"x_{wname}", np.nan)) \
                & np.isfinite(d.atr20) & (d.atr20 > 0)
            if f == "prev_down":
                m &= d.prev_down
            s = d[m]
            subs.append(pd.DataFrame(dict(pnl=s[f"x_{wname}"] - s[f"e_{wname}"] - MICRO[idx],
                                          atr=s.atr20, oos=s.oos, idx=idx)))
        sub = pd.concat(subs, ignore_index=True)
        sidx = sub[sub.idx != "GOLD"]
        rows.append(dict(win=wname, filt=f,
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(sub[(sub.idx == "GOLD") & ~sub.oos].pnl,
                                       sub[(sub.idx == "GOLD") & ~sub.oos].atr),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sub))

print("\n=== IS grid (indices pooled, ATR-normalized; gold shown as diagnostic) ===")
print(f"{'window':>10} {'filter':>10} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    print(f"{r['win']:>10} {r['filt']:>10} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("win", "filt")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant selectable; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42f_ondrift.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['win']} {winner['filt']} (neighbors positive {npos})")
sub = winner["_sub"]
oosall = sub[sub.oos]
oos = oosall[oosall.idx != "GOLD"]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (indices pooled, burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
    s = oosall[oosall.idx == idx]
    per[idx] = stats(s.pnl, s.atr)
    v = per[idx]
    if v.get("n", 0) >= 10:
        tag = " (diagnostic)" if idx == "GOLD" else ""
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}{tag}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("win", "filt", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42f_ondrift.json", "w"), indent=1, default=float)
