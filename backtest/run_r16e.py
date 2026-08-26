"""Round 16 second sweep: batteries E (IBS on Asia indices), G (Turtle Soup
daily, 5 markets), H (Gotobi USDJPY). F (Nikkei open-fade) runs separately
once the 1m download lands. Specs in reference/goal_ledger.md.
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
def met(f, col="ret"):
    if len(f) < 15:
        return dict(n=len(f), pf=np.nan, t=np.nan, win=np.nan)
    p = f[col] * 100
    return dict(n=len(f), pf=pfv(f[col]), win=float((f[col] > 0).mean()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))), exp_bps=float(p.mean() * 100))

def load_h1(path, tcol="datetime"):
    df = pd.read_csv(f"data/{path}")
    df["ts"] = pd.to_datetime(df[tcol], utc=True)
    return df.set_index("ts")[["open", "high", "low", "close"]].sort_index()

def daily_from_h1(df, h_start, h_end):
    """Day-session daily bars from 1h data, UTC hour window."""
    s = df[(df.index.hour >= h_start) & (df.index.hour < h_end)]
    D = s.groupby(s.index.date).agg(o=("open", "first"), h=("high", "max"),
                                    l=("low", "min"), c=("close", "last"))
    D.index = pd.to_datetime(D.index)
    return D

out = {"ledger": 0}

# ---------------------------------------------------------------- E: IBS Asia
print("=== E: IBS daily mean reversion on Asia indices ===")
frames = {}
frames["HSI"] = (daily_from_h1(load_h1("HK33_H1.csv"), 1, 9), 10.0)
frames["JP225"] = (daily_from_h1(load_h1("JP225_H1.csv"), 0, 7), 15.0)
frames["AUS200"] = (daily_from_h1(load_h1("AUS200_H1.csv"), 0, 7), 4.0)

def ibs_trades(D, cost_pts, shift=0):
    D = D.copy()
    D["ma200"] = D.c.rolling(200).mean()
    D["ibs"] = (D.c - D.l) / (D.h - D.l + 1e-12)
    sig = ((D.ibs < 0.2) & (D.c > D.ma200)).values
    if shift:
        sig = np.roll(sig, shift)
    ex = (D.ibs > 0.8).values
    cf = cost_pts / D.c.mean()
    cv = D.c.values
    rets, dl = [], []
    inpos = False; ent = None
    for i in range(1, len(D)):
        if not inpos and sig[i - 1]:
            inpos = True; ent = i - 1
        elif inpos and (ex[i - 1] or (i - 1 - ent) >= 10):
            rets.append(cv[i - 1] / cv[ent] - 1 - 2 * cf)
            dl.append(D.index[i - 1]); inpos = False
    return pd.DataFrame(dict(ret=rets, d=dl))

rng_ = np.random.default_rng(163)
out["E"] = {}
for name, (D, cost) in frames.items():
    f = ibs_trades(D, cost)
    mid = D.index[len(D) // 2]
    m = met(f); m["h1"] = met(f[f.d < mid]); m["h2"] = met(f[f.d >= mid])
    obs = m["t"]
    perm = []
    for _ in range(150):
        fp = ibs_trades(D, cost, shift=int(rng_.integers(30, len(D) - 30)))
        mp = met(fp)
        if np.isfinite(mp["t"]):
            perm.append(mp["t"])
    m["maxstat_p"] = float((np.array(perm) >= obs).mean()) if perm else np.nan
    m["perm_p50"] = float(np.median(perm)) if perm else np.nan
    out["E"][name] = m; out["ledger"] += 1
    print(f"  {name:>6}: n={m['n']:>3} win {m['win']*100:.0f}% PF {m['pf']:.2f} t {m['t']:+5.2f} "
          f"(h1 {m['h1']['t']:+5.2f} / h2 {m['h2']['t']:+5.2f})  drift-null p={m['maxstat_p']:.3f} "
          f"(perm med {m['perm_p50']:+.2f})")

# ---------------------------------------------------------------- G: Turtle Soup
print("\n=== G: Turtle Soup daily (20d-extreme undercut + reclaim, exit +5d) ===")
import engine
loc = engine.load_bars()
loc2 = loc.close.tz_convert(ZoneInfo("Europe/Athens"))
gold_d = pd.DataFrame(dict(
    o=loc.open.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").first(),
    h=loc.high.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").max(),
    l=loc.low.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").min(),
    c=loc2.resample("1D").last())).dropna()
gold_d.index = pd.to_datetime([x.date() for x in gold_d.index])

import index_data
NY = ZoneInfo("America/New_York")
def rth_daily(name):
    g = index_data.load(name); g = g[~g.index.duplicated()]
    et = g.index.tz_convert(NY)
    r = g[(et.hour * 60 + et.minute >= 570) & (et.hour < 16)]
    et2 = r.index.tz_convert(NY)
    D = r.groupby(et2.date).agg(o=("open", "first"), h=("high", "max"),
                                l=("low", "min"), c=("close", "last"))
    D.index = pd.to_datetime(D.index)
    return D

ts_frames = {"GOLD": (gold_d, 0.30), "SPX": (rth_daily("SPX"), 0.6),
             "NDX": (rth_daily("NDX"), 2.0), "HSI": (frames["HSI"][0], 10.0),
             "JP225": (frames["JP225"][0], 15.0)}
out["G"] = {}
for name, (D, cost) in ts_frames.items():
    cf = cost / D.c.mean()
    res = {}
    for side, sgn in (("long", 1), ("short", -1)):
        rets, dl = [], []
        hv, lv, cv = D.h.values, D.l.values, D.c.values
        for i in range(25, len(D) - 5):
            if sgn > 0:
                prior = lv[i - 20:i].min()
                arg = i - 20 + lv[i - 20:i].argmin()
                trig = lv[i] < prior and (i - arg) >= 4 and cv[i] > prior
            else:
                prior = hv[i - 20:i].max()
                arg = i - 20 + hv[i - 20:i].argmax()
                trig = hv[i] > prior and (i - arg) >= 4 and cv[i] < prior
            if trig:
                rets.append(sgn * (cv[i + 5] / cv[i] - 1) - 2 * cf)
                dl.append(D.index[i])
        f = pd.DataFrame(dict(ret=rets, d=dl))
        mid = D.index[len(D) // 2]
        m = met(f)
        m["h1"] = met(f[f.d < mid]) if len(f) else {}
        m["h2"] = met(f[f.d >= mid]) if len(f) else {}
        res[side] = m; out["ledger"] += 1
        if m["n"] >= 15:
            print(f"  {name:>5} {side:>5}: n={m['n']:>3} win {m['win']*100:.0f}% PF {m['pf']:.2f} "
                  f"t {m['t']:+5.2f} (h1 {m['h1'].get('t',np.nan):+5.2f} / h2 {m['h2'].get('t',np.nan):+5.2f})")
        else:
            print(f"  {name:>5} {side:>5}: n={m['n']} - too few")
    out["G"][name] = res

# ---------------------------------------------------------------- H: Gotobi
print("\n=== H: Gotobi USDJPY (06:00 JST -> ~10:00 JST) ===")
jpy = load_h1("USDJPY_H1.csv")
COST_PIPS = 0.015          # ~1.5 pips round trip in JPY terms
rows = []
for d, day in jpy.groupby(jpy.index.date):
    # morning window: 21:00 UTC previous calendar day .. 01:00 UTC this day is
    # awkward across the date groupby; instead anchor on the 21:00 UTC bar and
    # exit at the 00:00 UTC bar close of the NEXT calendar date.
    pass
# simpler: vectorized on bar timestamps
jpy["u_date"] = jpy.index.date
ent_bars = jpy[jpy.index.hour == 21]                      # 06:00 JST
ex_bars = jpy[jpy.index.hour == 0]                        # close of 00:00 bar ~ 10:00 JST
ex_map = {d: c for d, c in zip(ex_bars.u_date, ex_bars.close)}
for ts, r in ent_bars.iterrows():
    jst_date = (ts + pd.Timedelta(hours=9)).date()        # trading date in JST
    ex_date = (ts + pd.Timedelta(hours=4)).date()         # 01:00 UTC next day? 21:00+4h=01:00 UTC next
    x = ex_map.get((ts + pd.Timedelta(hours=3)).date())   # 00:00 UTC bar of next UTC day
    if x is None:
        continue
    ret = (x - r.open - COST_PIPS) / r.open
    dom = jst_date.day
    gotobi = dom in (5, 10, 15, 20, 25, 30)
    # weekend-shift variant: Friday whose sat/sun is gotobi
    wd = pd.Timestamp(jst_date).weekday()
    shifted = False
    if wd == 4:
        for k in (1, 2):
            nd = (pd.Timestamp(jst_date) + pd.Timedelta(days=k)).day
            if nd in (5, 10, 15, 20, 25, 30):
                shifted = True
    rows.append(dict(d=pd.Timestamp(jst_date), ret=ret, gotobi=gotobi, shifted=shifted))
J = pd.DataFrame(rows)
mid = pd.Timestamp("2021-06-01")
out["H"] = {}
for nm, mask in (("gotobi", J.gotobi), ("gotobi+shift", J.gotobi | J.shifted),
                 ("control", ~J.gotobi & ~J.shifted)):
    sub = J[mask]
    m = met(sub); m["h1"] = met(sub[sub.d < mid]); m["h2"] = met(sub[sub.d >= mid])
    out["H"][nm] = m; out["ledger"] += 1
    print(f"  {nm:>13}: n={m['n']:>4} win {m['win']*100:.0f}% t {m['t']:+5.2f} "
          f"avg {m['exp_bps']:+5.1f}bps (h1 {m['h1']['t']:+5.2f} / h2 {m['h2']['t']:+5.2f})")

json.dump(out, open("results/r16egh.json", "w"), indent=1, default=str)
print(f"\nledger +{out['ledger']} cells; written results/r16egh.json")
