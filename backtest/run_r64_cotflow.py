"""Round 64 attempt 47: gold speculator-flow liquidity premium - fade the
weekly COT large-spec flow, MGC (frozen per reference/goal_ledger.md
'Attempt 47' registration). Event dedupe: one position at a time - a week's
entry is skipped while the previous trade is still open, i.e. entry <= exit
session (busy = entry + hold-1 weekdays). This reproduces every registered
count (IS 147/114/76/66, independence subsets 45/31/21/18). NOTE: the on-disk
scratchpad/reg/cot_flow_counts_v2.py carries an off-by-one (busy = entry +
hold weekdays, which also blocks the session AFTER the exit) and yields IS
119/100/69/59 - that variant is counted here for the record, never traded.

IS-ONLY by default: the sealed OOS report weeks (rd > 2022-08-23, i.e. after
the first 75% of the 712 frozen report weeks) are DROPPED at frame-build time
and the intraday price frame is truncated 60 days past the cut, so no OOS
return can be computed. Writes ONLY results/r64_cotflow_is.json.

--unseal (refuses unless UNSEAL_OK=1) rebuilds the full frame and evaluates
ONLY the winner cell recorded in the IS results JSON on the sealed rows, at
the program bar; writes results/r64_cotflow_oos.json.
"""
import sys, os, json, warnings, datetime as dt
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo
from pandas.tseries.holiday import USFederalHolidayCalendar
warnings.filterwarnings("ignore")

UNSEAL = "--unseal" in sys.argv
if UNSEAL and os.environ.get("UNSEAL_OK") != "1":
    print("REFUSED: --unseal requires the environment variable UNSEAL_OK=1 (the OOS seal is "
          "opened deliberately by the parent, never by a builder run).")
    raise SystemExit(2)

NY = ZoneInfo("America/New_York")
COST = 0.35            # MGC points per round trip (registered)
COST15 = 1.5 * COST    # sensitivity
CUT = pd.Timestamp("2022-08-23")   # last IS report week (534 of 712 frozen weeks)
SPAN = (pd.Timestamp("2012-06-05"), pd.Timestamp("2026-01-20"))
GRID = [(1.0, 5), (1.0, 10), (1.5, 5), (1.5, 10)]
SCARCE = {(1.0, 10), (1.5, 5), (1.5, 10)}        # declared scarce-event cells
AUTO_SUBSUMED = {(1.5, 10)}                       # declared ex-ante (indep. subset IS 18 < 25)
IS_N_FLOOR = 40
INDEP_FLOOR = {(1.0, 5): 40, (1.0, 10): 25, (1.5, 5): 25, (1.5, 10): 25}
OOS_N_FLOOR = {(1.0, 5): 40, (1.0, 10): 25, (1.5, 5): 25, (1.5, 10): 25}
SUB_BAND = (0.25, 0.5)

# ---------------------------------------------------------------- COT frame
cot = (pd.read_csv("data/COT_gold_github.csv", parse_dates=["report_date_as_yyyy_mm_dd"])
       .rename(columns={"report_date_as_yyyy_mm_dd": "rd"}).sort_values("rd").reset_index(drop=True))
assert cot.rd.duplicated().sum() == 0 and len(cot) == 1047, "COT file differs from registration"
assert cot.rd.iloc[0] == pd.Timestamp("2006-01-03") and cot.rd.iloc[-1] == SPAN[1], "COT span differs"
cot = cot.drop_duplicates("rd")
cot["net_s"] = cot.noncomm_positions_long_all - cot.noncomm_positions_short_all
cot["net_c"] = cot.comm_positions_long_all - cot.comm_positions_short_all
cot["willco_s"] = cot.net_s / cot.open_interest_all
cot["willco_c"] = cot.net_c / cot.open_interest_all
cot["flow"] = cot.net_s.diff() / cot.open_interest_all.shift(1)
cot["z"] = cot.flow / cot.flow.shift(1).rolling(52).std()      # trailing 52 wk, current excluded


def cotidx(s, L):
    lo, hi = s.rolling(L).min(), s.rolling(L).max()
    return 100 * (s - lo) / (hi - lo)


cot["spec26"] = cotidx(cot.willco_s, 26)
cot["comm13"] = cotidx(cot.net_c, 13)
cot["commw13"] = cotidx(cot.willco_c, 13)

# release rule (corrected): Friday 15:30 ET; any federal holiday Mon..Fri of the
# report week -> following Monday 15:30 ET. Juneteenth from 2021 (observed).
hol = set(USFederalHolidayCalendar().holidays("2006-01-01", "2027-12-31").date)
for y in range(2021, 2027):
    j = dt.date(y, 6, 19)
    if j.weekday() == 5: j -= dt.timedelta(1)
    if j.weekday() == 6: j += dt.timedelta(1)
    hol.add(j)


def release(rd):
    rd = rd.date(); mon = rd - dt.timedelta(rd.weekday()); fri = mon + dt.timedelta(4)
    wk = [mon + dt.timedelta(i) for i in range(5)]
    if any(d in hol for d in wk):
        return fri + dt.timedelta(3), True
    return fri, False


SHUT = [(dt.date(2013, 10, 1), dt.date(2013, 11, 5)), (dt.date(2018, 12, 24), dt.date(2019, 3, 5)),
        (dt.date(2025, 9, 30), dt.date(2025, 12, 16))]


def nontradable(rd):
    rd = rd.date(); return any(a <= rd <= b for a, b in SHUT)


def next_weekday(d):
    d = d + dt.timedelta(1)
    while d.weekday() >= 5: d += dt.timedelta(1)
    return d


def wd_add(d, n):
    while n > 0:
        d = next_weekday(d); n -= 1
    return d


cot["rel"], cot["delayed"] = zip(*cot.rd.map(release))
cot["shut"] = cot.rd.map(nontradable)
cot["entry"] = cot.rel.map(next_weekday)                            # first session strictly after release
cot["late"] = cot.rel.map(lambda r: next_weekday(r + dt.timedelta(7)))  # placebo: after release + 7d
w = cot[(cot.rd >= SPAN[0]) & (cot.rd <= SPAN[1])].copy().reset_index(drop=True)
assert len(w) == 712, f"frozen span should hold 712 report weeks, got {len(w)}"
w["oos"] = w.rd > CUT
assert (~w.oos).sum() == 534 and w.oos.sum() == 178

# calendar-only availability assertion + distribution (no z, no prices), printed before any grid
w["release_ts"] = [pd.Timestamp(dt.datetime.combine(r, dt.time(15, 30)), tz=NY) for r in w.rel]
w["entry_0930"] = [pd.Timestamp(dt.datetime.combine(e, dt.time(9, 30)), tz=NY) for e in w.entry]
assert (w.release_ts < w.entry_0930).all(), "release must precede entry for every week"
trad = w[~w.shut]
gap = (pd.to_datetime(trad.entry) - trad.rd).dt.days.value_counts().sort_index()
print(f"report weeks {len(w)} (IS {(~w.oos).sum()} / OOS {w.oos.sum()}); weekday histogram "
      f"{w.rd.dt.dayofweek.value_counts().sort_index().to_dict()}")
print(f"holiday-delayed weeks {int(w.delayed.sum())}, shutdown (non-tradable) weeks {int(w.shut.sum())}, "
      f"tradable {len(trad)}")
print(f"entry - report_date (tradable weeks, calendar days): {gap.to_dict()}   [registered 6d 548 / 7d 130 / 8d 5]")
print(f"entry weekday (tradable): {pd.to_datetime(trad.entry).dt.dayofweek.value_counts().sort_index().to_dict()} "
      f"(0=Mon, 1=Tue)")
release_dist = {int(k): int(v) for k, v in gap.items()}

# ---------------------------------------------------------------- IS-ONLY MASK
if not UNSEAL:
    w = w[~w.oos].copy().reset_index(drop=True)       # sealed report weeks leave the frame here
    PRICE_END = (CUT + pd.Timedelta(days=60)).tz_localize("UTC")
    print(f"IS-ONLY: {len(w)} report weeks kept; price frame truncated at {PRICE_END.date()}")
else:
    PRICE_END = None

# ---------------------------------------------------------------- prices (r24 loader, lines 37-67)
import engine
ej = pd.read_csv("data/XAUUSD_m15_ejtrader.csv")
ej = ej[ej.Date != "Date"]
for c in ["open", "high", "low", "close"]:
    ej[c] = pd.to_numeric(ej[c], errors="coerce")
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


def xcheck(a, b):
    ov = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    return dict(n=len(ov),
                med_abs_bps=float(((ov.a - ov.b) / ov.b * 1e4).abs().median()),
                ret_corr=float(np.log(ov.a).diff().corr(np.log(ov.b).diff())))


check = dict(ej_vs_5m=xcheck(ej_d, d5), h1_vs_5m=xcheck(h1_d, d5), ej_vs_h1=xcheck(ej_d, h1_d))
print("cross-checks:", check)
for k, v in check.items():
    assert v["med_abs_bps"] < 10 and v["ret_corr"] > 0.99, f"{k} fails cross-check"

g = pd.concat([ej_d[ej_d.index < h1_d.index.min()], h1_d]).sort_index()
g.index = g.index.tz_localize(None).normalize()
print(f"spliced daily gold: {g.index.min().date()} .. {g.index.max().date()} ({len(g)} days)")

# spliced intraday frame: ejtrader 15m (/100) before the H1 collector starts, H1 after.
# Both feeds are open-time labelled (the 17:00 ET break hour is absent in both) -> close = label + duration.
ej15 = (ej[["open", "high", "low", "close"]] / 100.0).copy()
ej15["dur"] = pd.Timedelta(minutes=15)
h1x = h1[["open", "high", "low", "close"]].copy()
h1x["dur"] = pd.Timedelta(hours=1)
bars = pd.concat([ej15[ej15.index < h1x.index.min()], h1x]).sort_index()
bars = bars[~bars.index.duplicated()]
if PRICE_END is not None:
    bars = bars[bars.index < PRICE_END]
    g = g[g.index < PRICE_END.tz_localize(None)]
bars["ts_close"] = bars.index + bars.dur
ny_open = bars.index.tz_convert(NY)
bars["skey"] = (ny_open + pd.Timedelta(hours=7)).date          # 17:00 ET session boundary
bars = bars[pd.to_datetime(bars.skey).dt.dayofweek < 5]
print(f"spliced intraday frame: {bars.index.min()} .. {bars.index.max()} ({len(bars)} bars; "
      f"15m until {h1x.index.min()}, H1 after)")

daily = bars.groupby("skey").agg(hi=("high", "max"), lo=("low", "min"), n=("close", "size"))
daily["rng"] = daily.hi - daily.lo
daily["atr20"] = daily.rng.rolling(20).mean().shift(1)         # 20 prior daily ranges
ATR = daily.atr20.to_dict()

TSC = bars.ts_close.values.astype("datetime64[ns]")
CLOSE = bars.close.values
TSC_NY_DATE = np.array([t.date() for t in bars.ts_close.dt.tz_convert(NY)])
bdays = set(daily.index)


def _ts(d, hh, mm):
    return np.datetime64(pd.Timestamp(dt.datetime.combine(d, dt.time(hh, mm)), tz=NY).tz_convert("UTC")
                         .tz_localize(None), "ns")


def entry_mark(d0, max_adv=5):
    """First bar close at/after 09:30 ET on session d0 (advance to the next weekday with bars if the
    date has none). Returns (date_used, ts_close, close, advanced)."""
    d, adv = d0, 0
    while adv <= max_adv:
        i = np.searchsorted(TSC, _ts(d, 9, 30), "left")
        if i < len(TSC) and TSC[i] <= _ts(d, 17, 0):
            return d, TSC[i], float(CLOSE[i]), adv
        d = next_weekday(d); adv += 1
    return None, None, np.nan, adv


def exit_mark(x):
    """Last bar close at/before 16:00 ET on session x. Returns (ts_close, close, stale) where stale
    means the mark came from an earlier session (no bars on x, e.g. Good Friday)."""
    i = np.searchsorted(TSC, _ts(x, 16, 0), "right") - 1
    if i < 0:
        return None, np.nan, True
    return TSC[i], float(CLOSE[i]), TSC_NY_DATE[i] != x


# daily close series for the concurrent-move partition (report-date to report-date, sigma63)
lr = np.log(g).diff()
sig63 = lr.rolling(63).std()


def asof(s, d):
    i = s.index.searchsorted(pd.Timestamp(d), "right") - 1
    return float(s.iloc[i]) if i >= 0 else np.nan


# ---------------------------------------------------------------- events (frozen semantics)
def events(df, lo, hi, hold, offby1=False):
    """Weeks with lo <= |z| < hi (hi=None: no cap), shutdown weeks dropped, one position at a time:
    busy = exit session (entry + hold-1 weekdays); a week is skipped if its entry <= busy.
    offby1=True reproduces the on-disk count script's variant (busy = entry + hold weekdays) - record only."""
    busy, out = None, []
    for r in df.itertuples():
        if r.shut or not np.isfinite(r.z):
            continue
        az = abs(r.z)
        if az < lo or (hi is not None and az >= hi):
            continue
        if busy is not None and r.entry <= busy:
            continue
        busy = wd_add(r.entry, hold if offby1 else hold - 1); out.append(r)
    return out


def book(evs, hold, entry_col="entry"):
    rows = []
    for r in evs:
        side = -float(np.sign(r.z))                                   # fade the flow
        d_in, t_in, p_in, adv = entry_mark(getattr(r, entry_col))
        if d_in is None:
            rows.append(dict(rd=r.rd, ok=False)); continue
        x = wd_add(d_in, hold - 1)                                    # entry session = session 1
        t_out, p_out, stale = exit_mark(x)
        atr = ATR.get(d_in, np.nan)
        assert t_in is not None and t_out is not None and t_out > t_in
        assert pd.Timestamp(t_in, tz="UTC") > r.release_ts
        rows.append(dict(rd=r.rd, z=float(r.z), side=side, d_in=d_in, x=x, t_in=t_in, t_out=t_out,
                         adv=adv, stale=bool(stale), atr=atr, delayed=bool(r.delayed),
                         pnl=side * (p_out - p_in) - COST, pnl15=side * (p_out - p_in) - COST15,
                         mid=bool((r.spec26 > 20) & (r.spec26 < 80) & (r.comm13 > 20) & (r.comm13 < 80)
                                  & (r.commw13 > 20) & (r.commw13 < 80)),
                         ext=bool((r.spec26 >= 80) | (r.spec26 <= 20)),
                         ret_wk=asof(np.log(g), r.rd) - asof(np.log(g), r.rd_prev),
                         s63=asof(sig63, r.rd), ok=True))
    b = pd.DataFrame(rows)
    b = b[b.ok].copy() if len(b) else b
    if len(b):
        b["ratio"] = b.ret_wk.abs() / (b.s63 * np.sqrt(5))
        b = b.sort_values("t_in").reset_index(drop=True)
    return b


def stats(p, a, floor=10):
    r = np.asarray(p, float) / np.asarray(a, float)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < floor: return dict(n=int(len(p)))
    w_, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w_.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


def fmt(a, label):
    if a.get("n", 0) < 10:
        return f"{label:>34} | {a.get('n', 0):>4}   (under 10, not summarised)"
    pf = a['pf'] if np.isfinite(a['pf']) else float('inf')
    return (f"{label:>34} | {a['n']:>4} {a['wr']*100:>5.1f}% {pf:>5.2f} {a['avg_R']:>+7.3f} "
            f"{a['t']:>+6.2f} {str(a['halves']):>12}")


w["rd_prev"] = w.rd.shift(1)
w.loc[0, "rd_prev"] = cot.rd[cot.rd < w.rd.iloc[0]].iloc[-1]


# ================================================================ UNSEAL PATH (winner cell only)
if UNSEAL:
    isr = json.load(open("results/r64_cotflow_is.json"))
    if not isr.get("is_pass") or isr.get("winner") is None:
        print("No IS winner recorded; the seal stays closed."); raise SystemExit(1)
    thr, hold = float(isr["winner"]["thr"]), int(isr["winner"]["hold"])
    cell = (thr, hold)
    if cell in AUTO_SUBSUMED:
        print("Winner cell is auto-SUBSUMED by registration; seal stays closed."); raise SystemExit(1)
    evs = [r for r in events(w, thr, None, hold) if r.oos]           # events whose report week is sealed
    b = book(evs, hold)
    o = stats(b.pnl, b.atr); c15 = stats(b.pnl15, b.atr)
    floor = OOS_N_FLOOR[cell]
    PASS = (o.get("n", 0) >= floor and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
            and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
    power_fail = o.get("n", 0) < floor
    print(f"\n=== ONE-SHOT OOS, cell thr {thr} x hold {hold} (burned now) ===")
    print(fmt(o, "OOS"))
    print(fmt(c15, "OOS cost x1.5"))
    print(f"OOS GATE: {'PASS' if PASS else ('POWER FAIL - watch item at most' if power_fail else 'FAIL')}")
    json.dump(dict(cell=dict(thr=thr, hold=hold), oos=o, oos_cost15=c15, gate_pass=bool(PASS),
                   power_fail=bool(power_fail), n_floor=floor),
              open("results/r64_cotflow_oos.json", "w"), indent=1, default=float)
    raise SystemExit

# ================================================================ IS PATH
# signal-side overlap re-print (registered: printed before any grid is read)
print("\n=== signal-side event counts (IS rows only) [registered IS: 147 / 114 / 76 / 66; mid-band 45 / 31 / 21 / 18] ===")
sig_counts = {}
for thr, hold in GRID:
    ev = events(w, thr, None, hold)
    n = len(ev); nl = sum(1 for r in ev if r.z < 0); ns_ = n - nl
    mid = sum(1 for r in ev if (r.spec26 > 20) & (r.spec26 < 80) & (r.comm13 > 20) & (r.comm13 < 80)
              & (r.commw13 > 20) & (r.commw13 < 80))
    ext = np.mean([(r.spec26 >= 80) | (r.spec26 <= 20) for r in ev]) if n else np.nan
    dl = sum(1 for r in ev if r.delayed)
    sig_counts[f"thr{thr}_hold{hold}"] = dict(n=n, long=nl, short=ns_, r24_spec26_extreme_share=float(ext),
                                             indep_midband=mid, holiday_delayed=dl)
    print(f"thr {thr} hold {hold}: IS events {n} (long {nl} / short {ns_}); r24 spec26-extreme share "
          f"{ext:.2f}; all-r24-gauges mid-band subset {mid}; holiday-delayed {dl}")
sub_raw = w[(~w.shut) & (w.z.abs() >= SUB_BAND[0]) & (w.z.abs() < SUB_BAND[1])]
print(f"sub-band {SUB_BAND[0]} <= |z| < {SUB_BAND[1]}: IS tradable weeks {len(sub_raw)}   [registered IS 107]")
sig_counts["sub_band_weeks"] = int(len(sub_raw))
# for the record only: the on-disk count script's off-by-one dedupe (blocks the session after exit)
for thr, hold in GRID:
    sig_counts[f"thr{thr}_hold{hold}"]["n_if_offby1_busy_until"] = len(events(w, thr, None, hold, offby1=True))
print("IS events under the on-disk script's off-by-one dedupe (record only, NOT traded):",
      {k: v["n_if_offby1_busy_until"] for k, v in sig_counts.items() if isinstance(v, dict)})

rows, diag = [], {"sub_band": {}, "late": {}, "partition": {}, "independence": {}, "legs": {}}
books = {}
for thr, hold in GRID:
    ev = events(w, thr, None, hold)
    b = book(ev, hold); books[(thr, hold)] = b
    bl = book(ev, hold, entry_col="late")
    r = dict(thr=thr, hold=hold, selectable=True, scarce=(thr, hold) in SCARCE,
             auto_subsumed=(thr, hold) in AUTO_SUBSUMED,
             n_events=len(ev), n_booked=int(len(b)), n_atr_nan=int((~np.isfinite(b.atr)).sum()),
             n_entry_advanced=int((b.adv > 0).sum()), n_exit_stale=int(b.stale.sum()),
             IS=stats(b.pnl, b.atr), cost15=stats(b.pnl15, b.atr))
    diag["legs"][f"{thr}x{hold}"] = dict(long=stats(b.pnl[b.side > 0], b.atr[b.side > 0]),
                                         short=stats(b.pnl[b.side < 0], b.atr[b.side < 0]))
    diag["late"][f"{thr}x{hold}"] = dict(stats=stats(bl.pnl, bl.atr), n_events=int(len(bl)))
    fin = np.isfinite(b.ratio)
    diag["partition"][f"{thr}x{hold}"] = dict(small=stats(b.pnl[fin & (b.ratio < 1)], b.atr[fin & (b.ratio < 1)]),
                                              big=stats(b.pnl[fin & (b.ratio >= 1)], b.atr[fin & (b.ratio >= 1)]),
                                              n_ratio_nan=int((~fin).sum()))
    diag["independence"][f"{thr}x{hold}"] = stats(b.pnl[b.mid], b.atr[b.mid])
    rows.append(r)
for hold in (5, 10):
    bs = book(events(w, SUB_BAND[0], SUB_BAND[1], hold), hold)
    diag["sub_band"][f"hold{hold}"] = dict(stats=stats(bs.pnl, bs.atr), n_events=int(len(bs)))

print("\n=== IS grid (fade spec flow, MGC 0.35/RT, ATR20-normalised; IS report weeks 2012-06-05..2022-08-23) ===")
print(f"{'cell':>34} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12}")
for r in rows:
    tag = f"thr {r['thr']} x hold {r['hold']}" + (" [scarce]" if r["scarce"] else "") + \
          (" [auto-SUBSUMED]" if r["auto_subsumed"] else "")
    print(fmt(r["IS"], tag))
print("--- cost x1.5 (0.525/RT)")
for r in rows:
    print(fmt(r["cost15"], f"thr {r['thr']} x hold {r['hold']} cost1.5"))
print("--- legs (long = fade z<0 / short = fade z>0)")
for k, v in diag["legs"].items():
    print(fmt(v["long"], f"{k} LONG")); print(fmt(v["short"], f"{k} SHORT"))
print("--- (a) sub-threshold band 0.25<=|z|<0.5, same rule")
for k, v in diag["sub_band"].items():
    print(fmt(v["stats"], f"sub-band {k}"))
print("--- (b) late-entry placebo (entry after release+7d, same events)")
for k, v in diag["late"].items():
    print(fmt(v["stats"], f"{k} LATE"))
print("--- (c) concurrent price-move partition |ret_wk|/(sigma63*sqrt5) <1 (small) / >=1 (big), IS-only")
for k, v in diag["partition"].items():
    print(fmt(v["small"], f"{k} small-move")); print(fmt(v["big"], f"{k} big-move"))
print("--- (d) independence subset: all r24 gauges in 20-80 mid-band")
for k, v in diag["independence"].items():
    print(fmt(v, f"{k} r24-midband"))
print("--- mark verification: first 3 booked events of thr 1.0 x hold 5 (NY time) and first 2 after the H1 splice")
_b = books[(1.0, 5)]
for r in pd.concat([_b.head(3), _b[_b.t_in >= np.datetime64(h1x.index.min().tz_localize(None))].head(2)]).itertuples():
    print(f"  rd {r.rd.date()} z {r.z:+.2f} side {r.side:+.0f} in {pd.Timestamp(r.t_in, tz='UTC').tz_convert(NY)} "
          f"out {pd.Timestamp(r.t_out, tz='UTC').tz_convert(NY)} atr20 {r.atr:.2f} pnl {r.pnl:+.2f}")
print("--- execution notes per cell")
for r in rows:
    print(f"thr {r['thr']} x hold {r['hold']}: events {r['n_events']}, booked {r['n_booked']}, ATR-NaN {r['n_atr_nan']}, "
          f"entry advanced (no bars on scheduled day) {r['n_entry_advanced']}, exit mark stale {r['n_exit_stale']}")

# ---------------------------------------------------------------- selection (r61 form)
by = {(r["thr"], r["hold"]): r for r in rows}
ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= IS_N_FLOOR],
                key=lambda r: -(r["IS"].get("t") if r["IS"].get("t") is not None and np.isfinite(r["IS"].get("t")) else -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    sib = by[(cand["thr"], 10 if cand["hold"] == 5 else 5)]     # other hold at the same thr
    if (sib["IS"].get("avg_R") or -1) > 0:
        winner = cand; break
    verdict[f"sibling_fail_{cand['thr']}x{cand['hold']}"] = True
if winner is not None:
    thr, hold = winner["thr"], winner["hold"]; k = f"{thr}x{hold}"
    a = winner["IS"]
    verdict["t_ge_2"] = bool(a["t"] >= 2)
    verdict["halves_both_positive"] = bool(a["halves"] == [1.0, 1.0])
    verdict["cost15_positive"] = bool((winner["cost15"].get("avg_R") or -1) > 0)
    verdict["sibling_positive"] = True
    sb = diag["sub_band"][f"hold{hold}"]["stats"]
    verdict["a_subband_below"] = bool((sb.get("avg_R") if sb.get("n", 0) >= 10 else -9e9) < a["avg_R"])
    lt = diag["late"][k]["stats"]
    verdict["b_late_below"] = bool((lt.get("avg_R") if lt.get("n", 0) >= 10 else -9e9) < a["avg_R"])
    sm = diag["partition"][k]["small"]
    verdict["c_small_move_positive"] = bool((sm.get("avg_R") or -1) > 0)
    ind = diag["independence"][k]
    verdict["d_indep_n"] = int(ind.get("n", 0)); verdict["d_indep_floor"] = INDEP_FLOOR[(thr, hold)]
    verdict["d_independent"] = bool((thr, hold) not in AUTO_SUBSUMED and ind.get("n", 0) >= INDEP_FLOOR[(thr, hold)]
                                    and (ind.get("avg_R") or -1) > 0)
    ALL = all(verdict[x] for x in ["t_ge_2", "halves_both_positive", "cost15_positive", "sibling_positive",
                                   "a_subband_below", "b_late_below", "c_small_move_positive", "d_independent"])
    print(f"\nSELECTED (max IS t): thr {thr} x hold {hold}{' [scarce]' if winner['scarce'] else ''} | gates: {verdict}")
    if not verdict["d_independent"] and all(verdict[x] for x in ["t_ge_2", "halves_both_positive", "cost15_positive",
                                                                "a_subband_below", "b_late_below", "c_small_move_positive"]):
        print("Family SUBSUMED by r24 (independence gate): the OOS seal is NOT opened, no shot spent.")
    print(f"\nIS VERDICT: {'PASS - one OOS shot is earned' if ALL else 'FAIL - family dies at IS'}")
    verdict["is_pass"] = bool(ALL)
else:
    print(f"\nNo selectable cell passes n>={IS_N_FLOOR} & t>=2 & sibling rule; family fails at IS, OOS not opened.")
    verdict["is_pass"] = False

json.dump(dict(family="r64 attempt 47: gold COT spec-flow fade (MGC)", mode="IS_ONLY",
               is_cut=str(CUT.date()), is_weeks=int(len(w)), cost=COST, cost15=COST15,
               data_notes=dict(cross_check=check, release_distribution=release_dist,
                               holiday_delayed_weeks=int(cot[(cot.rd >= SPAN[0]) & (cot.rd <= SPAN[1])].delayed.sum()),
                               shutdown_weeks=int(cot[(cot.rd >= SPAN[0]) & (cot.rd <= SPAN[1])].shut.sum()),
                               intraday_frame=[str(bars.index.min()), str(bars.index.max())],
                               h1_start=str(h1x.index.min())),
               signal_counts=sig_counts,
               grid=rows, diagnostics=diag,
               winner=(dict(thr=winner["thr"], hold=winner["hold"], scarce=winner["scarce"], IS=winner["IS"])
                       if winner else None),
               verdict=verdict, is_pass=bool(verdict.get("is_pass", False))),
          open("results/r64_cotflow_is.json", "w"), indent=1, default=float)
print("\nwrote results/r64_cotflow_is.json (IS only)")
