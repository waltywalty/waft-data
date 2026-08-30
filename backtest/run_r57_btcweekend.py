"""Round 57 attempt 39: BTC weekend-move reversion (frozen per
reference/goal_ledger.md). 4 selectable cells + midweek diagnostics,
single OOS evaluation. Outputs results/r57_btcweekend.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST_BPS = 5.0

d = pd.read_csv("data/BTCUSD_daily_av.csv", parse_dates=["timestamp"])
d = d.set_index("timestamp").sort_index()
d = d[d.index >= "2015-01-01"]
c = d.close
ret = np.log(c).diff()
sig63 = ret.rolling(63).std().shift(1)
dow = c.index.dayofweek
print(f"BTC daily {c.index[0].date()}..{c.index[-1].date()}, {len(c)} bars")

# weekend events: Friday close -> Sunday close (UTC), entry Sunday close
fri = np.where(dow == 4)[0]
events = []
for i in fri:
    if i + 2 >= len(c):
        continue
    if dow[i + 2] != 6:                       # need Sat+Sun bars present
        continue
    wmove = np.log(c.iloc[i + 2] / c.iloc[i])
    events.append((i + 2, wmove))             # entry index = Sunday bar
print(f"weekend events: {len(events)}")

# midweek diagnostic events: Tue close -> Wed close move, entry Wed close
wed = np.where(dow == 2)[0]
diag_events = []
for i in wed:
    if i - 1 < 0 or dow[i - 1] != 1 or i + 2 >= len(c):
        continue
    diag_events.append((i, np.log(c.iloc[i] / c.iloc[i - 1])))
print(f"midweek diagnostic events: {len(diag_events)}")

cut = events[int(len(events) * 0.75)][0]      # OOS from this bar index
print(f"OOS from {c.index[cut].date()}")


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


def run(evts, filt, hold):
    pnls, sigs, ooss = [], [], []
    for i, mv in evts:
        s = sig63.iloc[i]
        if not np.isfinite(s) or s <= 0 or mv == 0:
            continue
        if filt == "sig" and abs(mv) < 1.0 * s:
            continue
        if i + hold >= len(c):
            continue
        fwd = np.log(c.iloc[i + hold] / c.iloc[i])
        pnls.append((-np.sign(mv) * fwd) * 1e4 - COST_BPS)
        sigs.append(s); ooss.append(i >= cut)
    return pd.DataFrame(dict(pnl=pnls, sig=sigs, oos=ooss))


CELLS = [("wknd", f, h) for f in ("any", "sig") for h in (1, 2)] + \
        [("mid_diag", "any", h) for h in (1, 2)]

rows = []
for kind, filt, hold in CELLS:
    sub = run(events if kind == "wknd" else diag_events, filt, hold)
    rows.append(dict(kind=kind, filt=filt, hold=hold, selectable=(kind == "wknd"),
                     IS=stats(sub.pnl[~sub.oos], sub.sig[~sub.oos], hold),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.sig[sub.oos], hold), _sub=sub, _hold=hold))

print("\n=== IS grid (BTC, reversion vs weekend move; bps net of 5bp RT) ===")
print(f"{'kind':>9} {'filt':>4} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avg bps':>8} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['kind']:>9} {r['filt']:>4} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.1f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= (120 if r["filt"] == "any" else 40)],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel if r["filt"] == cand["filt"] and r is not cand][0]
    if (sib["IS"].get("avg_bps") or -1) > 0:
        winner = cand
        break
if winner is not None:
    dg = [r for r in rows if r["kind"] == "mid_diag" and r["hold"] == winner["hold"]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_bps") or 9e9) < (winner["IS"].get("avg_bps") or -9e9)
    if not verdict["diag_below"]:
        print("\nWinner matched by midweek diagnostic: generic daily mean-reversion, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r57_btcweekend.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['filt']} hold{winner['hold']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.sig, winner["_hold"])
c15 = stats(oos.pnl - 0.5 * COST_BPS, oos.sig, winner["_hold"])
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avg {o.get('avg_bps',float('nan')):+.1f}bps t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avg {c15.get('avg_bps',float('nan')):+.1f}bps t {c15.get('t',float('nan')):+.2f}")
nfloor = 40 if winner["filt"] == "any" else 25
PASS = (o.get("n", 0) >= nfloor and (o.get("avg_bps") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_bps") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"filt": winner["filt"], "hold": winner["hold"], "IS": winner["IS"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r57_btcweekend.json", "w"), indent=1, default=float)
