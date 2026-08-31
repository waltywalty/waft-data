"""Round 60 attempt 42: leveraged-money positioning extremes (frozen per
reference/goal_ledger.md). 4 selectable cells + mid-band diagnostics,
single OOS evaluation. Outputs results/r60_tff.json."""
import pandas as pd, numpy as np, json, warnings, datetime as dt
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

SPLICE = {"SPX": ["E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
                  "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"],
          "NDX": ["NASDAQ-100 STOCK INDEX (MINI) - CHICAGO MERCANTILE EXCHANGE",
                  "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE"],
          "RTY": ["RUSSELL 2000 MINI INDEX FUTURE - ICE FUTURES U.S.",
                  "E-MINI RUSSELL 2000 INDEX - CHICAGO MERCANTILE EXCHANGE",
                  "RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE"]}

t = pd.read_csv("data/cftc_tff_indices.csv", parse_dates=["date"])
sig = {}
for idx, names in SPLICE.items():
    s = t[t.market.isin(names)].sort_values("date").drop_duplicates("date", keep="last")
    net = (s.lev_l - s.lev_s) / s.oi.replace(0, np.nan)
    ser = pd.Series(net.values, index=s.date.dt.date)
    pct = ser.rolling(156).rank(pct=True)
    sig[idx] = pct.dropna()
    print(f"{idx}: {len(ser)} report weeks, {len(sig[idx])} with 156w percentile "
          f"({sig[idx].index[0]}..{sig[idx].index[-1]})")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    return d


frames = {idx: build_days(idx) for idx in MICRO}
all_reports = sorted(set().union(*[set(s.index) for s in sig.values()]))
cutw = all_reports[int(len(all_reports) * 0.75)]
print(f"OOS from report week {cutw}")


def stats(p, a, floor=10):
    r = np.asarray(p, float) / np.asarray(a, float)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < floor: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def run(lo, hi, side, hold):
    pnls, atrs, ooss = [], [], []
    for idx, pct in sig.items():
        d = frames[idx]
        keys = d.index.tolist()
        kset = pd.Series(range(len(keys)), index=keys)
        busy = -1
        for rep, p in pct.items():
            if not (lo <= p <= hi):
                continue
            entry_day = rep + dt.timedelta(days=6)
            i = np.searchsorted(keys, entry_day)
            if i >= len(keys) or (keys[i] - entry_day).days > 5:
                continue
            j = i + hold
            if i <= busy or j >= len(keys):
                continue
            e, xp, a = d.o.iloc[i], d.c.iloc[j], d.atr20.iloc[i]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            pnls.append(side * (xp - e) - MICRO[idx])
            atrs.append(a); ooss.append(rep >= cutw)
            busy = j
    return pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss))


CELLS = [("lo_long", -0.01, 0.10, +1, 5, True), ("lo_long", -0.01, 0.10, +1, 20, True),
         ("hi_short", 0.90, 1.01, -1, 5, True), ("hi_short", 0.90, 1.01, -1, 20, True),
         ("mid_diag", 0.40, 0.60, +1, 5, False), ("mid_diag", 0.40, 0.60, +1, 20, False)]

rows = []
for name, lo, hi, side, hold, sel in CELLS:
    sub = run(lo, hi, side, hold)
    rows.append(dict(cell=name, hold=hold, side=("short" if side < 0 else "long"), selectable=sel,
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (indices pooled, ATR-normalized; mid-band diagnostic) ===")
print(f"{'cell':>9} {'hold':>4} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['cell']:>9} {r['hold']:>4} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

sel_rows = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel_rows if r["IS"].get("n", 0) >= 40],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel_rows if r["cell"] == cand["cell"] and r is not cand][0]
    if (sib["IS"].get("avg_R") or -1) > 0:
        winner = cand
        break
if winner is not None:
    dg = [r for r in rows if r["cell"] == "mid_diag" and r["hold"] == winner["hold"]][0]
    verdict["mid_below"] = (dg["IS"].get("avg_R") or 9e9) < (winner["IS"].get("avg_R") or -9e9)
    if not verdict["mid_below"]:
        print("\nWinner matched by mid-band diagnostic: not an extremes effect, self-refuted at IS.")
        winner = None

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r60_tff.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['cell']} hold{winner['hold']}")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * np.mean(list(MICRO.values())), oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 25 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"cell": winner["cell"], "hold": winner["hold"], "IS": winner["IS"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r60_tff.json", "w"), indent=1, default=float)
