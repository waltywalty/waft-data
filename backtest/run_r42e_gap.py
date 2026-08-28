"""Round 42 attempt 5: overnight gap - fill vs continuation by size (frozen per
reference/goal_ledger.md). 24-variant IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r42e_gap.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

BUCKETS = {"small": (0.1, 0.3), "mid": (0.3, 0.7), "large": (0.7, np.inf)}
DIRS = ("FILL", "CONT")
ENTRIES = ("0930", "1000")
EXITS = ("target", "eod")


def build(idx):
    rth = rth_of(load_frame(idx))
    days = {}
    daily = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                    hi=("high", "max"), lo=("low", "min"))
    daily["atr20"] = (daily.hi - daily.lo).rolling(20).mean().shift(1)
    daily["prevc"] = daily.c.shift(1)
    for skey, g in rth.groupby("skey"):
        d = daily.loc[skey]
        if len(g) < 50 or not np.isfinite(d.atr20) or d.atr20 <= 0 or not np.isfinite(d.prevc):
            continue
        days[skey] = (g[["open", "high", "low", "close"]].values, g.hm.values,
                      float(d.o), float(d.prevc), float(d.atr20))
    return days


def walk(arr, start, side, s_px, t_px):
    for k in range(start, len(arr)):
        o_, h_, l_, c_ = arr[k]
        if (side > 0 and l_ <= s_px) or (side < 0 and h_ >= s_px):
            return s_px
        if t_px is not None and ((side > 0 and h_ >= t_px) or (side < 0 and l_ <= t_px)):
            return t_px
    return arr[-1][3]


def stats(pnl, atr):
    p = np.asarray(pnl, float)
    r = p / np.asarray(atr, float)
    ok = np.isfinite(r)
    p, r = p[ok], r[ok]
    if len(p) < 10:
        return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]
    m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


data, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    days = build(idx)
    keys = sorted(days)
    cutd = keys[int(len(keys) * 0.75)]
    data[idx] = (days, cutd)
    split[idx] = str(cutd)

rows = []
for bname, (lo_, hi_) in BUCKETS.items():
    for dmode in DIRS:
        for ename in ENTRIES:
            for xmode in EXITS:
                pnls, atrs, ooss, idxs = [], [], [], []
                for idx, (days, cutd) in data.items():
                    for skey, (arr, hm, o930, prevc, atr20) in days.items():
                        g = o930 - prevc
                        gn = abs(g) / atr20
                        if not (lo_ <= gn < hi_):
                            continue
                        side = -np.sign(g) if dmode == "FILL" else np.sign(g)
                        if side == 0:
                            continue
                        if ename == "0930":
                            start, e = 0, o930
                        else:
                            pre = np.where(hm < 1000)[0]
                            post = np.where(hm >= 1000)[0]
                            if not len(pre) or not len(post):
                                continue
                            tgt0 = prevc if dmode == "FILL" else o930 + side * abs(g)
                            seg = arr[pre]
                            if (side > 0 and seg[:, 1].max() >= tgt0) or \
                               (side < 0 and seg[:, 2].min() <= tgt0):
                                continue          # target already touched pre-entry
                            start, e = post[0], arr[pre[-1]][3]
                        s_px = e - side * 0.5 * atr20
                        t_px = None
                        if xmode == "target":
                            t_px = prevc if dmode == "FILL" else o930 + side * abs(g)
                            if (side > 0 and t_px <= e) or (side < 0 and t_px >= e):
                                continue          # target not beyond entry
                        px = walk(arr, start, side, s_px, t_px)
                        pnls.append(side * (px - e) - MICRO[idx])
                        atrs.append(atr20)
                        ooss.append(skey >= cutd)
                        idxs.append(idx)
                sub = pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idxs))
                rows.append(dict(bucket=bname, dir=dmode, entry=ename, exit=xmode,
                                 IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                                 OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]),
                                 _sub=sub))

print("=== IS grid (pooled, ATR-normalized) ===")
print(f"{'bucket':>6} {'dir':>5} {'entry':>5} {'exit':>6} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10:
        continue
    print(f"{r['bucket']:>6} {r['dir']:>5} {r['entry']:>5} {r['exit']:>6} | {a['n']:>5} {a['wr']*100:>5.1f}% "
          f"{a['pf']:>5.2f} {a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("bucket", "dir", "entry", "exit")) == 3
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo variant selectable; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42e_gap.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: {winner['bucket']} {winner['dir']} entry {winner['entry']} exit {winner['exit']} "
      f"(neighbors positive {npos})")
sub = winner["_sub"]
oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in data:
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
               winner={x: winner[x] for x in ("bucket", "dir", "entry", "exit", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42e_gap.json", "w"), indent=1, default=float)
