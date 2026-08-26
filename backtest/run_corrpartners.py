"""Round 13: alternative correlation partners as regime gates for the Asia breakout.

Pre-registered questions (fixed before any data was gated):
  Q1  Does any partner's 20d correlation gate show a real gradient on ALL breakout
      trades, judged like AUD was: smooth decile gradient, same sign in both halves
      (2020-23 vs 2024-25), honest-OOS (rank on pre-2024 only)?
  Q2  RESCUE: among trades the deployed AUD gate skips (corr_aud > 0.5), does any
      partner identify a tradeable positive-edge subset? This is the only path to
      more frequency.
  Q3  AND: on the deployed set (corr_aud <= 0.5), does a second gate raise per-trade
      quality without gutting n? Only run for partners that pass Q1's gradient look.

Every cell is counted in the multiplicity ledger; the best finding is tested with a
circular-shift max-statistic permutation over the ENTIRE grid.

Convention mirrors deployable.py exactly: gold dailies = broker-EET resample of our
5m closes; partner dailies joined inner; 20d rolling corr of log returns (simple
diff for the 10y yield); calendar-reindexed, ffill, shift(1) so only data through
yesterday gates today. AUD is run as a control and must reproduce the deployed set.
"""
import pandas as pd, numpy as np, engine, trades, json, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

rng = np.random.default_rng(13)
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def met(x):
    if len(x) < 15:
        return dict(n=len(x), pf=np.nan, win=np.nan, exp=np.nan, t=np.nan)
    p = x.pnl_oz / x.entry * 100
    return dict(n=len(x), pf=pf(x.pnl_oz), win=float((x.pnl_oz > 0).mean()),
                exp=float(x.pnl_oz.mean()), t=float(p.mean() / p.std() * np.sqrt(len(p))))

# ---------------------------------------------------------------- daily returns
def fred(path, invert=False):
    d = pd.read_csv(f"data/{path}", index_col=0, parse_dates=True).iloc[:, 0]
    d = pd.to_numeric(d, errors="coerce").dropna()
    if invert:
        d = 1.0 / d
    return np.log(d).diff().dropna()

def av(path, diff_only=False):
    d = pd.read_csv(f"data/{path}", index_col=0, parse_dates=True).iloc[:, 0]
    d = pd.to_numeric(d, errors="coerce").dropna().sort_index()
    return (d.diff() if diff_only else np.log(d).diff()).dropna()

def intraday_daily(path):
    b = pd.read_csv(f"data/{path}", index_col=0, parse_dates=True)
    c = b.close.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").last()
    c = pd.Series(c.values, index=pd.to_datetime([x.date() for x in c.index])).dropna()
    return np.log(c).diff().dropna()

gold = engine.load_bars()
loc = gold.close.tz_convert(ZoneInfo("Europe/Athens"))
gd = loc.resample("1D").last()
gd = pd.Series(gd.values, index=pd.to_datetime([x.date() for x in gd.index])).dropna()
g_ret = np.log(gd).diff().dropna()

fx = {k: fred(f"{f}_daily_fred.csv", inv) for k, f, inv in (
    ("aud", "AUDUSD", False), ("eur", "EURUSD", False), ("gbp", "GBPUSD", False),
    ("jpy", "JPYUSD", True), ("chf", "CHFUSD", True), ("cad", "CADUSD", True),
    ("cny", "CNY", True))}
# synthetic dollar index: DXY weights minus SEK, renormalised; positive = USD up
w = {"eur": .576, "jpy": .136, "gbp": .119, "cad": .091, "chf": .036}
dxy = -sum(fx[k] * v for k, v in w.items()).dropna() / sum(w.values())

partners = dict(fx)
partners["dxy"] = dxy
partners["xag"] = av("SILVER_daily_av.csv")
partners["wti"] = av("WTI_daily_av.csv")
partners["ust10"] = av("UST10Y_daily_av.csv", diff_only=True)
partners["spx"] = intraday_daily("SPX_5m.csv")

def corr_of(p_ret, window=20):
    j = pd.concat([g_ret.rename("g"), p_ret.rename("p")], axis=1, join="inner").dropna()
    return (j.g.rolling(window).corr(j.p)
            .reindex(pd.date_range(j.index.min(), j.index.max(), freq="D"))
            .ffill().shift(1))

C = {k: corr_of(v) for k, v in partners.items()}

# provenance: directions should match known macro relationships
print("provenance (mean 20d corr with gold over trade window):")
for k in partners:
    m = C[k]["2020-09-01":"2025-08-01"].mean()
    print(f"  {k:>6}: {m:+.3f}")

# ---------------------------------------------------------------- trade set
t = trades.generate(gold, 60, stop_r=2.0, entry_cutoff_ldn=8)
t["pnl_oz"] = t.pnl_oz - np.where(t.reason == "stop", 0.30, 0.0)
t["day_n"] = pd.to_datetime(t.day).dt.normalize()
for k in C:
    t[f"c_{k}"] = t.day_n.map(C[k])
t = t.dropna(subset=[f"c_{k}" for k in C]).reset_index(drop=True)
t["os"] = pd.to_datetime(t.day) >= "2024-01-01"

base = met(t)
dep = met(t[t.c_aud <= 0.5])
print(f"\nbase (no gate): n={base['n']} PF {base['pf']:.3f} t {base['t']:+.2f}")
print(f"AUD control  : n={dep['n']} PF {dep['pf']:.3f} t {dep['t']:+.2f}  (deployed: 652 / 1.320 / +2.54)")
assert abs(dep["n"] - 652) <= 6, "AUD control failed to reproduce the deployed set"

THR = [-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.5, 0.6]
ledger = 0
res = {"base": base, "aud_control": dep, "partners": {}, "rescue": {}, "and_gate": {}}

def decile_gradient(x, col):
    q = pd.qcut(x[col], 10, duplicates="drop")
    rows = []
    for iv, grp in x.groupby(q):
        m = met(grp)
        m["lo"], m["hi"] = float(iv.left), float(iv.right)
        rows.append(m)
    return rows

def sweep(x, col):
    global ledger
    cells = []
    for thr in THR:
        for side in ("le", "ge"):
            sub = x[x[col] <= thr] if side == "le" else x[x[col] >= thr]
            m = met(sub)
            m.update(thr=thr, side=side,
                     is_=met(sub[~sub.os]), os_=met(sub[sub.os]))
            cells.append(m)
            ledger += 1
    return cells

# Q1: full set
for k in C:
    res["partners"][k] = dict(grad=decile_gradient(t, f"c_{k}"), sweep=sweep(t, f"c_{k}"))

# Q2: rescue on AUD-skipped days
skip = t[t.c_aud > 0.5].reset_index(drop=True)
res["rescue_base"] = met(skip)
print(f"\nAUD-skipped days: n={res['rescue_base']['n']} PF {res['rescue_base']['pf']:.3f} "
      f"t {res['rescue_base']['t']:+.2f}")
for k in C:
    if k == "aud":
        continue
    res["rescue"][k] = dict(grad=decile_gradient(skip, f"c_{k}"), sweep=sweep(skip, f"c_{k}"))

# ---------------------------------------------------------------- max-stat permutation
# statistic: best gated |t| improvement over its own base across ALL Q1+Q2 cells.
def best_stat(frame_pairs):
    best = -np.inf
    for x, basemean in frame_pairs:
        for k in C:
            col = x[f"c_{k}"]
            for thr in THR:
                for side in ("le", "ge"):
                    sub = x[col <= thr] if side == "le" else x[col >= thr]
                    if len(sub) < 40:
                        continue
                    p = sub.pnl_oz / sub.entry * 100
                    tt = p.mean() / p.std() * np.sqrt(len(p))
                    if np.isfinite(tt):
                        best = max(best, tt)
    return best

obs = best_stat([(t, None), (skip, None)])
perm = []
days = pd.date_range(t.day_n.min() - pd.Timedelta(days=40), t.day_n.max(), freq="D")
for i in range(300):
    tp = t.copy()
    sp = None
    for k in C:
        ser = C[k].reindex(days).ffill()
        shift = int(rng.integers(60, len(ser) - 60))
        rolled = pd.Series(np.roll(ser.values, shift), index=ser.index)
        tp[f"c_{k}"] = tp.day_n.map(rolled)
    tp = tp.dropna(subset=[f"c_{k}" for k in C])
    sp = tp[tp.c_aud > 0.5]          # rescue frame under the permuted aud gate
    perm.append(best_stat([(tp, None), (sp, None)]))
p_max = float((np.array(perm) >= obs).mean())
res["maxstat"] = dict(observed=float(obs), n_perm=len(perm), p=p_max,
                      perm_p50=float(np.median(perm)), perm_p95=float(np.percentile(perm, 95)))
res["ledger_cells"] = ledger
print(f"\nmax-stat: observed best t {obs:+.2f}, perm median {np.median(perm):+.2f}, "
      f"p95 {np.percentile(perm, 95):+.2f}, p = {p_max:.3f}  ({ledger} cells)")

json.dump(res, open("results/corrpartners.json", "w"), indent=1, default=str)
print("written results/corrpartners.json")
