"""Round 72A attempt 19 (r45_opex) reversed scoring, IN-SAMPLE ONLY.
Reversed cell = -1 x registered SHORT arm: W3 post-opex Monday open->close LONG
(monthly scope), secondary W4 post-opex Mon open->Wed close LONG (monthly).
Data-build functions copied verbatim from backtest/run_r45_opex.py; every
computation filters to oos == False (sessions before each instrument's own
IS cut, keys[int(len*0.75)]). No OOS row is ever used. Run from backtest/."""
import pandas as pd, numpy as np, json, warnings, datetime as dt, sys
sys.path.insert(0, "/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")
from scipy import stats as sst

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}


def build_days(idx):                       # copied from run_r45_opex.py
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    cutd = d.index.tolist()[int(len(d) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in d.index])
    return d, cutd


def third_friday(y, m):                    # copied
    f = dt.date(y, m, 1)
    off = (4 - f.weekday()) % 7
    return f + dt.timedelta(days=off + 14)


def month_trades(d, wname):                # copied verbatim from runner
    keys = d.index.tolist()
    out = []
    y0, y1 = keys[0].year, keys[-1].year
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            tf = third_friday(y, m)
            mon = tf - dt.timedelta(days=4)
            wk = [k for k in keys if mon <= k <= tf]
            if len(wk) < 3:
                continue
            expiry = wk[-1]
            if wname == "W1_opexweek":
                ek, xp = wk[0], d.c[expiry]
                e = d.o[ek]
            elif wname == "W2_wed_fri":
                wed = tf - dt.timedelta(days=2)
                cand = [k for k in wk if k <= wed]
                if not cand or cand[-1] == expiry:
                    continue
                ek = cand[-1]
                e, xp = d.c[ek], d.c[expiry]
            else:
                post = [k for k in keys if expiry < k <= expiry + dt.timedelta(days=4)]
                if not post:
                    continue
                ek = post[0]
                e = d.o[ek]
                if wname == "W3_postmon":
                    xp = d.c[ek]
                else:
                    wed2 = ek + dt.timedelta(days=2)
                    cand = [k for k in keys if ek <= k <= wed2]
                    xp = d.c[cand[-1]]
            a = d.atr20[ek]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            out.append((ek, m, xp - e, a, bool(d.oos[ek])))
    return out


def rstats(r, p=None):
    """r = R-multiples (net). WR/PF on points if p given (runner convention), else on r."""
    r = np.asarray(r, float); ok = np.isfinite(r); r = r[ok]
    p = r if p is None else np.asarray(p, float)[ok]
    n = len(r)
    if n < 10: return dict(n=int(n))
    w, ls = p[p > 0], p[p <= 0]; m = n // 2
    return dict(n=int(n), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avgR=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(n)) if r.std() > 0 else float("nan"),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t, pv = sst.ttest_ind(a, b, equal_var=False)
    return float(a.mean() - b.mean()), float(t), float(pv)


data, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    dis = d[~d.oos].copy()          # IN-SAMPLE ONLY from here on
    data[idx] = dis
    split[idx] = str(cutd)
    print(f"{idx}: IS cut (first OOS session) = {cutd}; IS sessions {len(dis)} "
          f"{dis.index[0]}..{dis.index[-1]}  [OOS rows dropped: {int(d.oos.sum())}]")
    assert not dis.oos.any()

IDX = ("SPX", "NDX", "RTY")
out = dict(is_cut=split, note="IS only; oos rows dropped before any computation")

# ---------------- reversed cells (LONG on the short-arm windows) -----------------
def cell_frame(wname, months, idxs=IDX, side=+1):
    rows = []
    for idx in idxs:
        for ek, m, dpts, a, oos in month_trades(data[idx], wname):
            assert not oos
            if m not in months: continue
            rows.append(dict(idx=idx, date=ek, m=m, dpts=side * dpts, atr=a, cost=MICRO[idx]))
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def score(df, label):
    res = {}
    for k in (1.0, 1.5, 2.0):
        pnl = df.dpts - k * df.cost
        res[f"x{k}"] = rstats(pnl / df.atr, pnl)
    r1 = (df.dpts - df.cost) / df.atr
    yrs = pd.Series(r1.values, index=pd.to_datetime(df.date)).groupby(lambda t: t.year).agg(["mean", "count"])
    res["per_year"] = {int(y): [round(v["mean"], 4), int(v["count"])] for y, v in yrs.iterrows()}
    res["per_year_signs"] = "".join("+" if v > 0 else "-" for v in yrs["mean"])
    res["gross_avgR"] = float((df.dpts / df.atr).mean())
    res["per_instrument_x1"] = {i: rstats(((df.dpts - df.cost) / df.atr)[df.idx == i]) for i in df.idx.unique()}
    print(f"\n[{label}] n={len(df)} gross avgR {res['gross_avgR']:+.4f}")
    for k in ("x1.0", "x1.5", "x2.0"):
        s = res[k]; print(f"  cost {k}: avgR {s['avgR']:+.4f} t {s['t']:+.2f} WR {s['wr']*100:.1f}% PF {s['pf']:.3f} halves(chrono) {s['halves']}")
    print(f"  per-year (x1): {res['per_year']}")
    print(f"  per-year signs: {res['per_year_signs']}")
    for i, s in res["per_instrument_x1"].items():
        print(f"  {i}: {s}")
    return res


MONTHLY, QUARTERLY = tuple(range(1, 13)), (3, 6, 9, 12)
NONQ = tuple(m for m in MONTHLY if m not in QUARTERLY)

w3 = cell_frame("W3_postmon", MONTHLY)
out["reversed_W3_monthly_LONG"] = score(w3, "REVERSED W3 post-opex Monday open->close LONG, monthly, SPX/NDX/RTY pooled")
# runner-order halves (instrument-major, as the runner's stats() computed them)
w3_runner_order = pd.concat([w3[w3.idx == i] for i in IDX])
r_ro = (w3_runner_order.dpts - w3_runner_order.cost) / w3_runner_order.atr
m = len(r_ro) // 2
out["reversed_W3_monthly_LONG"]["halves_runner_order"] = [float(np.sign(r_ro[:m].mean())), float(np.sign(r_ro[m:].mean()))]
print("  halves in runner (instrument-major) order:", out["reversed_W3_monthly_LONG"]["halves_runner_order"])

w4 = cell_frame("W4_postmon_wed", MONTHLY)
out["reversed_W4_monthly_LONG"] = score(w4, "REVERSED W4 post-opex Mon open->Wed close LONG, monthly, pooled")

# gold diagnostic
g3 = cell_frame("W3_postmon", MONTHLY, idxs=("GOLD",))
out["reversed_W3_monthly_LONG_GOLD_diag"] = rstats((g3.dpts - g3.cost) / g3.atr, g3.dpts - g3.cost)
print("\nGOLD diagnostic reversed W3 monthly:", out["reversed_W3_monthly_LONG_GOLD_diag"])

# ---------------- unconditional controls -----------------
# W3 control: every IS session, always-long open->close, 1x cost, ATR20-normalised
ctl_rows = []
for idx in IDX:
    d = data[idx]
    ok = np.isfinite(d.atr20) & (d.atr20 > 0)
    dd = d[ok]
    ctl_rows.append(pd.DataFrame(dict(idx=idx, date=dd.index, dpts=(dd.c - dd.o).values, atr=dd.atr20.values, cost=MICRO[idx])))
ctl = pd.concat(ctl_rows).sort_values("date").reset_index(drop=True)
ctl["r1"] = (ctl.dpts - ctl.cost) / ctl.atr
ctl_s = rstats(ctl.r1, ctl.dpts - ctl.cost)
out["control_W3_alwayslong_openclose"] = ctl_s
print(f"\n[CONTROL W3] always-long RTH open->close, every IS session, pooled, 1x: {ctl_s}")

# difference: reversed cell minus control. Cell days are a subset of control days.
r_cell = (w3.dpts - w3.cost) / w3.atr
diffW, tW, pW = welch(r_cell, ctl.r1)
# also cell vs complement (disjoint samples) - the cleaner Welch
key = set(zip(w3.idx, w3.date))
mask = np.array([(i, dte) in key for i, dte in zip(ctl.idx, ctl.date)])
comp = ctl.r1[~mask]
diffC, tC, pC = welch(r_cell, comp)
print(f"  matched cell days inside control: {int(mask.sum())} of {len(w3)}")
print(f"  diff cell - control(all sessions): {diffW:+.4f}  Welch t {tW:+.2f} p {pW:.3f}")
print(f"  diff cell - complement(non-cell sessions): {diffC:+.4f}  Welch t {tC:+.2f} p {pC:.3f}  (complement avgR {comp.mean():+.4f}, n {len(comp)})")
out["diff_vs_control_W3"] = dict(method="Welch two-sample t, reversed cell (n=%d) vs unconditional always-long open->close on every IS session (n=%d); cell is a subset of control days. Also cell vs complement." % (len(w3), len(ctl)),
                                 diff_vs_all=diffW, t_vs_all=tW, p_vs_all=pW,
                                 diff_vs_complement=diffC, t_vs_complement=tC, p_vs_complement=pC,
                                 control_n=len(ctl), control_avgR=ctl_s["avgR"], control_t=ctl_s["t"])

# Mondays-only control (the cell is always a Monday-ish first session of the post-opex week)
ctl["dow"] = pd.to_datetime(ctl.date).dt.dayofweek
mon = ctl[ctl.dow == 0]
mon_s = rstats(mon.r1, mon.dpts - mon.cost)
dM, tM, pM = welch(r_cell, mon.r1)
print(f"  [control: all IS Mondays always-long] {mon_s}; cell - Mondays diff {dM:+.4f} Welch t {tM:+.2f}")
out["control_W3_allMondays"] = dict(stats=mon_s, diff=dM, t=tM)

# W4 control: every week Mon open -> Wed close (first session of week -> last session <= Mon+2d), pooled
w4c = []
for idx in IDX:
    d = data[idx]; keys = d.index.tolist(); kser = pd.Series(keys)
    weeks = pd.to_datetime(kser).dt.to_period("W-SUN")
    for wk, grp in kser.groupby(weeks):
        ks = grp.tolist(); ek = ks[0]
        cand = [k for k in ks if k <= ek + dt.timedelta(days=2)]
        xk = cand[-1]
        a = d.atr20[ek]
        if not (np.isfinite(a) and a > 0): continue
        w4c.append(dict(idx=idx, date=ek, dpts=d.c[xk] - d.o[ek], atr=a, cost=MICRO[idx]))
w4c = pd.DataFrame(w4c).sort_values("date").reset_index(drop=True)
w4c["r1"] = (w4c.dpts - w4c.cost) / w4c.atr
w4c_s = rstats(w4c.r1, w4c.dpts - w4c.cost)
r4 = (w4.dpts - w4.cost) / w4.atr
d4, t4, p4 = welch(r4, w4c.r1)
print(f"\n[CONTROL W4] always-long week-first-session open -> (<=Mon+2d) close, every IS week: {w4c_s}")
print(f"  reversed W4 - control diff {d4:+.4f} Welch t {t4:+.2f} p {p4:.3f}")
out["control_W4"] = dict(stats=w4c_s, diff=d4, t=t4, p=p4)

# ---------------- gradient: family's own grid, reversed -----------------
print("\n=== GRADIENT (reversed = LONG on short-arm windows) : scope ladder ===")
grad = {}
for wn in ("W3_postmon", "W4_postmon_wed"):
    for sname, months in (("quarterly", QUARTERLY), ("non-quarterly(8 mo)", NONQ), ("monthly(all)", MONTHLY)):
        f = cell_frame(wn, months)
        s = rstats((f.dpts - f.cost) / f.atr, f.dpts - f.cost)
        grad[f"{wn}|{sname}"] = s
        print(f"  {wn:>15} {sname:>20}: n {s['n']:>4} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
# day-offset ladder: LONG open->close on session k after expiry (k=1 is the cell), and expiry day itself (k=0), pre-expiry k=-1..-4
print("\n=== GRADIENT / PLACEBO: shifted-clock ladder, LONG open->close on session expiry+k (k=1 = reversed cell), monthly, pooled ===")
def offset_cell(k_off, months=MONTHLY):
    rows = []
    for idx in IDX:
        d = data[idx]; keys = d.index.tolist(); pos = {kk: i for i, kk in enumerate(keys)}
        y0, y1 = keys[0].year, keys[-1].year
        for y in range(y0, y1 + 1):
            for m in months:
                tf = third_friday(y, m); mon = tf - dt.timedelta(days=4)
                wk = [kk for kk in keys if mon <= kk <= tf]
                if len(wk) < 3: continue
                expiry = wk[-1]; i = pos[expiry] + k_off
                if i < 0 or i >= len(keys): continue
                ek = keys[i]; a = d.atr20[ek]
                if not (np.isfinite(a) and a > 0): continue
                rows.append(dict(idx=idx, date=ek, dpts=d.c[ek] - d.o[ek], atr=a, cost=MICRO[idx]))
    return pd.DataFrame(rows)
ladder = {}
for k in range(-4, 8):
    f = offset_cell(k)
    s = rstats((f.dpts - f.cost) / f.atr, f.dpts - f.cost)
    ladder[k] = s
    tag = " <== reversed cell (post-opex Monday)" if k == 1 else (" (expiry Friday)" if k == 0 else "")
    print(f"  expiry{k:+d}: n {s['n']:>4} avgR {s['avgR']:+.4f} t {s['t']:+.2f}{tag}")
out["gradient_scope"] = grad
out["ladder_session_offset"] = {int(k): v for k, v in ladder.items()}

# placebo: shifted day - Monday one week after post-opex Monday (expiry+6 sessions ~ next Monday), and the Monday of opex week (expiry-4)
print("\n=== PLACEBO (reversed): same LONG open->close on the Monday-class sessions one week later / one week earlier ===")
plc = {}
for name, k in (("opex-week Monday (expiry-4)", -4), ("post-opex Monday +1wk (expiry+6)", 6), ("post-opex Monday +2wk (expiry+11)", 11)):
    f = offset_cell(k)
    s = rstats((f.dpts - f.cost) / f.atr, f.dpts - f.cost)
    plc[name] = s
    print(f"  {name}: {s}")
# sub-scope placebo: all NON-post-opex Mondays
nonpost = mon[~np.array([(i, dte) in key for i, dte in zip(mon.idx, mon.date)])]
s = rstats(nonpost.r1, nonpost.dpts - nonpost.cost); plc["all non-post-opex Mondays"] = s
print(f"  all non-post-opex IS Mondays always-long: {s}")
out["placebo"] = plc

json.dump(out, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_19.json", "w"), indent=1, default=float)
print("\nwrote r72a_19.json")
