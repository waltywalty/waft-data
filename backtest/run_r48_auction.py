"""Round 48 attempt 26: Treasury duration-auction day (frozen per
reference/goal_ledger.md). 6 selectable cells + 2Y diagnostics, single
OOS evaluation. Outputs results/r48_auction.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def auction_days(paths_terms):
    days = set()
    for path, terms in paths_terms:
        for r in json.load(open(path)):
            t = r.get("term") or ""
            if any(t.startswith(x) for x in terms) and r.get("auction_date"):
                days.add(pd.Timestamp(r["auction_date"]).date())
    return days


D10 = auction_days([("data/treasury_note_auctions.json", ("10-Year", "9-Year"))])
D30 = auction_days([("data/treasury_bond_auctions.json", ("30-Year", "29-Year"))])
D2 = auction_days([("data/treasury_note_auctions.json", ("2-Year",))])
print(f"auction days: 10Y {len(D10)}, 30Y {len(D30)}, 2Y {len(D2)} (all-history)")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m13 = np.where(hm >= 1300)[0]
        if not len(m13):
            continue
        rows.append(dict(skey=skey, o=g.open.values[0], p13=g.open.values[m13[0]],
                         c=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["nextc"] = d.c.shift(-1)
    keys = d.index.tolist()
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
    nis = sum(1 for k in d.index if k in D10)
    print(f"{idx}: {len(d)} sessions, {nis} 10Y auction days in span, OOS from {cutd}")

WINS = {"W1_conc": ("o", "p13", -1), "W2_relief": ("p13", "c", +1),
        "W3_relief_next": ("p13", "nextc", +1)}
TERMS = {"10Y": D10, "30Y": D30, "2Y_diag": D2}

rows = []
for wname, (ecol, xcol, side) in WINS.items():
    for tname, dayset in TERMS.items():
        pnls, atrs, ooss, idxs = [], [], [], []
        for idx, d in data.items():
            m = np.array([k in dayset for k in d.index]) & np.isfinite(d[ecol]) \
                & np.isfinite(d[xcol]) & np.isfinite(d.atr20) & (d.atr20 > 0)
            s = d[m]
            pnls += list(side * (s[xcol] - s[ecol]) - MICRO[idx])
            atrs += list(s.atr20); ooss += list(s.oos); idxs += [idx] * len(s)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
        sidx = sub[sub.idx != "GOLD"]
        g = sub[sub.idx == "GOLD"]
        rows.append(dict(win=wname, term=tname, side=("short" if side < 0 else "long"),
                         selectable=(tname != "2Y_diag"),
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; 2Y and gold diagnostic) ===")
print(f"{'window':>15} {'term':>8} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['win']:>15} {r['term']:>8} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel if r["side"] == cand["side"]
          and sum(r[x] == cand[x] for x in ("win", "term")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo selectable cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r48_auction.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['win']} {winner['term']} (same-arm neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("win", "term", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r48_auction.json", "w"), indent=1, default=float)
