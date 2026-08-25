"""Practitioner adaptations from the round-8 research, tested the house way.

Block A - onto the deployable Asia ORB (60m range, corr<=0.5, 2R stop, NY-close
exit, 08:00-London entry cutoff). These are refinement tests on an
already-selected strategy: everything here is exploratory, judged by sign
agreement between 2020-23 and 2024-25, and none of it re-sizes the headline.
  A1 Crabel NR7 conditioning          A2 Crabel inside-day conditioning
  A3 activity: range width / ATR14    A4 relative tick volume in the range
  A5 trigger delay (earliest-is-best) A6 prior-day-range interaction veto
  A7 Zarattini ATR-fraction stops     A8 Zarattini first-bar direction variant

Block B - onto the 2.6-sigma fade (15m, n=20, close_back), which is breakeven
gross: can any practitioner gate select a sub-population that pays more than
the spread?
  B1 ADX(14, 1h) trend gate           B2 band-walk veto (excursion length)
  B3 news-window scrub                B4 NY-anchored VWAP band fade
"""
import pandas as pd, numpy as np, warnings, json
import engine, trades, structure, meanrev
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
bars = engine.load_bars()
CORR = trades.corr_series(bars, 20)
SPLIT = pd.Timestamp("2024-01-01")
OUT = {"tests_run": 0}
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def seg(x, pnl="pnl_oz", entry="entry"):
    if len(x) < 15:
        return None
    p = x[pnl]
    pct = p / x[entry] * 100
    return dict(n=int(len(x)), pf=pfx(p), exp=float(p.mean()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0)


def show(lbl, x, days=None):
    OUT["tests_run"] += 1
    s = seg(x)
    if s is None:
        print(f"   {lbl:40s} too few trades (n={len(x)})")
        return None
    d = pd.to_datetime(days if days is not None else x.day)
    a, b = x[d < SPLIT], x[d >= SPLIT]
    sa, sb = seg(a), seg(b)
    isos = ""
    if sa and sb:
        agree = (sa["pf"] > 1) == (sb["pf"] > 1)
        isos = f" | 20-23 PF={sa['pf']:.3f} 24-25 PF={sb['pf']:.3f} {'AGREE' if agree else 'DISAGREE'}"
        s.update(is_pf=sa["pf"], os_pf=sb["pf"], agree=bool(agree))
    print(f"   {lbl:40s} n={s['n']:>4} PF={s['pf']:.3f} exp={s['exp']:+.2f} t={s['t']:+.2f}{isos}")
    return s


# ---------------------------------------------------------------- daily context
daily = structure.fx_daily(bars)
rng_d = daily.high - daily.low
tr = pd.concat([daily.high - daily.low,
                (daily.high - daily.close.shift(1)).abs(),
                (daily.low - daily.close.shift(1)).abs()], axis=1).max(axis=1)
feat = pd.DataFrame({
    "atr14": tr.rolling(14).mean(),
    "nr7": rng_d <= rng_d.rolling(7).min() + 1e-9,
    "inside": (daily.high < daily.high.shift(1)) & (daily.low > daily.low.shift(1)),
    "prevH": daily.high, "prevL": daily.low,
}).dropna(subset=["atr14"])


def prior_feats(day_index: pd.Series) -> pd.DataFrame:
    """For each calendar day, the features of the last FX session that COMPLETED
    before that day's 01:30 UTC Asia open (i.e. sessions ending <= day-1)."""
    dd = pd.DataFrame({"day": pd.to_datetime(day_index).astype("datetime64[ns]")}).sort_values("day")
    f = feat.copy()
    f.index = f.index.astype("datetime64[ns]")
    f["fday"] = f.index
    m = pd.merge_asof(dd.assign(key=dd.day - pd.Timedelta(days=1)).sort_values("key"),
                      f.sort_index(), left_on="key", right_index=True)
    return m.set_index("day")


# ---------------------------------------------------------------- Asia base set
# the exact deployed trade set (broker-EET lag-1 correlation filter), not a
# regenerated approximation - the adaptation tests must sit on the real thing
D = pd.read_pickle("results/trades_deployable.pkl").copy()
D["day"] = pd.to_datetime(D.day)
s0 = seg(D)
print(f"=== BASE: deployable Asia ORB  n={s0['n']} PF={s0['pf']:.3f} t={s0['t']:+.2f} ===")
assert abs(s0["pf"] - 1.320) < 0.02 and abs(s0["n"] - 652) <= 3, "base set drifted"
OUT["base"] = s0

# per-day range candle + trigger delay + relative volume
bL = engine.resample(bars, 60)
vol_rng, rhl = {}, {}
for d in D.day.dt.date.unique():
    day = pd.Timestamp(d)
    t0 = engine.session_start_utc(day)
    if t0 in bL.index:
        rhl[day] = (float(bL.at[t0, "high"]), float(bL.at[t0, "low"]))
# range-window tick volume for every day (needed for the 14-day average)
all_days = pd.Series(bars.index.date, index=bars.index).unique()
vr = {}
for d in all_days:
    day = pd.Timestamp(d)
    t0 = engine.session_start_utc(day)
    w = bars.loc[t0:t0 + pd.Timedelta(minutes=55)]
    if len(w) >= 12:
        vr[day] = float(w.volume.sum())
vr = pd.Series(vr).sort_index()
rvol = vr / vr.rolling(14).mean().shift(1)

pf_ = prior_feats(D.day)
D["atr14"] = pf_.reindex(D.day.values).atr14.values
D["nr7"] = pf_.reindex(D.day.values).nr7.values.astype(bool)
D["inside"] = pf_.reindex(D.day.values).inside.values.astype(bool)
D["prevH"] = pf_.reindex(D.day.values).prevH.values
D["prevL"] = pf_.reindex(D.day.values).prevL.values
D["rhigh"] = D.day.map(lambda d: rhl.get(d, (np.nan, np.nan))[0])
D["rlow"] = D.day.map(lambda d: rhl.get(d, (np.nan, np.nan))[1])
D["rvol"] = D.day.map(rvol)
D["delay_candles"] = ((D.t_fill - (D.day.dt.tz_localize("UTC") + pd.Timedelta(hours=1, minutes=30))).dt.total_seconds() / 60 - 120) / 60
D["ratr"] = D.range / D.atr14

print("\n=== A1/A2. CRABEL CONDITIONING (prior session NR7 / inside day) ===")
A = {}
A["nr7_on"] = show("after an NR7 session", D[D.nr7])
A["nr7_off"] = show("not after NR7", D[~D.nr7])
A["inside_on"] = show("after an inside session", D[D.inside])
A["inside_off"] = show("not after inside", D[~D.inside])
OUT["crabel"] = A

print("\n=== A3. ACTIVITY: opening-range width / ATR14, quintiles ===")
D["q_ratr"] = pd.qcut(D.ratr, 5, labels=False)
qs = []
for q in range(5):
    s = show(f"range/ATR quintile {q + 1} (q1 = narrowest)", D[D.q_ratr == q])
    if s:
        qs.append({"q": q + 1, **s})
OUT["ratr_quintiles"] = qs

print("\n=== A4. RELATIVE TICK VOLUME in the opening range, quintiles ===")
D2 = D.dropna(subset=["rvol"]).copy()
D2["q_rvol"] = pd.qcut(D2.rvol, 5, labels=False)
qs = []
for q in range(5):
    s = show(f"rel-volume quintile {q + 1} (q1 = quietest)", D2[D2.q_rvol == q])
    if s:
        qs.append({"q": q + 1, **s})
OUT["rvol_quintiles"] = qs

print("\n=== A5. TRIGGER DELAY (Crabel: earliest is best) ===")
T = {}
T["first"] = show("break on the FIRST post-range candle", D[D.delay_candles == 0])
T["later"] = show("break on a later candle", D[D.delay_candles > 0])
OUT["trigger_delay"] = T

print("\n=== A6. PRIOR-DAY-RANGE INTERACTION VETO ===")
inside_prior = (D.rhigh <= D.prevH) & (D.rlow >= D.prevL)
clears = np.where(D.side == 1, D.entry > D.prevH, D.entry < D.prevL)
veto = inside_prior & ~clears
V = {}
V["vetoed"] = show("trades the veto would DROP", D[veto])
V["kept"] = show("trades the veto keeps", D[~veto])
OUT["prior_day_veto"] = V

print("\n=== A7. ZARATTINI STOPS: fraction of ATR14 instead of 2x range ===")
nostop = trades.generate(bars, 60, stop_r=None, cost=0.30, entry_cutoff_ldn=8)
nostop["day"] = pd.to_datetime(nostop.day)
N = nostop[nostop.day.isin(D.day)].copy()      # same days as the deployed set
pfN = prior_feats(N.day)
N["atr14"] = pfN.reindex(N.day.values).atr14.values


def rewalk(df, stop_dollars):
    rows = []
    for _, r in df.iterrows():
        sd = stop_dollars(r)
        te = r.t_out                                   # time exit of the no-stop run
        stop = r.entry - r.side * sd
        path = bars.loc[r.t_fill:te - pd.Timedelta(minutes=5)]
        hit = path[(path.low <= stop) if r.side == 1 else (path.high >= stop)]
        if len(hit):
            pnl = r.side * (stop - r.entry) - 0.30
            rows.append({"day": r.day, "entry": r.entry, "pnl_oz": pnl, "why": "stop"})
        else:
            rows.append({"day": r.day, "entry": r.entry, "pnl_oz": r.pnl_oz, "why": "time"})
    return pd.DataFrame(rows)


Z = []
for f in (0.05, 0.10, 0.25, 0.50, 1.00):
    w = rewalk(N, lambda r, f=f: f * r.atr14)
    s = show(f"stop at {f:.2f} x ATR14 (stop-outs {100 * (w.why == 'stop').mean():.0f}%)", w)
    if s:
        Z.append({"f": f, "stop_rate": float((w.why == "stop").mean()), **s})
s = show("no stop at all (reference)", N)
Z.append({"f": None, "stop_rate": 0.0, **(s or {})})
s = show("2 x range (deployed reference)", D)
Z.append({"f": "2R", **(s or {})})
OUT["atr_stops"] = Z

print("\n=== A8. ZARATTINI FIRST-BAR DIRECTION at the Asia open ===")


def first_bar(tf, stop_kind):
    rows = []
    for d in all_days:
        day = pd.Timestamp(d)
        t0 = engine.session_start_utc(day)
        w = bars.loc[t0:t0 + pd.Timedelta(minutes=tf - 5)]
        if len(w) < tf // 5:
            continue
        o, c = float(w.iloc[0].open), float(w.iloc[-1].close)
        hi, lo = float(w.high.max()), float(w.low.min())
        if c == o:
            continue
        side = 1 if c > o else -1
        entry = c
        t_fill = t0 + pd.Timedelta(minutes=tf)
        te = pd.Timestamp(day.year, day.month, day.day, 16, 0, tz=NY).tz_convert("UTC")
        if te <= t_fill:
            continue
        a14 = feat.atr14.asof(day - pd.Timedelta(days=1))
        if stop_kind == "bar":
            stop = lo if side == 1 else hi
        else:
            if not np.isfinite(a14):
                continue
            stop = entry - side * stop_kind * a14
        path = bars.loc[t_fill:te - pd.Timedelta(minutes=5)]
        hit = path[(path.low <= stop) if side == 1 else (path.high >= stop)]
        if len(hit):
            px = stop
        else:
            px = engine.price_at(bars, te)
            if px is None:
                continue
        rows.append({"day": day, "entry": entry, "side": side,
                     "pnl_oz": side * (px - entry) - 0.30,
                     "why": "stop" if len(hit) else "time"})
    df = pd.DataFrame(rows)
    df["corr"] = df.day.map(CORR)
    return df


FB = {}
for tf in (5, 15):
    for sk in ("bar", 0.10, 0.25):
        fb = first_bar(tf, sk)
        lbl = f"{tf}m bar, stop {'at bar extreme' if sk == 'bar' else f'{sk:.2f}xATR'}"
        FB[f"{tf}_{sk}_all"] = show(lbl + " (all)", fb)
        FB[f"{tf}_{sk}_filt"] = show(lbl + " (corr<=0.5)", fb[fb["corr"] <= 0.5])
OUT["first_bar"] = {k: v for k, v in FB.items() if v}

# ================================================================ Block B
print("\n=== B. GATES ON THE 2.6-SIGMA FADE (15m, close_back, gross-breakeven) ===")
mr = meanrev.run(bars, tf=15, k=2.6, trigger="close_back")
mr["day"] = mr.t_fill.dt.tz_convert("UTC").dt.date


def show_mr(lbl, x):
    return show(lbl, x, days=pd.to_datetime(pd.Series(x.day.values, index=x.index)))


# B1: ADX(14) on 60m, Wilder, known at bar close
h = engine.resample(bars, 60)
up = h.high.diff()
dn = -h.low.diff()
plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=h.index)
minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=h.index)
tr1 = pd.concat([h.high - h.low, (h.high - h.close.shift(1)).abs(),
                 (h.low - h.close.shift(1)).abs()], axis=1).max(axis=1)
atr = tr1.ewm(alpha=1 / 14, adjust=False).mean()
pdi = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr
mdi = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr
dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
adx = dx.ewm(alpha=1 / 14, adjust=False).mean()
adx_known = adx.copy()
adx_known.index = adx_known.index + pd.Timedelta(minutes=60)
mr["adx"] = mr.t_fill.map(lambda t: adx_known.asof(t))
B1 = []
print("  B1. ADX(14, 1h) trend gate:")
for th in (20, 25, 30):
    s = show_mr(f"ADX < {th} (quiet regime)", mr[mr.adx < th])
    if s:
        B1.append({"th": th, "side": "below", **s})
    s = show_mr(f"ADX >= {th} (trending)", mr[mr.adx >= th])
    if s:
        B1.append({"th": th, "side": "above", **s})
OUT["adx_gate"] = B1

print("  B2. band-walk veto (bars spent beyond the band before re-entry):")
B2 = []
for lbl, m in (("single poke (exc_len = 1)", mr.exc_len <= 1),
               ("short walk (exc_len 2-3)", (mr.exc_len >= 2) & (mr.exc_len <= 3)),
               ("long walk (exc_len >= 4)", mr.exc_len >= 4)):
    s = show_mr(lbl, mr[m])
    if s:
        B2.append({"bucket": lbl, **s})
OUT["band_walk"] = B2

print("  B3. news-window scrub (8:30 & 14:00 ET windows dropped):")
et = mr.t_fill.dt.tz_convert(NY)
mins = et.dt.hour * 60 + et.dt.minute
news = ((mins >= 8 * 60 + 25) & (mins <= 9 * 60 + 5)) | ((mins >= 13 * 60 + 55) & (mins <= 14 * 60 + 35))
B3 = {}
B3["kept"] = show_mr("outside news windows", mr[~news])
B3["dropped"] = show_mr("inside news windows", mr[news])
OUT["news_scrub"] = B3

print("  B4. NY-anchored VWAP band fade:")


def vwap_fade(k):
    rows = []
    for d in all_days:
        day = pd.Timestamp(d)
        t0 = pd.Timestamp(day.year, day.month, day.day, 9, 30, tz=NY).tz_convert("UTC")
        te = pd.Timestamp(day.year, day.month, day.day, 16, 0, tz=NY).tz_convert("UTC")
        w = bars.loc[t0:te - pd.Timedelta(minutes=5)]
        if len(w) < 40:
            continue
        v = w.volume.values.astype(float)
        px = w.close.values
        cv = np.cumsum(v)
        vwap = np.cumsum(px * v) / cv
        var = np.cumsum(v * (px - vwap) ** 2) / cv     # streaming approximation
        sd = np.sqrt(var)
        z = np.where(sd > 0, (px - vwap) / sd, 0.0)
        busy = -1
        for i in range(3, len(w)):
            if i <= busy:
                continue
            zi, zp = z[i], z[i - 1]
            side = 1 if (zp <= -k and zi > -k and zi < 0) else \
                (-1 if (zp >= k and zi < k and zi > 0) else 0)
            if not side:
                continue
            entry, tgt = px[i], vwap[i]
            stop = entry - side * sd[i]
            if side * (tgt - entry) <= 0:
                continue
            out_px, why, j_out = None, "close", len(w) - 1
            for j in range(i + 1, len(w)):
                b = w.iloc[j]
                if (b.low <= stop) if side == 1 else (b.high >= stop):
                    out_px, why, j_out = stop, "stop", j
                    break
                if (b.high >= tgt) if side == 1 else (b.low <= tgt):
                    out_px, why, j_out = tgt, "target", j
                    break
            if out_px is None:
                out_px = px[-1]
            busy = j_out
            rows.append({"day": day, "entry": entry, "side": side, "why": why,
                         "pnl_oz": side * (out_px - entry) - 0.30})
    return pd.DataFrame(rows)


B4 = []
for k in (2.0, 2.6):
    vf = vwap_fade(k)
    s = show(f"VWAP fade k={k:.1f} (NY session)", vf)
    if s:
        B4.append({"k": k, **s})
OUT["vwap_fade"] = B4

json.dump(OUT, open("results/adapt.json", "w"), indent=1, default=str)
print(f"\ntests run this script: {OUT['tests_run']}")
print("written: results/adapt.json")
