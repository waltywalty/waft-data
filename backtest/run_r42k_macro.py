"""Round 42 attempt 11: macro-announcement-day equity premium (frozen per
goal_ledger.md). Outputs results/r42k_macro.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

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
        c, o = g.close.values, g.open.values
        if len(g) < 50 or hm[0] > 935: continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        w1400 = (hm >= 1400) & (hm < 1430)
        rng1400 = (g.high[w1400].max() - g.low[w1400].min()) if w1400.sum() >= 3 else np.nan
        rows_d.append(dict(skey=skey, o=o[0], c0800=np.nan, c1200=lb(1200),
                           c1355=lb(1400), c1400=lb(1405), cEnd=c[-1],
                           hi=g.high.max(), lo=g.low.min(), rng1400=rng1400))
    b24 = load_frame(idx)
    pre = {}
    for skey, g in b24.groupby("skey"):
        m = g.hm.values
        i8 = np.where(m == 800)[0]
        pre[skey] = g.open.values[i8[0]] if len(i8) else np.nan
    d = pd.DataFrame(rows_d).set_index("skey")
    d["c0800"] = pd.Series(d.index.map(lambda k: pre.get(k, np.nan)), index=d.index)
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["med1400"] = d.rng1400.rolling(60, min_periods=30).median()
    dts = pd.to_datetime(pd.Series(d.index, index=d.index).astype(str))
    d["nfp"] = (dts.dt.dayofweek == 4) & (dts.dt.day <= 7)
    d["friday"] = dts.dt.dayofweek == 4
    d["prev_c1355"] = d.c1355.shift(1)
    d["prev_c1400"] = d.c1400.shift(1)
    d["prev_cEnd"] = d.cEnd.shift(1)
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    d["idx"] = idx
    frames[idx] = d
    split[idx] = str(cutd)
    for th in (2.5, 3.5):
        f = d[d.rng1400 >= th * d.med1400]
        print(f"{idx}: FOMC-like days at x{th}: {len(f)} ({len(f)/ (len(d)/252):.1f}/yr)")

rows = []
def add(name, legfn):
    subs = []
    for idx, d in frames.items():
        pnl, m = legfn(d)
        s = d[m]
        subs.append(pd.DataFrame(dict(pnl=pnl[m] - MICRO[idx], atr=s.atr20, oos=s.oos, idx=idx)))
    sub = pd.concat(subs, ignore_index=True)
    rows.append(dict(cell=name, IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

add("NFP prevclose->close", lambda d: (d.cEnd - d.prev_cEnd, d.nfp & np.isfinite(d.prev_cEnd)))
add("NFP 0800->1200", lambda d: (d.c1200 - d.c0800, d.nfp & np.isfinite(d.c0800) & np.isfinite(d.c1200)))
add("NFP 0930->close", lambda d: (d.cEnd - d.o, d.nfp))
add("CTRL otherFri prevclose->close", lambda d: (d.cEnd - d.prev_cEnd, d.friday & ~d.nfp & np.isfinite(d.prev_cEnd)))
for th in (2.5, 3.5):
    add(f"FOMC{th} prev1400->1355", lambda d, t=th: (d.c1355 - d.prev_c1400,
        (d.rng1400 >= t * d.med1400) & np.isfinite(d.prev_c1400) & np.isfinite(d.c1355)))
    add(f"FOMC{th} 0930->1355", lambda d, t=th: (d.c1355 - d.o,
        (d.rng1400 >= t * d.med1400) & np.isfinite(d.c1355)))

print("\n=== IS grid (indices pooled, ATR-normalized; CTRL not selectable) ===")
print(f"{'cell':>32} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['cell']:>32} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel = [r for r in rows if not r["cell"].startswith("CTRL") and r["IS"].get("n", 0) >= 120]
ranked = sorted(sel, key=lambda r: -(r["IS"].get("t") or -99))
winner = None
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    winner = cand
    break

if winner is None:
    print("\nNo cell passes the IS t>=2 floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42k_macro.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['cell']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
    s = oos[oos.idx == idx]; per[idx] = stats(s.pnl, s.atr); v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"cell": winner["cell"], "IS": winner["IS"]},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42k_macro.json", "w"), indent=1, default=float)
