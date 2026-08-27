"""Round 27A: fair value gaps and inversions. Pre-registered in the goal ledger.

FVG: bull when low[t] > high[t-2]; zone [high[t-2], low[t]]; bear mirrored.
Formation windows: XAU 00:00-04:00 UTC; indices 09:30-10:30 ET.
Continuation: first retrace touch into the zone -> enter gap direction, stop
beyond far edge. Inversion: a bar CLOSING through the far edge -> enter in
violation direction, stop at near edge. Flat at session end. One trade per
day per cell (first signal).
"""
import pandas as pd, numpy as np, json, warnings, engine, index_data
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")

NY = ZoneInfo("America/New_York")
COST = {"XAU": 0.30, "SPX": 0.6, "NDX": 2.0, "RTY": 0.4}
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def bars_for(mkt):
    if mkt == "XAU":
        return engine.load_bars()
    return index_data.load(mkt)

def session_bounds(mkt, day):
    if mkt == "XAU":
        t0 = pd.Timestamp(day.year, day.month, day.day, 0, 0, tz="UTC")
        t1 = pd.Timestamp(day.year, day.month, day.day, 4, 0, tz="UTC")
        te = pd.Timestamp(day.year, day.month, day.day, 16, 0, tz=NY).tz_convert("UTC")
    else:
        t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30, tz=NY).tz_convert("UTC")
        t1 = pd.Timestamp(day.year, day.month, day.day, 10, 30, tz=NY).tz_convert("UTC")
        te = pd.Timestamp(day.year, day.month, day.day, 16, 0, tz=NY).tz_convert("UTC")
    return t0, t1, te

def run_cell(mkt, bars5, tf_min, construction):
    tf = f"{tf_min}min"
    b = bars5.resample(tf).agg(open=("open", "first"), high=("high", "max"),
                               low=("low", "min"), close=("close", "last")).dropna()
    cost = COST[mkt]
    trades = []
    for day, _ in b.groupby(b.index.date):
        d = pd.Timestamp(day)
        t0, t1, te = session_bounds(mkt, d)
        win = b.loc[t0:t1 - pd.Timedelta(seconds=1)]
        if len(win) < 3:
            continue
        # first FVG formed inside the window
        zone = None
        H, L = win.high.values, win.low.values
        for i in range(2, len(win)):
            if L[i] > H[i - 2]:
                zone = (H[i - 2], L[i], 1, win.index[i]); break     # bull: near=low[t], far=high[t-2]
            if H[i] < L[i - 2]:
                zone = (H[i], L[i - 2], -1, win.index[i]); break    # bear zone [high[t], low[t-2]]
        if zone is None:
            continue
        lo_z, hi_z, gdir, t_form = zone
        path = b.loc[t_form + pd.Timedelta(minutes=tf_min):te]
        if not len(path):
            continue
        pos = None
        for bar in path.itertuples():
            if pos is None:
                if construction == "cont":
                    # retrace touch into the zone -> trade gap direction
                    if gdir > 0 and bar.low <= hi_z:
                        pos = (1, hi_z, lo_z - (hi_z - lo_z) * 0.0, bar.Index)  # stop at far edge lo_z
                        stop = lo_z
                    elif gdir < 0 and bar.high >= lo_z:
                        pos = (-1, lo_z, hi_z, bar.Index); stop = hi_z
                    else:
                        continue
                else:  # inversion: bar CLOSES through the far edge -> violation direction
                    if gdir > 0 and bar.close < lo_z:
                        pos = (-1, float(bar.close), hi_z, bar.Index); stop = hi_z
                    elif gdir < 0 and bar.close > hi_z:
                        pos = (1, float(bar.close), lo_z, bar.Index); stop = lo_z
                    else:
                        continue
                side, entry, stop, t_in = pos
                continue
            side, entry, stop, t_in = pos
            if (side > 0 and bar.low <= stop) or (side < 0 and bar.high >= stop):
                pnl = side * (stop - entry) - 2 * cost
                trades.append(dict(day=d, side=side, pnl=pnl, entry=entry)); pos = None; break
        if pos is not None:
            side, entry, stop, t_in = pos
            i = b.index.searchsorted(te)
            exit_px = float(b.close.iloc[i - 1]) if i > 0 else float(path.close.iloc[-1])
            pnl = side * (exit_px - entry) - cost
            trades.append(dict(day=d, side=side, pnl=pnl, entry=entry))
    t = pd.DataFrame(trades)
    if len(t) < 30:
        return dict(n=len(t))
    p = t.pnl / t.entry * 100
    mid = t.day.iloc[len(t) // 2]
    d1, d2 = t[t.day <= mid], t[t.day > mid]
    return dict(n=len(t), pf=pf(t.pnl), exp=float(t.pnl.mean()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))),
                win=float((t.pnl > 0).mean()),
                h1_pf=pf(d1.pnl), h2_pf=pf(d2.pnl),
                h1_exp=float(d1.pnl.mean()), h2_exp=float(d2.pnl.mean()),
                long_pf=pf(t[t.side > 0].pnl) if (t.side > 0).sum() > 10 else None,
                short_pf=pf(t[t.side < 0].pnl) if (t.side < 0).sum() > 10 else None)

out = {}
for mkt in ("XAU", "SPX", "NDX", "RTY"):
    bars5 = bars_for(mkt)
    for tf in (15, 60):
        for con in ("cont", "inv"):
            k = f"{mkt}_{tf}m_{con}"
            out[k] = run_cell(mkt, bars5, tf, con)
            v = out[k]
            if "pf" in v:
                print(f"{k:>14}: n={v['n']:>5} PF {v['pf']:.3f} t {v['t']:+.2f} "
                      f"win {v['win']*100:.0f}%  halves {v['h1_pf']:.3f}/{v['h2_pf']:.3f}")
            else:
                print(f"{k:>14}: n={v['n']} (too few)")

json.dump(out, open("results/r27a_fvg.json", "w"), indent=1, default=float)
best = max((abs(v["t"]) for v in out.values() if "t" in v), default=0)
print(f"\nbest |t| across 16 cells: {best:.2f} (Bonferroni bar ~3.0)")
