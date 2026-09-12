"""Round 72A step 3, attempt 17 (r44_surprise): reversed macro-surprise drift, IS ONLY.
Event set, surprise mapping, ATR20, entry/exit and cut (keys[int(len*0.75)]) copied
verbatim from run_r44_surprise.py. Every event whose entry session is on/after the
instrument's IS cut is skipped BEFORE any return is computed. Never opens any *oos*
file. Run from backtest/.  Candidate cell: th0.5 / entry+60m, SPX/NDX/RTY pooled.
Reversed direction = -1 x (sign(dev) x indicator sign)."""
import pandas as pd, numpy as np, json, warnings, sys, os
sys.path.insert(0, os.getcwd())
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}
OUT = "/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_17.json"

POS = {"Nonfarm Payrolls", "Gross Domestic Product Annualized", "Retail Sales (MoM)",
       "Retail Sales Control Group", "ISM Manufacturing PMI", "ISM Services PMI",
       "Durable Goods Orders"}
NEG = {"Consumer Price Index (YoY)", "Consumer Price Index (MoM)",
       "Consumer Price Index ex Food & Energy (YoY)",
       "Consumer Price Index ex Food & Energy (MoM)"}

raw = open("data/econ_events_us_high_fxs.json").read()
d = json.loads(raw[raw.find('{'):])
if "result" in d: d = d["result"]
evs = []
for e in d["events"]:
    if e["n"] not in POS and e["n"] not in NEG: continue
    if e["dev"] is None or e["a"] is None or e["c"] is None: continue
    sgn = 1 if e["n"] in POS else -1
    evs.append(dict(t=pd.Timestamp(e["d"]), name=e["n"], dev=float(e["dev"]),
                    cls="growth" if sgn > 0 else "inflation",
                    dir=int(np.sign(e["dev"])) * sgn))
# NOTE: the runner drops dev==0 events; keep them in a separate list for the control
# (they are release sessions with no surprise) and for the sub-threshold placebo.
evs_all = evs
evs = [e for e in evs if e["dir"] != 0]
bytime = {}
for e in evs:
    k = e["t"]
    if k not in bytime or abs(e["dev"]) > abs(bytime[k]["dev"]):
        bytime[k] = e
evs = sorted(bytime.values(), key=lambda e: e["t"])
# control event list: all named-set release timestamps (dev==0 included), one per timestamp
bt_all = {}
for e in evs_all:
    k = e["t"]
    if k not in bt_all or abs(e["dev"]) > abs(bt_all[k]["dev"]):
        bt_all[k] = e
evs_ctrl = sorted(bt_all.values(), key=lambda e: e["t"])
print(f"usable surprise events (runner def): {len(evs)}; all named-set release timestamps: {len(evs_ctrl)}")

frames = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = load_frame(idx).tz_convert("UTC")
    atr = (b.groupby("skey").high.max() - b.groupby("skey").low.min()).rolling(20).mean().shift(1)
    keys = sorted(atr.index)
    cutd = keys[int(len(keys) * 0.75)]
    frames[idx] = (b, atr, cutd)
    print(f"IS cut {idx}: sessions with skey < {cutd} only (runner: keys[int(len*0.75)])")


def trades(th, hold, events, shift_days=0, band=None):
    """Per-event window return in the REGISTERED direction (before sign flip), IS only.
    Returns DataFrame: raw = dir_reg*(exit-entry) in points, atr, idx, cls, t, dir_reg.
    band=(lo,hi): keep lo <= |dev| < hi instead of |dev| >= th."""
    subs = []
    for idx, (b, atr, cutd) in frames.items():
        ix = b.index
        rec = []
        for e in events:
            ad = abs(e["dev"])
            if band is None:
                if ad < th: continue
            else:
                if not (band[0] <= ad < band[1]): continue
            t0 = e["t"] + pd.Timedelta(days=shift_days)
            if shift_days:
                # shifted-day placebo: land on a weekday (skip weekends)
                while t0.dayofweek >= 5: t0 -= pd.Timedelta(days=1)
            i0 = ix.searchsorted(t0 + pd.Timedelta(minutes=5))
            if i0 >= len(ix) or (ix[i0] - t0) > pd.Timedelta(hours=2): continue
            skey = b.skey.iloc[i0]
            if skey >= cutd: continue          # OOS FIREWALL: never compute past the cut
            a20 = atr.get(skey, np.nan)
            if not np.isfinite(a20) or a20 <= 0: continue
            entry = b.close.iloc[i0]
            if hold == "60m":
                i1 = ix.searchsorted(ix[i0] + pd.Timedelta(minutes=60))
                if i1 >= len(ix): continue
                exitpx = b.close.iloc[min(i1, len(ix) - 1)]
            else:
                day = b[b.skey == skey]
                hm = day.index.tz_convert("America/New_York")
                m16 = day[(hm.hour * 100 + hm.minute) < 1600]
                if not len(m16): continue
                exitpx = m16.close.iloc[-1]
            rec.append(dict(t=t0, skey=skey, idx=idx, cls=e["cls"], dir_reg=e["dir"],
                            dev=e["dev"], move=float(exitpx - entry), atr=float(a20)))
        subs.append(pd.DataFrame(rec))
    return pd.concat(subs, ignore_index=True)


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
    dd = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(dd), float(dd / se)


def paired(diff):
    diff = np.asarray(diff, float); diff = diff[np.isfinite(diff)]
    return float(diff.mean()), float(diff.mean() / diff.std(ddof=1) * np.sqrt(len(diff)))


def rev_R(df, mult=1.0):
    """Reversed net R: -(registered points) minus mult x micro, ATR-normalised."""
    cost = df.idx.map(MICRO)
    return (-(df.dir_reg * df.move) - mult * cost) / df.atr


def block(df, label):
    df = df[df.idx != "GOLD"].sort_values("t").reset_index(drop=True)
    r1, r15, r2, rg = rev_R(df, 1.0), rev_R(df, 1.5), rev_R(df, 2.0), rev_R(df, 0.0)
    s1, s15, s2, sg = st(r1), st(r15), st(r2), st(rg)
    # runner-order halves (instrument blocks, as the runner concatenates) for reference
    dfr = df.sort_values(["idx", "t"]).reset_index(drop=True)
    hr = st(rev_R(dfr, 1.0))["halves"]
    yrs = {}
    for y, g in df.groupby(df.t.dt.year):
        yrs[int(y)] = (float(np.sign(rev_R(g, 1.0).mean())), int(len(g)))
    print(f"\n--- {label} (reversed, SPX/NDX/RTY pooled, IS only) ---")
    print(f"n {s1['n']}  gross avgR {sg['avg']:+.4f} t {sg['t']:+.2f} | "
          f"x1 avgR {s1['avg']:+.4f} t {s1['t']:+.2f} WR {s1['wr']*100:.1f}% PF {s1['pf']:.3f} halves(time) {s1['halves']} halves(runner-order) {hr} | "
          f"x1.5 avgR {s15['avg']:+.4f} t {s15['t']:+.2f} | x2 avgR {s2['avg']:+.4f} t {s2['t']:+.2f}")
    print("per-year sign (net x1), n:", {y: f"{'+' if v[0] > 0 else '-'}{v[1]}" for y, v in yrs.items()})
    per_idx = {i: st(rev_R(g, 1.0)) for i, g in df.groupby("idx")}
    print("per-instrument x1:", {i: f"n{v['n']} avg{v['avg']:+.4f} t{v['t']:+.2f}" for i, v in per_idx.items()})
    sub = {c: st(rev_R(g, 1.0)) for c, g in df.groupby("cls")}
    print("subclass x1 (diagnostic only):", {c: f"n{v['n']} avg{v['avg']:+.4f} t{v['t']:+.2f} halves{v['halves']}" for c, v in sub.items()})
    longs = int((df.dir_reg < 0).sum()); shorts = int((df.dir_reg > 0).sum())
    print(f"reversed direction mix: long {longs} / short {shorts}")
    return dict(n=s1["n"], gross=sg, x1=s1, x15=s15, x2=s2, halves_runner_order=hr,
                per_year={y: v[0] for y, v in yrs.items()}, per_year_n={y: v[1] for y, v in yrs.items()},
                per_idx=per_idx, subclass=sub, long_n=longs, short_n=shorts, _df=df)


# ---------------- candidate cell: th0.5 / 60m ----------------
cell = block(trades(0.5, "60m", evs), "CELL th0.5 / entry+60m")
df = cell["_df"]

# sanity: registered-direction net x1 should reproduce the JSON (n 781, avgR -0.0209, t -2.16)
reg = st((df.dir_reg * df.move - df.idx.map(MICRO)) / df.atr)
print(f"\nregistered-direction reproduction: n {reg['n']} avgR {reg['avg']:+.4f} t {reg['t']:+.2f} "
      f"(JSON: n 781 avgR -0.0209 t -2.16)")

# ---------------- unconditional control ----------------
# Window = release+5m -> +60m on every named-set release session in IS (dev==0 and
# sub-threshold releases included). Always-long and always-short at 1x micro.
ctl = trades(0.0, "60m", evs_ctrl)
ctl = ctl[ctl.idx != "GOLD"].sort_values("t").reset_index(drop=True)
cost = ctl.idx.map(MICRO)
ctl_long = (ctl.move - cost) / ctl.atr
ctl_short = (-ctl.move - cost) / ctl.atr
sL, sS = st(ctl_long), st(ctl_short)
print(f"\n--- CONTROL: same window (release+5m -> +60m), every named-set release session in IS, x1 micro ---")
print(f"always-long : n {sL['n']} avgR {sL['avg']:+.4f} t {sL['t']:+.2f} halves {sL['halves']}")
print(f"always-short: n {sS['n']} avgR {sS['avg']:+.4f} t {sS['t']:+.2f} halves {sS['halves']}")
# the reversed cell is mixed-direction; the implied direction is the majority side
maj = "long" if cell["long_n"] >= cell["short_n"] else "short"
ctl_maj = ctl_long if maj == "long" else ctl_short
s_maj = sL if maj == "long" else sS
r1 = rev_R(df, 1.0)
w_d, w_t = welch(r1, ctl_maj)
print(f"implied control direction (majority of reversed trades): always-{maj}")
print(f"Welch reversed - always-{maj}: diff avgR {w_d:+.4f} t {w_t:+.2f}")
# paired by (event, instrument): the cell is a subset of the control events
key = ["t", "idx"]
m = df.merge(ctl.assign(cl=ctl_long.values, cs=ctl_short.values)[key + ["cl", "cs"]], on=key, how="inner")
mr = rev_R(m, 1.0)
p_d, p_t = paired(mr - (m.cl if maj == "long" else m.cs))
print(f"paired reversed - always-{maj} on the cell's own events (n {len(m)}): diff avgR {p_d:+.4f} t {p_t:+.2f}")
# per-trade own-direction control is tautological (identical to the cell) - not used.
# Secondary control: every IS session, 08:35 -> 09:35 NY (the modal release clock), always-long/short.
sec = []
for idx, (b, atr, cutd) in frames.items():
    if idx == "GOLD": continue
    bb = b[b.skey < cutd]
    ny = bb.index.tz_convert("America/New_York")
    hm = ny.hour * 100 + ny.minute
    e0 = bb[hm == 835]; e1 = bb[hm == 935]
    c0 = e0.groupby("skey").close.first(); c1 = e1.groupby("skey").close.first()
    j = pd.concat([c0.rename("p0"), c1.rename("p1")], axis=1).dropna()
    j["atr"] = atr.reindex(j.index).values; j = j[np.isfinite(j.atr) & (j.atr > 0)]
    j["idx"] = idx; sec.append(j)
sec = pd.concat(sec)
secL = (sec.p1 - sec.p0 - sec.idx.map(MICRO)) / sec.atr
sL2 = st(secL); sS2 = st(-(sec.p1 - sec.p0) / sec.atr - sec.idx.map(MICRO) / sec.atr)
print(f"secondary control, EVERY IS session 08:35->09:35 NY: always-long n {sL2['n']} avgR {sL2['avg']:+.4f} t {sL2['t']:+.2f}; "
      f"always-short avgR {sS2['avg']:+.4f} t {sS2['t']:+.2f}")

# ---------------- gradient: threshold ladder x hold, reversed ----------------
print("\n--- GRADIENT (reversed, net x1 / x2), threshold ladder x hold ---")
grad = {}
for hold in ("60m", "close"):
    for th in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
        g = trades(th, hold, evs); g = g[g.idx != "GOLD"].sort_values("t")
        a, a2 = st(rev_R(g, 1.0)), st(rev_R(g, 2.0))
        grad[f"th{th}_{hold}"] = dict(x1=a, x2=a2)
        print(f"th>={th:<4} {hold:>5}: n {a['n']:>4} x1 avgR {a['avg']:+.4f} t {a['t']:+.2f} halves {a['halves']} | x2 avgR {a2['avg']:+.4f} t {a2['t']:+.2f}")
# also the family's own 4-cell grid reversed at x1 is the th0.5/1.0 x 60m/close subset above.
# hold ladder at th0.5 (reversed): 30m / 60m / 120m / close
print("hold ladder at th0.5 (reversed x1):")
for mins in (15, 30, 60, 120, 180):
    # generic minute hold
    subs = []
    for idx, (b, atr, cutd) in frames.items():
        if idx == "GOLD": continue
        ix = b.index; rec = []
        for e in evs:
            if abs(e["dev"]) < 0.5: continue
            i0 = ix.searchsorted(e["t"] + pd.Timedelta(minutes=5))
            if i0 >= len(ix) or (ix[i0] - e["t"]) > pd.Timedelta(hours=2): continue
            skey = b.skey.iloc[i0]
            if skey >= cutd: continue
            a20 = atr.get(skey, np.nan)
            if not np.isfinite(a20) or a20 <= 0: continue
            i1 = ix.searchsorted(ix[i0] + pd.Timedelta(minutes=mins))
            if i1 >= len(ix): continue
            rec.append(dict(t=e["t"], idx=idx, dir_reg=e["dir"], move=float(b.close.iloc[i1] - b.close.iloc[i0]), atr=float(a20)))
        subs.append(pd.DataFrame(rec))
    g = pd.concat(subs).sort_values("t")
    a = st(rev_R(g, 1.0)); grad[f"th0.5_{mins}m"] = dict(x1=a)
    print(f"  hold {mins:>3}m: n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} halves {a['halves']}")

# ---------------- placebos ----------------
print("\n--- PLACEBOS (reversed x1) ---")
pb = trades(None, "60m", evs, band=(1e-9, 0.5)); pb = pb[pb.idx != "GOLD"].sort_values("t")
p1 = st(rev_R(pb, 1.0))
print(f"sub-threshold band 0<|dev|<0.5, same window: n {p1['n']} avgR {p1['avg']:+.4f} t {p1['t']:+.2f} halves {p1['halves']}")
plc = {}
for sd in (-1, -7, +7):
    ps = trades(0.5, "60m", evs, shift_days=sd); ps = ps[ps.idx != "GOLD"].sort_values("t")
    a = st(rev_R(ps, 1.0)); plc[f"shift{sd:+d}d"] = a
    print(f"shifted-day placebo (same clock, same direction, day {sd:+d}): n {a['n']} avgR {a['avg']:+.4f} t {a['t']:+.2f} halves {a['halves']}")

# ---------------- GOLD diagnostic (reversed), not selectable ----------------
gd = trades(0.5, "60m", evs); gd = gd[gd.idx == "GOLD"].sort_values("t")
gs = st(rev_R(gd, 1.0))
print(f"\nGOLD diagnostic reversed x1: n {gs['n']} avgR {gs['avg']:+.4f} t {gs['t']:+.2f} halves {gs['halves']}")

out = dict(cut={i: str(frames[i][2]) for i in frames},
           cell={k: v for k, v in cell.items() if k != "_df"},
           registered_reproduction=reg,
           control=dict(always_long=sL, always_short=sS, implied=maj,
                        welch=dict(diff=w_d, t=w_t), paired=dict(n=int(len(m)), diff=p_d, t=p_t),
                        secondary_all_sessions_0835_0935=dict(always_long=sL2, always_short=sS2)),
           gradient=grad, placebo=dict(subthreshold=p1, **plc), gold=gs)
json.dump(out, open(OUT, "w"), indent=1, default=float)
print("\nwrote", OUT)
