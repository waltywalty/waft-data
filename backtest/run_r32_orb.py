"""Round 32b: TradeAlgo's NQ Opening Range Breakout claim (74.5% WR, PF 2.51).

Source: tradealgo.com/trading-guides/futures/futures-trading-strategies
(retrieved 2026-08-27 via remote browser; local egress blocked). Spec as
stated: mark the 09:30-10:00 ET high/low; buy a break above / sell a break
below; stop = opposite side of the range; target = 1.5-2x range width;
filter option = trade only aligned with the overnight trend. No window, no
costs, no source given for the claimed stats.

Replication per pre-registration (goal_ledger.md): NDX 5m 2005-2025, first
breakout per day only, EOD flat at the 15:55 ET close if neither stop nor
target hits. Cells: entry {touch, close-beyond} x target {1.5x, 2x, EOD} x
filter {none, gap-align}, house cost 2.0 NDX pts RT + zero-cost primary.
Outputs results/r32_orb.json.
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

COST = 2.0

b = index_data.load("NDX").tz_convert("America/New_York")
b = b[b.index.dayofweek < 5]
b["d"] = b.index.date
b["hm"] = b.index.hour * 100 + b.index.minute
days = {d: g for d, g in b.groupby("d")}


def run(entry_mode, target_mult, gap_align, cost):
    trades = []
    prev_close = None
    for d in sorted(days):
        g = days[d]
        orb = g[(g.hm >= 930) & (g.hm < 1000)]
        sess = g[(g.hm >= 1000) & (g.hm <= 1555)]
        day_close = g[g.hm <= 1555]
        if len(orb) < 6 or len(sess) < 30:
            prev_close = day_close.close.iloc[-1] if len(day_close) else prev_close
            continue
        hi, lo = orb.high.max(), orb.low.min()
        rng = hi - lo
        o930 = orb.open.iloc[0]
        gap_dir = np.sign(o930 - prev_close) if prev_close else 0
        prev_close = day_close.close.iloc[-1]
        if rng <= 0:
            continue
        side = px_in = None
        t_in = None
        arr = sess[["open", "high", "low", "close"]].values
        for i, (op, h, l, c) in enumerate(arr):
            if entry_mode == "touch":
                if h > hi:
                    side, px_in, t_in = 1, max(hi, op), i
                elif l < lo:
                    side, px_in, t_in = -1, min(lo, op), i
            else:  # close beyond the level
                if c > hi:
                    side, px_in, t_in = 1, None, i   # enter next bar open
                elif c < lo:
                    side, px_in, t_in = -1, None, i
            if side:
                break
        if not side:
            continue
        if gap_align and gap_dir != 0 and side != gap_dir:
            continue
        if px_in is None:
            if t_in + 1 >= len(arr):
                continue
            px_in = arr[t_in + 1][0]
            t_in += 1
        stop = lo if side > 0 else hi
        tgt = px_in + side * target_mult * rng if target_mult else None
        px_out = None
        for op, h, l, c in arr[t_in + 1:]:
            if (side > 0 and l <= stop) or (side < 0 and h >= stop):
                px_out = stop; break
            if tgt and ((side > 0 and h >= tgt) or (side < 0 and l <= tgt)):
                px_out = tgt; break
        if px_out is None:
            px_out = arr[-1][3]
        pnl = side * (px_out - px_in) - cost
        trades.append(dict(d=str(d), pnl=pnl, r=pnl / rng))
    return pd.DataFrame(trades)


def score(tr):
    if not len(tr):
        return dict(n=0)
    p = tr.pnl
    w, l = p[p > 0], p[p <= 0]
    pf = w.sum() / abs(l.sum()) if len(l) and l.sum() < 0 else np.inf
    return dict(n=int(len(p)), wr=float((p > 0).mean()), pf=float(pf),
                total_pts=float(p.sum()), avg_pts=float(p.mean()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))) if p.std() > 0 else np.nan)


out = {}
for em in ("touch", "close"):
    for tm, tname in ((1.5, "t1.5x"), (2.0, "t2x"), (None, "eod")):
        for ga in (False, True):
            name = f"{em}|{tname}|{'gapalign' if ga else 'all'}"
            out[name] = score(run(em, tm, ga, COST))
out["close|t1.5x|all|zerocost"] = score(run("close", 1.5, False, 0.0))
out["touch|t1.5x|all|zerocost"] = score(run("touch", 1.5, False, 0.0))

json.dump(out, open("results/r32_orb.json", "w"), indent=1, default=float)
print(f"{'cell':>30} {'n':>6} {'WR':>7} {'PF':>6} {'avg pts':>8} {'t':>7}")
for k, s in out.items():
    if s["n"] == 0:
        print(f"{k:>30}  no trades"); continue
    print(f"{k:>30} {s['n']:>6} {s['wr']*100:>6.1f}% {s['pf']:>6.2f} {s['avg_pts']:>+8.2f} {s['t']:>+7.2f}")
print("\nclaimed (NQ ORB):               74.5%   2.51   'across hundreds of trades'")
