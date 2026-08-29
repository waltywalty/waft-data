"""Round 46 attempt 23: equity put/call contrarian gate (frozen per
reference/goal_ledger.md). 4 selectable cells + greed-short diagnostics,
single OOS evaluation. Outputs results/r46_putcall.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

# --- CBOE equity P/C: skip disclaimer preamble, parse DATE,CALL,PUT,TOTAL,P/C ---
lines = open("data/cboe_equitypc.csv").read().splitlines()
recs = []
for ln in lines:
    parts = [p.strip() for p in ln.split(",")]
    if len(parts) == 5 and "/" in parts[0]:
        try:
            recs.append((pd.Timestamp(parts[0]).date(), float(parts[4])))
        except Exception:
            pass
pc = pd.Series(dict(recs)).sort_index()
pc_pct = pc.rolling(252).rank(pct=True)          # trailing percentile incl. day T
print(f"CBOE equity P/C: {len(pc)} days {pc.index[0]}..{pc.index[-1]}, "
      f"{pc_pct.notna().sum()} with 252d percentile")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    return d


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
for idx in MICRO:
    d = build_days(idx)
    # join: restrict to sessions with a prior-day percentile available
    keys = d.index.tolist()
    kpos = {k: i for i, k in enumerate(keys)}
    d = d[[k in pc_pct.index and np.isfinite(pc_pct.get(k, np.nan)) or True for k in keys]]
    span = [k for k in keys if pc.index[0] <= k <= pc.index[-1]]
    cutd = span[int(len(span) * 0.75)]
    data[idx] = (d, keys, kpos, cutd)
    split[idx] = str(cutd)
    print(f"{idx}: {len(span)} joined sessions, OOS from {cutd}")

CELLS = [("fear", thr, hold) for thr in (0.8, 0.9) for hold in (1, 3)] + \
        [("greed", 0.1, hold) for hold in (1, 3)]

rows = []
for side_name, thr, hold in CELLS:
    pnls, atrs, ooss, idxs = [], [], [], []
    for idx, (d, keys, kpos, cutd) in data.items():
        busy = -1
        for k, pct in pc_pct.items():
            if not np.isfinite(pct) or k not in kpos:
                continue
            trig = pct >= thr if side_name == "fear" else pct <= thr
            if not trig:
                continue
            i = kpos[k] + 1                       # entry: next session open
            j = kpos[k] + hold                    # exit: hold-th session close
            if i >= len(keys) or j >= len(keys) or i <= busy:
                continue
            ek, xk = keys[i], keys[j]
            e, xp, a = d.o.get(ek, np.nan), d.c.get(xk, np.nan), d.atr20.get(ek, np.nan)
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            sgn = 1 if side_name == "fear" else -1
            pnls.append(sgn * (xp - e) - MICRO[idx])
            atrs.append(a); ooss.append(ek >= cutd); idxs.append(idx)
            busy = j
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
    rows.append(dict(side=side_name, thr=thr, hold=hold,
                     selectable=(side_name == "fear"),
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]),
                     _sub=sub))

print("\n=== IS grid (indices pooled, ATR-normalized; greed-short is diagnostic) ===")
print(f"{'side':>6} {'thr':>5} {'hold':>4} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['side']:>6} {r['thr']:>5} {r['hold']:>4} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

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
    print("\nNo fear cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r46_putcall.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: fear thr={winner['thr']} hold={winner['hold']}d (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (indices pooled, burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in MICRO:
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
               winner={x: winner[x] for x in ("side", "thr", "hold", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r46_putcall.json", "w"), indent=1, default=float)
