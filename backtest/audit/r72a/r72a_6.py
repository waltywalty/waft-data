"""R72A step-3 reversed scoring, attempt 6 (overnight-drift / European-open window).
IS ONLY. Reuses the runner's build() logic (copied verbatim from run_r42f_ondrift.py,
which itself execs load_frame from run_r37_scalps.py). Never touches OOS rows.
Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, json, warnings, sys
from scipy import stats as sps
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
# registered grid + gradient/placebo ladder (all clock windows, ET, [a,z))
WINDOWS = {"0100-0400": (100, 400), "0200-0330": (200, 330), "0230-0330": (230, 330),
           # gradient: sub-windows and nested widenings around the headline cell
           "0230-0300": (230, 300), "0300-0330": (300, 330), "0200-0400": (200, 400),
           "0230-0400": (230, 400), "0130-0330": (130, 330),
           # placebo: same-length (1h) windows shifted by whole hours
           "2330-0030": (2330, 2400), "0030-0130": (30, 130), "0130-0230": (130, 230),
           "0330-0430": (330, 430), "0430-0530": (430, 530), "0530-0630": (530, 630),
           "0630-0730": (630, 730), "0730-0830": (730, 830)}
FILTS = ("all", "prev_down")


def build(idx):
    b = load_frame(idx)
    rows = []
    for skey, g in b.groupby("skey"):
        hm = g.hm.values
        rec = dict(skey=skey, hi=g.high.max(), lo=g.low.min(), c=g.close.values[-1])
        for wname, (a, z) in WINDOWS.items():
            m = (hm >= a) & (hm < z)
            if m.sum() >= max(3, (z - a) // 15):
                rec[f"e_{wname}"] = g.open.values[np.argmax(m)]
                rec[f"x_{wname}"] = g.close.values[len(m) - 1 - np.argmax(m[::-1])]
        rows.append(rec)
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prev_ret"] = d.c.pct_change().shift(0)
    d["prev_down"] = d.prev_ret.shift(1) < 0
    return d


def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 10:
        return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]
    m = len(r) // 2
    return dict(n=int(len(r)), wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avg_R=float(r.mean()), t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))],
                half_means=[float(r[:m].mean()), float(r[m:].mean())])


frames = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d = build(idx)
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]           # runner's own IS cut
    d = d[d.index < cutd].copy()                  # IS ONLY - OOS rows dropped here
    d["idx"] = idx
    frames[idx] = d
    print(f"{idx}: IS cut {cutd} (sessions before cut kept: {len(d)}; last IS session {d.index[-1]})")


def cell(wname, filt, insts=("SPX", "NDX", "RTY")):
    """Reversed (SHORT) trades for a window/filter, pooled over insts, sorted by date.
    Returns DataFrame with gross pnl (points), cost (points), atr, date, idx."""
    subs = []
    for idx in insts:
        d = frames[idx]
        if f"e_{wname}" not in d:
            continue
        m = np.isfinite(d[f"e_{wname}"]) & np.isfinite(d[f"x_{wname}"]) & np.isfinite(d.atr20) & (d.atr20 > 0)
        if filt == "prev_down":
            m &= d.prev_down
        s = d[m]
        subs.append(pd.DataFrame(dict(date=s.index, gross=(s[f"e_{wname}"] - s[f"x_{wname}"]).values,
                                      cost=MICRO[idx], atr=s.atr20.values, idx=idx)))
    sub = pd.concat(subs, ignore_index=True).sort_values(["date", "idx"]).reset_index(drop=True)
    return sub


def R(sub, k):
    return (sub.gross - k * sub.cost) / sub.atr


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t, p = sps.ttest_ind(a, b, equal_var=False)
    return float(a.mean() - b.mean()), float(t), float(p)


out = {}
print("\n=== HEADLINE REVERSED CELL: SHORT 0230-0330 ET / all, SPX+NDX+RTY pooled, IS only ===")
hc = cell("0230-0330", "all")
res = {}
for k in (1.0, 1.5, 2.0):
    res[k] = stats(R(hc, k))
    print(f"cost x{k}: n {res[k]['n']} avgR {res[k]['avg_R']:+.4f} t {res[k]['t']:+.2f} WR {res[k]['wr']*100:.1f}% "
          f"PF {res[k]['pf']:.3f} halves(chrono) {res[k]['halves']} half_means {np.round(res[k]['half_means'],4).tolist()}")
g0 = stats(R(hc, 0.0))
print(f"gross (x0): avgR {g0['avg_R']:+.4f} t {g0['t']:+.2f}")
r1 = R(hc, 1.0)
yrs = pd.to_datetime(hc.date).dt.year
py = r1.groupby(yrs).agg(["mean", "count"])
py["t"] = r1.groupby(yrs).apply(lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)))
print("per-year (x1):"); print(py.round(4).to_string())
signs = "".join("+" if v > 0 else "-" for v in py["mean"])
print("per-year signs:", signs, f"({(py['mean']>0).sum()}/{len(py)} positive)")
print("per-instrument (x1):")
for idx in ("SPX", "NDX", "RTY"):
    s = stats(r1[hc.idx == idx]); print(f"  {idx}: n {s['n']} avgR {s['avg_R']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
gd = cell("0230-0330", "all", ("GOLD",))
for k in (1.0, 2.0):
    s = stats(R(gd, k)); print(f"  GOLD sibling short x{k}: n {s['n']} avgR {s['avg_R']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
out["headline"] = dict(cost={str(k): v for k, v in res.items()}, gross=g0, per_year=py.round(5).to_dict(), per_year_signs=signs)

print("\n=== CONTROL: always-SHORT over the same window on EVERY eligible IS session (x1) ===")
ctl = cell("0230-0330", "all")   # identical construction: the headline cell has filter=all
cs = stats(R(ctl, 1.0))
print(f"control: n {cs['n']} avgR {cs['avg_R']:+.4f} t {cs['t']:+.2f}")
print("NOTE: the headline cell IS the unconditional window (filter = all); reversed minus control = 0 by construction.")
d_avg, d_t, d_p = welch(R(hc, 1.0), R(ctl, 1.0))
print(f"diff reversed-control (Welch, identical samples): {d_avg:+.5f} t {d_t:+.2f}")
out["control"] = cs

print("\n--- secondary: reversed prev_down cell vs its complement (Welch) and vs control ---")
pdc = cell("0230-0330", "prev_down")
ps = stats(R(pdc, 1.0))
print(f"short 0230-0330 / prev_down: n {ps['n']} avgR {ps['avg_R']:+.4f} t {ps['t']:+.2f} halves {ps['halves']}")
comp_mask = ~ctl.set_index(["date", "idx"]).index.isin(pdc.set_index(["date", "idx"]).index)
comp = R(ctl, 1.0)[comp_mask]
da, dt, dp = welch(R(pdc, 1.0), comp)
print(f"prev_down minus complement (prev_up/flat): diff {da:+.4f} Welch t {dt:+.2f} p {dp:.3g}")
da2, dt2, _ = welch(R(pdc, 1.0), R(ctl, 1.0))
print(f"prev_down minus full control (overlapping, Welch): diff {da2:+.4f} t {dt2:+.2f}")

print("\n=== GRADIENT: reversed (short) across the registered grid + nested windows, x1 and x2, IS ===")
print(f"{'window':>10} {'filt':>9} | {'n':>6} {'gross':>8} {'x1 avgR':>8} {'x1 t':>7} {'x2 avgR':>8} {'x2 t':>7} {'halves':>12} | {'GOLD x1':>8}")
grad = {}
for w in ("0100-0400", "0200-0400", "0130-0330", "0200-0330", "0230-0400", "0230-0330", "0230-0300", "0300-0330"):
    for f in FILTS:
        c = cell(w, f)
        s0, s1, s2 = stats(R(c, 0)), stats(R(c, 1)), stats(R(c, 2))
        gg = stats(R(cell(w, f, ("GOLD",)), 1))
        grad[f"{w}/{f}"] = dict(n=s1["n"], gross=s0["avg_R"], x1=s1["avg_R"], t1=s1["t"], x2=s2["avg_R"], t2=s2["t"], halves=s1["halves"], gold_x1=gg.get("avg_R"))
        print(f"{w:>10} {f:>9} | {s1['n']:>6} {s0['avg_R']:>+8.4f} {s1['avg_R']:>+8.4f} {s1['t']:>+7.2f} {s2['avg_R']:>+8.4f} {s2['t']:>+7.2f} {str(s1['halves']):>12} | {gg.get('avg_R', float('nan')):>+8.4f}")
out["gradient"] = grad

print("\n=== PLACEBO: same 1h short window shifted by whole hours (filter=all), x1, IS ===")
plc = {}
for w in ("2330-0030", "0030-0130", "0130-0230", "0230-0330", "0330-0430", "0430-0530", "0530-0630", "0630-0730", "0730-0830"):
    c = cell(w, "all")
    if len(c) < 10:
        print(f"{w}: n {len(c)} (insufficient)"); continue
    s0, s1 = stats(R(c, 0)), stats(R(c, 1))
    gg = stats(R(cell(w, "all", ("GOLD",)), 1))
    plc[w] = dict(n=s1["n"], gross=s0["avg_R"], x1=s1["avg_R"], t1=s1["t"], halves=s1["halves"], gold_x1=gg.get("avg_R"))
    print(f"{w:>10} | n {s1['n']:>6} gross {s0['avg_R']:>+8.4f} x1 {s1['avg_R']:>+8.4f} t {s1['t']:>+7.2f} halves {s1['halves']} | GOLD x1 {gg.get('avg_R', float('nan')):+.4f}")
out["placebo"] = plc

print("\n=== PROVENANCE DIAGNOSTIC: mean 5m bar return (close/open-1, bp) by ET clock slot 01:00-04:00, IS, per instrument ===")
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = load_frame(idx)
    cut = frames[idx].index[-1]
    b = b[(pd.Series(b.skey.values, index=b.index) <= cut).values]  # IS sessions only (<= last IS session)
    b = b[(b.hm >= 100) & (b.hm < 400)]
    br = (b.close / b.open - 1) * 1e4
    slot = br.groupby(b.hm).agg(["mean", "count"])
    slot["t"] = br.groupby(b.hm).apply(lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)))
    worst = slot.sort_values("mean").head(4)
    print(f"{idx}: sum of slot means 0230-0330 = {slot.loc[(slot.index>=230)&(slot.index<330),'mean'].sum():+.2f} bp; "
          f"4 most negative slots: " + ", ".join(f"{int(h):04d} {m:+.2f}bp(t{t:+.1f})" for h, m, t in zip(worst.index, worst['mean'], worst['t'])))
    # bar-level: gap (open vs prior close) at each slot
    gap = (b.open / b.close.shift(1) - 1) * 1e4
    same = (b.skey.values[1:] == b.skey.values[:-1]); gap = gap.iloc[1:][same]; hmg = b.hm.iloc[1:][same]
    gs = gap.groupby(hmg).mean().sort_values().head(3)
    print(f"   most negative open-gap slots: " + ", ".join(f"{int(h):04d} {m:+.2f}bp" for h, m in gs.items()))

json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1, default=float)
