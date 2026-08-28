"""Round 42 attempt 7: gold session-clock split (Asia long / London short),
frozen per reference/goal_ledger.md. Outputs results/r42g_goldclock.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST = 0.35
WINSETS = {"A": dict(asia=(1900, 300), lon=(300, 1100)),
           "B": dict(asia=(2000, 200), lon=(300, 1000))}
LEGS = ("asia_long", "london_short", "both")

b = load_frame("GOLD")
b = b.sort_index()
hm = b.hm.values

def window_px(g, a, z):
    """First open / last close for a clock window; wraps midnight if a > z."""
    h = g.hm.values
    m = (h >= a) | (h < z) if a > z else (h >= a) & (h < z)
    if m.sum() < 10:
        return np.nan, np.nan
    return g.open.values[np.argmax(m)], g.close.values[len(m) - 1 - np.argmax(m[::-1])]

rows_d = []
for skey, g in b.groupby("skey"):
    rec = dict(skey=skey, hi=g.high.max(), lo=g.low.min())
    for wname, ws in WINSETS.items():
        ea, xa = window_px(g, *ws["asia"])
        el, xl = window_px(g, *ws["lon"])
        rec[f"asia_{wname}"] = xa - ea if np.isfinite(ea) else np.nan
        rec[f"lon_{wname}"] = el - xl if np.isfinite(el) else np.nan   # short pnl gross
    rows_d.append(rec)
d = pd.DataFrame(rows_d).set_index("skey")
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
cutd = d.index.tolist()[int(len(d) * 0.75)]
d["oos"] = d.index >= cutd
print(f"GOLD: {len(d)} sessions, OOS from {cutd}")

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

rows = []
for wname in WINSETS:
    for leg in LEGS:
        if leg == "asia_long":
            pnl = d[f"asia_{wname}"] - COST
        elif leg == "london_short":
            pnl = d[f"lon_{wname}"] - COST
        else:
            pnl = d[f"asia_{wname}"] + d[f"lon_{wname}"] - 2 * COST
        sub = pd.DataFrame(dict(pnl=pnl, atr=d.atr20, oos=d.oos)).dropna()
        rows.append(dict(win=wname, leg=leg,
                         IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (gold, ATR-normalized) ===")
print(f"{'set':>4} {'leg':>13} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    print(f"{r['win']:>4} {r['leg']:>13} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("win", "leg")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant selectable; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42g_goldclock.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: set {winner['win']} {winner['leg']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
nlegs = 2 if winner['leg'] == 'both' else 1
c15 = stats(oos.pnl - 0.5 * COST * nlegs, oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("win", "leg", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42g_goldclock.json", "w"), indent=1, default=float)
