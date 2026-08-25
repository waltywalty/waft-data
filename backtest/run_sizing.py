"""Streak statistics and streak-conditioned position sizing.

Part 1 answers the factual questions: average and record win/loss streaks on
the deployed trade sequence, with outlier treatment, plus the test that
decides whether streaks carry ANY information - serial dependence of trade
outcomes. If outcomes are independent, a sizing rule keyed to the previous
results changes the risk profile but cannot change the expectancy per dollar
risked; the simulations then measure exactly what it does change.

Part 2 simulates the ladders on the real $2,000 equity path (risk sized off
the actual 2R stop distance, 20:1 margin cap) and on 2,000 shuffled orderings
of the same trades, so the drawdown/ruin numbers are distributions, not one
lucky path.
"""
import pandas as pd, numpy as np, warnings, json
warnings.filterwarnings("ignore")
from scipy import stats as st

rng = np.random.default_rng(20260825)
D = pd.read_pickle("results/trades_deployable.pkl").sort_values("t_fill").reset_index(drop=True)
D["day"] = pd.to_datetime(D.day)
win = (D.pnl_oz > 0).astype(int).values
OUT = {}

print(f"=== 1. STREAKS over {len(D)} trades (win rate {win.mean()*100:.1f}%) ===")
streaks = {"win": [], "loss": []}
cur, kind = 1, win[0]
for w in win[1:]:
    if w == kind:
        cur += 1
    else:
        streaks["win" if kind else "loss"].append(cur)
        cur, kind = 1, w
streaks["win" if kind else "loss"].append(cur)
S = {}
for k in ("win", "loss"):
    v = sorted(streaks[k])
    top = v[-1]
    n_top = v.count(top)
    second = max(x for x in v if x < top) if any(x < top for x in v) else top
    S[k] = {"count": len(v), "mean": float(np.mean(v)), "median": float(np.median(v)),
            "p90": float(np.percentile(v, 90)), "max": int(top), "n_at_max": int(n_top),
            "second": int(second)}
    print(f"  {k:4s}: {len(v):>3} streaks, mean {np.mean(v):.2f}, median {np.median(v):.0f}, "
          f"p90 {np.percentile(v, 90):.0f}, longest {top} (x{n_top}), next-longest {second}")
OUT["streaks"] = S

# expected longest streak if outcomes were iid coin flips at the observed rates
p_l = 1 - win.mean()
exp_max_loss = float(np.log(len(D) * (1 - p_l)) / -np.log(p_l))
print(f"  longest loss streak EXPECTED from pure iid chance at this win rate: "
      f"~{exp_max_loss:.1f}")
OUT["iid_expected_max_loss_streak"] = exp_max_loss

print("\n=== 2. DO STREAKS CARRY INFORMATION? ===")
prev = win[:-1]
nxt = win[1:]
p_after_w = nxt[prev == 1].mean()
p_after_l = nxt[prev == 0].mean()
ct = pd.crosstab(prev, nxt)
chi2, pval = st.chi2_contingency(ct)[:2]
runs = len(streaks["win"]) + len(streaks["loss"])
n1, n0 = win.sum(), len(win) - win.sum()
mu = 2 * n1 * n0 / (n1 + n0) + 1
sd = np.sqrt(2 * n1 * n0 * (2 * n1 * n0 - n1 - n0) / ((n1 + n0) ** 2 * (n1 + n0 - 1)))
z = (runs - mu) / sd
ac1 = float(pd.Series(D.pnl_oz / D.entry).autocorr(1))
print(f"  P(win) unconditional        : {win.mean()*100:.1f}%")
print(f"  P(win | previous trade won) : {p_after_w*100:.1f}%")
print(f"  P(win | previous trade lost): {p_after_l*100:.1f}%   chi2 p = {pval:.3f}")
print(f"  runs test: {runs} runs vs {mu:.0f} expected, z = {z:+.2f}")
print(f"  lag-1 autocorrelation of returns: {ac1:+.3f}")
OUT["dependence"] = {"p_win": float(win.mean()), "p_after_win": float(p_after_w),
                     "p_after_loss": float(p_after_l), "chi2_p": float(pval),
                     "runs_z": float(z), "ret_autocorr1": float(ac1)}

print("\n=== 3. SIZING LADDERS on the real sequence ($2,000 start) ===")
stop_d = D.stop_dist.values
entry = D.entry.values
pnl_oz = D.pnl_oz.values
years = (D.t_fill.iloc[-1] - D.t_fill.iloc[0]).days / 365.25


def simulate(order, scheme):
    eq, peak, mdd = 2000.0, 2000.0, 0.0
    L = W = 0                                     # current loss / win streaks
    worst_trade = 0.0
    for i in order:
        if scheme == "flat1":      r = 0.01
        elif scheme == "flat2":    r = 0.02
        elif scheme == "lad1.5c4": r = min(0.01 * 1.5 ** L, 0.04)
        elif scheme == "lad2c8":   r = min(0.01 * 2.0 ** L, 0.08)
        elif scheme == "add.5c3":  r = min(0.01 + 0.005 * L, 0.03)
        elif scheme == "anti1.5":  r = min(0.01 * 1.5 ** W, 0.04)
        elif scheme == "halfloss": r = 0.005 if L > 0 else 0.01
        else: raise ValueError(scheme)
        oz = eq * r / stop_d[i]
        oz = min(oz, 20.0 * eq / entry[i])        # 20:1 margin cap
        pnl = oz * pnl_oz[i]
        worst_trade = min(worst_trade, pnl / eq)
        eq += pnl
        if eq <= 0:
            return dict(final=0.0, cagr=-1.0, mdd=1.0, worst=worst_trade, ruin=True)
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
        if pnl_oz[i] > 0: W, L = W + 1, 0
        else:             L, W = L + 1, 0
    return dict(final=eq, cagr=(eq / 2000.0) ** (1 / years) - 1, mdd=mdd,
                worst=worst_trade, ruin=False)


SCHEMES = [("flat1", "flat 1% (deployed)"), ("flat2", "flat 2%"),
           ("lad1.5c4", "x1.5 per loss, cap 4%"), ("lad2c8", "x2 per loss, cap 8%"),
           ("add.5c3", "+0.5%/loss, cap 3%"), ("anti1.5", "x1.5 per WIN, cap 4%"),
           ("halfloss", "halve after a loss")]
base_order = np.arange(len(D))
real = {}
for key, lbl in SCHEMES:
    s = simulate(base_order, key)
    real[key] = s
    print(f"  {lbl:26s} final ${s['final']:>8,.0f}  CAGR {s['cagr']*100:+5.1f}%  "
          f"maxDD {s['mdd']*100:4.1f}%  worst trade {s['worst']*100:5.1f}%")
OUT["real_path"] = {k: real[k] for k, _ in SCHEMES}

print("\n=== 4. THE SAME LADDERS OVER 2,000 SHUFFLED ORDERINGS ===")
print("   (order is luck; these are the distributions the ladder actually buys)")
boot = {}
orders = [rng.permutation(len(D)) for _ in range(2000)]
for key, lbl in SCHEMES:
    fin, mdd, ruin = [], [], 0
    for o in orders:
        s = simulate(o, key)
        fin.append(s["final"]); mdd.append(s["mdd"]); ruin += s["ruin"]
    fin, mdd = np.array(fin), np.array(mdd)
    boot[key] = {"median_final": float(np.median(fin)),
                 "p5_final": float(np.percentile(fin, 5)),
                 "median_mdd": float(np.median(mdd)),
                 "p95_mdd": float(np.percentile(mdd, 95)),
                 "p_dd30": float((mdd > 0.30).mean()),
                 "p_dd50": float((mdd > 0.50).mean()),
                 "p_ruin": ruin / len(orders)}
    b = boot[key]
    print(f"  {lbl:26s} median final ${b['median_final']:>8,.0f}  "
          f"median DD {b['median_mdd']*100:4.1f}%  p95 DD {b['p95_mdd']*100:4.1f}%  "
          f"P(DD>30%) {b['p_dd30']*100:4.1f}%  P(DD>50%) {b['p_dd50']*100:4.1f}%")
OUT["bootstrap"] = boot

json.dump(OUT, open("results/sizing.json", "w"), indent=1, default=str)
print("\nwritten: results/sizing.json")
