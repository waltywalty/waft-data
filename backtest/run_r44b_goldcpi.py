"""Round 44 attempt 18: gold vs CPI surprises (frozen per goal_ledger.md).
Outputs results/r44b_goldcpi.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST = 0.35
CPI = {"Consumer Price Index (YoY)", "Consumer Price Index (MoM)",
       "Consumer Price Index ex Food & Energy (YoY)",
       "Consumer Price Index ex Food & Energy (MoM)"}

raw = open("data/econ_events_us_high_fxs.json").read()
d = json.loads(raw[raw.find('{'):])
if "result" in d: d = d["result"]
evs = {}
for e in d["events"]:
    if e["n"] not in CPI or e["dev"] is None: continue
    k = pd.Timestamp(e["d"])
    if k not in evs or abs(e["dev"]) > abs(evs[k]["dev"]):
        evs[k] = dict(t=k, dev=float(e["dev"]))
evs = sorted(evs.values(), key=lambda e: e["t"])

def stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 8: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

b = load_frame("GOLD").tz_convert("UTC")
atr = (b.groupby("skey").high.max() - b.groupby("skey").low.min()).rolling(20).mean().shift(1)
keys = sorted(atr.index)
cutd = keys[int(len(keys) * 0.75)]
ix = b.index
rows = []
for th in (0.25, 0.5):
    for hold in ("60m", "close"):
        pnls, atrs, ooss = [], [], []
        for e in evs:
            if abs(e["dev"]) < th: continue
            i0 = ix.searchsorted(e["t"] + pd.Timedelta(minutes=5))
            if i0 >= len(ix) or (ix[i0] - e["t"]) > pd.Timedelta(hours=2): continue
            skey = b.skey.iloc[i0]
            a20 = atr.get(skey, np.nan)
            if not np.isfinite(a20) or a20 <= 0: continue
            entry = b.close.iloc[i0]
            if hold == "60m":
                i1 = ix.searchsorted(ix[i0] + pd.Timedelta(minutes=60))
                if i1 >= len(ix): continue
                exitpx = b.close.iloc[min(i1, len(ix) - 1)]
            else:
                day = b[b.skey == skey]
                hmny = day.index.tz_convert("America/New_York")
                m16 = day[(hmny.hour * 100 + hmny.minute) < 1600]
                if not len(m16): continue
                exitpx = m16.close.iloc[-1]
            side = -np.sign(e["dev"])
            pnls.append(side * (exitpx - entry) - COST)
            atrs.append(a20); ooss.append(skey >= cutd)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss))
        rows.append(dict(th=th, hold=hold, IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print(f"CPI events joined to gold data: cells below (OOS from {cutd})")
print(f"{'th':>5} {'hold':>6} | {'n':>3} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 8: continue
    print(f"{r['th']:>5} {r['hold']:>6} | {a['n']:>3} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = ranked[0] if ranked and (ranked[0]["IS"].get("t") or -9) >= 2 else None
if winner is None:
    print("\nNo cell passes the IS floor (t>=2, n>=40); family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r44b_goldcpi.json", "w"), indent=1, default=float)
    raise SystemExit
print(f"\nSELECTED: th{winner['th']} {winner['hold']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"OOS: n {o.get('n')} avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} "
      f"PF {o.get('pf',float('nan')):.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
PASS = (o.get("n", 0) >= 25 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"OOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("th", "hold", "IS")}, oos=o, oos_cost15=c15,
               gate_pass=bool(PASS)),
          open("results/r44b_goldcpi.json", "w"), indent=1, default=float)
