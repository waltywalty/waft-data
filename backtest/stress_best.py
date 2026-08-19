"""Stress the single best configuration found (60m range, London-close exit).
Anything that survives a wide search has to be shown to be stable, not just lucky."""
import pandas as pd, numpy as np, engine, entries
from scipy import stats

bars = engine.load_bars()
t = engine.backtest(bars, 60, "london_close")
t = t[t.traded].copy()
t["yr"] = t.t_fill.dt.year
t["passive"] = (t.exit - t.entry) / t.entry * 100          # always-long, same window
t["excess"] = t.pnl_pct - t.passive

print("=== 60m range / London-close exit — per year ===")
g = t.groupby("yr").apply(lambda x: pd.Series({
    "n": len(x), "win%": round((x.pnl_usd > 0).mean()*100, 1),
    "PF": round(x.pnl_usd[x.pnl_usd > 0].sum() / max(-x.pnl_usd[x.pnl_usd <= 0].sum(), 1e-9), 2),
    "strategy_%": round(x.pnl_pct.sum(), 1),
    "passive_long_%": round(x.passive.sum(), 1),
    "excess_%": round(x.excess.sum(), 1)}), include_groups=False)
print(g.to_string())

half = t.t_fill.dt.date < pd.Timestamp("2024-01-01").date()
for name, sub in [("IN-SAMPLE  2020-08..2023-12", t[half]), ("OUT-OF-SAMPLE 2024-01..2025-08", t[~half])]:
    pf = sub.pnl_usd[sub.pnl_usd > 0].sum() / -sub.pnl_usd[sub.pnl_usd <= 0].sum()
    print(f"\n{name}: n={len(sub)} PF={pf:.3f} win={100*(sub.pnl_usd>0).mean():.1f}% "
          f"exp={sub.pnl_pct.mean()*100:+.2f}bp  t={sub.pnl_pct.mean()/sub.pnl_pct.std()*np.sqrt(len(sub)):+.2f}")

print("\n=== Does it beat simply being long gold over the identical window? ===")
tt = stats.ttest_1samp(t.excess, 0)
print(f"  strategy total {t.pnl_pct.sum():+.1f}%   passive-long total {t.passive.sum():+.1f}%   "
      f"excess {t.excess.sum():+.1f}%  (t={tt.statistic:+.2f}, p={tt.pvalue:.3f})")

print("\n=== Cost sensitivity (60m / London close) ===")
for c in (0.0, 0.15, 0.30, 0.50, 0.75, 1.00):
    p = t.pnl_usd + 0.30 - c
    pf = p[p > 0].sum() / -p[p <= 0].sum()
    print(f"  round-trip ${c:.2f}: PF={pf:.3f}  exp=${p.mean():+.3f}  total=${p.sum():+.0f}")

print("\n=== Session-start sensitivity (is 09:30 HKT special?) ===")
import copy
for hh, mm in [(8,0),(8,30),(9,0),(9,30),(10,0),(10,30),(11,0)]:
    engine.RANGE_START_HKT = (hh, mm)
    x = engine.backtest(bars, 60, "london_close"); x = x[x.traded]
    m = engine.metrics(x, "")
    print(f"  range starts {hh:02d}:{mm:02d} HKT: n={m['n']:4d} PF={m['profit_factor']:.3f} "
          f"win={m['win_rate']*100:.1f}% exp=${m['exp_usd']:+.3f} t={m['t_stat']:+.2f}")
engine.RANGE_START_HKT = (9, 30)
