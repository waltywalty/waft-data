"""Realism checks on the sized results: stop width, stop slippage, path dependence."""
import pandas as pd, numpy as np, engine, trades, portfolio as P, warnings, json
warnings.filterwarnings("ignore")
gold = engine.load_bars()
corr = trades.corr_series(gold, 20)
pf = P.pf

print("=== A. STOP WIDTH (filtered rule, corr20 <= 0.5) ===")
print(f"{'stop':>8}{'n':>6}{'stopped%':>10}{'win%':>7}{'PF':>8}{'exp$/oz':>10}{'avg stop $':>12}")
sets = {}
for sr in (0.75, 1.0, 1.5, 2.0, 3.0, None):
    d = trades.generate(gold, 60, stop_r=sr)
    d["corr"] = pd.to_datetime(d.day).map(corr)
    d = d.dropna(subset=["corr"])
    f = d[d["corr"] <= 0.5].reset_index(drop=True)
    sets[sr] = f
    lbl = f"{sr:.2f}R" if sr else "none"
    print(f"{lbl:>8}{len(f):>6}{100*(f.reason=='stop').mean():>9.0f}%{100*(f.pnl_oz>0).mean():>6.1f}%"
          f"{pf(f.pnl_oz):>8.3f}{f.pnl_oz.mean():>10.2f}"
          f"{(sr*f['range']).mean() if sr else np.nan:>12.2f}")

print("\n=== B. STOP SLIPPAGE (risk 1% of a $2,000 account) ===")
print("  72% of 1R trades are stopped, and the stop sits only ~$5 away, so slippage bites hard.")
print(f"{'stop':>8}{'slip $0.00':>13}{'$0.25':>11}{'$0.50':>11}{'$1.00':>11}")
for sr in (1.0, 1.5, 2.0, 3.0):
    f = sets[sr]
    line = f"{sr:>7.1f}R"
    for slip in (0.0, 0.25, 0.50, 1.00):
        g = f.copy()
        g["pnl_oz"] = g.pnl_oz - np.where(g.reason == "stop", slip, 0.0)
        r = P.simulate(g, "risk", 0.01, 20.0)
        line += f"{r['final']:>11,.0f}" if slip == 0 else f"{r['final']:>11,.0f}"
    print(line)

print("\n=== C. Effective leverage actually used (risk 1%, 2R stop) ===")
f = sets[2.0]
eq = 2000.0; levs = []; capped = 0
for r in f.itertuples():
    oz = (eq * 0.01) / max(r.stop_dist, .01)
    raw = oz * r.entry / eq
    if oz > eq * 20 / r.entry:
        oz = eq * 20 / r.entry; capped += 1
    levs.append(oz * r.entry / eq)
    if oz * r.mae_oz >= eq: eq = 0; break
    eq = max(eq + oz * r.pnl_oz, 0)
print(f"  median {np.median(levs):.1f}:1 | 90th pct {np.percentile(levs,90):.1f}:1 | "
      f"max {np.max(levs):.1f}:1 | margin cap bound on {capped} of {len(f)} trades")

print("\n=== D. Path dependence ===")
rng = np.random.default_rng(5)
f = sets[2.0]
dds = []
for _ in range(2000):
    g = f.sample(frac=1.0, replace=False, random_state=int(rng.integers(1e9))).reset_index(drop=True)
    dds.append(P.simulate(g, "risk", 0.01, 20.0)["max_dd"])
dds = np.array(dds)
act = P.simulate(f, "risk", 0.01, 20.0)
print("  With fixed-fractional sizing the FINAL equity is order-independent by construction")
print(f"  (each trade returns a fixed fraction), so every shuffle ends at ${act['final']:,.0f}.")
print(f"  The DRAWDOWN is not: shuffling gives max DD median {np.median(dds)*100:.0f}%, "
      f"5th-95th {np.percentile(dds,5)*100:.0f}%-{np.percentile(dds,95)*100:.0f}%")
print(f"  history happened to deliver {act['max_dd']*100:.0f}% - "
      f"a rerun of the same edge could easily have been worse.")

print("\n=== E. The all-in 20:1 path in detail ===")
fa = pd.read_pickle("results/trades_60_ny.pkl")
fa = fa[fa["corr"] <= 0.5].reset_index(drop=True)
r = P.simulate(fa, "allin", None, 20.0)
c = r["curve"]
print(f"  final ${r['final']:,.0f} but low point was ${c.min():,.2f} on {c.idxmin()}")
print(f"  that is {(1-c.min()/c.cummax().loc[c.idxmin()])*100:.2f}% below the running peak — "
      f"a real broker would have closed the account long before this")
print(f"  peak was ${c.cummax().max():,.0f}; worst single trade {r['worst_trade']*100:.1f}%")
mx = float((fa.mae_oz / fa.entry).max() * 100)
mx_all = float((pd.read_pickle("results/trades_60_ny.pkl").eval("mae_oz/entry")).max() * 100)
print(f"  worst adverse excursion among FILTERED trades: {mx:.2f}% of price -> at 20:1 that is "
      f"{mx*20:.0f}% of the account")
print(f"  worst across ALL trades in the sample: {mx_all:.2f}% -> {mx_all*20:.0f}% of the account. "
      f"Anything at or past 5% is a zero.")
json.dump({"stop_grid": [{"stop": (sr if sr else 0), "n": len(sets[sr]),
                          "stopped": float((sets[sr].reason == 'stop').mean()),
                          "win": float((sets[sr].pnl_oz > 0).mean()),
                          "pf": pf(sets[sr].pnl_oz), "exp": float(sets[sr].pnl_oz.mean())}
                         for sr in (0.75, 1.0, 1.5, 2.0, 3.0, None)],
           "shuffle_dd": {"median": float(np.median(dds)), "p5": float(np.percentile(dds, 5)),
                          "p95": float(np.percentile(dds, 95)), "actual_dd": float(act["max_dd"]),
                          "final": float(act["final"])},
           "allin20_low": float(c.min())},
          open("results/portfolio_stress.json", "w"), indent=1)
