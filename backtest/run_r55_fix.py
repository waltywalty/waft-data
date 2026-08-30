"""Round 55 attempt 36: gold London PM fix window (frozen per
reference/goal_ledger.md). 4 selectable cells + shifted-window
diagnostics, single OOS evaluation. Outputs results/r55_fix.json."""
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
print(f"unified ET series {px.index[0]}..{px.index[-1]}, {len(px)} bars")

day = px.groupby(px.index.date)
rng = day.max() - day.min()
atr20 = rng.rolling(20).mean().shift(1)
days = sorted(set(px.index.date))
cutd = days[int(len(days) * 0.75)]
print(f"{len(days)} days, OOS from {cutd}")

# per-day mark at first bar close >= hh:mm
def marks(hh, mm):
    t0 = pd.Timestamp("2000-01-01") + pd.Timedelta(hours=hh, minutes=mm)
    out = {}
    for d0, g in px.groupby(px.index.date):
        tgt = pd.Timestamp(str(d0)) + pd.Timedelta(hours=hh, minutes=mm)
        i = g.index.searchsorted(tgt)
        if i < len(g) and (g.index[i] - tgt).total_seconds() <= 30 * 60:
            out[d0] = g.iloc[i]
    return pd.Series(out)


M = {t: marks(*t) for t in [(9, 0), (9, 30), (10, 0), (10, 30), (11, 0),
                            (7, 0), (7, 30), (8, 0), (8, 30)]}

CELLS = [("S1", (9, 0), (10, 0), -1, True), ("S2", (9, 30), (10, 0), -1, True),
         ("L1", (10, 0), (10, 30), +1, True), ("L2", (10, 0), (11, 0), +1, True),
         ("dS1", (7, 0), (8, 0), -1, False), ("dS2", (7, 30), (8, 0), -1, False),
         ("dL1", (8, 0), (8, 30), +1, False), ("dL2", (8, 0), (9, 0), +1, False)]


def stats(p, a):
    r = np.asarray(p, float) / np.asarray(a, float)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


rows = []
for name, e_t, x_t, side, sel in CELLS:
    e, x = M[e_t], M[x_t]
    j = pd.concat([e, x], axis=1, keys=["e", "x"]).dropna()
    j["atr"] = [atr20.get(k, np.nan) for k in j.index]
    j = j[np.isfinite(j.atr) & (j.atr > 0)]
    j["pnl"] = side * (j.x - j.e) - COST
    j["oos"] = [k >= cutd for k in j.index]
    rows.append(dict(cell=name, side=("short" if side < 0 else "long"), selectable=sel,
                     IS=stats(j.pnl[~j.oos], j.atr[~j.oos]),
                     OOS_sealed=stats(j.pnl[j.oos], j.atr[j.oos]), _sub=j))

print("\n=== IS grid (GOLD, ATR-normalized; d* = shifted-window diagnostics) ===")
print(f"{'cell':>5} {'side':>6} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['cell']:>5} {r['side']:>6} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = None
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel if r["side"] == cand["side"] and r is not cand][0]
    if (sib["IS"].get("avg_R") or -1) > 0:
        winner = cand
        break

verdict = {}
if winner is not None:
    dmap = {"S1": "dS1", "S2": "dS2", "L1": "dL1", "L2": "dL2"}
    dg = [r for r in rows if r["cell"] == dmap[winner["cell"]]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_R") or 9) < (winner["IS"].get("avg_R") or -9)
    if not verdict["diag_below"]:
        print(f"\nWinner {winner['cell']} matched by shifted-window diagnostic: drift, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r55_fix.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['cell']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner=winner["cell"], oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r55_fix.json", "w"), indent=1, default=float)
