"""Round-2 results -> results/summary2.json"""
import pandas as pd, numpy as np, engine, sweep, audusd, json, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo
from scipy import stats as st

gold = engine.load_bars()
gd = gold.close.resample("1D").last().dropna(); gd.index = gd.index.tz_localize(None).normalize()
ad = audusd.daily_from_fred(); ad.index = pd.to_datetime(ad.index).normalize()
dj = pd.concat([np.log(gd).diff().rename("g"), np.log(ad).diff().rename("a")],
               axis=1, join="inner").dropna()
CORR = dj.g.rolling(20).corr(dj.a).reindex(
    pd.date_range(dj.index.min(), dj.index.max(), freq="D")).ffill().shift(1)
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
O = {}

def simple(L, tz, h, m, cost=0.30):
    bL = engine.resample(gold, L); out = []
    for day, _ in gold.groupby(gold.index.date):
        t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30, tz=ZoneInfo("Asia/Hong_Kong")).tz_convert("UTC")
        if t0 not in bL.index: continue
        hi, lo = float(bL.at[t0, "high"]), float(bL.at[t0, "low"])
        te = pd.Timestamp(day.year, day.month, day.day, h, m, tz=ZoneInfo(tz)).tz_convert("UTC")
        fwd = bL.loc[t0 + pd.Timedelta(minutes=L):te]
        sig = fwd[(fwd.close > hi) | (fwd.close < lo)]
        if not len(sig): continue
        side = 1 if sig.iloc[0].close > hi else -1
        e = float(sig.iloc[0].close); px = engine.price_at(gold, te)
        if px is None: continue
        out.append({"day": day, "t": sig.index[0], "side": side, "entry": e,
                    "pnl": side * (px - e) - cost})
    d = pd.DataFrame(out)
    d["corr20"] = pd.to_datetime(d.day).map(CORR)
    return d.dropna(subset=["corr20"])

# --- sweep strategy grid ------------------------------------------------------
LIQ = {"dyn_swing": True, "breakout_low": True, "session_extreme": False, "range_opp": False}
grid = []
for L in (5, 15, 30, 60):
    for liq, hold in LIQ.items():
        d = sweep.run(gold, L, liq, 3, require_hold_range=hold)
        s = sweep.stats(d, "pnl_london_mid"); c = sweep.stats(d, "ctl_london_mid", "breakout_px")
        if s:
            grid.append({"range": L, "liq": liq, "n": s["n"],
                         "fill_rate": float(d.traded.sum()/max((d.bias!=0).sum(),1)),
                         "win": s["win"], "pf": s["pf"], "exp": s["exp"], "t": s["t"],
                         "breakout_pf": c["pf"]})
O["sweep_grid"] = grid

d30 = sweep.run(gold, 30, "dyn_swing", 3)
O["sweep_exits"] = [{"exit": a, **{k: float(v) for k, v in sweep.stats(d30, f"pnl_{a}").items()}}
                    for a in sweep.ANCHOR_ORDER if sweep.stats(d30, f"pnl_{a}")]
plain = engine.backtest(gold, 30, "london_mid"); plain = plain[plain.traded].set_index("day")
bd = d30[d30.bias != 0]
sel = {}
for lbl, sub in (("swept", bd[bd.traded]), ("never_swept", bd[~bd.traded])):
    idx = [x for x in sub.day if x in plain.index]; p = plain.loc[idx]
    sel[lbl] = {"n": len(p), "pf": pf(p.pnl_usd), "exp": float(p.pnl_usd.mean())}
O["selection"] = sel

# --- AUD relationship ---------------------------------------------------------
aud = audusd.build()
g15 = np.log(gold.close.resample("15min").last()).diff(); a15 = np.log(aud.close).diff()
j = pd.concat([g15.rename("g"), a15.rename("a")], axis=1, join="inner").dropna()
j = j[(j.g != 0) & (j.a != 0)]; j["h"] = j.index.hour
byh = j.groupby("h").apply(lambda x: x.g.corr(x.a))
roll20 = dj.g.rolling(20).corr(dj.a)
O["aud_rel"] = {"n15": int(len(j)), "corr15": float(j.g.corr(j.a)),
                "asia": float(byh.loc[[1,2,3,4,5]].mean()), "london": float(byh.loc[[8,9,10,11]].mean()),
                "ny": float(byh.loc[[13,14,15,16]].mean()),
                "daily_corr": float(dj[dj.index >= "2020-08-21"].g.corr(dj[dj.index >= "2020-08-21"].a)),
                "roll_med": float(roll20.median()), "roll_p05": float(roll20.quantile(.05)),
                "roll_p95": float(roll20.quantile(.95)),
                "intraday_span": [str(aud.index.min().date()), str(aud.index.max().date())]}

# --- the filter ---------------------------------------------------------------
ind = simple(60, "America/New_York", 16, 0)
O["filter_head"] = {}
for lbl, m in (("all", ind.corr20 == ind.corr20), ("lo", ind.corr20 <= .5), ("hi", ind.corr20 > .5)):
    s = ind[m]; p = s.pnl / s.entry * 100
    O["filter_head"][lbl] = {"n": len(s), "pf": pf(s.pnl), "win": float((s.pnl > 0).mean()),
                             "exp": float(s.pnl.mean()), "total": float(s.pnl.sum()),
                             "t": float(p.mean()/p.std()*np.sqrt(len(p)))}
O["threshold"] = [{"th": th, "n": int((ind.corr20 <= th).sum()),
                   "pf": pf(ind[ind.corr20 <= th].pnl),
                   "exp": float(ind[ind.corr20 <= th].pnl.mean())}
                  for th in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1)]
gen = []
for L in (5, 15, 30):
    for name, (tz, h, m) in (("london_open", ("Europe/London", 8, 0)),
                             ("london_mid", ("Europe/London", 12, 0)),
                             ("london_close", ("Europe/London", 16, 30)),
                             ("ny_close", ("America/New_York", 16, 0))):
        t = simple(L, tz, h, m); f = t[t.corr20 <= .5]
        gen.append({"range": L, "exit": name, "n": len(t), "pf_all": pf(t.pnl),
                    "n_f": len(f), "pf_f": pf(f.pnl)})
O["generalise"] = gen
f = ind[ind.corr20 <= .5].copy(); f["yr"] = pd.to_datetime(f.day).dt.year
O["filter_years"] = [{"yr": int(y), "n": len(x), "win": float((x.pnl > 0).mean()),
                      "pf": pf(x.pnl), "total": float(x.pnl.sum())} for y, x in f.groupby("yr")]
O["filter_cost"] = [{"c": c, "pf": pf(f.pnl + .30 - c), "exp": float((f.pnl + .30 - c).mean())}
                    for c in (0.0, 0.30, 0.50, 0.75, 1.00, 1.50)]
ind["os"] = pd.to_datetime(ind.day) >= "2024-01-01"
O["filter_isos"] = {}
for nm, mm in (("IS", ~ind.os), ("OS", ind.os)):
    x = ind[mm]
    O["filter_isos"][nm] = {"lo_n": int((x.corr20 <= .5).sum()), "lo_pf": pf(x[x.corr20 <= .5].pnl),
                            "lo_exp": float(x[x.corr20 <= .5].pnl.mean()),
                            "hi_n": int((x.corr20 > .5).sum()), "hi_pf": pf(x[x.corr20 > .5].pnl),
                            "hi_exp": float(x[x.corr20 > .5].pnl.mean())}
pct = ind.pnl / ind.entry * 100
O["continuous"] = {"rho": float(st.spearmanr(ind.corr20, pct).statistic),
                   "p": float(st.spearmanr(ind.corr20, pct).pvalue),
                   "slope_bp": float(st.linregress(ind.corr20, pct).slope * 100),
                   "slope_p": float(st.linregress(ind.corr20, pct).pvalue)}

# --- same-day AUD agreement (the thing that does NOT work) --------------------
def aud_move(day, t):
    t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30, tz=ZoneInfo("Asia/Hong_Kong")).tz_convert("UTC")
    w = aud.loc[t0:t]
    return float(np.log(w.close.iloc[-1] / w.open.iloc[0])) if len(w) > 1 else np.nan
sub = ind[(pd.to_datetime(ind.day) >= aud.index.min().tz_localize(None)) &
          (pd.to_datetime(ind.day) <= aud.index.max().tz_localize(None))].copy()
sub["am"] = [aud_move(r.day, r.t) for r in sub.itertuples()]
sub = sub.dropna(subset=["am"]); sub["agree"] = np.sign(sub.am) == sub.side
tt = st.ttest_ind(sub[sub.agree].pnl, sub[~sub.agree].pnl, equal_var=False)
O["sameday"] = {"n": len(sub),
                "agree": {"n": int(sub.agree.sum()), "pf": pf(sub[sub.agree].pnl),
                          "exp": float(sub[sub.agree].pnl.mean())},
                "diverge": {"n": int((~sub.agree).sum()), "pf": pf(sub[~sub.agree].pnl),
                            "exp": float(sub[~sub.agree].pnl.mean())},
                "t": float(tt.statistic), "p": float(tt.pvalue)}

# --- equity curves ------------------------------------------------------------
def curve(x):
    x = x.sort_values("t"); eq = (x.pnl / x.entry * 100).cumsum()
    i = np.linspace(0, len(eq) - 1, min(len(eq), 240)).astype(int)
    return {"x": [str(pd.Timestamp(x.t.iloc[k]).date()) for k in i],
            "y": [round(float(eq.iloc[k]), 2) for k in i]}
O["curves"] = {"all": curve(ind), "filtered": curve(ind[ind.corr20 <= .5]),
               "excluded": curve(ind[ind.corr20 > .5])}
O["placebo_p"] = 0.0002
json.dump(O, open("results/summary2.json", "w"), indent=1)
print("ok", len(json.dumps(O)), "bytes")
print("headline:", json.dumps(O["filter_head"], indent=1))
print("same-day AUD agreement:", json.dumps(O["sameday"], indent=1))
