"""The gold/AUD correlation regime looked like a real filter. Is it, or is it just
a disguised proxy for which year it was?"""
import pandas as pd, numpy as np, engine, sweep, audusd, warnings
warnings.filterwarnings("ignore")
from scipy import stats as st

gold = engine.load_bars()
gd = gold.close.resample("1D").last().dropna(); gd.index = gd.index.tz_localize(None).normalize()
ad = audusd.daily_from_fred(); ad.index = pd.to_datetime(ad.index).normalize()
dj = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
               axis=1, join="inner").dropna()
roll = dj.g.rolling(20).corr(dj.a).reindex(
    pd.date_range(dj.index.min(), dj.index.max(), freq="D")).ffill().shift(1)

d = sweep.structure_stop(gold, 60, buffer_r=99)
d["corr20"] = pd.to_datetime(d.day).dt.normalize().map(roll)
d = d.dropna(subset=["corr20"]).copy()
d["yr"] = pd.to_datetime(d.day).dt.year
d["hi"] = d.corr20 > .5

print("=== 1. Is the regime just a proxy for the calendar? ===")
print(d.groupby("yr").apply(lambda x: pd.Series({
    "days": len(x), "share_corr>0.5": round(x.hi.mean(), 2),
    "mean_corr20": round(x.corr20.mean(), 2)})).to_string())

print("\n=== 2. Does the filter work WITHIN each year? (controls for the regime confound) ===")
print(f"{'year':>6}{'n hi':>6}{'PF hi':>8}{'exp hi':>9}{'n lo':>6}{'PF lo':>8}{'exp lo':>9}{'lo-hi':>9}")
agree = 0; tot = 0
for y, x in d.groupby("yr"):
    for col in ["pnl_ny_close"]:
        a, b = x[x.hi][col].dropna(), x[~x.hi][col].dropna()
        if len(a) < 25 or len(b) < 25: continue
        pf = lambda s: s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9)
        tot += 1; agree += (b.mean() > a.mean())
        print(f"{y:>6}{len(a):>6}{pf(a):>8.2f}{a.mean():>9.2f}{len(b):>6}{pf(b):>8.2f}"
              f"{b.mean():>9.2f}{b.mean()-a.mean():>9.2f}")
print(f"  low-correlation beat high-correlation in {agree} of {tot} years with enough data")

print("\n=== 3. Continuous test: does correlation predict the trade's return? ===")
for col in ("pnl_london_mid", "pnl_ny_close"):
    x = d.dropna(subset=[col])
    pct = x[col] / x.entry * 100
    r = st.spearmanr(x.corr20, pct)
    ols = st.linregress(x.corr20, pct)
    print(f"  {col:16s} n={len(x):4d}  Spearman rho={r.statistic:+.3f} (p={r.pvalue:.4f})  "
          f"slope={ols.slope*100:+.2f}bp per +1.0 corr (p={ols.pvalue:.4f})")

print("\n=== 4. In-sample / out-of-sample ===")
d["os"] = pd.to_datetime(d.day) >= "2024-01-01"
for col in ("pnl_london_mid", "pnl_ny_close"):
    for name, m in (("IS 2020-23", ~d.os), ("OS 2024-25", d.os)):
        x = d[m].dropna(subset=[col])
        a, b = x[x.hi][col], x[~x.hi][col]
        pf = lambda s: s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9)
        if len(a) > 20 and len(b) > 20:
            print(f"  {col:16s} {name}: corr>0.5 n={len(a):4d} PF={pf(a):.2f} exp=${a.mean():+.2f} | "
                  f"corr<=0.5 n={len(b):4d} PF={pf(b):.2f} exp=${b.mean():+.2f}")

print("\n=== 5. Placebo: block-shuffle the regime labels ===")
rng = np.random.default_rng(11)
x = d.dropna(subset=["pnl_ny_close"]).reset_index(drop=True)
pnl = x.pnl_ny_close.values; hi = x.hi.values
real = pnl[~hi].mean() - pnl[hi].mean()
blocks = np.array_split(np.arange(len(hi)), 60)
N, beats = 5000, 0
for _ in range(N):
    order = rng.permutation(len(blocks))
    perm = np.concatenate([hi[blocks[i]] for i in order])[:len(hi)]
    if perm.sum() == 0 or (~perm).sum() == 0:
        continue
    if (pnl[~perm].mean() - pnl[perm].mean()) >= real:
        beats += 1
print(f"  observed low-minus-high edge ${real:+.2f}/trade")
print(f"  block-shuffled labels match or beat it in {beats/N*100:.1f}% of {N} draws -> p={beats/N:.3f}")
print("  (block shuffling preserves the regime's persistence, so it tests the LABEL, not the calendar)")

print("\n=== 6. Is it just a disguise for volatility or trendiness? ===")
gsess = gold.close.resample("1D").last().dropna()
gsess.index = gsess.index.tz_localize(None).normalize()
ret = np.log(gsess).diff()
vol20 = ret.rolling(20).std().shift(1)
# trendiness: |20d return| / sum of |daily returns| over the same window
trend20 = (ret.rolling(20).sum().abs() / ret.abs().rolling(20).sum()).shift(1)
d2 = d.copy()
d2["vol20"] = pd.to_datetime(d2.day).dt.normalize().map(vol20)
d2["trend20"] = pd.to_datetime(d2.day).dt.normalize().map(trend20)
d2 = d2.dropna(subset=["vol20", "trend20", "pnl_ny_close"])
print(f"  corr(corr20, vol20)   = {d2.corr20.corr(d2.vol20):+.3f}")
print(f"  corr(corr20, trend20) = {d2.corr20.corr(d2.trend20):+.3f}")
pf = lambda s: s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9)
print("\n  double sort - correlation regime WITHIN each volatility tercile:")
d2["vq"] = pd.qcut(d2.vol20, 3, labels=["low vol", "mid vol", "high vol"])
for q, g in d2.groupby("vq", observed=True):
    a, b = g[g.hi].pnl_ny_close, g[~g.hi].pnl_ny_close
    if len(a) > 20 and len(b) > 20:
        print(f"    {q:9s} corr>0.5 n={len(a):3d} PF={pf(a):.2f} exp=${a.mean():+.2f} | "
              f"corr<=0.5 n={len(b):3d} PF={pf(b):.2f} exp=${b.mean():+.2f}")
print("\n  double sort - correlation regime WITHIN each trendiness tercile:")
d2["tq"] = pd.qcut(d2.trend20, 3, labels=["choppy", "mid", "trending"])
for q, g in d2.groupby("tq", observed=True):
    a, b = g[g.hi].pnl_ny_close, g[~g.hi].pnl_ny_close
    if len(a) > 20 and len(b) > 20:
        print(f"    {q:9s} corr>0.5 n={len(a):3d} PF={pf(a):.2f} exp=${a.mean():+.2f} | "
              f"corr<=0.5 n={len(b):3d} PF={pf(b):.2f} exp=${b.mean():+.2f}")

print("\n=== 7. Combined rule: 60m bias breakout, hold to NY close, only when corr20 <= 0.5 ===")
x = d.dropna(subset=["pnl_ny_close"])
sel = x[~x.hi]
eq = sel.sort_values("t_fill").pnl_ny_close.cumsum()
pct = sel.pnl_ny_close / sel.entry * 100
print(f"  n={len(sel)}  win={100*(sel.pnl_ny_close>0).mean():.1f}%  PF={pf(sel.pnl_ny_close):.3f}  "
      f"exp=${sel.pnl_ny_close.mean():+.2f}  total=${sel.pnl_ny_close.sum():+.0f}")
print(f"  t-stat={pct.mean()/pct.std()*np.sqrt(len(pct)):+.2f}   "
      f"max drawdown ${(eq.cummax()-eq).max():.0f}")
print(f"  trades skipped by the filter: {len(x)-len(sel)} of {len(x)} ({(1-len(sel)/len(x))*100:.0f}%)")
