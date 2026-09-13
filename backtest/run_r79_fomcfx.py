"""Attempt 57 (Round 79): USD depreciation on FOMC days - long EURUSD around the 14:00 ET statement.

W1 PRE: prior day 17:00 NY -> 14:00 ET; W2 POST: 14:00 -> 17:00 ET; entry = open of the first bar at/after
the window start, exit = close of the last bar before the window end; cost 1 pip RT, 1.5x / 2x.
IS = ejtrader m15 (New York = feed - 7 h); OOS = Dukascopy 1m (UTC -> America/New_York), sealed unless
UNSEAL_OK=1 --unseal. Read-only: full day, FOMC-1 / FOMC+1, non-FOMC control, mirrors, per-year, USDJPY.
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
PIP = {"EURUSD": 1e-4, "USDJPY": 1e-2}
FOMC = pd.to_datetime(FOMC_DATES).date
SIGN = {"EURUSD": +1, "USDJPY": -1}          # USD down on FOMC days


def load_is(sym):
    df = pd.read_csv(os.path.join(HERE, "data", f"{sym}_m15_ejtrader.csv"), parse_dates=["Date"])
    px = df[["open", "high", "low", "close"]].astype(float)
    lo, hi = (0.8, 1.6) if sym == "EURUSD" else (60.0, 200.0)
    for _ in range(8):
        if lo <= px.close.median() <= hi: break
        px = px / 10.0
    assert lo <= px.close.median() <= hi
    px.index = df.Date - pd.Timedelta(hours=7)                       # New York clock, all year
    return px.sort_index()


def load_oos(sym):
    df = pd.read_csv(os.path.join(HERE, "data", "fx", "dukascopy", f"{sym}_1m.csv"), parse_dates=["time"]).set_index("time")
    df = df[df.volume > 0].tz_convert(ZoneInfo("America/New_York"))
    df = df[df.index >= pd.Timestamp("2022-04-01", tz="America/New_York")]
    px = df[["open", "high", "low", "close"]].astype(float); px.index = px.index.tz_localize(None)
    return px


def window_move(px, t0, t1):
    w = px[(px.index >= t0) & (px.index < t1)]
    if len(w) < 4:
        return np.nan, np.nan
    return float(np.log(w.close.iloc[-1] / w.open.iloc[0]) * 1e4), float(w.open.iloc[0])


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10:
        return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


WINDOWS = {"W1_pre": (-7, 14), "W2_post": (14, 17), "full_day": (-7, 17)}   # hours relative to the FOMC date's 00:00 NY (-7 = prior 17:00)


def day_rows(px, sym, dates, tag):
    rows = []
    for d in dates:
        base = pd.Timestamp(d)
        for wn, (h0, h1) in WINDOWS.items():
            mv, p0 = window_move(px, base + pd.Timedelta(hours=h0), base + pd.Timedelta(hours=h1))
            if np.isnan(mv): continue
            cost = PIP[sym] / p0 * 1e4; s = SIGN[sym]
            rows.append(dict(date=str(d), tag=tag, window=wn, sym=sym, raw=mv, gross=s * mv, net=s * mv - cost, net15=s * mv - 1.5 * cost, net2=s * mv - 2 * cost))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    for sym in ("EURUSD", "USDJPY"):
        px = load_oos(sym) if UNSEAL else load_is(sym)
        alld = sorted(set(px.index.date)); alld = [d for d in alld if pd.Timestamp(d).dayofweek < 5]
        span = (px.index.min().date(), px.index.max().date())
        fomc = [d for d in FOMC if span[0] < d <= span[1]]
        idx = {d: i for i, d in enumerate(alld)}
        prev = [alld[idx[d] - 1] for d in fomc if d in idx and idx[d] > 0]
        nxt = [alld[idx[d] + 1] for d in fomc if d in idx and idx[d] + 1 < len(alld)]
        ctrl = [d for d in alld if d not in set(fomc) and d not in set(prev) and d not in set(nxt)]
        parts = [day_rows(px, sym, fomc, "fomc"), day_rows(px, sym, prev, "fomc-1"), day_rows(px, sym, nxt, "fomc+1"), day_rows(px, sym, ctrl, "control")]
        t = pd.concat(parts).sort_values("date").reset_index(drop=True)
        out = {"span": [str(span[0]), str(span[1])], "fomc_days": len(fomc)}
        for tag in ("fomc", "fomc-1", "fomc+1", "control"):
            for wn in WINDOWS:
                g = t[(t.tag == tag) & (t.window == wn)]
                key = f"{tag}|{wn}"
                out[key] = dict(x1=stats(g.net), gross=stats(g.gross)) if tag != "fomc" else dict(
                    x1=stats(g.net), x15=stats(g.net15), x2=stats(g.net2), gross=stats(g.gross), mirror_x1=stats(-g.gross - (g.gross - g.net)),
                    per_year_net={int(y): round(float(v), 1) for y, v in g.groupby(pd.to_datetime(g.date).dt.year).net.mean().items()})
        res[sym] = out
        print(f"=== {sym} ({'OOS' if UNSEAL else 'IS'}) {out['span']} FOMC days {len(fomc)} ===")
        for k, v in out.items():
            if isinstance(v, dict): print(f"  {k:18s} net {json.dumps(v['x1'], default=float)}  gross mean {v['gross'].get('mean_bp', float('nan')):+.2f}" + (f"  per-year {v['per_year_net']}" if 'per_year_net' in v else ""))
    passes = {}
    for wn in ("W1_pre", "W2_post"):
        s = res["EURUSD"][f"fomc|{wn}"]["x1"]; x2 = res["EURUSD"][f"fomc|{wn}"]["x2"]
        passes[wn] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2.24 and s.get("pf", 0) >= 1.15
                          and s.get("halves") == [1.0, 1.0] and x2.get("mean_bp", -1) > 0)
    res["verdict"] = passes
    print(f"\nATTEMPT 57 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r79_fomcfx_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
