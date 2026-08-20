"""Apply the loop-engineering framework's three metrics to our rule.

IC / ICIR, signal decay half-life, and an explicit Bonferroni correction - the
three things that framework asks for which we had not computed.
"""
import pandas as pd, numpy as np, engine, trades, warnings, json
warnings.filterwarnings("ignore")
from scipy import stats as st

gold = engine.load_bars()
t = pd.read_pickle("results/trades_60_ny.pkl")     # 60m range, NY close, corr already attached
t["ret"] = t.pnl_oz / t.entry * 100                # trade return, %
t["signal"] = -t["corr"]                           # higher signal = looser coupling = trade
t["ym"] = pd.to_datetime(t.day).dt.to_period("M")

print("=== 1. INFORMATION COEFFICIENT / ICIR ===")
print("   IC here = the monthly correlation between the filter's signal value and the")
print("   return that followed. Note this is a TIME-SERIES adaptation: the textbook IC")
print("   is cross-sectional, ranking many assets each period.\n")
ic = t.groupby("ym").apply(lambda x: x.signal.corr(x.ret) if len(x) >= 8 else np.nan).dropna()
icir = ic.mean() / ic.std()
n_m = len(ic)
print(f"   months with enough trades : {n_m}")
print(f"   mean IC                   : {ic.mean():+.4f}")
print(f"   sd of IC                  : {ic.std():.4f}")
print(f"   ICIR                      : {icir:+.3f}   (annualised {icir*np.sqrt(12):+.2f})")
print(f"   share of months IC > 0    : {(ic > 0).mean()*100:.0f}%")
print(f"   t-stat of mean IC         : {ic.mean()/ic.std()*np.sqrt(n_m):+.2f} "
      f"(p={st.ttest_1samp(ic,0).pvalue:.3f})")
band = "STRONG (>0.5)" if icir > .5 else "MODERATE (0.3-0.5)" if icir > .3 else "WEAK (<0.3)"
print(f"   framework verdict         : {band}")

# the same, for the direction signal alone (breakout side vs realised move)
t["dir_ic"] = t.side
ic2 = t.groupby("ym").apply(lambda x: x.dir_ic.corr(x.ret) if len(x) >= 8 else np.nan).dropna()
print(f"\n   for comparison, the raw breakout DIRECTION as the signal: "
      f"ICIR {ic2.mean()/ic2.std():+.3f}")

print("\n=== 2. SIGNAL DECAY / HALF-LIFE ===")
print("   Autocorrelation of the filter signal itself, and of its predictive power.\n")
corr_daily = trades.corr_series(gold, 20).dropna()
ac = [(lag, corr_daily.autocorr(lag)) for lag in (1, 5, 10, 20, 50, 100)]
for lag, v in ac:
    print(f"   signal autocorrelation, lag {lag:>3}d : {v:+.3f}")
x = np.array([l for l, _ in ac]); y = np.array([v for _, v in ac])
m = y > 0
hl = np.log(0.5) / np.polyfit(x[m], np.log(y[m]), 1)[0]
print(f"   -> estimated half-life     : {hl:.0f} days")
print(f"   holding period             : 0.45 days (10.7 hours)")
print(f"   framework rule is 'reject if half-life < 5 days' -> "
      f"{'PASS' if hl >= 5 else 'FAIL'} by a wide margin")

# predictive decay: does the signal measured N days ago still predict?
print("\n   predictive power at increasing staleness (profit factor of the kept set):")
pf = lambda s: float(s[s > 0].sum()/max(-s[s <= 0].sum(), 1e-9))
raw = trades.corr_series(gold, 20)
for lag in (1, 3, 5, 10, 20, 40):
    C = raw.shift(lag - 1)                     # corr_series is already shifted 1
    z = t.copy(); z["c2"] = pd.to_datetime(z.day).dt.normalize().map(C)
    z = z.dropna(subset=["c2"])
    k = z[z.c2 <= .5]
    print(f"     lag {lag:>2}d: n={len(k):>4} PF={pf(k.pnl_oz):.3f}")

print("\n=== 3. BONFERRONI CORRECTION, STATED EXPLICITLY ===")
best = t[t["corr"] <= .5]
pct = best.pnl_oz / best.entry * 100
tstat = pct.mean()/pct.std()*np.sqrt(len(pct))
p_raw = st.ttest_1samp(pct, 0).pvalue
print(f"   headline rule: t = {tstat:+.2f}, uncorrected p = {p_raw:.5f}")
for n_tests in (18, 50, 100, 200):
    print(f"   Bonferroni for {n_tests:>3} tests: threshold p < {0.05/n_tests:.5f}  -> "
          f"{'PASSES' if p_raw < 0.05/n_tests else 'fails'}")
print(f"\n   For reference, the max-statistic randomisation test used in round two gave")
print(f"   a corrected p of 0.036 across 18 configurations. That method is strictly")
print(f"   better than Bonferroni here because our tests are highly correlated with")
print(f"   each other, which Bonferroni ignores and therefore over-penalises.")

json.dump({"icir": float(icir), "ic_mean": float(ic.mean()), "ic_sd": float(ic.std()),
           "ic_months": int(n_m), "ic_pos_share": float((ic > 0).mean()),
           "half_life_days": float(hl),
           "autocorr": [{"lag": int(l), "v": float(v)} for l, v in ac],
           "p_raw": float(p_raw), "t": float(tstat)},
          open("results/loop_metrics.json", "w"), indent=1)
