"""CNY vs AUD as the regime reference, and whether CNY adds anything on top."""
import pandas as pd, numpy as np, engine, trades, cny, warnings, json
warnings.filterwarnings("ignore")
from scipy import stats as st

gold = engine.load_bars()
C, _ = cny.build_corr(gold, 20)
t = pd.read_pickle("results/trades_60_ny.pkl")          # 60m range, NY close, no stop
t = t.drop(columns=["corr"])
d = pd.to_datetime(t.day).dt.normalize()
t["c_cny"], t["c_aud"] = d.map(C.cny), d.map(C.aud)
t = t.dropna(subset=["c_cny", "c_aud"]).reset_index(drop=True)

pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
def stat(x):
    p = x.pnl_oz; pct = p / x.entry * 100
    return dict(n=len(x), pf=pf(p), win=float((p > 0).mean()), exp=float(p.mean()),
                t=float(pct.mean()/pct.std()*np.sqrt(len(p))) if len(p) > 2 else np.nan)

base = stat(t)
print(f"=== BASELINE (no filter): n={base['n']} PF={base['pf']:.3f} "
      f"win={base['win']*100:.1f}% exp=${base['exp']:+.2f} t={base['t']:+.2f}\n")

print("=== A. HEAD TO HEAD, at matched quantile cut-offs ===")
print("(same absolute threshold would not be fair - the two series have different distributions)")
print(f"{'keep lowest':>13}{'':>3}{'CNY n':>7}{'CNY PF':>9}{'CNY exp':>9}{'CNY t':>7}"
      f"{'':>4}{'AUD n':>7}{'AUD PF':>9}{'AUD exp':>9}{'AUD t':>7}")
rows = []
for q in (0.2, 0.3, 0.4, 0.5, 0.6, 0.8):
    r = {"q": q}
    line = f"{q*100:>11.0f}%{'':>3}"
    for k, lbl in (("c_cny", "CNY"), ("c_aud", "AUD")):
        thr = t[k].quantile(q)
        s = stat(t[t[k] <= thr])
        r[lbl] = s
        line += f"{s['n']:>7}{s['pf']:>9.3f}{s['exp']:>9.2f}{s['t']:>7.2f}{'':>4}"
    rows.append(r)
    print(line)

print("\n=== B. AT THE ABSOLUTE 0.5 CUT USED FOR AUD ===")
for k, lbl in (("c_cny", "CNY"), ("c_aud", "AUD")):
    s, e = stat(t[t[k] <= .5]), stat(t[t[k] > .5])
    print(f"  {lbl}: kept n={s['n']} PF={s['pf']:.3f} exp=${s['exp']:+.2f} t={s['t']:+.2f}"
          f"   |  excluded n={e['n']} PF={e['pf']:.3f} exp=${e['exp']:+.2f}")

print("\n=== C. DOES CNY ADD ANYTHING ON TOP OF AUD? ===")
lo_a = t.c_aud <= .5
q = t.c_cny.quantile(.6)
lo_c = t.c_cny <= q
for lbl, m in (("AUD low only", lo_a), ("CNY low only", lo_c),
               ("BOTH low", lo_a & lo_c), ("AUD low, CNY high", lo_a & ~lo_c),
               ("AUD high, CNY low", ~lo_a & lo_c), ("BOTH high", ~lo_a & ~lo_c)):
    s = stat(t[m])
    if s["n"] >= 40:
        print(f"  {lbl:20s} n={s['n']:>4} PF={s['pf']:.3f} win={s['win']*100:>4.1f}% "
              f"exp=${s['exp']:+.2f} t={s['t']:+.2f}")

print("\n=== D. WITHIN the AUD-filtered set, does CNY still discriminate? ===")
sub = t[lo_a]
for lbl, m in (("CNY low", sub.c_cny <= q), ("CNY high", sub.c_cny > q)):
    s = stat(sub[m])
    print(f"  {lbl:10s} n={s['n']:>4} PF={s['pf']:.3f} exp=${s['exp']:+.2f} t={s['t']:+.2f}")
a, b = sub[sub.c_cny <= q].pnl_oz, sub[sub.c_cny > q].pnl_oz
tt = st.ttest_ind(a/sub[sub.c_cny <= q].entry, b/sub[sub.c_cny > q].entry, equal_var=False)
print(f"  difference: t={tt.statistic:+.2f}, p={tt.pvalue:.3f}")

print("\n=== E. CONTINUOUS: which reference predicts the trade return? ===")
pct = t.pnl_oz / t.entry * 100
for k, lbl in (("c_cny", "CNY"), ("c_aud", "AUD")):
    r = st.spearmanr(t[k], pct); ols = st.linregress(t[k], pct)
    print(f"  {lbl}: Spearman rho={r.statistic:+.3f} (p={r.pvalue:.4f})  "
          f"slope={ols.slope*100:+.1f}bp per +1.0 corr (p={ols.pvalue:.4f})")
X = np.column_stack([t.c_aud, t.c_cny, np.ones(len(t))])
beta, *_ = np.linalg.lstsq(X, pct.values, rcond=None)
resid = pct.values - X @ beta
se = np.sqrt(np.sum(resid**2)/(len(t)-3) * np.diag(np.linalg.inv(X.T @ X)))
print(f"  joint regression: AUD coef {beta[0]*100:+.1f}bp (t={beta[0]/se[0]:+.2f}), "
      f"CNY coef {beta[1]*100:+.1f}bp (t={beta[1]/se[1]:+.2f})")

json.dump({"base": base, "quantiles": rows,
           "abs05": {lbl: {"keep": stat(t[t[k] <= .5]), "drop": stat(t[t[k] > .5])}
                     for k, lbl in (("c_cny", "CNY"), ("c_aud", "AUD"))},
           "joint": {"aud_coef": float(beta[0]*100), "aud_t": float(beta[0]/se[0]),
                     "cny_coef": float(beta[1]*100), "cny_t": float(beta[1]/se[1])}},
          open("results/cny.json", "w"), indent=1)
