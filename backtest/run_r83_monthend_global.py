"""Attempt 60 (Round 83): out-of-market replication of the month-end index-extension long (attempt 59) on
German, UK and Japanese 10-year government bonds, with the US 10-year as a fidelity anchor.

Cell per market (selectable; two-sided Bonferroni-3 floor t >= 2.39): C1 EXTENSION LONG, close of T-3 -> month-end
close T on the market's own yield calendar. Proxy: par 10y bond, return = -ModD(y0)*dy + carry, semi-annual coupon
for US/UK/JP, annual for DE (Bunds); cost 3 bp RT, 1.5x / 2x. Gate per market as attempt 59 v2: net > 0, PF >= 1.15, own t >=
floor, halves [+,+], positive at 2x; year-stratified event-minus-control differential on the price component > 0,
t >= floor, halves [+,+], non-overlapping controls >= 5 bd from every month-end; placebo-clock max-stat (k in
+-4..+-13, 20 clocks, controls exclude true month-ends; signed t must beat all 20).
IS/OOS per market: the last 20% of month-ends are sealed (cut fixed from the series span at run time and printed);
OOS runs only with UNSEAL_OK=1 --unseal and only for markets that cleared IS; the US anchor uses attempt 59's own
cut (IS 1990-01..2019-04) and is never a selectable cell here.
Read-only: T-1 -> T, T -> T+2 (reversal), quarter-end vs other, era split at 2009, per-year, pooled three-market
differential. Outputs results/r83_monthend_global_{is,oos}.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from run_r81_monthend import month_end_positions, control_positions, stats, strat_diff, diff_halves  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
COST_BP = 3.0
T_FLOOR_IS, T_FLOOR_OOS = 2.39, 2.0
HOLDOUT = 0.20
MARKETS = {  # code: (file, coupon frequency per year, selectable)
    "US": ("fred_DGS10.csv", 2, False),
    "DE": ("yield_DE10Y_daily.csv", 1, True),
    "UK": ("yield_UK10Y_daily.csv", 2, True),
    "JP": ("yield_JP10Y_daily.csv", 2, True),   # JGBs pay semi-annual coupons (corrected pre-data, see ledger)
}
US_IS_MONTHS = (pd.Period("1990-01", "M"), pd.Period("2019-04", "M")); US_SERIES_CUT = pd.Timestamp("2019-05-06")
CELL = {"C1_extension_long": (-3, 0, +1)}
READ = {"T-1_long": (-1, 0, +1), "T+2_reversal_short": (0, 2, -1)}


def load_yield(fname):
    d = pd.read_csv(os.path.join(HERE, "data", fname)); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def mod_dur(y_pct, years, freq):
    c = y_pct / 100.0 / freq; n = freq * years
    if c <= 0: return float(years)                     # zero/negative yields: par-bond limit = maturity
    return (1 + c) / c * (1 - (1 + c) ** (-n)) / freq / (1 + c)


def ret_parts(y, years, freq, p0, p1):
    if p0 < 0 or p1 >= len(y) or p0 >= p1: return np.nan, np.nan
    y0, y1 = y.iloc[p0], y.iloc[p1]; days = (y.index[p1] - y.index[p0]).days
    if days > (p1 - p0) + 5: return np.nan, np.nan
    return -mod_dur(y0, years, freq) * (y1 - y0) / 100.0 * 1e4, y0 / 100.0 * days / 365.0 * 1e4


def rows_for(y, years, freq, pos_list, cells, tag):
    rows = []
    for p in pos_list:
        for cn, (a, b, s) in cells.items():
            px, cy = ret_parts(y, years, freq, p + a, p + b)
            if np.isnan(px): continue
            r = px + cy
            rows.append(dict(pos=p, date=y.index[p], tag=tag, cell=cn, sign=s, price=s * px, carry=s * cy, gross=s * r,
                             net=s * r - COST_BP, net15=s * r - 1.5 * COST_BP, net2=s * r - 2 * COST_BP))
    return pd.DataFrame(rows)


def placebo_maxima(y, freq, ev_pos, all_me, lo, hi):
    n = len(y); maxima = []
    for k in [k for k in range(-13, 14) if abs(k) >= 4]:
        sh = [p + k for p in ev_pos if 0 <= p + k < n]
        e = rows_for(y, 10, freq, sh, CELL, "placebo"); vals = []
        for cn, (a, b, s) in CELL.items():
            c = rows_for(y, 10, freq, control_positions(y, all_me, a, b, lo, hi, win_pos=sh), {cn: (a, b, s)}, "ctrl")
            r = strat_diff(e[e.cell == cn], c) if len(c) and len(e) else {}
            vals.append(abs(r.get("t") or 0.0))
        maxima.append(max(vals))
    return np.array(maxima)


def evaluate_market(code, y, freq, ev_pos, all_me):
    cells = dict(CELL); cells.update(READ)
    e = rows_for(y, 10, freq, ev_pos, cells, "event"); out = {"n_events": int(len(ev_pos))}
    if len(e) == 0: return out, e
    out["span"] = [str(e.date.min().date()), str(e.date.max().date())]
    lo, hi = min(ev_pos), max(ev_pos)
    for cn, (a, b, s) in cells.items():
        c = rows_for(y, 10, freq, control_positions(y, all_me, a, b, lo, hi), {cn: (a, b, s)}, "control"); g = e[e.cell == cn]
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), price_component=stats(g.price), carry=stats(g.carry),
                       control_price=stats(c.price), n_control=int(len(c)), strat_diff=strat_diff(g, c), diff_halves=diff_halves(g, c))
        if cn in CELL:
            q = g.date.dt.month.isin([3, 6, 9, 12])
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           quarter_end=dict(n=int(q.sum()), strat_diff=strat_diff(g[q], c)), other_month_end=dict(n=int((~q).sum()), strat_diff=strat_diff(g[~q], c)),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           by_era_diff={era: strat_diff(g[m_], c[m_c]) for era, m_, m_c in (
                               ("pre-2009", g.date < "2009-01-01", c.date < "2009-01-01"), ("2009+", g.date >= "2009-01-01", c.date >= "2009-01-01"))})
    return out, e


def split_market(y, code):
    """returns (series for this run, event positions, all month-end positions, cut description)."""
    if code == "US":
        if not UNSEAL:
            ys = y[y.index <= US_SERIES_CUT]; ev = month_end_positions(ys, *US_IS_MONTHS)
        else:
            ys = y[y.index >= pd.Timestamp("2018-06-01")]; ev = month_end_positions(ys, pd.Period("2019-05", "M"), ys.index[-1].to_period("M"))
        return ys, ev, month_end_positions(ys, ys.index[0].to_period("M"), ys.index[-1].to_period("M")), "attempt-59 cut"
    me_all = month_end_positions(y, y.index[0].to_period("M"), y.index[-1].to_period("M"))
    # drop a partial current month
    if y.index[me_all[-1]].to_period("M") == y.index[-1].to_period("M"): me_all = me_all[:-1]
    k = int(np.floor(len(me_all) * (1 - HOLDOUT)))
    last_is = y.index[me_all[k - 1]]; first_oos = y.index[me_all[k]]
    if not UNSEAL:
        ys = y[y.index <= last_is + pd.Timedelta(days=7)]
        ev = [p for p in month_end_positions(ys, ys.index[0].to_period("M"), last_is.to_period("M"))]
    else:
        ys = y[y.index >= first_oos - pd.Timedelta(days=45)]
        ev = month_end_positions(ys, first_oos.to_period("M"), y.index[me_all[-1]].to_period("M"))
    allme = month_end_positions(ys, ys.index[0].to_period("M"), ys.index[-1].to_period("M"))
    return ys, ev, allme, f"IS month-ends {str(y.index[me_all[0]].date())}..{str(last_is.date())} ({k}); OOS from {str(first_oos.date())} ({len(me_all) - k})"


if __name__ == "__main__":
    res = {"unsealed": UNSEAL, "markets": {}}
    cleared_prev = None
    if UNSEAL:
        isr = json.load(open(os.path.join(HERE, "results", "r83_monthend_global_is.json")))
        cleared_prev = [m for m, ok in isr["verdict"].items() if ok]
        if not cleared_prev: raise SystemExit("no market cleared IS; holdouts stay sealed")
    pooled_e, pooled_c = [], []
    for code, (fname, freq, selectable) in MARKETS.items():
        path = os.path.join(HERE, "data", fname)
        if not os.path.exists(path):
            print(f"=== {code}: {fname} missing - market skipped (data-gated) ==="); res["markets"][code] = {"skipped": "no data"}; continue
        if UNSEAL and (code not in cleared_prev): continue
        y = load_yield(fname); ys, ev, allme, cutdesc = split_market(y, code)
        out, e = evaluate_market(code, ys, freq, ev, allme); out["cut"] = cutdesc; out["coupon_freq"] = freq; out["selectable"] = selectable
        lo, hi = (min(ev), max(ev)) if ev else (0, 0)
        if not UNSEAL and ev:
            mx = placebo_maxima(ys, freq, ev, allme, lo, hi); t_obs = out["C1_extension_long"]["strat_diff"].get("t") or -9
            out["maxstat"] = dict(placebo_clocks=int(len(mx)), obs_t=float(t_obs), placebo_max_t=[round(float(x), 2) for x in mx], p=float((np.sum(mx >= t_obs) + 1) / (len(mx) + 1)))
        res["markets"][code] = out
        if selectable and len(e):
            g = e[e.cell == "C1_extension_long"].copy(); g["market"] = code; pooled_e.append(g)
            c = rows_for(ys, 10, freq, control_positions(ys, allme, -3, 0, lo, hi), CELL, "control"); c["market"] = code; pooled_c.append(c)
        v = out.get("C1_extension_long", {})
        print(f"=== {code} ({'OOS' if UNSEAL else 'IS'}; {cutdesc}; coupon {freq}/yr) month-ends {out['n_events']} ===")
        if v:
            print(f"  C1 net {json.dumps(v['x1'], default=float)}\n     price {v['price_component'].get('mean_bp', float('nan')):+.1f} carry {v['carry'].get('mean_bp', float('nan')):+.2f} control price {v['control_price'].get('mean_bp', float('nan')):+.1f} n_control {v['n_control']}\n     strat_diff {json.dumps(v['strat_diff'], default=float)} diff_halves {v['diff_halves']}\n     x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f} qtr {json.dumps(v['quarter_end']['strat_diff'], default=float)} other {json.dumps(v['other_month_end']['strat_diff'], default=float)}\n     era {json.dumps(v['by_era_diff'], default=float)}\n     per-year {v['per_year_net']}")
            for rn in READ: print(f"  {rn:18s} net {json.dumps(out[rn]['x1'], default=float)} diff {json.dumps(out[rn]['strat_diff'], default=float)}")
            if "maxstat" in out: print("  maxstat:", out["maxstat"])
    if pooled_e:
        E = pd.concat(pooled_e); C = pd.concat(pooled_c)
        res["pooled_three_market_diff"] = strat_diff(E, C); res["pooled_n"] = int(len(E))
        print("  pooled three-market differential (read-only):", res["pooled_three_market_diff"])
    passes = {}
    for code, out in res["markets"].items():
        if "skipped" in out or not out.get("selectable") or "C1_extension_long" not in out: continue
        v = out["C1_extension_long"]; s, sd = v["x1"], v["strat_diff"]; floor = T_FLOOR_OOS if UNSEAL else T_FLOOR_IS
        own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
        base = s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0] and v["x2"].get("mean_bp", -1) > 0 and sd.get("diff_bp", -1) > 0 and d_t >= floor
        ok = base and (v["x15"].get("mean_bp", -1) > 0 if UNSEAL else (v["diff_halves"] == [1.0, 1.0] and out["maxstat"]["p"] < 0.05))
        passes[code] = bool(ok)
    res["verdict"] = passes
    res["replicates"] = bool(sum(passes.values()) >= 2) if not UNSEAL else None
    print(f"\nATTEMPT 60 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes} (mechanism replicates in >= 2 of 3: {res['replicates']})")
    json.dump(res, open(os.path.join(HERE, "results", f"r83_monthend_global_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
