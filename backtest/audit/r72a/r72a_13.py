"""Round 72A step 3, attempt 13 (r42m_corrny) reversed scoring, IN-SAMPLE ONLY.
Data build copied verbatim from backtest/run_r42m_corrny.py; every statistic below is
computed on rows with oos == False (dates strictly before the runner's own cut).
Reversed cell = FOLLOW London move (+sign) in high-corr (corr > 0.5) regime, 09:30->12:00.
Costs 0.35/RT (runner COST) subtracted at 1x / 1.5x / 2x. Run from backtest/."""
import pandas as pd, numpy as np, warnings, sys, os
sys.path.insert(0, os.getcwd())
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST = 0.35

b = load_frame("GOLD")
gd = b.groupby("skey").close.last()
gd.index = pd.to_datetime(pd.Series(gd.index).astype(str))
a = pd.read_csv("data/AUDUSD_daily_fred.csv")
ad = pd.Series(pd.to_numeric(a.iloc[:, 1], errors="coerce").values,
               index=pd.to_datetime(a.iloc[:, 0])).dropna()
common = gd.index.intersection(ad.index)
rg, ra = np.log(gd[common]).diff(), np.log(ad[common]).diff()
corr = rg.rolling(20).corr(ra).shift(1)
corr_by_date = {d.date(): v for d, v in corr.items()}

rows_d = []
for skey, g in b.groupby("skey"):
    hm = g.hm.values
    c, o = g.close.values, g.open.values
    def px(t0, t1):
        m = (hm >= t0) & (hm < t1)
        if m.sum() < 5: return np.nan, np.nan
        return o[np.argmax(m)], c[len(m) - 1 - np.argmax(m[::-1])]
    lo_, lc = px(300, 800)
    no, _ = px(930, 1000)
    _, c12 = px(930, 1200)
    _, c16 = px(930, 1600)
    # placebo (shifted clock): Asia-session move 20:00->01:00 ET instead of London
    ao, ac = px(2000, 2400)
    rows_d.append(dict(skey=skey, lmove=(lc - lo_) if np.isfinite(lo_) else np.nan,
                       amove=(ac - ao) if np.isfinite(ao) else np.nan,
                       e=no, c12=c12, c16=c16, hi=g.high.max(), lo=g.low.min()))
d = pd.DataFrame(rows_d).set_index("skey")
d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
d["creg"] = pd.to_numeric(pd.Series(d.index.map(lambda k: corr_by_date.get(k, np.nan)),
                                    index=d.index), errors="coerce")
for col in ("creg", "atr20", "lmove", "amove", "e", "c12", "c16"):
    d[col] = pd.to_numeric(d[col], errors="coerce")
d = d[np.isfinite(d.creg) & np.isfinite(d.atr20) & (d.atr20 > 0) & np.isfinite(d.lmove) & np.isfinite(d.e)]
cutd = d.index.tolist()[int(len(d) * 0.75)]
d["oos"] = d.index >= cutd
print(f"GOLD: {len(d)} sessions total (runner count); IS CUT DATE = {cutd}; OOS rows DROPPED now.")
# ---- OOS FIREWALL: everything below uses IS only -------------------------------
d = d[~d.oos].copy()
print(f"IS sessions: {len(d)}  ({d.index.min()} .. {d.index.max()})")
assert d.index.max() < cutd
# lag columns (placebo) computed on IS rows only (lags within IS never look past the cut)
d["lmove_lag1"] = d.lmove.shift(1)
d["creg_lag60"] = d.creg.shift(60)
d["year"] = [k.year for k in d.index]

def stats(r, yrs=None):
    r = np.asarray(r, float); ok = np.isfinite(r); r = r[ok]
    if len(r) < 10: return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]; m = len(r) // 2
    out = dict(n=int(len(r)), avgR=float(r.mean()),
               t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else np.nan,
               wr=float((r > 0).mean()),
               pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
               halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])
    if yrs is not None:
        yrs = np.asarray(yrs)[ok]
        out["per_year"] = {int(y): (int((yrs == y).sum()), float(r[yrs == y].mean())) for y in sorted(set(yrs))}
    return out

def welch(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x[np.isfinite(x)], y[np.isfinite(y)]
    se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    return float(x.mean() - y.mean()), float((x.mean() - y.mean()) / se)

def R(mask, side, xcol="c12", k=1.0):
    """net R for sessions in mask, side = +1/-1 per session, cost multiple k."""
    pnl = side[mask] * (d[xcol][mask] - d.e[mask]) - k * COST
    return pnl / d.atr20[mask]

follow = np.sign(d.lmove)               # +sign(London move) = FOLLOW = reversed direction
elig = (follow != 0) & np.isfinite(d.c12)
hi, lo = (d.creg > 0.5), (d.creg <= 0.5)

print("\n=== REVERSED CELL: highcorr / any / 09:30-12:00, FOLLOW London (IS, net) ===")
cell = hi & elig
res = {}
for k in (1.0, 1.5, 2.0):
    s = stats(R(cell, follow, "c12", k), d.year[cell]); res[k] = s
    print(f"cost x{k}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f} WR {s['wr']*100:.1f}% PF {s['pf']:.3f} halves {s['halves']}")
print("per-year (n, mean R) at 1x:", res[1.0]["per_year"])
# sanity: registered (fade) cell at 1x must reproduce JSON grid[4]
sreg = stats(R(cell, -follow, "c12", 1.0))
print(f"check registered FADE cell at 1x: n {sreg['n']} avgR {sreg['avgR']:+.4f} t {sreg['t']:+.3f} (JSON: 401, -0.0425, -2.0047)")
sgross = stats(R(cell, follow, "c12", 0.0))
print(f"reversed GROSS (0x cost): avgR {sgross['avgR']:+.4f} t {sgross['t']:+.3f}")

print("\n=== UNCONDITIONAL CONTROLS (IS, 1x cost, 09:30-12:00) ===")
ctl_all = R(elig, follow, "c12", 1.0)                       # follow London on ALL eligible days
s_all = stats(ctl_all, d.year[elig]); print(f"follow-London ALL days: n {s_all['n']} avgR {s_all['avgR']:+.4f} t {s_all['t']:+.3f} halves {s_all['halves']}")
ctl_lo = R(lo & elig, follow, "c12", 1.0)                   # complement (low-corr follow) - disjoint
s_lo = stats(ctl_lo); print(f"follow-London LOW-corr days (disjoint complement): n {s_lo['n']} avgR {s_lo['avgR']:+.4f} t {s_lo['t']:+.3f}")
one = pd.Series(1.0, index=d.index)
allwin = np.isfinite(d.c12)
for nm, sd in (("always-LONG", one), ("always-SHORT", -one)):
    sa = stats(R(allwin, sd, "c12", 1.0)); sh = stats(R(hi & allwin, sd, "c12", 1.0))
    print(f"{nm} 09:30-12:00: ALL days n {sa['n']} avgR {sa['avgR']:+.4f} t {sa['t']:+.3f} | high-corr days n {sh['n']} avgR {sh['avgR']:+.4f} t {sh['t']:+.3f}")
cellR = R(cell, follow, "c12", 1.0)
dm, dt = welch(cellR, ctl_all); print(f"DIFF reversed cell - follow-ALL control: avgR {dm:+.4f}, Welch t {dt:+.3f} (cell is a subset of control; overlap ignored)")
dm2, dt2 = welch(cellR, ctl_lo); print(f"DIFF reversed cell - low-corr complement (disjoint Welch): avgR {dm2:+.4f}, t {dt2:+.3f}")
shi_long = R(cell, one, "c12", 1.0)
dm3, dt3 = welch(cellR, shi_long); print(f"DIFF reversed cell - always-LONG same days: avgR {dm3:+.4f}, t {dt3:+.3f}")

print("\n=== GRADIENT (reversed = FOLLOW London, IS, 1x net) ===")
print("-- family's own grid, high-corr regime, reversed:")
for th in (None, 0.25):
    for xcol in ("c12", "c16"):
        m = hi & (follow != 0) & np.isfinite(d[xcol])
        if th is not None: m &= d.lmove.abs() >= th * d.atr20
        s = stats(R(m, follow, xcol, 1.0)); print(f"  highcorr th={th or 'any'} hold={xcol}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f} halves {s['halves']}")
print("-- corr-threshold ladder (corr > c), any move, 09:30-12:00, FOLLOW:")
for cth in (-1.0, 0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    m = (d.creg > cth) & elig; s = stats(R(m, follow, "c12", 1.0))
    print(f"  corr>{cth:+.1f}: n {s.get('n')} avgR {s.get('avgR', float('nan')):+.4f} t {s.get('t', float('nan')):+.3f}")
print("-- corr band ladder (disjoint bins), FOLLOW 09:30-12:00:")
for a_, b_ in ((-1, 0.0), (0.0, 0.25), (0.25, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)):
    m = (d.creg > a_) & (d.creg <= b_) & elig; s = stats(R(m, follow, "c12", 1.0))
    print(f"  corr in ({a_},{b_}]: n {s.get('n')} avgR {s.get('avgR', float('nan')):+.4f} t {s.get('t', float('nan')):+.3f}")
print("-- |London move|/ATR20 threshold ladder, high-corr, FOLLOW 09:30-12:00:")
for th in (0.0, 0.1, 0.2, 0.25, 0.35, 0.5):
    m = hi & elig & (d.lmove.abs() >= th * d.atr20); s = stats(R(m, follow, "c12", 1.0))
    print(f"  |move|>={th}ATR: n {s.get('n')} avgR {s.get('avgR', float('nan')):+.4f} t {s.get('t', float('nan')):+.3f}")
print("-- sub-threshold band |move| < 0.25 ATR, high-corr, FOLLOW:")
m = hi & elig & (d.lmove.abs() < 0.25 * d.atr20); s = stats(R(m, follow, "c12", 1.0))
print(f"  n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f} halves {s['halves']}")

print("\n=== PLACEBOS (reversed, IS, 1x net) ===")
f1 = np.sign(d.lmove_lag1); m = hi & (f1 != 0) & np.isfinite(d.c12) & np.isfinite(f1)
s = stats(R(m, f1, "c12", 1.0)); print(f"day-shift: follow YESTERDAY's London move, high-corr: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f}")
h60 = (d.creg_lag60 > 0.5); m = h60 & elig
s = stats(R(m, follow, "c12", 1.0)); print(f"regime clock-shift: corr regime lagged 60 sessions, follow London: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f}")
fa = np.sign(d.amove); m = hi & (fa != 0) & np.isfinite(d.c12) & np.isfinite(fa)
s = stats(R(m, fa, "c12", 1.0)); print(f"clock-shift: follow ASIA 20:00-24:00 ET move instead of London, high-corr: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.3f}")
