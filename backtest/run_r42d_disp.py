"""Round 42 attempt 4: FP5 displacement magnitude/horizon repair (frozen per
reference/goal_ledger.md). 24-variant IS grid, pre-stated selection, single
OOS evaluation. Outputs results/r42d_disp.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of, resample_15m = ns["load_frame"], ns["rth_of"], ns["resample_15m"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def build(idx):
    b = load_frame(idx)
    q = resample_15m(b)
    q["skey"] = (q.index + pd.Timedelta(hours=8)).date
    drng = q.groupby("skey").high.max() - q.groupby("skey").low.min()
    atr20 = drng.rolling(20).mean().shift(1)
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr14 = tr.rolling(14).mean()
    q["ratio"] = tr / atr14
    q["bodyok"] = (q.close - q.open).abs() / (q.high - q.low).replace(0, np.nan) >= 0.6
    q["dir"] = np.sign(q.close - q.open)
    q["hm"] = q.index.hour * 100 + q.index.minute
    q["atr20"] = q.skey.map(atr20)
    return q


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


frames, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    q = build(idx)
    days = sorted(q.skey.unique())
    cutd = days[int(len(days) * 0.75)]
    q["oos"] = np.array([d >= cutd for d in q.skey])
    frames[idx] = q
    split[idx] = str(cutd)

KS = (1.5, 2.0, 2.5)
WINS = {"pre14": 1400, "pre1130": 1130}
STOPS = ("none", "1R")
EXITS = ("EOD", "t8")


def run_variant(idx, k, wcut, stop, exit_):
    q = frames[idx]
    arr = q[["open", "high", "low", "close"]].values
    n = len(q)
    sig = (q.ratio.values >= k) & q.bodyok.values & (q["dir"].values != 0) & (q.hm.values < wcut)
    skeys = q.skey.values
    pnls, atrs, ooss, last_exit = [], [], [], -1
    day_end = {}
    for i in range(n - 1, -1, -1):
        if skeys[i] not in day_end:
            day_end[skeys[i]] = i
    for i in np.where(sig)[0]:
        if i <= last_exit:
            continue
        de = day_end[skeys[i]]
        if de <= i:
            continue
        a20 = q.atr20.values[i]
        if not np.isfinite(a20) or a20 <= 0:
            continue
        side = q["dir"].values[i]
        e = arr[i][3]
        rng = arr[i][1] - arr[i][2]
        s_px = e - rng * side if stop == "1R" else None
        j2 = de if exit_ == "EOD" else min(i + 8, de)
        px, xk = None, j2
        for kk in range(i + 1, j2 + 1):
            o_, h_, l_, c_ = arr[kk]
            if s_px is not None and ((side > 0 and l_ <= s_px) or (side < 0 and h_ >= s_px)):
                px, xk = s_px, kk
                break
        if px is None:
            px = arr[j2][3]
        pnls.append(side * (px - e) - MICRO[idx])
        atrs.append(a20)
        ooss.append(bool(q.oos.values[i]))
        last_exit = xk
    return pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, idx=idx))


rows = []
for k in KS:
    for wname, wcut in WINS.items():
        for stop in STOPS:
            for exit_ in EXITS:
                sub = pd.concat([run_variant(idx, k, wcut, stop, exit_) for idx in frames],
                                ignore_index=True)
                rows.append(dict(k=k, win=wname, stop=stop, exit=exit_,
                                 IS=stats(sub.pnl[~sub.oos], sub.atr[~sub.oos]),
                                 OOS_sealed=stats(sub.pnl[sub.oos], sub.atr[sub.oos]),
                                 _sub=sub))

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("k", "win", "stop", "exit")) == 3
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

print("=== IS grid (pooled, ATR-normalized) ===")
print(f"{'k':>4} {'win':>8} {'stop':>5} {'exit':>4} | {'n':>6} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in sorted(rows, key=lambda r: (r["k"], r["win"], r["stop"], r["exit"])):
    a = r["IS"]
    if a.get("n", 0) < 10:
        continue
    print(f"{r['k']:>4} {r['win']:>8} {r['stop']:>5} {r['exit']:>4} | {a['n']:>6} {a['wr']*100:>5.1f}% "
          f"{a['pf']:>5.2f} {a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12}")

if winner is None:
    print("\nNo variant selectable; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r42d_disp.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: k{winner['k']} {winner['win']} stop={winner['stop']} exit={winner['exit']} "
      f"(neighbors positive {npos})")
sub = winner["_sub"]
oos = sub[sub.oos]
o = stats(oos.pnl, oos.atr)
print("\n=== ONE-SHOT OOS (burned now) ===")
print(f"pooled: n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
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
               winner={x: winner[x] for x in ("k", "win", "stop", "exit", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r42d_disp.json", "w"), indent=1, default=float)
