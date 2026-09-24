"""Attempt 62 (Round 86) v2 - after the critic pass: long the par 10-year from the T-1 close to the T close on central-
bank purchase-operation days whose sector CONTAINS the 10-year point. Fed = US primary (DGS10), BoE APF = UK
replication (IUDMNPY). Two selectable cells, Bonferroni-2 floor 2.24 IS / 2.0 OOS.

CONTROL CLOCK (v2): FAR-SECTOR purchase-operation days of the same sub-programme / phase (the central bank chose them
by the same published schedule rule; they are ordinary market days), year-stratified differential. Adjacent-sector
days (US: sector touching 5.5-9.5y or 10-17y without containing the 10y; UK: 10-25y bucket) are the GRADIENT read
and never enter the control. Non-operation days of the programme span are a read-only clock with FOMC, first-Friday
and holiday-adjacent days excluded (v1's clock, shown for the record).
NULL (v2): year-stratified permutation of the in-sector label among the in-sector + far-sector purchase days of the
same year, 500 draws, same statistic; p = share of draws with t >= observed. The +-4..+-13 bd shift clocks are a
read-only calendar check with the identical control construction.
BLOCKING (locality): the in-sector differential must exceed the adjacent-sector differential (both vs far-sector
days, same strata). 2y / 5y / 30y same-day yield-change differentials are read-only.
DYSFUNCTION RULE (pre-registered, both stages, both markets): operation days with >= 3 purchase operations (Mar-Apr
2020 Fed; the three-bucket BoE days of 2020) are excluded from events and controls; the full set is a read-only.
Sub-programme spans; SMALL_VALUE and RMP_BILLS phases dropped. Cut 2019-05-06. Family verdict at the sealed stage over
the markets that cleared IS: REPLICATES iff all pass, PARTIAL iff some, FAILS iff none.
Outputs results/r86_cbops_{is,oos}.json. OOS only with UNSEAL_OK=1 --unseal.
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from run_r81_monthend import stats, strat_diff, diff_halves  # noqa: E402
from run_r83_monthend_global import mod_dur, load_yield  # noqa: E402
from fomc_dates import FOMC_DATES  # noqa: E402

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
CUT = pd.Timestamp("2019-05-06")
COST_BP = 3.0
T_FLOOR_IS, T_FLOOR_OOS = 2.24, 2.0
CLOCKS = [k for k in range(-13, 14) if abs(k) >= 4]
N_PERM = 500
MAX_OPS_PER_DAY = 3           # >= 3 purchase ops on a day = dysfunction rule (excluded)
DROP_PHASES = ("SMALL_VALUE", "RMP_BILLS")
UK_IN = ("5-10y", "3-10y", "7-15y", "7-20y"); UK_ADJ = ("10-25y",)
TAG = "r86_cbops"
RNG = np.random.default_rng(20260924)


def sha256(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()


def load_av(fname):
    d = pd.read_csv(os.path.join(HERE, "data", fname)); d = d.iloc[:, :2]; d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def classify_sector(lo, hi):
    if lo <= 10.0 and hi >= 9.5: return "in"
    if (hi >= 5.5 and lo <= 9.5) or (lo <= 17.0 and hi >= 10.0): return "adjacent"
    return "far"


def fed_events():
    f = pd.read_csv(os.path.join(HERE, "data", "fed_tsy_operations.csv")); f["operation_date"] = pd.to_datetime(f.operation_date).dt.normalize()
    f["ptype"] = f.operation_type.str.lower(); f["sub"] = f.sub_programme.astype(str)
    f = f[~f["sub"].str.upper().str.startswith(DROP_PHASES)]
    nomp = f[(f.security_type == "nominal") & f.ptype.str.contains("purchase")].copy()
    nomp["cls"] = [classify_sector(a, b) for a, b in zip(nomp.sector_lo_y, nomp.sector_hi_y)]
    nomp["par"] = pd.to_numeric(nomp.total_par_amount_accepted.astype(str).str.replace(",", ""), errors="coerce")
    per_day = nomp.groupby("operation_date").agg(n_pur=("operation_id", "size"), sub=("sub", "first"), par=("par", "sum"),
                                                 cls=("cls", lambda s: "in" if (s == "in").any() else ("adjacent" if (s == "adjacent").any() else "far")))
    per_day["dysfunction"] = per_day.n_pur >= MAX_OPS_PER_DAY
    sale_days = set(f[(f.security_type == "nominal") & f.ptype.str.contains("sale")].operation_date)
    per_day["sale_same_day"] = per_day.index.isin(sale_days)
    spans = nomp.groupby("sub").operation_date.agg(["min", "max"])
    contains5 = nomp[(nomp.sector_lo_y <= 5.0) & (nomp.sector_hi_y >= 5.0) & (nomp.cls != "in")]
    return dict(days=per_day, spans=spans, allop=set(f.operation_date), sale_days=sorted(sale_days), mid_days=sorted(set(contains5.operation_date) - set(per_day[per_day.cls == "in"].index)))


def boe_events():
    b = pd.read_csv(os.path.join(HERE, "data", "boe_apf_gilt_operations.csv")); b["operation_date"] = pd.to_datetime(b.operation_date).dt.normalize()
    pur = b[b.operation_type.str.lower().str.contains("purchase") & (b.security_type.astype(str).str.lower() == "conventional") & (b.programme == "APF_QE")].copy()
    pur["cls"] = np.where(pur.maturity_bucket.isin(UK_IN), "in", np.where(pur.maturity_bucket.isin(UK_ADJ), "adjacent", "far"))
    pur["par"] = pd.to_numeric(pur.allocated_proceeds_gbp_m, errors="coerce")
    d = sorted(set(pur.operation_date)); phases = []; s0 = d[0]; prev = d[0]; k = 1; lab = {}
    for x in d[1:]:
        if (x - prev).days > 120: phases.append((f"phase{k}", s0, prev)); k += 1; s0 = x
        prev = x
    phases.append((f"phase{k}", s0, prev))
    for name, a, bb in phases:
        for x in d:
            if a <= x <= bb: lab[x] = name
    pur["sub"] = pur.operation_date.map(lab)
    per_day = pur.groupby("operation_date").agg(n_pur=("maturity_bucket", "size"), sub=("sub", "first"), par=("par", "sum"),
                                                cls=("cls", lambda s: "in" if (s == "in").any() else ("adjacent" if (s == "adjacent").any() else "far")))
    per_day["dysfunction"] = per_day.n_pur >= MAX_OPS_PER_DAY; per_day["sale_same_day"] = False
    spans = pd.DataFrame([(a, bb) for _, a, bb in phases], columns=["min", "max"], index=[n for n, _, _ in phases])
    return dict(days=per_day, spans=spans, allop=set(b.operation_date), sale_days=[], mid_days=[])


def day_return(y, freq, d, years=10):
    if d not in y.index: return None
    p = y.index.get_loc(d)
    if p == 0: return None
    y0, y1 = y.iloc[p - 1], y.iloc[p]; days = (y.index[p] - y.index[p - 1]).days
    if days > 6: return None
    px = -mod_dur(y0, years, freq) * (y1 - y0) / 100.0 * 1e4; cy = y0 / 100.0 * days / 365.0 * 1e4
    return dict(date=d, d0=y.index[p - 1], y0=float(y0), dy_bp=float((y1 - y0) * 100), price=px, carry=cy, gross=px + cy, net=px + cy - COST_BP,
                net15=px + cy - 1.5 * COST_BP, net2=px + cy - 2 * COST_BP)


def rows(y, freq, dates, tag, shift=0, years=10):
    out = []
    for d in dates:
        if shift:
            if d not in y.index: continue
            p = y.index.get_loc(d) + shift
            if p < 1 or p >= len(y): continue
            d = y.index[p]
        r = day_return(y, freq, d, years)
        if r: r["tag"] = tag; out.append(r)
    return pd.DataFrame(out, columns=["date", "d0", "y0", "dy_bp", "price", "carry", "gross", "net", "net15", "net2", "tag"])


def nonop_days(y, spans, allop, stage_oos):
    """v1's clock, read-only: programme-span business days with no operation, excluding FOMC statement days, first
    Fridays (payrolls) and holiday-adjacent sessions."""
    fomc = set(pd.to_datetime(list(FOMC_DATES)).normalize()); out = []
    for _, (a, b) in spans.iterrows():
        idx = y.index[(y.index >= a) & (y.index <= b)]
        for d in idx:
            if d in allop or d in fomc: continue
            if d.dayofweek == 4 and d.day <= 7: continue
            if (d.month, d.day) in {(7, 3), (12, 24), (12, 26), (12, 31), (1, 2)} or (d.month == 11 and d.dayofweek == 4 and 23 <= d.day <= 29): continue
            out.append(d)
    return sorted(set(out))


def stage_filter(days, stage_oos):
    return days[(days.index >= CUT) == stage_oos]


def perm_null(e_in, e_far, y, n_perm):
    """year-stratified relabelling of the in-sector label among in + far purchase days; returns array of t."""
    pool = pd.concat([e_in.assign(lbl=1), e_far.assign(lbl=0)]); pool["yr"] = pool.date.dt.year; ts = []
    groups = [(g.index.values, int(g.lbl.sum())) for _, g in pool.groupby("yr")]
    for _ in range(n_perm):
        lab = np.zeros(len(pool), bool); idx_map = {i: k for k, i in enumerate(pool.index)}
        for idx, n_in in groups:
            pick = RNG.choice(idx, size=n_in, replace=False)
            for i in pick: lab[idx_map[i]] = True
        r = strat_diff(pool[lab], pool[~lab]); ts.append(r.get("t") if r.get("t") is not None else 0.0)
    return np.array(ts, float)


def evaluate(code, y, freq, meta, aux=None, stage_oos=False):
    days = stage_filter(meta["days"], stage_oos); spans = meta["spans"]
    spans = spans[(spans["max"] >= CUT) if stage_oos else (spans["min"] < CUT)].copy()
    if stage_oos: spans["min"] = spans["min"].where(spans["min"] >= CUT, CUT)
    else: spans["max"] = spans["max"].where(spans["max"] < CUT, CUT - pd.Timedelta(days=1))
    ok = days[~days.dysfunction]
    ev_d = sorted(ok[ok.cls == "in"].index); far_d = sorted(ok[ok.cls == "far"].index); adj_d = sorted(ok[ok.cls == "adjacent"].index)
    e = rows(y, freq, ev_d, "event"); c = rows(y, freq, far_d, "far"); a = rows(y, freq, adj_d, "adjacent")
    out = dict(n_events=int(len(ev_d)), n_valid=int(len(e)), n_far=int(len(c)), n_adjacent=int(len(a)), n_dysfunction_excluded=int(days.dysfunction.sum()),
               spans={i: [str(x.date()), str(z.date())] for i, (x, z) in spans.iterrows()})
    if len(e) < 10 or len(c) < 10: return out
    out.update(span=[str(e.date.min().date()), str(e.date.max().date())], x1=stats(e.net), x15=stats(e.net15), x2=stats(e.net2), gross=stats(e.gross),
               price_component=stats(e.price), control_price=stats(c.price), strat_diff=strat_diff(e, c), diff_halves=diff_halves(e, c),
               mirror_x1=stats(-e.gross - COST_BP), yield_change_diff_bp=strat_diff(e, c, col="dy_bp"),
               adjacent=dict(x1=stats(a.net) if len(a) else {}, strat_diff=strat_diff(a, c) if len(a) else {}, yield_change_diff_bp=strat_diff(a, c, col="dy_bp") if len(a) else {}),
               far_x1=stats(c.net))
    out["blocking"] = dict(in_diff=out["strat_diff"].get("diff_bp"), adjacent_diff=out["adjacent"]["strat_diff"].get("diff_bp"),
                           passed=bool(out["strat_diff"].get("diff_bp", -9) > (out["adjacent"]["strat_diff"].get("diff_bp") if out["adjacent"]["strat_diff"].get("n_event") else -9e9)))
    # read-onlys
    em = e.merge(days[["sub", "par", "sale_same_day", "n_pur"]], left_on="date", right_index=True, how="left")
    out["by_programme"] = {str(k): dict(n=int(len(g)), net_mean=float(g.net.mean()), strat_diff=strat_diff(g, c[c.date.isin(set(days[days["sub"] == k].index))] if len(c) else c)) for k, g in em.groupby("sub")}
    out["par_weighted_net_bp"] = float(np.average(em.net, weights=em.par.fillna(0) + 1e-9)) if em.par.notna().any() else None
    out["twist_days_sale_same_day"] = dict(n=int(em.sale_same_day.sum()), x1=stats(em[em.sale_same_day].net) if em.sale_same_day.sum() >= 10 else {})
    out["multi_op_days_lt3"] = dict(n=int((em.n_pur >= 2).sum()), x1=stats(em[em.n_pur >= 2].net) if (em.n_pur >= 2).sum() >= 10 else {})
    dys = rows(y, freq, sorted(days[days.dysfunction & (days.cls == "in")].index), "dysfunction")
    out["dysfunction_days_readonly"] = dict(n=int(len(dys)), x1=stats(dys.net) if len(dys) >= 10 else {}, strat_diff=strat_diff(dys, c) if len(dys) >= 3 else {})
    pre = rows(y, freq, ev_d, "pre", shift=-1); post = rows(y, freq, ev_d, "post", shift=+1)
    cpre = rows(y, freq, far_d, "cpre", shift=-1); cpost = rows(y, freq, far_d, "cpost", shift=+1)
    out["pre_op_T-2_to_T-1"] = dict(x1=stats(pre.net) if len(pre) else {}, strat_diff=strat_diff(pre, cpre) if len(pre) and len(cpre) else {})
    out["post_op_T_to_T+1"] = dict(x1=stats(post.net) if len(post) else {}, strat_diff=strat_diff(post, cpost) if len(post) and len(cpost) else {})
    nd = nonop_days(y, spans, meta["allop"], stage_oos); cn = rows(y, freq, nd, "nonop")
    out["nonop_clock_readonly"] = dict(n_control=int(len(cn)), strat_diff=strat_diff(e, cn) if len(cn) >= 10 else {}, diff_halves=diff_halves(e, cn) if len(cn) >= 10 else [])
    # controls that are neither T-1 nor T+1 of an in-sector event (concession / reversal leakage check, read-only)
    nbr = set()
    for d in ev_d:
        if d in y.index:
            p = y.index.get_loc(d); nbr |= {y.index[q] for q in (p - 1, p + 1) if 0 <= q < len(y)}
    c_nb = c[~c.date.isin(nbr)]
    out["far_ex_T-1_T+1_readonly"] = dict(n_control=int(len(c_nb)), strat_diff=strat_diff(e, c_nb) if len(c_nb) >= 10 else {})
    if len(e) >= 10:
        i = e.net.abs().idxmax(); out["drop_one_max"] = dict(dropped_date=str(e.loc[i, "date"].date()), dropped_net_bp=float(e.loc[i, "net"]), x1=stats(e.drop(i).net), strat_diff=strat_diff(e.drop(i), c))
    out["per_year_net"] = {int(k): round(float(v), 1) for k, v in e.groupby(e.date.dt.year).net.mean().items()}
    out["weekday_mix"] = dict(events=e.date.dt.dayofweek.value_counts().sort_index().to_dict(), far=c.date.dt.dayofweek.value_counts().sort_index().to_dict())
    if aux:
        for name, ya, fq, yrs in aux.get("tenors", []):
            ea = rows(ya, fq, ev_d, "event", years=yrs); ca = rows(ya, fq, far_d, "far", years=yrs)
            out[f"{name}_same_days"] = dict(n=int(len(ea)), yield_change_diff_bp=strat_diff(ea, ca, col="dy_bp") if len(ea) and len(ca) else {}, price_diff=strat_diff(ea, ca) if len(ea) and len(ca) else {})
        md = [d for d in aux.get("mid_days", []) if (d >= CUT) == stage_oos and d in ok.index]
        if md:
            e10 = rows(y, freq, md, "mid"); out["contains_5y_days_10y"] = dict(n=int(len(e10)), yield_change_diff_bp=strat_diff(e10, c, col="dy_bp") if len(e10) else {})
            for name, ya, fq, yrs in aux.get("tenors", []):
                ea = rows(ya, fq, md, "mid", years=yrs); ca = rows(ya, fq, far_d, "far", years=yrs)
                out[f"contains_5y_days_{name}"] = dict(n=int(len(ea)), yield_change_diff_bp=strat_diff(ea, ca, col="dy_bp") if len(ea) and len(ca) else {})
        sd = [d for d in aux.get("sale_days", []) if (d >= CUT) == stage_oos]
        for name, ya, fq, yrs in aux.get("tenors", []):
            if name == "2y" and sd:
                es = rows(ya, fq, sd, "sale", years=yrs); cs = rows(ya, fq, far_d, "far", years=yrs)
                out["mep_sale_days_2y"] = dict(n=int(len(es)), yield_change_diff_bp=strat_diff(es, cs, col="dy_bp") if len(es) and len(cs) else {})
        for name, ds in aux.get("overlaps", {}).items():
            hit = e.date.isin(set(ds)); hitc = c.date.isin(set(ds))
            out[f"ex_{name}"] = dict(n_flagged_events=int(hit.sum()), n_flagged_far=int(hitc.sum()), x1=stats(e[~hit].net), strat_diff=strat_diff(e[~hit], c[~hitc]))
    if not stage_oos:
        t_obs = out["strat_diff"].get("t") or -9
        ts = perm_null(e, c, y, N_PERM)
        out["permutation_null"] = dict(n_perm=int(len(ts)), obs_t=float(t_obs), p=float((np.sum(ts >= t_obs) + 1) / (len(ts) + 1)), null_t_quantiles={q: round(float(np.quantile(ts, q)), 2) for q in (0.5, 0.9, 0.95, 0.99)})
        maxima = []; trueset = set(ev_d) | set(far_d) | set(adj_d)
        for k in CLOCKS:
            pe = rows(y, freq, ev_d, "placebo", shift=k); pe = pe[~pe.date.isin(trueset)]
            pc = rows(y, freq, far_d, "pfar", shift=k); pc = pc[~pc.date.isin(trueset)]
            r = strat_diff(pe, pc) if len(pe) >= 10 and len(pc) >= 10 else {}
            maxima.append(dict(k=k, n_e=int(len(pe)), n_c=int(len(pc)), t=r.get("t"), strata=r.get("n_event")))
        valid = [abs(m["t"]) for m in maxima if m["t"] is not None and m["n_e"] >= 0.8 * len(e)]
        out["shift_clocks_readonly"] = dict(clocks=maxima, n_valid=len(valid), obs_t=float(t_obs), p=float((np.sum(np.array(valid) >= t_obs) + 1) / (len(valid) + 1)) if valid else None)
    return out


def market_passes(out, stage_oos):
    s, sd = out.get("x1", {}), out.get("strat_diff", {}); floor = T_FLOOR_OOS if stage_oos else T_FLOOR_IS
    own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
    base = (s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("pf") or 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
            and out.get("x2", {}).get("mean_bp", -1) > 0 and sd.get("diff_bp", -1) > 0 and d_t >= floor and out.get("blocking", {}).get("passed"))
    if stage_oos: return bool(base and out.get("x15", {}).get("mean_bp", -1) > 0)
    return bool(base and out.get("diff_halves") == [1.0, 1.0] and out.get("permutation_null", {}).get("p", 1.0) < 0.05)


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)): return bool(o)
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, pd.Timestamp): return str(o.date())
    return o


def main():
    res = {"unsealed": UNSEAL, "cut": str(CUT.date()), "markets": {}, "file_sha256": {f: sha256(os.path.join(HERE, "data", f)) for f in ("fed_tsy_operations.csv", "boe_apf_gilt_operations.csv")}}
    isr = None; candidates = None
    if UNSEAL:
        with open(os.path.join(HERE, "results", f"{TAG}_is.json")) as f: isr = json.load(f)
        assert isr["file_sha256"] == res["file_sha256"], "operation files changed since the IS run"
        candidates = [m for m, ok in isr["verdict"].items() if ok]
        if not candidates: raise SystemExit("no market cleared IS; holdouts stay sealed")
    us10 = load_yield("fred_DGS10.csv"); us2 = load_yield("fred_DGS2.csv"); us5 = load_av("UST05Y_daily_av.csv"); us30 = load_av("UST30Y_daily_av.csv"); uk10 = load_yield("yield_UK10Y_daily.csv")
    fed = fed_events(); boe = boe_events()
    auc = json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json")))
    auc10 = set(pd.to_datetime([r["auction_date"] for r in auc if str(r.get("term", "")).startswith(("10", "9-Year"))]).normalize())
    me = set(); per = us10.index.to_period("M")
    for m in per.unique():
        pos = np.where(per == m)[0]; me |= {us10.index[q] for q in pos[-4:]}
    fomc = set(pd.to_datetime(list(FOMC_DATES)).normalize())
    aux_us = dict(tenors=[("2y", us2, 2, 2), ("5y", us5, 2, 5), ("30y", us30, 2, 30)], mid_days=fed["mid_days"], sale_days=fed["sale_days"], overlaps={"auction_days_10y": auc10, "month_end_T-3_T": me, "fomc_days": fomc})
    aux_uk = dict(tenors=[], overlaps={"fomc_days": fomc})
    for code, y, freq, meta, aux in (("US", us10, 2, fed, aux_us), ("UK", uk10, 2, boe, aux_uk)):
        if UNSEAL and code not in candidates: res["markets"][code] = {"skipped": "did not clear IS; holdout stays sealed"}; continue
        out = evaluate(code, y, freq, meta, aux=aux, stage_oos=UNSEAL); res["markets"][code] = out
        print(f"=== {code} ({'OOS' if UNSEAL else 'IS'}) in-sector days {out['n_events']} valid {out.get('n_valid')} far-control {out.get('n_far')} adjacent {out.get('n_adjacent')} dysfunction-excluded {out['n_dysfunction_excluded']} spans {out['spans']}")
        if "x1" in out:
            print(f"  C1 net {json.dumps(clean(out['x1']))}\n     price {out['price_component']['mean_bp']:+.1f} far-control price {out['control_price'].get('mean_bp', float('nan')):+.1f} (far net {out['far_x1'].get('mean_bp', float('nan')):+.1f})\n     strat_diff {json.dumps(clean(out['strat_diff']))} diff_halves {out['diff_halves']} x15 {out['x15']['mean_bp']:+.1f} x2 {out['x2']['mean_bp']:+.1f} mirror {out['mirror_x1']['mean_bp']:+.1f}\n     yield-change diff {json.dumps(clean(out['yield_change_diff_bp']))}\n     adjacent {json.dumps(clean(out['adjacent']['strat_diff']))} blocking {json.dumps(clean(out['blocking']))}\n     non-op clock (read-only) {json.dumps(clean(out['nonop_clock_readonly']))}\n     pre-op {json.dumps(clean(out['pre_op_T-2_to_T-1']['strat_diff']))} post-op {json.dumps(clean(out['post_op_T_to_T+1']['strat_diff']))}\n     by programme {json.dumps(clean({k: (v['n'], round(v['net_mean'], 1), v['strat_diff'].get('t')) for k, v in out['by_programme'].items()}))}\n     par-weighted net {out['par_weighted_net_bp']} twist {json.dumps(clean(out['twist_days_sale_same_day']))} dysfunction {json.dumps(clean(out['dysfunction_days_readonly']))}\n     drop-one-max {json.dumps(clean(out.get('drop_one_max', {})))}\n     per-year {out['per_year_net']} weekday {out['weekday_mix']}")
            for k in ("2y_same_days", "5y_same_days", "30y_same_days", "contains_5y_days_10y", "contains_5y_days_5y", "mep_sale_days_2y", "ex_auction_days_10y", "ex_month_end_T-3_T", "ex_fomc_days"):
                if k in out: print(f"     {k} {json.dumps(clean(out[k]))}"[:420])
            if "permutation_null" in out: print("  permutation null:", clean(out["permutation_null"]))
            if "shift_clocks_readonly" in out: print("  shift clocks (read-only):", clean({k: v for k, v in out["shift_clocks_readonly"].items() if k != "clocks"}))
    passes = {c: market_passes(o, UNSEAL) for c, o in res["markets"].items() if "x1" in o}
    res["verdict"] = passes
    if not UNSEAL:
        res["candidates"] = [m for m, ok in passes.items() if ok]; res["family"] = "FAILS at IS stage (no candidate)" if not res["candidates"] else f"CANDIDATES {res['candidates']} - verdict at the sealed stage"
    else:
        n = sum(passes.values()); res["family"] = "REPLICATES" if (n == len(candidates) and n >= 1) else ("PARTIAL" if n >= 1 else "FAILS")
    print(f"\n{TAG} {'OOS' if UNSEAL else 'IS'} VERDICT per market: {passes}\nFAMILY: {res['family']}")
    with open(os.path.join(HERE, "results", f"{TAG}_{'oos' if UNSEAL else 'is'}.json"), "w") as f: json.dump(clean(res), f, indent=1)


if __name__ == "__main__":
    main()
