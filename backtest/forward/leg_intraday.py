"""Round 71 forward-only intraday accrual on TRUE futures (ledger 2026-09-09, Round 71).

Five clock specs that the intraday program could not backtest honestly (the CFD frames
carry no auction prints and their MT5-era overnight path is not the futures' path - Round
70 provenance finding) are logged here DESCRIPTIVELY on the weekly IBKR pulls of the
front-month contracts. Nothing here writes journal rows: this leg is deliberately NOT in
autojournal.LEGS. Output = results/forward_intraday.json (per-event rows + per-spec score
at 1x / 1.5x / 2x micro costs) and the printed summary the routines quote.

Specs (frozen before the first pull was read; clock times America/New_York unless HKT):
  F1  ES expiry-morning gap fade   third Friday of every month (AM-settled SPX options;
                                    quarterly ES/SPX futures SOQ): gap = 09:30 open -
                                    prior session's 15:55-bar close (same contract);
                                    direction -sign(gap); 09:30 open -> 10:00 print.
  F2  ES MOC drift                  every session: direction sign(15:50 open - 09:30 open)
                                    (the day's return at 15:50); 15:50 open -> 16:00 print.
  F3  ES cash-close -> settlement   every session: direction -sign(16:00 print - 15:50 open)
                                    (reversal of the MOC push); 16:00 open -> 16:15 print.
  F4  GC Sunday reopen gap fade     Sunday 18:00 open vs Friday's last (16:55-bar) close:
                                    direction -sign(gap); 18:05 open -> 03:00 print Monday.
  F5  HSI futures L&I close flow    every session: direction sign(16:15 HKT open - 09:15 HKT
                                    open) (day return at 16:15); 16:15 HKT open -> 16:30
                                    print (the 08:15Z 15m bar, open -> close).
Every reference print precedes its entry; a missing bar voids the event (no fill assumed);
prints from two different contracts are never combined (a roll voids the event).
Costs per round trip: ES 0.35 pt (MES), GC 0.35 $/oz (MGC), HSI 10 pt (MHI, the house
number). R = (pnl - cost) / ATR where ATR = mean of the prior 20 sessions' 09:30-16:00 NY
range (ES/GC; the intraday engine's convention) or leg_mhi's ATR14 (HSI); while fewer
than 20 prior sessions exist the mean of the available ones (min 5) is used and atr_n
records how many. Score bar (registered): n >= 40 events, avg R > 0, t >= 2, halves
[+,+], positive at 2x cost. No promotion, no journal rows, no sizing without sign-off.
"""
import datetime as dt
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import leg_mhi as M  # noqa: E402  (ATR14 convention for HSI)

NY = "America/New_York"
COST = {"ES": 0.35, "GC": 0.35, "HSI": 10.0}
ATR_N, ATR_MIN = 20, 5


# ----------------------------------------------------------------------------- loading
def load_5m(data_dir, prefix):
    """Concatenate <prefix>_5m_*.json (IBKR get_price_history payloads, key 'contract');
    later files win on overlapping timestamps of the SAME contract; different contracts
    are kept side by side (the specs never mix them)."""
    files = sorted(glob.glob(os.path.join(data_dir, f"{prefix}_5m_*.json")))
    if not files:
        return None
    parts = []
    for f in files:
        d = json.load(open(f))
        b = pd.DataFrame({k: pd.to_numeric(d[k]) for k in ("open", "high", "low", "close", "volume")},
                         index=pd.to_datetime(d["time"], utc=True))
        b["contract"] = d.get("contract", os.path.basename(f))
        parts.append(b)
    b = pd.concat(parts).sort_index(kind="stable")
    b = b[~pd.MultiIndex.from_arrays([b.index, b.contract]).duplicated(keep="last")]
    b = b.tz_convert(NY)
    b["skey"] = (b.index + pd.Timedelta(hours=8)).date       # session = NY date of 16:00 prev -> 15:55
    b["hm"] = b.index.hour * 100 + b.index.minute
    b["dow"] = b.index.dayofweek
    return b


def _bar(day, hm):
    x = day[day.hm == hm]
    return x.iloc[0] if len(x) == 1 else None


def session_table(b):
    """Per (contract, session): RTH range and the last RTH print; ATR = mean of the PRIOR
    sessions' ranges (20, min 5)."""
    rth = b[(b.hm >= 930) & (b.hm <= 1555)]
    d = rth.groupby(["contract", "skey"]).agg(hi=("high", "max"), lo=("low", "min"), last=("close", "last"),
                                              n=("close", "size"))
    d["rng"] = d.hi - d.lo
    out = []
    for c, g in d.groupby(level=0):
        g = g.droplevel(0).sort_index()
        prior = g.rng.shift(1)
        atr = prior.rolling(ATR_N, min_periods=ATR_MIN).mean()
        atr_n = prior.rolling(ATR_N, min_periods=1).count()
        g = g.assign(atr=atr, atr_n=atr_n, contract=c)
        g.index = pd.MultiIndex.from_arrays([[c] * len(g), g.index], names=["contract", "skey"])
        out.append(g)
    return pd.concat(out) if out else d.assign(atr=np.nan, atr_n=0)


def third_friday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21


# ----------------------------------------------------------------------------- specs
def _row(spec, instr, date, contract, direction, entry, exit_px, atr, atr_n, note):
    pnl = direction * (exit_px - entry)
    cost = COST[instr]
    r = dict(spec=spec, instr=instr, date=str(date), contract=str(contract), dir=int(direction),
             entry=float(entry), exit=float(exit_px), pnl=float(pnl),
             atr=float(atr) if np.isfinite(atr) else None, atr_n=int(atr_n) if np.isfinite(atr_n) else 0,
             note=note)
    for k, m in (("R", 1.0), ("R15", 1.5), ("R20", 2.0)):
        r[k] = float((pnl - m * cost) / atr) if np.isfinite(atr) and atr > 0 else None
    return r


def es_events(b):
    rows = []
    if b is None:
        return rows
    st = session_table(b)
    for (c, key), day in b.groupby(["contract", "skey"]):
        if (c, key) not in st.index:
            continue
        atr, atr_n = st.loc[(c, key), "atr"], st.loc[(c, key), "atr_n"]
        keys = st.loc[c].index
        pos = keys.get_loc(key)
        prev_last = st.loc[(c, keys[pos - 1]), "last"] if pos > 0 else np.nan
        o930, o950, b955 = _bar(day, 930), _bar(day, 1550), _bar(day, 1555)
        # bars from 16:00 belong to the NEXT session key (skey = ts + 8h), so the post-close
        # prints are looked up by calendar date on the same contract
        post = b[(b.contract == c) & (b.index.date == key)]
        b1600, b1610 = _bar(post, 1600), _bar(post, 1610)
        # F1: third-Friday gap fade 09:30 -> 10:00
        if third_friday(key) and o930 is not None and np.isfinite(prev_last):
            x = _bar(day, 955)
            gap = o930.open - prev_last
            if x is not None and gap != 0:
                rows.append(_row("F1", "ES", key, c, -np.sign(gap), o930.open, x.close, atr, atr_n,
                                 f"gap {gap:+.2f}"))
        # F2: MOC drift 15:50 -> 16:00 signed by the day return at 15:50
        if o930 is not None and o950 is not None and b955 is not None:
            dr = o950.open - o930.open
            if dr != 0:
                rows.append(_row("F2", "ES", key, c, np.sign(dr), o950.open, b955.close, atr, atr_n,
                                 f"dayret {dr:+.2f}"))
        # F3: cash close -> settlement 16:00 -> 16:15, reversal of the 15:50 -> 16:00 push
        if o950 is not None and b955 is not None and b1600 is not None and b1610 is not None:
            push = b955.close - o950.open
            if push != 0:
                rows.append(_row("F3", "ES", key, c, -np.sign(push), b1600.open, b1610.close, atr, atr_n,
                                 f"push {push:+.2f}"))
    return rows


def gc_events(b):
    rows = []
    if b is None:
        return rows
    st = session_table(b)
    for (c, key), day in b.groupby(["contract", "skey"]):
        # the Monday session key holds Sunday 18:00 -> Monday 15:55
        if key.weekday() != 0:
            continue
        sun = day[(day.dow == 6) & (day.hm == 1800)]
        if len(sun) != 1:
            continue
        cb = b[(b.contract == c) & (b.index < sun.index[0])]
        if not len(cb):
            continue
        fri = cb.iloc[-1]
        if fri.name.weekday() != 4 or fri.hm != 1655:
            continue                                      # Friday's last print must be the 16:55 bar
        e = day[(day.dow == 6) & (day.hm == 1805)]
        x = day[(day.dow == 0) & (day.hm == 255)]
        if len(e) != 1 or len(x) != 1:
            continue
        gap = sun.open.iloc[0] - fri.close
        if gap == 0:
            continue
        atr = st.loc[(c, key), "atr"] if (c, key) in st.index else np.nan
        atr_n = st.loc[(c, key), "atr_n"] if (c, key) in st.index else 0
        rows.append(_row("F4", "GC", key, c, -np.sign(gap), e.open.iloc[0], x.close.iloc[0], atr, atr_n,
                         f"gap {gap:+.2f}"))
    return rows


def hsi_events(data_dir):
    rows = []
    files = sorted(glob.glob(os.path.join(data_dir, "hsi_fut_15m_*.json")))
    if not files:
        return rows
    parts = []
    for f in files:
        d = json.load(open(f))
        b = pd.DataFrame({k: pd.to_numeric(d[k]) for k in ("open", "high", "low", "close")},
                         index=pd.to_datetime(d["time"], utc=True))
        b["contract"] = d.get("contract", os.path.basename(f))
        parts.append(b)
    H = pd.concat(parts).sort_index(kind="stable")
    H = H[~H.index.duplicated(keep="last")]
    Hp, atr14 = M._prepare(H[["open", "high", "low", "close"]])
    Hp["contract"] = H.contract.reindex(Hp.index)
    for d, day in Hp.groupby("d"):
        o = day[day.hm == M.PRE_HM]
        w = day[day.hm == 815]
        if len(o) != 1 or len(w) != 1 or o.contract.iloc[0] != w.contract.iloc[0]:
            continue
        dr = w.open.iloc[0] - o.open.iloc[0]
        if dr == 0:
            continue
        a = atr14.get(d, np.nan)
        rows.append(_row("F5", "HSI", d, w.contract.iloc[0], np.sign(dr), w.open.iloc[0], w.close.iloc[0],
                         a, M.ATR_N if np.isfinite(a) else 0, f"dayret {dr:+.0f}"))
    return rows


# ----------------------------------------------------------------------------- scoring
def _stats(x):
    x = np.asarray([v for v in x if v is not None], float)
    if len(x) == 0:
        return dict(n=0)
    m = len(x) // 2
    return dict(n=int(len(x)), mean=float(x.mean()), wr=float((x > 0).mean()),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 1e-12 * max(1.0, abs(x.mean())) else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))] if m >= 1 else None)


def score(rows):
    out = {}
    for spec in ("F1", "F2", "F3", "F4", "F5"):
        rr = [r for r in rows if r["spec"] == spec]
        s = dict(n=len(rr), pts=_stats([r["pnl"] for r in rr]),
                 x1=_stats([r["R"] for r in rr]), x15=_stats([r["R15"] for r in rr]), x2=_stats([r["R20"] for r in rr]),
                 first=min((r["date"] for r in rr), default=None), last=max((r["date"] for r in rr), default=None))
        x1, x2 = s["x1"], s["x2"]
        s["bar"] = bool(x1.get("n", 0) >= 40 and (x1.get("mean") or -1) > 0 and (x1.get("t") or -9) >= 2
                        and x1.get("halves") == [1.0, 1.0] and (x2.get("mean") or -1) > 0)
        out[spec] = s
    return out


def run(data_dir, start=None):
    rows = es_events(load_5m(data_dir, "es")) + gc_events(load_5m(data_dir, "gc")) + hsi_events(data_dir)
    if start:
        rows = [r for r in rows if r["date"] >= start]
    rows.sort(key=lambda r: (r["spec"], r["date"]))
    return rows, score(rows)


def summary_lines(rows, sc):
    out = []
    for spec, s in sc.items():
        if s["n"] == 0:
            out.append(f"{spec}: no events yet"); continue
        p, x1 = s["pts"], s["x1"]
        line = (f"{spec}: n {s['n']} ({s['first']}..{s['last']}) mean {p['mean']:+.2f} pts WR {p['wr']*100:.0f}%")
        if p.get("t") is not None:
            line += f" t {p['t']:+.2f}"
        if x1.get("n"):
            line += f"; R x1 {x1['mean']:+.3f} (n {x1['n']}) x2 {s['x2'].get('mean', float('nan')):+.3f}"
        line += f"; bar {'MET' if s['bar'] else 'not met'} (needs n>=40, t>=2, [+,+], x2>0)"
        out.append(line)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "..", "data", "forward"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "results", "forward_intraday.json"))
    ap.add_argument("--start", default="2026-09-03", help="first session that counts (registration date + 1)")
    a = ap.parse_args()
    rows, sc = run(a.data, a.start)
    json.dump(dict(generated=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), start=a.start,
                   costs=COST, score=sc, events=rows), open(a.out, "w"), indent=1)
    for r in rows:
        print(f"  {r['spec']} {r['date']} {r['contract']:<6} dir {r['dir']:+d} {r['entry']:.2f} -> {r['exit']:.2f} "
              f"{r['pnl']:+.2f} pts  R {r['R'] if r['R'] is None else round(r['R'], 3)}  {r['note']}")
    for line in summary_lines(rows, sc):
        print(line)
    print(f"wrote {a.out}")
