"""Round 59 attempt 41: BTC DVOL-shock reversal (frozen per
reference/goal_ledger.md). 4 selectable cells + crush diagnostics,
single OOS evaluation. Outputs results/r59_dvolshock.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST_BPS = 5.0

dv = pd.read_csv("data/BTC_DVOL_deribit.csv")
dv["d"] = pd.to_datetime(dv.ts, unit="ms").dt.date
dvol = pd.Series(dv.close.values, index=dv.d)
z = (np.log(dvol).diff() / np.log(dvol).diff().rolling(63).std().shift(1))

px = pd.read_csv("data/BTCUSD_daily_av.csv", parse_dates=["timestamp"]).set_index("timestamp").sort_index()
c = px.close
kpos = {k.date(): i for i, k in enumerate(c.index)}
ret = np.log(c).diff()
sig63 = ret.rolling(63).std().shift(1)

joined = [k for k in z.index if k in kpos and np.isfinite(z[k])]
cut = joined[int(len(joined) * 0.75)]
print(f"{len(joined)} joined days, OOS from {cut}; z>=1.5: {int((z >= 1.5).sum())}, "
      f"z>=2: {int((z >= 2).sum())}, crush: {int((z <= -1.5).sum())}")


def stats(p, s, hold, floor=10):
    r = np.asarray(p, float) / (np.asarray(s, float) * np.sqrt(hold) * 1e4)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < floor: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_bps=float(p.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def run(kind, thr, hold):
    pnls, sigs, ooss = [], [], []
    busy = -1
    for k in joined:
        zv = z[k]
        trig = zv >= thr if kind == "shock" else zv <= thr
        if not trig:
            continue
        i = kpos[k]
        if i <= busy or i + hold >= len(c):
            continue
        s = sig63.iloc[i]
        if not np.isfinite(s) or s <= 0:
            continue
        pnls.append(np.log(c.iloc[i + hold] / c.iloc[i]) * 1e4 - COST_BPS)
        sigs.append(s); ooss.append(k >= cut)
        busy = i + hold
    return pd.DataFrame(dict(pnl=pnls, sig=sigs, oos=ooss))


CELLS = [("shock", t_, h) for t_ in (1.5, 2.0) for h in (1, 3)] + \
        [("crush_diag", -1.5, h) for h in (1, 3)]
rows = []
for kind, thr, hold in CELLS:
    sub = run(kind, thr, hold)
    rows.append(dict(kind=kind, thr=thr, hold=hold, selectable=(kind == "shock"),
                     IS=stats(sub.pnl[~sub.oos], sub.sig[~sub.oos], hold),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.sig[sub.oos], hold),
                     _sub=sub, _hold=hold))

print("\n=== IS grid (BTC long after DVOL shock; bps net of 5bp RT) ===")
print(f"{'kind':>11} {'thr':>5} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avg bps':>8} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>11} {r['thr']:>5} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.1f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel if r["thr"] == cand["thr"] and r is not cand][0]
    if (sib["IS"].get("avg_bps") or -1) > 0:
        winner = cand
        break
if winner is not None:
    dg = [r for r in rows if r["kind"] == "crush_diag" and r["hold"] == winner["hold"]][0]
    verdict["crush_below"] = (dg["IS"].get("avg_bps") or 9e9) < (winner["IS"].get("avg_bps") or -9e9)
    if not verdict["crush_below"]:
        print("\nWinner matched by crush diagnostic: drift, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo shock cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r59_dvolshock.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: z>={winner['thr']} hold{winner['hold']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.sig, winner["_hold"])
c15 = stats(oos.pnl - 0.5 * COST_BPS, oos.sig, winner["_hold"])
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avg {o.get('avg_bps',float('nan')):+.1f}bps t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avg {c15.get('avg_bps',float('nan')):+.1f}bps t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 25 and (o.get("avg_bps") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_bps") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"thr": winner["thr"], "hold": winner["hold"], "IS": winner["IS"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r59_dvolshock.json", "w"), indent=1, default=float)
