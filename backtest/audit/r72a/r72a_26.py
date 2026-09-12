"""Round 72A step 3, attempt 26 (Treasury duration-auction day), REVERSED, IS ONLY.
Reuses run_r48_auction.py's build_days / stats / auction_days logic verbatim
(via run_r37_scalps.py prefix for load_frame / rth_of). Same IS cut as the runner
(keys[int(len(keys)*0.75)], per instrument). Never reads any *oos* file; every
computation below is on rows with oos == False.
Run from /home/user/waft-data/backtest/."""
import pandas as pd, numpy as np, json, warnings, os, sys
sys.path.insert(0, "/home/user/waft-data/backtest")
os.chdir("/home/user/waft-data/backtest")
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}   # runner's dict, 1x round trip


def auction_days(paths_terms):
    days = set()
    for path, terms in paths_terms:
        for r in json.load(open(path)):
            t = r.get("term") or ""
            if any(t.startswith(x) for x in terms) and r.get("auction_date"):
                days.add(pd.Timestamp(r["auction_date"]).date())
    return days


NOTE, BOND = "data/treasury_note_auctions.json", "data/treasury_bond_auctions.json"
D10 = auction_days([(NOTE, ("10-Year", "9-Year"))])
D30 = auction_days([(BOND, ("30-Year", "29-Year"))])
D2 = auction_days([(NOTE, ("2-Year",))])
# extra terms for the duration ladder (gradient) - not selectable in the family
D3 = auction_days([(NOTE, ("3-Year",))])
D5 = auction_days([(NOTE, ("5-Year", "4-Year"))])
D7 = auction_days([(NOTE, ("7-Year", "6-Year"))])
D20 = auction_days([(BOND, ("20-Year", "19-Year"))])
print(f"auction days: 2Y {len(D2)} 3Y {len(D3)} 5Y {len(D5)} 7Y {len(D7)} 10Y {len(D10)} 20Y {len(D20)} 30Y {len(D30)} (all-history)")


def build_days(idx):          # verbatim from run_r48_auction.py
    rth = rth_of(load_frame(idx))
    rows = []
    for skey, g in rth.groupby("skey"):
        hm = g.hm.values
        m13 = np.where(hm >= 1300)[0]
        if not len(m13):
            continue
        rows.append(dict(skey=skey, o=g.open.values[0], p13=g.open.values[m13[0]],
                         c=g.close.values[-1], hi=g.high.max(), lo=g.low.min()))
    d = pd.DataFrame(rows).set_index("skey")
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["nextc"] = d.c.shift(-1)
    keys = d.index.tolist()
    cutd = keys[int(len(keys) * 0.75)]
    d["oos"] = np.array([k >= cutd for k in keys])
    return d, cutd


def stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


data, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    d, cutd = build_days(idx)
    nall = len(d)
    d = d[~d.oos].copy()                      # OOS FIREWALL: IS rows only from here on
    data[idx] = d
    split[idx] = str(cutd)
    print(f"{idx}: {nall} sessions total, {len(d)} IS sessions, IS CUT = {cutd} (sessions >= cut EXCLUDED)")

WINS = {"W1": ("o", "p13"), "W2": ("p13", "c"), "W3": ("p13", "nextc")}
REG_SIDE = {"W1": -1, "W2": +1, "W3": +1}            # registered direction
REV_SIDE = {w: -s for w, s in REG_SIDE.items()}      # reversed


def cell(win, dayset, side, insts=("SPX", "NDX", "RTY"), shift=0, cost_mult=1.0, exclude=None):
    """Trades on IS sessions whose key (shifted by `shift` sessions) is in dayset.
    dayset=None -> every eligible session (unconditional control). Gross pnl in
    price points, cost subtracted at cost_mult x MICRO. Returns DataFrame."""
    ecol, xcol = WINS[win]
    out = []
    for idx in insts:
        d = data[idx]
        keys = d.index.tolist()
        elig = np.isfinite(d[ecol]) & np.isfinite(d[xcol]) & np.isfinite(d.atr20) & (d.atr20 > 0)
        if dayset is None:
            m = elig.values
        else:
            if shift == 0:
                inday = np.array([k in dayset for k in keys])
            else:
                # trade the session `shift` sessions AFTER an auction day (negative = before)
                pos = np.array([k in dayset for k in keys])
                inday = np.zeros(len(keys), bool)
                src_i = np.where(pos)[0] + shift
                src_i = src_i[(src_i >= 0) & (src_i < len(keys))]
                inday[src_i] = True
            m = elig.values & inday
        if exclude is not None:
            m = m & ~np.array([k in exclude for k in keys])
        s = d[m]
        gross = side * (s[xcol] - s[ecol])
        out.append(pd.DataFrame(dict(gross=gross.values, atr=s.atr20.values, idx=idx,
                                     skey=s.index, pnl=(gross - cost_mult * MICRO[idx]).values)))
    return pd.concat(out, ignore_index=True)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float((a.mean() - b.mean()) / np.sqrt(va + vb))


def fmt(s):
    if s.get("n", 0) < 10: return f"n {s.get('n')} (too few)"
    return (f"n {s['n']:>4} WR {s['wr']*100:5.1f}% PF {s['pf']:5.2f} avgR {s['avg_R']:+.4f} "
            f"t {s['t']:+.2f} halves {s['halves']}")


# ---------------- headline reversed cell: W1 10Y LONG 09:30->13:00 ----------------
print("\n=== HEADLINE REVERSED CELL: W1 LONG 09:30->13:00 on 10Y auction days, SPX/NDX/RTY pooled, IS ===")
hd = {}
for cm in (1.0, 1.5, 2.0):
    c = cell("W1", D10, REV_SIDE["W1"], cost_mult=cm)
    hd[cm] = stats(c.pnl, c.atr)
    print(f"cost x{cm}: {fmt(hd[cm])}")
c1 = cell("W1", D10, REV_SIDE["W1"], cost_mult=1.0)
g = stats(c1.gross, c1.atr)
print(f"gross   : {fmt(g)}")
c1["R"] = c1.pnl / c1.atr
c1["year"] = pd.to_datetime(c1.skey).dt.year
py = c1.groupby("year").R.agg(["mean", "count"])
print("per-year (net 1x): " + " ".join(f"{y}:{'+' if m > 0 else '-'}({n})" for y, (m, n) in py.iterrows()))
print("per-instrument (net 1x):")
for idx in ("SPX", "NDX", "RTY"):
    s = c1[c1.idx == idx]; print(f"  {idx}: {fmt(stats(s.pnl, s.atr))}")
gd = cell("W1", D10, REV_SIDE["W1"], insts=("GOLD",))
print(f"GOLD diagnostic reversed W1 10Y long: {fmt(stats(gd.pnl, gd.atr))}")

# ---------------- unconditional control: always-long 09:30->13:00, every eligible IS session ----------------
print("\n=== CONTROL: always-LONG 09:30->13:00 on EVERY eligible IS session, pooled, 1x cost ===")
ctl = cell("W1", None, REV_SIDE["W1"])
cs = stats(ctl.pnl, ctl.atr)
print(f"control all sessions: {fmt(cs)}")
ctl_ex = cell("W1", None, REV_SIDE["W1"], exclude=D10)
cse = stats(ctl_ex.pnl, ctl_ex.atr)
print(f"control excl 10Y days: {fmt(cse)}")
rR, cR, ceR = c1.pnl / c1.atr, ctl.pnl / ctl.atr, ctl_ex.pnl / ctl_ex.atr
dA, tA = float(rR.mean() - cR.mean()), welch(rR, cR)
dB, tB = float(rR.mean() - ceR.mean()), welch(rR, ceR)
print(f"reversed - control(all):      dAvgR {dA:+.4f}  Welch t {tA:+.2f}   (cell is a subset of control days; Welch, not paired)")
print(f"reversed - control(non-10Y):  dAvgR {dB:+.4f}  Welch t {tB:+.2f}   (disjoint samples; Welch)")

# ---------------- full reversed grid (family's own grid, reversed) ----------------
print("\n=== REVERSED GRID (all cells = -1 x registered), pooled indices, net 1x, IS ===")
TERMS = {"10Y": D10, "30Y": D30, "2Y_diag": D2}
for w in WINS:
    for tn, ds in TERMS.items():
        c = cell(w, ds, REV_SIDE[w])
        c2 = cell(w, ds, REV_SIDE[w], cost_mult=2.0)
        s, s2 = stats(c.pnl, c.atr), stats(c2.pnl, c2.atr)
        print(f"{w} {'long' if REV_SIDE[w] > 0 else 'short':5} {tn:7}: {fmt(s)} | x2 avgR {s2.get('avg_R', float('nan')):+.4f} t {s2.get('t', float('nan')):+.2f}")

# secondary reversed cell W2 10Y SHORT vs always-short PM control (the beta test for the PM fade)
print("\n--- secondary: W2 SHORT 13:00->close on 10Y days vs always-short PM control ---")
w2 = cell("W2", D10, REV_SIDE["W2"]); w2c = cell("W2", None, REV_SIDE["W2"])
w2s, w2cs = stats(w2.pnl, w2.atr), stats(w2c.pnl, w2c.atr)
print(f"W2 10Y short: {fmt(w2s)}\nctl always-short PM: {fmt(w2cs)}")
print(f"diff dAvgR {w2s['avg_R']-w2cs['avg_R']:+.4f} Welch t {welch(w2.pnl/w2.atr, w2c.pnl/w2c.atr):+.2f}")

# ---------------- gradient: duration ladder, reversed W1 long, IS ----------------
print("\n=== GRADIENT: reversed W1 LONG 09:30->13:00 by auction term (duration ladder), pooled, net 1x, IS ===")
LADDER = [("2Y", D2), ("3Y", D3), ("5Y", D5), ("7Y", D7), ("10Y", D10), ("20Y", D20), ("30Y", D30)]
grad = {}
for tn, ds in LADDER:
    c = cell("W1", ds, REV_SIDE["W1"]); s = stats(c.pnl, c.atr); grad[tn] = s
    print(f"  {tn:4}: {fmt(s)}")
# 10Y+30Y pooled (unique days) and any-coupon-auction day
c = cell("W1", D10 | D30, REV_SIDE["W1"]); print(f"  10Y|30Y pooled: {fmt(stats(c.pnl, c.atr))}")
ALL = D2 | D3 | D5 | D7 | D10 | D20 | D30
c = cell("W1", ALL, REV_SIDE["W1"]); print(f"  any coupon auction day: {fmt(stats(c.pnl, c.atr))}")
c = cell("W1", None, REV_SIDE["W1"], exclude=ALL); print(f"  NO coupon auction day (control complement): {fmt(stats(c.pnl, c.atr))}")

# ---------------- placebo: shifted day (sessions before/after a 10Y auction day), reversed ----------------
print("\n=== PLACEBO: reversed W1 LONG 09:30->13:00 on sessions shifted k from a 10Y auction day, pooled, net 1x, IS ===")
plc = {}
for k in (-3, -2, -1, 0, +1, +2, +3):
    c = cell("W1", D10, REV_SIDE["W1"], shift=k, exclude=(D10 if k != 0 else None))
    s = stats(c.pnl, c.atr); plc[k] = s
    print(f"  shift {k:+d}: {fmt(s)}" + ("   <- the cell" if k == 0 else "   (excluding sessions that are themselves 10Y days)"))
# 10Y days that are ALSO 30Y days vs not (reopening weeks stack 10Y Wed / 30Y Thu; check same-day overlap)
ov = D10 & D30
print(f"  10Y&30Y same-day overlap: {len(ov)} days all-history")

out = dict(split=split, headline=dict(cell="W1 LONG 09:30->13:00, 10Y auction days, SPX/NDX/RTY pooled, IS",
                                       x1=hd[1.0], x15=hd[1.5], x2=hd[2.0], gross=g,
                                       per_year={int(y): dict(mean=float(m), n=int(n)) for y, (m, n) in py.iterrows()}),
           control_all=cs, control_non10Y=cse,
           diff_vs_control_all=dict(dAvgR=dA, t=tA), diff_vs_control_non10Y=dict(dAvgR=dB, t=tB),
           gradient_duration_ladder=grad, placebo_shift=plc,
           w2_secondary=dict(cell=w2s, control=w2cs))
json.dump(out, open("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_26.json", "w"),
          indent=1, default=float)
print("\nwrote r72a_26.json")
