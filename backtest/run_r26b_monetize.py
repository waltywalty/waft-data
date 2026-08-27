"""Round 26b: can the auction-candle signal be monetized? Pre-registered.
A: magnitude (|candle|/ATR14) quintile gradient. B: cost-structure sensitivity.
Plus the registered framing stat: the raw directional hit rate."""
import pandas as pd, numpy as np, json, warnings, engine
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")

gold = engine.load_bars()
d = gold.resample("1D").agg({"high": "max", "low": "min"}).dropna()
atr14 = (d.high - d.low).rolling(14).mean().shift(1)
atr14.index = atr14.index.tz_localize(None).normalize()

rows = []
for day, bars in gold.groupby(gold.index.date):
    dd = pd.Timestamp(day)
    ts = lambda h, m: pd.Timestamp(dd.year, dd.month, dd.day, h, m, tz="UTC")
    ny = pd.Timestamp(dd.year, dd.month, dd.day, 16, 0,
                      tz=ZoneInfo("America/New_York")).tz_convert("UTC")
    w = bars.loc[ts(2, 15):ts(2, 30) - pd.Timedelta(seconds=1)]
    if not len(w):
        continue
    a_o, a_c = float(w.open.iloc[0]), float(w.close.iloc[-1])
    i = bars.index.searchsorted(ny)
    if i <= 0:
        continue
    rows.append(dict(day=dd, mag=abs(a_c - a_o), sig=np.sign(a_c - a_o),
                     entry=a_c, p_ny=float(bars.close.iloc[i - 1])))
F = pd.DataFrame(rows).set_index("day")
F["atr"] = F.index.map(atr14)
F = F[(F.sig != 0) & F.atr.notna()]
F["rel"] = F.mag / F.atr
F["gross"] = F.sig * (F.p_ny - F.entry)
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

out = {}
# registered framing: raw directional hit rate
hit = float((F.gross > 0).mean())
out["hit_rate"] = dict(all=hit,
                       h1=float((F[F.index < "2024-01-01"].gross > 0).mean()),
                       h2=float((F[F.index >= "2024-01-01"].gross > 0).mean()))

# A: magnitude quintiles (gross, then net at spot costs)
F["q"] = pd.qcut(F.rel, 5, labels=False)
qg = {}
for q in range(5):
    x = F[F.q == q]
    net = x.gross - 0.60
    p = net / x.entry * 100
    qg[f"q{q}"] = dict(n=len(x), rel_med=float(x.rel.median()),
                       gross_exp=float(x.gross.mean()), net_exp=float(net.mean()),
                       net_pf=pf(net), t=float(p.mean() / p.std() * np.sqrt(len(p))),
                       hit=float((x.gross > 0).mean()))
out["A_magnitude"] = qg
# top-quintile halves (the registered subset check)
top = F[F.q == 4]
th = {}
for nm, m in (("h1", top.index < "2024-01-01"), ("h2", top.index >= "2024-01-01")):
    x = top[m]; net = x.gross - 0.60
    th[nm] = dict(n=len(x), net_exp=float(net.mean()), net_pf=pf(net))
out["A_top_halves"] = th

# B: cost structures on the full strategy and on the top quintile
B = {}
for nm, c in (("spot_0.60", 0.60), ("mgc_0.25", 0.25), ("zero", 0.0)):
    for sub, X in (("all", F), ("top_q", top)):
        net = X.gross - c
        p = net / X.entry * 100
        B[f"{nm}_{sub}"] = dict(n=len(X), exp=float(net.mean()), pf=pf(net),
                                t=float(p.mean() / p.std() * np.sqrt(len(p))))
out["B_costs"] = B

json.dump(out, open("results/r26b_monetize.json", "w"), indent=1, default=float)

print(f"=== FRAMING: raw directional hit rate = {hit*100:.1f}% "
      f"(h1 {out['hit_rate']['h1']*100:.1f}%, h2 {out['hit_rate']['h2']*100:.1f}%) ===\n")
print("=== A: |CANDLE|/ATR QUINTILES (net at spot $0.60) ===")
for q in range(5):
    v = qg[f"q{q}"]
    print(f"  q{q} (rel~{v['rel_med']:.3f}): n={v['n']:>3} hit {v['hit']*100:.1f}%  "
          f"gross ${v['gross_exp']:+.2f}  net ${v['net_exp']:+.2f}  PF {v['net_pf']:.3f}  t {v['t']:+.2f}")
print(f"  top-quintile halves: h1 ${th['h1']['net_exp']:+.2f} (PF {th['h1']['net_pf']:.3f}, n={th['h1']['n']})  "
      f"h2 ${th['h2']['net_exp']:+.2f} (PF {th['h2']['net_pf']:.3f}, n={th['h2']['n']})")
print("\n=== B: COST STRUCTURES ===")
for k, v in B.items():
    print(f"  {k:>16}: n={v['n']:>4} exp ${v['exp']:+.2f}  PF {v['pf']:.3f}  t {v['t']:+.2f}")
