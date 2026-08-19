"""Confluence filters, evaluated in-sample (2020-08..2023-12) and out-of-sample
(2024-01..2025-08). A filter is only interesting if it survives BOTH."""
import pandas as pd, numpy as np, engine, entries

bars = engine.load_bars()
OS_START = pd.Timestamp("2024-01-01").date()

# ---------- daily context, built only from information available before 01:30 --
sess = []
for d, grp in bars.groupby(bars.index.date):
    t0 = engine.session_start_utc(pd.Timestamp(d))
    s = grp[(grp.index >= t0) & (grp.index <= t0.normalize() + pd.Timedelta(hours=21))]
    if len(s) < 12:
        continue
    sess.append({"day": d, "s_open": float(s.iloc[0].open), "s_close": float(s.iloc[-1].close),
                 "s_high": float(s.high.max()), "s_low": float(s.low.min())})
S = pd.DataFrame(sess).set_index("day")
S["tr"] = np.maximum(S.s_high - S.s_low,
                     np.maximum((S.s_high - S.s_close.shift()).abs(),
                                (S.s_low - S.s_close.shift()).abs()))
S["atr14"] = S.tr.rolling(14).mean().shift(1)          # shift -> prior days only
S["prev_close"] = S.s_close.shift(1)
S["prev_high"] = S.s_high.shift(1)
S["prev_low"] = S.s_low.shift(1)
S["prev_dir"] = np.sign(S.s_close.shift(1) - S.s_open.shift(1))
S["ema20"] = S.s_close.shift(1).ewm(span=20).mean()
S["ema50"] = S.s_close.shift(1).ewm(span=50).mean()
S["trend"] = np.sign(S.ema20 - S.ema50)
S["mom5"] = np.sign(S.s_close.shift(1) - S.s_close.shift(6))
S["atr_pct"] = S.atr14.rolling(120).rank(pct=True)

def build(L, anchor, mode="confirm_close"):
    t = entries.backtest_entry(bars, L, anchor, mode=mode)
    t = t[t.traded].copy().join(S, on="day")
    t["dow"] = pd.to_datetime(t.day).dt.dayofweek
    t["rng_atr"] = t.range_size / t.atr14
    t["gap_dir"] = np.sign(t.range_open - t.prev_close)
    t["trend_align"] = (t.side == t.trend).astype(int)
    t["mom_align"] = (t.side == t.mom5).astype(int)
    t["prevdir_align"] = (t.side == t.prev_dir).astype(int)
    t["gap_align"] = (t.side == t.gap_dir).astype(int)
    t["clears_prev"] = np.where(t.side == 1, t.range_high > t.prev_high, t.range_low < t.prev_low).astype(int)
    t["loc_in_prev"] = (t.range_open - t.prev_low) / (t.prev_high - t.prev_low)
    t["is_os"] = pd.Series(t.day).apply(lambda d: d >= OS_START).values
    return t.dropna(subset=["atr14"])

def stat(x):
    if len(x) < 25:
        return None
    w, l = x.pnl_usd[x.pnl_usd > 0].sum(), -x.pnl_usd[x.pnl_usd <= 0].sum()
    return dict(n=len(x), win=round((x.pnl_usd > 0).mean()*100, 1),
                PF=round(w / l, 2) if l > 0 else np.inf, exp=round(x.pnl_usd.mean(), 2))

def report(t, name, groups):
    print(f"\n--- {name} ---")
    print(f"{'bucket':<26} {'IS n':>5} {'IS PF':>6} {'IS win%':>7} {'IS exp$':>8} | {'OS n':>5} {'OS PF':>6} {'OS win%':>7} {'OS exp$':>8}")
    for label, mask in groups:
        i, o = stat(t[mask & ~t.is_os]), stat(t[mask & t.is_os])
        if not i or not o:
            continue
        print(f"{label:<26} {i['n']:>5} {i['PF']:>6} {i['win']:>7} {i['exp']:>8} | "
              f"{o['n']:>5} {o['PF']:>6} {o['win']:>7} {o['exp']:>8}")

for L, anchor in [(30, "london_close"), (15, "london_close"), (30, "london_open")]:
    t = build(L, anchor)
    print("\n" + "=" * 110)
    all_i, all_o = stat(t[~t.is_os]), stat(t[t.is_os])
    print(f"BASE {L}m / {anchor}   IS: n={all_i['n']} PF={all_i['PF']} win={all_i['win']}% exp=${all_i['exp']}"
          f"   |   OS: n={all_o['n']} PF={all_o['PF']} win={all_o['win']}% exp=${all_o['exp']}")
    report(t, "Asia range size vs ATR14", [
        ("narrow  (<0.25x ATR)", t.rng_atr < 0.25),
        ("mid     (0.25-0.45x)", (t.rng_atr >= 0.25) & (t.rng_atr < 0.45)),
        ("wide    (>0.45x ATR)", t.rng_atr >= 0.45)])
    report(t, "trend alignment (EMA20 vs EMA50 of daily closes)", [
        ("with trend", t.trend_align == 1), ("against trend", t.trend_align == 0)])
    report(t, "5-day momentum alignment", [
        ("with momentum", t.mom_align == 1), ("against momentum", t.mom_align == 0)])
    report(t, "prior-day direction alignment", [
        ("with prior day", t.prevdir_align == 1), ("against prior day", t.prevdir_align == 0)])
    report(t, "overnight gap alignment (01:30 open vs prior 21:00 close)", [
        ("with gap", t.gap_align == 1), ("against gap", t.gap_align == 0)])
    report(t, "break also clears prior-day high/low", [
        ("clears prior day", t.clears_prev == 1), ("inside prior day", t.clears_prev == 0)])
    report(t, "volatility regime (ATR percentile, 120d)", [
        ("low vol  (<33%)", t.atr_pct < .33), ("mid vol", (t.atr_pct >= .33) & (t.atr_pct < .66)),
        ("high vol (>66%)", t.atr_pct >= .66)])
    report(t, "day of week", [(n, t.dow == i) for i, n in enumerate("Mon Tue Wed Thu Fri".split())])
    report(t, "direction", [("long only", t.side == 1), ("short only", t.side == -1)])
