"""Round-3 results -> results/summary3.json"""
import pandas as pd, numpy as np, engine, trades, portfolio as P, json, warnings
warnings.filterwarnings("ignore")
gold = engine.load_bars()
corr = trades.corr_series(gold, 20)
pf = P.pf
O = {"start": 2000.0}
O["thresholds"] = json.load(open("results/thresholds.json"))
O["stress"] = json.load(open("results/portfolio_stress.json"))

SLIP = 0.30                     # assumed extra slippage on a stopped exit
sets = {}
for sr in (1.0, 2.0, 3.0, None):
    d = trades.generate(gold, 60, stop_r=sr)
    d["corr"] = pd.to_datetime(d.day).map(corr)
    sets[sr] = d.dropna(subset=["corr"])

def slipped(d):
    g = d.copy()
    g["pnl_oz"] = g.pnl_oz - np.where(g.reason == "stop", SLIP, 0.0)
    return g

# ---- headline sizing table (filtered) ---------------------------------------
runs, curves = [], {}
fa = sets[None][sets[None]["corr"] <= .5].reset_index(drop=True)
spec = [("All-in, no leverage", fa, "allin", None, 1.0),
        ("All-in, 5:1", fa, "allin", None, 5.0),
        ("All-in, 20:1", fa, "allin", None, 20.0),
        ("All-in, 100:1", fa, "allin", None, 100.0)]
for sr in (1.0, 2.0, 3.0):
    f = slipped(sets[sr][sets[sr]["corr"] <= .5]).reset_index(drop=True)
    for risk in (0.01, 0.02):
        spec.append((f"Risk {risk*100:.0f}% · {sr:.0f}R stop", f, "risk", risk, 20.0))
for label, tr, mode, param, lev in spec:
    r = P.simulate(tr, mode, param, lev)
    curves[label] = r.pop("curve")
    runs.append({"label": label, "mode": mode, "lev": lev, "risk": param, **r})
O["runs"] = runs

# ---- unfiltered counterparts -------------------------------------------------
un = []
ua = sets[None].reset_index(drop=True)
us = slipped(sets[2.0]).reset_index(drop=True)
for label, tr, mode, param, lev in [("All-in, 20:1", ua, "allin", None, 20.0),
                                    ("Risk 1% · 2R stop", us, "risk", 0.01, 20.0),
                                    ("Risk 2% · 2R stop", us, "risk", 0.02, 20.0)]:
    r = P.simulate(tr, mode, param, lev)
    curves["unfiltered " + label] = r.pop("curve")
    un.append({"label": label, **r})
O["unfiltered"] = un

# ---- slippage grid -----------------------------------------------------------
sl = []
for sr in (1.0, 2.0, 3.0):
    row = {"stop": sr}
    base = sets[sr][sets[sr]["corr"] <= .5]
    for s in (0.0, 0.25, 0.5, 1.0):
        g = base.copy()
        g["pnl_oz"] = g.pnl_oz - np.where(g.reason == "stop", s, 0.0)
        row[f"s{s}"] = P.simulate(g.reset_index(drop=True), "risk", 0.01, 20.0)["final"]
    row["stopped"] = float((base.reason == "stop").mean())
    sl.append(row)
O["slippage"] = sl

# ---- benchmark ---------------------------------------------------------------
p0, p1 = float(gold.close.iloc[0]), float(gold.close.iloc[-1])
yrs = (gold.index[-1] - gold.index[0]).days / 365.25
dl = gold.close.resample("1D").last().dropna()
O["benchmark"] = {"final": 2000 * p1 / p0, "cagr": (p1 / p0) ** (1 / yrs) - 1,
                  "dd": float(((dl.cummax() - dl) / dl.cummax()).max())}

# buy & hold curve on the same calendar
bh = gold.close.resample("1D").last().dropna()
bh = bh[bh.index >= pd.Timestamp(str(fa.day.iloc[0]), tz="UTC")]
bh = (bh / float(bh.iloc[0]) * 2000.0)
bh.index = [d.date() for d in bh.index]
curves["Buy and hold gold"] = pd.Series(bh.values, index=bh.index)

def thin(c, n=200):
    step = max(len(c) // n, 1)
    return {"x": [str(d) for d in c.index[::step]], "y": [round(float(v), 2) for v in c.values[::step]]}
O["curves"] = {k: thin(v) for k, v in curves.items()}
json.dump(O, open("results/summary3.json", "w"), indent=1)
print("=== FINAL TABLE ($2,000, filtered rule, %0.2f slippage on stops) ===" % SLIP)
for r in runs:
    print(f"  {r['label']:<24} final ${r['final']:>10,.0f}  CAGR {r['cagr']*100:>7.1f}%  "
          f"maxDD {r['max_dd']*100:>5.1f}%  worst trade {r['worst_trade']*100:>6.1f}%  "
          f"ruin {r['ruin'] or '-'}")
print("\n=== UNFILTERED ===")
for r in un:
    print(f"  {r['label']:<24} final ${r['final']:>10,.0f}  CAGR {r['cagr']*100:>7.1f}%  "
          f"maxDD {r['max_dd']*100:>5.1f}%  ruin {r['ruin'] or '-'}")
print(f"\nbuy & hold gold: ${O['benchmark']['final']:,.0f}  CAGR {O['benchmark']['cagr']*100:.1f}%  "
      f"maxDD {O['benchmark']['dd']*100:.1f}%")
