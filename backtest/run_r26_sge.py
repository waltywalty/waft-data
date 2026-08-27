"""Round 26: the SGE auction-window battery. Pre-registered in the goal ledger.

Windows (UTC, from the round-17 session verification): SGE AM benchmark
auction 02:15; deployed opening range 01:30-02:30; day exit 16:00 New York.
"""
import pandas as pd, numpy as np, json, warnings, engine, trades
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")
rng = np.random.default_rng(26)

gold = engine.load_bars()
cd = trades.corr_series(gold, 20)
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

# ---------------------------------------------------------------- per-day frame
rows = []
for day, bars in gold.groupby(gold.index.date):
    d = pd.Timestamp(day)
    ts = lambda h, m: pd.Timestamp(d.year, d.month, d.day, h, m, tz="UTC")
    ny = pd.Timestamp(d.year, d.month, d.day, 16, 0,
                      tz=ZoneInfo("America/New_York")).tz_convert("UTC")
    def px(t):
        i = bars.index.searchsorted(t)
        return float(bars.close.iloc[i - 1]) if 0 < i <= len(bars) else np.nan
    def candle(t0, t1):
        w = bars.loc[t0:t1 - pd.Timedelta(seconds=1)]
        return (float(w.open.iloc[0]), float(w.close.iloc[-1])) if len(w) else (np.nan, np.nan)
    a5o, a5c = candle(ts(2, 15), ts(2, 20))
    a15o, a15c = candle(ts(2, 15), ts(2, 30))
    o5o, o5c = candle(ts(1, 30), ts(1, 35))
    o15o, o15c = candle(ts(1, 30), ts(1, 45))
    hr = bars.loc[ts(2, 15):ts(3, 15) - pd.Timedelta(seconds=1)]
    ctl = bars.loc[ts(3, 15):ts(4, 15) - pd.Timedelta(seconds=1)]
    rows.append(dict(
        day=d, a5=np.sign(a5c - a5o), a15=np.sign(a15c - a15o),
        o5=np.sign(o5c - o5o), o15=np.sign(o15c - o15o),
        p_0230=px(ts(2, 30)), p_ldn=px(ts(8, 0)), p_ny=px(ny),
        auc_hi=float(hr.high.max()) if len(hr) > 8 else np.nan,
        auc_lo=float(hr.low.min()) if len(hr) > 8 else np.nan,
        ctl_hi=float(ctl.high.max()) if len(ctl) > 8 else np.nan,
        ctl_lo=float(ctl.low.min()) if len(ctl) > 8 else np.nan,
        base=a5c))
F = pd.DataFrame(rows).set_index("day")
F["corr"] = F.index.map(cd)
F["fwd_ny"] = (F.p_ny - F.base) / F.base * 1e4      # bps from auction candle close
F["fwd_ldn"] = (F.p_ldn - F.base) / F.base * 1e4
print(f"days: {len(F)}; auction candle available on {F.a5.notna().mean()*100:.0f}%")

def t2(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 30 or len(b) < 30:
        return np.nan, len(a), len(b)
    return (float((a.mean() - b.mean()) /
                  np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))), len(a), len(b))

out = {}

# ---------------- A: auction-candle sign vs forward return (4 cells)
A = {}
for cnd in ("a5", "a15"):
    for tgt in ("fwd_ny", "fwd_ldn"):
        up, dn = F[F[cnd] > 0][tgt], F[F[cnd] < 0][tgt]
        tt, na, nb = t2(up, dn)
        A[f"{cnd}_{tgt}"] = dict(t2=tt, n_up=na, n_dn=nb,
                                 mean_up_bps=float(up.mean()), mean_dn_bps=float(dn.mean()))
        # halves
        for nm, m in (("h1", F.index < "2024-01-01"), ("h2", F.index >= "2024-01-01")):
            u, dnn = F[m & (F[cnd] > 0)][tgt], F[m & (F[cnd] < 0)][tgt]
            A[f"{cnd}_{tgt}"][nm] = t2(u, dnn)[0]
out["A_auction_candle"] = A

# ---------------- B: agreement of 09:30 open candle with auction candle (4 cells)
B = {}
for oc, ac in (("o5", "a5"), ("o15", "a15")):
    agree = (F[oc] * F[ac]) > 0
    valid = (F[oc] != 0) & (F[ac] != 0) & F[oc].notna() & F[ac].notna()
    for tgt in ("fwd_ny", "fwd_ldn"):
        # directional read: forward return in the direction of the OPEN candle,
        # agreement days vs disagreement days
        dirret = F[tgt] * F[oc]
        ag, dis = dirret[valid & agree], dirret[valid & ~agree]
        tt, na, nb = t2(ag, dis)
        B[f"{oc}x{ac}_{tgt}"] = dict(t2=tt, n_agree=na, n_dis=nb,
                                     mean_agree_bps=float(ag.mean()),
                                     mean_dis_bps=float(dis.mean()))
        for nm, m in (("h1", F.index < "2024-01-01"), ("h2", F.index >= "2024-01-01")):
            B[f"{oc}x{ac}_{tgt}"][nm] = t2(dirret[m & valid & agree], dirret[m & valid & ~agree])[0]
out["B_agreement"] = B

# ---------------- C: auction-hour range as value zone (2 trade cells + control)
def fade_range(hi_col, lo_col, t_start_h, t_start_m):
    trades_out = []
    for day, r in F.iterrows():
        hi, lo = r[hi_col], r[lo_col]
        if not np.isfinite(hi) or not np.isfinite(lo) or hi <= lo:
            continue
        mid, w = (hi + lo) / 2, hi - lo
        t0 = pd.Timestamp(day.year, day.month, day.day, t_start_h, t_start_m, tz="UTC")
        ny = pd.Timestamp(day.year, day.month, day.day, 16, 0,
                          tz=ZoneInfo("America/New_York")).tz_convert("UTC")
        path = gold.loc[t0:ny]
        if len(path) < 10:
            continue
        pos = None
        for bar in path.itertuples():
            if pos is None:
                if bar.high >= hi:
                    pos = (-1, hi, hi + 0.5 * w, bar.Index)   # short the high edge
                elif bar.low <= lo:
                    pos = (1, lo, lo - 0.5 * w, bar.Index)    # long the low edge
                continue
            side, entry, stop, t_in = pos
            if (side < 0 and bar.high >= stop) or (side > 0 and bar.low <= stop):
                pnl = side * (stop - entry) - 0.60
                trades_out.append(dict(day=day, side=side, pnl=pnl, entry=entry)); pos = None; break
            if (side < 0 and bar.low <= mid) or (side > 0 and bar.high >= mid):
                pnl = side * (mid - entry) - 0.30
                trades_out.append(dict(day=day, side=side, pnl=pnl, entry=entry)); pos = None; break
        if pos is not None:
            side, entry, stop, t_in = pos
            pnl = side * (float(path.close.iloc[-1]) - entry) - 0.30
            trades_out.append(dict(day=day, side=side, pnl=pnl, entry=entry))
    return pd.DataFrame(trades_out)

C = {}
for nm, hi_c, lo_c, hh, mm in (("auction", "auc_hi", "auc_lo", 3, 15),
                               ("control", "ctl_hi", "ctl_lo", 4, 15)):
    tr = fade_range(hi_c, lo_c, hh, mm)
    p = tr.pnl / tr.entry * 100
    d = dict(n=len(tr), pf=pf(tr.pnl), exp=float(tr.pnl.mean()),
             t=float(p.mean() / p.std() * np.sqrt(len(p))),
             win=float((tr.pnl > 0).mean()))
    for lbl, m in (("h1", pd.to_datetime(tr.day) < "2024-01-01"),
                   ("h2", pd.to_datetime(tr.day) >= "2024-01-01")):
        x = tr[m]
        d[lbl] = dict(n=len(x), pf=pf(x.pnl), exp=float(x.pnl.mean()))
    C[nm] = d
out["C_value_zone"] = C

# ---------------- overlap of the auction candle with the deployed signal
t60 = trades.generate(gold, 60, stop_r=2.0, entry_cutoff_ldn=8)
t60["day_ts"] = pd.to_datetime(t60.day)
j = t60.set_index("day_ts").join(F[["a5", "a15"]], how="inner")
overlap = float((np.sign(j.side) == j.a15).mean())
out["overlap_auction15_vs_breakout_dir"] = overlap

# ---------------- max-stat over the 10 counted cells (shared circular shift)
days_arr = F.index.values
def all_cells_stat(Fx):
    stats = []
    for cnd in ("a5", "a15"):
        for tgt in ("fwd_ny", "fwd_ldn"):
            v = t2(Fx[Fx[cnd] > 0][tgt], Fx[Fx[cnd] < 0][tgt])[0]
            if v == v: stats.append(abs(v))
    for oc, ac in (("o5", "a5"), ("o15", "a15")):
        valid = (Fx[oc] != 0) & (Fx[ac] != 0) & Fx[oc].notna() & Fx[ac].notna()
        agree = (Fx[oc] * Fx[ac]) > 0
        for tgt in ("fwd_ny", "fwd_ldn"):
            dirret = Fx[tgt] * Fx[oc]
            v = t2(dirret[valid & agree], dirret[valid & ~agree])[0]
            if v == v: stats.append(abs(v))
    return max(stats) if stats else 0.0

obs = all_cells_stat(F)
NPERM = 500
perm = np.empty(NPERM)
sig_cols = ["a5", "a15", "o5", "o15"]
for i in range(NPERM):
    sh = rng.integers(20, len(F) - 20)
    Fx = F.copy()
    Fx[sig_cols] = np.roll(F[sig_cols].values, sh, axis=0)
    perm[i] = all_cells_stat(Fx)
out["maxstat_AB"] = dict(observed=float(obs), p=float((perm >= obs).mean()),
                         n_cells=8, n_perm=NPERM)

json.dump(out, open("results/r26_sge.json", "w"), indent=1, default=float)

# ---------------- print
print("\n=== A: AUCTION-CANDLE SIGN vs FORWARD RETURN (two-sample t, up vs down days) ===")
for k, v in A.items():
    print(f"  {k:>13}: t2 {v['t2']:+.2f}  up {v['mean_up_bps']:+.1f}bps (n={v['n_up']}) "
          f"dn {v['mean_dn_bps']:+.1f}bps (n={v['n_dn']})  halves {v['h1']:+.2f} / {v['h2']:+.2f}")
print("\n=== B: OPEN-CANDLE DIRECTION, AGREEMENT vs DISAGREEMENT WITH AUCTION CANDLE ===")
for k, v in B.items():
    print(f"  {k:>16}: t2 {v['t2']:+.2f}  agree {v['mean_agree_bps']:+.1f}bps (n={v['n_agree']}) "
          f"dis {v['mean_dis_bps']:+.1f}bps (n={v['n_dis']})  halves {v['h1']:+.2f} / {v['h2']:+.2f}")
print("\n=== C: FADE THE HOUR-RANGE EDGES, TARGET MID (net) ===")
for nm, d in C.items():
    print(f"  {nm:>8}: n={d['n']:>4} PF {d['pf']:.3f} exp ${d['exp']:+.2f} t {d['t']:+.2f} "
          f"win {d['win']*100:.0f}%  h1 PF {d['h1']['pf']:.3f} / h2 PF {d['h2']['pf']:.3f}")
print(f"\nauction 15m candle matches deployed breakout direction on {overlap*100:.0f}% of trade days")
print(f"max-stat A+B: observed |t2| {obs:.2f}, p = {out['maxstat_AB']['p']:.3f}")
