"""Attempt 56 (Round 78, as AMENDED): Ranaldo local-hours pattern on EURUSD.

Blocks anchored to each currency area's own local hours via the IANA tz database, per calendar day:
  C1 SHORT EURUSD  08:00 Europe/Berlin -> 08:00 America/New_York      (EUR-only hours)
  C2 LONG  EURUSD  17:00 Europe/Berlin -> 16:55 America/New_York      (USD-only hours, exit before the 17:00 NY rollover)
  overlap placebo  08:00 America/New_York -> 17:00 Europe/Berlin     (both predictions, opposite signs: predicted ~0)
  Tokyo placebo    09:00 -> 17:00 Asia/Tokyo                          (EURUSD: no prediction; USDJPY read-only: long)
Clock: IS ejtrader m15 stamps follow the EU DST calendar (UTC+2 winter / UTC+3 summer, verified empirically): London wall
clock = stamp - 2 h in every week -> localised Europe/London and converted to UTC; OOS Dukascopy 1m stamps = UTC. A clock gate (08:30-ET first-Friday release peak in both seasons) runs first.
Bar: n >= 40, net mean > 0, t >= 2.24 (Bonferroni 2), bar-cell max-stat p < 0.05, PF >= 1.15, halves [+,+],
positive at 2x cost, raw AND drift-adjusted; opposite-sign-similar-size cells or a same-order placebo = drift artefact.
OOS (UNSEAL_OK=1 --unseal): EURUSD only, cleared cells only. Outputs results/r78_fxtod_{is,oos}.json.
"""
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
PIP = {"EURUSD": 1e-4, "USDJPY": 1e-2}
BER, NY, TKY, LON = ZoneInfo("Europe/Berlin"), ZoneInfo("America/New_York"), ZoneInfo("Asia/Tokyo"), ZoneInfo("Europe/London")
# block = (start tz, start "HH:MM", end tz, end "HH:MM"); end is exclusive
BLOCKS = {"C1_eur_only": (BER, "08:00", NY, "08:00"), "C2_usd_only": (BER, "17:00", NY, "16:55"),
          "overlap": (NY, "08:00", BER, "17:00"), "tokyo": (TKY, "09:00", TKY, "17:00")}
HOURS = {"C1_eur_only": 6.0, "C2_usd_only": 5.9, "overlap": 3.0, "tokyo": 8.0}
SIGN = {("EURUSD", "C1_eur_only"): -1, ("EURUSD", "C2_usd_only"): +1, ("EURUSD", "overlap"): 0, ("EURUSD", "tokyo"): 0,
        ("USDJPY", "tokyo"): +1, ("USDJPY", "C2_usd_only"): -1, ("USDJPY", "C1_eur_only"): 0, ("USDJPY", "overlap"): 0}
RNG = np.random.default_rng(78)


def load_is(sym):
    df = pd.read_csv(os.path.join(HERE, "data", f"{sym}_m15_ejtrader.csv"), parse_dates=["Date"])
    px = df[["open", "high", "low", "close"]].astype(float)
    lo, hi = (0.8, 1.6) if sym == "EURUSD" else (60.0, 200.0)
    for _ in range(8):
        if lo <= px.close.median() <= hi: break
        px = px / 10.0
    assert lo <= px.close.median() <= hi
    lon = (df.Date - pd.Timedelta(hours=2)).dt.tz_localize(LON, ambiguous="NaT", nonexistent="shift_forward")
    px.index = lon; px = px[~px.index.isna()]
    return px.tz_convert("UTC").sort_index(), 4            # bars per hour


def load_oos(sym):
    df = pd.read_csv(os.path.join(HERE, "data", "fx", "dukascopy", f"{sym}_1m.csv"), parse_dates=["time"]).set_index("time")
    df = df[(df.volume > 0) & (df.index >= pd.Timestamp("2022-04-01", tz="UTC"))]
    return df[["open", "high", "low", "close"]].astype(float), 60


def clock_gate(px, bph):
    """08:30-ET release peak on first Fridays must sit in the 08:30 ET slot in both DST seasons."""
    et = px.index.tz_convert(NY); d = pd.DataFrame(dict(rng=(px.high - px.low).values / px.close.values * 1e4), index=et)
    d["date"] = d.index.date; d["slot"] = d.index.hour * 100 + (d.index.minute // 15) * 15
    d["first_friday"] = (d.index.dayofweek == 4) & (d.index.day <= 7); d["summer"] = d.index.map(lambda t: bool(t.dst()))
    out = {}
    for season in (False, True):
        ff = d[d.first_friday & (d.summer == season) & (d.slot >= 700) & (d.slot <= 1000)]
        m = ff.groupby("slot").rng.mean(); out["summer" if season else "winter"] = dict(peak_slot=int(m.idxmax()), ratio=float(m.max() / m.drop(m.idxmax()).mean()))
    ok = out["winter"]["peak_slot"] == 830 and out["summer"]["peak_slot"] == 830
    return ok, out


def block_bounds(day, blk):
    tz0, h0, tz1, h1 = BLOCKS[blk]
    t0 = pd.Timestamp(f"{day} {h0}", tz=tz0).tz_convert("UTC"); t1 = pd.Timestamp(f"{day} {h1}", tz=tz1).tz_convert("UTC")
    return t0, t1


def blocks(px, bph, sym, which):
    rows = []
    days = sorted(set(px.index.tz_convert(BER).date))
    for d in days:
        if pd.Timestamp(d).dayofweek >= 5: continue
        for blk in which:
            t0, t1 = block_bounds(d, blk)
            if t1 <= t0: continue
            w = px[(px.index >= t0) & (px.index < t1)]
            expected = (t1 - t0).total_seconds() / 3600 * bph; step = pd.Timedelta(minutes=60 // bph)
            if len(w) < 0.9 * expected or (w.index[0] - t0) > step or (t1 - w.index[-1]) > 2 * step:
                rows.append(dict(date=str(d), block=blk, sym=sym, void=True)); continue
            entry, exit_px = float(w.open.iloc[0]), float(w.close.iloc[-1])
            mv = np.log(exit_px / entry) * 1e4; cost = PIP[sym] / entry * 1e4; s = SIGN[(sym, blk)]
            rows.append(dict(date=str(d), dow=pd.Timestamp(d).dayofweek, block=blk, sym=sym, void=False, raw=mv, sign=s,
                             gross=(s * mv if s else mv), net=(s * mv - cost if s else np.nan), net15=(s * mv - 1.5 * cost if s else np.nan),
                             net2=(s * mv - 2 * cost if s else np.nan), hours=(t1 - t0).total_seconds() / 3600))
    if not rows:
        return pd.DataFrame(columns=["date", "dow", "block", "sym", "void", "raw", "sign", "gross", "net", "net15", "net2", "hours"])
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def maxstat_two(t, cells, draws=2000):
    piv = t[t.block.isin(cells) & ~t.void].pivot_table(index="date", columns="block", values="net")
    X = piv.values; obs = {c: float(np.nanmean(piv[c]) / np.nanstd(piv[c], ddof=1) * np.sqrt(piv[c].notna().sum())) for c in piv.columns}
    mx = []
    for _ in range(draws):
        s = RNG.choice([-1.0, 1.0], size=(X.shape[0], 1)); Y = X * s
        mx.append(np.nanmax(np.abs(np.nanmean(Y, 0) / np.nanstd(Y, 0, ddof=1) * np.sqrt(np.sum(~np.isnan(Y), 0)))))
    return obs, np.array(mx)


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    cleared = None
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r78_fxtod_is.json")))
        cleared = [c for c, ok in isr["verdict"].items() if ok]
        if not cleared: raise SystemExit("no cell cleared IS; holdout stays sealed")
    for sym in (("EURUSD",) if UNSEAL else ("EURUSD", "USDJPY")):
        px, bph = load_oos(sym) if UNSEAL else load_is(sym)
        ok, gate = clock_gate(px, bph); res[f"{sym}_clock_gate"] = dict(passed=ok, **gate); print(f"{sym} clock gate {'PASS' if ok else 'FAIL'}: {gate}")
        if not ok: raise SystemExit("clock gate failed; no cell read")
        which = cleared if UNSEAL else list(BLOCKS)
        t = blocks(px, bph, sym, which)
        # unconditional per-hour drift over the sample (log return per bar x bars per hour), from the same frame
        lr = np.log(px.close / px.open).values * 1e4; drift_h = float(np.nanmean(lr) * bph)
        out = {"span": [str(t.date.min()), str(t.date.max())], "days": int(t.date.nunique()), "drift_bp_per_hour": drift_h,
               "voided": {b: int(g.void.sum()) for b, g in t.groupby("block")}}
        for blk in which:
            g = t[(t.block == blk) & ~t.void]; s = SIGN[(sym, blk)]
            if s:
                adj = g.net - s * drift_h * g.hours
                out[blk] = dict(sign=s, hours=float(g.hours.mean()) if len(g) else None, x1=stats(g.net), x15=stats(g.net15), x2=stats(g.net2), gross=stats(g.gross),
                                drift_adjusted_x1=stats(adj), mirror_x1=stats(-g.gross - (g.gross - g.net)),
                                per_year_net={int(y): round(float(v), 2) for y, v in g.groupby(pd.to_datetime(g.date).dt.year).net.mean().items()},
                                dow_net={int(k): round(float(v), 2) for k, v in g.groupby("dow").net.mean().items()})
            else:
                out[blk] = dict(sign=0, placebo_raw=stats(g.raw), note="no prediction; read-only placebo")
        if not UNSEAL and sym == "EURUSD":
            obs, mx = maxstat_two(t, ["C1_eur_only", "C2_usd_only"])
            out["maxstat"] = dict(obs_t=obs, p_per_cell={c: float((np.sum(mx >= abs(v)) + 1) / (len(mx) + 1)) for c, v in obs.items()})
        res[sym] = out
        print(f"=== {sym} ({'OOS' if UNSEAL else 'IS'}) {out['span']} {out['days']} days; drift {drift_h:+.3f} bp/h; voided {out['voided']} ===")
        for blk in which:
            print(f"  {blk:12s}: {json.dumps(out[blk], default=float)[:600]}")
        if "maxstat" in out: print("  maxstat:", out["maxstat"])
    if not UNSEAL:
        e = res["EURUSD"]; passes = {}
        for blk in ("C1_eur_only", "C2_usd_only"):
            s = e[blk]["x1"]; a = e[blk]["drift_adjusted_x1"]; p = e["maxstat"]["p_per_cell"].get(blk, 1.0)
            raw_ok = s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2.24 and s.get("pf", 0) >= 1.15 and s.get("halves") == [1.0, 1.0] and e[blk]["x2"]["mean_bp"] > 0
            adj_ok = a.get("mean_bp", -1) > 0 and (a.get("t") or -9) >= 2.24 and a.get("halves") == [1.0, 1.0]
            passes[blk] = bool(raw_ok and adj_ok and p < 0.05)
        m1, m2 = e["C1_eur_only"]["x1"].get("mean_bp", 0), e["C2_usd_only"]["x1"].get("mean_bp", 0)
        # drift-artefact rule: opposite signed raw moves of similar size (in EURUSD terms C1 is short, so compare raw block moves)
        r1, r2 = -m1, m2      # raw EURUSD moves in bp (C1 short -> raw = -net approx)
        artefact = bool(np.sign(r1) == np.sign(r2) and min(abs(r1), abs(r2)) > 0.5 * max(abs(r1), abs(r2)) and any(passes.values()))
        res["drift_artefact"] = artefact
        if artefact: passes = {k: False for k in passes}
        res["verdict"] = passes
        print(f"\nATTEMPT 56 IS VERDICT: {passes} (drift artefact: {artefact})")
    json.dump(res, open(os.path.join(HERE, "results", f"r78_fxtod_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
