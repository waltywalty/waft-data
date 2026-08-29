"""Round 46 attempt 24: FOMC-cycle even-week pattern (frozen per
reference/goal_ledger.md). 6 selectable cells + odd-week diagnostics,
single OOS evaluation. Outputs results/r46b_fomccycle.json."""
import pandas as pd, numpy as np, json, warnings, re
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

# verified FOMC announcement dates, reused verbatim from run_r42l_fomc.py
lsrc = open("run_r42l_fomc.py").read()
FOMC = sorted(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', lsrc, re.S).group(1).split()).date)
print(f"FOMC calendar: {len(FOMC)} meetings {FOMC[0]}..{FOMC[-1]}")


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d = d[[k >= FOMC[0] for k in d.index]]
    # cycle day: trading days since most recent announcement (day 0 = announcement)
    keys = d.index.tolist()
    cyc, fi, last0 = [], 0, None
    for i, k in enumerate(keys):
        while fi < len(FOMC) and FOMC[fi] <= k:
            last0 = None
            # announcement day may be a holiday-adjacent non-session; anchor to
            # the first session on/after the announcement date
            for j in range(i, max(-1, i - 5), -1):
                pass
            fi += 1
        cyc.append(k)
    # simpler: for each session, count sessions since the last session >= announcement
    anchor = {}
    ai = 0
    last_anchor_pos = None
    pos = {k: i for i, k in enumerate(keys)}
    anchors = []
    for f in FOMC:
        cand = [k for k in keys if k >= f]
        if cand:
            anchors.append(pos[cand[0]])
    cycday = np.full(len(keys), 999)
    for i in range(len(keys)):
        prior = [a for a in anchors if a <= i]
        if prior:
            cycday[i] = i - prior[-1]
    d["cyc"] = cycday
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd


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


data, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    data[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {len(d)} sessions in calendar span, OOS from {cutd}")

SCOPES = {"week0": (0, 4), "week2": (10, 14), "even": None, "odd_diag": None}


def in_scope(cyc, scope):
    if scope == "even":
        return ((cyc <= 4) | ((cyc >= 10) & (cyc <= 14)) | ((cyc >= 20) & (cyc <= 24)))
    if scope == "odd_diag":
        return (((cyc >= 5) & (cyc <= 9)) | ((cyc >= 15) & (cyc <= 19)))
    a, z = SCOPES[scope]
    return (cyc >= a) & (cyc <= z)


HOLDS = {"oc": ("o", "c"), "cc": ("prevc", "c")}

rows = []
for scope in SCOPES:
    for hname, (ecol, xcol) in HOLDS.items():
        pnls, atrs, ooss, idxs = [], [], [], []
        for idx, d in data.items():
            m = in_scope(d.cyc.values, scope) & np.isfinite(d[ecol]) & np.isfinite(d[xcol]) \
                & np.isfinite(d.atr20) & (d.atr20 > 0)
            s = d[m]
            pnls += list(s[xcol] - s[ecol] - MICRO[idx])
            atrs += list(s.atr20); ooss += list(s.oos); idxs += [idx] * len(s)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
        sidx = sub[sub.idx != "GOLD"]
        g = sub[sub.idx == "GOLD"]
        rows.append(dict(scope=scope, hold=hname, selectable=(scope != "odd_diag"),
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; odd weeks diagnostic; gold diagnostic) ===")
print(f"{'scope':>9} {'hold':>4} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['scope']:>9} {r['hold']:>4} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

sel = [r for r in rows if r["selectable"]]
ranked = sorted([r for r in sel if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in sel if sum(r[x] == cand[x] for x in ("scope", "hold")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo selectable cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r46b_fomccycle.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['scope']} {winner['hold']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (indices pooled, burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in ("SPX", "NDX", "RTY"):
    s = oos[oos.idx == idx]
    per[idx] = stats(s.pnl, s.atr)
    v = per[idx]
    if v.get("n", 0) >= 10:
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("scope", "hold", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r46b_fomccycle.json", "w"), indent=1, default=float)
