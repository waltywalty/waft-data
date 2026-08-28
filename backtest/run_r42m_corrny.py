"""Round 42 attempt 13: corr-regime conditional London->NY gold continuation
(frozen per goal_ledger.md). Outputs results/r42m_corrny.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST = 0.35

b = load_frame("GOLD")
# daily gold closes by session for corr
gd = b.groupby("skey").close.last()
gd.index = pd.to_datetime(pd.Series(gd.index).astype(str))
# AUD daily: prefer the M15 collector feed's daily closes (recent span), FRED fallback
a = pd.read_csv("data/AUDUSD_daily_fred.csv")
ad = pd.Series(pd.to_numeric(a.iloc[:, 1], errors="coerce").values,
               index=pd.to_datetime(a.iloc[:, 0])).dropna()
# IS-stage data-source correction (disclosed in ledger): the M15 collector feed
# spans only ~15 months and truncated the join to 312 sessions; FRED daily AUD
# restores the registered full-span intent. OOS untouched at correction time.
common = gd.index.intersection(ad.index)
rg, ra = np.log(gd[common]).diff(), np.log(ad[common]).diff()
corr = rg.rolling(20).corr(ra).shift(1)          # prior-day corr, no lookahead
corr_by_date = {d.date(): v for d, v in corr.items()}

rows_d = []
for skey, g in b.groupby("skey"):
    hm = g.hm.values
    c, o = g.close.values, g.open.values
    def px(t0, t1):
        m = (hm >= t0) & (hm < t1)
        if m.sum() < 5: return np.nan, np.nan
        return o[np.argmax(m)], c[len(m) - 1 - np.argmax(m[::-1])]
    lo_, lc = px(300, 800)
    no, _ = px(930, 1000)
    _, c12 = px(930, 1200)
    _, c16 = px(930, 1600)
    rows_d.append(dict(skey=skey, lmove=(lc - lo_) if np.isfinite(lo_) else np.nan,
                       e=no, c12=c12, c16=c16, hi=g.high.max(), lo=g.low.min()))
d = pd.DataFrame(rows_d).set_index("skey")
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
d["creg"] = pd.to_numeric(pd.Series(d.index.map(lambda k: corr_by_date.get(k, np.nan)),
                                    index=d.index), errors="coerce")
for col in ("creg", "atr20", "lmove", "e", "c12", "c16"):
    d[col] = pd.to_numeric(d[col], errors="coerce")
d = d[np.isfinite(d.creg) & np.isfinite(d.atr20) & (d.atr20 > 0) & np.isfinite(d.lmove) & np.isfinite(d.e)]
cutd = d.index.tolist()[int(len(d) * 0.75)]
d["oos"] = d.index >= cutd
print(f"GOLD: {len(d)} sessions with corr+London data, OOS from {cutd}; "
      f"low-corr share {(d.creg <= 0.5).mean()*100:.0f}%")

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
for regime, rname, dirsign in ((d.creg <= 0.5, "lowcorr", +1), (d.creg > 0.5, "highcorr", -1)):
    for th, tname in ((None, "any"), (0.25, "0.25atr")):
        for xcol, hname in (("c12", "0930-1200"), ("c16", "0930-1600")):
            m = regime & (np.sign(d.lmove) != 0) & np.isfinite(d[xcol])
            if th is not None:
                m &= d.lmove.abs() >= th * d.atr20
            side = dirsign * np.sign(d.lmove[m])
            pnl = side * (d[xcol][m] - d.e[m]) - COST
            sub = pd.DataFrame(dict(pnl=pnl, atr=d.atr20[m], oos=d.oos[m]))
            rows.append(dict(regime=rname, th=tname, hold=hname,
                             IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                             OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (gold; low-corr FOLLOWS London, high-corr FADES it) ===")
print(f"{'regime':>9} {'th':>8} {'hold':>10} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['regime']:>9} {r['th']:>8} {r['hold']:>10} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if r["regime"] == cand["regime"]
          and sum(r[x] == cand[x] for x in ("th", "hold")) == 1 and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42m_corrny.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['regime']} {winner['th']} {winner['hold']} (in-regime neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
c15 = stats(oos.pnl - 0.5 * COST, oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("regime", "th", "hold", "IS")},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42m_corrny.json", "w"), indent=1, default=float)
