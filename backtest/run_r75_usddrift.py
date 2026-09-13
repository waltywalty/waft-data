"""Attempt 55 (Round 75): USD post-announcement drift on EURUSD after 08:30 / 10:00 ET US releases.

Stage 1 gate: the release jump (t0 -> t0+5m) signed by the mapped USD direction must be > 0
with t >= 3 at IS, else the family dies unrun. Stage 2 (P1): enter open of the t0+5m bar,
exit close of the bar ending t0+60m, direction = mapped USD direction (short EURUSD on a
USD-positive surprise); cost 1 pip RT; 1.5x / 2x. IS = first 75% of release timestamps; OOS
sealed unless UNSEAL_OK=1 --unseal. Outputs results/r75_usddrift_is.json (or _oos.json).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
POS = {"Nonfarm Payrolls", "Average Hourly Earnings (MoM)", "Average Hourly Earnings (YoY)", "Retail Sales (MoM)",
       "Retail Sales Control Group", "Gross Domestic Product Annualized", "Durable Goods Orders",
       "Nondefense Capital Goods Orders ex Aircraft", "Consumer Price Index (MoM)", "Consumer Price Index (YoY)",
       "Consumer Price Index ex Food & Energy (MoM)", "Consumer Price Index ex Food & Energy (YoY)",
       "Producer Price Index ex Food & Energy (YoY)", "Core Personal Consumption Expenditures - Price Index (MoM)",
       "Core Personal Consumption Expenditures - Price Index (YoY)", "ISM Manufacturing PMI", "ISM Services PMI"}
CLASS = {"growth": {"Nonfarm Payrolls", "Retail Sales (MoM)", "Retail Sales Control Group", "Gross Domestic Product Annualized",
                    "Durable Goods Orders", "Nondefense Capital Goods Orders ex Aircraft", "ISM Manufacturing PMI", "ISM Services PMI"},
         "inflation": {n for n in POS if "Price" in n or "Earnings" in n}}
PIP = {"EURUSD": 1e-4, "USDJPY": 1e-2}


if __name__ == "__main__":


    def load(sym):
        df = pd.read_csv(f"data/fx/dukascopy/{sym}_1m.csv", parse_dates=["time"]).set_index("time")
        return df[df.volume > 0]


    ev = pd.DataFrame(json.load(open("data/econ_events_us_high_fxs.json"))["result"]["events"])
    ev["t"] = pd.to_datetime(ev.d, utc=True)
    ev = ev[(ev.t >= "2022-04-01") & (ev.t <= "2026-09-11") & ev.n.isin(POS) & (ev.dev.fillna(0) != 0)].copy()
    et = ev.t.dt.tz_convert("America/New_York"); ev = ev[(et.dt.hour * 100 + et.dt.minute).isin([830, 1000])]
    ev["absdev"] = ev.dev.abs()
    ev = ev.sort_values(["t", "absdev"], ascending=[True, False]).drop_duplicates("t", keep="first").reset_index(drop=True)
    ev["usd"] = np.sign(ev.dev).astype(int)                    # +1 = USD-positive surprise (all names are USD-positive-on-beat)
    ev["cls"] = ["growth" if n in CLASS["growth"] else "inflation" for n in ev.n]
    cut = int(len(ev) * 0.75); ev["oos"] = ev.index >= cut
    evs = ev[ev.oos] if UNSEAL else ev[~ev.oos]
    print(f"release timestamps {len(ev)} (IS {cut}, OOS {len(ev) - cut}); this run {'OOS' if UNSEAL else 'IS'} n {len(evs)}; last {evs.t.max()}")


    def mv(px, t0, t1):
        w = px[(px.index >= t0) & (px.index < t1)]
        return np.nan if len(w) < max(3, int((t1 - t0).total_seconds() / 60 * 0.5)) else float(np.log(w.close.iloc[-1] / w.open.iloc[0]) * 1e4)


    def stats(x):
        x = np.asarray(x, float); x = x[np.isfinite(x)]
        if len(x) < 10:
            return dict(n=int(len(x)))
        m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
        return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                    pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                    t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                    halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


    def window(px, sym, a, b, sign_col="usd", mult=1.0, shift_days=0, usd_to_px=-1.0):
        """Signed net return in bp per event over [t0+a, t0+b) minutes (shifted by shift_days).
        usd_to_px: EURUSD moves opposite to USD (-1); USDJPY with USD (+1)."""
        out = []
        for _, r in evs.iterrows():
            t0 = r.t + pd.Timedelta(days=shift_days)
            m = mv(px, t0 + pd.Timedelta(minutes=a), t0 + pd.Timedelta(minutes=b))
            if np.isnan(m):
                continue
            px0 = px[px.index >= t0 + pd.Timedelta(minutes=a)].open.iloc[0]
            out.append(dict(t=r.t, n=r.n, cls=r.cls, dev=r.dev, ret=r[sign_col] * usd_to_px * m - mult * PIP[sym] / px0 * 1e4))
        return pd.DataFrame(out)


    res = {"unsealed": UNSEAL, "events": int(len(evs))}
    eur = load("EURUSD")
    # stage 1: mapping gate on the jump (no cost)
    jump = window(eur, "EURUSD", 0, 5, mult=0.0)
    res["gate_jump_0_5m"] = stats(jump.ret)
    res["gate_jump_by_class"] = {c: stats(jump[jump.cls == c].ret) for c in ("growth", "inflation")}
    g = res["gate_jump_0_5m"]
    GATE = g.get("n", 0) >= 40 and g.get("mean_bp", -1) > 0 and (g.get("t") or -9) >= 3
    res["gate_pass"] = bool(GATE)
    print("STAGE 1 jump (signed by mapping):", json.dumps(g, default=float)); print("  by class:", json.dumps(res["gate_jump_by_class"], default=float))
    print(f"GATE: {'PASS' if GATE else 'FAIL - drift cell not read'}")
    if GATE:
        p1 = window(eur, "EURUSD", 5, 60)
        res["P1_5_60"] = dict(x1=stats(p1.ret), x15=stats(window(eur, "EURUSD", 5, 60, mult=1.5).ret), x2=stats(window(eur, "EURUSD", 5, 60, mult=2.0).ret),
                              gross=stats(window(eur, "EURUSD", 5, 60, mult=0.0).ret),
                              per_year={int(y): round(float(v), 2) for y, v in p1.groupby(p1.t.dt.year).ret.mean().items()},
                              per_class={c: stats(p1[p1.cls == c].ret) for c in ("growth", "inflation")})
        res["horizon_5_30_x1"] = stats(window(eur, "EURUSD", 5, 30).ret)
        res["horizon_5_120_x1"] = stats(window(eur, "EURUSD", 5, 120).ret)
        res["mirror_x1"] = stats(-window(eur, "EURUSD", 5, 60, mult=0.0).ret - (PIP["EURUSD"] / 1.09 * 1e4))
        res["placebo_lookahead_-60_-5_gross"] = stats(window(eur, "EURUSD", -60, -5, mult=0.0).ret)
        res["placebo_nextday_5_60_gross"] = stats(window(eur, "EURUSD", 5, 60, mult=0.0, shift_days=1).ret)
        q = p1.dev.abs().quantile([1 / 3, 2 / 3]).values
        res["dose_terciles_x1"] = {k: stats(p1[m].ret) for k, m in (("low", p1.dev.abs() <= q[0]), ("mid", (p1.dev.abs() > q[0]) & (p1.dev.abs() <= q[1])), ("high", p1.dev.abs() > q[1]))}
        res["dose_cuts"] = [float(x) for x in q]
        jpy = load("USDJPY")
        res["USDJPY_readonly"] = dict(jump=stats(window(jpy, "USDJPY", 0, 5, mult=0.0, usd_to_px=+1.0).ret), P1_x1=stats(window(jpy, "USDJPY", 5, 60, usd_to_px=+1.0).ret))
        s = res["P1_5_60"]["x1"]
        PASS = (s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2 and s.get("pf", 0) >= 1.15
                and s.get("halves") == [1.0, 1.0] and res["P1_5_60"]["x2"]["mean_bp"] > 0)
        res["P1_pass"] = bool(PASS)
        for k, v in res.items():
            if k not in ("unsealed", "events", "gate_jump_0_5m", "gate_jump_by_class", "gate_pass"):
                print(f"  {k}: {json.dumps(v, default=float)}")
        print(f"\nATTEMPT 55 {'OOS' if UNSEAL else 'IS'} VERDICT: {'PASS' if PASS else 'FAIL'}")
    json.dump(res, open(f"results/r75_usddrift_{'oos' if UNSEAL else 'is'}.json", "w"), indent=1, default=float)
