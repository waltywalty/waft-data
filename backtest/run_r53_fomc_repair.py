"""Round 53 attempt 34: FOMC horizon-match repair (frozen per
reference/goal_ledger.md Round 53 registration). IS-ONLY script: OOS rows
are masked before any statistic; no OOS code path exists here.
Outputs results/r53_fomc_repair_is.json."""
import pandas as pd, numpy as np, json, warnings, datetime as dt, re
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

lsrc = open("run_r42l_fomc.py").read()
FOMC = set(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', lsrc, re.S).group(1).split()).date)


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


frames = {}
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
        rows_d.append(dict(skey=skey, o=o[0], c1355=lb(1400), cEnd=c[-1],
                           hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prev_cEnd"] = d.cEnd.shift(1)
    d["fomc"] = [k in FOMC for k in d.index]
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    # IS-ONLY MASK: the sealed rows leave the frame here and never return
    frames[idx] = d[~d.oos].copy()
    print(f"{idx}: {len(d)} sessions -> {len(frames[idx])} IS rows (sealed rows dropped; cut {cutd})")

# legs: (name, pnl function per frame, cost multiplier)
LEGS = {"C1_ON": (lambda d: d.o - d.prev_cEnd, 1),
        "C2_PM": (lambda d: d.cEnd - d.c1355, 1),
        "C3_ONPM": (lambda d: (d.o - d.prev_cEnd) + (d.cEnd - d.c1355), 2)}
ANCHORS = {"anchor_fullday": lambda d: d.cEnd - d.prev_cEnd,
           "anchor_0930_1355": lambda d: d.c1355 - d.o}


def collect(dayflag_col, legname):
    fn, mult = LEGS.get(legname, (ANCHORS.get(legname), 1))
    subs = []
    for idx, d in frames.items():
        pnl = fn(d)
        m = d[dayflag_col] & np.isfinite(pnl)
        s = d[m]
        subs.append(pd.DataFrame(dict(pnl=pnl[m] - mult * MICRO[idx], atr=s.atr20,
                                      skey=s.index, idx=idx)))
    return pd.concat(subs, ignore_index=True)


# placebo days: session exactly 7 calendar days before each statement day
for idx, d in frames.items():
    kset = set(d.index)
    plc = set()
    for k in d.index[d.fomc]:
        p = k - dt.timedelta(days=7)
        if p in kset and p not in FOMC:
            plc.add(p)
    d["placebo"] = [k in plc for k in d.index]

rows, diag = [], []
for legname in LEGS:
    sub = collect("fomc", legname)
    rows.append(dict(cell=legname, IS=stats(sub.pnl, sub.atr), _sub=sub))
    psub = collect("placebo", legname)
    diag.append(dict(cell=legname + "_placebo", IS=stats(psub.pnl, psub.atr), _sub=psub))
anch = [dict(cell=a, IS=stats(collect("fomc", a).pnl, collect("fomc", a).atr)) for a in ANCHORS]

print("\n=== IS grid (indices pooled, ATR-normalized, 2013+ IS rows only) ===")
print(f"{'cell':>22} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows + diag + anch:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['cell']:>22} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner = ranked[0] if ranked and (ranked[0]["IS"].get("t") or -9) >= 2 else None
verdict = {}
if winner is not None:
    others = [r for r in rows if r is not winner]
    verdict["neighbors_positive"] = all((r["IS"].get("avg_R") or -1) > 0 for r in others)
    pc = [dd for dd in diag if dd["cell"] == winner["cell"] + "_placebo"][0]
    verdict["placebo_below"] = (pc["IS"].get("avg_R") or 9) < (winner["IS"].get("avg_R") or -9)
    # differential halves: pair each FOMC event with its placebo by instrument+date offset
    fsub, psub = winner["_sub"], pc["_sub"]
    fmap = {(r.idx, r.skey): r.pnl / r.atr for r in fsub.itertuples()}
    pmap = {(r.idx, r.skey + dt.timedelta(days=7)): r.pnl / r.atr for r in psub.itertuples()}
    pairs = sorted((k[1], fmap[k] - pmap[k]) for k in fmap if k in pmap)
    dv = [v for _, v in pairs]
    m = len(dv) // 2
    verdict["diff_halves"] = [float(np.sign(np.mean(dv[:m]))), float(np.sign(np.mean(dv[m:])))] if m >= 5 else None
    verdict["diff_both_positive"] = bool(verdict["diff_halves"] == [1.0, 1.0])
    morning = [a for a in anch if a["cell"] == "anchor_0930_1355"][0]
    verdict["morning_drag_nonpositive"] = (morning["IS"].get("avg_R") or 1) <= 0
    ALL = (verdict["neighbors_positive"] and verdict["placebo_below"]
           and verdict["diff_both_positive"] and verdict["morning_drag_nonpositive"])
    print(f"\nSELECTED: {winner['cell']} | gates: {verdict}")
    print(f"\nIS VERDICT: {'PASS - one OOS shot is earned' if ALL else 'FAIL - family dies at IS'}")
    verdict["is_pass"] = bool(ALL)
else:
    print("\nNo cell passes n>=120 & t>=2; family dies at IS.")
    verdict["is_pass"] = False

json.dump(dict(grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               diagnostics=[{x: v for x, v in r.items() if not x.startswith("_")} for r in diag],
               anchors=anch, winner=(winner["cell"] if winner else None), verdict=verdict),
          open("results/r53_fomc_repair_is.json", "w"), indent=1, default=float)
