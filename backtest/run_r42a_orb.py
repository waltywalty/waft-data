"""Round 42 attempt 1: ORB repaired by participation gates (frozen per
reference/goal_ledger.md). 48-variant IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r42a_orb.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
WINDOWS = {15: 945, 30: 1000, 60: 1030}


def build_days(idx):
    b = load_frame(idx)
    rth = rth_of(b)
    rows = []
    daily = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                    hi=("high", "max"), lo=("low", "min"))
    daily["rng"] = daily.hi - daily.lo
    daily["atr20"] = daily.rng.rolling(20).mean().shift(1)
    daily["prevc"] = daily.c.shift(1)
    daily["nr7"] = (daily.rng.shift(1) <= daily.rng.shift(1).rolling(7).min()).astype(bool)
    v30 = rth[rth.hm < 1000].groupby("skey").volume.sum()
    daily["rvol30"] = v30 / v30.rolling(20).mean().shift(1)
    trades = []
    for skey, g in rth.groupby("skey"):
        d = daily.loc[skey]
        if not np.isfinite(d.atr20) or d.atr20 <= 0 or len(g) < 50:
            continue
        arr = g[["open", "high", "low", "close"]].values
        hm = g.hm.values
        gapn = abs(d.o - d.prevc) / d.atr20 if np.isfinite(d.prevc) else np.nan
        for W, cut in WINDOWS.items():
            inwin = hm < cut
            if inwin.sum() < max(2, W // 5 - 1) or inwin.all():
                continue
            orh, orl = arr[inwin, 1].max(), arr[inwin, 2].min()
            rng = orh - orl
            if rng <= 0:
                continue
            post = arr[~inwin]
            bi, side = None, 0
            for i, (o_, h_, l_, c_) in enumerate(post):
                up, dn = h_ > orh, l_ < orl
                if up and dn:
                    bi = None
                    break                      # ambiguous first bar: skip day
                if up or dn:
                    bi, side = i, (1 if up else -1)
                    break
            if bi is None:
                continue
            e = orh if side > 0 else orl
            for sm, sname in ((0, "fullR"), (1, "halfR")):
                s_px = (orl if side > 0 else orh) if sm == 0 else e - 0.5 * rng * side
                for tm, tname in ((0, "T2R"), (1, "EOD")):
                    t_px = e + 2 * rng * side if tm == 0 else None
                    px = None
                    for k in range(bi, len(post)):
                        o_, h_, l_, c_ = post[k]
                        if (side > 0 and l_ <= s_px) or (side < 0 and h_ >= s_px):
                            px = s_px
                            break
                        if t_px is not None and k > bi and (
                                (side > 0 and h_ >= t_px) or (side < 0 and l_ <= t_px)):
                            px = t_px
                            break
                    if px is None:
                        px = post[-1][3]
                    trades.append(dict(skey=skey, W=W, stop=sname, tgt=tname,
                                       pnl=side * (px - e) - MICRO[idx],
                                       atr=d.atr20, rvol=d.rvol30, gap=gapn,
                                       nr7=bool(d.nr7)))
    return pd.DataFrame(trades)


def stats(df):
    p = df.pnl.values
    r = (df.pnl / df.atr).values
    if len(p) < 10:
        return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]
    m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


GATES = {"none": lambda d: np.ones(len(d), bool),
         "rvol1.5": lambda d: d.rvol.values >= 1.5,
         "gap0.5atr": lambda d: d.gap.values >= 0.5,
         "nr7": lambda d: d.nr7.values}

all_tr, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    df = build_days(idx)
    df["idx"] = idx
    days = sorted(df.skey.unique())
    cutd = days[int(len(days) * 0.75)]
    df["oos"] = df.skey >= cutd
    all_tr[idx] = df
    split[idx] = str(cutd)
    print(f"{idx}: {len(days)} sessions, OOS from {cutd}")
big = pd.concat(all_tr.values(), ignore_index=True)

rows = []
for W in WINDOWS:
    for gname, gfn in GATES.items():
        for sname in ("fullR", "halfR"):
            for tname in ("T2R", "EOD"):
                sub = big[(big.W == W) & (big.stop == sname) & (big.tgt == tname)]
                sub = sub[gfn(sub)]
                is_, oos = sub[~sub.oos], sub[sub.oos]
                rows.append(dict(W=W, gate=gname, stop=sname, tgt=tname,
                                 IS=stats(is_), OOS_sealed=stats(oos)))

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))


def neighbors(v):
    out = []
    for r in rows:
        same = sum(r[k] == v[k] for k in ("W", "gate", "stop", "tgt"))
        if same == 3:
            out.append(r)
    return out


winner = None
for cand in ranked:
    nb = [r for r in neighbors(cand) if r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner = cand
        winner["_neighbors_pos"] = f"{pos}/{len(nb)}"
        break

print("\n=== IS ranking, top 10 (pooled, ATR-normalized) ===")
print(f"{'W':>3} {'gate':>10} {'stop':>6} {'tgt':>4} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in ranked[:10]:
    a = r["IS"]
    print(f"{r['W']:>3} {r['gate']:>10} {r['stop']:>6} {r['tgt']:>4} | {a['n']:>5} {a['wr']*100:>5.1f}% "
          f"{a['pf']:>5.2f} {a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

print(f"\nSELECTED (pre-stated rule): W{winner['W']} {winner['gate']} {winner['stop']} "
      f"{winner['tgt']}  (neighbors positive: {winner['_neighbors_pos']})")

# ---- the single OOS evaluation ------------------------------------------------
sel = big[(big.W == winner["W"]) & (big.stop == winner["stop"]) & (big.tgt == winner["tgt"])]
sel = sel[GATES[winner["gate"]](sel)]
oos = sel[sel.oos]
o = stats(oos)
print("\n=== ONE-SHOT OOS (last 25% of sessions, burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in all_tr:
    s = oos[oos.idx == idx]
    per[idx] = stats(s)
    if per[idx].get("n", 0) >= 10:
        v = per[idx]
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}")
    else:
        print(f"  {idx}: n {per[idx].get('n',0)} (too few)")
cost15 = oos.copy()
for idx in all_tr:
    cost15.loc[cost15.idx == idx, "pnl"] -= 0.5 * MICRO[idx]
c15 = stats(cost15)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")

PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE ({'PASS' if PASS else 'FAIL'}): bar = same sign, t>=2, PF>=1.15, cost x1.5 positive")

json.dump(dict(split=split, grid=rows, winner={k: v for k, v in winner.items() if k != "_neighbors_pos"},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42a_orb.json", "w"), indent=1, default=float)
