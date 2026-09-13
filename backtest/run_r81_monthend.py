"""Attempt 59 (Round 81): month-end index duration extension in the 10-year Treasury.

Cells (selectable, 10y outright par-bond proxy from the DGS10 CMT; two-sided Bonferroni-2 floor 2.26):
  C1 EXTENSION LONG   T-1 close -> T close        (T = last business day of the month on the DGS10 calendar)
  C2 REVERSAL SHORT   T close   -> T+2 close
Gate per cell: net > 0, PF >= 1.15, own t >= 2.26, halves [+,+], positive at 2x (3 bp RT);
year-stratified event-minus-control differential > 0, t >= 2.26, halves [+,+] with NON-OVERLAPPING control
windows >= 3 bd from any month-end; placebo-clock max-stat over the other business-day-of-month ranks
T-10..T+10 (observed max over cells must beat all 20 placebo maxima); BLOCKING cross-section: the 30y
differential must exceed the 2y differential.
IS: month-ends 1990-01..2020-02 on series clipped at 2020-03-05; OOS: month-ends 2020-03.. sealed
(UNSEAL_OK=1 --unseal). Read-only: 2y/5y/30y analogs, quarter-end split, FOMC/auction-adjacent flags,
T-2->T and T->T+1 variants, mirrors, per-year, drift, era split. Outputs results/r81_monthend_{is,oos}.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fomc_dates import FOMC_DATES  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
SERIES_CUT = pd.Timestamp("2020-03-05")
IS_START, IS_END_MONTH = pd.Timestamp("1990-01-01"), pd.Period("2020-02", "M")
OOS_START_MONTH = pd.Period("2020-03", "M")
COST_BP = 3.0
T_FLOOR = 2.26
CELLS = {"C1_extension_long": (-1, 0, +1), "C2_reversal_short": (0, 2, -1)}
READ = {"T-2_long": (-2, 0, +1), "T+1_short": (0, 1, -1)}
TENORS = {"10y": ("fred_DGS10.csv", 10), "2y": ("fred_DGS2.csv", 2), "5y": ("UST05Y_daily_av.csv", 5), "30y": ("UST30Y_daily_av.csv", 30)}
FOMC = set(pd.to_datetime(FOMC_DATES).normalize())


def load_yield(tenor):
    f, _ = TENORS[tenor]
    d = pd.read_csv(os.path.join(HERE, "data", f)); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def auction_dates():
    n = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json"))))
    b = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_bond_auctions.json"))))
    return set(pd.to_datetime(pd.concat([n.auction_date, b.auction_date])).dt.normalize())


def mod_dur(y_pct, years):
    c = y_pct / 200.0; n = 2 * years
    if c <= 0: return years
    return (1 + c) / c * (1 - (1 + c) ** (-n)) / 2.0 / (1 + c)


def ret_bp(y, years, p0, p1):
    if p0 < 0 or p1 >= len(y) or p0 >= p1: return np.nan
    y0, y1 = y.iloc[p0], y.iloc[p1]; days = (y.index[p1] - y.index[p0]).days
    if days > (p1 - p0) + 5: return np.nan
    return -mod_dur(y0, years) * (y1 - y0) / 100.0 * 1e4 + y0 / 100.0 * days / 365.0 * 1e4


def month_end_positions(y, lo_month, hi_month):
    """position of the last business day (on the yield calendar) of each month in [lo_month, hi_month]."""
    per = y.index.to_period("M"); out = []
    for m in pd.period_range(lo_month, hi_month, freq="M"):
        pos = np.where(per == m)[0]
        if len(pos): out.append(int(pos[-1]))
    return out


def rows_for(y, years, pos_list, cells, tag):
    rows = []
    for p in pos_list:
        for cn, (a, b, s) in cells.items():
            r = ret_bp(y, years, p + a, p + b)
            if np.isnan(r): continue
            rows.append(dict(pos=p, date=y.index[p], tag=tag, cell=cn, sign=s, raw=r, gross=s * r, net=s * r - COST_BP,
                             net15=s * r - 1.5 * COST_BP, net2=s * r - 2 * COST_BP))
    return pd.DataFrame(rows)


def control_positions(y, ev_pos, a, b, excl=3):
    """non-overlapping tiling of anchors p whose window [p+a, p+b] lies entirely >= excl bd from every event position."""
    n = len(y); near = np.zeros(n, bool)
    for e in ev_pos: near[max(0, e - excl + 1):min(n, e + excl)] = True
    ok = ~near; cum = np.concatenate([[0], np.cumsum(ok)]); L = b - a
    out = []; p = max(0, -a)
    while p + b < n:
        if cum[p + b + 1] - cum[p + a] == L + 1: out.append(p); p += L
        else: p += 1
    return out


def stats(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 10: return dict(n=int(len(x)))
    m = len(x) // 2; w, l = x[x > 0], x[x <= 0]
    return dict(n=int(len(x)), mean_bp=float(x.mean()), wr=float((x > 0).mean()),
                pf=float(w.sum() / abs(l.sum())) if len(l) and l.sum() < 0 else float("inf"),
                t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 1e-12 else None,
                halves=[float(np.sign(x[:m].mean())), float(np.sign(x[m:].mean()))])


def strat_diff(ev, ct, col="gross", min_e=3, min_c=5):
    ev = ev.copy(); ct = ct.copy(); ev["yr"] = ev.date.dt.year; ct["yr"] = ct.date.dt.year
    num = den = var = 0.0; used = dropped = 0
    for yr, g in ev.groupby("yr"):
        c = ct[ct.yr == yr]
        if len(g) < min_e or len(c) < min_c: dropped += len(g); continue
        w = len(g); num += w * (g[col].mean() - c[col].mean()); den += w; used += w
        var += w * w * (g[col].var(ddof=1) / len(g) + c[col].var(ddof=1) / len(c))
    if den == 0: return dict(n_event=0)
    d = num / den; se = np.sqrt(var) / den
    return dict(n_event=int(used), n_control=int(len(ct)), dropped_events=int(dropped), diff_bp=float(d), se=float(se), t=float(d / se) if se > 0 else None)


def diff_halves(ev, ct):
    ev = ev.sort_values("date"); m = len(ev) // 2; cut = ev.date.iloc[m]; out = []
    for e, c in ((ev.iloc[:m], ct[ct.date < cut]), (ev.iloc[m:], ct[ct.date >= cut])):
        out.append(float(np.sign(strat_diff(e, c).get("diff_bp", 0.0))))
    return out


def evaluate(y, years, ev_pos, cells, full):
    e = rows_for(y, years, ev_pos, cells, "event"); out = {"n_events": int(len(ev_pos))}
    if len(e) == 0: return out, e
    out["span"] = [str(e.date.min().date()), str(e.date.max().date())]
    auc = auction_dates()
    for cn, (a, b, s) in cells.items():
        c = rows_for(y, years, control_positions(y, ev_pos, a, b), {cn: (a, b, s)}, "control"); g = e[e.cell == cn]
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), control_gross=stats(c.gross), n_control=int(len(c)),
                       strat_diff=strat_diff(g, c), diff_halves=diff_halves(g, c))
        if full:
            q = g.date.dt.month.isin([3, 6, 9, 12])
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           quarter_end=dict(n=int(q.sum()), strat_diff=strat_diff(g[q], c)), other_month_end=dict(n=int((~q).sum()), strat_diff=strat_diff(g[~q], c)),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           by_era_diff={era: strat_diff(g[m_], c[m_c]) for era, m_, m_c in (
                               ("1990-2008", g.date < "2009-01-01", c.date < "2009-01-01"), ("2009+", g.date >= "2009-01-01", c.date >= "2009-01-01"))},
                           fomc_adjacent_n=int(g.date.map(lambda d: any(abs((d - f).days) <= 1 for f in FOMC)).sum()),
                           auction_adjacent_n=int(g.date.map(lambda d: any(abs((d - x).days) <= 1 for x in auc)).sum()))
    return out, e


def placebo_maxstat(y, years, ev_pos, obs_max):
    """the same two cells anchored at every other business-day-of-month rank T-10..T+10 (20 placebo clocks)."""
    n = len(y); maxima = []
    for k in [k for k in range(-10, 11) if k != 0]:
        sh = [p + k for p in ev_pos if 0 <= p + k < n]
        e = rows_for(y, years, sh, CELLS, "placebo"); vals = []
        for cn, (a, b, s) in CELLS.items():
            c = rows_for(y, years, control_positions(y, sh, a, b), {cn: (a, b, s)}, "ctrl")
            vals.append(abs(strat_diff(e[e.cell == cn], c).get("t") or 0.0))
        maxima.append(max(vals))
    maxima = np.array(maxima)
    return dict(placebo_clocks=int(len(maxima)), obs_max_t=float(obs_max), placebo_max_t=[round(float(v), 2) for v in maxima],
                p=float((np.sum(maxima >= obs_max) + 1) / (len(maxima) + 1)))


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    series = {}
    for tenor in TENORS:
        y = load_yield(tenor)
        series[tenor] = y[y.index <= SERIES_CUT] if not UNSEAL else y[y.index >= pd.Timestamp("2020-01-01")]
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r81_monthend_is.json")))
        cleared = [c for c, ok in isr["verdict"].items() if ok]
        if not cleared: raise SystemExit("no cell cleared IS; holdout stays sealed")
    else:
        cleared = list(CELLS)
    lo_m, hi_m = (OOS_START_MONTH, pd.Period("2026-08", "M")) if UNSEAL else (pd.Period("1990-01", "M"), IS_END_MONTH)
    cells = dict(CELLS); cells.update(READ)
    y10 = series["10y"]; ev10 = month_end_positions(y10, lo_m, hi_m)
    if not UNSEAL: assert y10.index[max(ev10) + 2] <= SERIES_CUT
    out, e = evaluate(y10, 10, ev10, cells, full=True)
    allpos = list(range(1, len(y10) - 2))
    out["unconditional_1d_long"] = stats(rows_for(y10, 10, allpos[::1], {"u": (-1, 0, +1)}, "u").gross)
    out["unconditional_2d_long"] = stats(rows_for(y10, 10, allpos[::2], {"u": (0, 2, +1)}, "u").gross)
    res["10y"] = out
    print(f"=== 10y ({'OOS' if UNSEAL else 'IS'}) month-ends {out['n_events']} {out.get('span')} ===")
    for cn in cells:
        v = out[cn]
        print(f"  {cn:18s} net {json.dumps(v['x1'], default=float)}\n      strat_diff {json.dumps(v['strat_diff'], default=float)} diff_halves {v['diff_halves']} n_control {v['n_control']} control_gross {v['control_gross'].get('mean_bp', float('nan')):+.2f}")
        if "x2" in v:
            print(f"      x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f} qtr {json.dumps(v['quarter_end']['strat_diff'], default=float)} other {json.dumps(v['other_month_end']['strat_diff'], default=float)}\n      era {json.dumps(v['by_era_diff'], default=float)} fomc_adj {v['fomc_adjacent_n']} auction_adj {v['auction_adjacent_n']}\n      per-year {v['per_year_net']}")
    print("  unconditional 1d long:", out["unconditional_1d_long"], "\n  unconditional 2d long:", out["unconditional_2d_long"])
    cross = {}
    for tenor, (_, yrs) in TENORS.items():
        if tenor == "10y": continue
        yt = series[tenor]; evt = month_end_positions(yt, lo_m, hi_m)
        o, _ = evaluate(yt, yrs, evt, CELLS, full=False); cross[tenor] = {cn: dict(x1=o[cn]["x1"], strat_diff=o[cn]["strat_diff"]) for cn in CELLS if cn in o}
        print(f"  read-only {tenor}: " + "; ".join(f"{cn} net {o[cn]['x1'].get('mean_bp', float('nan')):+.1f} (t {o[cn]['x1'].get('t') or 0:+.2f}) diff {o[cn]['strat_diff'].get('diff_bp', float('nan')):+.1f} (t {o[cn]['strat_diff'].get('t') or 0:+.2f})" for cn in CELLS if cn in o))
    res["cross_section"] = cross
    if not UNSEAL:
        obs = max(abs(out[cn]["strat_diff"].get("t") or 0.0) for cn in CELLS)
        res["maxstat"] = placebo_maxstat(y10, 10, ev10, obs); print("  placebo-clock maxstat:", res["maxstat"])
    passes = {}
    for cn in cleared:
        v = out[cn]; s, x2, sd = v["x1"], v["x2"], v["strat_diff"]; floor = 2.0 if UNSEAL else T_FLOOR
        own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
        p_ok = True if UNSEAL else res["maxstat"]["p"] < 0.05
        x15_ok = v["x15"].get("mean_bp", -1) > 0 if UNSEAL else True
        d30 = cross.get("30y", {}).get(cn, {}).get("strat_diff", {}).get("diff_bp", -1e9); d2 = cross.get("2y", {}).get(cn, {}).get("strat_diff", {}).get("diff_bp", 1e9)
        cross_ok = d30 > d2
        passes[cn] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
                          and x2.get("mean_bp", -1) > 0 and x15_ok and sd.get("diff_bp", -1) > 0 and d_t >= floor and v["diff_halves"] == [1.0, 1.0] and p_ok and cross_ok)
    res["verdict"] = passes
    print(f"\nATTEMPT 59 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r81_monthend_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
