"""Round 62 attempt 45: consumer-pessimism regime, Michigan sentiment
(frozen per reference/goal_ledger.md). 4 selectable cells + optimism
diagnostics + independence gate vs mfg-PMI regime, single OOS
evaluation. Outputs results/r62_mich.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

ev = json.loads(open("data/econ_events_us_high_fxs.json").read()
                [open("data/econ_events_us_high_fxs.json").read().find("{"):])["result"]["events"]


def releases(name):
    out = []
    for e in ev:
        if (e.get("n") or "") == name and e.get("a") is not None:
            et = pd.Timestamp(e["d"]).tz_convert("America/New_York").tz_localize(None)
            out.append((et.date(), float(e["a"])))
    out.sort()
    return out


mich = releases("Michigan Consumer Sentiment Index")
mfg = releases("ISM Manufacturing PMI")
print(f"Michigan releases: {len(mich)} ({mich[0][0]}..{mich[-1][0]}), "
      f"<65: {sum(1 for _, v in mich if v < 65)}, <70: {sum(1 for _, v in mich if v < 70)}, "
      f">=85: {sum(1 for _, v in mich if v >= 85)}")


def last_before(rel, keys):
    lvl, j, out = np.nan, 0, []
    for k in keys:
        while j < len(rel) and rel[j][0] < k:
            lvl = rel[j][1]; j += 1
        out.append(lvl)
    return out


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d = d[[k >= mich[0][0] for k in d.index]]
    keys = d.index.tolist()
    d["sent"] = last_before(mich, keys)
    d["mfg"] = last_before(mfg, keys)
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
    print(f"{idx}: {len(d)} sessions, pessimism<65 share {(d.sent < 65).mean()*100:.0f}%, "
          f"OOS from {d.index.tolist()[int(len(d)*0.75)]}")


def run(thr, group):
    pnls, atrs, ooss, nomfg = [], [], [], []
    for idx, d in frames.items():
        if group == "RTY" and idx != "RTY":
            continue
        m = np.isfinite(d.sent) & np.isfinite(d.prevc) & np.isfinite(d.atr20) & (d.atr20 > 0)
        if thr == "opt":
            m &= d.sent >= 85
        else:
            m &= d.sent < thr
        s = d[m]
        pnls += list((s.c - s.prevc) - MICRO[idx] / 20)
        atrs += list(s.atr20); ooss += list(s.oos)
        nomfg += list(~(s.mfg < 50))          # outside mfg-contraction regime
    return pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, nomfg=nomfg))


CELLS = [(65, "pooled", True), (65, "RTY", True), (70, "pooled", True), (70, "RTY", True),
         ("opt", "pooled", False), ("opt", "RTY", False)]
rows = []
for thr, grp, sel in CELLS:
    sub = run(thr, grp)
    rows.append(dict(thr=str(thr), group=grp, selectable=sel,
                     IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                     IS_nomfg=stats(sub.pnl[~sub.oos & sub.nomfg], sub.atr[~sub.oos & sub.nomfg]),
                     OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]), _sub=sub))

print("\n=== IS grid (daily bookings, ATR-normalized; optimism cells diagnostic) ===")
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
    dg = [r for r in rows if r["thr"] == "opt" and r["group"] == winner["group"]][0]
    verdict["diag_below"] = (dg["IS"].get("avg_R") or 9e9) < (winner["IS"].get("avg_R") or -9e9)
    if not verdict["diag_below"]:
        print("\nWinner matched by optimism diagnostic: generic drift, self-refuted at IS.")
        winner = None
if winner is not None:
    # independence gate: IS avgR outside mfg-contraction regime must be positive
    verdict["independent"] = (winner["IS_nomfg"].get("avg_R") or -1) > 0
    if not verdict["independent"]:
        print("\nIndependence gate FAILED: non-overlap subset not positive at IS."
              "\nFamily SUBSUMED by attempt 44's mfg-PMI regime; OOS seal NOT opened, no shot spent.")
        json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                       winner={"thr": winner["thr"], "group": winner["group"], "IS": winner["IS"],
                               "IS_nomfg": winner["IS_nomfg"]},
                       gate_pass=False, subsumed=True, verdict=verdict),
                  open("results/r62_mich.json", "w"), indent=1, default=float)
        raise SystemExit

if winner is None:
    print("\nNo selectable cell passes floors + diagnostics; family fails at IS, OOS not opened.")
    json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False, verdict=verdict),
              open("results/r62_mich.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: thr {winner['thr']} {winner['group']} "
      f"(independence gate passed: nomfg IS avgR {winner['IS_nomfg'].get('avg_R'):+.3f})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
c15 = stats(oos.pnl - 0.5 * np.mean(list(MICRO.values())) / 20, oos.atr)
onm = stats(oos.pnl[oos.nomfg], oos.atr[oos.nomfg])
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
print(f"OOS outside mfg regime: avgR {onm.get('avg_R',float('nan')):+.3f} "
      f"t {onm.get('t',float('nan')):+.2f} (n{onm.get('n')})")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={"thr": winner["thr"], "group": winner["group"], "IS": winner["IS"],
                       "IS_nomfg": winner["IS_nomfg"]},
               oos=o, oos_cost15=c15, oos_nomfg=onm, gate_pass=bool(PASS), verdict=verdict),
          open("results/r62_mich.json", "w"), indent=1, default=float)
