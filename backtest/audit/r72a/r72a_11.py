"""Round 72A step 3, attempt 11 (r42k_macro): reversed NFP 08:00->12:00 cell, IS ONLY.
Frame build copied verbatim from run_r42k_macro.py (same ATR20, same NFP label,
same cut keys[int(len*0.75)]); every row with oos=True is dropped before any
return is computed. Never opens any *oos* file. Run from backtest/."""
import pandas as pd, numpy as np, json, warnings, sys, os
sys.path.insert(0, os.getcwd())  # run from backtest/ so index_data and run_r37_scalps resolve
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35}

def st(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 2: return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]; m = len(r) // 2
    return dict(n=int(len(r)), avg=float(r.mean()),
                t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se)

# ---------------- frame build (verbatim from run_r42k_macro.py, plus extra exit/entry prints) ----
LB_TIMES = [900, 930, 1000, 1030, 1100, 1130, 1200, 1230, 1300, 1400, 1500]
PRE_TIMES = [600, 630, 700, 730, 800, 815, 830, 845, 900, 915]
frames, split = {}, {}
for idx in MICRO:
    b24 = load_frame(idx)
    rth = rth_of(b24)
    rows_d = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        c, o = g.close.values, g.open.values
        if len(g) < 50 or hm[0] > 935: continue
        def lb(t):
            m = np.where(hm < t)[0]
            return c[m[-1]] if len(m) else np.nan
        row = dict(skey=skey, o=o[0], cEnd=c[-1], hi=g.high.max(), lo=g.low.min())
        for t in LB_TIMES: row[f"c{t}"] = lb(t)   # c1200 == runner's c1200 (last close before 12:00)
        rows_d.append(row)
    pre = {t: {} for t in PRE_TIMES}
    for skey, g in b24.groupby("skey"):
        m = g.hm.values; ov = g.open.values
        for t in PRE_TIMES:
            i8 = np.where(m == t)[0]
            pre[t][skey] = ov[i8[0]] if len(i8) else np.nan
    d = pd.DataFrame(rows_d).set_index("skey")
    for t in PRE_TIMES:
        d[f"o{t}"] = pd.Series(d.index.map(lambda k: pre[t].get(k, np.nan)), index=d.index)
    d["c0800"] = d["o800"]                     # runner's c0800 = open of the 08:00 bar
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    dts = pd.to_datetime(pd.Series(d.index, index=d.index).astype(str))
    d["date"] = dts
    d["nfp"] = (dts.dt.dayofweek == 4) & (dts.dt.day <= 7)
    d["friday"] = dts.dt.dayofweek == 4
    d["dom"] = dts.dt.day
    d["prev_cEnd"] = d.cEnd.shift(1)
    d["nfp_prev"] = d.nfp.shift(-1, fill_value=False)   # session before an NFP session
    d["nfp_next"] = d.nfp.shift(1, fill_value=False)    # session after an NFP session
    d = d[np.isfinite(d.atr20) & (d.atr20 > 0)]
    cutd = d.index.tolist()[int(len(d) * 0.75)]        # runner's cut, identical formula
    d["oos"] = d.index >= cutd
    split[idx] = str(cutd)
    d = d[~d.oos].copy()                                # ---- OOS FIREWALL: IS rows only from here
    d["idx"] = idx
    frames[idx] = d
    print(f"{idx}: IS cut {cutd} (runner split {split[idx]}), IS sessions {len(d)}, "
          f"IS range {d.date.min().date()} .. {d.date.max().date()}")

stored = json.load(open("results/r42k_macro.json"))["split"]
assert stored == split, (stored, split)
print("IS cuts match results/r42k_macro.json split:", split)

allis = pd.concat(frames.values()).sort_values("date")

# NOTE: allis has duplicate skey index across instruments; work with positional Series.
allis = allis.reset_index().rename(columns={"index": "skey"})
def R(mask, pnl_pts, k=1.0):
    m = mask & np.isfinite(pnl_pts)
    s = allis[m]
    r = (pnl_pts[m] - s.idx.map(MICRO) * k) / s.atr20
    out = pd.DataFrame(dict(r=r.values, date=s.date.values, idx=s.idx.values)).sort_values("date")
    return out

short_0800_1200 = allis.c0800 - allis.c1200          # SHORT: entry 08:00 open, exit last close before 12:00
elig = np.isfinite(allis.c0800) & np.isfinite(allis.c1200)

print("\n=== REVERSED CELL: SHORT indices, NFP day 08:00 -> 12:00, IS only, pooled, ATR20 units ===")
rev = {}
for k in (1.0, 1.5, 2.0):
    o = R(allis.nfp & elig, short_0800_1200, k); rev[k] = o
    a = st(o.r)
    print(f"  cost x{k}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} WR {a['wr']*100:.1f}% PF {a['pf']:.3f} halves(chrono) {a['halves']}")
o1 = rev[1.0]
# runner-order halves (concat SPX, NDX, RTY) for comparison
ro = pd.concat([R((allis.nfp & elig & (allis.idx == i)), short_0800_1200, 1.0) for i in MICRO])
m = len(ro) // 2
print(f"  halves in runner concat order (SPX,NDX,RTY): [{np.sign(ro.r.values[:m].mean()):+.0f},{np.sign(ro.r.values[m:].mean()):+.0f}]")
print("  gross (no cost):", {k: round(v, 4) for k, v in st(R(allis.nfp & elig, short_0800_1200, 0.0).r).items() if k in ('avg', 't')})
print("  per instrument x1:")
for i in MICRO:
    a = st(o1[o1.idx == i].r)
    print(f"    {i}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} WR {a['wr']*100:.1f}% PF {a['pf']:.3f}")
print("  per-year (pooled, x1):")
yr = o1.groupby(pd.to_datetime(o1.date).dt.year).r.agg(['count', 'mean'])
signs = "".join("+" if v > 0 else "-" for v in yr['mean'])
for y, rw in yr.iterrows(): print(f"    {y}: n {int(rw['count'])} avgR {rw['mean']:+.4f}")
print("  per-year signs:", signs, f"({(yr['mean']>0).sum()} of {len(yr)} positive)")

print("\n=== UNCONDITIONAL CONTROL: always-SHORT 08:00 -> 12:00, EVERY eligible IS session, x1 ===")
ctl = R(elig, short_0800_1200, 1.0); a = st(ctl.r)
print(f"  n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} WR {a['wr']*100:.1f}% PF {a['pf']:.3f} halves {a['halves']}")
comp = R(elig & ~allis.nfp, short_0800_1200, 1.0); ac = st(comp.r)
print(f"  complement (non-NFP sessions): n {ac['n']} avgR {ac['avg']:+.4f} t {ac['t']:+.2f}")
d1, t1 = welch(o1.r, comp.r)
d2, t2 = welch(o1.r, ctl.r)
print(f"  DIFF reversed - complement (Welch, disjoint samples): {d1:+.4f}R  t {t1:+.2f}")
print(f"  DIFF reversed - full control (Welch, overlapping; for reference): {d2:+.4f}R  t {t2:+.2f}")
# halves of the differential
mm = len(o1) // 2
cd = pd.to_datetime(o1.date)
h1 = o1.r.values[:mm].mean() - comp[pd.to_datetime(comp.date) <= cd.iloc[mm-1]].r.mean()
h2 = o1.r.values[mm:].mean() - comp[pd.to_datetime(comp.date) > cd.iloc[mm-1]].r.mean()
print(f"  differential halves: [{h1:+.4f}, {h2:+.4f}]")
print("  Friday-only control (always-short 08:00->12:00 on non-NFP Fridays):",
      {k: round(v, 4) for k, v in st(R(elig & allis.friday & ~allis.nfp, short_0800_1200, 1.0).r).items() if k in ('n', 'avg', 't')})

print("\n=== GRADIENT (reversed = SHORT, NFP days, x1 cost) ===")
print("  (a) family's own frozen grid, reversed:")
for name, pnl, mask in [("SHORT NFP prevclose->close", allis.prev_cEnd - allis.cEnd, allis.nfp & np.isfinite(allis.prev_cEnd)),
                        ("SHORT NFP 0800->1200", short_0800_1200, allis.nfp & elig),
                        ("SHORT NFP 0930->close", allis.o - allis.cEnd, allis.nfp)]:
    a = st(R(mask, pnl, 1.0).r)
    print(f"    {name:>28}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} halves {a['halves']}")
print("  (b) exit-time ladder, entry 08:00 open fixed, SHORT NFP days:")
grad_exit = {}
for t in [930, 1000, 1030, 1100, 1130, 1200, 1230, 1300, 1400, 1500, 1555]:
    px = allis.o if t == 930 else (allis.cEnd if t == 1555 else allis[f"c{t}"])
    pnl = allis.c0800 - px
    a = st(R(allis.nfp & np.isfinite(allis.c0800) & np.isfinite(px), pnl, 1.0).r); grad_exit[t] = a
    print(f"    08:00 -> {t:>4}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")
print("  (c) entry-time ladder, exit 12:00 fixed, SHORT NFP days:")
for t in PRE_TIMES:
    pnl = allis[f"o{t}"] - allis.c1200
    a = st(R(allis.nfp & np.isfinite(allis[f"o{t}"]) & np.isfinite(allis.c1200), pnl, 1.0).r)
    print(f"    {t:>4} -> 12:00: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")
print("  (d) sub-windows of 08:00->12:00 (SHORT NFP): where does the reversed edge sit?")
for a_, b_ in [(800, 830), (830, 900), (900, 930), (930, 1000), (1000, 1100), (1100, 1200)]:
    pa = allis[f"o{a_}"] if a_ < 930 else (allis.o if a_ == 930 else allis[f"c{a_}"])
    pb = allis[f"o{b_}"] if b_ < 930 else (allis.o if b_ == 930 else allis[f"c{b_}"])
    a = st(R(allis.nfp & np.isfinite(pa) & np.isfinite(pb), pa - pb, 0.0).r)   # GROSS, sub-window
    print(f"    {a_:>4}->{b_:>4} gross: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")

print("\n=== PLACEBO (SHORT 08:00 -> 12:00, x1 cost) ===")
plac = {}
for name, mask in [("2nd Friday (dom 8-14)", allis.friday & (allis.dom >= 8) & (allis.dom <= 14)),
                   ("3rd Friday (dom 15-21)", allis.friday & (allis.dom >= 15) & (allis.dom <= 21)),
                   ("4th/5th Friday (dom>=22)", allis.friday & (allis.dom >= 22)),
                   ("all non-NFP Fridays", allis.friday & ~allis.nfp),
                   ("session before NFP (Thu)", allis.nfp_prev),
                   ("session after NFP (Mon)", allis.nfp_next),
                   ("first-week non-Friday (dom<=7, Mon-Thu)", (allis.dom <= 7) & ~allis.friday),
                   ("all non-NFP sessions", ~allis.nfp)]:
    a = st(R(mask & elig, short_0800_1200, 1.0).r); plac[name] = a
    print(f"  {name:>40}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")
print("  shifted clock on NFP days (SHORT):")
for name, pnl in [("12:00 -> 15:55", allis.c1200 - allis.cEnd), ("prev close -> 08:00", allis.prev_cEnd - allis.c0800)]:
    a = st(R(allis.nfp & np.isfinite(pnl), pnl, 1.0).r)
    print(f"    {name:>22}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")

# ---- watch #6 (turn-of-month) split: NFP by trading day of month
allis["tdm"] = allis.groupby([allis.idx, allis.date.dt.year, allis.date.dt.month]).cumcount() + 1
print("\n=== INDEPENDENCE: SHORT NFP 08:00->12:00 by trading-day-of-month (x1) ===")
for name, mask in [("NFP td<=3", allis.nfp & (allis.tdm <= 3)), ("NFP td>=4", allis.nfp & (allis.tdm >= 4))]:
    a = st(R(mask & elig, short_0800_1200, 1.0).r)
    print(f"  {name}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")
for name, mask in [("non-NFP td<=3 always-short", ~allis.nfp & (allis.tdm <= 3)), ("non-NFP td>=4 always-short", ~allis.nfp & (allis.tdm >= 4))]:
    a = st(R(mask & elig, short_0800_1200, 1.0).r)
    print(f"  {name}: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f}")

out = dict(split=split, reversed={str(k): st(v.r) for k, v in rev.items()}, control=st(ctl.r),
           complement=st(comp.r), diff_vs_complement=dict(avgR=d1, t=t1), diff_vs_full=dict(avgR=d2, t=t2),
           per_year_signs=signs, grad_exit={str(k): v for k, v in grad_exit.items()}, placebo=plac)
json.dump(out, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_11.json", "w"), indent=1, default=float)

# ---- reproduction check: registered LONG cell with the runner's stats() (ddof=0), must equal results JSON IS block
def runner_stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    return dict(n=int(len(p)), avg_R=float(r.mean()), t=float(r.mean() / r.std() * np.sqrt(len(r))), wr=float((p > 0).mean()))
chk = pd.concat([allis[(allis.idx == i) & allis.nfp & elig].assign(pnl=lambda s: s.c1200 - s.c0800 - MICRO[i]) for i in MICRO])
print("\nREPRO registered LONG NFP 0800->1200 (runner order, ddof=0):", runner_stats(chk.pnl, chk.atr20))
print("stored JSON IS block:", {k: v for k, v in json.load(open("results/r42k_macro.json"))["grid"][1]["IS"].items() if k in ("n", "avg_R", "t", "wr")})
