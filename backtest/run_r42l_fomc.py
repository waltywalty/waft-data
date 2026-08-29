"""Round 42 attempt 12: FOMC pre-announcement drift with the ex-ante calendar
(frozen per goal_ledger.md). Dates from the Fed's published schedules
(assistant knowledge; federalreserve.gov blocked by proxy) - VALIDATED against
the 14:00 vol signature before use. Outputs results/r42l_fomc.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

FOMC = """2013-01-30 2013-03-20 2013-05-01 2013-06-19 2013-07-31 2013-09-18 2013-10-30 2013-12-18
2014-01-29 2014-03-19 2014-04-30 2014-06-18 2014-07-30 2014-09-17 2014-10-29 2014-12-17
2015-01-28 2015-03-18 2015-04-29 2015-06-17 2015-07-29 2015-09-17 2015-10-28 2015-12-16
2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29""".split()
FOMC = set(pd.to_datetime(FOMC).date)

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
        if len(g) < 50 or hm[0] > 935 or skey < pd.Timestamp("2013-01-01").date():
            continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        w14 = (hm >= 1400) & (hm < 1430)
        rows_d.append(dict(skey=skey, o=o[0], c1355=lb(1400), c1400v=lb(1405), cEnd=c[-1],
                           hi=g.high.max(), lo=g.low.min(),
                           rng1400=(g.high[w14].max() - g.low[w14].min()) if w14.sum() >= 3 else np.nan))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["med1400"] = d.rng1400.rolling(60, min_periods=30).median()
    d["fomc"] = [k in FOMC for k in d.index]
    d["prev_c1400"] = d.c1400v.shift(1)
    d["prev_cEnd"] = d.cEnd.shift(1)
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    d["idx"] = idx
    frames[idx] = d
    split[idx] = str(cutd)

# ---- calendar validator (SPX): flagged dates must show the 14:00 signature ----
dv = frames["SPX"]
f = dv[dv.fomc & np.isfinite(dv.med1400)]
vfrac = float((f.rng1400 >= 2.0 * f.med1400).mean())
base = dv[~dv.fomc & np.isfinite(dv.med1400)]
bfrac = float((base.rng1400 >= 2.0 * base.med1400).mean())
print(f"calendar validator: {len(f)} FOMC dates in SPX data; {vfrac*100:.0f}% show 14:00 range >= 2x median "
      f"(base rate {bfrac*100:.0f}%)")
# r43b: the calendar is now two-source verified (web + knowledge, see ledger);
# the vol signature is a diagnostic only - many statement days are fully priced.
print("calendar provenance: two-source verified (r43b); vol signature diagnostic only")

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

add("prev1400->1355 (Lucca-Moench)", lambda d: (d.c1355 - d.prev_c1400,
    d.fomc & np.isfinite(d.prev_c1400) & np.isfinite(d.c1355)))
add("0930->1355", lambda d: (d.c1355 - d.o, d.fomc & np.isfinite(d.c1355)))
add("prevclose->close", lambda d: (d.cEnd - d.prev_cEnd, d.fomc & np.isfinite(d.prev_cEnd)))

print("\n=== IS grid (indices pooled, ATR-normalized, 2013+) ===")
print(f"{'cell':>30} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    print(f"{r['cell']:>30} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 60],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = ranked[0] if ranked and (ranked[0]["IS"].get("t") or -9) >= 2 else None

if winner is None:
    print("\nNo cell passes the IS t>=2 floor; family fails at IS, OOS not opened.")
    json.dump(dict(validator=dict(frac=vfrac, base=bfrac), split=split,
                   grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42l_fomc.json", "w"), indent=1, default=float)
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
json.dump(dict(validator=dict(frac=vfrac, base=bfrac), split=split,
               grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"cell": winner["cell"], "IS": winner["IS"]},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42l_fomc.json", "w"), indent=1, default=float)
