"""Round 45 attempt 19: options-expiration calendar family (frozen per
reference/goal_ledger.md). 8-cell IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r45_opex.json."""
import pandas as pd, numpy as np, json, warnings, datetime as dt
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def build_days(idx):
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in d.index])
    return d, cutd


def third_friday(y, m):
    f = dt.date(y, m, 1)
    off = (4 - f.weekday()) % 7          # first Friday
    return f + dt.timedelta(days=off + 14)


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
    print(f"{idx}: {len(d)} sessions {d.index[0]}..{d.index[-1]}, OOS from {cutd}")

# windows: (name, direction, mechanism arm)
WINS = {"W1_opexweek": (+1, "long"), "W2_wed_fri": (+1, "long"),
        "W3_postmon": (-1, "short"), "W4_postmon_wed": (-1, "short")}
SCOPES = {"monthly": tuple(range(1, 13)), "quarterly": (3, 6, 9, 12)}


def month_trades(d, wname):
    """One (entry_skey, pnl_gross_signed_pts, atr) tuple per expiration month."""
    keys = d.index.tolist()
    kset = pd.Series(range(len(keys)), index=keys)
    out = []
    y0, y1 = keys[0].year, keys[-1].year
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            tf = third_friday(y, m)
            mon = tf - dt.timedelta(days=4)
            # expiry session: last session in [mon, tf]
            wk = [k for k in keys if mon <= k <= tf]
            if len(wk) < 3:
                continue
            expiry = wk[-1]
            if wname == "W1_opexweek":
                ek, xp = wk[0], d.c[expiry]
                e = d.o[ek]
            elif wname == "W2_wed_fri":
                wed = tf - dt.timedelta(days=2)
                cand = [k for k in wk if k <= wed]
                if not cand or cand[-1] == expiry:
                    continue
                ek = cand[-1]
                e, xp = d.c[ek], d.c[expiry]
            else:
                post = [k for k in keys if expiry < k <= expiry + dt.timedelta(days=4)]
                if not post:
                    continue
                ek = post[0]
                e = d.o[ek]
                if wname == "W3_postmon":
                    xp = d.c[ek]
                else:
                    wed2 = ek + dt.timedelta(days=2)
                    cand = [k for k in keys if ek <= k <= wed2]
                    xp = d.c[cand[-1]]
            a = d.atr20[ek]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            out.append((ek, m, xp - e, a, bool(d.oos[ek])))
    return out


cache = {(idx, w): month_trades(data[idx], w) for idx in data for w in WINS}

rows = []
for wname, (side, arm) in WINS.items():
    for sname, months in SCOPES.items():
        pnls, atrs, ooss, idxs = [], [], [], []
        for idx in data:
            for ek, m, dpts, a, oos in cache[(idx, wname)]:
                if m not in months:
                    continue
                pnls.append(side * dpts - MICRO[idx])
                atrs.append(a); ooss.append(oos); idxs.append(idx)
        sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
        sidx = sub[sub.idx != "GOLD"]
        g = sub[sub.idx == "GOLD"]
        rows.append(dict(win=wname, scope=sname, arm=arm,
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_gold=stats(g.pnl[~g.oos], g.atr[~g.oos]),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]),
                         _sub=sidx))

print("\n=== IS grid (indices pooled, ATR-normalized; gold diagnostic) ===")
print(f"{'window':>15} {'scope':>10} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'gold avgR':>9}")
for r in rows:
    a, gg = r["IS"], r["IS_gold"]
    if a.get("n", 0) < 10: continue
    print(f"{r['win']:>15} {r['scope']:>10} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | {gg.get('avg_R', float('nan')):>+9.3f}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in rows if r["arm"] == cand["arm"]
          and sum(r[x] == cand[x] for x in ("win", "scope")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor (n>=120, t>=2, neighbor majority); family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r45_opex.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['win']} {winner['scope']} (same-arm neighbors positive {npos})")
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
               winner={x: winner[x] for x in ("win", "scope", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r45_opex.json", "w"), indent=1, default=float)
