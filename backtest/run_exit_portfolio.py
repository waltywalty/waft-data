"""The decisive exit comparison: $2,000 at flat 1% risk, deployed exit vs the
two profit-factor winners from run_exits (breakeven at +1 range, 2x-range
trail). PF is a ratio; compounding cares about expectancy against risk taken.
Position is sized off the INITIAL 2R stop in all three cases, so the variants
differ only in realized exits.

The path-walk is run_exits.walk (same code, copied - run_exits executes its
study on import)."""
import pandas as pd, numpy as np, warnings, json
import engine, trades
warnings.filterwarnings("ignore")

bars = engine.load_bars()
D = pd.read_pickle("results/trades_deployable.pkl")
D["day"] = pd.to_datetime(D.day)
nostop = trades.generate(bars, 60, stop_r=None, cost=0.30, entry_cutoff_ldn=8)
nostop["day"] = pd.to_datetime(nostop.day)
N = nostop[nostop.day.isin(D.day)].copy()


def walk(r, stop_mult=2.0, trail_mult=None, be_after=None):
    side, entry, rng_ = r.side, r.entry, r.range
    stop = entry - side * stop_mult * rng_
    best = entry
    for ts, b in bars.loc[r.t_fill:r.t_out - pd.Timedelta(minutes=5)].iterrows():
        cur = stop
        if trail_mult is not None:
            tr = best - side * trail_mult * rng_
            cur = max(cur, tr) if side == 1 else min(cur, tr)
        if be_after is not None and side * (best - entry) >= be_after * rng_:
            cur = max(cur, entry) if side == 1 else min(cur, entry)
        if (b.low <= cur) if side == 1 else (b.high >= cur):
            return cur
        best = max(best, b.high) if side == 1 else min(best, b.low)
    return engine.price_at(bars, r.t_out)


def equity(pnls, stops, entries, tf):
    eq, peak, mdd = 2000.0, 2000.0, 0.0
    for p, sd, e in zip(pnls, stops, entries):
        oz = min(eq * 0.01 / sd, 20.0 * eq / e)
        eq += oz * p
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    yrs = (tf.iloc[-1] - tf.iloc[0]).days / 365.25
    return eq, (eq / 2000.0) ** (1 / yrs) - 1, mdd


OUT = {}
for lbl, kw in (("deployed (2R stop, 16:00 NY)", {}),
                ("breakeven at +1 range", {"be_after": 1.0}),
                ("trail 2 x range", {"trail_mult": 2.0})):
    pnls, stops, entries, tf = [], [], [], []
    for _, r in N.iterrows():
        px = walk(r, **kw)
        if px is None:
            continue
        pnls.append(r.side * (px - r.entry) - 0.30)
        stops.append(2.0 * r.range)
        entries.append(r.entry)
        tf.append(r.t_fill)
    tf = pd.Series(tf)
    fin, cagr, mdd = equity(pnls, stops, entries, tf)
    p = pd.Series(pnls)
    OUT[lbl] = {"n": len(p), "pf": float(p[p > 0].sum() / -p[p <= 0].sum()),
                "exp": float(p.mean()), "final": fin, "cagr": cagr, "mdd": mdd}
    print(f"{lbl:32s} n={len(p)} PF={OUT[lbl]['pf']:.3f} exp={p.mean():+.2f} | "
          f"$2,000 -> ${fin:,.0f}  CAGR {cagr*100:+.1f}%  maxDD {mdd*100:.1f}%")

json.dump(OUT, open("results/exit_portfolio.json", "w"), indent=1)
print("written: results/exit_portfolio.json")
