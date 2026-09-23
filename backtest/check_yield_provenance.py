"""Round 83 / attempt 60 data-provenance checker for daily 10-year yield series (DE, UK, JP; US as anchor).

PROVENANCE ONLY. Computes no month-end return, no event statistic. The month-end section is dates-only.
Usage: python3 check_yield_provenance.py MARKET path.csv [--raw mof|bbk|boe] [--json out.json]
  MARKET in DE, UK, JP, US. Default input is the delivered 2-column csv (date,y) exactly as load_yield reads it.
  --raw mof : MoF jgbcm_all.csv (cp932, era dates S/H/R, columns 1年..40年, '-' missing) -> 10年 column
  --raw bbk : Bundesbank REST csv (header lines, '.' missing, flag column)
  --raw boe : BoE IADB csv (DATE,SERIES; 'dd Mon yyyy')
"""
import io
import json
import re
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

ERA = {"M": 1867, "T": 1911, "S": 1925, "H": 1988, "R": 2018}


def easter(y):
    a = y % 19; b = y // 100; c = y % 100; d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451; mo = (h + l - 7 * m + 114) // 31; da = ((h + l - 7 * m + 114) % 31) + 1
    return date(y, mo, da)


def must_be_closed(market, years):
    """dates on which the local government bond market is closed in EVERY year of the span (hard check).
    DE: Frankfurt/Bund market; UK: gilt market (LSE calendar); JP: JSDA/TSE calendar."""
    out = set()
    for y in years:
        e = easter(y)
        if market == "DE":
            out |= {date(y, 1, 1), e - timedelta(2), e + timedelta(1), date(y, 5, 1), date(y, 12, 24), date(y, 12, 25), date(y, 12, 26), date(y, 12, 31)}
        elif market == "UK":
            out |= {date(y, 1, 1), e - timedelta(2), e + timedelta(1), date(y, 12, 25), date(y, 12, 26)}
        elif market == "JP":
            out |= {date(y, 1, 1), date(y, 1, 2), date(y, 1, 3), date(y, 12, 31), date(y, 5, 3), date(y, 5, 4), date(y, 5, 5), date(y, 11, 3), date(y, 11, 23), date(y, 2, 11)}
        elif market == "US":
            out |= {date(y, 1, 1), date(y, 7, 4), date(y, 12, 25)}
    return out


ROWS_PER_YEAR = {"DE": (244, 256), "UK": (247, 256), "JP": (238, 250), "US": (245, 254)}  # JP band is post-1989 (no Saturdays)

# level anchors: date -> (expected %, tolerance, confidence). Tolerances widened where the delivered series may be a fitted
# curve (DE/UK) rather than the benchmark bond, by ~10-15 bp. Dates chosen OUTSIDE [T-3, T+2] of any month-end.
ANCHORS = {
    "DE": [("1990-09-19", 9.0, 0.35, "medium"), ("1994-09-14", 7.5, 0.35, "medium"), ("1999-01-13", 3.65, 0.3, "medium"),
           ("2008-06-16", 4.6, 0.2, "high"), ("2012-06-01", 1.17, 0.18, "high"), ("2015-04-17", 0.07, 0.15, "high"),
           ("2016-07-08", -0.19, 0.12, "high"), ("2019-08-28", -0.71, 0.12, "high"), ("2020-03-09", -0.85, 0.15, "medium"),
           ("2022-12-19", 2.2, 0.2, "medium"), ("2023-10-04", 2.97, 0.15, "high"), ("2025-03-05", 2.8, 0.15, "high")],
    "UK": [("1990-01-17", 11.6, 0.6, "low"), ("1994-09-14", 8.9, 0.4, "medium"), ("2000-01-19", 5.75, 0.3, "medium"),
           ("2008-12-17", 3.15, 0.3, "medium"), ("2012-07-18", 1.5, 0.2, "medium"), ("2016-08-12", 0.53, 0.12, "high"),
           ("2020-08-04", 0.09, 0.1, "high"), ("2022-09-23", 3.82, 0.2, "high"), ("2022-10-11", 4.5, 0.25, "medium"),
           ("2023-08-17", 4.73, 0.15, "medium"), ("2025-01-09", 4.88, 0.15, "high")],
    "JP": [("1990-09-19", 8.4, 0.5, "medium"), ("1998-10-02", 0.75, 0.25, "medium"), ("2003-06-11", 0.44, 0.06, "high"),
           ("2006-05-10", 2.0, 0.15, "medium"), ("2013-04-10", 0.58, 0.15, "medium"), ("2016-02-09", -0.02, 0.06, "high"),
           ("2016-07-08", -0.28, 0.06, "high"), ("2019-09-04", -0.28, 0.06, "medium"), ("2022-12-19", 0.25, 0.04, "high"),
           ("2022-12-20", 0.41, 0.06, "high"), ("2024-05-22", 1.0, 0.06, "high"), ("2025-05-21", 1.55, 0.12, "medium")],
    "US": [("1990-09-19", 8.9, 0.3, "medium"), ("2008-06-16", 4.25, 0.2, "high"), ("2016-07-08", 1.37, 0.08, "high"),
           ("2020-03-09", 0.54, 0.08, "high"), ("2023-10-19", 4.98, 0.08, "high")],
}
# one-day jump anchors for the DATE-SHIFT test: date -> (lo, hi) bounds on y[d] - y[d-1] in percent. All outside [T-3, T+2].
JUMPS = {
    "DE": [("2025-03-05", 0.20, 0.42, "high"), ("2016-06-24", -0.22, -0.05, "medium"), ("2015-06-03", 0.08, 0.25, "medium")],
    "UK": [("2022-09-23", 0.18, 0.45, "high"), ("2022-09-26", 0.15, 0.50, "high"), ("2016-06-24", -0.40, -0.14, "high"), ("2016-08-04", -0.25, -0.05, "medium")],
    "JP": [("2022-12-20", 0.10, 0.25, "high"), ("2013-04-04", -0.22, -0.05, "medium"), ("2024-08-05", -0.25, -0.07, "medium")],
    "US": [("2020-03-09", -0.30, -0.10, "high"), ("2016-11-09", 0.12, 0.30, "high")],
}
YCC_JP = (pd.Timestamp("2016-01-29"), pd.Timestamp("2024-03-19"))   # negative-rate + YCC era: exact repeats are legitimate


def read_raw(path, mode):
    if mode == "mof":
        raw = open(path, "rb").read()
        txt = raw.decode("cp932", errors="replace")
        lines = txt.splitlines()
        hdr_i = next(i for i, l in enumerate(lines) if "10" in l and ("年" in l or "Y" in l))
        df = pd.read_csv(io.StringIO("\n".join(lines[hdr_i:])), dtype=str)
        col = [c for c in df.columns if c.strip() in ("10年", "10Y")][0]
        dcol = df.columns[0]

        def conv(s):
            s = str(s).strip()
            m = re.match(r"^([MTSHR])(\d+)\.(\d+)\.(\d+)$", s)
            if m: return pd.Timestamp(ERA[m.group(1)] + int(m.group(2)), int(m.group(3)), int(m.group(4)))
            return pd.to_datetime(s, errors="coerce")
        d = pd.DataFrame({"date": df[dcol].map(conv), "y": df[col]})
        info = dict(raw_encoding="cp932", raw_header_line=hdr_i, raw_columns=list(df.columns), raw_rows=int(len(df)),
                    era_dates=int(df[dcol].astype(str).str.match(r"^[MTSHR]\d+\.").sum()), missing_marker_rows=int((df[col].astype(str).str.strip() == "-").sum()))
        return d, info
    if mode == "bbk":
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        hdr_i = next(i for i, l in enumerate(lines) if re.match(r"^\d{4}-\d{2}-\d{2}", l))
        df = pd.read_csv(io.StringIO("\n".join(lines[hdr_i:])), header=None, dtype=str)
        d = pd.DataFrame({"date": pd.to_datetime(df[0], errors="coerce"), "y": df[1]})
        info = dict(raw_header_lines=lines[:hdr_i], raw_rows=int(len(df)), dot_missing=int((df[1].astype(str).str.strip() == ".").sum()),
                    decimal_comma_rows=int(df[1].astype(str).str.contains(",").sum()))
        return d, info
    if mode == "boe":
        df = pd.read_csv(path, dtype=str)
        d = pd.DataFrame({"date": pd.to_datetime(df.iloc[:, 0], format="%d %b %Y", errors="coerce"), "y": df.iloc[:, 1]})
        return d, dict(raw_columns=list(df.columns), raw_rows=int(len(df)))
    df = pd.read_csv(path, dtype=str)
    if df.shape[1] < 2: raise SystemExit("need >= 2 columns (date, y)")
    d = pd.DataFrame({"date": pd.to_datetime(df.iloc[:, 0], errors="coerce"), "y": df.iloc[:, 1]})
    return d, dict(raw_columns=list(df.columns), raw_rows=int(len(df)))


def main():
    market, path = sys.argv[1], sys.argv[2]
    mode = sys.argv[sys.argv.index("--raw") + 1] if "--raw" in sys.argv else None
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    d, info = read_raw(path, mode)
    R = {"market": market, "file": path, "raw": info, "checks": {}}
    C = R["checks"]
    ystr = d.y.astype(str).str.strip()
    # --- parse hazards exactly as load_yield would see them (to_numeric(errors='coerce') then dropna) ---
    haz = dict(decimal_comma=int(ystr.str.match(r"^-?\d+,\d+$").sum()), unicode_minus=int(ystr.str.contains("−").sum()),
               dash_missing=int((ystr == "-").sum()), dot_missing=int((ystr == ".").sum()), blank=int((ystr == "").sum() + d.y.isna().sum()),
               pct_sign=int(ystr.str.contains("%").sum()), bad_dates=int(d.date.isna().sum()))
    ynum = pd.to_numeric(ystr, errors="coerce")
    haz["rows_dropped_by_coerce"] = int(ynum.isna().sum()); haz["rows_dropped_by_coerce_weekday"] = int((ynum.isna() & (d.date.dt.dayofweek < 5)).sum())
    dropped = d[ynum.isna()].date.dropna()
    haz["dropped_by_year"] = {int(k): int(v) for k, v in dropped.groupby(dropped.dt.year).size().items()} if len(dropped) else {}
    C["parse"] = dict(**haz, verdict="PASS" if haz["decimal_comma"] == 0 and haz["unicode_minus"] == 0 and haz["pct_sign"] == 0 and haz["bad_dates"] == 0 else "FAIL")
    s = pd.Series(ynum.values, index=d.date).dropna(); dup = int(s.index.duplicated().sum()); s = s[~s.index.duplicated()].sort_index()
    # --- span / counts ---
    yrs = s.groupby(s.index.year).size(); lo, hi = ROWS_PER_YEAR[market]
    full_years = yrs[(yrs.index > s.index[0].year) & (yrs.index < s.index[-1].year)]
    odd = {int(k): int(v) for k, v in full_years.items() if v < lo or v > hi}
    C["span"] = dict(first=str(s.index[0].date()), last=str(s.index[-1].date()), rows=int(len(s)), duplicate_dates=dup,
                     rows_per_year_band=[lo, hi], years_outside_band=odd, rows_per_year={int(k): int(v) for k, v in yrs.items()},
                     verdict="PASS" if not odd else "FAIL")
    # --- weekdays ---
    wd = s.index.dayofweek; sat, sun = s.index[wd == 5], s.index[wd == 6]
    C["weekday"] = dict(distribution={int(k): int(v) for k, v in pd.Series(wd).value_counts().sort_index().items()},
                        saturday_rows=int(len(sat)), sunday_rows=int(len(sun)), saturday_years=sorted(set(int(x) for x in sat.year))[:60],
                        first_saturdays=[str(x.date()) for x in sat[:5]], last_saturday=str(sat[-1].date()) if len(sat) else None,
                        verdict="PASS" if len(sun) == 0 and (len(sat) == 0 or (market == "JP" and sat.max() < pd.Timestamp("1989-03-01"))) else "FAIL")
    # --- rows on must-be-closed dates (carry-forward / vendor fill detector) ---
    closed = must_be_closed(market, range(s.index[0].year, s.index[-1].year + 1))
    on_closed = [str(x.date()) for x in s.index if x.date() in closed]
    C["holiday_rows"] = dict(n=len(on_closed), dates=on_closed[:40], verdict="PASS" if not on_closed else "FAIL")
    # --- missing weekdays: classify as holiday-like (fixed date, Easter-relative, floating Monday, equinox) or one-off gap ---
    allbd = pd.bdate_range(s.index[0], s.index[-1]); miss = allbd.difference(s.index)
    rec = pd.Series([(x.month, x.day) for x in miss]).value_counts().to_dict()
    recm = pd.Series([(x.month, (x.day - 1) // 7, x.dayofweek) for x in miss]).value_counts().to_dict()
    # last-Monday-of-month holidays (UK spring/summer bank holidays, US Memorial Day)
    reclm = pd.Series([(x.month, x.dayofweek, (x + pd.offsets.MonthEnd(0) - x).days < 7) for x in miss]).value_counts().to_dict()
    def holiday_like(x):
        e = pd.Timestamp(easter(x.year)); off = (x - e).days
        if off in (-2, 1, 39, 50, 60): return True                       # Good Friday, Easter Monday, Ascension, Whit Monday, Corpus Christi
        if rec.get((x.month, x.day), 0) >= 3: return True                          # fixed-date holiday (or its recurring substitute)
        if recm.get((x.month, (x.day - 1) // 7, x.dayofweek), 0) >= 3: return True  # n-th weekday of month
        if x.dayofweek == 0 and reclm.get((x.month, 0, True), 0) >= 3: return True  # last Monday of month
        if market == "JP" and ((x.month == 3 and x.day in (20, 21)) or (x.month == 9 and x.day in (22, 23, 24))): return True  # equinox
        if x.dayofweek == 0 and (rec.get((x.month, x.day - 1), 0) >= 3 or rec.get((x.month, x.day - 2), 0) >= 3): return True  # substitute Monday
        return False
    nonrec = [x for x in miss if not holiday_like(x) and x.date() not in closed]
    def near_me(x):
        nxt = x + pd.offsets.BMonthEnd(0); prv = x - pd.offsets.BMonthEnd(1)
        return (nxt - x).days <= 7 or (x - prv).days <= 3
    nonrec_near = [str(x.date()) for x in nonrec if near_me(x)]
    C["gaps"] = dict(missing_weekdays_total=int(len(miss)), missing_holiday_like=int(len(miss) - len(nonrec)), missing_one_off=int(len(nonrec)),
                     one_off_by_year={int(k): int(v) for k, v in pd.Series([x.year for x in nonrec]).value_counts().sort_index().items()},
                     one_off_all=[str(x.date()) for x in nonrec][:80], one_off_near_month_end=nonrec_near[:60], n_one_off_near_month_end=len(nonrec_near),
                     note="one-off gaps must each be matched to a known market closure (funeral, storm, jubilee, 2019 JP 10-day Golden Week) or they are data gaps",
                     verdict="PASS" if len(nonrec_near) == 0 else ("UNCERTAIN" if len(nonrec_near) <= 0.03 * len(allbd) / 21 else "FAIL"))
    # --- exact consecutive repeats, judged against the zero-change rate implied by resolution and volatility ---
    dec = ystr[ynum.notna()].str.extract(r"\.(\d+)$")[0].str.len().fillna(0)
    res_bp = 100.0 / (10 ** int(dec.mode().iloc[0])) if len(dec) else 1.0     # publication resolution in bp
    rep = (s.diff() == 0); rep_dates = s.index[rep.values]
    dy_bp = s.diff() * 100
    by_year = pd.DataFrame(dict(rep=rep, sd=dy_bp)).groupby(s.index.year).agg(rep=("rep", "mean"), sd=("sd", "std"), n=("rep", "size"))
    by_year["expected"] = np.minimum(0.95, 0.4 * res_bp / by_year.sd.clip(lower=0.3))
    excess = by_year[(by_year.rep > 2.5 * by_year.expected + 0.03) & (by_year.n >= 100)]
    if market == "JP": excess = excess[(excess.index < YCC_JP[0].year) | (excess.index > YCC_JP[1].year)]
    runs = []; k = 0
    for i, r in enumerate(rep.values):
        if r: k += 1
        else:
            if k >= 3: runs.append((str(s.index[i - k - 1].date()), k + 1))
            k = 0
    if k >= 3: runs.append((str(s.index[len(s) - k - 1].date()), k + 1))
    long_runs = [r for r in runs if r[1] >= 6 and not (market == "JP" and YCC_JP[0] <= pd.Timestamp(r[0]) <= YCC_JP[1])]
    C["repeats"] = dict(resolution_bp=res_bp, consecutive_exact_repeats=int(rep.sum()), share=float(rep.mean()),
                        years_with_excess_repeats={int(k): dict(share=round(float(v.rep), 3), expected=round(float(v.expected), 3), sd_bp=round(float(v.sd), 2)) for k, v in excess.iterrows()},
                        n_runs_len_ge_4=len(runs), runs_len_ge_6_outside_ycc=long_runs[:40], repeats_on_holiday_rows=int(sum(1 for x in rep_dates if x.date() in closed)),
                        note="a 1 bp series with daily sd 6 bp repeats ~10% of days legitimately; excess = share > 2.5x expected + 3 pp in a year with >= 100 rows",
                        verdict="FAIL" if (len(excess) > 0 or any(1 for x in rep_dates if x.date() in closed)) else ("UNCERTAIN" if long_runs else "PASS"))
    # --- scale / sign / resolution ---
    dy = s.diff().dropna() * 100  # bp
    sd_by_year = {int(k): round(float(v), 2) for k, v in dy.groupby(dy.index.year).std().items()}
    neg = s[s < 0]
    C["scale"] = dict(min=float(s.min()), min_date=str(s.idxmin().date()), max=float(s.max()), max_date=str(s.idxmax().date()), median=float(s.median()),
                      decimals_mode=int(dec.mode().iloc[0]) if len(dec) else None, decimals_max=int(dec.max()) if len(dec) else None,
                      negative_rows=int(len(neg)), negative_span=[str(neg.index[0].date()), str(neg.index[-1].date())] if len(neg) else None,
                      daily_change_sd_bp_overall=float(dy.std()), daily_change_sd_bp_by_year=sd_by_year,
                      verdict="PASS" if 0.3 < s.median() < 12 and 1.0 < dy.std() < 15 and s.max() < 25 and s.min() > -2 else "FAIL")
    # --- large one-day jumps (roll / error detector); dates only where inside a month-end window ---
    me = s.groupby(s.index.to_period("M")).apply(lambda g: g.index[-1]); me_pos = {s.index.get_loc(t) for t in me}
    inwin = set()
    for p in me_pos:
        for k in range(-3, 3): inwin.add(p + k)
    big = dy[dy.abs() > 25]
    big_in = [str(t.date()) for t in big.index if s.index.get_loc(t) in inwin]
    big_out = [(str(t.date()), round(float(v), 1)) for t, v in big.items() if s.index.get_loc(t) not in inwin]
    C["jumps"] = dict(n_abs_gt_25bp=int(len(big)), n_inside_monthend_windows=len(big_in), inside_window_dates=big_in[:60],
                      outside_window_top=sorted(big_out, key=lambda x: -abs(x[1]))[:15],
                      note="inside-window entries are dates only (no sign, no size): provenance flag, not a return")
    # --- anchors ---
    anc = []
    for dt, exp, tol, conf in ANCHORS.get(market, []):
        t = pd.Timestamp(dt)
        if t < s.index[0] or t > s.index[-1]: anc.append(dict(date=dt, expected=exp, actual=None, verdict="OUT_OF_SPAN", confidence=conf)); continue
        i = s.index.get_indexer([t], method="nearest")[0]; act = float(s.iloc[i]); off = abs((s.index[i] - t).days)
        anc.append(dict(date=dt, used=str(s.index[i].date()), expected=exp, tol=tol, actual=act, diff=round(act - exp, 3), confidence=conf,
                        verdict="PASS" if abs(act - exp) <= tol and off <= 3 else ("UNCERTAIN" if abs(act - exp) <= 2 * tol else "FAIL")))
    fails = [a for a in anc if a["verdict"] == "FAIL"]; hi_fails = [a for a in fails if a["confidence"] == "high"]
    C["anchors"] = dict(items=anc, n_pass=sum(a["verdict"] == "PASS" for a in anc), n_fail=len(fails), n_high_conf_fail=len(hi_fails),
                        verdict="FAIL" if hi_fails else ("UNCERTAIN" if fails else "PASS"))
    jm = []
    for dt, lo_, hi_, conf in JUMPS.get(market, []):
        t = pd.Timestamp(dt)
        if t not in s.index: jm.append(dict(date=dt, verdict="NO_ROW", confidence=conf)); continue
        i = s.index.get_loc(t); ch = float(s.iloc[i] - s.iloc[i - 1]); prev = str(s.index[i - 1].date())
        # date-shift diagnostic: which of d-1, d, d+1 carries the largest move
        nb = {str(s.index[j].date()): round(float(s.iloc[j] - s.iloc[j - 1]), 3) for j in range(max(1, i - 1), min(len(s), i + 2))}
        jm.append(dict(date=dt, prev_row=prev, change=round(ch, 3), bounds=[lo_, hi_], neighbours=nb, confidence=conf, verdict="PASS" if lo_ <= ch <= hi_ else "FAIL"))
    jfail = [j for j in jm if j["verdict"] == "FAIL"]
    C["jump_anchors_date_shift"] = dict(items=jm, verdict="FAIL" if [j for j in jfail if j["confidence"] == "high"] else ("UNCERTAIN" if jfail else "PASS"))
    # --- month-end calendar (dates only) ---
    dec_T = {int(t.year): str(t.date()) for t in me if t.month == 12}
    T_on_closed = [str(t.date()) for t in me if t.date() in closed]
    T_repeat = int(sum(1 for t in me if rep.get(t, False)))
    spans = []
    for t in me:
        p = s.index.get_loc(t)
        if p >= 3: spans.append(((t - s.index[p - 3]).days, str(t.date())))
    wide = [x for x in spans if x[0] > 7]
    C["month_end_calendar"] = dict(n_month_ends=int(len(me)), december_T_by_year={k: v for k, v in list(dec_T.items())[-12:]}, december_T_all_31st=int(sum(v.endswith("-31") for v in dec_T.values())),
                                    december_T_all_30th=int(sum(v.endswith("-30") for v in dec_T.values())), december_T_28th=int(sum(v.endswith("-28") for v in dec_T.values())),
                                    T_on_must_be_closed=T_on_closed, T_with_exact_repeat=T_repeat, windows_Tm3_to_T_span_gt_7days=[x[1] for x in wide][:40], n_wide_windows=len(wide),
                                    T_weekday_distribution={int(k): int(v) for k, v in pd.Series(me.dt.dayofweek).value_counts().sort_index().items()},
                                    T_repeat_share=round(T_repeat / max(len(me), 1), 3), base_repeat_share=round(float(rep.mean()), 3),
                                    verdict="PASS" if not T_on_closed and T_repeat / max(len(me), 1) <= 2 * float(rep.mean()) + 0.02 else "FAIL")
    verdicts = {k: v.get("verdict") for k, v in C.items() if isinstance(v, dict) and "verdict" in v}
    R["verdicts"] = verdicts
    R["overall"] = "FAIL" if "FAIL" in verdicts.values() else ("UNCERTAIN" if "UNCERTAIN" in verdicts.values() else "PASS")
    print(json.dumps(R, indent=1, default=str))
    if out_json: json.dump(R, open(out_json, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
