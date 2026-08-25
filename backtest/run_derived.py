"""Round 12: strategies DERIVED from the repo's own validated structure, not
imported from outside. Pre-registered before running; every cell reported.

The synthesis behind them: the one real edge is a slow drift - Asia-open
direction on low gold/AUD-correlation days persists until the NY close and no
interference helps. The NY open itself prices information in minutes (both
directions dead), but the drift is still in progress AT the NY open. So:

  1. NY RE-ENTRY (a genuine "NY session strategy"): on deployed-filter days
     where the Asia break fired, enter at 09:30 NY in the Asia-break direction,
     exit 16:00 NY. Variants: unconditional / only if the original trade is in
     profit at the NY open; no stop / 2x-range stop.  (4 cells)
  2. LONDON RE-ENTRY: same construction at 08:00 London, conditional on
     in-profit - equivalently, the marginal leg of pyramiding the winner.
     (2 cells: no stop / 2R)
  3. LONDON-OPEN ORB (the symmetry test): the exact Asia construction moved to
     the 08:00-London open - 60m range, first 60m close beyond, corr filter,
     16:00-NY exit. If the edge is about illiquid-open price discovery, the
     semi-liquid London open should sit between Asia (works) and NY (dead).
     (4 cells: stop x filter)

Multiplicity: 10 pre-registered cells, one derived family. Split 2024-01-01.
"""
import pandas as pd, numpy as np, warnings, json
import engine, trades
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

NY, LDN = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
bars = engine.load_bars()
CORR = trades.corr_series(bars, 20)
SPLIT = pd.Timestamp("2024-01-01")
OUT = {"cells": []}
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def report(label, rows, key):
    if len(rows) < 30:
        print(f"   {label:52s} too few trades ({len(rows)})")
        return
    d = pd.DataFrame(rows)
    d["day"] = pd.to_datetime(d.day)
    p = d.pnl
    pct = p / d.entry * 100
    a, b = d[d.day < SPLIT], d[d.day >= SPLIT]
    s = dict(n=len(d), win=float((p > 0).mean()), pf=pfx(p), exp=float(p.mean()),
             t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0,
             pf0=pfx(p + 0.30), is_pf=pfx(a.pnl) if len(a) > 20 else np.nan,
             os_pf=pfx(b.pnl) if len(b) > 20 else np.nan)
    agree = (s["is_pf"] > 1) == (s["os_pf"] > 1)
    print(f"   {label:52s} n={s['n']:>4} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
          f"exp={s['exp']:+.2f} t={s['t']:+.2f} | PF0={s['pf0']:.3f} | "
          f"IS {s['is_pf']:.3f} OS {s['os_pf']:.3f} {'AGREE' if agree else 'DISAGREE'}")
    OUT["cells"].append({"label": label, "family": key, **s, "agree": bool(agree)})


def clock(day, h, m, tz):
    return pd.Timestamp(day.year, day.month, day.day, h, m, tz=tz).tz_convert("UTC")


# base: the deployed entries, no-stop path (interference-free reference frame)
N = trades.generate(bars, 60, stop_r=None, cost=0.30, entry_cutoff_ldn=8)
N["day"] = pd.to_datetime(N.day)
DEP = pd.read_pickle("results/trades_deployable.pkl")
N = N[N.day.isin(pd.to_datetime(DEP.day))].copy()
print(f"base: {len(N)} deployed-day entries\n")

print("=== 1. NY RE-ENTRY of the Asia signal (a derived NY-session strategy) ===")
for cond in ("all", "in_profit"):
    for stop_on in (False, True):
        rows = []
        for _, r in N.iterrows():
            d = r.day
            t_ny = clock(d, 9, 30, NY)
            t_x = clock(d, 16, 0, NY)
            if r.t_fill >= t_ny:
                continue
            px_ny = engine.price_at(bars, t_ny)
            if px_ny is None:
                continue
            if cond == "in_profit" and r.side * (px_ny - r.entry) <= 0:
                continue
            side, entry = int(r.side), float(px_ny)
            stop = entry - side * 2 * r.range if stop_on else None
            path = bars.loc[t_ny:t_x - pd.Timedelta(minutes=5)]
            out_px, why = None, "time"
            if stop is not None and len(path):
                hitm = (path.low <= stop) if side == 1 else (path.high >= stop)
                if hitm.any():
                    out_px, why = stop, "stop"
            if out_px is None:
                out_px = engine.price_at(bars, t_x)
                if out_px is None:
                    continue
            rows.append(dict(day=d, entry=entry, pnl=side * (out_px - entry) - 0.30))
        report(f"NY 09:30 re-entry / {cond} / {'2R stop' if stop_on else 'no stop'}",
               rows, "ny_reentry")

print("\n=== 2. LONDON RE-ENTRY (the pyramid leg, standalone) ===")
for stop_on in (False, True):
    rows = []
    for _, r in N.iterrows():
        d = r.day
        t_l = clock(d, 8, 0, LDN)
        t_x = clock(d, 16, 0, NY)
        if r.t_fill >= t_l:
            continue
        px_l = engine.price_at(bars, t_l)
        if px_l is None or r.side * (px_l - r.entry) <= 0:
            continue                                   # add only to a winner
        side, entry = int(r.side), float(px_l)
        stop = entry - side * 2 * r.range if stop_on else None
        path = bars.loc[t_l:t_x - pd.Timedelta(minutes=5)]
        out_px = None
        if stop is not None and len(path):
            hitm = (path.low <= stop) if side == 1 else (path.high >= stop)
            if hitm.any():
                out_px = stop
        if out_px is None:
            out_px = engine.price_at(bars, t_x)
            if out_px is None:
                continue
        rows.append(dict(day=d, entry=entry, pnl=side * (out_px - entry) - 0.30))
    report(f"London 08:00 add-leg / in_profit / {'2R stop' if stop_on else 'no stop'}",
           rows, "ldn_reentry")

print("\n=== 3. LONDON-OPEN ORB (the symmetry test) ===")
for filt in ("all", "corr<=0.5"):
    for stop_on in (False, True):
        rows = []
        for d in pd.Series(bars.index.date, index=bars.index).unique():
            day = pd.Timestamp(d)
            t0 = clock(day, 8, 0, LDN)
            t1 = t0 + pd.Timedelta(minutes=60)
            t_dead = clock(day, 13, 0, LDN)
            t_x = clock(day, 16, 0, NY)
            w = bars.loc[t0:t1 - pd.Timedelta(minutes=5)]
            if len(w) < 12:
                continue
            rh, rl = float(w.high.max()), float(w.low.min())
            if rh <= rl:
                continue
            if filt != "all":
                cr = CORR.get(day, np.nan)
                if not np.isfinite(cr) or cr > 0.5:
                    continue
            side, entry, t_fill = 0, None, None
            t = t1
            while t + pd.Timedelta(minutes=60) <= t_dead:
                blk = bars.loc[t:t + pd.Timedelta(minutes=55)]
                t += pd.Timedelta(minutes=60)
                if not len(blk):
                    continue
                c = float(blk.iloc[-1].close)
                if c > rh:
                    side, entry, t_fill = 1, c, t
                    break
                if c < rl:
                    side, entry, t_fill = -1, c, t
                    break
            if not side:
                continue
            stop = entry - side * 2 * (rh - rl) if stop_on else None
            path = bars.loc[t_fill:t_x - pd.Timedelta(minutes=5)]
            out_px = None
            if stop is not None and len(path):
                hitm = (path.low <= stop) if side == 1 else (path.high >= stop)
                if hitm.any():
                    out_px = stop
            if out_px is None:
                out_px = engine.price_at(bars, t_x)
                if out_px is None:
                    continue
            rows.append(dict(day=day, entry=entry, pnl=side * (out_px - entry) - 0.30))
        report(f"London ORB 60m / {filt} / {'2R stop' if stop_on else 'no stop'}",
               rows, "ldn_orb")

json.dump(OUT, open("results/derived.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} pre-registered cells. written: results/derived.json")
