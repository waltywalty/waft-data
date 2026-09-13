"""Attempt 58 (Round 80): Treasury auction cycle on the 10-year itself (Lou, Yan & Zhang 2013).

Cells (selectable, 10-year auctions, Bonferroni 2 -> t floor 2.24):
  C1 RECOVERY LONG    T close -> T+5 close
  C2 CONCESSION SHORT T-5 close -> T close
Price proxy: par 10y semiannual bond implied by the FRED DGS10 constant-maturity yield,
r_bp = -ModD(y0) * dy * 1e4 + carry (y0 * days/365 * 1e4); cost 3 bp RT, 1.5x / 2x.
Gate: event net > 0, PF >= 1.15, own t >= 2.24, halves [+,+], positive at 2x; event-minus-control
differential > 0, Welch t >= 2.24, diff halves [+,+]; calendar-shift max-stat p < 0.05.
IS = 10y auctions 1990-01-01..2020-02-12; OOS = 2020-02-13.. sealed (UNSEAL_OK=1 --unseal).
Read-only: T+-2 / T+-10 windows, new-issue vs reopening, 2y/5y/30y analogs, FOMC-adjacent exclusion,
mirrors, per-year, drift. Outputs results/r80_auction_{is,oos}.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fomc_dates import FOMC_DATES  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
IS_START, IS_END = pd.Timestamp("1990-01-01"), pd.Timestamp("2020-02-12")
COST_BP = 3.0
T_FLOOR = 2.24
CELLS = {"C1_recovery_long": (0, 5, +1), "C2_concession_short": (-5, 0, -1)}
READ = {"T-2_short": (-2, 0, -1), "T+2_long": (0, 2, +1), "T-10_short": (-10, 0, -1), "T+10_long": (0, 10, +1)}
RNG = np.random.default_rng(80)
FOMC = set(pd.to_datetime(FOMC_DATES).normalize())


def load_yield(tenor):
    if tenor == "10y":
        d = pd.read_csv(os.path.join(HERE, "data", "fred_DGS10.csv")); d.columns = ["date", "y"]
    elif tenor == "2y":
        d = pd.read_csv(os.path.join(HERE, "data", "fred_DGS2.csv")); d.columns = ["date", "y"]
    else:
        d = pd.read_csv(os.path.join(HERE, "data", f"UST{'30' if tenor == '30y' else '05'}Y_daily_av.csv")); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    d = d.dropna().sort_values("date").drop_duplicates("date").set_index("date")
    return d.y


def auctions(tenor):
    n = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json"))))
    b = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_bond_auctions.json"))))
    if tenor == "10y": a = n[n.term.str.startswith(("10-Year", "9-Year"))]
    elif tenor == "2y": a = n[n.term.str.startswith(("2-Year", "1-Year 1"))]
    elif tenor == "5y": a = n[n.term.str.startswith(("5-Year", "4-Year 1"))]
    else: a = b[b.term.str.startswith(("30-Year", "29-Year"))]
    a = a.assign(date=pd.to_datetime(a.auction_date).dt.normalize(), reopen=(a.reopening == "Yes"))
    return a[["date", "reopen"]].drop_duplicates("date").sort_values("date").reset_index(drop=True)


def mod_dur(y_pct, years):
    c = y_pct / 200.0; n = 2 * years
    if c <= 0: return years
    mac_half = (1 + c) / c * (1 - (1 + c) ** (-n))
    return mac_half / 2.0 / (1 + c)


def window_return(y, pos0, pos1, years):
    """bp return of a long par bond from close index pos0 to close index pos1 on the yield calendar."""
    if pos0 < 0 or pos1 >= len(y) or pos0 >= pos1: return np.nan
    y0, y1 = y.iloc[pos0], y.iloc[pos1]; days = (y.index[pos1] - y.index[pos0]).days
    if days > 3 * (pos1 - pos0) + 4: return np.nan          # gap in the series
    return -mod_dur(y0, years) * (y1 - y0) / 100.0 * 1e4 + y0 / 100.0 * days / 365.0 * 1e4


def cell_rows(y, dates, cells, years, tag):
    idx = {d: i for i, d in enumerate(y.index)}
    rows = []
    for d in dates:
        i = idx.get(d)
        if i is None:                                       # auction on a non-yield day (holiday print) -> next yield day
            nxt = y.index[y.index >= d]
            if len(nxt) == 0 or (nxt[0] - d).days > 3: continue
            i = idx[nxt[0]]
        for cn, (a, b, s) in cells.items():
            r = window_return(y, i + a, i + b, years)
            if np.isnan(r): continue
            rows.append(dict(date=d, tag=tag, cell=cn, sign=s, raw=r, gross=s * r, net=s * r - COST_BP,
                             net15=s * r - 1.5 * COST_BP, net2=s * r - 2 * COST_BP))
    return pd.DataFrame(rows)


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10: return dict(n=int(len(x)))
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
    ev = ev.sort_values("date"); m = len(ev) // 2; cut = ev.date.iloc[m]; out = []
    for e, c in ((ev.iloc[:m], ct[ct.date < cut]), (ev.iloc[m:], ct[ct.date >= cut])):
        out.append(float(np.sign(e.gross.mean() - c.gross.mean())) if len(e) and len(c) else 0.0)
    return out


def control_dates(y, ev_dates, lo, hi):
    """business days (on the yield calendar) at least 6 business days from every event date, inside [lo, hi]."""
    pos = np.array(sorted({i for i, d in enumerate(y.index) if lo <= d <= hi}))
    ev_pos = np.array([y.index.get_indexer([d], method="bfill")[0] for d in ev_dates]); ev_pos = ev_pos[ev_pos >= 0]
    near = np.zeros(len(y), bool)
    for p in ev_pos: near[max(0, p - 5):p + 6] = True
    return [y.index[p] for p in pos if not near[p]]


def run_block(y, ev, lo, hi, years, tag, with_read=True):
    ev = ev[(ev.date >= lo) & (ev.date <= hi)]
    cells = dict(CELLS); cells.update(READ if with_read else {})
    e = cell_rows(y, ev.date, cells, years, "event"); c = cell_rows(y, control_dates(y, ev.date, lo, hi), cells, years, "control")
    out = {"n_auctions": int(len(ev)), "span": [str(ev.date.min().date()), str(ev.date.max().date())], "n_control_days": int(c.date.nunique()) if len(c) else 0}
    for cn in cells:
        g = e[e.cell == cn]; ct = c[c.cell == cn]
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), control_gross=stats(ct.gross), vs_control=welch(g.gross, ct.gross), diff_halves=diff_halves(g, ct))
        if cn in CELLS:
            m = ev.set_index("date").reopen
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           new_issue_gross=stats(g[~g.date.map(m).fillna(False).astype(bool)].gross), reopening_gross=stats(g[g.date.map(m).fillna(False).astype(bool)].gross),
                           ex_fomc_adjacent_vs_control=welch(g[~g.date.map(lambda d: any(abs((d - f).days) <= 1 for f in FOMC if abs((d - f).days) <= 3))].gross, ct.gross) if tag == "10y" else None)
    return out, e, c


def maxstat(y, ev, lo, hi, years, obs, shifts=range(8, 121)):
    idx = {d: i for i, d in enumerate(y.index)}; n = len(y)
    ev = ev[(ev.date >= lo) & (ev.date <= hi)]
    pos = [idx.get(d, y.index.get_indexer([d], method="bfill")[0]) for d in ev.date]
    ctrl_all = cell_rows(y, control_dates(y, ev.date, lo, hi), CELLS, years, "control")
    mx = []
    for k in list(shifts) + [-k for k in shifts]:
        sh = [y.index[p + k] for p in pos if 0 <= p + k < n]
        e = cell_rows(y, sh, CELLS, years, "shift"); vals = []
        for cn in CELLS:
            vals.append(abs(welch(e[e.cell == cn].gross, ctrl_all[ctrl_all.cell == cn].gross).get("t", 0.0)))
        mx.append(max(vals))
    mx = np.array(mx)
    return dict(obs_max_t=obs, p=float((np.sum(mx >= obs) + 1) / (len(mx) + 1)), shifts=int(len(mx)))


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    lo, hi = (IS_END + pd.Timedelta(days=1), pd.Timestamp("2030-01-01")) if UNSEAL else (IS_START, IS_END)
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r80_auction_is.json")))
        cleared = [c for c, ok in isr["verdict"].items() if ok]
        if not cleared: raise SystemExit("no cell cleared IS; holdout stays sealed")
    y10 = load_yield("10y"); ev10 = auctions("10y")
    out, e, c = run_block(y10, ev10, lo, hi, 10, "10y")
    lr = np.log1p(0) ; drift5 = stats(cell_rows(y10, [d for d in y10.index if lo <= d <= hi][::5], {"any5": (0, 5, +1)}, 10, "all")["gross"])
    out["unconditional_5d_long_gross"] = drift5
    res["10y"] = out
    print(f"=== 10y ({'OOS' if UNSEAL else 'IS'}) {out['span']} auctions {out['n_auctions']} control days {out['n_control_days']} ===")
    for cn, v in out.items():
        if isinstance(v, dict) and "x1" in v:
            print(f"  {cn:20s} net {json.dumps(v['x1'], default=float)} vs_control {json.dumps(v['vs_control'], default=float)} diff_halves {v['diff_halves']}")
            if "per_year_net" in v: print(f"      x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f} new {v['new_issue_gross'].get('mean_bp', float('nan')):+.1f} reopen {v['reopening_gross'].get('mean_bp', float('nan')):+.1f} per-year {v['per_year_net']}")
    print("  unconditional 5d long gross:", drift5)
    if not UNSEAL:
        obs = max(abs(out[cn]["vs_control"].get("t", 0.0)) for cn in CELLS)
        res["maxstat"] = maxstat(y10, ev10, lo, hi, 10, obs); print("  maxstat:", res["maxstat"])
        for tenor, yrs in (("2y", 2), ("5y", 5), ("30y", 30)):
            try:
                o2, _, _ = run_block(load_yield(tenor), auctions(tenor), lo, hi, yrs, tenor, with_read=False)
                res[f"readonly_{tenor}"] = {k: (dict(x1=v["x1"], vs_control=v["vs_control"]) if isinstance(v, dict) and "x1" in v else v) for k, v in o2.items()}
                print(f"  read-only {tenor}: " + "; ".join(f"{cn} net {o2[cn]['x1'].get('mean_bp', float('nan')):+.1f} (t {o2[cn]['x1'].get('t') or 0:+.2f}) diff {o2[cn]['vs_control'].get('diff_bp', float('nan')):+.1f} (t {o2[cn]['vs_control'].get('t') or 0:+.2f})" for cn in CELLS))
            except Exception as ex:
                print(f"  read-only {tenor}: unavailable ({ex})")
    passes = {}
    for cn in (cleared if UNSEAL else CELLS):
        v = out[cn]; s, x2, vc = v["x1"], v["x2"], v["vs_control"]; floor = 2.0 if UNSEAL else T_FLOOR
        own_t = s.get("t") if s.get("t") is not None else -9; d_t = vc.get("t") if vc.get("t") is not None else -9
        p_ok = True if UNSEAL else res["maxstat"]["p"] < 0.05
        x15_ok = v["x15"].get("mean_bp", -1) > 0 if UNSEAL else True
        passes[cn] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
                          and x2.get("mean_bp", -1) > 0 and x15_ok and vc.get("diff_bp", -1) > 0 and d_t >= floor and v["diff_halves"] == [1.0, 1.0] and p_ok)
    res["verdict"] = passes
    print(f"\nATTEMPT 58 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r80_auction_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
