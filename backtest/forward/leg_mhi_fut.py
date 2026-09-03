"""MHIF leg of the forward auto-journal: the MHI frozen rule (run_hsi.py H-A fade,
cell t0.3_s0.5_c1600) evaluated on REAL HSI futures 15m bars instead of the HK33 CFD.

Why it exists (ledger 2026-09-03, futures fidelity check): the CFD has no pre-open
auction print, so its 01:15 UTC bar is synthetic and its push is ~0.7x the futures
push; at the frozen 0.3 threshold the two feeds trigger on disjoint sessions. The
CFD stream (leg_mhi) keeps running for comparison; THIS stream is the one a futures
account would actually trade and is the promotion evidence for the MHI rule.

Input: <data_dir>/hsi_fut_15m_*.json - IBKR get_price_history responses for the
front-month HSI future (HKFE), FIFTEEN_MINS, outside_rth true, one file per weekly
pull, optional key "contract". Files are concatenated in sorted-name order; where two
pulls overlap (a roll), the LATER file's bars win. The rule itself is imported from
leg_mhi so the two legs cannot drift apart.
"""
import glob
import json
import os

import numpy as np
import pandas as pd

import leg_mhi as M

INSTR = "MHIF"


def load(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, "hsi_fut_15m_*.json")))
    if not files:
        raise FileNotFoundError("no hsi_fut_15m_*.json in " + data_dir)
    parts = []
    for f in files:
        d = json.load(open(f))
        b = pd.DataFrame({"open": pd.to_numeric(d["open"]), "high": pd.to_numeric(d["high"]),
                          "low": pd.to_numeric(d["low"]), "close": pd.to_numeric(d["close"])},
                         index=pd.to_datetime(d["time"], utc=True))
        b["contract"] = d.get("contract", os.path.basename(f))
        parts.append(b)
    H = pd.concat(parts).sort_index(kind="stable")
    H = H[~H.index.duplicated(keep="last")]      # later file wins on overlap
    return H


def rows(data_dir, require_complete=True):
    H = load(data_dir)
    out = []
    for t in M._trades(H[["open", "high", "low", "close"]], require_complete=require_complete):
        contract = H.loc[t["t_entry"], "contract"] if t["t_entry"] in H.index else "?"
        out.append(dict(
            date=(t["t_entry"] + M.HKT).date().isoformat(),
            instr=INSTR,
            side="S" if t["push"] > 0 else "L",
            entry=t["entry"],
            stop=t["stop"],
            exit=t["exit"],
            note="fade|" + ("stop" if t["stopped"] else "time") + "|" + str(contract),
            src="auto",
        ))
    return out


def status(data_dir):
    H = load(data_dir)
    Hp, atr14 = M._prepare(H[["open", "high", "low", "close"]])
    last = H.index.max()
    d = last.date()
    pre = Hp[(Hp.d == d) & (Hp.hm == M.PRE_HM)]
    line = (f"MHIF: futures data {H.index.min().date()} -> {last.isoformat()} "
            f"(contracts {', '.join(sorted(set(H.contract)))}); intraday leg, no overnight position")
    if len(pre) and d in atr14 and np.isfinite(atr14[d]):
        push = pre.close.iloc[0] - pre.open.iloc[0]
        pn = push / atr14[d]
        line += (f"; last session {d.isoformat()} push {push:+.1f} = {pn:+.2f} ATR14 "
                 f"({'TRIGGER' if abs(pn) >= M.TRIG else 'no trigger'})"
                 f"{'' if M._session_complete(Hp, d) else ' [session incomplete]'}")
    return line


if __name__ == "__main__":
    import sys
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "forward")
    for r in rows(dd):
        print(r)
    print(status(dd))
