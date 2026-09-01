"""Round 63 attempt 46: labor-deterioration regime, Sahm-style gap
(frozen per reference/goal_ledger.md). 4 selectable cells + improving
diagnostics + independence gate vs mfg-PMI regime, single OOS
evaluation. Outputs results/r63_sahm.json."""
import pandas as pd, numpy as np, json, datetime as dt, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

u = pd.read_csv("data/UNRATE_av.csv", parse_dates=["timestamp"]).set_index("timestamp").value
u = u.interpolate(limit=1)                      # 2025-10 shutdown gap, declared in ledger
ma3 = u.rolling(3).mean()
gap = ma3 - ma3.rolling(12).min().shift(1)      # 3m MA vs its min over prior 12 months
# month-M value known from the 8th of month M+1
known = [(ts + pd.offsets.MonthBegin(1) + pd.Timedelta(days=7)).date() for ts in gap.index]
rel = sorted(zip(known, gap.values))
rel = [(k, g) for k, g in rel if np.isfinite(g)]
print(f"gap series: {len(rel)} months, {rel[0][0]}..{rel[-1][0]}, "
      f">=0.5: {sum(1 for _, g in rel if g >= 0.5)}, >=0.3: {sum(1 for _, g in rel if g >= 0.3)}")

ev = json.loads(open("data/econ_events_us_high_fxs.json").read()
                [open("data/econ_events_us_high_fxs.json").read().find("{"):])["result"]["events"]
mfg = []
for e in ev:
    if (e.get("n") or "") == "ISM Manufacturing PMI" and e.get("a") is not None:
        et = pd.Timestamp(e["d"]).tz_convert("America/New_York").tz_localize(None)
        mfg.append((et.date(), float(e["a"])))
mfg.sort()


def last_before(r, keys):
    lvl, j, out = np.nan, 0, []
    for k in keys:
        while j < len(r) and r[j][0] < k:
            lvl = r[j][1]; j += 1
        out.append(lvl)
    return out


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d = d[[k >= rel[0][0] for k in d.index]]
    keys = d.index.tolist()
    d["gap"] = last_before(rel, keys)
    d["mfg"] = last_before(mfg, keys)           # NaN before 2013 feed start
    mfg_known = [k >= mfg[0][0] for k in keys]
    d["mfg_defined"] = mfg_known
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d


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


frames = {idx: build_days(idx) for idx in MICRO}
for idx, d in frames.items():
    print(f"{idx}: {len(d)} sessions ({d.index.tolist()[0]}..{d.index.tolist()[-1]}), "
          f"gap>=0.5 share {(d.gap >= 0.5).mean()*100:.0f}%, "
          f"OOS from {d.index.tolist()[int(len(d)*0.75)]}")


def run(thr, group):
    pnls, atrs, ooss, nomfg = [], [], [], []
    for idx, d in frames.items():
        if group == "RTY" and idx != "RTY":
            continue
        m = np.isfinite(d.gap) & np.isfinite(d.prevc) & np.isfinite(d.atr20) & (d.atr20 > 0)
        if thr == "imp":
            m &= d.gap <= 0.05
        else:
            m &= d.gap >= thr
        s = d[m]
        pnls += list((s.c - s.prevc) - MICRO[idx] / 20)
        atrs += list(s.atr20); ooss += list(s.oos)
        # independence gate: defined-and-outside mfg contraction (pre-2013 excluded)
        nomfg += list(s.mfg_defined & ~(s.mfg < 50))
    return pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, nomfg=nomfg))


CELLS = [(0.50, "pooled", True), (0.50, "RTY", True), (0.30, "pooled", True), (0.30, "RTY", True),
         ("imp", "pooled", False), ("imp", "RTY", False)]
rows = []
for thr, grp, sel in CELLS:
    sub = run(thr, grp)
    rows.append(dict(thr=str(thr), group=grp, selectable=sel,
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     IS_nomfg=stats(sub.pnl[~sub.oos & sub.nomfg], sub.atr[~sub.oos & sub.nomfg]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (daily bookings, ATR-normalized; improving cells diagnostic) ===")
print(f"{'thr':>5} {'group':>7} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | nomfg avgR")
for r in rows:
    a, b = r["IS"], r["IS_nomfg"]
    if a.get("n", 0) < 10: continue
    print(f"{r['thr']:>5} {r['group']:>7} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | "
          f"{b.get('avg_R', float('nan')):+.3f} (n{b.get('n')})")

sel_rows = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel_rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = [r for r in sel_rows if (r["thr"] == cand["thr"]) != (r["group"] == cand["group"])
           and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in sib if (r["IS"].get("avg_R") or -1) > 0)
    if len(sib) == 0 or pos >= len(sib) / 2:
        winner = cand
        break
if winner is not None:
    dg = [r for r in rows if r["thr"] == "imp" and r["group"] == winner["group"]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_R") or 9e9) < (winner["IS"].get("avg_R") or -9e9)
    if not verdict["diag_below"]:
        print("\nWinner matched by improving-labor diagnostic: generic drift, self-refuted at IS.")
        winner = None
if winner is not None:
    verdict["independent"] = (winner["IS_nomfg"].get("n", 0) < 30) or \
                             (winner["IS_nomfg"].get("avg_R") or -1) > 0
    if not verdict["independent"]:
        print("\nIndependence gate FAILED: non-overlap subset not positive at IS."
              "\nFamily SUBSUMED by attempt 44's mfg-PMI regime; OOS seal NOT opened, no shot spent.")
        json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                       winner={"thr": winner["thr"], "group": winner["group"], "IS": winner["IS"],
                               "IS_nomfg": winner["IS_nomfg"]},
                       gate_pass=False, subsumed=True, verdict=verdict),
                  open("results/r63_sahm.json", "w"), indent=1, default=float)
        raise SystemExit

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r63_sahm.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: gap >= {winner['thr']} {winner['group']} "
      f"(independence: nomfg IS avgR {winner['IS_nomfg'].get('avg_R', float('nan')):+.3f})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * np.mean(list(MICRO.values())) / 20, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"thr": winner["thr"], "group": winner["group"], "IS": winner["IS"],
                       "IS_nomfg": winner["IS_nomfg"]},
               oos=o, oos_cost15=c15, gate_pass=bool(PASS), verdict=verdict),
          open("results/r63_sahm.json", "w"), indent=1, default=float)
