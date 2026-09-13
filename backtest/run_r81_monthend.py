"""Attempt 59 v2 (Round 81, RE-REGISTERED): month-end index duration extension in the 10-year Treasury.

Selectable cell (one; house floor t >= 2.0):
  C1 EXTENSION LONG   T-3 close -> T close   (T = last business day of the month on the DGS10 calendar)
Read-only: T-1 -> T long, T -> T+2 short (the conjectured reversal), 2y/5y/30y analogs, quarter-end split,
auction-inside-window and FOMC-inside-window (2013+) splits, Dec-31 early-close flag, S&P 500 same-window
return (from the 5m CFD frame where available), mirrors, per-year, era split, unconditional drift.
Gate: net > 0 (full return incl. carry), PF >= 1.15, own t >= 2.0, halves [+,+], positive at 2x (3 bp RT);
year-stratified event-minus-control differential on the -ModD*dy PRICE COMPONENT > 0, t >= 2.0, halves [+,+],
non-overlapping control windows every day >= 5 bd from EVERY month-end in the loaded series, control universe
clipped to the event span; placebo-clock max-stat (k in +-4..+-13, 20 clocks, placebo controls exclude the true
month-ends; the cell's SIGNED t must beat all 20 placebo maxima); BLOCKING: the 30-year's price-component
differential in the same window > 0 (2002-02..2006-02 excluded).
IS: month-ends 1990-01..2019-04 on series clipped at 2019-05-06; OOS: month-ends 2019-05.. sealed
(UNSEAL_OK=1 --unseal); OOS bar = house bar + differential > 0 with t >= 2. Outputs results/r81_monthend_{is,oos}.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fomc_dates import FOMC_DATES  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
SERIES_CUT = pd.Timestamp("2019-05-06")
IS_MONTHS = (pd.Period("1990-01", "M"), pd.Period("2019-04", "M"))
OOS_MONTHS = (pd.Period("2019-05", "M"), pd.Period("2026-08", "M"))
COST_BP = 3.0
T_FLOOR = 2.0
CELL = {"C1_extension_long": (-3, 0, +1)}
READ = {"T-1_long": (-1, 0, +1), "T+2_reversal_short": (0, 2, -1)}
TENORS = {"10y": ("fred_DGS10.csv", 10), "2y": ("fred_DGS2.csv", 2), "5y": ("UST05Y_daily_av.csv", 5), "30y": ("UST30Y_daily_av.csv", 30)}
FOMC = set(pd.to_datetime(FOMC_DATES).normalize())
EXCL = 5
SUSP = (pd.Timestamp("2002-02-01"), pd.Timestamp("2006-02-28"))          # 30y composite era, excluded from the blocking leg


def load_yield(tenor):
    f, _ = TENORS[tenor]
    d = pd.read_csv(os.path.join(HERE, "data", f)); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def auction_dates():
    n = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json"))))
    b = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_bond_auctions.json"))))
    return set(pd.to_datetime(pd.concat([n.auction_date, b.auction_date])).dt.normalize())


def spx_daily():
    try:
        d = pd.read_csv(os.path.join(HERE, "data", "SPX_5m.csv"))
        tcol = [c for c in d.columns if c.lower() in ("ts", "time", "date", "datetime", "timestamp")][0]
        d[tcol] = pd.to_datetime(d[tcol]); d["day"] = d[tcol].dt.normalize()
        return d.groupby("day").close.last()
    except Exception:
        return None


def mod_dur(y_pct, years):
    c = y_pct / 200.0; n = 2 * years
    if c <= 0: return years
    return (1 + c) / c * (1 - (1 + c) ** (-n)) / 2.0 / (1 + c)


def ret_parts(y, years, p0, p1):
    """(price component bp, carry bp) of a long from close p0 to close p1; nan if invalid."""
    if p0 < 0 or p1 >= len(y) or p0 >= p1: return np.nan, np.nan
    y0, y1 = y.iloc[p0], y.iloc[p1]; days = (y.index[p1] - y.index[p0]).days
    if days > (p1 - p0) + 5: return np.nan, np.nan
    return -mod_dur(y0, years) * (y1 - y0) / 100.0 * 1e4, y0 / 100.0 * days / 365.0 * 1e4


def month_end_positions(y, lo_m, hi_m):
    per = y.index.to_period("M"); out = []
    for m in pd.period_range(lo_m, hi_m, freq="M"):
        pos = np.where(per == m)[0]
        if len(pos): out.append(int(pos[-1]))
    return out


def rows_for(y, years, pos_list, cells, tag):
    rows = []
    for p in pos_list:
        for cn, (a, b, s) in cells.items():
            px, cy = ret_parts(y, years, p + a, p + b)
            if np.isnan(px): continue
            r = px + cy
            rows.append(dict(pos=p, date=y.index[p], tag=tag, cell=cn, sign=s, price=s * px, carry=s * cy, gross=s * r,
                             net=s * r - COST_BP, net15=s * r - 1.5 * COST_BP, net2=s * r - 2 * COST_BP))
    return pd.DataFrame(rows)


def control_positions(y, excl_pos, a, b, lo, hi):
    """non-overlapping tiling of anchors p in [lo, hi] whose window [p+a, p+b] lies entirely >= EXCL bd from every excluded position."""
    n = len(y); near = np.zeros(n, bool)
    for e in excl_pos: near[max(0, e - EXCL + 1):min(n, e + EXCL)] = True
    ok = ~near; cum = np.concatenate([[0], np.cumsum(ok)]); L = b - a
    out = []; p = max(lo, -a)
    while p + b < n and p <= hi:
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


def strat_diff(ev, ct, col="price", min_e=3, min_c=5):
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


def diff_halves(ev, ct, col="price"):
    ev = ev.sort_values("date"); m = len(ev) // 2; cut = ev.date.iloc[m]; out = []
    for e, c in ((ev.iloc[:m], ct[ct.date < cut]), (ev.iloc[m:], ct[ct.date >= cut])):
        out.append(float(np.sign(strat_diff(e, c, col).get("diff_bp", 0.0))))
    return out


def evaluate(y, years, ev_pos, all_me, cells, full, extra=None):
    e = rows_for(y, years, ev_pos, cells, "event"); out = {"n_events": int(len(ev_pos))}
    if len(e) == 0: return out, e
    out["span"] = [str(e.date.min().date()), str(e.date.max().date())]
    lo, hi = min(ev_pos), max(ev_pos)
    for cn, (a, b, s) in cells.items():
        c = rows_for(y, years, control_positions(y, all_me, a, b, lo, hi), {cn: (a, b, s)}, "control"); g = e[e.cell == cn]
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), price_component=stats(g.price), carry=stats(g.carry),
                       control_price=stats(c.price), control_carry=stats(c.carry), n_control=int(len(c)),
                       strat_diff=strat_diff(g, c), diff_halves=diff_halves(g, c), strat_diff_gross=strat_diff(g, c, "gross"))
        if full:
            auc, spx = extra["auc"], extra["spx"]
            dates = list(y.index)
            inwin = g.pos.map(lambda p: any(dates[q] in auc for q in range(p + a + 1, p + b + 1)))          # auction on a day inside the window
            fomc_in = g.pos.map(lambda p: any(dates[q] in FOMC for q in range(p + a + 1, p + b + 1)))
            post2013 = g.date >= "2013-01-01"; q = g.date.dt.month.isin([3, 6, 9, 12]); dec = g.date.dt.month == 12
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           quarter_end=dict(n=int(q.sum()), strat_diff=strat_diff(g[q], c)), other_month_end=dict(n=int((~q).sum()), strat_diff=strat_diff(g[~q], c)),
                           auction_in_window=dict(n=int(inwin.sum()), strat_diff=strat_diff(g[inwin], c)), no_auction_in_window=dict(n=int((~inwin).sum()), strat_diff=strat_diff(g[~inwin], c)),
                           fomc_in_window_2013plus=dict(n=int((fomc_in & post2013).sum()), of=int(post2013.sum()), strat_diff=strat_diff(g[fomc_in & post2013], c[c.date >= "2013-01-01"])),
                           no_fomc_2013plus=dict(n=int((~fomc_in & post2013).sum()), strat_diff=strat_diff(g[~fomc_in & post2013], c[c.date >= "2013-01-01"])),
                           dec31_early_close=dict(n=int(dec.sum()), gross=stats(g[dec].gross)),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           by_era_diff={era: strat_diff(g[m_], c[m_c]) for era, m_, m_c in (
                               ("1990-2008", g.date < "2009-01-01", c.date < "2009-01-01"), ("2009+", g.date >= "2009-01-01", c.date >= "2009-01-01"))})
            if spx is not None:
                sp = []
                for p in g.pos:
                    d0, d1 = dates[p + a], dates[p + b]
                    if d0 in spx.index and d1 in spx.index: sp.append(np.log(spx[d1] / spx[d0]) * 1e4)
                out[cn]["spx_same_window_bp"] = stats(sp)
    return out, e


def placebo_maxima(y, years, ev_pos, all_me, lo, hi):
    n = len(y); maxima = []
    for k in [k for k in range(-13, 14) if abs(k) >= 4]:
        sh = [p + k for p in ev_pos if 0 <= p + k < n]
        e = rows_for(y, years, sh, CELL, "placebo"); vals = []
        for cn, (a, b, s) in CELL.items():
            c = rows_for(y, years, control_positions(y, sorted(set(all_me) | set(sh)), a, b, lo, hi), {cn: (a, b, s)}, "ctrl")
            vals.append(abs(strat_diff(e[e.cell == cn], c).get("t") or 0.0))
        maxima.append(max(vals))
    return np.array(maxima)


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    series = {}
    for tenor in TENORS:
        y = load_yield(tenor)
        series[tenor] = y[y.index <= SERIES_CUT] if not UNSEAL else y[y.index >= pd.Timestamp("2018-06-01")]
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r81_monthend_is.json")))
        if not isr["verdict"].get("C1_extension_long"): raise SystemExit("cell did not clear IS; holdout stays sealed")
    lo_m, hi_m = OOS_MONTHS if UNSEAL else IS_MONTHS
    cells = dict(CELL); cells.update(READ)
    y10 = series["10y"]; ev10 = month_end_positions(y10, lo_m, hi_m)
    all_me10 = month_end_positions(y10, y10.index[0].to_period("M"), y10.index[-1].to_period("M"))
    if not UNSEAL: assert y10.index[max(ev10) + 2] <= SERIES_CUT
    extra = {"auc": auction_dates(), "spx": spx_daily()}
    out, e = evaluate(y10, 10, ev10, all_me10, cells, full=True, extra=extra)
    lo, hi = min(ev10), max(ev10)
    out["unconditional_3d_long_price"] = stats(rows_for(y10, 10, list(range(lo, hi, 3)), {"u": (0, 3, +1)}, "u").price)
    res["10y"] = out
    print(f"=== 10y ({'OOS' if UNSEAL else 'IS'}) month-ends {out['n_events']} {out.get('span')} ===")
    for cn in cells:
        v = out[cn]
        print(f"  {cn:20s} net {json.dumps(v['x1'], default=float)}\n      price {v['price_component'].get('mean_bp', float('nan')):+.1f} carry {v['carry'].get('mean_bp', float('nan')):+.2f} | control price {v['control_price'].get('mean_bp', float('nan')):+.1f} carry {v['control_carry'].get('mean_bp', float('nan')):+.2f} n_control {v['n_control']}\n      strat_diff(price) {json.dumps(v['strat_diff'], default=float)} diff_halves {v['diff_halves']}")
        if "x2" in v:
            print(f"      x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f}\n      qtr {json.dumps(v['quarter_end']['strat_diff'], default=float)}\n      other {json.dumps(v['other_month_end']['strat_diff'], default=float)}\n      auction_in {v['auction_in_window']['n']} {json.dumps(v['auction_in_window']['strat_diff'], default=float)}\n      no_auction {v['no_auction_in_window']['n']} {json.dumps(v['no_auction_in_window']['strat_diff'], default=float)}\n      fomc_in(2013+) {v['fomc_in_window_2013plus']['n']}/{v['fomc_in_window_2013plus']['of']} {json.dumps(v['fomc_in_window_2013plus']['strat_diff'], default=float)} no_fomc {json.dumps(v['no_fomc_2013plus']['strat_diff'], default=float)}\n      era {json.dumps(v['by_era_diff'], default=float)}\n      dec31 {json.dumps(v['dec31_early_close'], default=float)} spx_same_window {json.dumps(v.get('spx_same_window_bp'), default=float)}\n      per-year {v['per_year_net']}")
    print("  unconditional 3d long price:", out["unconditional_3d_long_price"])
    cross = {}
    for tenor, (_, yrs) in TENORS.items():
        if tenor == "10y": continue
        yt = series[tenor]; evt = month_end_positions(yt, lo_m, hi_m); allt = month_end_positions(yt, yt.index[0].to_period("M"), yt.index[-1].to_period("M"))
        if tenor == "30y": evt = [p for p in evt if not (SUSP[0] <= yt.index[p] <= SUSP[1])]
        o, _ = evaluate(yt, yrs, evt, allt, CELL, full=False)
        cross[tenor] = {cn: dict(n=o["n_events"], x1=o[cn]["x1"], strat_diff=o[cn]["strat_diff"], roll_at_month_end=(tenor in ("2y", "5y"))) for cn in CELL if cn in o}
        print(f"  read-only {tenor} (n {o['n_events']}): " + "; ".join(f"{cn} net {o[cn]['x1'].get('mean_bp', float('nan')):+.1f} (t {o[cn]['x1'].get('t') or 0:+.2f}) price-diff {o[cn]['strat_diff'].get('diff_bp', float('nan')):+.1f} (t {o[cn]['strat_diff'].get('t') or 0:+.2f})" for cn in CELL if cn in o))
    res["cross_section"] = cross
    cn = "C1_extension_long"; v = out[cn]; s, sd = v["x1"], v["strat_diff"]
    if not UNSEAL:
        mx = placebo_maxima(y10, 10, ev10, all_me10, lo, hi); t_obs = sd.get("t") or -9
        res["maxstat"] = dict(placebo_clocks=int(len(mx)), obs_t=float(t_obs), placebo_max_t=[round(float(x), 2) for x in mx], p=float((np.sum(mx >= t_obs) + 1) / (len(mx) + 1)))
        print("  placebo-clock maxstat:", res["maxstat"])
    floor = T_FLOOR
    own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
    base = s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0] and v["x2"].get("mean_bp", -1) > 0 and sd.get("diff_bp", -1) > 0 and d_t >= floor
    if UNSEAL:
        ok = base and v["x15"].get("mean_bp", -1) > 0
    else:
        d30 = cross.get("30y", {}).get(cn, {}).get("strat_diff", {}).get("diff_bp", -1)
        ok = base and v["diff_halves"] == [1.0, 1.0] and res["maxstat"]["p"] < 0.05 and d30 > 0
    res["verdict"] = {cn: bool(ok)}
    print(f"\nATTEMPT 59 {'OOS' if UNSEAL else 'IS'} VERDICT: {res['verdict']}")
    json.dump(res, open(os.path.join(HERE, "results", f"r81_monthend_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
