"""Does AUDUSD confirming or diverging from the gold bias improve the strategy?"""
import pandas as pd, numpy as np, engine, sweep, audusd, warnings
warnings.filterwarnings("ignore")
from scipy import stats as st

gold = engine.load_bars()
aud = audusd.build()
OVL = (aud.index.min(), aud.index.max())

print("=== 0. THE RELATIONSHIP ITSELF ===")
g15 = np.log(gold.close.resample("15min").last()).diff()
a15 = np.log(aud.close).diff()
j = pd.concat([g15.rename("g"), a15.rename("a")], axis=1, join="inner").dropna()
j = j[(j.g != 0) & (j.a != 0)]
print(f"  15-minute return correlation, {len(j):,} bars: {j.g.corr(j.a):+.3f}")
j["h"] = j.index.hour
byh = j.groupby("h").apply(lambda x: x.g.corr(x.a))
asia = byh.loc[[1, 2, 3, 4, 5]].mean(); lon = byh.loc[[8, 9, 10, 11]].mean(); ny = byh.loc[[13, 14, 15, 16]].mean()
print(f"  by session: Asia (01-05 UTC) {asia:+.3f} | London (08-11) {lon:+.3f} | NY (13-16) {ny:+.3f}")
gd = gold.close.resample("1D").last().dropna()
gd.index = gd.index.tz_localize(None).normalize()
ad = audusd.daily_from_fred()
ad.index = pd.to_datetime(ad.index).normalize()
dj = pd.concat([np.log(gd).diff().rename("g"),
                np.log(ad).diff().rename("a")], axis=1, join="inner").dropna()
dj = dj[dj.index >= "2020-08-21"]
print(f"  daily return correlation 2020-2025, {len(dj):,} days: {dj.g.corr(dj.a):+.3f}")
roll = dj.g.rolling(20).corr(dj.a)
print(f"  20-day rolling correlation: median {roll.median():+.3f}, "
      f"range {roll.quantile(.05):+.3f} to {roll.quantile(.95):+.3f} (it is not stable)")

# ---------------------------------------------------------------- intraday test
print(f"\n=== 1. INTRADAY CONFLUENCE (AUDUSD data available {OVL[0].date()} .. {OVL[1].date()}) ===")
def aud_feature(day, t_bias):
    """AUDUSD's own move from 09:30 HKT to the moment gold's bias is set."""
    t0 = engine.session_start_utc(pd.Timestamp(day))
    w = aud.loc[t0:t_bias]
    if len(w) < 2:
        return np.nan
    return float(np.log(w.close.iloc[-1] / w.open.iloc[0]))

rows = []
for L in (30, 60):
    d = sweep.structure_stop(gold, L, buffer_r=99)     # plain breakout, time exits
    d = d[(pd.to_datetime(d.day) >= OVL[0].tz_localize(None)) &
          (pd.to_datetime(d.day) <= OVL[1].tz_localize(None))].copy()
    d["aud_ret"] = [aud_feature(r.day, r.t_fill) for r in d.itertuples()]
    d = d.dropna(subset=["aud_ret"])
    d["agree"] = (np.sign(d.aud_ret) == d.bias)
    for a in ("london_open", "london_mid", "pre_ny", "ny_close"):
        col = f"pnl_{a}"
        base = sweep.stats(d, col)
        for label, m in (("AUD agrees", d.agree), ("AUD diverges", ~d.agree)):
            s = sweep.stats(d[m], col)
            if s and base:
                rows.append({"range": f"{L}m", "exit": a, "subset": label, "n": s["n"],
                             "win%": round(s["win"]*100, 1), "PF": round(s["pf"], 3),
                             "exp_$": round(s["exp"], 2),
                             "vs_all_PF": round(s["pf"] - base["pf"], 3)})
r = pd.DataFrame(rows)
print(r.to_string(index=False))
n_all = len(d)
print(f"\n  (sample: {n_all} days with both gold and AUDUSD data — all inside the pre-2022 era)")

# significance of the split on the pooled sample
d60 = d
for a in ("london_mid", "ny_close"):
    x, y = d60[d60.agree][f"pnl_{a}"].dropna(), d60[~d60.agree][f"pnl_{a}"].dropna()
    t = st.ttest_ind(x, y, equal_var=False)
    print(f"  60m/{a:11s} agree {x.mean():+.2f} vs diverge {y.mean():+.2f} $/trade  "
          f"(t={t.statistic:+.2f}, p={t.pvalue:.3f})")

# --------------------------------------------------- full-sample regime version
print("\n=== 2. CORRELATION REGIME (daily AUD/gold correlation — available for all 5 years) ===")
roll = roll.reindex(pd.date_range(dj.index.min(), dj.index.max(), freq="D")).ffill()
rows = []
for L in (30, 60):
    for a in ("london_mid", "ny_close"):
        d2 = sweep.structure_stop(gold, L, buffer_r=99)
        d2["corr20"] = pd.to_datetime(d2.day).dt.normalize().map(roll.shift(1))
        d2 = d2.dropna(subset=["corr20"])
        base = sweep.stats(d2, f"pnl_{a}")
        for label, m in (("corr > 0.5 (risk-on link tight)", d2.corr20 > .5),
                         ("corr 0-0.5", (d2.corr20 >= 0) & (d2.corr20 <= .5)),
                         ("corr < 0 (decoupled)", d2.corr20 < 0)):
            s = sweep.stats(d2[m], f"pnl_{a}")
            if s:
                rows.append({"range": f"{L}m", "exit": a, "regime": label, "n": s["n"],
                             "win%": round(s["win"]*100, 1), "PF": round(s["pf"], 3),
                             "exp_$": round(s["exp"], 2), "vs_all_PF": round(s["pf"]-base["pf"], 3)})
print(pd.DataFrame(rows).to_string(index=False))
