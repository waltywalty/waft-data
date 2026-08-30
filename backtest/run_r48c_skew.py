"""Round 48 attempt 28: tail-risk premium harvest via SKEW (frozen per
reference/goal_ledger.md). 4 selectable cells + low-SKEW diagnostics,
single OOS evaluation. Outputs results/r48c_skew.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

sk = pd.read_csv("data/SKEW_history_cboe.csv")
skew = pd.Series(sk.SKEW.values, index=pd.to_datetime(sk.DATE).dt.date)
pct = skew.rolling(252).rank(pct=True)
print(f"SKEW: {len(skew)} days {skew.index[0]}..{skew.index[-1]}")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
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
    data[idx] = (d, {k: i for i, k in enumerate(d.index)}, d.index.tolist())
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} sessions, OOS from {cutd}")

CELLS = [("high", thr, hold) for thr in (0.8, 0.9) for hold in (1, 5)] + \
        [("low_diag", 0.2, hold) for hold in (1, 5)]

rows = []
for kind, thr, hold in CELLS:
    pnls, atrs, ooss, idxs = [], [], [], []
    for idx, (d, kpos, keys) in data.items():
        busy = -1
        for k, p in pct.items():
            if not np.isfinite(p) or k not in kpos:
                continue
            trig = p >= thr if kind == "high" else p <= thr
            if not trig:
                continue
            i, j = kpos[k] + 1, kpos[k] + hold
            if j >= len(keys) or i <= busy:
                continue
            ek, xk = keys[i], keys[j]
            e, xp, a = d.o[ek], d.c[xk], d.atr20[ek]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            pnls.append(xp - e - MICRO[idx])
            atrs.append(a); ooss.append(bool(d.oos[ek])); idxs.append(idx)
            busy = j
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
    sidx = sub[sub.idx != "GOLD"]
    g = sub[sub.idx == "GOLD"]
    rows.append(dict(kind=kind, thr=thr, hold=hold, selectable=(kind == "high"),
                     IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                     IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                     OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                     _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; low-SKEW and gold diagnostic) ===")
print(f"{'kind':>9} {'thr':>4} {'hold':>4} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>9} {r['thr']:>4} {r['hold']:>4} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
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
    print("\nNo high-SKEW cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r48c_skew.json", "w"), indent=1, default=float)
    raise SystemExit

# self-refutation check (attempt-25 lesson): high-SKEW premium must beat the low-SKEW drift
lo = [r for r in rows if r["kind"] == "low_diag" and r["hold"] == winner["hold"]]
if lo and (lo[0]["IS"].get("avg_R") or -9) >= (winner["IS"].get("avg_R") or -9):
    print(f"\nSELECTED {winner['thr']}/{winner['hold']}d but low-SKEW diagnostic matches it "
          f"({lo[0]['IS'].get('avg_R'):+.3f} vs {winner['IS'].get('avg_R'):+.3f}): generic drift, "
          "family self-refutes at IS; OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, self_refuted=True),
              open("results/r48c_skew.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: high thr={winner['thr']} hold={winner['hold']}d (neighbors positive {npos})")
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
          open("results/r48c_skew.json", "w"), indent=1, default=float)
