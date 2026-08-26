"""Round 24 Spec A: Turtle risk layer transplanted onto the deployed trade set,
plus the Marcus gap-through-stop tail audit. Pre-registered in the goal ledger.

All overlays keep the deployed ENTRIES and the 16:00-NY flat; only sizing,
stop placement, and adds change. Scored on risk-adjusted account numbers
($2,000 start, 1% base risk, 20x leverage cap) against the deployed baseline.
Registered expectation: sizing changes risk shape, not expectancy sign.
"""
import pandas as pd, numpy as np, json, warnings, engine
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")

f = pd.read_pickle("results/trades_deployable.pkl")
gold = engine.load_bars()

# N = 20-day Wilder ATR on daily bars from the verified 5m feed, lagged one day
d = gold.resample("1D").agg({"high": "max", "low": "min", "close": "last"}).dropna()
prev_c = d.close.shift(1)
tr = pd.concat([d.high - d.low, (d.high - prev_c).abs(), (d.low - prev_c).abs()], axis=1).max(axis=1)
N = tr.ewm(alpha=1 / 20, adjust=False).mean().shift(1)          # Wilder, closed bars only
N.index = N.index.tz_localize(None).normalize()
f = f.copy()
f["day_ts"] = pd.to_datetime(f.day).dt.normalize()
f["N"] = f.day_ts.map(N)
f = f.dropna(subset=["N"]).reset_index(drop=True)
print(f"trades with N available: {len(f)} (of 652); N median ${f.N.median():.1f}, "
      f"vs stop_dist median ${f.stop_dist.median():.1f}")

COST, SLIP = 0.30, 0.30
LEV = 20.0

def account(rows, start=2000.0):
    """rows: iterable of (day, entry, per_oz_risk_dollars, pnl_oz, mae_oz).
    Sizes 1% of equity by per_oz_risk, margin-capped; returns account stats."""
    eq, curve = start, []
    for day, entry, risk_oz, pnl_oz, mae_oz in rows:
        if eq <= 0:
            curve.append((day, 0.0)); continue
        oz = (eq * 0.01) / max(risk_oz, 0.01)
        oz = min(oz, eq * LEV / entry)
        if oz * mae_oz >= eq:
            eq = 0.0; curve.append((day, 0.0)); continue
        eq = max(eq + oz * pnl_oz, 0.0)
        curve.append((day, eq))
    c = pd.Series([e for _, e in curve], index=[d for d, _ in curve])
    peak = c.cummax()
    dd = ((peak - c) / peak.replace(0, np.nan)).fillna(1.0)
    yrs = (pd.Timestamp(c.index[-1]) - pd.Timestamp(c.index[0])).days / 365.25
    cagr = (c.iloc[-1] / start) ** (1 / yrs) - 1 if c.iloc[-1] > 0 else -1.0
    return dict(final=float(c.iloc[-1]), cagr=float(cagr), max_dd=float(dd.max()),
                mar=float(cagr / dd.max()) if dd.max() > 0 else np.nan)

out = {}

# ---------------- baseline: deployed sizing (1% / actual stop distance)
base_rows = [(r.day, r.entry, r.stop_dist, r.pnl_oz, r.mae_oz) for r in f.itertuples()]
out["baseline_deployed"] = account(base_rows)

# ---------------- overlay 1: N-sizing (1% / N), same trades
out["overlay1_N_sizing"] = account(
    [(r.day, r.entry, r.N, r.pnl_oz, r.mae_oz) for r in f.itertuples()])

# ---------------- overlay 2: 2N stop, re-simulated on 5m paths
def resim(row, stop_mult_N=2.0):
    stop = row.entry - row.side * stop_mult_N * row.N
    te = row.t_out if row.reason == "time" else None
    day = pd.Timestamp(row.day)
    t_end = pd.Timestamp(day.year, day.month, day.day, 16, 0,
                         tz=ZoneInfo("America/New_York")).tz_convert("UTC")
    path = gold.loc[row.t_fill:t_end]
    if not len(path):
        return None
    if row.side > 0:
        hit = path[path.low <= stop]
    else:
        hit = path[path.high >= stop]
    if len(hit):
        exit_px, reason, t_x = stop, "stop", hit.index[0]
    else:
        exit_px, reason, t_x = float(path.close.iloc[-1]), "time", path.index[-1]
    pnl = row.side * (exit_px - row.entry) - COST - (SLIP if reason == "stop" else 0.0)
    if row.side > 0:
        mae = row.entry - float(path.low.loc[:t_x].min())
    else:
        mae = float(path.high.loc[:t_x].max()) - row.entry
    return pnl, max(mae, 0.0), reason

r2 = [resim(r) for r in f.itertuples()]
ok = [i for i, x in enumerate(r2) if x is not None]
f2 = f.iloc[ok].reset_index(drop=True)
pnl2 = np.array([r2[i][0] for i in ok]); mae2 = np.array([r2[i][1] for i in ok])
stopped2 = np.mean([r2[i][2] == "stop" for i in ok])
pct2 = pnl2 / f2.entry * 100
pf_ = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
out["overlay2_2N_stop"] = dict(
    n=len(f2), pf=pf_(pd.Series(pnl2)), exp=float(pnl2.mean()),
    t=float(pct2.mean() / pct2.std() * np.sqrt(len(pct2))), stopped=float(stopped2),
    account=account([(f2.day.iloc[i], f2.entry.iloc[i], 2.0 * f2.N.iloc[i],
                      pnl2[i], mae2[i]) for i in range(len(f2))]))

# ---------------- overlay 3: pyramiding, gradient over max-units
def pyramid(row, max_units):
    day = pd.Timestamp(row.day)
    t_end = pd.Timestamp(day.year, day.month, day.day, 16, 0,
                         tz=ZoneInfo("America/New_York")).tz_convert("UTC")
    path = gold.loc[row.t_fill:t_end]
    if not len(path):
        return None
    side, Nv = row.side, row.N
    entries = [row.entry]
    stop = row.entry - side * row.stop_dist          # deployed initial stop
    pnl_units, done = [], False
    for bar in path.itertuples():
        # stop check first (conservative: stop before add within a bar)
        if (side > 0 and bar.low <= stop) or (side < 0 and bar.high >= stop):
            for e in entries:
                pnl_units.append(side * (stop - e) - COST - SLIP)
            done = True
            break
        # add units each +0.5N of favorable movement from the FIRST entry
        while (len(entries) < max_units
               and ((side > 0 and bar.high >= row.entry + side * 0.5 * Nv * len(entries))
                    or (side < 0 and bar.low <= row.entry + side * 0.5 * Nv * len(entries)))):
            add_px = row.entry + side * 0.5 * Nv * len(entries)
            entries.append(add_px)
            stop = add_px - side * 2.0 * Nv          # all stops to 2N below newest add
    if not done:
        exit_px = float(path.close.iloc[-1])
        for e in entries:
            pnl_units.append(side * (exit_px - e) - COST)
    return float(np.mean(pnl_units)), len(entries)   # per-unit pnl, units used

grad = {}
for mu in (1, 2, 3, 4):
    res = [pyramid(r, mu) for r in f.itertuples()]
    ok3 = [i for i, x in enumerate(res) if x is not None]
    per_oz = np.array([res[i][0] for i in ok3])
    units = np.array([res[i][1] for i in ok3])
    fx = f.iloc[ok3]
    pct = per_oz / fx.entry.values * 100
    grad[f"max_units_{mu}"] = dict(
        n=len(ok3), avg_units=float(units.mean()), pf=pf_(pd.Series(per_oz)),
        exp_per_unit_oz=float(per_oz.mean()),
        t=float(pct.mean() / pct.std() * np.sqrt(len(pct))),
        account=account([(fx.day.iloc[k], fx.entry.iloc[k], fx.stop_dist.iloc[k],
                          per_oz[j] * units[j], units[j] * fx.stop_dist.iloc[k] * 1.0)
                         for j, k in enumerate(range(len(fx)))]))
out["overlay3_pyramid"] = grad

# ---------------- overlay 4: drawdown throttle on the deployed baseline
def account_throttle(rows, start=2000.0):
    eq, peak, curve = start, start, []
    for day, entry, risk_oz, pnl_oz, mae_oz in rows:
        if eq <= 0:
            curve.append((day, 0.0)); continue
        peak = max(peak, eq)
        dd = (peak - eq) / peak
        scale = max(1.0 - 2.0 * dd, 0.2)             # -20% size per -10% DD, floored
        oz = (eq * 0.01 * scale) / max(risk_oz, 0.01)
        oz = min(oz, eq * LEV / entry)
        if oz * mae_oz >= eq:
            eq = 0.0; curve.append((day, 0.0)); continue
        eq = max(eq + oz * pnl_oz, 0.0)
        curve.append((day, eq))
    c = pd.Series([e for _, e in curve], index=[d for d, _ in curve])
    pk = c.cummax(); dd = ((pk - c) / pk.replace(0, np.nan)).fillna(1.0)
    yrs = (pd.Timestamp(c.index[-1]) - pd.Timestamp(c.index[0])).days / 365.25
    cagr = (c.iloc[-1] / start) ** (1 / yrs) - 1 if c.iloc[-1] > 0 else -1.0
    return dict(final=float(c.iloc[-1]), cagr=float(cagr), max_dd=float(dd.max()),
                mar=float(cagr / dd.max()) if dd.max() > 0 else np.nan)
out["overlay4_dd_throttle"] = account_throttle(base_rows)

# ---------------- Marcus gap-through-stop tail audit (descriptive)
st = f[f.reason == "stop"].copy()
st["intended_loss"] = st.stop_dist                      # $/oz at the stop, pre-slippage
st["realized_loss"] = -(st.pnl_oz)                      # includes cost + modeled slippage
st["gap_through"] = st.realized_loss - st.intended_loss - COST - SLIP  # beyond model
# worst realized vs intended at 1% risk: loss fraction = realized/intended * 1%
ratio = st.realized_loss / st.intended_loss
# data-gap exposure inside trade windows
gaps = []
for r in f.sample(min(len(f), 200), random_state=7).itertuples():
    day = pd.Timestamp(r.day)
    t_end = pd.Timestamp(day.year, day.month, day.day, 16, 0,
                         tz=ZoneInfo("America/New_York")).tz_convert("UTC")
    ix = gold.loc[r.t_fill:t_end].index
    if len(ix) > 1:
        gaps.append(float(ix.to_series().diff().max().total_seconds() / 60))
out["gap_audit"] = dict(
    n_stop_exits=len(st),
    worst_loss_ratio=float(ratio.max()), p99_loss_ratio=float(ratio.quantile(0.99)),
    med_loss_ratio=float(ratio.median()),
    pct_worse_than_1p25x=float((ratio > 1.25).mean()),
    worst_loss_at_1pct_risk=float(ratio.max() * 0.01),
    max_bar_gap_minutes_sampled=float(max(gaps)) if gaps else None,
    note="ratio = realized loss / intended stop distance; includes $0.30 cost + $0.30 modeled stop slippage")

json.dump(out, open("results/r24_turtle.json", "w"), indent=1, default=str)

print("\n=== SPEC A: TURTLE RISK LAYER ON THE DEPLOYED SET ($2,000, 1% risk) ===")
for k in ("baseline_deployed", "overlay1_N_sizing", "overlay4_dd_throttle"):
    a = out[k]
    print(f"{k:22s} final ${a['final']:>9,.0f}  CAGR {a['cagr']*100:+6.1f}%  "
          f"maxDD {a['max_dd']*100:5.1f}%  MAR {a['mar']:.2f}")
a = out["overlay2_2N_stop"]
print(f"overlay2_2N_stop       PF {a['pf']:.3f} exp ${a['exp']:+.2f}/oz t {a['t']:+.2f} "
      f"stopped {a['stopped']*100:.0f}%  -> final ${a['account']['final']:>9,.0f} "
      f"maxDD {a['account']['max_dd']*100:.1f}% MAR {a['account']['mar']:.2f}")
print("\npyramiding gradient (per-unit expectancy and account):")
for mu in (1, 2, 3, 4):
    gr = grad[f"max_units_{mu}"]
    print(f"  max_units={mu}: avg units {gr['avg_units']:.2f}  PF {gr['pf']:.3f}  "
          f"${gr['exp_per_unit_oz']:+.2f}/oz/unit  t {gr['t']:+.2f}  "
          f"final ${gr['account']['final']:>9,.0f}  maxDD {gr['account']['max_dd']*100:.1f}%")
ga = out["gap_audit"]
print(f"\n=== MARCUS GAP AUDIT === {ga['n_stop_exits']} stop exits; "
      f"median loss ratio {ga['med_loss_ratio']:.3f}, p99 {ga['p99_loss_ratio']:.3f}, "
      f"worst {ga['worst_loss_ratio']:.3f} (= {ga['worst_loss_at_1pct_risk']*100:.2f}% of equity at 1% risk); "
      f"{ga['pct_worse_than_1p25x']*100:.1f}% of stops worse than 1.25x intended; "
      f"largest 5m-bar gap in sampled windows {ga['max_bar_gap_minutes_sampled']:.0f} min")
