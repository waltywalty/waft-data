"""Round 72A step 3 - reversed scoring, IS ONLY, for attempt 12-revival (r42l_fomc,
registered cell '0930->1355' LONG, reversed = SHORT statement-day 09:30 -> 13:55).
Reuses the data build of run_r42l_fomc.py verbatim (load_frame/rth_of from
run_r37_scalps.py, frozen FOMC calendar, MICRO costs, per-instrument 75% cut).
OOS FIREWALL: sealed rows (oos=True, i.e. skey >= cut) are dropped from every frame
immediately after the cut is computed and never touched; no *oos* file is opened."""
import os, sys, re, json, datetime as dt, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
BT = "/home/user/waft-data/backtest"
os.chdir(BT); sys.path.insert(0, BT)
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}; exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}          # runner's MICRO dict, per RT
lsrc = open("run_r42l_fomc.py").read()
FOMC = set(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', lsrc, re.S).group(1).split()).date)

def tstat(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return float(r.mean() / r.std() * np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else np.nan

def stats(pnl, atr, dates=None):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    out = dict(n=int(len(p)), wr=float((p > 0).mean()),
               pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
               avg_R=float(r.mean()), t=tstat(r),
               halves_runner_order=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])
    if dates is not None:
        d = np.asarray(dates)[ok]; o = np.argsort(d, kind="stable"); rs = r[o]
        out["halves_chrono"] = [float(np.sign(rs[:m].mean())), float(np.sign(rs[m:].mean()))]
        out["halves_chrono_means"] = [float(rs[:m].mean()), float(rs[m:].mean())]
    return out

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float(a.mean() - b.mean()), float((a.mean() - b.mean()) / np.sqrt(va + vb))

# ---------------- data build (identical to run_r42l_fomc.py) ----------------
frames, split = {}, {}
for idx in MICRO:
    rth = rth_of(load_frame(idx))
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values; c, o = g.close.values, g.open.values
        if len(g) < 50 or hm[0] > 935 or skey < pd.Timestamp("2013-01-01").date():
            continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        rows_d.append(dict(skey=skey, o=o[0], c1355=lb(1400), c1400v=lb(1405), cEnd=c[-1],
                           c1030=lb(1035), c1130=lb(1135), c1230=lb(1235), c1330=lb(1335),
                           hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows_d).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["fomc"] = [k in FOMC for k in d.index]
    d["prev_c1400"] = d.c1400v.shift(1)
    d["prev_cEnd"] = d.cEnd.shift(1)
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = d.index >= cutd
    split[idx] = str(cutd)
    frames[idx] = d[~d.oos].copy()               # OOS FIREWALL: sealed rows leave here
    print(f"{idx}: {len(d)} sessions, IS cut {cutd} -> {len(frames[idx])} IS rows kept, "
          f"{int(d.oos.sum())} sealed rows DROPPED (never used)")
    assert frames[idx].index.max() < cutd
print("IS cut dates used:", split)

# placebo days (attempt-34 definition): session exactly 7 calendar days before each statement day
for idx, d in frames.items():
    kset = set(d.index); plc = set()
    for k in d.index[d.fomc]:
        p = k - dt.timedelta(days=7)
        if p in kset and p not in FOMC: plc.add(p)
    d["placebo"] = [k in plc for k in d.index]

def collect(pnl_fn, mask_fn, costmult=1.0, legs=1):
    subs = []
    for idx, d in frames.items():
        g = pnl_fn(d); m = mask_fn(d) & np.isfinite(g)
        s = d[m]
        subs.append(pd.DataFrame(dict(gross=g[m], pnl=g[m] - costmult * legs * MICRO[idx],
                                      atr=s.atr20, skey=s.index, idx=idx)))
    return pd.concat(subs, ignore_index=True)

# ---------------- reversed cell: SHORT 09:30 -> 13:55 on statement days ----------------
short_am = lambda d: d.o - d.c1355
is_fomc = lambda d: d.fomc
is_all = lambda d: pd.Series(True, index=d.index)
is_nonfomc = lambda d: ~d.fomc
is_plc = lambda d: d.placebo

R = {}
for k in (1.0, 1.5, 2.0):
    sub = collect(short_am, is_fomc, k)
    R[k] = stats(sub.pnl, sub.atr, sub.skey)
rev = collect(short_am, is_fomc, 1.0)
rev["R"] = rev.pnl / rev.atr
rev["Rgross"] = rev.gross / rev.atr
print("\n=== REVERSED CELL: short statement-day 09:30 -> 13:55, SPX/NDX/RTY pooled, IS only ===")
print(f"gross: avgR {rev.Rgross.mean():+.4f} t {tstat(rev.Rgross):+.2f}")
for k in (1.0, 1.5, 2.0):
    a = R[k]
    print(f"cost x{k}: n {a['n']} WR {a['wr']*100:.1f}% PF {a['pf']:.3f} avgR {a['avg_R']:+.4f} t {a['t']:+.2f} "
          f"halves chrono {a['halves_chrono']} (means {np.round(a['halves_chrono_means'],4).tolist()}) "
          f"halves runner-order {a['halves_runner_order']}")
print("per-instrument (1x):")
for idx in MICRO:
    s = rev[rev.idx == idx]
    print(f"  {idx}: n {len(s)} avgR {s.R.mean():+.4f} t {tstat(s.R):+.2f} WR {(s.pnl>0).mean()*100:.1f}%")
rev["year"] = [k.year for k in rev.skey]
py = rev.groupby("year").R.agg(["count", "mean"])
py["t"] = rev.groupby("year").R.apply(tstat)
print("per-year (1x):")
print(py.round(4).to_string())
print("per-year signs:", "".join("+" if v > 0 else "-" for v in py["mean"]))

# ---------------- unconditional control: always-short 09:30 -> 13:55, every IS session ----------------
ctl = collect(short_am, is_all, 1.0); ctl["R"] = ctl.pnl / ctl.atr
cmp_ = collect(short_am, is_nonfomc, 1.0); cmp_["R"] = cmp_.pnl / cmp_.atr
cs = stats(ctl.pnl, ctl.atr, ctl.skey)
print(f"\n=== CONTROL: always-short 09:30->13:55 on EVERY IS session, 1x cost ===")
print(f"n {cs['n']} avgR {cs['avg_R']:+.4f} t {cs['t']:+.2f} WR {cs['wr']*100:.1f}% PF {cs['pf']:.3f} "
      f"halves chrono {cs['halves_chrono']}")
for idx in MICRO:
    s = ctl[ctl.idx == idx]
    print(f"  {idx}: n {len(s)} avgR {s.R.mean():+.4f} t {tstat(s.R):+.2f}")
d_all = float(rev.R.mean() - ctl.R.mean())
d_cmp, t_cmp = welch(rev.R, cmp_.R)
print(f"diff reversed - control(all sessions): {d_all:+.4f}")
print(f"diff reversed - control(non-FOMC complement, n {len(cmp_)}): {d_cmp:+.4f}, Welch t {t_cmp:+.2f}")
print("(cell is a subset of control days -> paired-by-date is degenerate; Welch on disjoint samples used)")

# ---------------- gradient: the family's own grid, reversed (all windows SHORT) ----------------
print("\n=== GRADIENT: family grid reversed (all SHORT, statement days, IS, 1x cost) ===")
GRID = [("prev1400->1355 (L-M)", lambda d: d.prev_c1400 - d.c1355, 1),
        ("0930->1355 [registered cell]", short_am, 1),
        ("prevclose->close (full day)", lambda d: d.prev_cEnd - d.cEnd, 1),
        ("r53 C1_ON prevclose->0930", lambda d: d.prev_cEnd - d.o, 1),
        ("r53 C2_PM 1355->close", lambda d: d.c1355 - d.cEnd, 1),
        ("r53 C3_ON+PM (2 legs)", lambda d: (d.prev_cEnd - d.o) + (d.c1355 - d.cEnd), 2)]
grad = []
for name, fn, legs in GRID:
    s = collect(fn, is_fomc, 1.0, legs); a = stats(s.pnl, s.atr, s.skey)
    grad.append(dict(cell=name, **{k: v for k, v in a.items()}))
    print(f"{name:>32} | n {a['n']:>4} avgR {a['avg_R']:+.4f} t {a['t']:+.2f} PF {a['pf']:.2f} halves {a['halves_chrono']}")
print("--- descriptive exit-time ladder of the reversed morning short (09:30 -> X), statement days ---")
ladder = []
for nm, col in [("1030", "c1030"), ("1130", "c1130"), ("1230", "c1230"), ("1330", "c1330"), ("1355", "c1355")]:
    s = collect(lambda d, c=col: d.o - d[c], is_fomc, 1.0); a = stats(s.pnl, s.atr, s.skey)
    ladder.append(dict(exit=nm, **a))
    print(f"  0930->{nm}: n {a['n']} avgR {a['avg_R']:+.4f} t {a['t']:+.2f} halves {a['halves_chrono']}")
print("--- same ladder on ALL IS sessions (always-short control by exit) ---")
for nm, col in [("1030", "c1030"), ("1130", "c1130"), ("1230", "c1230"), ("1330", "c1330"), ("1355", "c1355")]:
    s = collect(lambda d, c=col: d.o - d[c], is_all, 1.0); a = stats(s.pnl, s.atr, s.skey)
    print(f"  0930->{nm}: n {a['n']} avgR {a['avg_R']:+.4f} t {a['t']:+.2f}")

# ---------------- placebo: matched day 7 calendar days earlier, reversed (short 09:30->13:55) ----------------
pl = collect(short_am, is_plc, 1.0); ps = stats(pl.pnl, pl.atr, pl.skey)
pl["R"] = pl.pnl / pl.atr
print(f"\n=== PLACEBO (7-days-earlier matched sessions), short 09:30->13:55, 1x ===")
print(f"n {ps['n']} avgR {ps['avg_R']:+.4f} t {ps['t']:+.2f} WR {ps['wr']*100:.1f}% halves {ps['halves_chrono']}")
dp, tp = welch(rev.R, pl.R)
print(f"reversed - placebo: {dp:+.4f} Welch t {tp:+.2f}")

# ---------------- supplementary: R-based PF, year-concentration ----------------
print("\n=== SUPPLEMENTARY (1x) ===")
for k in (1.0, 1.5, 2.0):
    s_ = collect(short_am, is_fomc, k); r_ = (s_.pnl / s_.atr).values
    print(f"cost x{k}: PF on R units {r_[r_>0].sum()/abs(r_[r_<=0].sum()):.3f}  (runner-convention PF on raw points {R[k]['pf']:.3f})")
for drop in [(2013,), (2017,), (2013, 2017)]:
    s_ = rev[~rev.year.isin(drop)]
    print(f"excluding {drop}: n {len(s_)} avgR {s_.R.mean():+.4f} t {tstat(s_.R):+.2f}")
print("share of total reversed R from 2013+2017:",
      round(float(rev[rev.year.isin([2013, 2017])].R.sum() / rev.R.sum()), 2))
rev.sort_values("skey").to_csv("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_12-revival_reversed_trades_IS.csv", index=False)

json.dump(dict(is_cut=split, reversed={str(k): v for k, v in R.items()},
               per_year={int(y): dict(n=int(r["count"]), avgR=float(r["mean"]), t=float(r["t"])) for y, r in py.iterrows()},
               control=cs, diff_vs_all=d_all, diff_vs_complement=dict(avgR=d_cmp, t=t_cmp, n_complement=int(len(cmp_))),
               gradient=grad, ladder=ladder, placebo=ps, placebo_diff=dict(avgR=dp, t=tp)),
          open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_12-revival.json", "w"),
          indent=1, default=float)
