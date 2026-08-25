"""Is there a better exit than the 16:00-New-York clock?

Entries are FROZEN at the deployable spec (60m range, corr filter, 08:00-London
deadline); only the exit changes. Families tested cleanly, no hybrids:

 1. the hold curve - average unrealized P&L by hours held (a diagnostic, not a
    search: it shows where the day's drift actually ends)
 2. alternative clock exits (with the deployed 2R stop)
 3. profit targets in range multiples (stop 2R, remainder to the NY close)
 4. trailing stops in range multiples
 5. breakeven moves after k ranges of profit
 6. an overnight hold to the next Asia open (informational - swap not modelled)

Every row shows the 2020-23 / 2024-25 sign split. This is exploration on a
burned sample: anything that looks better than the clock must survive both
halves AND make mechanical sense before it is even a forward-test candidate.
"""
import pandas as pd, numpy as np, warnings, json
import engine, trades
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
bars = engine.load_bars()
SPLIT = pd.Timestamp("2024-01-01")
OUT = {}
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

D = pd.read_pickle("results/trades_deployable.pkl")
D["day"] = pd.to_datetime(D.day)
nostop = trades.generate(bars, 60, stop_r=None, cost=0.30, entry_cutoff_ldn=8)
nostop["day"] = pd.to_datetime(nostop.day)
N = nostop[nostop.day.isin(D.day)].copy()
print(f"base: {len(N)} no-stop entries on the deployed days "
      f"(deployed 2R reference PF {pfx(D.pnl_oz):.3f})")


def seg(p, entry):
    pct = p / entry * 100
    return dict(n=int(len(p)), pf=pfx(p), exp=float(p.mean()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0)


def show(lbl, df, key=None):
    s = seg(df.pnl, df.entry)
    a = df[df.day < SPLIT]
    b = df[df.day >= SPLIT]
    sa, sb = pfx(a.pnl), pfx(b.pnl)
    agree = (sa > 1) == (sb > 1)
    print(f"   {lbl:44s} n={s['n']:>4} PF={s['pf']:.3f} exp={s['exp']:+.2f} "
          f"t={s['t']:+.2f} | 20-23 {sa:.3f} 24-25 {sb:.3f} {'AGREE' if agree else 'DISAGREE'}")
    rec = {"label": lbl, **s, "is_pf": float(sa), "os_pf": float(sb), "agree": bool(agree)}
    if key:
        OUT.setdefault(key, []).append(rec)
    return rec


def walk(r, stop_mult=2.0, target_mult=None, trail_mult=None, trail_after=0.0,
         be_after=None, t_exit=None):
    """Re-walk one trade's 5m path. Returns (exit_px, why, t_out).
    Trail/BE updates use the PRIOR bars' extremes before checking the current
    bar, so nothing acts on information from inside the bar being tested."""
    side, entry, rng = r.side, r.entry, r.range
    te = t_exit if t_exit is not None else r.t_out
    stop = entry - side * stop_mult * rng if stop_mult is not None else None
    target = entry + side * target_mult * rng if target_mult is not None else None
    best = entry                                   # best favorable price so far
    path = bars.loc[r.t_fill:te - pd.Timedelta(minutes=5)]
    for ts, b in path.iterrows():
        cur = stop
        if trail_mult is not None and side * (best - entry) >= trail_after * rng:
            tr = best - side * trail_mult * rng
            cur = tr if cur is None else (max(cur, tr) if side == 1 else min(cur, tr))
        if be_after is not None and side * (best - entry) >= be_after * rng:
            cur = entry if cur is None else (max(cur, entry) if side == 1 else min(cur, entry))
        hit_s = cur is not None and ((b.low <= cur) if side == 1 else (b.high >= cur))
        hit_t = target is not None and ((b.high >= target) if side == 1 else (b.low <= target))
        if hit_s:                                  # conservative: stop before target
            return cur, "stop", ts
        if hit_t:
            return target, "target", ts
        best = max(best, b.high) if side == 1 else min(best, b.low)
    px = engine.price_at(bars, te)
    return px, "time", te


def variant(lbl, key, **kw):
    rows = []
    for _, r in N.iterrows():
        px, why, t_out = walk(r, **kw)
        if px is None:
            continue
        rows.append({"day": r.day, "entry": r.entry,
                     "pnl": r.side * (px - r.entry) - 0.30, "why": why})
    return show(lbl, pd.DataFrame(rows), key)


print("\n=== 1. THE HOLD CURVE (no stop; average open P&L by hours since fill) ===")
marks = list(range(1, 15))
curve = {m: [] for m in marks}
mfe_hours = []
for _, r in N.iterrows():
    path = bars.loc[r.t_fill:r.t_out]
    if len(path):
        fav = r.side * (path.high if r.side == 1 else path.low) - r.side * r.entry
        mfe_hours.append((path.index[np.argmax(fav.values)] - r.t_fill).total_seconds() / 3600)
    for m in marks:
        tm = r.t_fill + pd.Timedelta(hours=m)
        if tm >= r.t_out:
            break
        px = engine.price_at(bars, tm)
        if px is not None:
            curve[m].append(r.side * (px - r.entry) - 0.30)
hc = []
for m in marks:
    v = curve[m]
    if len(v) > 400:
        hc.append({"h": m, "n": len(v), "mean": float(np.mean(v)), "median": float(np.median(v))})
        print(f"   +{m:>2}h: n={len(v):>4}  mean {np.mean(v):+.2f}  median {np.median(v):+.2f}")
full = N.pnl_oz
print(f"   at the 16:00-NY exit (mean hold {((N.t_out - N.t_fill).dt.total_seconds()/3600).mean():.1f}h): "
      f"mean {full.mean():+.2f}  median {full.median():+.2f}")
print(f"   median time to maximum favorable price: {np.median(mfe_hours):.1f}h")
OUT["hold_curve"] = hc
OUT["mfe_median_h"] = float(np.median(mfe_hours))

print("\n=== 2. CLOCK EXITS (2R stop throughout; deployed = 16:00 NY) ===")


def clock(lbl, tz, h, mi=0):
    z = ZoneInfo(tz)
    rows = []
    for _, r in N.iterrows():
        d = r.day
        te = pd.Timestamp(d.year, d.month, d.day, h, mi, tz=z).tz_convert("UTC")
        if te <= r.t_fill:
            continue
        px, why, _ = walk(r, stop_mult=2.0, t_exit=te)
        if px is None:
            continue
        rows.append({"day": r.day, "entry": r.entry,
                     "pnl": r.side * (px - r.entry) - 0.30, "why": why})
    return show(lbl, pd.DataFrame(rows), "clock")


clock("12:00 London", "Europe/London", 12)
clock("14:00 London", "Europe/London", 14)
clock("16:30 London (London close)", "Europe/London", 16, 30)
clock("09:30 New York (NY open)", "America/New_York", 9, 30)
clock("11:00 New York", "America/New_York", 11)
clock("13:00 New York", "America/New_York", 13)
clock("16:00 New York (deployed)", "America/New_York", 16)

print("\n=== 3. PROFIT TARGETS (2R stop, unfilled remainder to 16:00 NY) ===")
for k in (1.0, 2.0, 3.0, 4.0, 6.0):
    variant(f"target at {k:.0f} x range", "target", stop_mult=2.0, target_mult=k)
variant("no target (deployed)", "target", stop_mult=2.0)

print("\n=== 4. TRAILING STOPS (initial stop 2R) ===")
for k in (1.0, 1.5, 2.0, 3.0):
    variant(f"trail {k:.1f} x range from best price", "trail",
            stop_mult=2.0, trail_mult=k)
for k in (1.0, 2.0):
    variant(f"trail {k:.1f} x range, armed after +1 range", "trail",
            stop_mult=2.0, trail_mult=k, trail_after=1.0)

print("\n=== 5. BREAKEVEN MOVES (2R stop until armed) ===")
for k in (0.5, 1.0, 1.5):
    variant(f"stop to entry after +{k:.1f} range", "breakeven",
            stop_mult=2.0, be_after=k)

print("\n=== 6. OVERNIGHT HOLD (informational; swap/rollover NOT modelled) ===")
rows = []
for _, r in N.iterrows():
    te = engine.session_start_utc(r.day + pd.Timedelta(days=1))
    px, why, _ = walk(r, stop_mult=2.0, t_exit=te)
    if px is None:
        continue
    rows.append({"day": r.day, "entry": r.entry,
                 "pnl": r.side * (px - r.entry) - 0.30, "why": why})
show("hold to next 09:30 HKT, 2R stop", pd.DataFrame(rows), "overnight")

json.dump(OUT, open("results/exits.json", "w"), indent=1, default=str)
print("\nwritten: results/exits.json")
