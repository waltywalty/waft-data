"""Round 42 attempt 16: gold/silver RV session reversion (frozen per
goal_ledger.md). Outputs results/r42p_gsrv.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST_BPS = 4.0

# gold: 16:00 ET session closes + intraday 09:30/12:00/16:00 marks from 5m
g = load_frame("GOLD")
grows = []
for skey, gg in g.groupby("skey"):
    hm = gg.hm.values
    c, o = gg.close.values, gg.open.values
    def at(t0, kind="o"):
        m = np.where(hm >= t0)[0]
        return (o if kind == "o" else c)[m[0]] if len(m) else np.nan
    def lastb(t1):
        m = np.where(hm < t1)[0]
        return c[m[-1]] if len(m) else np.nan
    grows.append(dict(skey=skey, g930=at(930), g16=lastb(1600), gEnd=c[-1]))
gd = pd.DataFrame(grows).set_index("skey")

# silver H1 (UTC): session close = last bar before 20:00 UTC (16:00 EDT) per
# calendar date; 09:30 ET mark = first bar at/after 13:00 UTC (13:30 rounded to H1)
sv = pd.read_csv("data/XAGUSD_H1.csv")
ts = pd.to_datetime(sv.datetime, utc=True)
s = pd.Series(sv.close.values, index=ts).sort_index()
sny = s.tz_convert("America/New_York")
srows = {}
for day, gg in sny.groupby(sny.index.date):
    hh = gg.index.hour * 100 + gg.index.minute
    m16 = np.where(hh < 1600)[0]
    m930 = np.where(hh >= 900)[0]          # H1 granularity: 09:00 or 10:00 bar
    srows[day] = (gg.values[m930[0]] if len(m930) else np.nan,
                  gg.values[m16[-1]] if len(m16) else np.nan)
sd = pd.DataFrame.from_dict(srows, orient="index", columns=["s930", "s16"])

d = gd.join(sd, how="inner")
for col in d.columns:
    d[col] = pd.to_numeric(d[col], errors="coerce")
d = d.dropna(subset=["g16", "s16"])
d["rg"] = np.log(d.g16).diff()
d["rs"] = np.log(d.s16).diff()
d["spr"] = d.rg - d.rs
d["sig20"] = d.spr.rolling(20).std()
d["ev"] = d.spr.shift(1)                     # yesterday's divergence
d["sig_prior"] = d.sig20.shift(1)
d = d[np.isfinite(d.ev) & np.isfinite(d.sig_prior) & (d.sig_prior > 0)]
cutd = d.index.tolist()[int(len(d) * 0.75)]
d["oos"] = pd.Series(d.index >= cutd, index=d.index)
print(f"pair sessions: {len(d)}, OOS from {cutd}")
print("signal availability: complete at prior 16:00 ET close; entry next 09:30 ET - OK")

# session-leg returns for the holds
d["rg_rth"] = np.log(d.g16) - np.log(d.g930)
d["rs_rth"] = np.log(d.s16) - np.log(d.s930)
d["rg_full"] = np.log(d.gEnd) - np.log(d.g930)   # to that session's final close
d["rs_full"] = d.rs_rth                          # H1 silver: 16:00 is the honest last mark

def stats(pnl_bps, sig):
    p = np.asarray(pnl_bps, float)
    r = p / (np.asarray(sig, float) * 1e4)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_bps=float(p.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

rows = []
for k in (1.0, 1.5, 2.0):
    for hold, hname in (("rth", "RTH"), ("full", "full")):
        m = d.ev.abs() >= k * d.sig_prior
        side = -np.sign(d.ev[m])                 # convergence
        rg_h = d[f"rg_{hold}"][m]
        rs_h = d[f"rs_{hold}"][m]
        pnl = (side * (rg_h - rs_h)) * 1e4 - COST_BPS
        sub = pd.DataFrame(dict(pnl=pnl, sig=d.sig_prior[m], oos=d.oos[m]))
        rows.append(dict(k=k, hold=hname,
                         IS=stats(sub.pnl[~sub.oos], sub.sig[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.sig[sub.oos]), _sub=sub))

print("\n=== IS grid (spread bps net of 4bp cost; t on sigma-normalized) ===")
print(f"{'k':>4} {'hold':>5} | {'n':>4} {'WR':>6} {'PF':>5} {'avg bps':>8} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['k']:>4} {r['hold']:>5} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.2f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("k", "hold")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_bps") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42p_gsrv.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: k{winner['k']} {winner['hold']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.sig)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avg {o.get('avg_bps',float('nan')):+.2f}bps t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * COST_BPS, oos.sig)
print(f"cost x1.5: avg {c15.get('avg_bps',float('nan')):+.2f}bps t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_bps") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_bps") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("k", "hold", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42p_gsrv.json", "w"), indent=1, default=float)
