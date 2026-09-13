"""Attempt 56 (Round 78): Ranaldo time-of-day pattern - EURUSD by trading-hour block.

C1 SHORT EURUSD 08:00 -> 13:00 London; C2 LONG EURUSD 13:00 -> 21:00 London; every weekday; entry =
open of the block's first 15m bar, exit = close of its last bar; cost 1 pip RT, 1.5x / 2x.
IS = ejtrader m15 2012-11..2022-03 (London = feed stamp - 2 h); OOS = Dukascopy 1m 2022-04..2026-09
(UTC -> Europe/London), sealed unless UNSEAL_OK=1 --unseal. Read-only: Asia block, mirrors, per-year,
day-of-week, USDJPY under the paper's sign, gross vs net. Outputs results/r78_fxtod_{is,oos}.json.
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
BLOCKS = {"asia_00_08": (0, 8), "eu_08_13": (8, 13), "us_13_21": (13, 21)}
# paper's sign per (instrument, block): EURUSD short in EU hours, long in US hours; USDJPY long in Tokyo hours, short in US hours
SIGN = {("EURUSD", "eu_08_13"): -1, ("EURUSD", "us_13_21"): +1, ("EURUSD", "asia_00_08"): 0,
        ("USDJPY", "asia_00_08"): +1, ("USDJPY", "us_13_21"): -1, ("USDJPY", "eu_08_13"): 0}


def load_is(sym):
    df = pd.read_csv(os.path.join(HERE, "data", f"{sym}_m15_ejtrader.csv"), parse_dates=["Date"])
    px = df[["open", "high", "low", "close"]].astype(float)
    lo, hi = (0.8, 1.6) if sym == "EURUSD" else (60.0, 200.0)
    for _ in range(8):
        if lo <= px.close.median() <= hi: break
        px = px / 10.0
    assert lo <= px.close.median() <= hi
    px.index = df.Date - pd.Timedelta(hours=2)                       # London clock, all year (UTC+2 winter / UTC+3 summer feed)
    return px.sort_index()


def load_oos(sym):
    df = pd.read_csv(os.path.join(HERE, "data", "fx", "dukascopy", f"{sym}_1m.csv"), parse_dates=["time"]).set_index("time")
    df = df[df.volume > 0].tz_convert(ZoneInfo("Europe/London"))
    df = df[df.index >= pd.Timestamp("2022-04-01", tz="Europe/London")]
    px = df[["open", "high", "low", "close"]].astype(float)
    px.index = px.index.tz_localize(None)                            # naive London clock, same as the IS frame
    return px


def blocks(px, sym):
    rows = []
    px = px[px.index.dayofweek < 5]
    for d, day in px.groupby(px.index.date):
        for name, (h0, h1) in BLOCKS.items():
            w = day[(day.index.hour >= h0) & (day.index.hour < h1)]
            if len(w) < 0.6 * (h1 - h0) * (4 if len(day) < 500 else 60):       # require most of the block's bars
                continue
            entry, exit_px = float(w.open.iloc[0]), float(w.close.iloc[-1])
            mv = np.log(exit_px / entry) * 1e4
            cost_bp = PIP[sym] / entry * 1e4
            s = SIGN[(sym, name)]
            rows.append(dict(date=str(d), dow=pd.Timestamp(d).dayofweek, block=name, sym=sym, raw_bp=mv, sign=s,
                             gross=s * mv if s else mv, net=(s * mv - cost_bp) if s else np.nan,
                             net15=(s * mv - 1.5 * cost_bp) if s else np.nan, net2=(s * mv - 2 * cost_bp) if s else np.nan))
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


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    for sym in ("EURUSD", "USDJPY"):
        try:
            px = load_oos(sym) if UNSEAL else load_is(sym)
        except FileNotFoundError as ex:
            res[sym] = f"skipped: {ex}"; continue
        t = blocks(px, sym)
        out = {"span": [str(t.date.min()), str(t.date.max())], "days": int(t.date.nunique())}
        for name in BLOCKS:
            g = t[t.block == name]
            if SIGN[(sym, name)]:
                out[name] = dict(sign=SIGN[(sym, name)], x1=stats(g.net), x15=stats(g.net15), x2=stats(g.net2), gross=stats(g.gross),
                                 mirror_x1=stats(-g.gross - (g.gross - g.net)),
                                 per_year_net={int(y): round(float(v), 2) for y, v in g.groupby(pd.to_datetime(g.date).dt.year).net.mean().items()},
                                 dow_net={int(k): round(float(v), 2) for k, v in g.groupby("dow").net.mean().items()})
            else:
                out[name] = dict(sign=0, unsigned_raw=stats(g.raw_bp), note="no local-currency prediction; read-only")
        res[sym] = out
        print(f"=== {sym} ({'OOS' if UNSEAL else 'IS'}) {out['span']} {out['days']} days ===")
        for name in BLOCKS:
            print(f"  {name}: {json.dumps(out[name], default=float)}")
    # verdict: EURUSD C1 / C2 selectable, Bonferroni 2 -> 2.24
    passes = {}
    for name in ("eu_08_13", "us_13_21"):
        s = res["EURUSD"][name]["x1"] if isinstance(res.get("EURUSD"), dict) else {}
        passes[name] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2.24 and s.get("pf", 0) >= 1.15
                            and s.get("halves") == [1.0, 1.0] and res["EURUSD"][name]["x2"]["mean_bp"] > 0)
    res["verdict"] = passes
    print(f"\nATTEMPT 56 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r78_fxtod_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
