"""The exact configuration an MT5 EA would run, scored honestly."""
import pandas as pd, numpy as np, engine, trades, audusd, portfolio as P, warnings, json
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

gold = engine.load_bars()
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

# correlation exactly as MT5 would compute it: broker (EET) daily bars, lagged one day
loc = gold.close.tz_convert(ZoneInfo("Europe/Athens"))
gd = loc.resample("1D").last()
gd = pd.Series(gd.values, index=pd.to_datetime([x.date() for x in gd.index])).dropna()
ad = audusd.daily_from_fred(); ad.index = pd.to_datetime(ad.index).normalize()
j = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
              axis=1, join="inner").dropna()
C = (j.g.rolling(20).corr(j.a)
     .reindex(pd.date_range(j.index.min(), j.index.max(), freq="D")).ffill().shift(1))

out = {}
for stop_r, label in ((2.0, "2R stop"), (None, "no stop")):
    t = trades.generate(gold, 60, stop_r=stop_r)
    t["c"] = pd.to_datetime(t.day).dt.normalize().map(C)
    t = t.dropna(subset=["c"])
    f = t[t.c <= 0.5].reset_index(drop=True)
    f["pnl_oz"] = f.pnl_oz - np.where(f.reason == "stop", 0.30, 0.0)     # stop slippage
    pct = f.pnl_oz / f.entry * 100
    yrs = (pd.Timestamp(f.day.iloc[-1]) - pd.Timestamp(f.day.iloc[0])).days / 365.25
    d = dict(n=len(f), per_year=len(f)/yrs, win=float((f.pnl_oz > 0).mean()), pf=pf(f.pnl_oz),
             exp=float(f.pnl_oz.mean()), t=float(pct.mean()/pct.std()*np.sqrt(len(f))),
             hold_h=float((f.t_out - f.t_fill).dt.total_seconds().mean()/3600),
             stopped=float((f.reason == "stop").mean()) if stop_r else 0.0)
    f["os"] = pd.to_datetime(f.day) >= "2024-01-01"
    for nm, mm in (("is", ~f.os), ("os", f.os)):
        x = f[mm]; px = x.pnl_oz / x.entry * 100
        d[nm] = dict(n=len(x), pf=pf(x.pnl_oz), win=float((x.pnl_oz > 0).mean()),
                     exp=float(x.pnl_oz.mean()),
                     t=float(px.mean()/px.std()*np.sqrt(len(x))))
    out[label] = d
    if stop_r:
        f.to_pickle("results/trades_deployable.pkl")

print("=== THE DEPLOYABLE CONFIGURATION (filter from broker EET bars, lagged 1 day) ===")
for label, d in out.items():
    print(f"\n  -- {label} --")
    print(f"     {d['n']} trades over 5 years ({d['per_year']:.0f}/year), "
          f"avg hold {d['hold_h']:.1f} h" + (f", stopped {d['stopped']*100:.0f}%" if d['stopped'] else ""))
    print(f"     win {d['win']*100:.1f}%   PF {d['pf']:.3f}   ${d['exp']:+.2f}/oz   t {d['t']:+.2f}")
    print(f"     in-sample  2020-23: n={d['is']['n']:>3} PF {d['is']['pf']:.3f} "
          f"win {d['is']['win']*100:.1f}% ${d['is']['exp']:+.2f}/oz  t {d['is']['t']:+.2f}")
    print(f"     out-of-sample 24-25: n={d['os']['n']:>3} PF {d['os']['pf']:.3f} "
          f"win {d['os']['win']*100:.1f}% ${d['os']['exp']:+.2f}/oz  t {d['os']['t']:+.2f}")

print("\n=== ACCOUNT SIMULATION ON THE DEPLOYABLE TRADE SET ===")
f = pd.read_pickle("results/trades_deployable.pkl")
sims = {}
for acct in (2000, 10000):
    for risk in (0.01, 0.02):
        r = P.simulate(f, "risk", risk, 20.0, start=acct)
        r.pop("curve")
        sims[f"{acct}_{risk}"] = r
        print(f"  ${acct:>6,} at {risk*100:.0f}% risk: final ${r['final']:>9,.0f}  "
              f"CAGR {r['cagr']*100:>6.1f}%  maxDD {r['max_dd']*100:>5.1f}%  "
              f"worst trade {r['worst_trade']*100:>5.1f}%")

print("\n=== THE HONEST FORWARD EXPECTATION ===")
d = out["2R stop"]
print(f"  If the future looks like 2020-23 (the weaker half): PF {d['is']['pf']:.2f}, "
      f"${d['is']['exp']:+.2f}/oz")
print(f"  If it looks like 2024-25 (the stronger half):       PF {d['os']['pf']:.2f}, "
      f"${d['os']['exp']:+.2f}/oz")
r_is = P.simulate(f[pd.to_datetime(f.day) < "2024-01-01"].reset_index(drop=True),
                  "risk", 0.01, 20.0, start=2000)
print(f"  A $2,000 account run only through 2020-23 at 1% risk: "
      f"${r_is['final']:,.0f} ({r_is['cagr']*100:+.1f}%/yr, {r_is['max_dd']*100:.0f}% DD)")
out["sims"] = sims
out["is_only_2000"] = {k: v for k, v in r_is.items() if k != "curve"}
json.dump(out, open("results/deployable.json", "w"), indent=1, default=str)
