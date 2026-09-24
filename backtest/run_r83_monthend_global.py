"""Attempt 60 (Round 83) v2: out-of-market replication of the month-end index-extension long (attempt 59) on German,
UK and Japanese 10-year government bonds, with the US 10-year as a fidelity anchor. v2 adopts the three critics'
pre-data amendments (ledger, Round 83 AMENDMENT): a manifest gate, a fixed calendar cut, a family verdict decided
at the sealed stage, a roll guard, a date-clustered pooled differential, a US-orthogonalised read-only, the
YCC / negative-yield / December splits and a drop-one-max influence read.

Cell per market (selectable; two-sided Bonferroni-3 floor t >= 2.39): C1 EXTENSION LONG, close of T-3 -> month-end
close T on the market's own yield calendar. Proxy: par 10y bond, return = -ModD(y0)*dy + carry, semi-annual coupon for
US/UK/JP, annual for DE (Bunds); exact par ModD at negative yields; cost 3 bp RT, 1.5x / 2x. IS bar per market as
attempt 59 v2: n >= 40, net > 0, PF >= 1.15, own t >= floor, halves [+,+], positive at 2x; year-stratified
event-minus-control differential on the price component > 0, t >= floor, halves [+,+], non-overlapping controls >= 5
bd from every month-end; placebo-clock max-stat (k in +-4..+-13, 20 clocks, controls exclude true month-ends; signed t
must beat all 20). OOS bar: n >= 40, net > 0, PF >= 1.15, t >= 2.0, [+,+], positive at 1.5x and 2x, differential > 0
with t >= 2.0.

GATE: a market runs only if reference/yields_global_manifest.json admits it (passed true, series id, source, route,
construction, quote time, span, scale / known-date / holiday-row checks; issue-based series need roll dates). The
data file's SHA-256 and the manifest's are recorded at IS and asserted at OOS.
CUT (fixed calendar, same for every market, identical to attempt 59): IS month-ends 1990-01..2019-04 (series clipped
at 2019-05-06), sealed OOS month-ends 2019-05..2026-08 (series from 2018-06-01). Admission also needs >= 120 IS
month-ends. Month-ends before 1990 are a read-only mechanism placebo (pre-index era), never a verdict input.
FAMILY VERDICT (sealed stage only): REPLICATES iff >= 2 markets pass the OOS bar; PARTIAL iff exactly 1; FAILS iff
0; INCONCLUSIVE iff < 2 markets admitted. IS clearing makes a market a CANDIDATE (one sealed shot), nothing more;
0 candidates = FAILS at the IS stage. A JP miss inside yield-curve control counts (symmetric); the split is read-only.
Read-only (never touch a verdict): per market T-1 -> T, T -> T+2 reversal, quarter-end vs other, era split 2009,
per-year, mirror, ex-December, drop-one-max influence, YCC-window split (JP) and negative-yield split (all),
jump-rank roll guard, ex-roll re-score (issue-based series), US-orthogonalised differential; family: US anchor,
date-clustered pooled differential, market-stratified pooled differential, cross-market event correlation, family
max-stat. Outputs results/r83_monthend_global_{is,oos}.json. OOS only with UNSEAL_OK=1 --unseal.
"""
import hashlib
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
MANIFEST = os.path.join(HERE, "reference", "yields_global_manifest.json")
MARKETS = {  # code: (file, coupon frequency per year, selectable)
    "US": ("fred_DGS10.csv", 2, False),
    "DE": ("yield_DE10Y_par_daily.csv", 1, True),   # Bundesbank Svensson PAR yield (ZAR); the spot (ZST) file is a companion, not run
    "UK": ("yield_UK10Y_daily.csv", 2, True),
    "JP": ("yield_JP10Y_daily.csv", 2, True),   # JGBs pay semi-annual coupons (corrected pre-data, see ledger)
}
REGISTERED_CUT = dict(is_first_month="1990-01", is_last_month="2019-04", is_series_clip="2019-05-06", oos_first_month="2019-05",
                      oos_last_month="2026-08", oos_series_start="2018-06-01")
PRE_INDEX_ERA_END = pd.Timestamp("1990-01-10")   # read-only mechanism placebo: series start .. 1989-12 month-ends
MIN_IS_EVENTS, MIN_OOS_EVENTS = 120, 40
CELL = {"C1_extension_long": (-3, 0, +1)}
READ = {"T-1_long": (-1, 0, +1), "T+2_reversal_short": (0, 2, -1)}
YCC = (pd.Timestamp("2016-09-21"), pd.Timestamp("2024-03-19"))   # BoJ yield-curve control window (JP read-only split)
MANIFEST_REQUIRED = ("series_id", "source", "route", "construction", "quote_time", "first_date", "last_date",
                     "scale_check", "known_date_checks", "holiday_row_check", "passed")
CONSTRUCTIONS = ("fitted-par", "fitted-spot", "bucket-average", "issue-based")
SPLIT_MONTHS = None   # optional read-only split of C1 by calendar month set (set by a wrapper before main())


def sha256(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()


def load_manifest():
    if not os.path.exists(MANIFEST): return {}
    with open(MANIFEST) as f: return json.load(f).get("markets", {})


def admitted(code, man):
    """manifest gate: returns (ok, reason)."""
    m = man.get(code)
    if m is None: return False, "no manifest entry"
    missing = [k for k in MANIFEST_REQUIRED if k not in m]
    if missing: return False, f"manifest fields missing: {missing}"
    if m["construction"] not in CONSTRUCTIONS: return False, f"unknown construction {m['construction']!r}"
    if m["construction"] == "issue-based" and not m.get("roll_dates"): return False, "issue-based series without roll dates"
    if not m["passed"]: return False, "manifest passed=false"
    return True, "admitted"


def load_yield(fname):
    """contract: exactly two columns (date, yield_pct), ISO naive dates, '.' decimal, percent, no Sunday rows (JP
    Saturday half-sessions allowed before 1989-03, pre-IS), unique ascending dates, missing empty/NaN/'.', leading
    not-yet-published rows allowed, no gap > 12 calendar days."""
    d = pd.read_csv(os.path.join(HERE, "data", fname))
    assert d.shape[1] == 2, f"{fname}: expected 2 columns (date, yield_pct), got {list(d.columns)}"
    d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date, format="%Y-%m-%d")
    assert not d.y.astype(str).str.contains(",").any(), f"{fname}: comma in a value (European decimal?)"
    raw = d.y.astype(str).str.strip(); d["y"] = pd.to_numeric(d.y, errors="coerce")
    first = d.y.first_valid_index(); d = d.loc[first:]; raw = raw.loc[first:]   # leading rows before the provider published the tenor
    n_missing = int((d.y.isna() & ~(raw.isna() | raw.isin([".", "", "nan", "NaN", "None"]))).sum())   # FRED "." / blank holiday markers are legitimate (pandas 3 keeps NaN through astype(str))
    y = d.dropna().sort_values("date", kind="stable").set_index("date").y
    assert y.index.is_unique and y.index.is_monotonic_increasing, f"{fname}: duplicate dates"
    assert (y.index.dayofweek < 6).all(), f"{fname}: Sunday rows"
    sat = y.index[y.index.dayofweek == 5]
    assert len(sat) == 0 or (fname.startswith("yield_JP") and sat.max() < pd.Timestamp("1989-03-01")), f"{fname}: Saturday rows after 1989-02 ({len(sat)})"
    assert -2.0 < y.min() and 1.0 < y.max() < 25.0, f"{fname}: yields {y.min():.3f}..{y.max():.3f} not in percent"
    gaps = y.index.to_series().diff().dt.days
    assert gaps.max() <= 12, f"{fname}: {int(gaps.max())}-day gap ending {gaps.idxmax().date()}"
    assert n_missing < 0.02 * len(d), f"{fname}: {n_missing} non-numeric values"
    assert len(y) >= 2500, f"{fname}: only {len(y)} rows"
    return y


def mod_dur(y_pct, years, freq):
    """modified duration of a par bond (coupon = yield), exact for negative yields while 1 + c > 0."""
    c = y_pct / 100.0 / freq; n = freq * years
    if abs(c) < 1e-12: return float(years)
    return (1 - (1 + c) ** (-n)) / (c * freq)


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
            rows.append(dict(pos=p, date=y.index[p], d0=y.index[p + a], d1=y.index[p + b], y0=float(y.iloc[p + a]), tag=tag,
                             cell=cn, sign=s, price=s * px, carry=s * cy, gross=s * r, net=s * r - COST_BP,
                             net15=s * r - 1.5 * COST_BP, net2=s * r - 2 * COST_BP))
    return pd.DataFrame(rows)


def empty_cell(g):
    return dict(x1=stats(g.net) if len(g) else dict(n=0), n_control=0, strat_diff=dict(n_event=0), diff_halves=[0.0, 0.0])


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


def us_window_price(us, d0, d1):
    """US 10y par-bond price component (bp) over the same calendar window, as-of lookups (US holidays shift the read)."""
    y0, y1 = us.asof(d0), us.asof(d1)
    if np.isnan(y0) or np.isnan(y1): return np.nan
    return -mod_dur(y0, 10, 2) * (y1 - y0) / 100.0 * 1e4


def orthogonalise(g, c, us, beta=None):
    """foreign price component minus beta x US same-window price; beta from this run's controls unless given (OOS uses IS beta)."""
    g = g.copy(); c = c.copy()
    g["us"] = [us_window_price(us, a, b) for a, b in zip(g.d0, g.d1)]; c["us"] = [us_window_price(us, a, b) for a, b in zip(c.d0, c.d1)]
    g = g.dropna(subset=["us"]); c = c.dropna(subset=["us"])
    if len(c) < 30 or len(g) < 10: return dict(n_event=int(len(g)), note="too few rows")
    if beta is None:
        cov = np.cov(c.price, c.us); beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] > 0 else 0.0
    g["price_o"] = g.price - beta * g.us; c["price_o"] = c.price - beta * c.us
    return dict(beta=float(beta), us_event_mean_bp=float(g.us.mean()), us_control_mean_bp=float(c.us.mean()),
                event_ortho=stats(g.price_o), strat_diff=strat_diff(g, c, col="price_o"), raw_diff_for_reference=strat_diff(g, c).get("diff_bp"))


def jump_rank_guard(y, all_me):
    """blind roll guard: share of robust-jump days (|dy| > 4 x 1.4826 x trailing-60d MAD of dy) at business-day ranks
    T-4..T+1 around every month-end vs mid-month ranks T-14..T-7. ratio > 2 (with >= 5 event-rank jumps) flags the
    market 'pass with roll flag'."""
    dy = y.diff(); mad = dy.rolling(60).apply(lambda v: np.median(np.abs(v - np.median(v))), raw=True).shift(1)
    jump = (dy.abs() > 4 * 1.4826 * mad).values; valid = mad.notna().values & (mad.values > 0)
    rank = np.full(len(y), 99, int)
    for m in all_me:
        for r in range(-14, 2):
            p = m + r
            if 0 <= p < len(y) and rank[p] == 99: rank[p] = r
    ev = (rank >= -4) & (rank <= 1) & valid; mid = (rank >= -14) & (rank <= -7) & valid
    se = float(jump[ev].mean()) if ev.sum() else np.nan; sm = float(jump[mid].mean()) if mid.sum() else np.nan
    ratio = float(se / sm) if (sm == sm and sm > 0) else (np.inf if (se == se and se > 0) else np.nan)
    by_rank = {int(r): dict(n=int(((rank == r) & valid).sum()), jump_share=float(jump[(rank == r) & valid].mean()) if ((rank == r) & valid).sum() else None)
               for r in range(-14, 2)}
    return dict(event_rank_jump_share=se, mid_month_jump_share=sm, ratio=ratio, event_rank_jumps=int(jump[ev].sum()),
                mid_month_jumps=int(jump[mid].sum()), roll_flag=bool((ratio == ratio) and ratio > 2 and jump[ev].sum() >= 5), by_rank=by_rank)   # inf ratio flags; nan does not


def drop_one_max(g, c):
    """influence read: the cell without its single largest |net| event."""
    if len(g) < 10: return dict(n=int(len(g)))
    i = g.net.abs().idxmax(); r = g.loc[i]
    return dict(dropped_date=str(r.date.date()), dropped_net_bp=float(r.net), x1=stats(g.drop(i).net), strat_diff=strat_diff(g.drop(i), c))


def evaluate_market(code, y, freq, ev_pos, all_me, us=None, roll_dates=(), beta=None):
    cells = dict(CELL); cells.update(READ)
    e = rows_for(y, 10, freq, ev_pos, cells, "event"); out = {"n_events": int(len(ev_pos))}
    if len(e) == 0: return out, e, None
    out["span"] = [str(e.date.min().date()), str(e.date.max().date())]
    lo, hi = min(ev_pos), max(ev_pos); c1 = None
    for cn, (a, b, s) in cells.items():
        c = rows_for(y, 10, freq, control_positions(y, all_me, a, b, lo, hi), {cn: (a, b, s)}, "control"); g = e[e.cell == cn]
        if len(c) == 0 or len(g) == 0: out[cn] = empty_cell(g); continue
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), price_component=stats(g.price), carry=stats(g.carry),
                       control_price=stats(c.price), n_control=int(len(c)), strat_diff=strat_diff(g, c), diff_halves=diff_halves(g, c))
        if cn in CELL:
            c1 = c
            q = g.date.dt.month.isin([3, 6, 9, 12]); dec = g.date.dt.month == 12
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           quarter_end=dict(n=int(q.sum()), strat_diff=strat_diff(g[q], c)), other_month_end=dict(n=int((~q).sum()), strat_diff=strat_diff(g[~q], c)),
                           ex_december=dict(n=int((~dec).sum()), x1=stats(g[~dec].net), strat_diff=strat_diff(g[~dec], c)),
                           december_only=dict(n=int(dec.sum()), x1=stats(g[dec].net)),
                           drop_one_max=drop_one_max(g, c),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           by_era_diff={era: strat_diff(g[m_], c[m_c]) for era, m_, m_c in (
                               ("pre-2009", g.date < "2009-01-01", c.date < "2009-01-01"), ("2009+", g.date >= "2009-01-01", c.date >= "2009-01-01"))})
            if SPLIT_MONTHS:
                im, imc = g.date.dt.month.isin(SPLIT_MONTHS), c.date.dt.month.isin(SPLIT_MONTHS)
                out[cn]["month_split"] = dict(months=sorted(SPLIT_MONTHS), inside=dict(n=int(im.sum()), x1=stats(g[im].net), strat_diff=strat_diff(g[im], c)),
                                              outside=dict(n=int((~im).sum()), x1=stats(g[~im].net), strat_diff=strat_diff(g[~im], c)))
            neg, negc = g.y0 <= 0, c.y0 <= 0
            out[cn]["negative_yield_split"] = dict(n_neg=int(neg.sum()), neg=dict(x1=stats(g[neg].net), strat_diff=strat_diff(g[neg], c[negc])),
                                                   pos=dict(x1=stats(g[~neg].net), strat_diff=strat_diff(g[~neg], c[~negc])))
            if code == "JP":
                w, wc = g.date.between(*YCC), c.date.between(*YCC)
                out[cn]["ycc_split"] = dict(window=[str(YCC[0].date()), str(YCC[1].date())], n_in=int(w.sum()),
                                            inside=dict(x1=stats(g[w].net), strat_diff=strat_diff(g[w], c[wc])),
                                            outside=dict(x1=stats(g[~w].net), strat_diff=strat_diff(g[~w], c[~wc])))
            if roll_dates:
                rd = pd.to_datetime(list(roll_dates))
                hit = np.array([bool(((rd >= a) & (rd <= b)).any()) for a, b in zip(g.d0, g.d1)])
                out[cn]["ex_roll"] = dict(n_flagged=int(hit.sum()), flagged_dates=[str(d.date()) for d in g.date[hit]],
                                          x1=stats(g[~hit].net), strat_diff=strat_diff(g[~hit], c))
            if us is not None and code != "US":
                out[cn]["us_orthogonalised"] = orthogonalise(g, c, us, beta)
    out["jump_rank_guard"] = jump_rank_guard(y, all_me)
    return out, e, c1


def split_market(y, code):
    """fixed calendar cut for every market (REGISTERED_CUT). returns (series, event positions, all month-ends, cut record)."""
    if not UNSEAL:
        ys = y[y.index <= pd.Timestamp(REGISTERED_CUT["is_series_clip"])]
        ev = month_end_positions(ys, pd.Period(REGISTERED_CUT["is_first_month"], "M"), pd.Period(REGISTERED_CUT["is_last_month"], "M"))
    else:
        ys = y[y.index >= pd.Timestamp(REGISTERED_CUT["oos_series_start"])]
        ev = month_end_positions(ys, pd.Period(REGISTERED_CUT["oos_first_month"], "M"), pd.Period(REGISTERED_CUT["oos_last_month"], "M"))
    allme = month_end_positions(ys, ys.index[0].to_period("M"), ys.index[-1].to_period("M"))
    rec = dict(REGISTERED_CUT); rec.update(stage="OOS" if UNSEAL else "IS", series_first=str(y.index[0].date()), series_last=str(y.index[-1].date()),
                                          n_events=int(len(ev)), first_event=str(ys.index[ev[0]].date()) if ev else None, last_event=str(ys.index[ev[-1]].date()) if ev else None)
    return ys, ev, allme, rec


def pre_index_era(y, freq):
    """read-only mechanism placebo: the cell on month-ends before 1990 (bond indexing / benchmarked funds were marginal
    before the 1986 Lehman Aggregate, WGBI and NOMURA-BPI launches), own controls, no verdict role."""
    ys = y[y.index <= PRE_INDEX_ERA_END]
    if len(ys) < 500: return dict(n=0, note="series starts after 1989")
    ev = month_end_positions(ys, ys.index[0].to_period("M"), pd.Period("1989-12", "M")); allme = month_end_positions(ys, ys.index[0].to_period("M"), ys.index[-1].to_period("M"))
    e = rows_for(ys, 10, freq, ev, CELL, "event")
    if len(e) < 10: return dict(n=int(len(e)))
    c = rows_for(ys, 10, freq, control_positions(ys, allme, -3, 0, min(ev), max(ev)), CELL, "control")
    return dict(span=[str(e.date.min().date()), str(e.date.max().date())], x1=stats(e.net), x2=stats(e.net2), strat_diff=strat_diff(e, c), diff_halves=diff_halves(e, c))


def pooled_clustered(E, C):
    """per market and year: event price minus that market's control mean; then average across markets per calendar
    month-end date; t across dates (same-date cross-market dependence removed by construction)."""
    z = []
    for mk in E.market.unique():
        g = E[E.market == mk].copy(); c = C[C.market == mk]
        cm = c.groupby(c.date.dt.year).price.mean()
        g["z"] = g.price - g.date.dt.year.map(cm); g["month"] = g.date.dt.to_period("M"); z.append(g.dropna(subset=["z"])[["month", "z"]])
    Z = pd.concat(z).groupby("month").z.agg(["mean", "count"])
    s = stats(Z["mean"]); s.update(n_dates=int(len(Z)), dates_with_all_markets=int((Z["count"] == E.market.nunique()).sum()))
    return s


def pooled_market_stratified(E, C):
    num = den = var = 0.0
    for mk in E.market.unique():
        r = strat_diff(E[E.market == mk], C[C.market == mk])
        if r.get("n_event"): w = r["n_event"]; num += w * r["diff_bp"]; den += w; var += (w * r["se"]) ** 2
    return dict(n_event=int(den), diff_bp=num / den, se=np.sqrt(var) / den, t=num / np.sqrt(var),
                note="market x year strata; SE ignores same-date cross-market correlation") if den else dict(n_event=0)


def cross_market_corr(E):
    P = E.assign(month=E.date.dt.to_period("M")).pivot_table(index="month", columns="market", values="price")
    out = {}
    for i, a in enumerate(P.columns):
        for b in P.columns[i + 1:]:
            q = P[[a, b]].dropna()
            if len(q) >= 30: out[f"{a}-{b}"] = dict(n=int(len(q)), corr=float(q.corr().iloc[0, 1]))
    return out


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)): return bool(o)
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (pd.Timestamp,)): return str(o.date())
    return o


def market_passes(v, stage_oos, floor_is=None):
    s, sd = v["x1"], v["strat_diff"]; floor = T_FLOOR_OOS if stage_oos else (T_FLOOR_IS if floor_is is None else floor_is); nmin = MIN_OOS_EVENTS if stage_oos else 40
    own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
    base = (s.get("n", 0) >= nmin and s.get("mean_bp", -1) > 0 and (s.get("pf") or 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
            and v.get("x2", {}).get("mean_bp", -1) > 0 and sd.get("diff_bp", -1) > 0 and d_t >= floor)
    if stage_oos: return bool(base and v.get("x15", {}).get("mean_bp", -1) > 0)
    return bool(base and v.get("diff_halves") == [1.0, 1.0] and v.get("maxstat", {}).get("p", 1.0) < 0.05)


def main(markets=None, t_floor_is=None, tag="r83_monthend_global", single=False):
    """single=True: one selectable market, the family verdict is that market's own verdict (attempt 61 wrapper)."""
    markets = markets or MARKETS; floor_is = T_FLOOR_IS if t_floor_is is None else t_floor_is
    man = load_manifest()
    res = {"unsealed": UNSEAL, "registered_cut": REGISTERED_CUT, "tag": tag, "t_floor_is": floor_is, "manifest_sha256": sha256(MANIFEST) if os.path.exists(MANIFEST) else None, "markets": {}}
    isr = None
    if UNSEAL:
        with open(os.path.join(HERE, "results", f"{tag}_is.json")) as f: isr = json.load(f)
        candidates = [m for m, ok in isr["verdict"].items() if ok]
        if not candidates: raise SystemExit("no market cleared IS; holdouts stay sealed")
        assert isr.get("manifest_sha256") == res["manifest_sha256"], "manifest changed since the IS run"
    us_full = load_yield("fred_DGS10.csv") if os.path.exists(os.path.join(HERE, "data", "fred_DGS10.csv")) else None
    pooled_e, pooled_c, maxima = [], [], {}
    for code, (fname, freq, selectable) in markets.items():
        path = os.path.join(HERE, "data", fname)
        if not os.path.exists(path):
            print(f"=== {code}: {fname} missing - market skipped (data-gated) ==="); res["markets"][code] = {"skipped": "no data"}; continue
        if selectable:
            ok, why = admitted(code, man)
            if not ok:
                print(f"=== {code}: not admitted by manifest ({why}) - market skipped ==="); res["markets"][code] = {"skipped": f"manifest: {why}"}; continue
        if UNSEAL and selectable and code not in candidates:
            res["markets"][code] = {"skipped": "did not clear IS; holdout stays sealed"}; continue
        y = load_yield(fname); ys, ev, allme, cutrec = split_market(y, code)
        fsha = sha256(path)
        if UNSEAL and code in isr["markets"] and "cut_record" in isr["markets"][code]:
            prev = isr["markets"][code]
            assert prev["file_sha256"] == fsha, f"{code}: data file changed since the IS run"
            assert all(prev["cut_record"][k] == cutrec[k] for k in REGISTERED_CUT), f"{code}: registered cut moved"
        if selectable and not UNSEAL and len(ev) < MIN_IS_EVENTS:
            print(f"=== {code}: only {len(ev)} IS month-ends (< {MIN_IS_EVENTS}) - not admitted ==="); res["markets"][code] = {"skipped": f"IS month-ends {len(ev)} < {MIN_IS_EVENTS}", "cut_record": cutrec}; continue
        beta = isr["markets"][code]["C1_extension_long"].get("us_orthogonalised", {}).get("beta") if (UNSEAL and selectable) else None
        roll = man.get(code, {}).get("roll_dates", ()) if selectable else ()
        out, e, c1 = evaluate_market(code, ys, freq, ev, allme, us=us_full if selectable else None, roll_dates=roll, beta=beta)
        out.update(cut_record=cutrec, file_sha256=fsha, coupon_freq=freq, selectable=selectable, manifest=man.get(code))
        if not UNSEAL: out["pre_index_era_readonly"] = pre_index_era(y, freq)
        lo, hi = (min(ev), max(ev)) if ev else (0, 0)
        if not UNSEAL and ev and "C1_extension_long" in out and out["C1_extension_long"].get("n_control"):
            mx = placebo_maxima(ys, freq, ev, allme, lo, hi); t_obs = out["C1_extension_long"]["strat_diff"].get("t") or -9
            out["C1_extension_long"]["maxstat"] = out["maxstat"] = dict(placebo_clocks=int(len(mx)), obs_t=float(t_obs), placebo_max_t=[round(float(x), 2) for x in mx],
                                                                       p=float((np.sum(mx >= t_obs) + 1) / (len(mx) + 1)))
            if selectable: maxima[code] = (mx, float(t_obs))
        res["markets"][code] = out
        if selectable and len(e) and c1 is not None:
            g = e[e.cell == "C1_extension_long"].copy(); g["market"] = code; pooled_e.append(g); c1 = c1.copy(); c1["market"] = code; pooled_c.append(c1)
        v = out.get("C1_extension_long", {})
        print(f"=== {code} ({'OOS' if UNSEAL else 'IS'}; events {cutrec['first_event']}..{cutrec['last_event']}; coupon {freq}/yr; sha {fsha[:8]}) month-ends {out['n_events']} ===")
        if v and v.get("n_control"):
            print(f"  C1 net {json.dumps(clean(v['x1']))}\n     price {v['price_component'].get('mean_bp', float('nan')):+.1f} carry {v['carry'].get('mean_bp', float('nan')):+.2f} control price {v['control_price'].get('mean_bp', float('nan')):+.1f} n_control {v['n_control']}\n     strat_diff {json.dumps(clean(v['strat_diff']))} diff_halves {v['diff_halves']}\n     x15 {v['x15'].get('mean_bp', float('nan')):+.1f} x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f} qtr {json.dumps(clean(v['quarter_end']['strat_diff']))} other {json.dumps(clean(v['other_month_end']['strat_diff']))}\n     ex-Dec {json.dumps(clean(v['ex_december']['strat_diff']))} drop-one-max {json.dumps(clean(v['drop_one_max']))}\n     era {json.dumps(clean(v['by_era_diff']))}\n     neg-yield split n_neg {v['negative_yield_split']['n_neg']} neg {json.dumps(clean(v['negative_yield_split']['neg']['strat_diff']))}\n     per-year {v['per_year_net']}")
            if "ycc_split" in v: print(f"     YCC split {json.dumps(clean(v['ycc_split']))}")
            if "month_split" in v: print(f"     month split {json.dumps(clean(v['month_split']))}")
            if "ex_roll" in v: print(f"     ex-roll {json.dumps(clean(v['ex_roll']))}")
            if "us_orthogonalised" in v: print(f"     US-orthogonalised {json.dumps(clean(v['us_orthogonalised']))}")
            print(f"     jump-rank roll guard {json.dumps(clean({k: out['jump_rank_guard'][k] for k in ('event_rank_jump_share', 'mid_month_jump_share', 'ratio', 'event_rank_jumps', 'roll_flag')}))}")
            for rn in READ: print(f"  {rn:18s} net {json.dumps(clean(out[rn]['x1']))} diff {json.dumps(clean(out[rn]['strat_diff']))}")
            if "maxstat" in out: print("  maxstat:", clean(out["maxstat"]))
            if out.get("pre_index_era_readonly", {}).get("x1"): print(f"  pre-1990 mechanism placebo (read-only) {json.dumps(clean(out['pre_index_era_readonly']))}")
    if pooled_e:
        E = pd.concat(pooled_e); C = pd.concat(pooled_c)
        res["pooled_date_clustered"] = pooled_clustered(E, C); res["pooled_market_stratified"] = pooled_market_stratified(E, C)
        res["cross_market_event_corr"] = cross_market_corr(E)
        print("  pooled, date-clustered (read-only):", clean(res["pooled_date_clustered"]))
        print("  pooled, market-stratified (read-only):", clean(res["pooled_market_stratified"]))
        print("  cross-market event corr:", clean(res["cross_market_event_corr"]))
    if len(maxima) >= 2:
        fam = np.max(np.vstack([mx for mx, _ in maxima.values()]), axis=0); obs = max(t for _, t in maxima.values())
        res["family_maxstat"] = dict(markets=list(maxima), obs_max_t=float(obs), placebo_family_max_t=[round(float(x), 2) for x in fam], p=float((np.sum(fam >= obs) + 1) / (len(fam) + 1)))
        print("  family max-stat (read-only):", clean(res["family_maxstat"]))
    passes = {}
    for code, out in res["markets"].items():
        if "skipped" in out or not out.get("selectable") or "C1_extension_long" not in out or not out["C1_extension_long"].get("n_control"): continue
        passes[code] = market_passes(out["C1_extension_long"], UNSEAL, floor_is)
    res["verdict"] = passes; n_adm = len(passes)
    if not UNSEAL:
        res["candidates"] = [m for m, ok in passes.items() if ok]
        if single: res["family"] = "INCONCLUSIVE (market not admitted)" if n_adm < 1 else ("FAILS at IS stage" if not res["candidates"] else f"CANDIDATE {res['candidates']} - one sealed shot")
        else: res["family"] = "INCONCLUSIVE (fewer than 2 markets admitted)" if n_adm < 2 else ("FAILS at IS stage (no candidate)" if not res["candidates"] else f"CANDIDATES {res['candidates']} - verdict at the sealed stage")
        for code in maxima:
            if passes.get(code) and res["markets"][code]["jump_rank_guard"]["roll_flag"]: res["family"] += f"; {code} candidate carries a roll flag"
    else:
        n_pass = sum(passes.values())
        if single: res["family"] = "PASS" if n_pass == 1 else "FAILS"
        else: res["family"] = "REPLICATES" if n_pass >= 2 else ("PARTIAL" if n_pass == 1 else "FAILS")
        res["shots_taken"] = len(passes)
        flags = [c for c in passes if passes[c] and (res["markets"][c]["jump_rank_guard"]["roll_flag"] or isr["markets"].get(c, {}).get("jump_rank_guard", {}).get("roll_flag"))]
        if flags: res["family"] += f" (roll flag on {flags}, IS or OOS stage)"
    print(f"\n{tag} {'OOS' if UNSEAL else 'IS'} VERDICT per market: {passes}\nFAMILY: {res['family']}")
    with open(os.path.join(HERE, "results", f"{tag}_{'oos' if UNSEAL else 'is'}.json"), "w") as f:
        json.dump(clean(res), f, indent=1)
    return res


if __name__ == "__main__":
    main()
