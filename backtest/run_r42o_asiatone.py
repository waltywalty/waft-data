"""Round 42 attempt 15: Asia-close risk tone -> US RTH session (frozen per
goal_ledger.md). Outputs results/r42o_asiatone.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

def asia_daily(name):
    # LOOKAHEAD FIX (audit of the first run): these are 24h CFD feeds, so the
    # last bar of a UTC date is ~23:00 UTC (7pm ET) - AFTER the US close. The
    # signal must be known before 09:30 ET, so the Asia "close" is the last
    # bar at or before 08:00 UTC (HK cash close; 5.5h before the NY open).
    df = pd.read_csv(f"data/{name}")
    ts = pd.to_datetime(df.datetime, utc=True)
    s = pd.Series(df.close.values, index=ts).sort_index()
    s = s[s.index.hour <= 8]
    d = s.groupby(s.index.date).last()
    r = pd.Series(d).pct_change()
    sig = r.rolling(20).std()
    return r, sig

rj, sj = asia_daily("JP225_H1.csv")
rh, sh = asia_daily("HK33_H1.csv")

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
for idx in MICRO:
    rth = rth_of(load_frame(idx))
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        if len(g) < 50 or hm[0] > 935: continue
        m12 = np.where(hm < 1200)[0]
        rows_d.append(dict(skey=skey, o=g.open.values[0],
                           c12=g.close.values[m12[-1]] if len(m12) else np.nan,
                           cEnd=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["rj"] = pd.to_numeric(d.index.map(lambda k: rj.get(k, np.nan)), errors="coerce")
    d["rh"] = pd.to_numeric(d.index.map(lambda k: rh.get(k, np.nan)), errors="coerce")
    d["sj"] = pd.to_numeric(d.index.map(lambda k: sj.get(k, np.nan)), errors="coerce")
    d["sh"] = pd.to_numeric(d.index.map(lambda k: sh.get(k, np.nan)), errors="coerce")
    d = d[np.isfinite(d.rj) & np.isfinite(d.rh) & np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    d["idx"] = idx
    frames[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} joined sessions, OOS from {cutd}")

rows = []
for filt, fname in ((False, "any"), (True, "0.5sig")):
    for xcol, hname in (("c12", "0930-1200"), ("cEnd", "0930-close")):
        subs = []
        for idx, d in frames.items():
            agree = (np.sign(d.rj) == np.sign(d.rh)) & (np.sign(d.rj) != 0)
            m = agree & np.isfinite(d[xcol])
            if filt:
                m &= (d.rj.abs() >= 0.5 * d.sj) & (d.rh.abs() >= 0.5 * d.sh)
            side = np.sign(d.rj[m])
            pnl = side * (d[xcol][m] - d.o[m]) - MICRO[idx]
            sub = pd.DataFrame(dict(pnl=pnl, atr=d.atr20[m], oos=d.oos[m], idx=idx))
            subs.append(sub)
        sub = pd.concat(subs, ignore_index=True)
        rows.append(dict(filt=fname, hold=hname,
                         IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                         OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (indices pooled, ATR-normalized) ===")
print(f"{'filt':>7} {'hold':>11} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['filt']:>7} {r['hold']:>11} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("filt", "hold")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42o_asiatone.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['filt']} {winner['hold']} (neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("filt", "hold", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42o_asiatone.json", "w"), indent=1, default=float)
