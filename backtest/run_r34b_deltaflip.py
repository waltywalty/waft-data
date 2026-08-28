"""Round 34b: test of the user's delta-flip hypothesis (see pre-registration
in reference/goal_ledger.md). Event: red 15m candle with POSITIVE sub-bar
delta proxy after a falling 8-bar stretch -> long flip (mirror short).
Outputs results/r34b_deltaflip.json."""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))] if m > 5 else [np.nan, np.nan]


out = {}
for idx in ("SPX", "NDX", "RTY"):
    b = index_data.load(idx).tz_convert("America/New_York")["2010":]
    b = b[b.index.dayofweek < 5].copy()
    b["sdelta"] = np.sign(b.close - b.open) * b.volume
    q = b.resample("15min").agg(open=("open", "first"), high=("high", "max"),
                                low=("low", "min"), close=("close", "last"),
                                delta=("sdelta", "sum")).dropna(subset=["open"])
    q["skey"] = (q.index + pd.Timedelta(hours=8)).date
    ret = q.close / q.open - 1
    prior8 = q.close.pct_change(8).shift(0)          # trailing 8-bar move up to this bar's close
    red, green = q.close < q.open, q.close > q.open
    dpos, dneg = q.delta > 0, q.delta <= 0
    res = {}
    for horizon, hb in (("1h", 4), ("3h", 12)):
        fwd = q.close.shift(-hb) / q.close - 1
        same = q.skey.values == pd.Series(q.skey).shift(-hb).values
        f = fwd.where(same)
        for cond, cname in ((prior8 < 0, "after selloff"), (pd.Series(True, index=q.index), "any")):
            evL = f[red & dpos & cond].dropna()          # user's long flip
            cvL = f[red & dneg & cond].dropna()          # ordinary red bar
            res[f"long {cname} {horizon}"] = dict(
                n=int(len(evL)), ev_bps=float(evL.mean() * 1e4), ctrl_bps=float(cvL.mean() * 1e4),
                t=welch(evL, cvL), halves=halves(evL.values))
        # mirror short: green candle, negative delta, after rally
        for cond, cname in ((prior8 > 0, "after rally"), (pd.Series(True, index=q.index), "any")):
            evS = (-f)[green & (q.delta < 0) & cond].dropna()
            cvS = (-f)[green & (q.delta >= 0) & cond].dropna()
            res[f"short {cname} {horizon}"] = dict(
                n=int(len(evS)), ev_bps=float(evS.mean() * 1e4), ctrl_bps=float(cvS.mean() * 1e4),
                t=welch(evS, cvS), halves=halves(evS.values))
    out[idx] = res

json.dump(out, open("results/r34b_deltaflip.json", "w"), indent=1, default=float)
for idx in out:
    print(f"\n=== {idx} ===")
    print(f"{'cell':>22} {'n':>6} {'event':>8} {'control':>8} {'t(diff)':>8} {'halves':>14}")
    for k, v in out[idx].items():
        print(f"{k:>22} {v['n']:>6} {v['ev_bps']:>+7.1f}b {v['ctrl_bps']:>+7.1f}b {v['t']:>+8.2f} {str(v['halves']):>14}")
