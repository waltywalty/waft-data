"""Round 42 attempt 8: ALMA baseline repair (frozen per goal_ledger.md).
Outputs results/r42h_alma.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

def alma(x, n=50, off=0.85, sig=6.0):
    m, s = off * (n - 1), n / sig
    w = np.exp(-((np.arange(n) - m) ** 2) / (2 * s * s))
    w /= w.sum()
    return pd.Series(x).rolling(n).apply(lambda v: (v * w).sum(), raw=True).values

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

frames, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = load_frame(idx)
    q = b.resample("6h").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna(subset=["open"])
    c = q.close.values
    q["alma"] = alma(c)
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    q["atr14"] = tr.rolling(14).mean()
    q["atr56"] = tr.rolling(56).mean()
    q["atrD"] = q.atr14 * 2.0                      # ~daily-scale normalizer (4 bars/day)
    cutt = q.index[int(len(q) * 0.75)]
    q["oos"] = q.index >= cutt
    frames[idx] = q
    split[idx] = str(cutt)

rows = []
for s_lb in (4, 8):
    for gate in ("none", "calm"):
        for ex in ("t6", "atrstop"):
            subs = []
            for idx, q in frames.items():
                c, al = q.close.values, q.alma.values
                a14, a56 = q.atr14.values, q.atr56.values
                cross = (c > al) & (np.roll(c, 1) <= np.roll(al, 1))
                slope = al > np.roll(al, s_lb)
                sig = cross & slope
                sig[:60] = False
                if gate == "calm":
                    sig &= (a14 / a56) <= 1.0
                arr = q[["open", "high", "low", "close"]].values
                n = len(q)
                pnls, atrs, ooss, last_exit = [], [], [], -1
                for i in np.where(sig)[0]:
                    if i <= last_exit or i + 2 >= n or not np.isfinite(q.atrD.values[i]):
                        continue
                    e = arr[i][3]
                    if ex == "t6":
                        j2, px = min(i + 6, n - 1), None
                        for k in range(i + 1, j2 + 1):
                            pass
                        px = arr[j2][3]
                        xk = j2
                    else:
                        s_px = e - 2 * a14[i]
                        j2, px, xk = min(i + 12, n - 1), None, min(i + 12, n - 1)
                        for k in range(i + 1, j2 + 1):
                            if arr[k][2] <= s_px:
                                px, xk = s_px, k
                                break
                        if px is None:
                            px = arr[j2][3]
                    pnls.append(px - e - MICRO[idx])
                    atrs.append(q.atrD.values[i])
                    ooss.append(bool(q.oos.values[i]))
                    last_exit = xk
                subs.append(pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idx)))
            sub = pd.concat(subs, ignore_index=True)
            rows.append(dict(s=s_lb, gate=gate, exit=ex,
                             IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                             OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("=== IS grid (pooled, ATR-normalized) ===")
print(f"{'s':>3} {'gate':>5} {'exit':>8} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['s']:>3} {r['gate']:>5} {r['exit']:>8} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break                                     # amended floor: IS t >= 2
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("s", "gate", "exit")) == 2
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant passes the IS t>=2 floor + neighbor rule; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42h_alma.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: s{winner['s']} {winner['gate']} {winner['exit']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("s", "gate", "exit", "IS")},
               oos_pooled=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42h_alma.json", "w"), indent=1, default=float)
