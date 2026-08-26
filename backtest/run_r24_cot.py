"""Round 24 Spec B: Williams COT Index on gold - replication-first.

Pre-registered in reference/goal_ledger.md before this file ran. The rule
under test is Larry Williams' published form: stochastic-normalize the
commercials' net position over 26 weeks; >= 80 = bullish extreme (trade with
the hedgers), <= 20 = bearish. WillCo variant divides by open interest first.

Alignment: COT report_date is the Tuesday of the positioning week, published
Friday. The index computed through week T is usable from the FOLLOWING Monday
open. We hold Monday open -> next Monday open on daily closes (the spliced
series is a close series; Monday close stands in for Monday open - one day of
drift, both legs, direction-neutral; noted as a simplification).
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

rng = np.random.default_rng(24)

# ---------------------------------------------------------------- data
# Provenance decision (documented deviation from the pre-registration): the
# Alpha Vantage daily series FAILED its registered cross-check - it contains
# synthetic weekend rows and +/-40-100bp day-level noise (daily return corr
# vs our verified 5m feed only 0.53 at every candidate day boundary). The
# price series is instead spliced from our own cross-verified feeds:
# ejtrader M15 (2012-05..2016-04, /100 scaling, Europe/Athens tz) + the H1
# collector (2016-04..2026-08). Their overlaps with the 5m feed agree to
# ~1bp median with return corr 0.9995+. Window becomes 2012-06..2026-08;
# the registered halves split (2019-01-01) is kept unchanged.
from zoneinfo import ZoneInfo
cot = pd.read_csv("data/COT_gold_github.csv", parse_dates=["report_date_as_yyyy_mm_dd"])
cot = cot.rename(columns={"report_date_as_yyyy_mm_dd": "date"}).sort_values("date")
cot = cot[["date", "open_interest_all", "comm_positions_long_all",
           "comm_positions_short_all", "noncomm_positions_long_all",
           "noncomm_positions_short_all"]].reset_index(drop=True)

import engine
ej = pd.read_csv("data/XAUUSD_m15_ejtrader.csv")
ej = ej[ej.Date != "Date"]
ej["close"] = pd.to_numeric(ej.close, errors="coerce")
ej["ts"] = pd.to_datetime(ej.Date, errors="coerce")
ej = ej.dropna(subset=["close", "ts"]).set_index("ts").sort_index()
ej.index = (ej.index.tz_localize(ZoneInfo("Europe/Athens"), nonexistent="shift_forward",
                                 ambiguous="NaT").tz_convert("UTC"))
ej = ej[ej.index.notna()]
ej_d = (ej.close / 100.0).resample("1D").last().dropna()

h1 = pd.read_csv("data/XAUUSD_H1_collector.csv", parse_dates=["datetime"]).set_index("datetime").sort_index()
h1_d = h1.close.resample("1D").last().dropna()

g5 = engine.load_bars()
d5 = g5.close.resample("1D").last().dropna()

# cross-checks on the overlaps (all tz-aware UTC daily closes)
def xcheck(a, b):
    ov = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    return dict(n=len(ov),
                med_abs_bps=float(((ov.a - ov.b) / ov.b * 1e4).abs().median()),
                ret_corr=float(np.log(ov.a).diff().corr(np.log(ov.b).diff())))
check = dict(ej_vs_5m=xcheck(ej_d, d5), h1_vs_5m=xcheck(h1_d, d5),
             ej_vs_h1=xcheck(ej_d, h1_d))
print("cross-checks:", check)
for k, v in check.items():
    assert v["med_abs_bps"] < 10 and v["ret_corr"] > 0.99, f"{k} fails cross-check"

g = pd.concat([ej_d[ej_d.index < h1_d.index.min()], h1_d]).sort_index()
g.index = g.index.tz_localize(None).normalize()
print(f"spliced daily gold: {g.index.min().date()} .. {g.index.max().date()} ({len(g)} days)")

# ---------------------------------------------------------------- signal frame
cot["net_c"] = cot.comm_positions_long_all - cot.comm_positions_short_all
cot["net_s"] = cot.noncomm_positions_long_all - cot.noncomm_positions_short_all
cot["willco_c"] = cot.net_c / cot.open_interest_all
cot["willco_s"] = cot.net_s / cot.open_interest_all

def cotidx(s, L):
    lo, hi = s.rolling(L).min(), s.rolling(L).max()
    return 100 * (s - lo) / (hi - lo)

# weekly gold return: Monday(report date + 6d) close -> next Monday close
# build a Monday-close series aligned to each report's first tradable Monday
gd = g.copy()
def monday_close_on_or_after(ts):
    # first available daily close on/after the target Monday
    idx = gd.index.searchsorted(ts)
    return (gd.index[idx], float(gd.iloc[idx])) if idx < len(gd) else (None, None)

rows = []
for i in range(len(cot) - 1):
    t_mon = cot.date.iloc[i] + pd.Timedelta(days=6)      # Tuesday report + 6d = Monday
    t_nxt = t_mon + pd.Timedelta(days=7)
    a, pa = monday_close_on_or_after(t_mon)
    b, pb = monday_close_on_or_after(t_nxt)
    if a is None or b is None or a >= b:
        continue
    rows.append(dict(date=cot.date.iloc[i], t_in=a, t_out=b, ret=np.log(pb / pa)))
wk = pd.DataFrame(rows).set_index("date")
sig = cot.set_index("date")
print(f"weeks with tradable Monday->Monday returns: {len(wk)}  "
      f"({wk.t_in.min().date()} .. {wk.t_out.max().date()})")

SPLIT = pd.Timestamp("2019-01-01")
COST = 0.60 / 1800 * 1e0        # ~$0.60/oz round trip on ~$1800 gold, in log terms ~3.3bp
def score(pos, ret):
    """pos: -1/0/+1 per week (already lagged correctly by construction)."""
    trades = (pos != pos.shift()).fillna(True) & (pos != 0)
    net = pos * ret - trades.astype(float) * COST
    x = net[pos != 0]
    if len(x) < 8 or x.std() == 0:
        return dict(n=int(len(x)), t=0.0, ann=0.0, win=np.nan, exposure=float((pos != 0).mean()))
    return dict(n=int(len(x)), t=float(x.mean() / x.std() * np.sqrt(len(x))),
                ann=float(x.sum() / max(len(ret) / 52, 1e-9)),
                win=float((x > 0).mean()), exposure=float((pos != 0).mean()))

def run_rule(series_name, L, hi_th, lo_th, fade=False, long_only=False):
    idx = cotidx(sig[series_name], L).reindex(wk.index)
    pos = pd.Series(0.0, index=wk.index)
    pos[idx >= hi_th] = 1.0
    pos[idx <= lo_th] = -1.0
    if fade:
        pos = -pos
    if long_only:
        pos = pos.clip(lower=0)
    ret = wk.ret
    full = score(pos, ret)
    h1 = score(pos[wk.index < SPLIT], ret[wk.index < SPLIT])
    h2 = score(pos[wk.index >= SPLIT], ret[wk.index >= SPLIT])
    return dict(full=full, h1=h1, h2=h2)

out = {"cross_check": check}

# -- headline replications (counted: 4 tests + 2 spec-fade = 6)
out["LW1_longshort"] = run_rule("net_c", 26, 80, 20)
out["LW1_longonly"]  = run_rule("net_c", 26, 80, 20, long_only=True)
out["LW2_longshort"] = run_rule("willco_c", 26, 80, 20)
out["LW2_longonly"]  = run_rule("willco_c", 26, 80, 20, long_only=True)
out["spec_fade_longshort"] = run_rule("net_s", 26, 80, 20, fade=True)   # specs crowded long -> short
out["spec_fade_willco"]    = run_rule("willco_s", 26, 80, 20, fade=True)

# time-in-state base rates for the registered structural-short caveat
idx26 = cotidx(sig.net_c, 26).reindex(wk.index)
out["base_rates"] = dict(pct_ge80=float((idx26 >= 80).mean()),
                         pct_le20=float((idx26 <= 20).mean()),
                         pct_mid=float(((idx26 > 20) & (idx26 < 80)).mean()))

# -- gradient: 4 lookbacks x 3 threshold pairs x 2 constructions = 24 cells
grid = {}
for nm, col in (("net", "net_c"), ("willco", "willco_c")):
    for L in (13, 26, 52, 156):
        for hi_th, lo_th in ((70, 30), (80, 20), (90, 10)):
            grid[f"{nm}_L{L}_{hi_th}"] = run_rule(col, L, hi_th, lo_th)
out["grid"] = grid

# -- max-stat circular-shift permutation over ALL counted cells (6 + 24 = 30)
def cell_t(series_name, L, hi_th, lo_th, ret, fade=False, long_only=False):
    idx = cotidx(sig[series_name], L).reindex(wk.index)
    pos = pd.Series(0.0, index=wk.index)
    pos[idx >= hi_th] = 1.0
    pos[idx <= lo_th] = -1.0
    if fade: pos = -pos
    if long_only: pos = pos.clip(lower=0)
    x = (pos * ret)[pos != 0]
    return abs(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 8 and x.std() > 0 else 0.0

cells = ([("net_c", 26, 80, 20, False, False), ("net_c", 26, 80, 20, False, True),
          ("willco_c", 26, 80, 20, False, False), ("willco_c", 26, 80, 20, False, True),
          ("net_s", 26, 80, 20, True, False), ("willco_s", 26, 80, 20, True, False)]
         + [(col, L, hi, lo, False, False)
            for col in ("net_c", "willco_c") for L in (13, 26, 52, 156)
            for hi, lo in ((70, 30), (80, 20), (90, 10))])

obs_max = max(cell_t(*c[:4], wk.ret, fade=c[4], long_only=c[5]) for c in cells)
NPERM = 500
perm_max = np.empty(NPERM)
retv = wk.ret.values
for k in range(NPERM):
    sh = rng.integers(10, len(retv) - 10)
    r = pd.Series(np.roll(retv, sh), index=wk.index)
    perm_max[k] = max(cell_t(*c[:4], r, fade=c[4], long_only=c[5]) for c in cells)
out["maxstat"] = dict(observed_max_t=float(obs_max),
                      p=float((perm_max >= obs_max).mean()),
                      n_cells=len(cells), n_perm=NPERM,
                      bonferroni_note="two-sided alpha 0.05 / 30 cells -> per-cell |t| ~ 3.1 needed")

# -- cost sensitivity on the headline cell
sens = {}
for mult in (0.0, 1.0, 2.0, 4.0):
    global COST_SAVE
    c0 = COST
    globals()["COST"] = c0 * mult
    sens[f"x{mult}"] = run_rule("net_c", 26, 80, 20)["full"]
    globals()["COST"] = c0
out["cost_sens"] = sens

json.dump(out, open("results/r24_cot.json", "w"), indent=1)

# ---------------------------------------------------------------- print
def fmt(d):
    return (f"n={d['n']:>4} t={d['t']:+.2f} ann={d['ann']*100:+5.1f}% "
            f"win={d['win']*100 if d['win']==d['win'] else 0:4.1f}% exp={d['exposure']*100:4.1f}%")
print("\n=== WILLIAMS COT INDEX ON GOLD (weekly, Monday->Monday, net of costs) ===")
print(f"base rates 26w commercials index: >=80 {out['base_rates']['pct_ge80']*100:.1f}% of weeks, "
      f"<=20 {out['base_rates']['pct_le20']*100:.1f}%")
for k in ("LW1_longshort", "LW1_longonly", "LW2_longshort", "LW2_longonly",
          "spec_fade_longshort", "spec_fade_willco"):
    d = out[k]
    print(f"\n{k:22s} full {fmt(d['full'])}")
    print(f"{'':22s} h1   {fmt(d['h1'])}")
    print(f"{'':22s} h2   {fmt(d['h2'])}")
print("\n--- gradient (full-sample t by lookback x threshold) ---")
for nm in ("net", "willco"):
    for hi in (70, 80, 90):
        row = "  ".join(f"L{L}:{grid[f'{nm}_L{L}_{hi}']['full']['t']:+.2f}" for L in (13, 26, 52, 156))
        print(f"{nm:7s} {hi}/{100-hi}: {row}")
print(f"\nmax-stat: observed max |t| {out['maxstat']['observed_max_t']:.2f}, "
      f"p = {out['maxstat']['p']:.3f} over {out['maxstat']['n_cells']} cells")
print("cost sensitivity (LW-1 full-sample t):",
      {k: f"{v['t']:+.2f}" for k, v in sens.items()})
