"""Round 72A step 3, attempt 20 (r45b_holiday) reversed scoring, IS ONLY.
Reversed cell = SHORT 12:00->close on all pre-holiday sessions, SPX/NDX/RTY pooled,
micro costs subtracted at 1x/1.5x/2x. Never touches oos rows. Run from backtest/."""
import sys, os; os.chdir("/home/user/waft-data/backtest"); sys.path.insert(0, "/home/user/waft-data/backtest")
import numpy as np, pandas as pd, datetime as dt, warnings
warnings.filterwarnings("ignore")

# reuse the runner's functions (everything above its module-level data loop)
src = open("run_r45b_holiday.py").read().split("data, split = {}, {}")[0]
ns = {}
exec(src, ns)
build_days, weekdays_between, big3, MICRO = ns["build_days"], ns["weekdays_between"], ns["big3"], ns["MICRO"]
load_frame, rth_of = ns["load_frame"], ns["rth_of"]

def tstat(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std(ddof=1) > 0 else np.nan

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se)

def full(df, label):
    """df has columns R1,R15,R2 (net R at 1x/1.5x/2x), date, idx, gross."""
    df = df.sort_values(["date", "idx"])
    r1 = df.R1.values; m = len(r1) // 2
    w, l = r1[r1 > 0], r1[r1 <= 0]
    pf = w.sum() / abs(l.sum()) if len(l) and l.sum() < 0 else np.inf
    yrs = df.groupby(df.date.map(lambda d: d.year)).R1.mean()
    out = dict(n=int(len(df)), gross=float(df.gross.mean()), avgR_x1=float(r1.mean()),
               avgR_x15=float(df.R15.mean()), avgR_x2=float(df.R2.mean()),
               t_x1=tstat(r1), t_x15=tstat(df.R15), t_x2=tstat(df.R2),
               wr=float((r1 > 0).mean()), pf=float(pf),
               halves_bydate=[float(np.sign(r1[:m].mean())), float(np.sign(r1[m:].mean()))],
               halves_vals=[float(r1[:m].mean()), float(r1[m:].mean())],
               per_year={int(y): round(float(v), 4) for y, v in yrs.items()})
    print(f"{label}: n {out['n']} gross {out['gross']:+.4f} net1x {out['avgR_x1']:+.4f} (t {out['t_x1']:+.2f}) "
          f"1.5x {out['avgR_x15']:+.4f} (t {out['t_x15']:+.2f}) 2x {out['avgR_x2']:+.4f} (t {out['t_x2']:+.2f}) "
          f"WR {out['wr']*100:.1f}% PF {out['pf']:.2f} halves(by date) {out['halves_bydate']} {['%+.3f'%v for v in out['halves_vals']]}")
    print("   per-year mean R (1x):", out["per_year"])
    return out

# ---- build IS-only day tables --------------------------------------------------
data = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    keys = d.index.tolist()
    preh = [weekdays_between(keys[i], keys[i + 1]) >= 1 for i in range(len(keys) - 1)] + [False]
    d["preh"] = preh
    d["big3"] = [big3(k) if p else False for k, p in zip(keys, preh)]
    # post-holiday (placebo): previous session skipped a weekday
    d["posth"] = [False] + [weekdays_between(keys[i - 1], keys[i]) >= 1 for i in range(1, len(keys))]
    # pre-pre-holiday (placebo): the session before a pre-holiday session
    d["prepreh"] = list(np.roll(np.array(preh), -1)); d.loc[d.index[-1], "prepreh"] = False
    # pre-weekend Friday, not pre-holiday (placebo): next session is >=2 calendar days later, no weekday skipped
    d["prewknd"] = [((keys[i + 1] - keys[i]).days >= 2 and not preh[i]) for i in range(len(keys) - 1)] + [False]
    # hourly entry ladder for the reversed short: open at 10:00/11:00/13:00/14:00 bars
    rth = rth_of(load_frame(idx))
    for hh in (1000, 1100, 1300, 1400, 1500):
        col = {}
        for skey, g in rth.groupby("skey"):
            mm = np.where(g.hm.values >= hh)[0]
            col[skey] = g.open.values[mm[0]] if len(mm) else np.nan
        d[f"c{hh}"] = pd.Series(col)
    ISd = d[~d.oos].copy()          # IS ONLY - OOS rows dropped here and never used
    assert ISd.index.max() < cutd
    print(f"{idx}: IS cut {cutd} (runner keys[int(len*0.75)]); IS sessions {len(ISd)} "
          f"last IS session {ISd.index.max()}, pre-holiday IS {int(ISd.preh.sum())}, big3 {int(ISd.big3.sum())}")
    data[idx] = ISd

def cell(ecol, xcol, mask_fn, sign=-1, insts=("SPX", "NDX", "RTY")):
    """sign=-1 => SHORT entry ecol exit xcol. Returns per-trade frame with net R at 1x/1.5x/2x."""
    rows = []
    for idx in insts:
        d = data[idx]
        m = mask_fn(d) & np.isfinite(d[ecol]) & np.isfinite(d[xcol]) & np.isfinite(d.atr20) & (d.atr20 > 0)
        s = d[m]
        gross = sign * (s[xcol] - s[ecol])
        c = MICRO[idx]
        rows.append(pd.DataFrame(dict(date=s.index, idx=idx, gross=gross / s.atr20,
                                      R1=(gross - c) / s.atr20, R15=(gross - 1.5 * c) / s.atr20,
                                      R2=(gross - 2 * c) / s.atr20)))
    return pd.concat(rows, ignore_index=True)

print("\n=== REVERSED CELL: SHORT 12:00->close, all pre-holiday sessions, SPX/NDX/RTY pooled, IS ===")
rev = cell("c12", "c", lambda d: d.preh)
R = full(rev, "REVERSED H2/all SHORT")
for idx in ("SPX", "NDX", "RTY"):
    s = rev[rev.idx == idx]
    print(f"   {idx}: n {len(s)} net1x {s.R1.mean():+.4f} t {tstat(s.R1):+.2f}")
# runner-order halves (instrument-blocked, as the runner computed them)
rr = rev.R1.values; m = len(rr) // 2
print(f"   halves in runner order (instrument-blocked): [{np.sign(rr[:m].mean()):+.0f},{np.sign(rr[m:].mean()):+.0f}]")

print("\n=== UNCONDITIONAL CONTROL: always-SHORT 12:00->close, every eligible IS session, 1x cost ===")
ctl = cell("c12", "c", lambda d: np.ones(len(d), bool))
C = full(ctl, "CONTROL always-short 12->close")
ctl_ex = cell("c12", "c", lambda d: ~d.preh)
CX = full(ctl_ex, "CONTROL ex pre-holiday days")
dif_all = R["avgR_x1"] - C["avgR_x1"]; t_all = welch(rev.R1, ctl.R1)
dif_ex = R["avgR_x1"] - CX["avgR_x1"]; t_ex = welch(rev.R1, ctl_ex.R1)
print(f"DIFF reversed - control(all sessions): {dif_all:+.4f}  Welch t {t_all:+.2f}")
print(f"DIFF reversed - control(ex pre-holiday): {dif_ex:+.4f}  Welch t {t_ex:+.2f}")
# paired-by-date view: reversed day minus the mean of the same instrument's other IS days is the same
# as the ex-cell Welch above; the cell is a strict subset of control days so Welch is the stated method.

print("\n=== GRADIENT (a): family grid reversed - SHORT {H1,H2,H3} x {all,big3}, 1x cost ===")
HOLDS = {"H1_open_close": ("o", "c"), "H2_1200_close": ("c12", "c"), "H3_prevc_close": ("prevc", "c")}
grid = {}
for h, (e, x) in HOLDS.items():
    for sc in ("all", "big3"):
        f = cell(e, x, (lambda d: d.preh) if sc == "all" else (lambda d: d.big3))
        r1 = f.R1.values; mm = len(r1) // 2
        f2 = f.sort_values(["date", "idx"]); r1s = f2.R1.values
        grid[(h, sc)] = (len(f), r1.mean(), tstat(r1), f.R2.mean())
        print(f"  SHORT {h:>15} {sc:>5}: n {len(f):>3} net1x {r1.mean():+.4f} t {tstat(r1):+.2f} 2x {f.R2.mean():+.4f} "
              f"halves(date) [{np.sign(r1s[:mm].mean()):+.0f},{np.sign(r1s[mm:].mean()):+.0f}]")

print("\n=== GRADIENT (b): entry-time ladder for the reversed SHORT ->close on pre-holiday sessions, 1x cost ===")
print("    (control = same ladder always-short, all IS sessions)")
ladder = {}
for ecol, lab in (("o", "09:30"), ("c1000", "10:00"), ("c1100", "11:00"), ("c12", "12:00"),
                  ("c1300", "13:00"), ("c1400", "14:00"), ("c1500", "15:00")):
    f = cell(ecol, "c", lambda d: d.preh); g = cell(ecol, "c", lambda d: np.ones(len(d), bool))
    ladder[lab] = (len(f), f.R1.mean(), tstat(f.R1), g.R1.mean(), f.R1.mean() - g.R1.mean(), welch(f.R1, g.R1))
    print(f"  {lab}->close: preh n {len(f):>3} net1x {f.R1.mean():+.4f} t {tstat(f.R1):+.2f} | control {g.R1.mean():+.4f} "
          f"| diff {f.R1.mean()-g.R1.mean():+.4f} Welch t {welch(f.R1, g.R1):+.2f}")

print("\n=== PLACEBO: same SHORT 12:00->close window on shifted days, 1x cost ===")
plac = {}
for col, lab in (("posth", "post-holiday session (day after)"), ("prepreh", "pre-pre-holiday (day before the cell)"),
                 ("prewknd", "plain pre-weekend Friday, not pre-holiday")):
    f = cell("c12", "c", lambda d, c=col: d[c].astype(bool))
    f2 = f.sort_values(["date", "idx"]); r1s = f2.R1.values; mm = len(r1s) // 2
    plac[lab] = (len(f), f.R1.mean(), tstat(f.R1))
    print(f"  {lab:>42}: n {len(f):>4} net1x {f.R1.mean():+.4f} t {tstat(f.R1):+.2f} "
          f"halves [{np.sign(r1s[:mm].mean()):+.0f},{np.sign(r1s[mm:].mean()):+.0f}]")

print("\n=== GOLD diagnostic, reversed SHORT 12:00->close pre-holiday, IS ===")
g = cell("c12", "c", lambda d: d.preh, insts=("GOLD",))
print(f"  n {len(g)} net1x {g.R1.mean():+.4f} t {tstat(g.R1):+.2f}")

print("\n=== SURVIVOR BAR (registered) ===")
checks = dict(t1_ge_2=R["t_x1"] >= 2, avgR_x2_pos=R["avgR_x2"] > 0,
              halves_pos=all(v > 0 for v in R["halves_bydate"]),
              diff_ctl_pos_t2=(dif_all > 0 and t_all >= 2))
for k, v in checks.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
