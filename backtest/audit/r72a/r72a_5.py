"""Round 72A step 3, attempt 5 (overnight gap, small bucket, CONT/0930/target) REVERSED, IS ONLY.
Reuses run_r37_scalps.py load_frame/rth_of and a verbatim copy of run_r42e_gap.py build()/walk().
Per-instrument IS cut = keys[int(len(keys)*0.75)] exactly as the runner; sessions on/after the cut
are dropped BEFORE any return is computed (OOS firewall). Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, warnings, sys, os, json
sys.path.insert(0, "/home/user/waft-data/backtest"); os.chdir("/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's dict, full round trip, points

# ---- verbatim from run_r42e_gap.py ----
def build(idx):
    rth = rth_of(load_frame(idx))
    days = {}
    daily = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                    hi=("high", "max"), lo=("low", "min"))
    daily["atr20"] = (daily.hi - daily.lo).rolling(20).mean().shift(1)
    daily["prevc"] = daily.c.shift(1)
    for skey, g in rth.groupby("skey"):
        d = daily.loc[skey]
        if len(g) < 50 or not np.isfinite(d.atr20) or d.atr20 <= 0 or not np.isfinite(d.prevc):
            continue
        days[skey] = (g[["open", "high", "low", "close"]].values, g.hm.values,
                      float(d.o), float(d.prevc), float(d.atr20))
    return days

def walk(arr, start, side, s_px, t_px):
    for k in range(start, len(arr)):
        o_, h_, l_, c_ = arr[k]
        if (side > 0 and l_ <= s_px) or (side < 0 and h_ >= s_px):
            return s_px
        if t_px is not None and ((side > 0 and h_ >= t_px) or (side < 0 and l_ <= t_px)):
            return t_px
    return arr[-1][3]

def trade_gross(arr, hm, o930, prevc, atr20, dmode, ename, xmode):
    """Runner's per-day trade logic, gross points (no cost); NaN if the day is skipped."""
    g = o930 - prevc
    side = -np.sign(g) if dmode == "FILL" else np.sign(g)
    if side == 0:
        return np.nan
    if ename == "0930":
        start, e = 0, o930
    else:
        pre = np.where(hm < 1000)[0]; post = np.where(hm >= 1000)[0]
        if not len(pre) or not len(post):
            return np.nan
        tgt0 = prevc if dmode == "FILL" else o930 + side * abs(g)
        seg = arr[pre]
        if (side > 0 and seg[:, 1].max() >= tgt0) or (side < 0 and seg[:, 2].min() <= tgt0):
            return np.nan
        start, e = post[0], arr[pre[-1]][3]
    s_px = e - side * 0.5 * atr20
    t_px = None
    if xmode == "target":
        t_px = prevc if dmode == "FILL" else o930 + side * abs(g)
        if (side > 0 and t_px <= e) or (side < 0 and t_px >= e):
            return np.nan
    px = walk(arr, start, side, s_px, t_px)
    return side * (px - e)

COMBOS = [(d, e, x) for d in ("FILL", "CONT") for e in ("0930", "1000") for x in ("target", "eod")]
rows = []
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    days = build(idx); keys = sorted(days); cutd = keys[int(len(keys) * 0.75)]
    is_keys = [k for k in keys if k < cutd]                      # OOS FIREWALL
    print(f"IS cut {idx}: {cutd}  (IS sessions {len(is_keys)}, dropped on/after cut {len(keys)-len(is_keys)})")
    prev_g = np.nan
    for k in is_keys:
        arr, hm, o930, prevc, atr20 = days[k]
        g = o930 - prevc; gn = abs(g) / atr20
        r = dict(idx=idx, skey=k, g=g, gn=gn, atr=atr20, cost=MICRO[idx], prev_g=prev_g,
                 long_eod=arr[-1][3] - o930)
        for (d, e, x) in COMBOS:
            r[f"{d}_{e}_{x}"] = trade_gross(arr, hm, o930, prevc, atr20, d, e, x)
        # lagged-gap placebo: direction from PREVIOUS session's gap sign, today's small-gap filter, 0930->EOD, 0.5xATR stop
        if np.isfinite(prev_g) and prev_g != 0:
            side = -np.sign(prev_g)                         # reversed (fade) of yesterday's gap
            r["placebo_lag_gross"] = side * (walk(arr, 0, side, o930 - side * 0.5 * atr20, None) - o930)
        else:
            r["placebo_lag_gross"] = np.nan
        rows.append(r); prev_g = g
big = pd.DataFrame(rows); big["date"] = pd.to_datetime(big.skey); big["year"] = big.date.dt.year

def st(gross, cost, atr, dates=None, years=None, mult=1.0):
    gross = np.asarray(gross, float); ok = np.isfinite(gross)
    r = (gross[ok] - mult * np.asarray(cost, float)[ok]) / np.asarray(atr, float)[ok]
    n = len(r); m = n // 2
    if n < 2: return dict(n=n)
    w, l = r[r > 0], r[r <= 0]
    out = dict(n=n, avgR=float(r.mean()), t=float(r.mean() / r.std() * np.sqrt(n)) if r.std() > 0 else np.nan,
               wr=float((r > 0).mean()), pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else np.inf,
               halves_runner=[int(np.sign(r[:m].mean())), int(np.sign(r[m:].mean()))])
    if dates is not None:
        dd = np.asarray(dates)[ok]; o = np.argsort(dd, kind="stable"); rc = r[o]
        out["halves_chrono"] = [int(np.sign(rc[:m].mean())), int(np.sign(rc[m:].mean()))]
    if years is not None:
        yy = np.asarray(years)[ok]
        out["per_year"] = {int(y): (int(np.sign(r[yy == y].mean())), int((yy == y).sum())) for y in sorted(set(yy))}
    return out

def fmt(s):
    if s.get("n", 0) < 2: return f"n {s.get('n',0)}"
    return (f"n {s['n']:5d} avgR {s['avgR']:+.4f} t {s['t']:+6.2f} WR {s['wr']:.3f} PF {s['pf']:.3f} "
            f"halves(runner-order) {s['halves_runner']} halves(chrono) {s.get('halves_chrono')}")

def ladder(sub, gross, label):
    out = {}
    for mult in (1.0, 1.5, 2.0):
        out[mult] = st(gross, sub.cost, sub.atr, sub.date.values, sub.year.values, mult)
    s1, s15, s2, sg = out[1.0], out[1.5], out[2.0], st(gross, sub.cost, sub.atr, mult=0.0)
    print(f"{label}\n  1x  : {fmt(s1)}\n  1.5x: avgR {s15.get('avgR',np.nan):+.4f} t {s15.get('t',np.nan):+.2f}\n"
          f"  2x  : avgR {s2.get('avgR',np.nan):+.4f} t {s2.get('t',np.nan):+.2f}\n  gross: avgR {sg.get('avgR',np.nan):+.4f} t {sg.get('t',np.nan):+.2f}")
    if "per_year" in s1:
        print("  per-year sign (1x) [year: sign, n]:", {y: v for y, v in s1["per_year"].items()})
    return out

BUCKETS = {"small": (0.1, 0.3), "mid": (0.3, 0.7), "large": (0.7, np.inf)}
small = big[(big.gn >= 0.1) & (big.gn < 0.3)]

print("\n=== SANITY: registered cells recomputed at 1x (should match results/r42e_gap.json IS) ===")
for c in ("CONT_0930_target", "FILL_0930_target", "CONT_0930_eod", "FILL_0930_eod"):
    print(f"  small/{c}: {fmt(st(small[c], small.cost, small.atr, small.date.values))}")

print("\n=== REVERSED CELL (primary): literal -1 x small/CONT/0930/target gross, costs subtracted ===")
rev = ladder(small, -small.CONT_0930_target, "reversed literal mirror (side=-sign(g), TP 0.5xATR, SL |g|, EOD backstop)")
print("\n=== REVERSED CELL (registered tradable mirror): small/FILL/0930/target ===")
rev_fill = ladder(small, small.FILL_0930_target, "small/FILL/0930/target (side=-sign(g), target prior close, 0.5xATR stop)")
print("\n=== EOD-exit pair: literal -1 x small/CONT/0930/eod and small/FILL/0930/eod ===")
rev_eod = ladder(small, -small.CONT_0930_eod, "reversed literal mirror of CONT/0930/eod (side=-sign(g), TP 0.5xATR, no SL, EOD)")
fill_eod = ladder(small, small.FILL_0930_eod, "small/FILL/0930/eod")

print("\n=== PER-INSTRUMENT, reversed literal mirror, 1x ===")
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    s = small[small.idx == idx]; print(f"  {idx}: {fmt(st(-s.CONT_0930_target, s.cost, s.atr, s.date.values))}")

print("\n=== UNCONDITIONAL CONTROLS, every eligible IS session (any gap size, g != 0), 09:30 -> EOD close, 1x cost ===")
allg = big[big.g != 0]
ctrl = {}
ctrl["fade_all"] = st(-np.sign(allg.g) * allg.long_eod, allg.cost, allg.atr, allg.date.values, allg.year.values)
ctrl["long_all"] = st(allg.long_eod, allg.cost, allg.atr, allg.date.values, allg.year.values)
ctrl["short_all"] = st(-allg.long_eod, allg.cost, allg.atr, allg.date.values, allg.year.values)
# same-mechanics control: reversed literal mirror rule applied on every eligible session regardless of size
ctrl["mirror_rule_all"] = st(-allg.CONT_0930_target, allg.cost, allg.atr, allg.date.values, allg.year.values)
for k, v in ctrl.items(): print(f"  {k:>16}: {fmt(v)}")
print("  (direction implied by the reversal = -sign(gap), mixed long/short; fade_all is that direction on all sessions,"
      "\n   long_all / short_all are the pure always-long / always-short window controls)")

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float); a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean(); se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)); return d, d / se
def Rx1(gross, sub): return (np.asarray(gross, float) - sub.cost.values) / sub.atr.values
print("\n=== DIFFERENCE reversed minus control (Welch, two samples; cell days are a subset of control days) ===")
for cname, cg, csub in (("fade_all", -np.sign(allg.g) * allg.long_eod, allg), ("long_all", allg.long_eod, allg),
                        ("short_all", -allg.long_eod, allg), ("mirror_rule_all", -allg.CONT_0930_target, allg)):
    d, t = welch(Rx1(-small.CONT_0930_target, small), Rx1(cg, csub))
    print(f"  reversed literal mirror - {cname:>16}: dAvgR {d:+.4f} t {t:+.2f}")
d, t = welch(Rx1(small.FILL_0930_target, small), Rx1(-np.sign(allg.g) * allg.long_eod, allg))
print(f"  small/FILL/0930/target  - fade_all        : dAvgR {d:+.4f} t {t:+.2f}")
# paired by date: on the cell's own days, reversed cell minus same-day fade-to-EOD (isolates exit mechanics)
pr = Rx1(-small.CONT_0930_target, small) - Rx1(-np.sign(small.g) * small.long_eod, small)
pr = pr[np.isfinite(pr)]
print(f"  paired-by-date on cell days (reversed mirror - same-day fade-to-EOD): dAvgR {pr.mean():+.4f} t {pr.mean()/pr.std(ddof=1)*np.sqrt(len(pr)):+.2f} n {len(pr)}")

print("\n=== GRADIENT: |gap|/ATR20 ladder, reversed literal mirror (-1 x CONT/0930/target) and FILL/0930/target, 1x ===")
bands = [(0.0, 0.05), (0.05, 0.1), (0.1, 0.15), (0.15, 0.2), (0.2, 0.25), (0.25, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0), (1.0, np.inf)]
for lo_, hi_ in bands:
    s = big[(big.gn >= lo_) & (big.gn < hi_) & (big.g != 0)]
    a = st(-s.CONT_0930_target, s.cost, s.atr); b = st(s.FILL_0930_target, s.cost, s.atr); c = st(s.FILL_0930_eod, s.cost, s.atr)
    print(f"  [{lo_:.2f},{hi_ if np.isfinite(hi_) else 'inf'}): mirror n {a.get('n',0):5d} avgR {a.get('avgR',np.nan):+.4f} t {a.get('t',np.nan):+.2f} | "
          f"FILL/target avgR {b.get('avgR',np.nan):+.4f} t {b.get('t',np.nan):+.2f} | FILL/eod avgR {c.get('avgR',np.nan):+.4f} t {c.get('t',np.nan):+.2f}")
print("\n=== GRADIENT: family grid reversed (literal -1 x CONT gross) by bucket x entry x exit, 1x ===")
for bname, (lo_, hi_) in BUCKETS.items():
    s = big[(big.gn >= lo_) & (big.gn < hi_)]
    for e in ("0930", "1000"):
        for x in ("target", "eod"):
            a = st(-s[f"CONT_{e}_{x}"], s.cost, s.atr, s.date.values); b = st(s[f"FILL_{e}_{x}"], s.cost, s.atr, s.date.values)
            print(f"  {bname:>5} {e} {x:>6}: -CONT n {a['n']:5d} avgR {a['avgR']:+.4f} t {a['t']:+.2f} halves {a['halves_chrono']} | "
                  f"FILL n {b['n']:5d} avgR {b['avgR']:+.4f} t {b['t']:+.2f} halves {b['halves_chrono']}")

print("\n=== PLACEBO ===")
sub = big[(big.gn > 0) & (big.gn < 0.1)]
p1 = st(-sub.CONT_0930_target, sub.cost, sub.atr, sub.date.values)
print(f"  sub-threshold band |g|/ATR in (0,0.1), reversed literal mirror: {fmt(p1)}")
p1b = st(sub.FILL_0930_eod, sub.cost, sub.atr, sub.date.values)
print(f"  sub-threshold band (0,0.1), FILL/0930/eod                     : {fmt(p1b)}")
p2 = st(small.placebo_lag_gross, small.cost, small.atr, small.date.values)
print(f"  day-shifted: fade PREVIOUS session's gap sign on today's small-gap days, 0930->EOD, 0.5xATR stop: {fmt(p2)}")
sh = big[(big.gn >= 0.1) & (big.gn < 0.3) & np.isfinite(big.prev_g) & (big.prev_g != 0)]
sh_g = -np.sign(sh.prev_g) * sh.long_eod
p3 = st(sh_g, sh.cost, sh.atr, sh.date.values)
print(f"  day-shifted: fade previous gap sign, 0930->EOD no stop, small-gap days: {fmt(p3)}")

json.dump(dict(reversed_literal={str(k): v for k, v in rev.items()}, reversed_fill={str(k): v for k, v in rev_fill.items()},
               reversed_eod_literal={str(k): v for k, v in rev_eod.items()}, fill_eod={str(k): v for k, v in fill_eod.items()},
               controls=ctrl, placebo=dict(subband=p1, subband_fill_eod=p1b, lag_stop=p2, lag_eod=p3)),
          open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_5.json", "w"), indent=1, default=float)
