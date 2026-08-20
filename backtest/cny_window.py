import pandas as pd, numpy as np, engine, cny, warnings, json
warnings.filterwarnings("ignore")
gold = engine.load_bars()
t0 = pd.read_pickle("results/trades_60_ny.pkl").drop(columns=["corr"])
pf = lambda s: float(s[s > 0].sum()/max(-s[s <= 0].sum(), 1e-9))
def stat(x):
    p = x.pnl_oz; pct = p/x.entry*100
    return len(x), pf(p), float(p.mean()), float(pct.mean()/pct.std()*np.sqrt(len(p)))

print("=== Window sweep: does a longer window rescue CNY? (profit factor / t-stat) ===")
print(f"{'window':>8}" + "".join(f"{'keep '+str(int(q*100))+'%':>18}" for q in (0.2, 0.4, 0.6)))
best = None
for w in (10, 20, 40, 60, 90, 120):
    C, _ = cny.build_corr(gold, w)
    d = pd.to_datetime(t0.day).dt.normalize()
    x = t0.copy(); x["c"] = d.map(C.cny); x["a"] = d.map(C.aud)
    x = x.dropna(subset=["c"])
    line = f"{w:>6}d "
    for q in (0.2, 0.4, 0.6):
        n, p, e, tt = stat(x[x.c <= x.c.quantile(q)])
        line += f"{p:>10.3f} (t{tt:+.2f})"
        if best is None or tt > best[0]: best = (tt, w, q, p, n)
    print(line)
print(f"  best CNY cell anywhere: window {best[1]}d, keep {best[2]*100:.0f}%, "
      f"PF {best[3]:.3f}, t {best[0]:+.2f}, n {best[4]}")
print("  (AUD at 20d / keep 50% gives PF 1.337, t +2.76 - and that was not the best-of-grid pick)")

print("\n=== In-sample / out-of-sample for CNY at its own best cut ===")
C, _ = cny.build_corr(gold, best[1])
d = pd.to_datetime(t0.day).dt.normalize()
x = t0.copy(); x["c"] = d.map(C.cny); x = x.dropna(subset=["c"])
x["os"] = pd.to_datetime(x.day) >= "2024-01-01"
thr = x.c.quantile(best[2])
for nm, m in (("IS 2020-23", ~x.os), ("OS 2024-25", x.os)):
    s = x[m]
    k = stat(s[s.c <= thr]); r = stat(s[s.c > thr])
    print(f"  {nm}: kept n={k[0]:>3} PF={k[1]:.3f} exp=${k[2]:+.2f}  |  "
          f"excluded n={r[0]:>3} PF={r[1]:.3f} exp=${r[2]:+.2f}")
