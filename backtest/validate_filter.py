"""Independent re-implementation + generalisation checks for the AUD-correlation filter."""
import pandas as pd, numpy as np, engine, sweep, audusd, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

gold = engine.load_bars()
gd = gold.close.resample("1D").last().dropna(); gd.index = gd.index.tz_localize(None).normalize()
ad = audusd.daily_from_fred(); ad.index = pd.to_datetime(ad.index).normalize()
dj = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
               axis=1, join="inner").dropna()
CORR = dj.g.rolling(20).corr(dj.a).reindex(
    pd.date_range(dj.index.min(), dj.index.max(), freq="D")).ffill().shift(1)

# ---------- independent implementation, written from scratch -------------------
def simple(bars5, L, exit_tz, exit_h, exit_m, cost=0.30):
    bL = engine.resample(bars5, L)
    out = []
    for day, grp in bars5.groupby(bars5.index.date):
        t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30,
                          tz=ZoneInfo("Asia/Hong_Kong")).tz_convert("UTC")
        if t0 not in bL.index:
            continue
        hi, lo = float(bL.at[t0, "high"]), float(bL.at[t0, "low"])
        te = pd.Timestamp(day.year, day.month, day.day, exit_h, exit_m,
                          tz=ZoneInfo(exit_tz)).tz_convert("UTC")
        fwd = bL.loc[t0 + pd.Timedelta(minutes=L):te]
        sig = fwd[(fwd.close > hi) | (fwd.close < lo)]
        if not len(sig):
            continue
        t_b = sig.index[0]
        side = 1 if sig.iloc[0].close > hi else -1
        entry = float(sig.iloc[0].close)
        px = engine.price_at(bars5, te)
        if px is None:
            continue
        out.append({"day": day, "side": side, "entry": entry,
                    "pnl": side * (px - entry) - cost})
    return pd.DataFrame(out)

pf = lambda s: s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9)
print("=== 1. Independent re-implementation (60m range, NY close) ===")
ind = simple(gold, 60, "America/New_York", 16, 0)
ind["corr20"] = pd.to_datetime(ind.day).map(CORR)
ind = ind.dropna(subset=["corr20"])
for label, m in (("all trades", ind.index == ind.index),
                 ("corr20 <= 0.5", ind.corr20 <= .5), ("corr20 > 0.5", ind.corr20 > .5)):
    s = ind[m]
    pct = s.pnl / s.entry * 100
    print(f"  {label:15s} n={len(s):4d} PF={pf(s.pnl):.3f} win={100*(s.pnl>0).mean():.1f}% "
          f"exp=${s.pnl.mean():+.2f} t={pct.mean()/pct.std()*np.sqrt(len(pct)):+.2f}")

print("\n=== 2. Does the filter lift the ORIGINAL 12 configurations too? ===")
print(f"{'range':>7}{'exit':>14}{'n all':>7}{'PF all':>8}{'n filt':>8}{'PF filt':>9}{'lift':>7}")
lifts = []
for L in (5, 15, 30):
    for name, (tz, h, m) in (("london_open", ("Europe/London", 8, 0)),
                             ("london_mid", ("Europe/London", 12, 0)),
                             ("london_close", ("Europe/London", 16, 30)),
                             ("ny_close", ("America/New_York", 16, 0))):
        t = simple(gold, L, tz, h, m)
        t["corr20"] = pd.to_datetime(t.day).map(CORR)
        t = t.dropna(subset=["corr20"])
        f = t[t.corr20 <= .5]
        lift = pf(f.pnl) - pf(t.pnl)
        lifts.append(lift)
        print(f"{L:>6}m{name:>14}{len(t):>7}{pf(t.pnl):>8.3f}{len(f):>8}{pf(f.pnl):>9.3f}{lift:>+7.3f}")
print(f"  filter improved {sum(1 for x in lifts if x > 0)} of {len(lifts)} configurations")

print("\n=== 3. Per-year, filtered rule (60m -> NY close, corr20 <= 0.5) ===")
f = ind[ind.corr20 <= .5].copy()
f["yr"] = pd.to_datetime(f.day).dt.year
print(f.groupby("yr").apply(lambda x: pd.Series({
    "n": len(x), "win%": round(100*(x.pnl > 0).mean(), 1), "PF": round(pf(x.pnl), 2),
    "total_$": round(x.pnl.sum(), 0)})).to_string())

print("\n=== 4. Cost sensitivity ===")
for c in (0.0, 0.30, 0.50, 0.75, 1.00, 1.50):
    p = f.pnl + 0.30 - c
    print(f"  round-trip ${c:.2f}: PF={pf(p):.3f} exp=${p.mean():+.2f} total=${p.sum():+.0f}")

print("\n=== 5. Threshold sensitivity (is 0.5 a cherry-picked cut?) ===")
for th in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    s = ind[ind.corr20 <= th]
    if len(s) > 100:
        print(f"  corr20 <= {th:.1f}: n={len(s):4d} PF={pf(s.pnl):.3f} exp=${s.pnl.mean():+.2f}")

print("\n=== 6. Randomisation null on the filtered rule ===")
rng = np.random.default_rng(3)
gross = (f.pnl.values + 0.30)
ent = f.entry.values
real = ((f.side.values * 0 + 1) * gross - 0.30).sum()   # observed (sides already applied)
real = f.pnl.sum()
N, beats = 5000, 0
mag = np.abs(gross)
for _ in range(N):
    sgn = rng.choice([-1, 1], size=len(mag))
    if (sgn * mag - 0.30).sum() >= real:
        beats += 1
print(f"  observed total ${real:+.0f}; random directions beat it in {beats/N*100:.2f}% of draws -> p={beats/N:.4f}")
