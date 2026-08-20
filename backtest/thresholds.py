"""How sensitive is the filter to the correlation cut-off and the window length?"""
import pandas as pd, numpy as np, engine, trades, warnings, json
warnings.filterwarnings("ignore")

gold = engine.load_bars()
t0 = pd.read_pickle("results/trades_60_ny.pkl")
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
def stat(x):
    p = x.pnl_oz; pct = p / x.entry * 100
    return (len(x), pf(p), float((p > 0).mean()), float(p.mean()),
            float(pct.mean() / pct.std() * np.sqrt(len(p))) if len(p) > 2 else np.nan)

print("=== A. CORRELATION CUT-OFF (20-day window, 60m range, NY close) ===")
print(f"{'cut-off':>10}{'kept':>7}{'PF':>8}{'win%':>7}{'exp$':>8}{'t':>7}   |"
      f"{'excluded':>9}{'PF':>8}{'exp$':>8}")
rows = []
base = stat(t0)
for th in np.round(np.arange(-0.4, 1.0, 0.1), 2):
    a, b = t0[t0["corr"] <= th], t0[t0["corr"] > th]
    if len(a) < 40:
        continue
    na, pa, wa, ea, ta = stat(a)
    line = f"{th:>10.1f}{na:>7}{pa:>8.3f}{wa*100:>7.1f}{ea:>8.2f}{ta:>7.2f}   |"
    if len(b) >= 40:
        nb, pb, wb, eb, tb = stat(b)
        line += f"{nb:>9}{pb:>8.3f}{eb:>8.2f}"
    else:
        line += f"{len(b):>9}{'-':>8}{'-':>8}"
    print(line)
    rows.append({"th": float(th), "n": na, "pf": pa, "win": wa, "exp": ea, "t": ta,
                 "n_ex": len(b), "pf_ex": pf(b.pnl_oz) if len(b) >= 40 else None})
print(f"{'no filter':>10}{base[0]:>7}{base[1]:>8.3f}{base[2]*100:>7.1f}{base[3]:>8.2f}{base[4]:>7.2f}")

print("\n=== B. WINDOW LENGTH x CUT-OFF (profit factor; n in brackets) ===")
wins = [10, 20, 30, 40, 60, 90]
ths = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8]
tab = {}
print(f"{'window':>8}" + "".join(f"{'<=%.1f' % th:>16}" for th in ths))
for w in wins:
    c = trades.corr_series(gold, w)
    x = t0.copy(); x["corr"] = pd.to_datetime(x.day).map(c); x = x.dropna(subset=["corr"])
    line = f"{w:>6}d "
    for th in ths:
        s = x[x["corr"] <= th]
        if len(s) >= 40:
            line += f"{pf(s.pnl_oz):>9.3f} ({len(s):>3})"
            tab[f"{w}_{th}"] = {"pf": pf(s.pnl_oz), "n": len(s), "exp": float(s.pnl_oz.mean())}
        else:
            line += f"{'-':>16}"
    print(line)

print("\n=== C. Fraction of days each cut-off keeps ===")
for th in (0.0, 0.2, 0.4, 0.5, 0.6, 0.8):
    print(f"  corr20 <= {th:>4.1f}: keeps {(t0['corr'] <= th).mean()*100:5.1f}% of days "
          f"({int((t0['corr'] <= th).sum())} of {len(t0)})")

json.dump({"cutoff": rows, "window_grid": tab,
           "base": {"n": base[0], "pf": base[1], "win": base[2], "exp": base[3], "t": base[4]}},
          open("results/thresholds.json", "w"), indent=1)
