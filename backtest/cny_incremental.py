"""The fair test: does CNY in its BEST form add anything to AUD in its stated form?"""
import pandas as pd, numpy as np, engine, cny, warnings
warnings.filterwarnings("ignore")
from scipy import stats as st

gold = engine.load_bars()
t0 = pd.read_pickle("results/trades_60_ny.pkl").drop(columns=["corr"])
d = pd.to_datetime(t0.day).dt.normalize()
C20, _ = cny.build_corr(gold, 20)
C90, _ = cny.build_corr(gold, 90)
t = t0.copy()
t["aud"] = d.map(C20.aud)                 # AUD as stated in round two
t["cny90"] = d.map(C90.cny)               # CNY at its best-of-grid window
t = t.dropna(subset=["aud", "cny90"]).reset_index(drop=True)
pf = lambda s: float(s[s > 0].sum()/max(-s[s <= 0].sum(), 1e-9))
def stat(x):
    p = x.pnl_oz; pct = p/x.entry*100
    return dict(n=len(x), pf=pf(p), exp=float(p.mean()),
                t=float(pct.mean()/pct.std()*np.sqrt(len(p))) if len(p) > 2 else np.nan)

thr_c = t.cny90.quantile(.60)
lo_a, lo_c = t.aud <= .5, t.cny90 <= thr_c
print(f"overlap of the two filters: {(lo_a == lo_c).mean()*100:.0f}% of days agree; "
      f"regime series correlate {t.aud.corr(t.cny90):+.3f}\n")

print("=== Cross-tab, CNY at its best window (90d) ===")
for lbl, m in (("AUD low  · CNY low ", lo_a & lo_c), ("AUD low  · CNY high", lo_a & ~lo_c),
               ("AUD high · CNY low ", ~lo_a & lo_c), ("AUD high · CNY high", ~lo_a & ~lo_c)):
    s = stat(t[m])
    if s["n"] >= 30:
        print(f"  {lbl} n={s['n']:>4} PF={s['pf']:.3f} exp=${s['exp']:+.2f} t={s['t']:+.2f}")

print("\n=== Incremental value, both directions ===")
sub = t[lo_a]
a, b = sub[sub.cny90 <= thr_c], sub[sub.cny90 > thr_c]
tt = st.ttest_ind(a.pnl_oz/a.entry, b.pnl_oz/b.entry, equal_var=False)
print(f"  CNY inside the AUD-filtered set: PF {pf(a.pnl_oz):.3f} (n={len(a)}) vs "
      f"{pf(b.pnl_oz):.3f} (n={len(b)}), t={tt.statistic:+.2f}, p={tt.pvalue:.3f}")
sub = t[lo_c]
a, b = sub[sub.aud <= .5], sub[sub.aud > .5]
tt = st.ttest_ind(a.pnl_oz/a.entry, b.pnl_oz/b.entry, equal_var=False)
print(f"  AUD inside the CNY-filtered set: PF {pf(a.pnl_oz):.3f} (n={len(a)}) vs "
      f"{pf(b.pnl_oz):.3f} (n={len(b)}), t={tt.statistic:+.2f}, p={tt.pvalue:.3f}")

pct = t.pnl_oz/t.entry*100
X = np.column_stack([t.aud, t.cny90, np.ones(len(t))])
beta, *_ = np.linalg.lstsq(X, pct.values, rcond=None)
resid = pct.values - X @ beta
se = np.sqrt(np.sum(resid**2)/(len(t)-3)*np.diag(np.linalg.inv(X.T @ X)))
print(f"\n  joint regression: AUD {beta[0]*100:+.1f}bp (t={beta[0]/se[0]:+.2f}), "
      f"CNY90 {beta[1]*100:+.1f}bp (t={beta[1]/se[1]:+.2f})")

print("\n=== Is CNY's out-of-sample 'validation' real, or is the filter just inactive? ===")
t["os"] = pd.to_datetime(t.day) >= "2024-01-01"
for nm, m in (("IS 2020-23", ~t.os), ("OS 2024-25", t.os)):
    s = t[m]
    keep = (s.cny90 <= thr_c).mean()
    unf = stat(s)
    fil = stat(s[s.cny90 <= thr_c])
    print(f"  {nm}: CNY keeps {keep*100:>4.0f}% of days | unfiltered PF {unf['pf']:.3f} "
          f"-> filtered PF {fil['pf']:.3f}  (lift {fil['pf']-unf['pf']:+.3f})")
    sa = stat(s[s.aud <= .5])
    print(f"{'':13} AUD keeps {(s.aud<=.5).mean()*100:>4.0f}% of days | unfiltered PF {unf['pf']:.3f} "
          f"-> filtered PF {sa['pf']:.3f}  (lift {sa['pf']-unf['pf']:+.3f})")
