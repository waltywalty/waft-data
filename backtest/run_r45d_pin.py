"""Round 45 attempt 22: expiry-day strike pinning (frozen per
reference/goal_ledger.md). 4 selectable cells + non-opex diagnostics,
single OOS evaluation. Outputs results/r45d_pin.json."""
import pandas as pd, numpy as np, json, warnings, datetime as dt
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
GRID = {"SPX": 25.0, "NDX": 100.0, "RTY": 20.0, "GOLD": 25.0}


def third_friday(y, m):
    f = dt.date(y, m, 1)
    return f + dt.timedelta(days=(4 - f.weekday()) % 7 + 14)


def build_days(idx):
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m15 = np.where(hm >= 1500)[0]
        if not len(m15):
            continue
        rows.append(dict(skey=skey, p15=g.open.values[m15[0]], c=g.close.values[-1],
                         hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in d.index])
    # opex Friday: last session on or within 3 days before the third Friday
    keys = d.index.tolist()
    opex = set()
    for y in range(keys[0].year, keys[-1].year + 1):
        for m in range(1, 13):
            tf = third_friday(y, m)
            wk = [k for k in keys if tf - dt.timedelta(days=3) <= k <= tf]
            if wk:
                opex.add(wk[-1])
    d["opex"] = [k in opex for k in keys]
    d["friday"] = [k.weekday() == 4 for k in keys]
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
    print(f"{idx}: {len(d)} sessions, {int(d.opex.sum())} opex Fridays, OOS from {cutd}")

THRS = (0.1, 0.2)
GDIVS = {"G": 1.0, "G/2": 2.0}

rows = []
for daytype in ("opex", "nonopex_fri"):
    for thr in THRS:
        for gname, gdiv in GDIVS.items():
            pnls, atrs, ooss, idxs = [], [], [], []
            for idx, d in data.items():
                gsize = GRID[idx] / gdiv
                if daytype == "opex":
                    m = d.opex
                else:
                    m = d.friday & ~d.opex
                s = d[m & np.isfinite(d.p15) & np.isfinite(d.c)
                      & np.isfinite(d.atr20) & (d.atr20 > 0)]
                L = np.round(s.p15 / gsize) * gsize
                dist = L - s.p15
                sel = (dist.abs() <= thr * s.atr20) & (dist != 0)
                s = s[sel]; dd = dist[sel]
                side = np.sign(dd)
                pnls += list(side * (s.c - s.p15) - MICRO[idx])
                atrs += list(s.atr20); ooss += list(s.oos); idxs += [idx] * len(s)
            sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
            sidx = sub[sub.idx != "GOLD"]
            rows.append(dict(day=daytype, thr=thr, grid=gname,
                             selectable=(daytype == "opex"),
                             IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                             OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                             _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; non-opex Fridays are diagnostic) ===")
print(f"{'day':>12} {'thr':>5} {'grid':>4} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['day']:>12} {r['thr']:>5} {r['grid']:>4} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel_rows = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel_rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel_rows if sum(r[x] == cand[x] for x in ("thr", "grid")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo opex cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r45d_pin.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: opex thr={winner['thr']} grid={winner['grid']} (neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("day", "thr", "grid", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r45d_pin.json", "w"), indent=1, default=float)
