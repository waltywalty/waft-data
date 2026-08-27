"""Round 27B: gold/dollar as lag-1 signals for equity futures. Pre-registered.

Signals (all from closed data through day D-1): gold 1d/5d return sign,
synthetic-DXY 1d return sign, DXY 20d trend sign, gold/AUD 20d corr <= 0.5,
gold-SPX 20d corr median split. Targets: day D close-to-close and NY-session
(09:30->16:00 ET) returns on SPX/NDX/RTY. Two-sample t, max-stat over all 36
cells with a shared circular day shift.
"""
import pandas as pd, numpy as np, json, warnings, index_data
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")
rng = np.random.default_rng(27)
NY = ZoneInfo("America/New_York")

# ---------------- gold spliced daily (r24 construction) + FX dailies
ej = pd.read_csv("data/XAUUSD_m15_ejtrader.csv"); ej = ej[ej.Date != "Date"]
ej["close"] = pd.to_numeric(ej.close, errors="coerce")
ej["ts"] = pd.to_datetime(ej.Date, errors="coerce")
ej = ej.dropna(subset=["close", "ts"]).set_index("ts").sort_index()
ej.index = (ej.index.tz_localize(ZoneInfo("Europe/Athens"), nonexistent="shift_forward",
                                 ambiguous="NaT").tz_convert("UTC"))
ej = ej[ej.index.notna()]
ej_d = (ej.close / 100.0).resample("1D").last().dropna()
h1 = pd.read_csv("data/XAUUSD_H1_collector.csv", parse_dates=["datetime"]).set_index("datetime").sort_index()
h1_d = h1.close.resample("1D").last().dropna()
gold_d = pd.concat([ej_d[ej_d.index < h1_d.index.min()], h1_d]).sort_index()
gold_d.index = gold_d.index.tz_localize(None).normalize()
g_ret = np.log(gold_d).diff()

def fred(path, col):
    d = pd.read_csv(f"data/{path}", parse_dates=["observation_date"])
    s = pd.to_numeric(d.set_index("observation_date").iloc[:, 0], errors="coerce").dropna()
    return np.log(s).diff()

fx = {k: fred(f"{f}_daily_fred.csv", k) for k, f in
      (("eur", "EURUSD"), ("gbp", "GBPUSD"), ("jpy", "JPYUSD"),
       ("chf", "CHFUSD"), ("cad", "CADUSD"), ("aud", "AUDUSD"))}
w = {"eur": .576, "jpy": .136, "gbp": .119, "cad": .091, "chf": .036}
dxy_ret = -sum(fx[k] * v for k, v in w.items()).dropna() / sum(w.values())
dxy_lvl = dxy_ret.cumsum()

corr_aud = (pd.concat([g_ret.rename("g"), fx["aud"].rename("a")], axis=1, join="inner")
            .dropna().g.rolling(20).corr(
            pd.concat([g_ret.rename("g"), fx["aud"].rename("a")], axis=1, join="inner").dropna().a))

# ---------------- index daily frames from the 5m feeds
def idx_frames(mkt):
    b = index_data.load(mkt)
    et = b.index.tz_convert(NY)
    day = pd.Series(et.date, index=b.index)
    c_by_day = b.close.groupby(day.values).last()
    c_by_day.index = pd.to_datetime(c_by_day.index)
    cc = np.log(c_by_day).diff()
    mins = et.hour * 60 + et.minute
    rth = b[(mins >= 570) & (mins < 960)]
    et2 = rth.index.tz_convert(NY)
    day2 = pd.Series(et2.date, index=rth.index)
    o = rth.open.groupby(day2.values).first(); c = rth.close.groupby(day2.values).last()
    sess = np.log(pd.Series(c.values, index=pd.to_datetime(c.index)) /
                  pd.Series(o.values, index=pd.to_datetime(o.index)))
    return cc.dropna(), sess.dropna()

IDX = {m: idx_frames(m) for m in ("SPX", "NDX", "RTY")}
spx_cc = IDX["SPX"][0]
corr_gspx = (pd.concat([g_ret.rename("g"), spx_cc.rename("s")], axis=1, join="inner")
             .dropna().g.rolling(20).corr(
             pd.concat([g_ret.rename("g"), spx_cc.rename("s")], axis=1, join="inner").dropna().s))

SIGNALS = {
    "gold_1d": np.sign(g_ret),
    "gold_5d": np.sign(g_ret.rolling(5).sum()),
    "dxy_1d": np.sign(dxy_ret),
    "dxy_trend20": np.sign(dxy_lvl - dxy_lvl.rolling(20).mean()),
    "corr_gate": (corr_aud <= 0.5).astype(float) * 2 - 1,          # +1 in-state
    "gspx_corr": (corr_gspx > corr_gspx.expanding().median()).astype(float) * 2 - 1,
}
SIGNALS = {k: s.shift(1).dropna() for k, s in SIGNALS.items()}      # lag 1: usable day D

def t2(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 50 or len(b) < 50:
        return np.nan, len(a), len(b)
    return (float((a.mean() - b.mean()) /
                  np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))), len(a), len(b))

START = pd.Timestamp("2012-06-01")
SPLIT = pd.Timestamp("2019-01-01")
out, cells = {}, {}
for sk, sig in SIGNALS.items():
    for mkt in ("SPX", "NDX", "RTY"):
        for ti, tk in ((0, "cc"), (1, "sess")):
            tgt = IDX[mkt][ti]
            j = pd.concat([sig.rename("s"), tgt.rename("r")], axis=1, join="inner").dropna()
            j = j[j.index >= START]
            up, dn = j[j.s > 0].r * 1e4, j[j.s < 0].r * 1e4
            tt, nu, nd = t2(up, dn)
            rec = dict(t2=tt, n_up=nu, n_dn=nd,
                       up_bps=float(up.mean()), dn_bps=float(dn.mean()))
            for nm, m in (("h1", j.index < SPLIT), ("h2", j.index >= SPLIT)):
                rec[nm] = t2(j[m & (j.s > 0)].r * 1e4, j[m & (j.s < 0)].r * 1e4)[0]
            cells[f"{sk}_{mkt}_{tk}"] = rec
out["cells"] = cells

# max-stat: shared circular shift of all signal series (in days)
all_days = sorted(set().union(*[set(s.index) for s in SIGNALS.values()]))
day_ix = {d: i for i, d in enumerate(all_days)}
sig_arr = {k: pd.Series(s.reindex(all_days).values, index=all_days) for k, s in SIGNALS.items()}

def max_abs_t(sigs):
    best = 0.0
    for sk, sig in sigs.items():
        for mkt in ("SPX", "NDX", "RTY"):
            for ti in (0, 1):
                tgt = IDX[mkt][ti]
                j = pd.concat([sig.rename("s"), tgt.rename("r")], axis=1, join="inner").dropna()
                j = j[j.index >= START]
                v = t2(j[j.s > 0].r, j[j.s < 0].r)[0]
                if v == v:
                    best = max(best, abs(v))
    return best

obs = max_abs_t(sig_arr)
NPERM = 300
perm = np.empty(NPERM)
n_all = len(all_days)
for i in range(NPERM):
    sh = rng.integers(30, n_all - 30)
    shifted = {k: pd.Series(np.roll(s.values, sh), index=all_days) for k, s in sig_arr.items()}
    perm[i] = max_abs_t(shifted)
out["maxstat"] = dict(observed=float(obs), p=float((perm >= obs).mean()),
                      n_cells=36, n_perm=NPERM)

json.dump(out, open("results/r27b_inversion.json", "w"), indent=1, default=float)

print("=== GOLD/DOLLAR LAG-1 SIGNALS -> EQUITY FUTURES (two-sample t, up vs down state) ===")
for k, v in cells.items():
    flag = " *" if v["t2"] == v["t2"] and abs(v["t2"]) > 2 else ""
    print(f"  {k:>26}: t2 {v['t2'] if v['t2']==v['t2'] else 0:+.2f}  "
          f"up {v['up_bps']:+.1f} (n={v['n_up']}) dn {v['dn_bps']:+.1f} (n={v['n_dn']})  "
          f"halves {v['h1'] if v['h1']==v['h1'] else 0:+.2f}/{v['h2'] if v['h2']==v['h2'] else 0:+.2f}{flag}")
print(f"\nmax-stat over 36 cells: observed |t| {obs:.2f}, p = {out['maxstat']['p']:.3f}")
