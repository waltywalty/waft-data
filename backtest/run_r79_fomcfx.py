"""Attempt 57 (Round 79, RE-REGISTERED after critic review): USD depreciation on FOMC days - long EURUSD.

Cells (selectable, EURUSD, long; Bonferroni 2 -> t floor 2.28 at df ~71):
  W1 PRE : 18:00 New York on the prior trading day -> 14:00 ET on the statement day
  W2 POST: 14:00 ET -> 17:00 ET on the statement day
Gated statistic = the FOMC-window mean MINUS the same clock window on non-event control days (the paper's
claim is a differential, per attempt 34's precedent), Welch t on the differential, halves [+,+] on the
differential; plus FOMC net mean > 0, PF >= 1.15, positive at 2x cost; calendar-shift max-stat p < 0.05.
Entry = open of the first bar at/after the window start (coverage-guarded), exit = close of the last bar
before the window end; cost 1 pip RT (~0.9 bp), 1.5x / 2x / 4x; W2 delayed-entry read (entry = close of the
first bar) reported alongside.
Clock: IS ejtrader m15 = CET/CEST before 2014-12-01 and EET/EEST after (vendor splice), EU DST calendar ->
London wall clock -> UTC -> America/New_York; a provenance assertion requires >= 75% of FOMC days to carry
their range peak at 14:00-14:30 NY. OOS Dukascopy 1m = UTC -> America/New_York, sealed (UNSEAL_OK=1 --unseal).
Read-only: full day (prior 18:00 -> 17:00), FOMC-1 / FOMC+1, control, mirrors, per-year, easing/tightening
split, USDJPY (short) and AUDUSD (long, IS only - the paper's high-differential prediction AUD > EUR).
Outputs results/r79_fomcfx_{is,oos}.json.
"""
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fomc_dates import FOMC_DATES  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
NY, LON = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
PIP = {"EURUSD": 1e-4, "USDJPY": 1e-2, "AUDUSD": 1e-4}
SCALE = {"EURUSD": (0.8, 1.6), "USDJPY": (60.0, 200.0), "AUDUSD": (0.5, 1.2)}
FOMC = sorted(pd.to_datetime(FOMC_DATES).date)
# unscheduled Fed actions: excluded from the CONTROL, never added to the event set
EXTRA_FED_DAYS = set(pd.to_datetime(["2020-03-03", "2020-03-13", "2020-03-16"]).date)
SIGN = {"EURUSD": +1, "USDJPY": -1, "AUDUSD": +1}          # USD down on FOMC days
T_FLOOR = 2.28
# hours relative to the FOMC date's 00:00 NY (-6 = prior day 18:00 NY)
WINDOWS = {"W1_pre": (-6, 14), "W2_post": (14, 17), "full_day": (-6, 17)}
# read-only regime split (public cycle dates, approximate): cutting cycles vs hiking cycles vs hold
EASING = [("2019-07-31", "2020-03-31"), ("2024-09-18", "2026-12-31")]
TIGHT = [("2015-12-16", "2018-12-19"), ("2022-03-16", "2023-07-26")]
RNG = np.random.default_rng(79)


def regime(d):
    ts = pd.Timestamp(d)
    if any(pd.Timestamp(a) <= ts <= pd.Timestamp(b) for a, b in EASING): return "easing"
    if any(pd.Timestamp(a) <= ts <= pd.Timestamp(b) for a, b in TIGHT): return "tightening"
    return "hold"


def load_is(sym):
    df = pd.read_csv(os.path.join(HERE, "data", f"{sym}_m15_ejtrader.csv"), parse_dates=["Date"])
    px = df[["open", "high", "low", "close"]].astype(float)
    lo, hi = SCALE[sym]
    for _ in range(8):
        if lo <= px.close.median() <= hi: break
        px = px / 10.0
    assert lo <= px.close.median() <= hi
    base = np.where(df.Date < pd.Timestamp("2014-12-01"), 1, 2)      # CET era -> EET era vendor splice
    lon = (df.Date - pd.to_timedelta(base, unit="h")).dt.tz_localize(LON, ambiguous="NaT", nonexistent="shift_forward")
    px.index = lon; px = px[~px.index.isna()]
    px.index = px.index.tz_convert(NY).tz_localize(None)
    return px.sort_index(), pd.Timedelta(minutes=15)


def load_oos(sym):
    df = pd.read_csv(os.path.join(HERE, "data", "fx", "dukascopy", f"{sym}_1m.csv"), parse_dates=["time"]).set_index("time")
    df = df[df.volume > 0].tz_convert(NY)
    df = df[df.index >= pd.Timestamp("2022-04-01", tz=NY)]
    px = df[["open", "high", "low", "close"]].astype(float); px.index = px.index.tz_localize(None)
    return px, pd.Timedelta(minutes=1)


def clock_assert(px, bar, dates, label):
    """>= 75% of FOMC days must carry their 12:00-16:00 NY range peak in the 14:00-14:30 slot."""
    hits = tot = 0
    for d in dates:
        base = pd.Timestamp(d); w = px[(px.index >= base + pd.Timedelta(hours=12)) & (px.index < base + pd.Timedelta(hours=16))]
        if len(w) < 8: continue
        tot += 1; pk = (w.high - w.low).idxmax(); m = pk.hour * 60 + pk.minute
        hits += 14 * 60 <= m <= 14 * 60 + 30
    frac = hits / max(tot, 1); print(f"{label} clock provenance: {hits}/{tot} FOMC days peak at 14:00-14:30 NY ({frac:.0%})")
    assert frac >= 0.75, f"clock unverified on {label}: {frac:.0%}"
    return dict(hits=hits, days=tot, frac=frac)


def window_move(px, bar, t0, t1, delayed=False):
    i0, i1 = px.index.searchsorted([t0, t1], side="left"); w = px.iloc[i0:i1]
    exp = (t1 - t0) / bar
    if len(w) < 0.6 * exp or (w.index[0] - t0) > 2 * bar or (t1 - w.index[-1]) > 2 * bar:
        return np.nan, np.nan
    p0 = float(w.close.iloc[0]) if delayed else float(w.open.iloc[0])
    return float(np.log(w.close.iloc[-1] / p0) * 1e4), p0


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def welch(a, b):
    a = np.asarray(a, float); a = a[np.isfinite(a)]; b = np.asarray(b, float); b = b[np.isfinite(b)]
    if len(a) < 10 or len(b) < 10: return dict(n_event=int(len(a)), n_control=int(len(b)))
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return dict(n_event=int(len(a)), n_control=int(len(b)), diff_bp=float(a.mean() - b.mean()), t=float((a.mean() - b.mean()) / se))


def diff_halves(ev, ct):
    """sign of the event-minus-control differential in each chronological half (control split at the same date)."""
    ev = ev.sort_values("date"); m = len(ev) // 2; cut = ev.date.iloc[m]
    out = []
    for e, c in ((ev.iloc[:m], ct[ct.date < cut]), (ev.iloc[m:], ct[ct.date >= cut])):
        out.append(float(np.sign(e.gross.mean() - c.gross.mean())) if len(e) and len(c) else 0.0)
    return out


def day_rows(px, bar, sym, dates, tag):
    rows = []
    for d in dates:
        base = pd.Timestamp(d)
        for wn, (h0, h1) in WINDOWS.items():
            mv, p0 = window_move(px, bar, base + pd.Timedelta(hours=h0), base + pd.Timedelta(hours=h1))
            if np.isnan(mv): continue
            cost = PIP[sym] / p0 * 1e4; s = SIGN[sym]
            r = dict(date=str(d), tag=tag, window=wn, sym=sym, regime=regime(d), raw=mv, gross=s * mv, net=s * mv - cost,
                     net15=s * mv - 1.5 * cost, net2=s * mv - 2 * cost, net4=s * mv - 4 * cost)
            if wn == "W2_post":
                mvd, _ = window_move(px, bar, base + pd.Timedelta(hours=h0), base + pd.Timedelta(hours=h1), delayed=True)
                r["net_delayed"] = s * mvd - cost if np.isfinite(mvd) else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    syms = ("EURUSD",) if UNSEAL else ("EURUSD", "USDJPY", "AUDUSD")
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r79_fomcfx_is.json")))
        cleared = [c for c, ok in isr["verdict"].items() if ok]
        if not cleared: raise SystemExit("no cell cleared IS; holdout stays sealed")
    for sym in syms:
        px, bar = load_oos(sym) if UNSEAL else load_is(sym)
        alld = [d for d in sorted(set(px.index.date)) if pd.Timestamp(d).dayofweek < 5]
        idx = {d: i for i, d in enumerate(alld)}
        fomc = [d for d in FOMC if d in idx and idx[d] > 0 and idx[d] + 1 < len(alld)]
        gate = clock_assert(px, bar, fomc, f"{sym} {'OOS' if UNSEAL else 'IS'}")
        prev = [alld[idx[d] - 1] for d in fomc]; nxt = [alld[idx[d] + 1] for d in fomc]
        excl = set(fomc) | set(prev) | set(nxt) | EXTRA_FED_DAYS
        ctrl = [d for d in alld if d not in excl]
        parts = [day_rows(px, bar, sym, fomc, "fomc"), day_rows(px, bar, sym, prev, "fomc-1"), day_rows(px, bar, sym, nxt, "fomc+1"), day_rows(px, bar, sym, ctrl, "control")]
        t = pd.concat(parts).sort_values("date").reset_index(drop=True)
        out = {"span": [str(alld[0]), str(alld[-1])], "fomc_days": len(fomc), "control_days": len(ctrl), "clock": gate}
        ct_all = t[t.tag == "control"]
        for tag in ("fomc", "fomc-1", "fomc+1", "control"):
            for wn in WINDOWS:
                g = t[(t.tag == tag) & (t.window == wn)]; key = f"{tag}|{wn}"
                if tag == "control":
                    out[key] = dict(gross=stats(g.gross)); continue
                ct = ct_all[ct_all.window == wn]
                out[key] = dict(x1=stats(g.net), gross=stats(g.gross), vs_control=welch(g.gross, ct.gross), diff_halves=diff_halves(g, ct))
                if tag == "fomc":
                    out[key].update(x15=stats(g.net15), x2=stats(g.net2), x4=stats(g.net4), mirror_x1=stats(-g.gross - (g.gross - g.net)),
                                    per_year_net={int(y): round(float(v), 1) for y, v in g.groupby(pd.to_datetime(g.date).dt.year).net.mean().items()},
                                    regime_diff={rg: round(float(g[g.regime == rg].gross.mean() - ct[ct.regime == rg].gross.mean()), 2)
                                                 for rg in ("easing", "tightening", "hold") if (g.regime == rg).sum() >= 5 and (ct.regime == rg).sum() >= 20})
                    if wn == "W2_post": out[key]["delayed_entry_x1"] = stats(g.net_delayed)
        res[sym] = out
        print(f"=== {sym} ({'OOS' if UNSEAL else 'IS'}) {out['span']} FOMC days {len(fomc)}, control {len(ctrl)} ===")
        for k, v in out.items():
            if isinstance(v, dict) and "x1" in v:
                print(f"  {k:18s} net {json.dumps(v['x1'], default=float)}  vs_control {json.dumps(v['vs_control'], default=float)} diff_halves {v['diff_halves']}"
                      + (f"\n      per-year {v['per_year_net']} regime {v['regime_diff']} x2 {v['x2'].get('mean_bp', float('nan')):+.2f} x4 {v['x4'].get('mean_bp', float('nan')):+.2f}" if 'per_year_net' in v else "")
                      + (f" delayed {json.dumps(v['delayed_entry_x1'], default=float)}" if 'delayed_entry_x1' in v else ""))
            elif isinstance(v, dict) and "gross" in v:
                print(f"  {k:18s} control gross {json.dumps(v['gross'], default=float)}")
        if sym == "EURUSD" and not UNSEAL:
            # calendar-shift max-stat: shift every FOMC date by k trading days, k in +-1..+-250 (500 shifts, all used)
            allrows = t.set_index(["date", "window"])  # gross by (date, window) for every tagged day
            grossmap = {wn: t[t.window == wn].set_index("date").gross for wn in ("W1_pre", "W2_post")}
            # rows for days not in any tag (none: every weekday is tagged) -> use t directly
            def max_t(dates):
                ex = {str(d) for d in dates}; vals = []
                for wn in ("W1_pre", "W2_post"):
                    gm = grossmap[wn]; e = gm[gm.index.isin(ex)]; c = gm[~gm.index.isin(ex)]
                    vals.append(abs(welch(e, c).get("t", 0.0)))
                return max(vals)
            obs = max_t(fomc); n = len(alld); mx = []
            for k in list(range(1, 251)) + list(range(-250, 0)):
                sh = [alld[idx[d] + k] for d in fomc if 0 <= idx[d] + k < n]
                mx.append(max_t(sh))
            mx = np.array(mx); res["maxstat"] = dict(obs_max_t=obs, p=float((np.sum(mx >= obs) + 1) / (len(mx) + 1)), shifts=int(len(mx)))
            print("  maxstat (calendar shift):", res["maxstat"])
    passes = {}
    cells = cleared if UNSEAL else ("W1_pre", "W2_post")
    for wn in cells:
        c = res["EURUSD"][f"fomc|{wn}"]; s, x2, vc = c["x1"], c["x2"], c["vs_control"]
        t_ok = (vc.get("t") if vc.get("t") is not None else -9) >= (2.0 if UNSEAL else T_FLOOR)
        p_ok = True if UNSEAL else res["maxstat"]["p"] < 0.05
        passes[wn] = bool(s.get("n", 0) >= (30 if UNSEAL else 40) and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and x2.get("mean_bp", -1) > 0
                          and vc.get("diff_bp", -1) > 0 and t_ok and c["diff_halves"] == [1.0, 1.0] and p_ok)
    res["verdict"] = passes
    print(f"\nATTEMPT 57 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r79_fomcfx_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
