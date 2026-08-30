"""Round 48 attempt 27: auction-outcome direction (frozen per
reference/goal_ledger.md). 4 selectable cells + 2Y diagnostics, single
OOS evaluation. Outputs results/r48b_btc.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def load_auctions(path, prefixes):
    out = []
    for r in json.load(open(path)):
        t = r.get("term") or ""
        if any(t.startswith(x) for x in prefixes) and r.get("auction_date") and r.get("btc"):
            try:
                out.append((pd.Timestamp(r["auction_date"]).date(), float(r["btc"])))
            except (TypeError, ValueError):
                pass
    return sorted(out)


BUCKETS = {"10Y": load_auctions("data/treasury_note_auctions.json", ("10-Year", "9-Year")),
           "30Y": load_auctions("data/treasury_bond_auctions.json", ("30-Year", "29-Year")),
           "2Y": load_auctions("data/treasury_note_auctions.json", ("2-Year",))}


def z_by_date(auctions):
    """z-score of btc vs prior 8 same-bucket auctions; keyed by auction date."""
    out = {}
    vals = [b for _, b in auctions]
    for i, (dte, b) in enumerate(auctions):
        if i < 8:
            continue
        prior = np.array(vals[i - 8:i])
        sd = prior.std()
        if sd > 0:
            out[dte] = (b - prior.mean()) / sd
    return out


Z = {k: z_by_date(v) for k, v in BUCKETS.items()}
for k in Z:
    print(f"{k}: {len(BUCKETS[k])} auctions with btc, {len(Z[k])} with z-score")
# same-day 10Y+30Y collision: later auction wins -> 30Y overrides 10Y (30Y follows 10Y in the cycle)
DUR = dict(Z["10Y"])
DUR.update(Z["30Y"])


def build_days(idx):
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m13 = np.where(hm >= 1305)[0]
        if not len(m13):
            continue
        rows.append(dict(skey=skey, p1305=g.open.values[m13[0]], c=g.close.values[-1],
                         hi=g.high.max(), lo=g.low.min()))
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
    nz = sum(1 for k in d.index if k in DUR)
    print(f"{idx}: {len(d)} sessions, {nz} duration-auction days with z, OOS from {cutd}")

CELLS = [("dur", thr, hold) for thr in (0.0, 0.5) for hold in ("close", "nextc")] + \
        [("2y_diag", thr, hold) for thr in (0.0, 0.5) for hold in ("close", "nextc")]

rows = []
for kind, thr, hold in CELLS:
    zmap = DUR if kind == "dur" else Z["2Y"]
    xcol = "c" if hold == "close" else "nextc"
    pnls, atrs, ooss, idxs = [], [], [], []
    for idx, d in data.items():
        for k in d.index:
            z = zmap.get(k)
            if z is None or abs(z) <= thr:
                continue
            e, xp, a = d.p1305[k], d[xcol][k], d.atr20[k]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            pnls.append(np.sign(z) * (xp - e) - MICRO[idx])
            atrs.append(a); ooss.append(bool(d.oos[k])); idxs.append(idx)
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
    sidx = sub[sub.idx != "GOLD"]
    g = sub[sub.idx == "GOLD"]
    rows.append(dict(kind=kind, thr=thr, hold=hold, selectable=(kind == "dur"),
                     IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                     IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                     OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                     _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; 2Y and gold diagnostic) ===")
print(f"{'kind':>8} {'thr':>4} {'hold':>6} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>8} {r['thr']:>4} {r['hold']:>6} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel if sum(r[x] == cand[x] for x in ("thr", "hold")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo selectable cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r48b_btc.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: dur |z|>{winner['thr']} hold={winner['hold']} (neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("kind", "thr", "hold", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r48b_btc.json", "w"), indent=1, default=float)
