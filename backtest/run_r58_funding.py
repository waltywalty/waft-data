"""Round 58 attempt 40: BTC crowded-leverage reversion via funding extremes
(frozen per reference/goal_ledger.md). 4 selectable cells + moderate-band
diagnostics, single OOS evaluation. Outputs results/r58_funding.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST_BPS = 5.0

fr_lines = [l for l in open("data/BTC_funding_binance.csv").read().splitlines()
            if l and not l.startswith("calc_time")]
fr = pd.DataFrame([l.split(",") for l in fr_lines], columns=["t", "iv", "r"])
fr["t"] = pd.to_datetime(pd.to_numeric(fr.t), unit="ms")
fr["r"] = pd.to_numeric(fr.r)
daily_f = fr.groupby(fr.t.dt.date).r.sum()
pct = daily_f.rolling(252).rank(pct=True).shift(0)   # percentile of day T, known 16:00 UTC

d = pd.read_csv("data/BTCUSD_daily_av.csv", parse_dates=["timestamp"]).set_index("timestamp").sort_index()
c = d.close
ret = np.log(c).diff()
sig63 = ret.rolling(63).std().shift(1)
kpos = {k.date(): i for i, k in enumerate(c.index)}
keys = [k.date() for k in c.index]
print(f"funding days {daily_f.index[0]}..{daily_f.index[-1]}; price days {keys[0]}..{keys[-1]}")

joined = [k for k in daily_f.index if k in kpos and np.isfinite(pct.get(k, np.nan))]
cut = joined[int(len(joined) * 0.75)]
print(f"{len(joined)} joined signal days, OOS from {cut}")


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


def run(lo, hi, side, hold):
    pnls, sigs, ooss = [], [], []
    busy = -1
    for k in joined:
        p = pct[k]
        if not (lo <= p <= hi):
            continue
        i = kpos[k]
        if i <= busy or i + hold >= len(c):
            continue
        s = sig63.iloc[i]
        if not np.isfinite(s) or s <= 0:
            continue
        fwd = np.log(c.iloc[i + hold] / c.iloc[i])
        pnls.append(side * fwd * 1e4 - COST_BPS)
        sigs.append(s); ooss.append(k >= cut)
        busy = i + hold
    return pd.DataFrame(dict(pnl=pnls, sig=sigs, oos=ooss))


CELLS = [("hi_short", 0.9, 1.01, -1, 1, True), ("hi_short", 0.9, 1.01, -1, 3, True),
         ("lo_long", -0.01, 0.1, +1, 1, True), ("lo_long", -0.01, 0.1, +1, 3, True),
         ("mid_short_diag", 0.6, 0.8, -1, 1, False), ("mid_short_diag", 0.6, 0.8, -1, 3, False),
         ("mid_long_diag", 0.2, 0.4, +1, 1, False), ("mid_long_diag", 0.2, 0.4, +1, 3, False)]

rows = []
for name, lo, hi, side, hold, sel in CELLS:
    sub = run(lo, hi, side, hold)
    rows.append(dict(cell=name, hold=hold, side=("short" if side < 0 else "long"),
                     selectable=sel,
                     IS=stats(sub.pnl[~sub.oos], sub.sig[~sub.oos], hold),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.sig[sub.oos], hold),
                     _sub=sub, _hold=hold))

print("\n=== IS grid (BTC, bps net of 5bp RT; mid-band cells diagnostic) ===")
print(f"{'cell':>15} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avg bps':>8} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['cell']:>15} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.1f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel_rows = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel_rows if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel_rows if r["cell"] == cand["cell"] and r is not cand][0]
    if (sib["IS"].get("avg_bps") or -1) > 0:
        winner = cand
        break
if winner is not None:
    dname = "mid_short_diag" if winner["side"] == "short" else "mid_long_diag"
    dg = [r for r in rows if r["cell"] == dname and r["hold"] == winner["hold"]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_bps") or 9e9) < (winner["IS"].get("avg_bps") or -9e9)
    if not verdict["diag_below"]:
        print("\nWinner matched by moderate-band diagnostic: monotone carry artifact, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r58_funding.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['cell']} hold{winner['hold']}")
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
               winner={"cell": winner["cell"], "hold": winner["hold"], "IS": winner["IS"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r58_funding.json", "w"), indent=1, default=float)
