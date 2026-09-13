"""Attempt 58 v2 (Round 80, RE-REGISTERED after critic review): Treasury auction cycle on the 10-year,
tested as the paper's duration-matched spread (Lou, Yan & Zhang 2013).

Instrument: long 10y CMT par bond vs a DV01-matched short in the 5y CMT par bond (or the reverse).
Spread return (bp of 10y notional) = -ModD10 * (dy10 - dy5) * 1e4 + carry, carry = (y10 - y5 * ModD10/ModD5) * days/365 * 1e4.
Cells (selectable, 10y auctions; two-sided Bonferroni-2 floor 2.26 at df ~236, directional hypothesis):
  C1 RECOVERY   long the spread  T close -> T+5 close
  C2 CONCESSION short the spread T-5 close -> T close
Gate per cell: event net > 0, PF >= 1.15, own t >= 2.26, halves [+,+], positive at 2x cost (4 bp RT pair cost);
YEAR-STRATIFIED event-minus-control differential > 0 with t >= 2.26 and halves [+,+]; per-cell max-stat p < 0.05
from a de-resonated calendar-shift null with the control rebuilt per shift; C1 additionally needs the same
differential sign on BOTH the new-issue and the reopening subsets (CMT roll guard).
Control windows: every day of the window >= 6 business days from every 10y auction.
IS: auctions 1990-01-01..2020-02-04 on a series clipped at 2020-02-12; OOS: auctions >= 2020-02-12, sealed
(UNSEAL_OK=1 --unseal). Read-only: outright 10y legs, the 5y hedge leg alone, T+-2 spread windows, issue-date-
excluded C1, mirrors, per-year, unconditional drift. Outputs results/r80_auction_{is,oos}.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
SERIES_CUT = pd.Timestamp("2020-02-12")            # IS series end (exclusive of nothing after)
IS_EV_START, IS_EV_END = pd.Timestamp("1990-01-01"), pd.Timestamp("2020-02-04")
OOS_EV_START = pd.Timestamp("2020-02-12")
COST_BP = 4.0
T_FLOOR = 2.26
CELLS = {"C1_recovery": (0, 5, +1), "C2_concession": (-5, 0, -1)}
READ = {"T-2_concession": (-2, 0, -1), "T+2_recovery": (0, 2, +1)}
EXCL = 6                                            # control windows: every day >= 6 bd from every auction


def load_yield(tenor):
    f = {"10y": "fred_DGS10.csv", "5y": "UST05Y_daily_av.csv"}[tenor]
    d = pd.read_csv(os.path.join(HERE, "data", f)); d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def auctions10():
    n = pd.DataFrame(json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json"))))
    a = n[n.term.str.startswith(("10-Year", "9-Year"))]
    a = a.assign(date=pd.to_datetime(a.auction_date).dt.normalize(), issue=pd.to_datetime(a.issue_date).dt.normalize(), reopen=(a.reopening == "Yes"))
    return a[["date", "issue", "reopen"]].drop_duplicates("date").sort_values("date").reset_index(drop=True)


def mod_dur(y_pct, years):
    c = y_pct / 200.0; n = 2 * years
    if c <= 0: return years
    return (1 + c) / c * (1 - (1 + c) ** (-n)) / 2.0 / (1 + c)


def make_frame(y10, y5):
    f = pd.DataFrame({"y10": y10, "y5": y5}).dropna()
    f["d10"] = f.y10.map(lambda v: mod_dur(v, 10)); f["d5"] = f.y5.map(lambda v: mod_dur(v, 5))
    return f


def leg_returns(f, p0, p1):
    """returns (spread_bp, outright10_bp, hedge5_bp) for a long from close index p0 to p1; nan if invalid."""
    if p0 < 0 or p1 >= len(f) or p0 >= p1: return (np.nan,) * 3
    a, b = f.iloc[p0], f.iloc[p1]; days = (f.index[p1] - f.index[p0]).days
    if days > (p1 - p0) + 5: return (np.nan,) * 3
    r10 = -a.d10 * (b.y10 - a.y10) / 100.0 * 1e4 + a.y10 / 100.0 * days / 365.0 * 1e4
    ratio = a.d10 / a.d5
    r5 = -a.d5 * (b.y5 - a.y5) / 100.0 * 1e4 + a.y5 / 100.0 * days / 365.0 * 1e4
    return r10 - ratio * r5, r10, ratio * r5


def rows_for(f, pos_list, cells, tag):
    rows = []
    for p in pos_list:
        for cn, (a, b, s) in cells.items():
            sp, r10, r5 = leg_returns(f, p + a, p + b)
            if np.isnan(sp): continue
            rows.append(dict(pos=p, date=f.index[p], tag=tag, cell=cn, sign=s, spread=sp, out10=r10, hedge5=r5,
                             gross=s * sp, net=s * sp - COST_BP, net15=s * sp - 1.5 * COST_BP, net2=s * sp - 2 * COST_BP,
                             gross_out10=s * r10, gross_hedge=-s * r5))
    return pd.DataFrame(rows)


def control_positions(f, ev_pos, a, b):
    """anchor positions p such that every day in [p+a, p+b] is >= EXCL bd from every event position."""
    n = len(f); near = np.zeros(n, bool)
    for e in ev_pos: near[max(0, e - EXCL + 1):min(n, e + EXCL)] = True
    ok = ~near; cum = np.concatenate([[0], np.cumsum(ok)])
    out = []
    for p in range(max(0, -a), n - b):
        if cum[p + b + 1] - cum[p + a] == (b - a + 1): out.append(p)
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
    """year-stratified event-minus-control mean, weights = event share by year; SE from within-stratum variances."""
    ev = ev.copy(); ct = ct.copy(); ev["yr"] = ev.date.dt.year; ct["yr"] = ct.date.dt.year
    num = den = var = 0.0; used = 0; dropped = 0
    for yr, g in ev.groupby("yr"):
        c = ct[ct.yr == yr]
        if len(g) < min_e or len(c) < min_c: dropped += len(g); continue
        w = len(g); num += w * (g[col].mean() - c[col].mean()); den += w; used += w
        var += w * w * (g[col].var(ddof=1) / len(g) + c[col].var(ddof=1) / len(c))
    if den == 0: return dict(n_event=0)
    d = num / den; se = np.sqrt(var) / den
    return dict(n_event=int(used), n_control=int(len(ct)), dropped_events=int(dropped), diff_bp=float(d), se=float(se), t=float(d / se) if se > 0 else None)


def diff_halves(ev, ct, col="gross"):
    ev = ev.sort_values("date"); m = len(ev) // 2; cut = ev.date.iloc[m]
    out = []
    for e, c in ((ev.iloc[:m], ct[ct.date < cut]), (ev.iloc[m:], ct[ct.date >= cut])):
        r = strat_diff(e, c, col); out.append(float(np.sign(r.get("diff_bp", 0.0))))
    return out


def evaluate(f, ev, cells, tag, full=True):
    idx = {d: i for i, d in enumerate(f.index)}
    ev = ev[ev.date.isin(idx)].copy(); ev["pos"] = ev.date.map(idx)
    e = rows_for(f, ev.pos.tolist(), cells, "event")
    out = {"n_auctions": int(len(ev)), "span": [str(ev.date.min().date()), str(ev.date.max().date())]}
    ctrl = {}
    for cn, (a, b, s) in cells.items():
        cp = control_positions(f, ev.pos.tolist(), a, b); c = rows_for(f, cp, {cn: (a, b, s)}, "control"); ctrl[cn] = c
        g = e[e.cell == cn]
        out[cn] = dict(x1=stats(g.net), gross=stats(g.gross), control_gross=stats(c.gross), n_control=int(len(c)),
                       strat_diff=strat_diff(g, c), diff_halves=diff_halves(g, c),
                       control_years_covered={int(k): int(v) for k, v in c.date.dt.year.value_counts().sort_index().items()} if not full else None)
        if full and cn in CELLS:
            re = ev.set_index("pos").reopen; iss = ev.set_index("pos").issue
            gn, gr = g[~g.pos.map(re).astype(bool)], g[g.pos.map(re).astype(bool)]
            out[cn].update(x15=stats(g.net15), x2=stats(g.net2), mirror_x1=stats(-g.gross - COST_BP),
                           outright10_gross=stats(g.gross_out10), hedge5_leg_gross=stats(g.gross_hedge),
                           control_outright10_gross=stats(c.gross_out10), control_hedge5_gross=stats(c.gross_hedge),
                           new_issue=dict(n=int(len(gn)), strat_diff=strat_diff(gn, c), gross=stats(gn.gross)),
                           reopening=dict(n=int(len(gr)), strat_diff=strat_diff(gr, c), gross=stats(gr.gross)),
                           per_year_net={int(k): round(float(v), 1) for k, v in g.groupby(g.date.dt.year).net.mean().items()},
                           by_era_diff={era: strat_diff(g[m_], c[m_c]) for era, m_, m_c in (
                               ("1990-2008", g.date < "2009-01-01", c.date < "2009-01-01"), ("2009+", g.date >= "2009-01-01", c.date >= "2009-01-01"))})
            if cn == "C1_recovery":
                # issue-date-excluded recovery: T close -> close of the day before issue (or T+5, whichever first)
                vals = []
                for p in g.pos:
                    i_iss = idx.get(iss[p]); end = min(p + 5, (i_iss - 1) if i_iss is not None else p + 5)
                    sp = leg_returns(f, p, end)[0]
                    if np.isfinite(sp): vals.append(sp)
                out[cn]["issue_excluded_gross"] = stats(vals)
    return out, e, ctrl


def maxstat(f, ev_pos, obs_by_cell, shifts=range(8, 121)):
    """shift the auction calendar by k business days; drop shifts where > 10% of shifted dates fall within 5 bd
    of a real auction (resonance); rebuild the control per shift with the same rule; null = max over cells of |t|."""
    n = len(f); real = np.zeros(n, bool)
    for e in ev_pos: real[max(0, e - 5):min(n, e + 6)] = True
    mx = []; used = 0
    for k in list(shifts) + [-k for k in shifts]:
        sh = [p + k for p in ev_pos if 0 <= p + k < n]
        if np.mean([real[p] for p in sh]) > 0.10: continue
        used += 1; vals = []
        e = rows_for(f, sh, CELLS, "shift")
        for cn, (a, b, s) in CELLS.items():
            c = rows_for(f, control_positions(f, sh, a, b), {cn: (a, b, s)}, "ctrl")
            r = strat_diff(e[e.cell == cn], c); vals.append(abs(r.get("t") or 0.0))
        mx.append(max(vals))
    mx = np.array(mx)
    return {"shifts_used": int(used), "null_max_t_95pct": float(np.quantile(mx, 0.95)) if len(mx) else None,
            "p_per_cell": {cn: float((np.sum(mx >= t) + 1) / (len(mx) + 1)) for cn, t in obs_by_cell.items()}}


if __name__ == "__main__":
    res = {"unsealed": UNSEAL}
    y10, y5 = load_yield("10y"), load_yield("5y")
    if not UNSEAL:
        y10, y5 = y10[y10.index <= SERIES_CUT], y5[y5.index <= SERIES_CUT]
        cleared = list(CELLS)
    else:
        isr = json.load(open(os.path.join(HERE, "results", "r80_auction_is.json")))
        cleared = [c for c, ok in isr["verdict"].items() if ok]
        if not cleared: raise SystemExit("no cell cleared IS; holdout stays sealed")
        y10, y5 = y10[y10.index >= pd.Timestamp("2019-12-01")], y5[y5.index >= pd.Timestamp("2019-12-01")]
    f = make_frame(y10, y5); ev = auctions10()
    ev = ev[(ev.date >= IS_EV_START) & (ev.date <= IS_EV_END)] if not UNSEAL else ev[ev.date >= OOS_EV_START]
    if not UNSEAL:
        assert f.index.max() <= SERIES_CUT
    cells = dict(CELLS); cells.update(READ)
    out, e, ctrl = evaluate(f, ev, cells, "10y")
    pos_all = np.arange(0, len(f) - 5, 5)
    out["unconditional_5d_spread_long"] = stats(rows_for(f, pos_all.tolist(), {"u": (0, 5, +1)}, "u").gross)
    out["unconditional_5d_outright10_long"] = stats(rows_for(f, pos_all.tolist(), {"u": (0, 5, +1)}, "u").gross_out10)
    res["10y_spread"] = out
    print(f"=== 10y-vs-5y spread ({'OOS' if UNSEAL else 'IS'}) auctions {out['n_auctions']} {out['span']} ===")
    for cn in cells:
        v = out[cn]
        print(f"  {cn:16s} net {json.dumps(v['x1'], default=float)}\n      strat_diff {json.dumps(v['strat_diff'], default=float)} diff_halves {v['diff_halves']} n_control {v['n_control']} control_gross {v['control_gross'].get('mean_bp', float('nan')):+.2f}")
        if "x2" in v:
            print(f"      x2 {v['x2'].get('mean_bp', float('nan')):+.1f} mirror {v['mirror_x1'].get('mean_bp', float('nan')):+.1f} outright10 {v['outright10_gross'].get('mean_bp', float('nan')):+.1f} (ctrl {v['control_outright10_gross'].get('mean_bp', float('nan')):+.1f}) hedge5 {v['hedge5_leg_gross'].get('mean_bp', float('nan')):+.1f} (ctrl {v['control_hedge5_gross'].get('mean_bp', float('nan')):+.1f})")
            print(f"      new_issue {json.dumps(v['new_issue']['strat_diff'], default=float)} reopening {json.dumps(v['reopening']['strat_diff'], default=float)}")
            print(f"      era {json.dumps(v['by_era_diff'], default=float)}\n      per-year {v['per_year_net']}" + (f"\n      issue_excluded {json.dumps(v['issue_excluded_gross'], default=float)}" if 'issue_excluded_gross' in v else ""))
    print("  unconditional 5d spread long:", out["unconditional_5d_spread_long"], "\n  unconditional 5d outright10 long:", out["unconditional_5d_outright10_long"])
    if not UNSEAL:
        idx = {d: i for i, d in enumerate(f.index)}; ev_pos = [idx[d] for d in ev.date if d in idx]
        obs = {cn: (out[cn]["strat_diff"].get("t") or 0.0) for cn in CELLS}       # signed, hypothesised direction
        res["maxstat"] = maxstat(f, ev_pos, obs); print("  maxstat:", res["maxstat"])
    passes = {}
    for cn in cleared:
        v = out[cn]; s, x2, sd = v["x1"], v["x2"], v["strat_diff"]; floor = 2.0 if UNSEAL else T_FLOOR
        own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
        p_ok = True if UNSEAL else res["maxstat"]["p_per_cell"][cn] < 0.05
        x15_ok = v["x15"].get("mean_bp", -1) > 0 if UNSEAL else True
        roll_ok = True if cn != "C1_recovery" else (v["new_issue"]["strat_diff"].get("diff_bp", -1) > 0 and v["reopening"]["strat_diff"].get("diff_bp", -1) > 0)
        passes[cn] = bool(s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and s.get("pf", 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
                          and x2.get("mean_bp", -1) > 0 and x15_ok and sd.get("diff_bp", -1) > 0 and d_t >= floor and v["diff_halves"] == [1.0, 1.0] and p_ok and roll_ok)
    res["verdict"] = passes
    print(f"\nATTEMPT 58 {'OOS' if UNSEAL else 'IS'} VERDICT: {passes}")
    json.dump(res, open(os.path.join(HERE, "results", f"r80_auction_{'oos' if UNSEAL else 'is'}.json"), "w"), indent=1, default=float)
