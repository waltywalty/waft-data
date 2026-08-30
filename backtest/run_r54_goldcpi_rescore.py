"""Round 54: watch #5 re-score on the extended 2013-2026 gold history
(frozen spec per reference/goal_ledger.md Round 54 registration).
Outputs results/r54_goldcpi_rescore.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST = 0.35

# --- unified ET bar-close series: m15 (ET = feed - 7h) before the 5m feed starts ---
m15 = pd.read_csv("data/XAUUSD_m15_ejtrader.csv", parse_dates=["Date"])
m15_ts = m15.Date - pd.Timedelta(hours=7)
m15_px = pd.Series(m15.close.values / 100.0, index=m15_ts).sort_index()

f5 = pd.read_csv("data/XAUUSD_5m.csv")
f5_ts = pd.to_datetime(f5.Date.astype(str) + " " + f5.Time.astype(str))
f5_px = pd.Series(f5.Close.values, index=f5_ts).sort_index()

cutover = f5_px.index[0]
px = pd.concat([m15_px[m15_px.index < cutover], f5_px]).sort_index()
px = px[~px.index.duplicated()]
print(f"unified ET close series: {px.index[0]} .. {px.index[-1]}, {len(px)} bars, cutover {cutover}")

# daily ATR20 (range of ET calendar day, rolling 20, shifted)
dts = pd.Series(px.values, index=px.index)
day = dts.groupby(dts.index.date)
rng = day.max() - day.min()
atr20 = rng.rolling(20).mean().shift(1)

# --- CPI events ---
raw = open("data/econ_events_us_high_fxs.json").read()
ev = json.loads(raw[raw.find("{"):])["result"]["events"]
cpi = []
for e in ev:
    name = e.get("n") or ""
    if "Consumer Price Index" not in name:
        continue
    dev = e.get("dev")
    if dev is None or not np.isfinite(float(dev)) or float(dev) == 0:
        continue
    et = pd.Timestamp(e["d"]).tz_convert("America/New_York").tz_localize(None)
    cpi.append((et, float(dev), name))
cpi.sort()
print(f"CPI variant events with dev: {len(cpi)}")

# collapse same-timestamp variants keeping max |dev|
by_ts = {}
for et, dev, name in cpi:
    if et not in by_ts or abs(dev) > abs(by_ts[et][0]):
        by_ts[et] = (dev, name)
# releases are 08:30 ET; check the UTC->ET mapping empirically on the modal hour
hrs = pd.Series([k.hour * 100 + k.minute for k in by_ts])
print("release ET clock distribution (top):", hrs.value_counts().head(3).to_dict())

bars = px.index.values
positions = pd.Series(range(len(px)), index=px.index)


def first_at_or_after(t, max_lag_min=45):
    i = px.index.searchsorted(pd.Timestamp(t))
    if i >= len(px): return None
    if (px.index[i] - pd.Timestamp(t)).total_seconds() > max_lag_min * 60: return None
    return i


def score(thr, hold):
    pnls, atrs, keys = [], [], []
    for et, (dev, name) in sorted(by_ts.items()):
        if abs(dev) < thr:
            continue
        i = first_at_or_after(et + pd.Timedelta(minutes=5))
        if i is None:
            continue
        e = px.iloc[i]
        d0 = px.index[i].date()
        if hold == "60m":
            j = first_at_or_after(px.index[i] + pd.Timedelta(minutes=60), max_lag_min=90)
            if j is None: continue
            xp = px.iloc[j]
        else:
            day_bars = px[(px.index.date == d0) & (px.index <= pd.Timestamp(str(d0)) + pd.Timedelta(hours=16))]
            if not len(day_bars) or day_bars.index[-1] <= px.index[i]: continue
            xp = day_bars.iloc[-1]
        a = atr20.get(d0, np.nan)
        if not (np.isfinite(a) and a > 0): continue
        side = -np.sign(dev)
        pnls.append(side * (xp - e) - COST)
        atrs.append(a); keys.append(d0)
    return np.array(pnls), np.array(atrs), keys


def stats(p, a):
    r = p / a
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


out = {}
print(f"\n=== Watch #5 re-score, extended span (PRIMARY = thr 0.25, hold close) ===")
print(f"{'thr':>5} {'hold':>6} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for thr in (0.25, 0.5):
    for hold in ("60m", "close"):
        p, a, k = score(thr, hold)
        s = stats(p, a)
        out[f"thr{thr}_{hold}"] = s
        if s.get("n", 0) >= 10:
            c15 = stats(p - 0.5 * COST, a)
            s["cost15_avg_R"] = c15.get("avg_R")
            tag = "  <- PRIMARY" if (thr == 0.25 and hold == "close") else ""
            print(f"{thr:>5} {hold:>6} | {s['n']:>4} {s['wr']*100:>5.1f}% {s['pf']:>5.2f} "
                  f"{s['avg_R']:>+7.3f} {s['t']:>+6.2f} {str(s['halves']):>12}{tag}")

pr = out["thr0.25_close"]
PASS = (pr.get("n", 0) >= 40 and (pr.get("avg_R") or -1) > 0 and (pr.get("t") or -9) >= 2
        and (pr.get("pf") or 0) >= 1.15 and (pr.get("cost15_avg_R") or -1) > 0)
print(f"\nPRIMARY vs program bar: {'PASS - goes to user for sign-off' if PASS else 'FAIL - stays a watch item'}")
json.dump(dict(cells=out, primary="thr0.25_close", bar_pass=bool(PASS)),
          open("results/r54_goldcpi_rescore.json", "w"), indent=1, default=float)
