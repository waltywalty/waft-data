"""Round 35a: gold/DXY positive-correlation divergence (user hypothesis).
Frozen per pre-registration in reference/goal_ledger.md.
Outputs results/r35_divergence.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")


def load_ej(name, scale=1.0):
    df = pd.read_csv(f"data/{name}")
    ts = pd.to_datetime(df.iloc[:, 0]).dt.tz_localize("Europe/Athens", ambiguous="NaT",
                                                      nonexistent="NaT").dt.tz_convert("UTC")
    s = pd.Series(df.close.values / scale, index=ts)
    return s[~s.index.isna()][~s.index.duplicated()].sort_index()


g = load_ej("XAUUSD_m15_ejtrader.csv", 100.0)
e = load_ej("EURUSD_m15_ejtrader.csv")
j = load_ej("USDJPY_m15_ejtrader.csv")
# scale sanity: EURUSD ~1.x, USDJPY ~1xx; auto-descale if the feed is x1e5-style
if e.median() > 100:
    e = e / 1e5
if j.median() > 1000:
    j = j / 100

idx = g.index.intersection(e.index).intersection(j.index)
g, e, j = g[idx], e[idx], j[idx]
rg = np.log(g).diff()
rdxy = 0.809 * (-np.log(e).diff()) + 0.191 * np.log(j).diff()

W_CORR, W_TREND, W_FLIP = 24, 8, 2
corr = rg.rolling(W_CORR).corr(rdxy)
tg = np.log(g).diff(W_TREND)          # gold 8-bar move
td = pd.Series(rdxy).rolling(W_TREND).sum()
fd = pd.Series(rdxy).rolling(W_FLIP).sum()   # DXY 2-bar move


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))] if m > 5 else [np.nan, np.nan]


out = {"span": f"{idx[0]:%Y-%m-%d}..{idx[-1]:%Y-%m-%d}", "n_bars": int(len(idx))}
for cth in (0.3, 0.5):
    regime = corr >= cth
    for dname, dsign in (("down", -1), ("up", 1)):
        shared = regime & (np.sign(tg) == dsign) & (np.sign(td) == dsign)
        ev_mask = shared & (np.sign(fd) == -dsign)      # DXY flips against the move
        cv_mask = shared & (np.sign(fd) == dsign)       # DXY still with the move
        for hb, hn in ((4, "1h"), (16, "4h")):
            fwd = np.log(g).diff(hb).shift(-hb) * dsign  # gold continuation, claim dir
            evv = fwd[ev_mask].dropna()
            cvv = fwd[cv_mask].dropna()
            out[f"corr>={cth} {dname} {hn}"] = dict(
                n=int(len(evv)), ev_bps=float(evv.mean() * 1e4),
                ctrl_bps=float(cvv.mean() * 1e4), t=welch(evv, cvv),
                halves=halves(evv.values))

json.dump(out, open("results/r35_divergence.json", "w"), indent=1, default=float)
print(f"span {out['span']}  bars {out['n_bars']:,}  regime share corr>=0.3: {float((corr>=0.3).mean())*100:.1f}%")
print(f"{'cell':>22} {'n':>6} {'event':>8} {'control':>8} {'t(diff)':>8} {'halves':>14}")
for k, v in out.items():
    if isinstance(v, dict):
        print(f"{k:>22} {v['n']:>6} {v['ev_bps']:>+7.1f}b {v['ctrl_bps']:>+7.1f}b {v['t']:>+8.2f} {str(v['halves']):>14}")
