"""Round 55 attempt 37: gold margin-cascade continuation (frozen per
reference/goal_ledger.md). 4 selectable cells + sub-threshold
diagnostics, single OOS evaluation. Outputs results/r55b_margin.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST = 0.35

m15 = pd.read_csv("data/XAUUSD_m15_ejtrader.csv", parse_dates=["Date"])
m15_px = pd.Series(m15.close.values / 100.0, index=m15.Date - pd.Timedelta(hours=7)).sort_index()
f5 = pd.read_csv("data/XAUUSD_5m.csv")
f5_px = pd.Series(f5.Close.values,
                  index=pd.to_datetime(f5.Date.astype(str) + " " + f5.Time.astype(str))).sort_index()
cutover = f5_px.index[0]
px = pd.concat([m15_px[m15_px.index < cutover], f5_px]).sort_index()
px = px[~px.index.duplicated()]

# daily table on ET calendar days: 16:00 close mark, 09:30 entry mark, range
rows_d = []
for d0, g in px.groupby(px.index.date):
    base = pd.Timestamp(str(d0))
    def mark(hh, mm):
        i = g.index.searchsorted(base + pd.Timedelta(hours=hh, minutes=mm))
        return g.iloc[i] if i < len(g) and (g.index[i] - base - pd.Timedelta(hours=hh, minutes=mm)).total_seconds() <= 1800 else np.nan
    c16 = g[g.index <= base + pd.Timedelta(hours=16)]
    rows_d.append(dict(day=d0, e930=mark(9, 30), c16=(c16.iloc[-1] if len(c16) else np.nan),
                       hi=g.max(), lo=g.min()))
d = pd.DataFrame(rows_d).set_index("day")
d = d[np.isfinite(d.c16)]
d["ret"] = np.log(d.c16).diff()
d["sig63"] = d.ret.rolling(63).std().shift(1)
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
d["z"] = d.ret / d.sig63
keys = d.index.tolist()
cutd = keys[int(len(keys) * 0.75)]
d["oos"] = np.array([k >= cutd for k in keys])
print(f"{len(d)} sessions {keys[0]}..{keys[-1]}, OOS from {cutd}; "
      f"|z|>=2: {int((d.z.abs() >= 2).sum())}, |z|>=3: {int((d.z.abs() >= 3).sum())}")


def stats(p, a, floor=10):
    r = np.asarray(p, float) / np.asarray(a, float)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < floor: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


CELLS = [("sel", thr, hold) for thr in (2.0, 3.0) for hold in (1, 2)] + \
        [("diag", 0.5, hold) for hold in (1, 2)]

rows = []
zv, e_arr, c_arr, a_arr, oosv = d.z.values, d.e930.values, d.c16.values, d.atr20.values, d.oos.values
n = len(d)
for kind, thr, hold in CELLS:
    pnls, atrs, ooss = [], [], []
    busy = -1
    for i in range(n - hold):
        if i <= busy or not np.isfinite(zv[i]):
            continue
        az = abs(zv[i])
        trig = az >= thr if kind == "sel" else (0.5 <= az < 1.0)
        if not trig:
            continue
        j = i + 1
        if not (np.isfinite(e_arr[j]) and np.isfinite(c_arr[i + hold]) and np.isfinite(a_arr[j]) and a_arr[j] > 0):
            continue
        side = np.sign(zv[i])
        pnls.append(side * (c_arr[i + hold] - e_arr[j]) - COST)
        atrs.append(a_arr[j]); ooss.append(bool(oosv[j]))
        busy = i + hold
    sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss))
    rows.append(dict(kind=kind, thr=thr, hold=hold, selectable=(kind == "sel"),
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (GOLD, ATR-normalized; sub-threshold cells diagnostic) ===")
print(f"{'kind':>5} {'thr':>4} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>5} {r['thr']:>4} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel if r["thr"] == cand["thr"] and r is not cand][0]
    if (sib["IS"].get("avg_R") or -1) > 0:
        winner = cand
        break
if winner is not None:
    dg = [r for r in rows if r["kind"] == "diag" and r["hold"] == winner["hold"]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_R") or 9) < (winner["IS"].get("avg_R") or -9)
    if not verdict["diag_below"]:
        print("\nWinner matched by sub-threshold diagnostic: generic momentum, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r55b_margin.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: thr{winner['thr']} hold{winner['hold']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 25 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"thr": winner["thr"], "hold": winner["hold"], "IS": winner["IS"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r55b_margin.json", "w"), indent=1, default=float)
