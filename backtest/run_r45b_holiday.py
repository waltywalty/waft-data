"""Round 45 attempt 20: pre-holiday calendar premium (frozen per
reference/goal_ledger.md). 6-cell IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r45b_holiday.json."""
import pandas as pd, numpy as np, json, warnings, datetime as dt
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def build_days(idx):
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m12 = np.where(hm >= 1200)[0]
        rows.append(dict(skey=skey, o=g.open.values[0], c=g.close.values[-1],
                         c12=g.open.values[m12[0]] if len(m12) else np.nan,
                         hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in d.index])
    return d, cutd


def weekdays_between(a, b):
    """count of Mon-Fri dates strictly between sessions a and b"""
    n, k = 0, a + dt.timedelta(days=1)
    while k < b:
        if k.weekday() < 5:
            n += 1
        k += dt.timedelta(days=1)
    return n


def big3(k):
    """session before July 4, Thanksgiving (4th Thu Nov), or Christmas"""
    y = k.year
    jul4 = dt.date(y, 7, 4)
    f = dt.date(y, 11, 1)
    thx = f + dt.timedelta(days=(3 - f.weekday()) % 7 + 21)
    xmas = dt.date(y, 12, 25)
    return any(k < h and (h - k).days <= 4 for h in (jul4, thx, xmas))


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
    keys = d.index.tolist()
    # pre-holiday: next session skips >= 1 weekday (holiday schedule is ex-ante public)
    preh = [weekdays_between(keys[i], keys[i + 1]) >= 1 for i in range(len(keys) - 1)] + [False]
    d["preh"] = preh
    d["big3"] = [big3(k) if p else False for k, p in zip(keys, preh)]
    data[idx] = d
    split[idx] = str(cutd)
    ish = d[~d.oos]
    print(f"{idx}: {len(d)} sessions, {int(d.preh.sum())} pre-holiday "
          f"({int(d.big3.sum())} big3), IS pre-holiday {int(ish.preh.sum())}, OOS from {cutd}")

HOLDS = {"H1_open_close": ("o", "c"), "H2_1200_close": ("c12", "c"),
         "H3_prevc_close": ("prevc", "c")}
SCOPES = ("all", "big3")

rows = []
for hname, (ecol, xcol) in HOLDS.items():
    for scope in SCOPES:
        pnls, atrs, ooss, idxs = [], [], [], []
        for idx, d in data.items():
            m = d.preh & np.isfinite(d[ecol]) & np.isfinite(d[xcol]) \
                & np.isfinite(d.atr20) & (d.atr20 > 0)
            if scope == "big3":
                m &= d.big3
            s = d[m]
            pnls += list(s[xcol] - s[ecol] - MICRO[idx])
            atrs += list(s.atr20); ooss += list(s.oos); idxs += [idx] * len(s)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
        sidx = sub[sub.idx != "GOLD"]
        g = sub[sub.idx == "GOLD"]
        rows.append(dict(hold=hname, scope=scope,
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; gold diagnostic) ===")
print(f"{'hold':>15} {'scope':>6} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['hold']:>15} {r['scope']:>6} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

def floor_n(r):
    return 60 if r["scope"] == "big3" else 120

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= floor_n(r)],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("hold", "scope")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r45b_holiday.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['hold']} {winner['scope']} (neighbors positive {npos})")
sub = winner["_sub"]; oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
nfloor = 25 if winner["scope"] == "big3" else 40
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
PASS = (o.get("n", 0) >= nfloor and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("hold", "scope", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r45b_holiday.json", "w"), indent=1, default=float)
