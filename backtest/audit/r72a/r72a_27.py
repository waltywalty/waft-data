"""Round 72A step 3, attempt 27 (auction-outcome direction, bid-to-cover surprise),
REVERSED, IS ONLY.
Copies run_r48b_btc.py's load_auctions / z_by_date / build_days / stats verbatim
(load_frame / rth_of via the run_r37_scalps.py prefix, as the runner does).
Same IS cut as the runner: per instrument keys[int(len(keys)*0.75)].
Never reads any *oos* file; every number below is on rows with oos == False.
Reversed rule: direction = -sign(z) (fade the bid-to-cover surprise), entry first 5m
bar open at/after 13:05 ET, exit RTH close (headline) or next session close.
Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, json, warnings, os, sys
from scipy import stats as sps
sys.path.insert(0, "/home/user/waft-data/backtest")
os.chdir("/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's dict, 1x round trip
OUT = "/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_27.json"


def load_auctions(path, prefixes):            # verbatim from run_r48b_btc.py
    out = []
    for r in json.load(open(path)):
        t = r.get("term") or ""
        if any(t.startswith(x) for x in prefixes) and r.get("auction_date") and r.get("btc"):
            try:
                out.append((pd.Timestamp(r["auction_date"]).date(), float(r["btc"])))
            except (TypeError, ValueError):
                pass
    return sorted(out)


BUCKETS = {"10Y": load_auctions("data/treasury_note_auctions.json", ("10-Year", "9-Year")),
           "30Y": load_auctions("data/treasury_bond_auctions.json", ("30-Year", "29-Year")),
           "2Y": load_auctions("data/treasury_note_auctions.json", ("2-Year",))}


def z_by_date(auctions):                      # verbatim
    out = {}
    vals = [b for _, b in auctions]
    for i, (dte, b) in enumerate(auctions):
        if i < 8:
            continue
        prior = np.array(vals[i - 8:i])
        sd = prior.std()
        if sd > 0:
            out[dte] = (b - prior.mean()) / sd
    return out


Z = {k: z_by_date(v) for k, v in BUCKETS.items()}
for k in Z:
    print(f"{k}: {len(BUCKETS[k])} auctions with btc, {len(Z[k])} with z-score")
DUR = dict(Z["10Y"]); DUR.update(Z["30Y"])   # later auction (30Y) wins on collisions, as runner
DUR_SRC = {k: "10Y" for k in Z["10Y"]}; DUR_SRC.update({k: "30Y" for k in Z["30Y"]})


def build_days(idx):                          # verbatim from run_r48b_btc.py
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m13 = np.where(hm >= 1305)[0]
        if not len(m13):
            continue
        rows.append(dict(skey=skey, p1305=g.open.values[m13[0]], c=g.close.values[-1],
                         hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["nextc"] = d.c.shift(-1)
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd


def build_days_am(idx):
    """placebo helper: 09:30 open and 13:00 price (pre-result window), same session keys."""
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m13 = np.where(hm >= 1300)[0]
        if not len(m13):
            continue
        rows.append(dict(skey=skey, o930=g.open.values[0], p1300=g.open.values[m13[0]]))
    return pd.DataFrame(rows).set_index("skey")


def st(r):
    """stats on an array of NET R (already cost-subtracted). Halves chronological."""
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 10:
        return dict(n=int(len(r)))
    m = len(r) // 2
    w, ls = r[r > 0], r[r <= 0]
    return dict(n=int(len(r)), wr=float((r > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else float("inf"),
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std() > 0 else float("nan"),
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def fmt(s, tag=""):
    if s.get("n", 0) < 10:
        return f"{tag} n {s.get('n', 0)} (too few)"
    return (f"{tag} n {s['n']:>5} WR {s['wr']*100:5.1f}% PF {s['pf']:5.2f} avgR {s['avg_R']:+.4f} "
            f"t {s['t']:+.2f} halves {s['halves']}")


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se)


# ---------------------------------------------------------------- data (IS only)
data, cut, am = {}, {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    cut[idx] = str(cutd)
    is_d = d[~d.oos].copy()          # OOS FIREWALL: drop every session at/after the cut
    assert (is_d.index < cutd).all()
    data[idx] = is_d
    am[idx] = build_days_am(idx).reindex(is_d.index)
    print(f"{idx}: {len(d)} sessions total, IS {len(is_d)} sessions before cut {cutd} (used); "
          f"{sum(1 for k in is_d.index if k in DUR)} duration-auction days with z in IS")
print("IS cut dates used (per instrument, = runner's keys[int(len*0.75)]):", cut)

# ---------------------------------------------------------------- trade builder
def trades(zmap, thr, hold, sign_mult=-1.0, insts=("SPX", "NDX", "RTY"), shift=0,
           entry_col="p1305", exit_col=None, zsign=None, band=None, src_filter=None):
    """Return DataFrame of IS trades. sign_mult=-1 => reversed (fade the surprise).
    shift=k: trade on the session k after the auction session (placebo).
    band=(lo,hi): keep lo < |z| <= hi (sub-threshold band).
    Costs are SUBTRACTED at multiples 1, 1.5, 2 (columns r1, r15, r2)."""
    xcol = exit_col or ("c" if hold == "close" else "nextc")
    rows = []
    for idx in insts:
        d = data[idx]
        keys = d.index.tolist(); pos = {k: i for i, k in enumerate(keys)}
        auc_days = [k for k in keys if k in zmap]
        for ak in auc_days:
            z = zmap[ak]
            if abs(z) <= thr:
                continue
            if band is not None and not (band[0] < abs(z) <= band[1]):
                continue
            if zsign is not None and np.sign(z) != zsign:
                continue
            if src_filter is not None and DUR_SRC.get(ak) != src_filter:
                continue
            j = pos[ak] + shift
            if j < 0 or j >= len(keys):
                continue
            k = keys[j]
            if shift != 0 and k in zmap:
                continue                      # placebo excludes sessions that are themselves auction days
            e = am[idx].o930[k] if entry_col == "o930" else d[entry_col][k]
            xp = am[idx].p1300[k] if xcol == "p1300" else d[xcol][k]
            a = d.atr20[k]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            dirn = sign_mult * np.sign(z)
            g = dirn * (xp - e)
            m = MICRO[idx]
            rows.append(dict(date=k, idx=idx, z=z, dir=dirn, g=g / a,
                             r1=(g - m) / a, r15=(g - 1.5 * m) / a, r2=(g - 2 * m) / a))
    df = pd.DataFrame(rows)
    return df.sort_values(["date", "idx"]).reset_index(drop=True) if len(df) else df


def control(direction, insts=("SPX", "NDX", "RTY"), hold="close", cost_mult=1.0):
    """Unconditional: EVERY eligible IS session, fixed direction, same window, 1x cost."""
    xcol = "c" if hold == "close" else "nextc"
    rows = []
    for idx in insts:
        d = data[idx]
        for k in d.index:
            e, xp, a = d.p1305[k], d[xcol][k], d.atr20[k]
            if not (np.isfinite(e) and np.isfinite(xp) and np.isfinite(a) and a > 0):
                continue
            rows.append(dict(date=k, idx=idx, r1=(direction * (xp - e) - cost_mult * MICRO[idx]) / a))
    return pd.DataFrame(rows).sort_values(["date", "idx"]).reset_index(drop=True)


def per_year(df):
    y = df.groupby(pd.to_datetime(df.date).dt.year).r1.agg(["mean", "count"])
    return {int(k): (int(np.sign(v["mean"])), int(v["count"]), float(v["mean"])) for k, v in y.iterrows()}


res = {"cut": cut, "cell": "REVERSED: dir = -sign(z), 10Y+30Y pooled, any |z|, 13:05->RTH close, SPX/NDX/RTY pooled, IS only"}

# ---------------------------------------------------------------- 1. reversed headline cell
print("\n=== REVERSED headline cell: fade the bid-to-cover surprise, any |z|, 13:05 -> close, indices pooled, IS ===")
rv = trades(DUR, 0.0, "close")
s1, s15, s2 = st(rv.r1), st(rv.r15), st(rv.r2)
print(fmt(s1, "net 1x  :")); print(fmt(s15, "net 1.5x:")); print(fmt(s2, "net 2x  :"))
sg = st(rv.g); print(fmt(sg, "gross   :"), "(info only)")
# runner's ordering (instrument-major) for halves comparison
rv_runner_order = pd.concat([rv[rv.idx == i] for i in ("SPX", "NDX", "RTY")])
print("halves in runner's instrument-major order:", st(rv_runner_order.r1)["halves"],
      " | chronological:", s1["halves"])
py = per_year(rv)
print("per-year sign (year: sign, n, avgR):", {k: (v[0], v[1], round(v[2], 4)) for k, v in py.items()})
print("direction mix of reversed trades: short (z>0) =", int((rv.dir < 0).sum()), " long (z<0) =", int((rv.dir > 0).sum()))
print("per instrument (net 1x):")
for i in ("SPX", "NDX", "RTY"):
    print("  ", fmt(st(rv[rv.idx == i].r1), i))
res["reversed"] = dict(x1=s1, x15=s15, x2=s2, gross=sg, per_year=py,
                       n_short=int((rv.dir < 0).sum()), n_long=int((rv.dir > 0).sum()),
                       halves_runner_order=st(rv_runner_order.r1)["halves"],
                       per_inst={i: st(rv[rv.idx == i].r1) for i in ("SPX", "NDX", "RTY")})

# check against the registered-direction numbers in results JSON (sanity: n and -avgR gross-cost symmetry)
fw = trades(DUR, 0.0, "close", sign_mult=+1.0)
print(f"sanity: registered direction recomputed net 1x: {fmt(st(fw.r1))}  (ledger: n 851 avgR -0.0395 t -2.52)")

# ---------------------------------------------------------------- 2. controls
print("\n=== UNCONDITIONAL CONTROLS: every eligible IS session, 13:05 -> close, indices pooled, net 1x ===")
cs = control(-1.0); cl = control(+1.0)
print(fmt(st(cs.r1), "always-SHORT:")); print(fmt(st(cl.r1), "always-LONG :"))
# direction-mixed control: the direction the reversal implies, trade by trade
ws = (rv.dir < 0).mean()
mix_mean = ws * cs.r1.mean() + (1 - ws) * cl.r1.mean()
print(f"direction-mixed control (w_short={ws:.3f}): avgR {mix_mean:+.4f}")
# primary: majority direction of the reversed cell
prim_dir = "short" if ws >= 0.5 else "long"
ctl = cs if prim_dir == "short" else cl
dA, tA = welch(rv.r1, ctl.r1)
print(f"PRIMARY diff reversed - always-{prim_dir} (Welch, two samples): dAvgR {dA:+.4f} t {tA:+.2f}")
# stratified: reversed-short trades vs always-short; reversed-long trades vs always-long
rs, rl = rv[rv.dir < 0], rv[rv.dir > 0]
dS, tS = welch(rs.r1, cs.r1); dL, tL = welch(rl.r1, cl.r1)
print(f"  stratified: reversed SHORT (z>0) n {len(rs)} avgR {rs.r1.mean():+.4f} vs always-short: d {dS:+.4f} t {tS:+.2f}")
print(f"              reversed LONG  (z<0) n {len(rl)} avgR {rl.r1.mean():+.4f} vs always-long : d {dL:+.4f} t {tL:+.2f}")
# direction-matched control per trade (each reversed trade vs mean of the control in its own direction):
# excess = r_trade - E[control in that direction]; t on the excess (one-sample, trade-level)
exc = np.where(rv.dir < 0, rv.r1 - cs.r1.mean(), rv.r1 - cl.r1.mean())
tE = exc.mean() / exc.std(ddof=1) * np.sqrt(len(exc))
print(f"  direction-matched excess over control (one-sample t on excess): d {exc.mean():+.4f} t {tE:+.2f}")
# auction-day unconditional short (candidate_reason's control), paired by date x instrument
ad = control(-1.0).merge(rv[["date", "idx", "r1"]], on=["date", "idx"], suffixes=("_ctl", "_rev"))
diffp = ad.r1_rev - ad.r1_ctl
tP = diffp.mean() / diffp.std(ddof=1) * np.sqrt(len(diffp))
print(f"SECONDARY auction-day unconditional SHORT 13:05->close (same days): n {len(ad)} avgR {ad.r1_ctl.mean():+.4f} "
      f"t {st(ad.r1_ctl)['t']:+.2f}; paired diff reversed - auction-day-short: d {diffp.mean():+.4f} t {tP:+.2f}")
ad_l = control(+1.0).merge(rv[["date", "idx", "r1"]], on=["date", "idx"], suffixes=("_ctl", "_rev"))
print(f"           auction-day unconditional LONG  13:05->close (same days): n {len(ad_l)} avgR {ad_l.r1_ctl.mean():+.4f} t {st(ad_l.r1_ctl)['t']:+.2f}")
res["control"] = dict(always_short=st(cs.r1), always_long=st(cl.r1), w_short=float(ws), mixed_avgR=float(mix_mean),
                      primary_dir=prim_dir, primary_diff=dict(d=dA, t=tA, method="Welch two-sample"),
                      strat_short=dict(d=dS, t=tS), strat_long=dict(d=dL, t=tL),
                      matched_excess=dict(d=float(exc.mean()), t=float(tE)),
                      auction_day_short=dict(n=int(len(ad)), avgR=float(ad.r1_ctl.mean()), t=st(ad.r1_ctl)["t"],
                                             paired_diff_d=float(diffp.mean()), paired_diff_t=float(tP)),
                      auction_day_long=dict(n=int(len(ad_l)), avgR=float(ad_l.r1_ctl.mean()), t=st(ad_l.r1_ctl)["t"]))

# ---------------------------------------------------------------- 3. gradient
print("\n=== GRADIENT (reversed, net 1x, IS): |z| threshold ladder x hold; registered grid = thr {0, 0.5} x hold {close, nextc} ===")
grad = {}
for hold in ("close", "nextc"):
    for thr in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
        s = st(trades(DUR, thr, hold).r1); grad[f"thr{thr}_{hold}"] = s
        tag = "*" if thr in (0.0, 0.5) else " "
        print(fmt(s, f" {tag}|z|>{thr:<4} {hold:>5}:"))
print(" sub-threshold bands (reversed, close):")
for lo, hi in ((0.0, 0.5), (0.5, 1.0), (1.0, 99.0)):
    s = st(trades(DUR, 0.0, "close", band=(lo, hi)).r1); grad[f"band{lo}-{hi}_close"] = s
    print(fmt(s, f"   {lo}<|z|<={hi}:"))
print(" by bucket (reversed, any |z|, close):")
for b in ("10Y", "30Y"):
    s = st(trades(DUR, 0.0, "close", src_filter=b).r1); grad[f"bucket{b}_close"] = s
    print(fmt(s, f"   {b} only:"))
print(" by sign (reversed, any |z|, close):")
for zs, lab in ((+1, "z>0 -> reversed SHORT"), (-1, "z<0 -> reversed LONG ")):
    s = st(trades(DUR, 0.0, "close", zsign=zs).r1); grad[f"sign{zs}_close"] = s
    print(fmt(s, f"   {lab}:"))
print(" 2Y diagnostic reversed:")
for hold in ("close", "nextc"):
    for thr in (0.0, 0.5):
        s = st(trades(Z["2Y"], thr, hold).r1); grad[f"2Y_thr{thr}_{hold}"] = s
        print(fmt(s, f"   2Y |z|>{thr} {hold}:"))
print(" GOLD diagnostic reversed (GOLD IS cut", cut["GOLD"], "):")
for hold in ("close", "nextc"):
    for thr in (0.0, 0.5):
        s = st(trades(DUR, thr, hold, insts=("GOLD",)).r1); grad[f"GOLD_thr{thr}_{hold}"] = s
        print(fmt(s, f"   GOLD |z|>{thr} {hold}:"))
res["gradient"] = grad

# ---------------------------------------------------------------- 4. placebo
print("\n=== PLACEBO (reversed, net 1x, IS) ===")
plc = {}
print(" (a) day-shift: same -sign(z) direction traded 13:05->close on the session k after the auction day")
for k in (-3, -2, -1, 0, 1, 2, 3):
    s = st(trades(DUR, 0.0, "close", shift=k).r1); plc[f"shift{k}"] = s
    print(fmt(s, f"   shift {k:+d}:"), "<- the cell" if k == 0 else "")
print(" (b) clock-shift: same -sign(z) direction on the SAME day but 09:30 -> 13:00 (before the result exists; signal not yet known)")
s = st(trades(DUR, 0.0, "close", entry_col="o930", exit_col="p1300").r1); plc["am_pre_result"] = s
print(fmt(s, "   09:30->13:00 pre-result:"))
print(" (c) sign placebo: random-sign direction is by construction ~ -cost; the z-sign split above is the informative one")
res["placebo"] = plc

json.dump(res, open(OUT, "w"), indent=1, default=float)
print("\nwrote", OUT)
