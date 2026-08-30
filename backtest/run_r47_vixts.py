"""Round 47 attempt 25: vol term-structure regime gate (frozen per
reference/goal_ledger.md). 4 selectable cells + contango diagnostics,
single OOS evaluation. Outputs results/r47_vixts.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def cboe(path):
    d = pd.read_csv(path)
    return pd.Series(d.CLOSE.values, index=pd.to_datetime(d.DATE).dt.date)


vix = cboe("data/VIX_history_cboe.csv")
v9 = cboe("data/VIX9D_history_cboe.csv")
v3 = cboe("data/VIX3M_history_cboe.csv")
ratios = {"9d_30d": (v9 / vix).dropna(), "30d_3m": (vix / v3).dropna()}
for k, r in ratios.items():
    print(f"{k}: {len(r)} days {r.index[0]}..{r.index[-1]}, "
          f"share >= 1.0: {(r >= 1).mean()*100:.1f}%")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d = d[[k >= pd.Timestamp("2011-01-04").date() for k in d.index]]
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
    print(f"{idx}: {len(d)} sessions from 2011, OOS from {cutd}")

# prior-close signal per session: last CBOE value strictly before the session date
def prior_signal(keys, r):
    rd = sorted(r.index)
    out, j = [], 0
    for k in keys:
        while j < len(rd) and rd[j] < k:
            j += 1
        out.append(r[rd[j - 1]] if j > 0 else np.nan)
    return np.array(out)


CELLS = [("inv", leg, thr) for leg in ratios for thr in (1.0, 1.05)] + \
        [("contango_diag", leg, 0.9) for leg in ratios]

rows = []
for kind, leg, thr in CELLS:
    pnls, atrs, ooss, idxs = [], [], [], []
    for idx, d in data.items():
        keys = d.index.tolist()
        sig = prior_signal(keys, ratios[leg])
        o, c, pc, a20 = d.o.values, d.c.values, d.prevc.values, d.atr20.values
        oosv = d.oos.values
        in_pos = False
        for i in range(1, len(keys)):
            s = sig[i]
            if not np.isfinite(s) or not np.isfinite(a20[i]) or a20[i] <= 0:
                continue
            trig = s >= thr if kind == "inv" else s <= thr
            if not in_pos and trig:
                pnls.append(c[i] - o[i] - MICRO[idx])       # entry day, RT cost here
                atrs.append(a20[i]); ooss.append(bool(oosv[i])); idxs.append(idx)
                in_pos = True
            elif in_pos:
                if np.isfinite(pc[i]):
                    pnls.append(c[i] - pc[i])
                    atrs.append(a20[i]); ooss.append(bool(oosv[i])); idxs.append(idx)
                if not trig:
                    in_pos = False                          # exit at this close
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
    sidx = sub[sub.idx != "GOLD"]
    g = sub[sub.idx == "GOLD"]
    rows.append(dict(kind=kind, leg=leg, thr=thr, selectable=(kind == "inv"),
                     IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                     IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                     OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                     _sub=sidx))

print("\n=== IS grid (indices pooled, daily bookings, ATR-normalized; contango cells diagnostic) ===")
print(f"{'kind':>14} {'leg':>7} {'thr':>5} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>14} {r['leg']:>7} {r['thr']:>5} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel if sum(r[x] == cand[x] for x in ("leg", "thr")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo inversion cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r47_vixts.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: inv {winner['leg']} thr={winner['thr']} (neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("kind", "leg", "thr", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r47_vixts.json", "w"), indent=1, default=float)
