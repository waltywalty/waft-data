"""Round 45 attempt 21: turn-of-month premium (frozen per
reference/goal_ledger.md). 6-cell IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r45c_tom.json."""
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
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in d.index])
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
    print(f"{idx}: {len(d)} sessions, OOS from {cutd}")

# windows: (entry_day_offset_from_last, entry_col, exit_day_offset, exit_col)
# offsets: 0 = last trading day of month, -1 = day before, +k = kth day of next month
WINS = {"T1_last_p3": (0, "o", 3, "c"), "T2_last_p1": (0, "o", 1, "c"),
        "T3_m1_p3": (-1, "c", 3, "c")}
SCOPES = {"all": tuple(range(1, 13)), "qtr": (3, 6, 9, 12)}

rows = []
for wname, (eoff, ecol, xoff, xcol) in WINS.items():
    for sname, months in SCOPES.items():
        pnls, atrs, ooss, idxs = [], [], [], []
        for idx, d in data.items():
            keys = d.index.tolist()
            # last trading day of each month = session whose successor is a new month
            for i in range(1, len(keys) - 4):
                if keys[i + 1].month == keys[i].month:
                    continue
                if keys[i].month not in months:
                    continue
                ei, xi = i + eoff, i + xoff
                if ei < 0 or xi >= len(keys):
                    continue
                e, xp, a = d[ecol].iloc[ei], d[xcol].iloc[xi], d.atr20.iloc[ei]
                if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                    continue
                pnls.append(xp - e - MICRO[idx])
                atrs.append(a); ooss.append(bool(d.oos.iloc[ei])); idxs.append(idx)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
        sidx = sub[sub.idx != "GOLD"]
        g = sub[sub.idx == "GOLD"]
        rows.append(dict(win=wname, scope=sname,
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; gold diagnostic) ===")
print(f"{'window':>11} {'scope':>5} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['win']:>11} {r['scope']:>5} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

def floor_n(r):
    return 60 if r["scope"] == "qtr" else 120

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= floor_n(r)],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("win", "scope")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r45c_tom.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['win']} {winner['scope']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
nfloor = 25 if winner["scope"] == "qtr" else 40
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
PASS = (o.get("n", 0) >= nfloor and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("win", "scope", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r45c_tom.json", "w"), indent=1, default=float)
