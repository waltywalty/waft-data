"""Round 11-B/C: the 30-minute-range + 10-minute-confirm + EMA-pullback
continuation entry, and the micro-futures point-target panel.

The user's spec: mark the first 30-minute candle after the NY open; wait for a
10-MINUTE candle to close outside that range; drop to the 2-minute chart with a
20 EMA; when price pulls back and interacts with the EMA and then continues in
the breakout direction, enter for continuation. Exits: prior-day high/low,
prior-hour high/low, and friends.

Data honesty: bars here are 5-minute, so the 2-minute/20-EMA (a 40-minute
smoothing span) is implemented as its exact time-equivalent - an 8-period EMA
on 5-minute closes - and a 20-period 5m EMA is run alongside as the slow
variant. The 2-minute microstructure itself is bracketed, not simulated.

Mechanics (long side; shorts mirrored):
  range = 09:30-10:00 ET high/low
  confirm = first 10m block (anchored 10:00) closing above the range high,
            scanned to 12:00 ET
  pullback = a later 5m bar whose LOW touches the EMA (value known at the
             prior bar's close - no intrabar peeking)
  entry   = first 5m close after the touch that is above both the range high
            and the EMA -> enter at that close, by 13:00 ET at the latest
  stop    = pullback low (the lowest low from confirm to entry)
  exits   = prior-day H/L target, prior-hour H/L target, 2R, or EoD hold

Part C prices the same entries (plus the plain 30m ORB entry and the Asia gold
entry) as micro futures: profit target 15 or 20 POINTS, stop = target / RR for
RR in {1, 2, 3}, flat at EoD if neither side is hit. Point values: MGC $10,
MES $5, MNQ $2, M2K $5. A fixed point target is a very different fraction of
each market's price (15 NDX points is ~0.1%; 15 XAU points ~0.6%) - reported,
not hidden.
"""
import pandas as pd, numpy as np, warnings, json
import mkts
warnings.filterwarnings("ignore")

OUT = {"cells": []}


def ema_series(M, span_bars):
    return pd.Series(M.c, index=M.ix).ewm(span=span_bars, adjust=False).mean().values


def ema_pullback_entries(M, ema, feat):
    """One candidate entry per day. Returns list of dicts with entry context."""
    out = []
    for d in M.days:
        day = pd.Timestamp(d)
        t0, t1 = M.nyt(day, 9, 30), M.nyt(day, 10, 0)
        j0, j1 = M.rng(t0, t1)
        if j1 - j0 < 6:
            continue
        rh, rl = float(M.h[j0:j1].max()), float(M.l[j0:j1].min())
        if rh <= rl:
            continue
        # 10-minute confirmation blocks anchored on 10:00, scanned to 12:00
        k0, k1 = M.rng(t1, M.nyt(day, 12, 0))
        side, kc = 0, None
        for k in range(k0, k1 - 1, 2):                  # 2 x 5m = one 10m block
            blk_c = M.c[min(k + 1, k1 - 1)]
            if blk_c > rh:
                side, kc = 1, k + 1
                break
            if blk_c < rl:
                side, kc = -1, k + 1
                break
        if not side:
            continue
        # pullback to the EMA, then continuation close, entry by 13:00
        e0, e1 = kc + 1, M.ix.searchsorted(M.nyt(day, 13, 0))
        touched, ke = False, None
        for k in range(e0, min(e1, len(M.c))):
            ema_prev = ema[k - 1]                        # known at bar open
            if not touched:
                if (side == 1 and M.l[k] <= ema_prev) or (side == -1 and M.h[k] >= ema_prev):
                    touched = True
            else:
                if (side == 1 and M.c[k] > max(rh, ema_prev)) or \
                   (side == -1 and M.c[k] < min(rl, ema_prev)):
                    ke = k
                    break
        if ke is None:
            continue
        entry = float(M.c[ke])
        ext = float(M.l[kc:ke + 1].min()) if side == 1 else float(M.h[kc:ke + 1].max())
        if side * (entry - ext) <= 0.0003 * entry:
            continue
        f = feat.reindex([day])
        out.append(dict(day=day, side=side, entry=entry, ke=ke,
                        stop0=ext, rh=rh, rl=rl,
                        p_h=float(f.p_h.iloc[0]), p_l=float(f.p_l.iloc[0])))
    return out


def close_out(M, day, side, entry, ke, stop, target, t_exit):
    t_fill = M.ix[ke] + pd.Timedelta(minutes=5)
    px, why, _ = mkts.hit(M, M.ix.searchsorted(t_fill), M.ix.searchsorted(t_exit),
                          side, stop, target)
    if px is None:
        px = M.at(t_exit)
        if px is None:
            return None
        why = "time"
    return dict(day=day, side=side, entry=entry, why=why,
                pnl=side * (px - entry) - M.cost)


def prior_hour_level(M, day, ke, side):
    t_ref = M.ix[ke]
    h0 = t_ref.floor("h") - pd.Timedelta(hours=1)
    j0, j1 = M.rng(h0, t_ref.floor("h"))
    if j1 <= j0:
        return np.nan
    return float(M.h[j0:j1].max()) if side == 1 else float(M.l[j0:j1].min())


MKTS = mkts.load_mkts()
print("=== B. EMA-PULLBACK CONTINUATION (30m range, 10m confirm) ===")
entries_by_mkt = {}
for M in MKTS:
    feat = mkts.rth_features(M)
    for span, sl in ((8, "8-EMA (2m-20 equivalent)"), (20, "20-EMA on 5m")):
        ema = ema_series(M, span)
        ents = ema_pullback_entries(M, ema, feat)
        if span == 8:
            entries_by_mkt[M.name] = ents               # for the points panel
        t_eod = lambda day: M.nyt(day, 16)
        for ex in ("prev_day", "prev_hour", "2R", "eod"):
            rows = []
            for e in ents:
                stop, tgt = e["stop0"], None
                R = e["side"] * (e["entry"] - stop)
                if ex == "prev_day":
                    tgt = e["p_h"] if e["side"] == 1 else e["p_l"]
                    if not np.isfinite(tgt) or e["side"] * (tgt - e["entry"]) < 0.25 * R:
                        continue
                elif ex == "prev_hour":
                    tgt = prior_hour_level(M, e["day"], e["ke"], e["side"])
                    if not np.isfinite(tgt) or e["side"] * (tgt - e["entry"]) < 0.25 * R:
                        continue
                elif ex == "2R":
                    tgt = e["entry"] + e["side"] * 2 * R
                tr = close_out(M, e["day"], e["side"], e["entry"], e["ke"], stop, tgt,
                               t_eod(e["day"]))
                if tr:
                    rows.append(tr)
            mkts.show(M, f"{sl} / exit {ex}", rows, OUT["cells"], "ema_pull")

print("\n=== C. MICRO-FUTURES POINT TARGETS (target 15/20 pts, stop = target/RR) ===")
print("    contracts: XAU~MGC $10/pt, SPX~MES $5/pt, NDX~MNQ $2/pt, RTY~M2K $5/pt")


def points_panel(M, name, entries):
    for tp in (15.0, 20.0):
        for rr in (1.0, 2.0, 3.0):
            rows = []
            for e in entries:
                stop = e["entry"] - e["side"] * tp / rr
                tgt = e["entry"] + e["side"] * tp
                tr = close_out(M, e["day"], e["side"], e["entry"], e["ke"], stop, tgt,
                               M.nyt(pd.Timestamp(e["day"]), 16))
                if tr:
                    rows.append(tr)
            pct = tp / np.median([e["entry"] for e in entries]) * 100 if entries else 0
            mkts.show(M, f"{name}: +{tp:.0f}pt ({pct:.2f}%), RR 1:{rr:.0f}",
                      rows, OUT["cells"], "points")


def orb_entries(M):
    out = []
    for d in M.days:
        day = pd.Timestamp(d)
        t0, t1 = M.nyt(day, 9, 30), M.nyt(day, 10, 0)
        j0, j1 = M.rng(t0, t1)
        if j1 - j0 < 6:
            continue
        rh, rl = float(M.h[j0:j1].max()), float(M.l[j0:j1].min())
        if rh <= rl:
            continue
        k0, k1 = M.rng(t1, M.nyt(day, 12, 0))
        brk = (M.c[k0:k1] > rh) | (M.c[k0:k1] < rl)
        if not brk.any():
            continue
        k = k0 + int(np.argmax(brk))
        out.append(dict(day=day, side=1 if M.c[k] > rh else -1,
                        entry=float(M.c[k]), ke=k))
    return out


for M in MKTS:
    points_panel(M, "30m ORB break", orb_entries(M))
    if entries_by_mkt.get(M.name):
        points_panel(M, "EMA pullback", entries_by_mkt[M.name])

# the Asia gold entry as MGC with point targets
import engine as gold_engine, trades
gold = MKTS[0]
N = trades.generate(gold_engine.load_bars(), 60, stop_r=None, cost=0.30, entry_cutoff_ldn=8)
N["day"] = pd.to_datetime(N.day)
DEP = pd.read_pickle("results/trades_deployable.pkl")
N = N[N.day.isin(pd.to_datetime(DEP.day))]
asia_entries = [dict(day=r.day, side=int(r.side), entry=float(r.entry),
                     ke=gold.ix.searchsorted(r.t_fill)) for _, r in N.iterrows()]
for tp in (15.0, 20.0):
    for rr in (1.0, 2.0, 3.0):
        rows = []
        for e in asia_entries:
            stop = e["entry"] - e["side"] * tp / rr
            tgt = e["entry"] + e["side"] * tp
            day = pd.Timestamp(e["day"])
            t_exit = pd.Timestamp(day.year, day.month, day.day, 16, tz=mkts.NY).tz_convert("UTC")
            tr = close_out(gold, e["day"], e["side"], e["entry"], e["ke"], stop, tgt, t_exit)
            if tr:
                rows.append(tr)
        mkts.show(gold, f"Asia gold entry as MGC: +{tp:.0f}pt, RR 1:{rr:.0f}",
                  rows, OUT["cells"], "points_asia")

json.dump(OUT, open("results/ema_points.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} cells. written: results/ema_points.json")
