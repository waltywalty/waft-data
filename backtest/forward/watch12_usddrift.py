"""Watch item #12 (attempt 55): USD post-release drift on EURUSD, forward scorer.

Frozen cell: mapped USD direction from the registered release-name set (short EURUSD on a
USD-positive surprise), enter at the open of the 5m bar starting t0+5m, exit at the close of
the 5m bar starting t0+55m, 1 pip round-trip cost. Inputs: data/forward/eurusd_5m_*.json
(IBKR EUR.USD CASH, midpoint, concatenated, later file wins) and data/econ_events_us_high_fxs.json
(FXStreet; re-pulled monthly). Events before START are the attempt-55 IS/OOS sample and are
never scored here. Prints the forward tally and writes results/watch12_forward.json.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); BT = os.path.dirname(HERE)
sys.path.insert(0, BT)
from run_r75_usddrift import POS, CLASS  # noqa: E402  (frozen name set; the module body runs IS only if executed directly)

START = pd.Timestamp("2026-09-12", tz="UTC")   # registration date; forward events strictly after
PIP = 1e-4


def load_eur(data_dir):
    parts = []
    for f in sorted(glob.glob(os.path.join(data_dir, "eurusd_5m_*.json"))):
        d = json.load(open(f))
        parts.append(pd.DataFrame(dict(open=pd.to_numeric(d["open"]), close=pd.to_numeric(d["close"])), index=pd.to_datetime(d["time"], utc=True)))
    if not parts:
        return pd.DataFrame(columns=["open", "close"])
    b = pd.concat(parts).sort_index(kind="stable")
    return b[~b.index.duplicated(keep="last")]


def events():
    ev = pd.DataFrame(json.load(open(os.path.join(BT, "data", "econ_events_us_high_fxs.json")))["result"]["events"])
    ev["t"] = pd.to_datetime(ev.d, utc=True)
    ev = ev[(ev.t > START) & ev.n.isin(POS) & (ev.dev.fillna(0) != 0)].copy()
    et = ev.t.dt.tz_convert("America/New_York"); ev = ev[(et.dt.hour * 100 + et.dt.minute).isin([830, 1000])]
    ev["absdev"] = ev.dev.abs()
    ev = ev.sort_values(["t", "absdev"], ascending=[True, False]).drop_duplicates("t", keep="first")
    ev["usd"] = np.sign(ev.dev).astype(int)
    return ev


def rows(data_dir):
    b = load_eur(data_dir); out = []
    for _, r in events().iterrows():
        e = b[b.index == r.t + pd.Timedelta(minutes=5)]; x = b[b.index == r.t + pd.Timedelta(minutes=55)]
        if len(e) != 1 or len(x) != 1:
            continue
        gross = -r.usd * np.log(x.close.iloc[0] / e.open.iloc[0]) * 1e4
        out.append(dict(t=str(r.t), name=r.n, dev=float(r.dev), usd=int(r.usd), gross_bp=float(gross), net_bp=float(gross - PIP / e.open.iloc[0] * 1e4)))
    return out


def main():
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BT, "data", "forward")
    rr = rows(dd); x = np.array([r["net_bp"] for r in rr])
    s = dict(n=int(len(x)))
    if len(x) >= 2:
        s.update(mean_net_bp=float(x.mean()), wr=float((x > 0).mean()), t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 0 else None)
    print(f"watch #12 forward: {s}; sign-agreement shot condition: n >= 40 and mean > 0 -> {'MET' if s['n'] >= 40 and s.get('mean_net_bp', -1) > 0 else 'not met'}")
    for r in rr:
        print(f"  {r['t']} {r['name'][:34]:34s} dev {r['dev']:+.2f} usd {r['usd']:+d} net {r['net_bp']:+.2f} bp")
    json.dump(dict(start=str(START), summary=s, events=rr), open(os.path.join(BT, "results", "watch12_forward.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
