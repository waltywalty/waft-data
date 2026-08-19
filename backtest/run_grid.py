"""Core parameter grid: 3 range lengths x 4 London exit anchors."""
import pandas as pd, numpy as np, engine, pickle

pd.set_option("display.width", 200, "display.max_columns", 50)
bars = engine.load_bars()

rows, logs = [], {}
for L in (5, 15, 30):
    for anchor in engine.EXITS:
        tr = engine.backtest(bars, L, anchor)
        logs[(L, anchor)] = tr
        m = engine.metrics(tr, f"{L}m / {anchor}")
        m["range_min"], m["exit"] = L, anchor
        rows.append(m)

res = pd.DataFrame(rows)
pickle.dump(logs, open("results/grid_logs.pkl", "wb"))
res.to_csv("results/grid_metrics.csv", index=False)

out = res[["range_min", "exit", "n", "trade_rate", "long", "short", "win_rate",
           "profit_factor", "exp_usd", "exp_pct", "payoff", "total_pct", "max_dd_pct",
           "sharpe_ann", "t_stat"]].copy()
for c in ["trade_rate", "win_rate", "profit_factor", "payoff"]:
    out[c] = out[c].round(3)
for c in ["exp_usd", "exp_pct", "total_pct", "max_dd_pct", "sharpe_ann", "t_stat"]:
    out[c] = out[c].round(2)
print("=== CORE GRID: 09:30 HKT opening-range breakout, XAUUSD, Aug-2020..Aug-2025 ===")
print("(costs $0.30/round trip; pnl_pct = % of gold price; exit at London clock time)\n")
print(out.to_string(index=False))

# breakout timing distribution
print("\n=== breakout timing (minutes after range close) ===")
for L in (5, 15, 30):
    t = logs[(L, "london_close")]
    t = t[t.traded]
    q = t.brk_delay_min.quantile([.25, .5, .75, .9]).round(0)
    utc = (t.t_entry.dt.hour + t.t_entry.dt.minute / 60)
    print(f"  {L:2d}m range: median {q.loc[0.5]:.0f} min  (p25 {q.loc[0.25]:.0f} / p75 {q.loc[0.75]:.0f} / p90 {q.loc[0.9]:.0f})"
          f" | median entry {int(utc.median()):02d}:{int(utc.median()%1*60):02d} UTC"
          f" | {(t.brk_delay_min<=60).mean()*100:.0f}% break within 1h")
