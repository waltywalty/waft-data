"""Round 72A step 3, attempt 24 (r46b FOMC-cycle even-week): REVERSED cell at IS ONLY.
Registered cell = LONG week0 (cycle days 0-4) / RTH open->close, SPX/NDX/RTY pooled,
ATR20-normalized, micro cost per RT subtracted.  Reversed cell = SHORT same window.
IS cut = runner's keys[int(len(keys)*0.75)] per instrument; rows with oos=True are
dropped immediately after build and never touched.  No OOS file is opened.
Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, json, warnings, re, sys, os
sys.path.insert(0, os.getcwd())
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's MICRO dict, verbatim

lsrc = open("run_r42l_fomc.py").read()
FOMC = sorted(pd.to_datetime(re.search(r'FOMC = """(.*?)"""', lsrc, re.S).group(1).split()).date)
print(f"FOMC calendar: {len(FOMC)} meetings {FOMC[0]}..{FOMC[-1]}")


def build_days_IS(idx):
    """Verbatim copy of the runner's build_days, then IS filter applied before return."""
    rth = rth_of(load_frame(idx))
    d = rth.groupby("skey").agg(o=("open", "first"), c=("close", "last"),
                                hi=("high", "max"), lo=("low", "min"))
    d = d[np.isfinite(d.o) & np.isfinite(d.c)]
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d = d[[k >= FOMC[0] for k in d.index]]
    keys = d.index.tolist()
    pos = {k: i for i, k in enumerate(keys)}
    anchors = []
    for f in FOMC:
        cand = [k for k in keys if k >= f]
        if cand:
            anchors.append(pos[cand[0]])
    cycday = np.full(len(keys), 999)
    for i in range(len(keys)):
        prior = [a for a in anchors if a <= i]
        if prior:
            cycday[i] = i - prior[-1]
    d["cyc"] = cycday
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    d_is = d[~d.oos].copy()                      # OOS FIREWALL: drop holdout rows here
    assert d_is.index.max() < cutd
    d_is["idx"] = idx
    d_is["date"] = pd.to_datetime(d_is.index)
    return d_is, cutd


def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 10: return dict(n=int(len(r)))
    w, ls = r[r > 0], r[r <= 0]
    m = len(r) // 2
    return dict(n=int(len(r)), wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avgR=float(r.mean()),
                t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else float("nan"),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se)


data, cuts = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days_IS(idx)
    data[idx] = d; cuts[idx] = str(cutd)
    print(f"{idx}: IS cut date {cutd} | IS sessions {len(d)} {d.index.min()}..{d.index.max()}")

IDX = pd.concat([data[i] for i in ("SPX", "NDX", "RTY")]).sort_values(["date", "idx"])
ok = np.isfinite(IDX.atr20) & (IDX.atr20 > 0) & np.isfinite(IDX.prevc)
IDX = IDX[ok].copy()
G = data["GOLD"]; G = G[np.isfinite(G.atr20) & (G.atr20 > 0) & np.isfinite(G.prevc)].copy()


def rev_R(df, hold, k):
    """Reversed (SHORT) return in ATR units at cost multiple k: -(exit - entry) - k*micro."""
    ecol, xcol = {"oc": ("o", "c"), "cc": ("prevc", "c")}[hold]
    micro = df.idx.map(MICRO).values
    return (-(df[xcol].values - df[ecol].values) - k * micro) / df.atr20.values


def in_scope(cyc, scope):
    if scope == "even":
        return ((cyc <= 4) | ((cyc >= 10) & (cyc <= 14)) | ((cyc >= 20) & (cyc <= 24)))
    if scope == "odd_diag":
        return (((cyc >= 5) & (cyc <= 9)) | ((cyc >= 15) & (cyc <= 19)))
    a, z = {"week0": (0, 4), "week2": (10, 14)}[scope]
    return (cyc >= a) & (cyc <= z)


out = dict(is_cuts=cuts, note="IS only; reversed = SHORT; costs subtracted at k x MICRO")

# ---------- reversed candidate cell: SHORT week0 / oc ----------
cell = IDX[in_scope(IDX.cyc.values, "week0")].copy()
res = {}
for k in (1.0, 1.5, 2.0):
    res[f"x{k}"] = stats(rev_R(cell, "oc", k))
cell["R1"] = rev_R(cell, "oc", 1.0)
# halves in the runner's ordering (instrument-major) for cross-check
runner_order = pd.concat([cell[cell.idx == i] for i in ("SPX", "NDX", "RTY")])
res["halves_runner_order_x1"] = stats(runner_order.R1)["halves"]
res["per_year_x1"] = {int(y): dict(n=int(len(g)), avgR=float(g.R1.mean()),
                                   sign=float(np.sign(g.R1.mean())))
                      for y, g in cell.groupby(cell.date.dt.year)}
res["per_instrument_x1"] = {i: stats(cell[cell.idx == i].R1) for i in ("SPX", "NDX", "RTY")}
res["per_cycle_day_x1"] = {int(c): stats(cell[cell.cyc == c].R1) for c in range(5)}
res["week0_ex_day0_x1"] = stats(cell[cell.cyc >= 1].R1)
res["week0_ex_day0_x2"] = stats(rev_R(cell[cell.cyc >= 1], "oc", 2.0))
res["day0_only_x1"] = stats(cell[cell.cyc == 0].R1)
res["gold_diag_x1"] = stats(rev_R(G[in_scope(G.cyc.values, "week0")], "oc", 1.0))
out["reversed_week0_oc"] = res

print("\n=== REVERSED CELL: SHORT week0 (cycle days 0-4) / RTH open->close, SPX/NDX/RTY pooled, IS ===")
for k in ("x1.0", "x1.5", "x2.0"):
    s = res[k]; print(f"  cost {k}: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} WR {s['wr']*100:.1f}% PF {s['pf']:.3f} halves(chrono) {s['halves']}")
print(f"  halves in runner (instrument-major) order @x1: {res['halves_runner_order_x1']}")
print("  per-year @x1: " + " ".join(f"{y}:{v['sign']:+.0f}({v['avgR']:+.3f},n{v['n']})" for y, v in res["per_year_x1"].items()))
print("  per-instrument @x1: " + " | ".join(f"{i}: n {v['n']} avgR {v['avgR']:+.3f} t {v['t']:+.2f}" for i, v in res["per_instrument_x1"].items()))
print("  per-cycle-day @x1: " + " | ".join(f"d{c}: n {v['n']} avgR {v['avgR']:+.3f} t {v['t']:+.2f}" for c, v in res["per_cycle_day_x1"].items()))
s = res["week0_ex_day0_x1"]; print(f"  week0 EXCLUDING day 0 @x1: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f} halves {s['halves']}")
s = res["week0_ex_day0_x2"]; print(f"  week0 EXCLUDING day 0 @x2: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f}")
s = res["gold_diag_x1"]; print(f"  GOLD diagnostic reversed @x1: n {s['n']} avgR {s['avgR']:+.4f} t {s['t']:+.2f}")

# ---------- unconditional control: SHORT RTH open->close on EVERY eligible IS session ----------
IDX["R1oc"] = rev_R(IDX, "oc", 1.0)
ctrl = stats(IDX.R1oc)
comp = IDX[~in_scope(IDX.cyc.values, "week0")]
d_all, t_all = welch(cell.R1, IDX.R1oc)
d_cmp, t_cmp = welch(cell.R1, comp.R1oc)
out["control_short_oc_all_sessions_x1"] = ctrl
out["control_per_instrument_x1"] = {i: stats(IDX[IDX.idx == i].R1oc) for i in ("SPX", "NDX", "RTY")}
out["diff_vs_control"] = dict(cell_minus_all=dict(avgR=d_all, t=t_all, method="Welch, cell vs all eligible sessions (cell is a subset of control)"),
                              cell_minus_complement=dict(avgR=d_cmp, t=t_cmp, n_comp=int(len(comp)),
                                                         method="Welch, cell vs non-week0 sessions (independent samples)"))
print("\n=== UNCONDITIONAL CONTROL: SHORT RTH open->close every eligible IS session, same 1x cost ===")
print(f"  control: n {ctrl['n']} avgR {ctrl['avgR']:+.4f} t {ctrl['t']:+.2f} WR {ctrl['wr']*100:.1f}% PF {ctrl['pf']:.3f} halves {ctrl['halves']}")
print("  per-instrument: " + " | ".join(f"{i}: n {v['n']} avgR {v['avgR']:+.3f} t {v['t']:+.2f}" for i, v in out["control_per_instrument_x1"].items()))
print(f"  reversed - control(all):        d {d_all:+.4f}  Welch t {t_all:+.2f}")
print(f"  reversed - complement(non-wk0): d {d_cmp:+.4f}  Welch t {t_cmp:+.2f}  (n_comp {len(comp)})")

# ---------- gradient: family's own grid, reversed (all 8 cells, both holds) ----------
grid = {}
print("\n=== GRADIENT: family grid reversed (SHORT), IS, cost x1 ===")
for scope in ("week0", "week2", "even", "odd_diag"):
    for hold in ("oc", "cc"):
        sub = IDX[in_scope(IDX.cyc.values, scope)]
        st = stats(rev_R(sub, hold, 1.0)); grid[f"{scope}/{hold}"] = st
        print(f"  {scope:>9}/{hold}: n {st['n']} avgR {st['avgR']:+.4f} t {st['t']:+.2f} halves {st['halves']}")
out["gradient_grid_reversed_x1"] = grid
# cycle-day ladder 0..29 reversed oc (how localized is the effect?)
ladder = {}
print("  cycle-day ladder, SHORT oc @x1 (n, avgR, t):")
for c in range(0, 30):
    sub = IDX[IDX.cyc == c]
    if len(sub) >= 10:
        st = stats(rev_R(sub, "oc", 1.0)); ladder[c] = st
        print(f"    day {c:>2}: n {st['n']:>4} avgR {st['avgR']:+.4f} t {st['t']:+.2f}")
out["cycle_day_ladder_short_oc_x1"] = {int(k): v for k, v in ladder.items()}
# widening window around the registered cell: days 0-k for k = 0..9
widen = {}
print("  widening window SHORT oc @x1, days 0..k:")
for kk in range(0, 10):
    sub = IDX[IDX.cyc <= kk]
    st = stats(rev_R(sub, "oc", 1.0)); widen[kk] = st
    print(f"    days 0-{kk}: n {st['n']} avgR {st['avgR']:+.4f} t {st['t']:+.2f}")
out["widening_window_short_oc_x1"] = widen

# ---------- placebo: family's own placebo (odd-week diagnostic) reversed + shifted-clock windows ----------
plc = {}
print("\n=== PLACEBO (reversed SHORT oc @x1) ===")
# pre-announcement window: last 5 sessions before each anchor (sessions whose next anchor is 1-5 sessions ahead)
nxt = {}
for idx in ("SPX", "NDX", "RTY"):
    d = data[idx]; keys = d.index.tolist(); cyc = d.cyc.values
    zeros = [i for i, c in enumerate(cyc) if c == 0]
    dist = np.full(len(keys), 999)
    for i in range(len(keys)):
        fut = [zp for zp in zeros if zp > i]
        if fut: dist[i] = fut[0] - i
    nxt[idx] = pd.Series(dist, index=keys)
IDX["to_next"] = [nxt[r.idx].get(r.Index, 999) for r in IDX.itertuples()]
PLACEBOS = {"odd_diag_wk1 days5-9": IDX[(IDX.cyc >= 5) & (IDX.cyc <= 9)],
            "odd_diag_wk3 days15-19": IDX[(IDX.cyc >= 15) & (IDX.cyc <= 19)],
            "shift+2 days2-6": IDX[(IDX.cyc >= 2) & (IDX.cyc <= 6)],
            "shift+3 days3-7": IDX[(IDX.cyc >= 3) & (IDX.cyc <= 7)],
            "shift-5 pre-announcement (next anchor 1-5 sessions ahead)": IDX[(IDX.to_next >= 1) & (IDX.to_next <= 5)]}
for name, sub in PLACEBOS.items():
    st = stats(rev_R(sub, "oc", 1.0)); plc[name] = st
    print(f"  {name}: n {st['n']} avgR {st['avgR']:+.4f} t {st['t']:+.2f} halves {st['halves']}")
out["placebo_reversed_x1"] = plc

# ---------- survivor bar ----------
r1, r2 = res["x1.0"], res["x2.0"]
bar = dict(t_x1_ge_2=r1["t"] >= 2, avgR_x2_pos=r2["avgR"] > 0,
           halves_pos=(r1["halves"][0] > 0 and r1["halves"][1] > 0),
           diff_vs_control_pos_t2=(d_all > 0 and t_all >= 2))
out["bar"] = bar
print("\n=== SURVIVOR BAR (gradient judged by hand) ===")
for k, v in bar.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
json.dump(out, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_24.json", "w"),
          indent=1, default=float)
print("\nwrote r72a_24.json")
