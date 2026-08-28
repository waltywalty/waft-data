"""Round 39c: tradeable form of the r39 Part A candidate - first 1H-aligned 5m
displacement of the session, enter at signal close, hold to session close,
micro costs, non-overlapping. Outputs results/r39c_eodhold.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

out = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b24 = load_frame(idx)
    c1 = b24.close.resample("1h").last().dropna()
    bias = np.sign(c1 - c1.rolling(20).mean())
    bias.index = bias.index + pd.Timedelta("1h")
    bias = bias.dropna()
    q = rth_of(b24)
    tr = np.maximum(q.high - q.low, np.maximum((q.high - q.close.shift(1)).abs(),
                                               (q.low - q.close.shift(1)).abs()))
    atr = tr.rolling(14).mean()
    body = (q.close - q.open).abs()
    disp = (tr >= 1.5 * atr) & (body / (q.high - q.low).replace(0, np.nan) >= 0.6)
    d = np.sign(q.close - q.open)
    m = disp & (d != 0)
    eod = q.groupby("skey").close.transform("last")
    t_sig = q.index + pd.Timedelta(minutes=5)
    bi = bias.index.searchsorted(t_sig, side="right") - 1
    bv = np.where(bi >= 0, bias.values[np.clip(bi, 0, None)], np.nan)
    aligned = m & (d.values == bv)
    ev = q[aligned].copy()
    ev["pnl"] = (d[aligned] * (eod[aligned] - q.close[aligned])) - MICRO[idx]
    first = ev.groupby("skey").head(1)          # non-overlapping: 1 trade/day
    p = first.pnl.values
    h = len(p) // 2
    w, l = p[p > 0], p[p <= 0]
    out[idx] = dict(n=int(len(p)), wr=float((p > 0).mean()),
                    pf=float(w.sum() / abs(l.sum())) if len(l) else np.inf,
                    avg=float(p.mean()), total=float(p.sum()),
                    t=float(p.mean() / p.std() * np.sqrt(len(p))),
                    halves=[float(np.sign(p[:h].mean())), float(np.sign(p[h:].mean()))],
                    avg_gross=float(p.mean() + MICRO[idx]))
json.dump(out, open("results/r39c_eodhold.json", "w"), indent=1)
print(f"{'idx':>5} {'n':>6} {'WR':>7} {'PF':>6} {'avg net':>8} {'gross':>7} {'t':>6} {'halves':>14}")
for k, v in out.items():
    print(f"{k:>5} {v['n']:>6} {v['wr']*100:>6.1f}% {v['pf']:>6.2f} {v['avg']:>+8.3f} "
          f"{v['avg_gross']:>+7.3f} {v['t']:>+6.2f} {str(v['halves']):>14}")
