"""Watch item #13 (attempt 59): month-end index-extension long in the 10-year Treasury, forward scorer.

Frozen cell: long from the close of the third-to-last business day of the month (T-3) to the month-end
close (T), every calendar month; 3 bp round-trip cost, 1.5x / 2x. Scored on TWO proxies:
  (a) the CMT par-bond proxy of the pass: FRED DGS10 in data/fred_DGS10.csv (refreshed by the monthly routine
      where FRED is reachable); return = -ModD(y0) * dy + carry, exactly as run_r81_monthend.py;
  (b) ZN front-month daily bars from data/forward/zn_1d_*.json (IBKR FUT, ONE_DAY bars, concatenated, later
      file wins), return = log(close_T / close_{T-3}) in bp of price.
Month-ends strictly after START are forward; nothing before START is ever scored here (it is the attempt-59
IS/OOS sample). Graduation bar (to a sign-off request): n >= 40 on BOTH proxies, net > 0, t >= 2, PF >= 1.15,
halves [+,+], positive at 1.5x. Prints the tally and writes results/watch13_forward.json. No journal row.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); BT = os.path.dirname(HERE)
sys.path.insert(0, BT)
from run_r81_monthend import mod_dur, stats  # noqa: E402

START = pd.Timestamp("2026-09-13")
COST_BP = 3.0


def month_end_trades(close, start=START):
    """close: Series indexed by naive date (one row per trading day). Returns DataFrame of forward T-3 -> T trades."""
    close = close.dropna().sort_index(); per = close.index.to_period("M"); rows = []
    for m in sorted(set(per)):
        pos = np.where(per == m)[0]
        if len(pos) < 4: continue
        p = int(pos[-1]); d = close.index[p]
        if d <= start: continue
        # month-end is only known once the next month has printed (guards a partial current month)
        if p + 1 >= len(close) or close.index[p + 1].to_period("M") == m: continue
        rows.append(dict(month=str(m), t_minus3=str(close.index[p - 3].date()), t=str(d.date()), c0=float(close.iloc[p - 3]), c1=float(close.iloc[p])))
    return pd.DataFrame(rows)


def score_cmt(bt=BT):
    d = pd.read_csv(os.path.join(bt, "data", "fred_DGS10.csv")); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce"); y = d.dropna().set_index("date").y
    tr = month_end_trades(y)
    if len(tr) == 0: return tr, {}
    tr["gross_bp"] = [-mod_dur(a, 10) * (b - a) / 100.0 * 1e4 + a / 100.0 * (pd.Timestamp(t1) - pd.Timestamp(t0)).days / 365.0 * 1e4
                      for a, b, t0, t1 in zip(tr.c0, tr.c1, tr.t_minus3, tr.t)]
    return tr, tally(tr)


def load_zn(data_dir):
    parts = []
    for f in sorted(glob.glob(os.path.join(data_dir, "zn_1d_*.json"))):
        d = json.load(open(f))
        parts.append(pd.DataFrame(dict(close=pd.to_numeric(d["close"]), contract=d.get("contract", os.path.basename(f))),
                                  index=pd.to_datetime(d["time"], utc=True).tz_convert("America/New_York").tz_localize(None).normalize()))
    if not parts: return pd.DataFrame(columns=["close", "contract"])
    b = pd.concat(parts).sort_index(kind="stable"); b = b[~b.index.duplicated(keep="last")]
    return b


def score_zn(data_dir):
    b = load_zn(data_dir); tr = month_end_trades(b.close) if len(b) else pd.DataFrame()
    if len(tr) == 0: return tr, {}
    same = [b.contract.get(pd.Timestamp(t0)) == b.contract.get(pd.Timestamp(t1)) for t0, t1 in zip(tr.t_minus3, tr.t)]
    tr = tr[np.array(same)].reset_index(drop=True)          # never score a month-end that straddles a contract roll
    if len(tr) == 0: return tr, {}
    tr["gross_bp"] = np.log(tr.c1 / tr.c0) * 1e4
    return tr, tally(tr)


def tally(tr):
    g = tr.gross_bp.values; out = {}
    for k, m in (("x1", 1.0), ("x15", 1.5), ("x2", 2.0)):
        out[k] = stats(g - m * COST_BP)
    s = out["x1"]
    out["bar"] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("t") or -9) >= 2 and s.get("pf", 0) >= 1.15
                      and s.get("halves") == [1.0, 1.0] and out["x15"].get("mean_bp", -1) > 0)
    out["n"] = int(len(g)); out["gross_mean_bp"] = float(g.mean()) if len(g) else None
    return out


if __name__ == "__main__":
    data_dir = os.path.join(BT, "data", "forward")
    cmt_tr, cmt = score_cmt(); zn_tr, zn = score_zn(data_dir)
    res = {"start": str(START.date()), "cmt": cmt, "zn": zn, "cmt_trades": cmt_tr.to_dict("records") if len(cmt_tr) else [], "zn_trades": zn_tr.to_dict("records") if len(zn_tr) else [],
           "graduate": bool(cmt.get("bar") and zn.get("bar"))}
    print(f"WATCH #13 forward: CMT n {cmt.get('n', 0)} mean {cmt.get('gross_mean_bp')} | ZN n {zn.get('n', 0)} mean {zn.get('gross_mean_bp')} | graduate {res['graduate']}")
    json.dump(res, open(os.path.join(BT, "results", "watch13_forward.json"), "w"), indent=1, default=float)
