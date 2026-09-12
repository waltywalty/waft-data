"""Round 72A step 3 - attempt 48 (r65 aggregate short-interest regime) REVERSED, IS ONLY.
Reuses the runner's data-build section (everything before its '# ---- IS grid' marker);
the runner drops sealed rows (oos=True, sessions >= OOS_START) at frame build when
--unseal is absent, so no OOS row ever enters this script. Writes nothing under backtest/.
Strict reversal (72A rule): cell = -1 x registered direction = SHORT SPX+NDX pooled while
regime LOW50 (p<=50); control = always-short on every eligible IS session, same cost.
Secondary (candidate note): LONG in HIGH (p>=75) vs always-long control."""
import sys, os, numpy as np, pandas as pd, datetime as dt
assert "--unseal" not in sys.argv and os.environ.get("UNSEAL_OK") is None
os.chdir("/home/user/waft-data/backtest"); sys.path.insert(0, "/home/user/waft-data/backtest")
src = open("run_r65_shortint.py").read()
head = src.split("# ------------------------------------------------------------------ IS grid")[0]
ns = {"__name__": "r72a_48_build"}
sys.argv = [sys.argv[0]]                      # no --unseal, ever
exec(head, ns)
frames, MICRO, AMORT, GROUPS, REG = ns["frames"], ns["MICRO"], ns["AMORT"], ns["GROUPS"], ns["REG"]
OOS_START, IS_LAST, stats, diff_t, universe = ns["OOS_START"], ns["IS_LAST"], ns["stats"], ns["diff_t"], ns["universe"]
regime_mask, all_blocks, p_carry, all_dates, rng = ns["regime_mask"], ns["all_blocks"], ns["p_carry"], ns["all_dates"], ns["rng"]

print("\n=== r72a attempt 48 reversed (IS ONLY) ===")
print(f"IS cut used: sessions strictly before OOS_START = {OOS_START} (last IS bookable session {IS_LAST})")
for i in frames:
    f = frames[i]
    assert (~f.oos).all() and f.index.max() < OOS_START, i
    print(f"  {i}: {len(f)} IS rows {f.index[0]}..{f.index[-1]}, oos rows present: {int(f.oos.sum())}")


def book(d, idx, mask, mult=1.0, sign=-1):
    """runner's book() with a direction sign; costs always SUBTRACTED."""
    m = np.asarray(mask, bool)
    start = m & ~np.r_[False, m[:-1]]
    ep = np.cumsum(start) * m
    ok = m & np.isfinite(d.prevc.values) & np.isfinite(d.atr20.values) & (d.atr20.values > 0)
    s = d[ok]; epi = ep[ok]
    sizes = np.bincount(ep)[epi]
    pnl = sign * (s.c.values - s.prevc.values) - mult * (MICRO[idx] / AMORT + 2 * MICRO[idx] / sizes)
    return pd.DataFrame(dict(skey=s.index, idx=idx, pnl=pnl, atr=s.atr20.values, R=pnl / s.atr20.values,
                             blk=s.blk.values, nomfg=~(s.pmi.values < 50), oos=s.oos.values))


def cell(maskf, grp, mult=1.0, sign=-1, masks=None):
    parts = [book(frames[i], i, masks[i] if masks else maskf(frames[i]), mult, sign) for i in GROUPS[grp]]
    return pd.concat(parts).sort_values(["skey", "idx"]).reset_index(drop=True)


def full(sub):
    s = stats(sub.pnl, sub.atr)
    yrs = sub.groupby(pd.to_datetime(sub.skey).dt.year).R.mean()
    s["per_year"] = {int(y): f"{v:+.3f}" for y, v in yrs.items()}
    s["per_year_signs"] = "".join("+" if v > 0 else "-" for v in yrs.values)
    return s


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(a.mean() - b.mean()), float((a.mean() - b.mean()) / se)


def report(name, maskf, grp, sign, ctrl_name):
    print(f"\n--- {name} ---")
    s1 = full(cell(maskf, grp, 1.0, sign)); s15 = full(cell(maskf, grp, 1.5, sign)); s2 = full(cell(maskf, grp, 2.0, sign))
    print(f"n {s1['n']} WR {s1['wr']*100:.1f}% PF {s1['pf']:.3f} avgR x1 {s1['avg_R']:+.4f} t {s1['t']:+.2f} | x1.5 {s15['avg_R']:+.4f} "
          f"| x2 {s2['avg_R']:+.4f} t {s2['t']:+.2f} | halves {s1['halves']} | per-year {s1['per_year']} signs {s1['per_year_signs']}")
    sub = cell(maskf, grp, 1.0, sign)
    ctrl = cell(lambda d: np.ones(len(d), bool), grp, 1.0, sign)
    c = full(ctrl)
    print(f"control ({ctrl_name}, all eligible IS sessions, x1): n {c['n']} avgR {c['avg_R']:+.4f} t {c['t']:+.2f} halves {c['halves']} per-year {c['per_year']}")
    dpair = diff_t(sub, ctrl, grp)
    dw, tw = welch(sub.R, ctrl.R)
    non = ctrl[~ctrl.set_index(["skey", "idx"]).index.isin(sub.set_index(["skey", "idx"]).index)]
    dn, tn = welch(sub.R, non.R)
    print(f"diff cell - control: runner paired-universe diff {dpair['diff']:+.4f} t {dpair['t']:+.2f} (N {dpair['n_universe']}); "
          f"Welch two-sample {dw:+.4f} t {tw:+.2f}; Welch cell vs NON-cell days {dn:+.4f} t {tn:+.2f} (n_non {len(non)})")
    return s1, s15, s2, c, dpair, (dw, tw), (dn, tn)


# ---------------- primary: strict reversal = SHORT in LOW50 pooled
P = report("REVERSED primary: SHORT SPX+NDX pooled in LOW50 (p<=50)", lambda d: d.p <= 50, "pooled", -1, "always-short")
# other selectable cells reversed
for nm, mf, g in [("SHORT LOW25 pooled", lambda d: d.p <= 25, "pooled"), ("SHORT LOW50 NDX", lambda d: d.p <= 50, "NDX"),
                  ("SHORT LOW25 NDX", lambda d: d.p <= 25, "NDX")]:
    report(nm, mf, g, -1, "always-short")

# ---------------- gradient: reversed threshold ladder (cumulative p<=X) and bands, pooled, x1
print("\n=== gradient (SHORT, pooled, x1): cumulative thresholds p<=X ===")
for X in (10, 25, 35, 50, 65, 75, 90, 100):
    s = stats(*(lambda c: (c.pnl, c.atr))(cell(lambda d, X=X: d.p <= X, "pooled", 1.0, -1)))
    print(f"  p<={X:>3}: n {s.get('n'):>5} avgR {s.get('avg_R', float('nan')):+.4f} t {s.get('t', float('nan')):+.2f} halves {s.get('halves')}")
print("=== gradient (SHORT, pooled, x1): bands ===")
for nm, lo, hi in [("0-25", 0, 25), ("25-50", 25, 50), ("50-75", 50, 75), ("75-100", 75, 101)]:
    s = stats(*(lambda c: (c.pnl, c.atr))(cell(lambda d, lo=lo, hi=hi: (d.p > lo - 1e-9) & (d.p < hi) if lo > 0 else d.p < hi, "pooled", 1.0, -1)))
    print(f"  band {nm:>6}: n {s.get('n'):>5} avgR {s.get('avg_R', float('nan')):+.4f} t {s.get('t', float('nan')):+.2f} halves {s.get('halves')}")

# ---------------- placebo 1: regime shifted by k availability blocks (the signal applied to the wrong settlement), SHORT LOW50 pooled
print("\n=== placebo A: regime block shifted by k settlements (SHORT LOW50 pooled, x1) ===")
bidx = {b: j for j, b in enumerate(all_blocks)}
for k in (-4, -2, -1, 1, 2, 4):
    masks = {}
    for i in frames:
        pj = []
        for b in frames[i].blk:
            j = bidx[b] + k
            pj.append(p_carry.get(all_dates[all_blocks[j]], np.nan) if 0 <= j < len(all_blocks) else np.nan)
        pj = np.asarray(pj, float)
        masks[i] = np.isfinite(pj) & (pj <= 50)
    s = stats(*(lambda c: (c.pnl, c.atr))(cell(None, "pooled", 1.0, -1, masks=masks)))
    print(f"  shift {k:+d}: n {s.get('n'):>5} avgR {s.get('avg_R', float('nan')):+.4f} t {s.get('t', float('nan')):+.2f} halves {s.get('halves')}")

# ---------------- placebo 2: the family's r16-B random-regime max-stat null, REVERSED (max SHORT avgR over 4 selectable cells)
NPERM = 1000
blocks = all_blocks; bpos = {b: j for j, b in enumerate(blocks)}
params = {}
for thr in ("LOW50", "LOW25"):
    on = np.array([bool(REG[thr](p_carry.get(all_dates[b], np.nan))) for b in blocks])
    starts = np.flatnonzero(on & ~np.r_[False, on[:-1]]); ends = np.flatnonzero(on & ~np.r_[on[1:], False])
    lens = ends - starts + 1
    params[thr] = dict(share=float(on.mean()), mean_len=float(lens.mean()), n_runs=int(len(lens)))
rng = np.random.default_rng(7248)


def random_regime(share, mean_len):
    p_on = min(1.0, 1.0 / mean_len); off_len = mean_len * (1 - share) / share; p_off = min(1.0, 1.0 / off_len)
    out = np.zeros(len(blocks), bool); i = 0; state = rng.random() < share
    while i < len(blocks):
        L = int(rng.geometric(p_on if state else p_off)); out[i:i + L] = state; i += L; state = not state
    return out


null = np.empty(NPERM); null_t = np.empty(NPERM)
for q in range(NPERM):
    best, bt = -np.inf, -np.inf
    for thr in ("LOW50", "LOW25"):
        rr = random_regime(params[thr]["share"], params[thr]["mean_len"])
        masks = {i: np.array([rr[bpos[b]] for b in frames[i].blk], bool) for i in frames}
        for g_ in GROUPS:
            s_ = cell(None, g_, 1.0, -1, masks=masks)
            if len(s_) >= 10:
                best = max(best, float(s_.R.mean()))
                bt = max(bt, float(s_.R.mean() / s_.R.std() * np.sqrt(len(s_))))
    null[q] = best; null_t[q] = bt
obs = P[0]["avg_R"]; obs_t = P[0]["t"]
best_obs = max(obs, *[stats(*(lambda c: (c.pnl, c.atr))(cell(mf, g, 1.0, -1)))["avg_R"] for mf, g in
                     [(lambda d: d.p <= 25, "pooled"), (lambda d: d.p <= 50, "NDX"), (lambda d: d.p <= 25, "NDX")]])
print(f"\n=== placebo B: r16-B random-regime max-stat null REVERSED ({NPERM} draws, params {params}) ===")
print(f"  null avgR median {np.median(null):+.4f} p95 {np.percentile(null, 95):+.4f}; observed primary {obs:+.4f} p {(null >= obs).mean():.3f}; "
      f"best observed selectable {best_obs:+.4f} p {(null >= best_obs).mean():.3f}")
print(f"  null max-t median {np.median(null_t):+.2f} p95 {np.percentile(null_t, 95):+.2f}; observed primary t {obs_t:+.2f} p {(null_t >= obs_t).mean():.3f}")

# ---------------- secondary read flagged by the candidate note: LONG in HIGH vs always-long
S = report("SECONDARY (candidate note): LONG SPX+NDX pooled in HIGH (p>=75)", lambda d: d.p >= 75, "pooled", +1, "always-long")
report("SECONDARY: LONG pooled in MID (50-75)", lambda d: (d.p > 50) & (d.p < 75), "pooled", +1, "always-long")
report("SECONDARY: LONG pooled in p>50 (MID+HIGH)", lambda d: d.p > 50, "pooled", +1, "always-long")
report("SECONDARY: LONG NDX in HIGH (p>=75)", lambda d: d.p >= 75, "NDX", +1, "always-long")
print("\ndone (IS only; nothing written under backtest/)")
