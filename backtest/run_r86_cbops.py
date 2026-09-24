"""Attempt 62 (Round 86): long the par 10-year from the T-1 close to the T close on central-bank in-sector purchase-
operation days. Fed SOMA Treasury operations (nominal purchases whose sector overlaps 7-10y) = US primary, BoE APF gilt
purchases in a bucket containing the 10-year point = UK replication. Two selectable cells (one per market), Bonferroni-2
floor 2.24 IS / 2.0 OOS. Era-internal controls: business days inside each programme's span with no operation of any
type, each used once (one-day windows, non-overlapping by construction), year-stratified differential. Placebo-clock
max-stat over k in +-4..+-13 bd with the weekly-cadence resonance guard (placebo days on a true operation day dropped).
US blocking cross-section (local supply): on 7-10y days the 10y yield change (event minus control) must be more
negative than the 2y's; on 4-5.5y-only days the 5y's must be more negative than the 10y's. UK blocking: in-bucket
differential > out-of-bucket purchase-day differential. Family verdict at the sealed stage. Cut 2019-05-06.
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

UNSEAL = "--unseal" in sys.argv and os.environ.get("UNSEAL_OK") == "1"
CUT = pd.Timestamp("2019-05-06")
COST_BP = 3.0
T_FLOOR_IS, T_FLOOR_OOS = 2.24, 2.0
CLOCKS = [k for k in range(-13, 14) if abs(k) >= 4]
TAG = "r86_cbops"


def sha256(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()


def load_av(fname):
    d = pd.read_csv(os.path.join(HERE, "data", fname)); d = d.iloc[:, :2]; d.columns = ["date", "y"]
    d["date"] = pd.to_datetime(d.date); d["y"] = pd.to_numeric(d.y, errors="coerce")
    return d.dropna().sort_values("date").drop_duplicates("date").set_index("date").y


def fed_events():
    f = pd.read_csv(os.path.join(HERE, "data", "fed_tsy_operations.csv")); f["operation_date"] = pd.to_datetime(f.operation_date)
    f["ptype"] = f.operation_type.str.lower(); ov = f.overlaps_7_10y.astype(str).str.lower().isin(["true", "1", "yes"])
    nomp = f[(f.security_type == "nominal") & f.ptype.str.contains("purchase")]
    insec = nomp[ov[nomp.index]]
    mid = nomp[(nomp.sector_lo_y <= 5.5) & (nomp.sector_hi_y >= 4.0) & ~ov[nomp.index]]   # 4-5.5y covered, 7-10y not
    outsec = nomp[~ov[nomp.index]]
    sales2 = f[(f.security_type == "nominal") & f.ptype.str.contains("sale") & (f.sector_hi_y <= 3.5)]
    prog = f.groupby("programme").operation_date.agg(["min", "max"])
    allop = set(f.operation_date.dt.normalize())
    second = f.groupby("operation_date").size(); second = set(second[second > 1].index)
    ev = insec.groupby("operation_date").agg(programme=("programme", "first"), n_ops=("operation_id", "size"), par=("total_par_amount_accepted", "sum")).reset_index()
    ev["second_op_day"] = ev.operation_date.isin(second)
    return dict(events=ev, mid_days=sorted(set(mid.operation_date)), out_days=sorted(set(outsec.operation_date) - set(insec.operation_date)),
                sale_days=sorted(set(sales2.operation_date)), prog=prog, allop=allop)


def boe_events():
    b = pd.read_csv(os.path.join(HERE, "data", "boe_apf_gilt_operations.csv")); b["operation_date"] = pd.to_datetime(b.operation_date)
    pur = b[b.operation_type.str.lower().str.contains("purchase") & (b.security_type.astype(str).str.lower() == "conventional") & (b.programme == "APF_QE")]
    inb = pur[pur.residual_maturity_min_y.le(10) & pur.residual_maturity_max_y.ge(10)]
    out = pur[~pur.index.isin(inb.index)]
    prog = pur.assign(era=pur.bucket_regime).groupby("era").operation_date.agg(["min", "max"])
    # programme spans: contiguous purchase phases (gap > 120 days starts a new phase)
    d = sorted(set(pur.operation_date)); spans = []; s0 = d[0]; prev = d[0]
    for x in d[1:]:
        if (x - prev).days > 120: spans.append((s0, prev)); s0 = x
        prev = x
    spans.append((s0, prev)); prog = pd.DataFrame(spans, columns=["min", "max"], index=[f"phase{i+1}" for i in range(len(spans))])
    allop = set(b.operation_date.dt.normalize())
    ev = inb.groupby("operation_date").agg(programme=("bucket_regime", "first"), n_ops=("maturity_bucket", "size"), par=("allocated_proceeds_gbp_m", "sum"), bucket=("maturity_bucket", "first")).reset_index()
    ev["second_op_day"] = ev.n_ops > 1
    return dict(events=ev, mid_days=[], out_days=sorted(set(out.operation_date) - set(inb.operation_date)), sale_days=[], prog=prog, allop=allop)


def day_return(y, freq, d):
    """one-day par-bond return components ending at the close of date d (previous observation to d)."""
    if d not in y.index: return None
    p = y.index.get_loc(d)
    if p == 0: return None
    y0, y1 = y.iloc[p - 1], y.iloc[p]; days = (y.index[p] - y.index[p - 1]).days
    if days > 6: return None
    px = -mod_dur(y0, 10, freq) * (y1 - y0) / 100.0 * 1e4; cy = y0 / 100.0 * days / 365.0 * 1e4
    return dict(date=d, d0=y.index[p - 1], y0=float(y0), dy_bp=float((y1 - y0) * 100), price=px, carry=cy, gross=px + cy, net=px + cy - COST_BP,
                net15=px + cy - 1.5 * COST_BP, net2=px + cy - 2 * COST_BP)


def rows(y, freq, dates, tag, shift=0):
    out = []
    for d in dates:
        if shift:
            if d not in y.index: continue
            p = y.index.get_loc(d) + shift
            if p < 1 or p >= len(y): continue
            d = y.index[p]
        r = day_return(y, freq, d)
        if r: r["tag"] = tag; out.append(r)
    return pd.DataFrame(out)


def control_days(y, prog, allop, exclude=()):
    """era-internal control days: business days of the yield series inside each programme span, not an operation day of any
    type, not in `exclude`; each used once."""
    ex = set(pd.to_datetime(list(exclude))); out = []
    for _, (a, b) in prog.iterrows():
        idx = y.index[(y.index >= a) & (y.index <= b)]
        out += [d for d in idx if d not in allop and d not in ex]
    return sorted(set(out))


def evaluate(code, y, freq, ev, meta, aux=None, stage_oos=False):
    dates = sorted(set(ev.operation_date)); dates = [d for d in dates if (d >= CUT) == stage_oos]
    prog = meta["prog"]; prog = prog[(prog["max"] >= CUT) if stage_oos else (prog["min"] < CUT)]
    prog = prog.assign(**{"min": prog["min"].clip(lower=CUT) if stage_oos else prog["min"], "max": prog["max"].clip(upper=CUT - pd.Timedelta(days=1)) if not stage_oos else prog["max"]})
    e = rows(y, freq, dates, "event"); out = dict(n_events=int(len(dates)), n_valid=int(len(e)), programme_spans={i: [str(a.date()), str(b.date())] for i, (a, b) in prog.iterrows()})
    if len(e) < 10: return out
    cd = control_days(y, prog, meta["allop"]); c = rows(y, freq, cd, "control")
    out.update(span=[str(e.date.min().date()), str(e.date.max().date())], x1=stats(e.net), x15=stats(e.net15), x2=stats(e.net2), gross=stats(e.gross),
               price_component=stats(e.price), control_price=stats(c.price), n_control=int(len(c)), strat_diff=strat_diff(e, c), diff_halves=diff_halves(e, c),
               mirror_x1=stats(-e.gross - COST_BP), yield_change_diff_bp=strat_diff(e, c, col="dy_bp"))
    # read-onlys
    pre = rows(y, freq, dates, "pre", shift=-1); post = rows(y, freq, dates, "post", shift=+1)
    out["pre_op_T-2_to_T-1"] = dict(x1=stats(pre.net) if len(pre) else {}, strat_diff=strat_diff(pre, c) if len(pre) else {})
    out["post_op_T_to_T+1"] = dict(x1=stats(post.net) if len(post) else {}, strat_diff=strat_diff(post, c) if len(post) else {})
    em = e.merge(ev[["operation_date", "programme", "second_op_day"]].drop_duplicates("operation_date"), left_on="date", right_on="operation_date", how="left")
    out["by_programme"] = {str(k): dict(n=int(len(g)), net_mean=float(g.net.mean()), strat_diff=strat_diff(g, c)) for k, g in em.groupby("programme")}
    out["second_op_days"] = dict(n=int(em.second_op_day.sum()), x1=stats(em[em.second_op_day].net) if em.second_op_day.sum() else {})
    outd = [d for d in meta["out_days"] if (d >= CUT) == stage_oos and d not in set(dates)]
    o = rows(y, freq, outd, "outsector")
    out["out_of_sector_purchase_days"] = dict(n=int(len(o)), x1=stats(o.net) if len(o) else {}, strat_diff=strat_diff(o, c) if len(o) else {})
    if len(e) >= 10:
        i = e.net.abs().idxmax(); out["drop_one_max"] = dict(dropped_date=str(e.loc[i, "date"].date()), dropped_net_bp=float(e.loc[i, "net"]), x1=stats(e.drop(i).net), strat_diff=strat_diff(e.drop(i), c))
    out["per_year_net"] = {int(k): round(float(v), 1) for k, v in e.groupby(e.date.dt.year).net.mean().items()}
    if aux:
        # cross-section: 2y / 5y yield-change differentials on the same days (US); auction / month-end overlaps
        for name, ya, fq in aux.get("tenors", []):
            ea = rows(ya, fq, dates, "event"); ca = rows(ya, fq, cd, "control")
            out[f"{name}_same_days"] = dict(n=int(len(ea)), yield_change_diff_bp=strat_diff(ea, ca, col="dy_bp") if len(ea) and len(ca) else {}, price_diff=strat_diff(ea, ca) if len(ea) and len(ca) else {})
        if aux.get("mid_days") is not None:
            md = [d for d in aux["mid_days"] if (d >= CUT) == stage_oos]
            e10 = rows(y, freq, md, "mid"); out["mid_sector_days_10y"] = dict(n=int(len(e10)), yield_change_diff_bp=strat_diff(e10, c, col="dy_bp") if len(e10) else {})
            for name, ya, fq in aux.get("tenors", []):
                ea = rows(ya, fq, md, "mid"); ca = rows(ya, fq, cd, "control")
                out[f"mid_sector_days_{name}"] = dict(n=int(len(ea)), yield_change_diff_bp=strat_diff(ea, ca, col="dy_bp") if len(ea) and len(ca) else {})
        if aux.get("sale_days"):
            sd = [d for d in aux["sale_days"] if (d >= CUT) == stage_oos]
            for name, ya, fq in aux.get("tenors", []):
                if name == "2y":
                    es = rows(ya, fq, sd, "sale"); cs = rows(ya, fq, cd, "control")
                    out["mep_sale_days_2y"] = dict(n=int(len(es)), yield_change_diff_bp=strat_diff(es, cs, col="dy_bp") if len(es) and len(cs) else {})
        for name, ds in aux.get("overlaps", {}).items():
            hit = e.date.isin(set(ds))
            out[f"ex_{name}"] = dict(n_flagged=int(hit.sum()), x1=stats(e[~hit].net), strat_diff=strat_diff(e[~hit], c))
    # placebo max-stat (IS only)
    if not stage_oos:
        t_obs = out["strat_diff"].get("t") or -9; maxima = []; trueset = set(dates)
        for k in CLOCKS:
            pe = rows(y, freq, dates, "placebo", shift=k); pe = pe[~pe.date.isin(trueset)]
            pdays = set(pe.date); excl = set()
            for d in list(meta["allop"]) + list(pdays):
                if d in y.index:
                    p = y.index.get_loc(d); excl |= {y.index[q] for q in (p - 1, p, p + 1) if 0 <= q < len(y)}
            pc = rows(y, freq, control_days(y, prog, meta["allop"], exclude=excl), "pctrl")
            r = strat_diff(pe, pc) if len(pe) and len(pc) else {}; maxima.append(abs(r.get("t") or 0.0))
        mx = np.array(maxima); out["maxstat"] = dict(placebo_clocks=len(mx), obs_t=float(t_obs), placebo_max_t=[round(float(x), 2) for x in mx], p=float((np.sum(mx >= t_obs) + 1) / (len(mx) + 1)))
    return out


def blocking_us(out):
    """local supply: 10y yield fall on 7-10y days exceeds the 2y's; on 4-5.5y-only days the 5y's exceeds the 10y's."""
    try:
        a = out["yield_change_diff_bp"]["diff_bp"] < out["2y_same_days"]["yield_change_diff_bp"]["diff_bp"]
        b = out["mid_sector_days_5y"]["yield_change_diff_bp"]["diff_bp"] < out["mid_sector_days_10y"]["yield_change_diff_bp"]["diff_bp"]
        return dict(seven_ten_days_10y_below_2y=bool(a), mid_days_5y_below_10y=bool(b), passed=bool(a and b))
    except KeyError as ex:
        return dict(passed=False, missing=str(ex))


def blocking_uk(out):
    try:
        a = out["strat_diff"]["diff_bp"] > out["out_of_sector_purchase_days"]["strat_diff"]["diff_bp"]
        return dict(in_bucket_diff_exceeds_out_of_bucket=bool(a), passed=bool(a))
    except KeyError as ex:
        return dict(passed=False, missing=str(ex))


def market_passes(out, stage_oos):
    s, sd = out.get("x1", {}), out.get("strat_diff", {}); floor = T_FLOOR_OOS if stage_oos else T_FLOOR_IS
    own_t = s.get("t") if s.get("t") is not None else -9; d_t = sd.get("t") if sd.get("t") is not None else -9
    base = (s.get("n", 0) >= 40 and s.get("mean_bp", -1) > 0 and (s.get("pf") or 0) >= 1.15 and own_t >= floor and s.get("halves") == [1.0, 1.0]
            and out.get("x2", {}).get("mean_bp", -1) > 0 and sd.get("diff_bp", -1) > 0 and d_t >= floor and out.get("blocking", {}).get("passed"))
    if stage_oos: return bool(base and out.get("x15", {}).get("mean_bp", -1) > 0)
    return bool(base and out.get("diff_halves") == [1.0, 1.0] and out.get("maxstat", {}).get("p", 1.0) < 0.05)


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
    isr = None
    if UNSEAL:
        with open(os.path.join(HERE, "results", f"{TAG}_is.json")) as f: isr = json.load(f)
        assert isr["file_sha256"] == res["file_sha256"], "operation files changed since the IS run"
        candidates = [m for m, ok in isr["verdict"].items() if ok]
        if not candidates: raise SystemExit("no market cleared IS; holdouts stay sealed")
    us10 = load_yield("fred_DGS10.csv"); us2 = load_yield("fred_DGS2.csv"); us5 = load_av("UST05Y_daily_av.csv"); uk10 = load_yield("yield_UK10Y_daily.csv")
    fed = fed_events(); boe = boe_events()
    auc = json.load(open(os.path.join(HERE, "data", "treasury_note_auctions.json")))
    auc10 = set(pd.to_datetime([r["auction_date"] for r in auc if str(r.get("term", "")).startswith(("10", "9-Year"))]).normalize())   # new 10y issues and their reopenings (labelled 9-Year xx-Month)
    me = set(); per = us10.index.to_period("M")
    for m in per.unique():
        pos = np.where(per == m)[0]; me |= {us10.index[q] for q in pos[-4:]}
    aux_us = dict(tenors=[("2y", us2, 2), ("5y", us5, 2)], mid_days=fed["mid_days"], sale_days=fed["sale_days"], overlaps={"auction_days_10y": auc10, "month_end_T-3_T": me})
    aux_uk = dict(tenors=[], overlaps={})
    for code, y, freq, ev, meta, aux, blk in (("US", us10, 2, fed["events"], fed, aux_us, blocking_us), ("UK", uk10, 2, boe["events"], boe, aux_uk, blocking_uk)):
        if UNSEAL and code not in candidates: res["markets"][code] = {"skipped": "did not clear IS; holdout stays sealed"}; continue
        out = evaluate(code, y, freq, ev, meta, aux=aux, stage_oos=UNSEAL); out["blocking"] = blk(out) if "x1" in out else dict(passed=False)
        res["markets"][code] = out
        print(f"=== {code} ({'OOS' if UNSEAL else 'IS'}) operation days {out['n_events']} valid {out.get('n_valid')} spans {out['programme_spans']}")
        if "x1" in out:
            print(f"  C1 net {json.dumps(clean(out['x1']))}\n     price {out['price_component']['mean_bp']:+.1f} control price {out['control_price'].get('mean_bp', float('nan')):+.1f} n_control {out['n_control']}\n     strat_diff {json.dumps(clean(out['strat_diff']))} diff_halves {out['diff_halves']} x15 {out['x15']['mean_bp']:+.1f} x2 {out['x2']['mean_bp']:+.1f} mirror {out['mirror_x1']['mean_bp']:+.1f}\n     yield-change diff {json.dumps(clean(out['yield_change_diff_bp']))}\n     blocking {json.dumps(clean(out['blocking']))}\n     pre-op {json.dumps(clean(out['pre_op_T-2_to_T-1']['strat_diff']))} post-op {json.dumps(clean(out['post_op_T_to_T+1']['strat_diff']))}\n     out-of-sector {json.dumps(clean(out['out_of_sector_purchase_days']))}\n     by programme {json.dumps(clean({k: (v['n'], round(v['net_mean'], 1), v['strat_diff'].get('t')) for k, v in out['by_programme'].items()}))}\n     drop-one-max {json.dumps(clean(out.get('drop_one_max', {})))}\n     per-year {out['per_year_net']}")
            for k in ("2y_same_days", "5y_same_days", "mid_sector_days_10y", "mid_sector_days_5y", "mep_sale_days_2y", "ex_auction_days_10y", "ex_month_end_T-3_T", "second_op_days"):
                if k in out: print(f"     {k} {json.dumps(clean(out[k]))}"[:400])
            if "maxstat" in out: print("  maxstat:", clean(out["maxstat"]))
    passes = {c: market_passes(o, UNSEAL) for c, o in res["markets"].items() if "x1" in o}
    res["verdict"] = passes
    if not UNSEAL:
        res["candidates"] = [m for m, ok in passes.items() if ok]; res["family"] = "FAILS at IS stage (no candidate)" if not res["candidates"] else f"CANDIDATES {res['candidates']} - verdict at the sealed stage"
    else:
        n = sum(passes.values()); res["family"] = "REPLICATES" if n == 2 else ("PARTIAL" if n == 1 else "FAILS")
    print(f"\n{TAG} {'OOS' if UNSEAL else 'IS'} VERDICT per market: {passes}\nFAMILY: {res['family']}")
    with open(os.path.join(HERE, "results", f"{TAG}_{'oos' if UNSEAL else 'is'}.json"), "w") as f: json.dump(clean(res), f, indent=1)


if __name__ == "__main__":
    main()
