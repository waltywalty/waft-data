"""Round 41: specification-mining demonstration on the gold flip scalp.
Frozen per pre-registration in reference/goal_ledger.md. Searches 240 spec
variants on the FIRST half of the data, then evaluates the in-sample winner
(and top 10) on the untouched SECOND half. Outputs results/r41_specmine.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]

COST = 0.35
CAP = 32                      # max holding, bars

b5 = load_frame("GOLD")
d5 = np.sign(b5.close - b5.open) * b5.volume
q = b5.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna(subset=["open"])
q["delta"] = d5.resample("15min").sum().reindex(q.index)
pct = (q.delta.abs().rolling(100).rank(pct=True) * 100).values
red = (q.close < q.open).values
dpos = (q.delta > 0).values
prior8 = (q.close.shift(1) / q.close.shift(9) - 1).values
atLow = (q.low <= q.low.rolling(20).min()).values
o, h, l, c = (q[k].values for k in ("open", "high", "low", "close"))
n = len(q)
mid = n // 2

CTX = {"all": np.ones(n, bool), "trend": prior8 < 0, "low": atLow,
       "trend+low": (prior8 < 0) & atLow}
EXITS = [("TP5/SL5", 5, 5), ("TP10/SL5", 10, 5), ("TP10/SL10", 10, 10),
         ("TP10/SL20", 10, 20), ("time4", None, None, 4), ("time8", None, None, 8)]


def trade(i0, e, tp, sl, tmax):
    """Long from price e after bar i0; worst-case SL first; cap; return net pnl."""
    j2 = min(i0 + (tmax or CAP), n - 1)
    for k in range(i0 + 1, j2 + 1):
        if tp is not None:
            if l[k] <= e - sl:
                return -sl - COST
            if h[k] >= e + tp:
                return tp - COST
    return c[j2] - e - COST


def run_variant(th, ctxname, delay, exit_):
    ename, tp, sl = exit_[0], exit_[1], exit_[2]
    tmax = exit_[3] if len(exit_) > 3 else None
    ev = red & dpos & CTX[ctxname] & np.isfinite(pct) & (pct >= th)
    ii = np.where(ev)[0]
    pnls, times, last_exit = [], [], -1
    for i in ii:
        if i <= last_exit or i + 2 >= n:
            continue
        if delay:                        # wait for the extra dip
            if not (l[i + 1] < l[i]):
                continue
            i0, e = i + 1, c[i + 1]
        else:
            i0, e = i, c[i]
        p = trade(i0, e, tp, sl, tmax)
        pnls.append(p)
        times.append(i)
        last_exit = i0 + (tmax or CAP)
    return np.array(pnls), np.array(times)


def stats(p):
    if len(p) < 10:
        return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg=float(p.mean()), total=float(p.sum()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))) if p.std() > 0 else np.nan)


rows = []
for th in (70, 80, 90, 95, 97):
    for ctxname in CTX:
        for delay in (False, True):
            for exit_ in EXITS:
                p, t_ = run_variant(th, ctxname, delay, exit_)
                is_, oos = p[t_ < mid], p[t_ >= mid]
                rows.append(dict(spec=f"th{th} {ctxname} {'dip-entry' if delay else 'close-entry'} {exit_[0]}",
                                 IS=stats(is_), OOS=stats(oos)))

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 30],
                key=lambda r: -(r["IS"].get("t") or -99))
out = dict(n_variants=len(rows), winner=ranked[0], top10=ranked[:10],
           top10_is_avg=float(np.mean([r["IS"]["avg"] for r in ranked[:10]])),
           top10_oos_avg=float(np.mean([r["OOS"].get("avg", np.nan) for r in ranked[:10]])))
json.dump(out, open("results/r41_specmine.json", "w"), indent=1, default=float)

print(f"searched {len(rows)} variants; ranked {len(ranked)} with n>=30 IS trades\n")
print("=== TOP 10 BY IN-SAMPLE t (first half) -> SAME SPEC OUT-OF-SAMPLE (second half) ===")
print(f"{'spec':>42} | {'n':>5} {'WR':>6} {'PF':>5} {'avg':>6} {'t':>5} | {'n':>5} {'WR':>6} {'PF':>5} {'avg':>6} {'t':>6}")
for r in ranked[:10]:
    a, b_ = r["IS"], r["OOS"]
    print(f"{r['spec']:>42} | {a['n']:>5} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} {a['avg']:>+6.2f} {a['t']:>+5.2f} | "
          f"{b_.get('n',0):>5} {b_.get('wr',0)*100:>5.1f}% {b_.get('pf',float('nan')):>5.2f} "
          f"{b_.get('avg',float('nan')):>+6.2f} {b_.get('t',float('nan')):>+6.2f}")
print(f"\ntop-10 avg pnl/trade: IS {out['top10_is_avg']:+.3f} -> OOS {out['top10_oos_avg']:+.3f}")
