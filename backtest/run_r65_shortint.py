"""Round 65 attempt 48: aggregate short-interest information-lag regime (RRZ)
on SPX/NDX - frozen per reference/goal_ledger.md 'Attempt 48' registration and
its 2026-09-03 pre-run data declaration (basket = the 80 FINRA series on disk,
data/shortint/; GOOG has no series, the 19 outage tickers are excluded).

IS-ONLY BY DEFAULT (OOS firewall): the sealed rows - sessions governed by
settlement #90 onward (registered: 2024-10-15..2025-12-31) - are dropped at
frame build and no statistic is ever computed on them. Output:
results/r65_shortint_is.json (IS only; no OOS keys).
--unseal (refuses unless UNSEAL_OK=1) rebuilds the full frame and evaluates
ONLY the winner cell recorded in the IS json, at the program bar plus the
registered OOS qualifier (e); writes results/r65_shortint_oos.json."""
import pandas as pd, numpy as np, json, os, sys, re, datetime as dt, warnings
from bisect import bisect_right
warnings.filterwarnings("ignore")

UNSEAL = "--unseal" in sys.argv
if UNSEAL and os.environ.get("UNSEAL_OK") != "1":
    raise SystemExit("--unseal refused: the seal opens only with UNSEAL_OK=1 (one shot).")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame, rth_of = ns["load_frame"], ns["rth_of"]

MICRO = {"SPX": 0.35, "NDX": 1.0}   # micro RT, points; RTY dropped per registration
AMORT = 20                           # MICRO/20 per daily booking (attempt 44-46 convention)
WINDOW = 24                          # trailing settlements INCLUDING t (~1 year)
BURN_IN = 24                         # registered: signal defined from the 25th settlement
AVAIL_LAG = 10                       # known at the close of the 10th trading day after t
MIN_REPORTERS = 60
IS_SETTLEMENTS = 89                  # registered split: IS = first 89 defined settlements
N_FLOOR = 120
NPERM = 1000
SI_DIR = "data/shortint"
GROUPS = {"pooled": ["SPX", "NDX"], "NDX": ["NDX"]}
rng = np.random.default_rng(65)


def stats(p, a, floor=10):
    r = np.asarray(p, float) / np.asarray(a, float)
    ok = np.isfinite(r); p, r = np.asarray(p, float)[ok], r[ok]
    if len(p) < floor: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


# ------------------------------------------------------------------ PMI regime (gate d / qualifier e)
raw = open("data/econ_events_us_high_fxs.json").read()
ev = json.loads(raw[raw.find("{"):])["result"]["events"]
pmi = []
for e in ev:
    if (e.get("n") or "") == "ISM Manufacturing PMI" and e.get("a") is not None:
        et = pd.Timestamp(e["d"]).tz_convert("America/New_York").tz_localize(None)
        pmi.append((et.date(), float(e["a"])))
pmi.sort()


def last_before(rel, keys):
    lvl, j, out = np.nan, 0, []
    for k in keys:
        while j < len(rel) and rel[j][0] < k:
            lvl = rel[j][1]; j += 1
        out.append(lvl)
    return out


# ------------------------------------------------------------------ short-interest signal (signal side)
tickers = [t.strip() for t in open(f"{SI_DIR}/tickers.txt") if t.strip()]
assert len(tickers) == 100
comp = json.load(open(f"{SI_DIR}/composition.json"))["constituents"]
company = {c["ticker"]: c["company"] for c in comp}
series, status = {}, {}
for t in tickers:
    fp = f"{SI_DIR}/si_{t}.json"
    if not os.path.exists(fp):
        status[t] = "not_fetched"; continue
    d = json.load(open(fp))
    status[t] = d["status"]
    if d["status"] != "ok" or not d["rows"]:
        continue
    assert d["estimate_lines_below_table"] == [], f"{t}: estimate rows present"
    rows = pd.DataFrame(d["rows"])
    rows["settlement_date"] = pd.to_datetime(rows.settlement_date).dt.date
    rows = rows[np.isfinite(rows.short_position.astype(float)) & (rows.short_position > 0)]
    if t == "META":   # provenance flag: rows before 2022-06-15 are not Meta Platforms
        rows = rows[rows.settlement_date >= dt.date(2022, 6, 15)]
    assert rows.settlement_date.is_unique, t
    series[t] = rows.set_index("settlement_date").short_position.astype(float)
basket = sorted(series)
excluded = [t for t in tickers if t not in series]
assert len(basket) == 80, f"basket must be the 80 declared series, got {len(basket)}"
assert "GOOG" in excluded and "GOOGL" in basket

# point-in-time membership: a ticker ADDED in a quarter window is a non-member for every
# settlement before that window's END date; same-window Removed+Added of the same company
# (holding-company re-listing) is continuous; departed members are not added back.
chg = json.load(open(f"{SI_DIR}/index_changes.json"))["changes"]
_STOP = {"inc", "plc", "corp", "corporation", "co", "ltd", "the", "company"}
norm = lambda s: " ".join(w for w in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if w not in _STOP)
member_from, relist = {}, set()
for r in chg:
    if r["change"] != "Added" or r["ticker"] not in basket:
        continue
    if any(x["change"] == "Removed" and x["window_end"] == r["window_end"]
           and norm(x["company"]) == norm(r["company"]) for x in chg):
        relist.add(r["ticker"]); continue
    we = pd.Timestamp(r["window_end"]).date()
    member_from[r["ticker"]] = max(member_from.get(r["ticker"], dt.date(1900, 1, 1)), we)

all_dates = sorted(set().union(*[set(s.index) for s in series.values()]))
SI = pd.DataFrame(index=pd.Index(all_dates, name="settlement"))
for t in basket:
    s = series[t].reindex(all_dates).astype(float)
    if t in member_from:
        s[[x < member_from[t] for x in all_dates]] = np.nan
    SI[t] = np.log(s)
cov = SI.notna().sum(axis=1)
A = SI.mean(axis=1).where(cov >= MIN_REPORTERS)          # < 60 reporters -> undefined, regime carries
pct = A.rolling(WINDOW, min_periods=WINDOW).apply(
    lambda w: ((w[:-1] < w[-1]).sum() + 0.5 * (w[:-1] == w[-1]).sum()) / (len(w) - 1) * 100, raw=True)
pct.iloc[:BURN_IN] = np.nan                                # 24-report burn-in: first signal = 25th settlement
st = pd.DataFrame(dict(A=A, cov=cov, p=pct))


# NYSE full-closure holidays 2020-2025. The CFD feeds carry early-close sessions on these days
# (e.g. MLK Day 2021-01-18, 42 bars, last print 12:55); they are not trading days for the
# registered +10 availability count. NYSE half-days remain trading days but have no 15:55 print.
NYSE_HOL = set(pd.to_datetime("""
2020-01-01 2020-01-20 2020-02-17 2020-04-10 2020-05-25 2020-07-03 2020-09-07 2020-11-26 2020-12-25
2021-01-01 2021-01-18 2021-02-15 2021-04-02 2021-05-31 2021-07-05 2021-09-06 2021-11-25 2021-12-24
2022-01-17 2022-02-21 2022-04-15 2022-05-30 2022-06-20 2022-07-04 2022-09-05 2022-11-24 2022-12-26
2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 2023-09-04 2023-11-23 2023-12-25
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
""".split()).date)


def build_days(idx):
    """Feed sessions with >= 40 RTH bars (r37 convention). Returns (trading days, bookable frame):
    trading days = feed sessions on NYSE trading days (half-days count, full holidays do not);
    bookable sessions = trading days whose last RTH bar is the 15:55 ET print (the registered
    session close). Bookings run 15:55 print to 15:55 print; ATR20 = rolling 20 bookable-session
    ranges, lag 1; 200-SMA over bookable-session closes. This reproduces the registered calendar
    (regime sessions from 2021-02-02, sealed from 2024-10-15, 119 tradable settlements)."""
    rth = rth_of(load_frame(idx))
    g = rth.groupby("skey")
    d = g.agg(o=("open", "first"), c=("close", "last"), hi=("high", "max"),
              lo=("low", "min"), nb=("close", "size"), last_hm=("hm", "last"), first_hm=("hm", "first"))
    d = d[(d.nb >= 40) & np.isfinite(d.o) & np.isfinite(d.c)]
    d = d[[k not in NYSE_HOL for k in d.index]]
    tdays = list(d.index)
    # bookable = full session: 15:55 print AND first RTH bar by 09:35 (r53 convention; drops the two
    # partial feed days 2021-05-07 / 2022-04-06 and reproduces the registered 916 IS sessions)
    d = d[(d.last_hm == 1555) & (d.first_hm <= 935)].copy()
    d["atr20"] = (d.hi - d.lo).rolling(20).mean().shift(1)
    d["prevc"] = d.c.shift(1)
    d["trend"] = (d.c > d.c.rolling(200).mean()).astype(float).shift(1)   # state at the prior close
    return tdays, d


_built = {idx: build_days(idx) for idx in MICRO}
days = {idx: _built[idx][1] for idx in MICRO}
cal = _built["SPX"][0]                 # trading-day calendar for the +10 rule (SPX feed; NDX identical 2021-2025)
book_cal = list(days["SPX"].index)     # bookable sessions (15:55 print)


def avail_of(t):
    j = bisect_right(cal, t) + AVAIL_LAG - 1
    return cal[j] if j < len(cal) else None


st["avail"] = [avail_of(t) for t in st.index]
st["first_sess"] = [book_cal[bisect_right(book_cal, a)] if a is not None and bisect_right(book_cal, a) < len(book_cal)
                    else None for a in st.avail]
st["defined"] = st.p.notna()
st["tradable"] = st.first_sess.notna()
D = st[st.defined & st.tradable]
assert len(D) >= IS_SETTLEMENTS + 1
IS_D, OOS_D = D.iloc[:IS_SETTLEMENTS], D.iloc[IS_SETTLEMENTS:]
OOS_START = OOS_D.first_sess.iloc[0]        # calendar date only (signal side), no return read
IS_LAST = book_cal[bisect_right(book_cal, OOS_START) - 2]

# (f) signal-side pre-run checks - no returns
for t, r in D.iterrows():
    n_between = bisect_right(cal, r.avail) - bisect_right(cal, t)
    assert t < r.avail < r.first_sess and n_between == AVAIL_LAG, (t, r.avail, r.first_sess)
non_member_2021 = sorted(t for t in basket if t in member_from and member_from[t] > dt.date(2021, 1, 15))
print("=== signal-side pre-run checks (no returns) ===")
print(f"basket: {len(basket)} FINRA series of 100 registered; excluded {len(excluded)}: "
      f"{' '.join(excluded)}")
print(f"membership rollback: added-in-table {sorted((k, str(v)) for k, v in member_from.items())}; re-listings treated "
      f"continuous {sorted(relist)}; non-members at 2021-01-15: {len(non_member_2021)}/{len(basket)} "
      f"({len(non_member_2021)/len(basket)*100:.1f}% < 20% cap) {non_member_2021}")
print(f"settlements on disk: {len(st)} ({st.index[0]}..{st.index[-1]}); reporting coverage "
      f"min {cov.min()} / median {cov.median():.0f} / max {cov.max()}; below {MIN_REPORTERS}: {(cov < MIN_REPORTERS).sum()}")
print(f"defined-and-tradable settlements: {len(D)} ({D.index[0]}..{D.index[-1]}); coverage on those "
      f"min {D['cov'].min()} / median {D['cov'].median():.0f} / max {D['cov'].max()}")
print(f"split: IS = first {IS_SETTLEMENTS} settlements ({IS_D.index[0]}..{IS_D.index[-1]}), regime sessions "
      f"{IS_D.first_sess.iloc[0]}..{IS_LAST}; sealed = {len(OOS_D)} settlements from {OOS_D.index[0]}, "
      f"sessions from {OOS_START} (registered: 2024-09-30 / 2024-10-15)")
print(f"availability: settlement t -> known at close of the {AVAIL_LAG}th NYSE trading day after t -> regime from the "
      f"next bookable session (asserted for all {len(D)} settlements; e.g. {D.index[0]} -> {D.avail.iloc[0]} -> "
      f"{D.first_sess.iloc[0]}; last: {D.index[-1]} -> {D.avail.iloc[-1]} -> {D.first_sess.iloc[-1]})")
print(f"calendar: {sum(1 for k in cal if dt.date(2021,1,1) <= k <= dt.date(2025,12,31))} NYSE trading days in the SPX feed 2021-2025, "
      f"{sum(1 for k in book_cal if dt.date(2021,1,1) <= k <= dt.date(2025,12,31))} with a 15:55 print (bookable)")

# ------------------------------------------------------------------ session frames
p_carry = st.p.ffill()                                       # skipped settlement -> prior regime carries
avail_list = [(a, t) for t, a in zip(st.index, st.avail) if a is not None]
avail_dates = [a for a, _ in avail_list]


def with_regime(d):
    keys = d.index.tolist()
    blk, pval = [], []
    for k in keys:
        j = bisect_right(avail_dates, k) - 1
        while j >= 0 and avail_dates[j] >= k:      # regime applies from the session AFTER availability
            j -= 1
        if j < 0:
            blk.append(-1); pval.append(np.nan); continue
        t = avail_list[j][1]
        blk.append(all_dates.index(t)); pval.append(p_carry.get(t, np.nan))
    d = d.copy()
    d["blk"] = blk; d["p"] = pval
    d["pmi"] = last_before(pmi, keys)
    d = d[np.isfinite(d.p) & (d.index >= D.first_sess.iloc[0])]
    d["oos"] = np.array([k >= OOS_START for k in d.index])
    return d


frames = {}
for idx in MICRO:
    d = with_regime(days[idx])
    n_all = len(d)
    if not UNSEAL:
        d = d[~d.oos].copy()           # IS-ONLY MASK: sealed rows leave the frame here and never return
        print(f"{idx}: {n_all} regime sessions -> {len(d)} IS rows ({d.index[0]}..{d.index[-1]}; "
              f"registered 916); sealed rows dropped at build")
    frames[idx] = d
    del d

REG = {"LOW50": lambda p: p <= 50, "LOW25": lambda p: p <= 25,
       "MID": lambda p: (p > 50) & (p < 75), "HIGH": lambda p: p >= 75}


def regime_mask(d, reg):
    return (d.trend == 1.0) if reg == "TREND" else REG[reg](d.p)


def book(d, idx, mask, mult=1.0):
    """Daily close-to-close bookings (15:55 ET print) on sessions where mask holds,
    net of MICRO/20 per booking and one full micro RT per regime toggle (entry
    and exit of each contiguous episode = 2 RT), amortized evenly over the episode."""
    m = np.asarray(mask, bool)
    start = m & ~np.r_[False, m[:-1]]
    ep = np.cumsum(start) * m
    ok = m & np.isfinite(d.prevc.values) & np.isfinite(d.atr20.values) & (d.atr20.values > 0)
    s = d[ok]; epi = ep[ok]
    sizes = np.bincount(ep)[epi]
    pnl = (s.c.values - s.prevc.values) - mult * (MICRO[idx] / AMORT + 2 * MICRO[idx] / sizes)
    return pd.DataFrame(dict(skey=s.index, idx=idx, pnl=pnl, atr=s.atr20.values,
                             R=pnl / s.atr20.values, blk=s.blk.values,
                             nomfg=~(s.pmi.values < 50), oos=s.oos.values))


def cell(reg, grp, mult=1.0, masks=None):
    parts = [book(frames[i], i, masks[i] if masks else regime_mask(frames[i], reg), mult)
             for i in GROUPS[grp]]
    return pd.concat(parts).sort_values(["skey", "idx"]).reset_index(drop=True)


def universe(grp):
    keys = []
    for i in GROUPS[grp]:
        d = frames[i]
        ok = np.isfinite(d.prevc) & np.isfinite(d.atr20) & (d.atr20 > 0) & ~d.oos
        keys += [(k, i) for k in d.index[ok]]
    return sorted(keys)


def diff_t(subA, subB, grp):
    """Paired daily-difference t of avgR_A - avgR_B over the grouping's IS bookings
    (handles overlapping session sets; mean of D equals avgR_A - avgR_B exactly)."""
    U = universe(grp); N = len(U); pos = {k: j for j, k in enumerate(U)}
    a, b = np.zeros(N), np.zeros(N)
    for r in subA.itertuples(): a[pos[(r.skey, r.idx)]] = r.R
    for r in subB.itertuples(): b[pos[(r.skey, r.idx)]] = r.R
    Dd = a / (len(subA) / N) - b / (len(subB) / N)
    return dict(diff=float(Dd.mean()), t=float(Dd.mean() / Dd.std() * np.sqrt(N)) if Dd.std() > 0 else np.nan,
                n_universe=N)


all_blocks = sorted(set().union(*[set(frames[i].blk) for i in MICRO]))


def episodes(sub):
    """Settlement-level episodes: runs of consecutive availability blocks in regime."""
    blks = sorted(sub.blk.unique())
    runs, cur = [], [blks[0]]
    for b0, b1 in zip(blks[:-1], blks[1:]):
        if all_blocks.index(b1) == all_blocks.index(b0) + 1: cur.append(b1)
        else: runs.append(cur); cur = [b1]
    runs.append(cur)
    out = []
    for run in runs:
        x = sub[sub.blk.isin(run)]
        out.append(dict(start=str(all_dates[run[0]]), end=str(all_dates[run[-1]]), blocks=len(run),
                        n=int(len(x)), meanR=float(x.R.mean())))
    return out


# ------------------------------------------------------------------ IS grid
SEL = [("LOW50", "pooled"), ("LOW25", "pooled"), ("LOW50", "NDX"), ("LOW25", "NDX")]
DIAG = [("MID", "pooled"), ("HIGH", "pooled"), ("TREND", "pooled"),
        ("MID", "NDX"), ("HIGH", "NDX"), ("TREND", "NDX")]
rows = []
for reg, grp in SEL + DIAG:
    sub = cell(reg, grp)
    c15 = cell(reg, grp, mult=1.5)
    nsess = sum(int((~frames[i].oos).sum()) for i in GROUPS[grp])
    eps = episodes(sub) if len(sub) else []
    rows.append(dict(reg=reg, group=grp, selectable=(reg, grp) in SEL,
                     IS=stats(sub.pnl, sub.atr), IS_cost15=stats(c15.pnl, c15.atr),
                     IS_nomfg=stats(sub.pnl[sub.nomfg], sub.atr[sub.nomfg]),
                     share=float(len(sub) / nsess) if nsess else np.nan,
                     episodes=eps, ep_pos=sum(1 for e in eps if e["meanR"] > 0), ep_n=len(eps),
                     mean_ep_blocks=float(np.mean([e["blocks"] for e in eps])) if eps else np.nan,
                     _sub=sub))
R = {(r["reg"], r["group"]): r for r in rows}

if not UNSEAL:
    print("\n=== signal-side regime structure (IS blocks, no returns) ===")
    for reg, grp in SEL:
        r = R[(reg, grp)]
        print(f"{reg:>6} {grp:>7}: session share {r['share']*100:.1f}%, episodes {r['ep_n']}, "
              f"mean episode {r['mean_ep_blocks']:.2f} blocks")

    print("\n=== IS grid (daily 15:55 ET close-to-close, long only, ATR20-normalized, net of MICRO/20 + toggle RTs) ===")
    print(f"{'reg':>6} {'group':>7} {'sel':>3} | {'n':>5} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | "
          f"{'share':>5} {'eps+/n':>7} | {'nomfg avgR (n)':>16} | {'x1.5 avgR':>9}")
    for r in rows:
        a, b, c = r["IS"], r["IS_nomfg"], r["IS_cost15"]
        if a.get("n", 0) < 10:
            print(f"{r['reg']:>6} {r['group']:>7} {'*' if r['selectable'] else '':>3} | n {a.get('n')} (below floor)")
            continue
        print(f"{r['reg']:>6} {r['group']:>7} {'*' if r['selectable'] else '':>3} | {a['n']:>5} {a['wr']*100:>5.1f}% "
              f"{a['pf']:>5.2f} {a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | "
              f"{r['share']*100:>4.0f}% {r['ep_pos']:>3}/{r['ep_n']:<3} | "
              f"{b.get('avg_R', float('nan')):>+7.3f} (n{b.get('n'):>4})    | {c.get('avg_R', float('nan')):>+8.3f}")

    # ---------------------------------------------------------------- selection (r61 rule + registered gates)
    sel_rows = [r for r in rows if r["selectable"]]
    ranked = sorted([r for r in sel_rows if r["IS"].get("n", 0) >= N_FLOOR],
                    key=lambda r: -(r["IS"].get("t") or -99))
    winner, verdict = None, {}
    for cand in ranked:
        if (cand["IS"].get("t") or -9) < 2:
            break
        other = "LOW25" if cand["reg"] == "LOW50" else "LOW50"
        sib = R[(other, cand["group"])]                     # registered (g): other threshold, same grouping
        sib_ok = sib["IS"].get("n", 0) >= 30 and (sib["IS"].get("avg_R") or -1) > 0
        sib61 = [r for r in sel_rows if (r["reg"] == cand["reg"]) != (r["group"] == cand["group"])
                 and r["IS"].get("n", 0) >= 30]
        pos61 = sum(1 for r in sib61 if (r["IS"].get("avg_R") or -1) > 0)
        verdict.setdefault("sibling_checks", []).append(
            dict(cell=f"{cand['reg']} {cand['group']}", registered_sibling_positive=bool(sib_ok),
                 r61_majority=bool(len(sib61) == 0 or pos61 >= len(sib61) / 2)))
        if sib_ok and (len(sib61) == 0 or pos61 >= len(sib61) / 2):
            winner = cand
            break
    print(f"\nranking (n >= {N_FLOOR}): " + ", ".join(f"{r['reg']} {r['group']} t {r['IS']['t']:+.2f}" for r in ranked))

    maxstat = None
    if winner is not None:
        w, grp = winner, winner["group"]
        low, high, mid, trend = w, R[("HIGH", grp)], R[("MID", grp)], R[("TREND", grp)]
        low25, low50 = R[("LOW25", grp)], R[("LOW50", grp)]
        # (a) HIGH-regime control: LOW - HIGH difference with its t
        dh = diff_t(low["_sub"], high["_sub"], grp)
        verdict["a_low_minus_high"] = dh
        verdict["a_pass"] = bool((high["IS"].get("avg_R") or 9e9) < (low["IS"].get("avg_R") or -9e9))
        # (b) gradient band: LOW25 -> LOW50 -> MID -> HIGH non-increasing
        g = [x["IS"].get("avg_R", np.nan) for x in (low25, low50, mid, high)]
        verdict["b_gradient"] = [float(v) for v in g]
        verdict["b_pass"] = bool(all(np.isfinite(g)) and all(g[i] >= g[i + 1] for i in range(3)))
        # (c)(i) trend-state drift control: LOW must beat the >200-SMA long by t >= 2 (paired difference)
        dtr = diff_t(low["_sub"], trend["_sub"], grp)
        verdict["c1_low_minus_trend"] = dtr
        verdict["c1_pass"] = bool((dtr["t"] or -9) >= 2)
        # (c)(ii) r16-B randomly-timed-regime max-stat null: per draw, one random regime per
        # threshold (matched block coverage share and mean episode length in availability blocks),
        # applied to both groupings with the same cost model; max avgR over the 4 selectable cells.
        blocks = all_blocks; bpos = {b: j for j, b in enumerate(blocks)}
        params = {}
        for thr in ("LOW50", "LOW25"):
            on = np.array([bool(REG[thr](p_carry.get(all_dates[b], np.nan))) for b in blocks])
            starts = np.flatnonzero(on & ~np.r_[False, on[:-1]])
            ends = np.flatnonzero(on & ~np.r_[on[1:], False])
            lens = ends - starts + 1
            params[thr] = dict(share=float(on.mean()), mean_len=float(lens.mean()), n_runs=int(len(lens)))

        def random_regime(share, mean_len):
            p_on = min(1.0, 1.0 / mean_len)
            off_len = mean_len * (1 - share) / share
            p_off = min(1.0, 1.0 / off_len)
            out = np.zeros(len(blocks), bool); i = 0; state = rng.random() < share
            while i < len(blocks):
                L = int(rng.geometric(p_on if state else p_off))
                out[i:i + L] = state; i += L; state = not state
            return out

        null = np.empty(NPERM); real_share, real_len = [], []
        for k in range(NPERM):
            best = -np.inf
            for thr in ("LOW50", "LOW25"):
                rr = random_regime(params[thr]["share"], params[thr]["mean_len"])
                real_share.append(rr.mean())
                st_ = np.flatnonzero(rr & ~np.r_[False, rr[:-1]]); en_ = np.flatnonzero(rr & ~np.r_[rr[1:], False])
                if len(st_): real_len.append(float((en_ - st_ + 1).mean()))
                masks = {i: np.array([rr[bpos[b]] for b in frames[i].blk], bool) for i in MICRO}
                for g_ in GROUPS:
                    s_ = cell(thr, g_, masks=masks)
                    if len(s_) >= 10:
                        best = max(best, float(s_.R.mean()))
            null[k] = best
        obs = low["IS"]["avg_R"]
        maxstat = dict(n_perm=NPERM, params=params, null_p95=float(np.percentile(null, 95)),
                       null_median=float(np.median(null)), observed_avgR=float(obs),
                       p_value=float((null >= obs).mean()),
                       realized_share=float(np.mean(real_share)), realized_mean_len=float(np.mean(real_len)))
        verdict["c2_maxstat"] = maxstat
        verdict["c2_pass"] = bool(obs > maxstat["null_p95"])
        # (d) independence gate vs attempt 44: outside PMI < 50, n >= 120, avgR > 0, > HIGH on same sessions
        nm, nmh = low["IS_nomfg"], high["IS_nomfg"]
        verdict["d_nomfg"] = dict(low=nm, high=nmh)
        verdict["d_pass"] = bool(nm.get("n", 0) >= N_FLOOR and (nm.get("avg_R") or -1) > 0
                                 and (nm.get("avg_R") or -1) > (nmh.get("avg_R") or -9e9))
        # (g) halves, cost x1.5, episodes
        verdict["g_halves_same_sign"] = bool(low["IS"]["halves"][0] == low["IS"]["halves"][1] == 1.0)
        verdict["g_cost15_positive"] = bool((low["IS_cost15"].get("avg_R") or -1) > 0)
        verdict["g_episodes"] = dict(positive=low["ep_pos"], total=low["ep_n"])
        gates = ["a_pass", "b_pass", "c1_pass", "c2_pass", "d_pass", "g_halves_same_sign", "g_cost15_positive"]
        failed = [k for k in gates if not verdict[k]]
        verdict["failed_gates"] = failed
        verdict["is_pass"] = not failed
        verdict["subsumed"] = (not verdict["d_pass"]) and all(verdict[k] for k in gates if k != "d_pass")
        print(f"\nSELECTED CANDIDATE: {w['reg']} {w['group']} (IS n {w['IS']['n']} avgR {w['IS']['avg_R']:+.3f} t {w['IS']['t']:+.2f})")
        print(f"(a) LOW - HIGH: diff {dh['diff']:+.3f} t {dh['t']:+.2f} (HIGH avgR {high['IS'].get('avg_R', float('nan')):+.3f}) -> {'pass' if verdict['a_pass'] else 'FAIL'}")
        print(f"(b) gradient LOW25/LOW50/MID/HIGH avgR {['%+.3f' % v for v in g]} -> {'pass' if verdict['b_pass'] else 'FAIL'}")
        print(f"(c)(i) LOW - TREND(>200 SMA): diff {dtr['diff']:+.3f} t {dtr['t']:+.2f} (TREND avgR {trend['IS'].get('avg_R', float('nan')):+.3f}, n {trend['IS'].get('n')}) -> {'pass' if verdict['c1_pass'] else 'FAIL'}")
        print(f"(c)(ii) r16-B null: {NPERM} random regimes, params {params}; realized share {maxstat['realized_share']:.3f}, "
              f"mean len {maxstat['realized_mean_len']:.2f}; null median {maxstat['null_median']:+.4f}, p95 {maxstat['null_p95']:+.4f}, "
              f"observed {obs:+.4f}, p {maxstat['p_value']:.3f} -> {'pass' if verdict['c2_pass'] else 'FAIL'}")
        print(f"(d) independence (outside PMI<50): LOW avgR {nm.get('avg_R', float('nan')):+.3f} (n {nm.get('n')}) vs HIGH "
              f"{nmh.get('avg_R', float('nan')):+.3f} (n {nmh.get('n')}) -> {'pass' if verdict['d_pass'] else 'FAIL (SUBSUMED)'}")
        print(f"(g) halves {low['IS']['halves']}, cost x1.5 avgR {low['IS_cost15'].get('avg_R', float('nan')):+.3f}, "
              f"episodes {low['ep_pos']}/{low['ep_n']} positive")
        print(f"\nIS VERDICT: {'PASS - one OOS shot is earned (open only via --unseal with UNSEAL_OK=1)' if verdict['is_pass'] else 'FAIL - family dies at IS; seal NOT opened, no shot spent; failed ' + str(failed)}")
    else:
        verdict["is_pass"] = False
        print(f"\nNo selectable cell passes n >= {N_FLOOR}, t >= 2.0 and the sibling rule; family fails at IS, seal NOT opened.")

    json.dump(dict(family="Attempt 48 aggregate short-interest information-lag regime (RRZ) SPX/NDX",
                   basket=dict(n=len(basket), tickers=basket, excluded=excluded, member_from={k: str(v) for k, v in member_from.items()},
                               relistings=sorted(relist), non_members_2021_01_15=non_member_2021),
                   signal=dict(settlements=len(st), coverage_min=int(cov.min()), coverage_median=float(cov.median()),
                               coverage_max=int(cov.max()), defined_tradable=len(D), first_defined=str(D.index[0]),
                               last_defined=str(D.index[-1]), is_settlements=IS_SETTLEMENTS,
                               is_first_settlement=str(IS_D.index[0]), is_last_settlement=str(IS_D.index[-1]),
                               is_sessions_from=str(IS_D.first_sess.iloc[0]), is_sessions_to=str(IS_LAST),
                               sealed_from=str(OOS_START), is_rows={i: int(len(frames[i])) for i in MICRO},
                               availability_lag_sessions=AVAIL_LAG, window=WINDOW, burn_in=BURN_IN),
                   grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows if r["selectable"]],
                   diagnostics=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows if not r["selectable"]],
                   winner=({"reg": winner["reg"], "group": winner["group"], "IS": winner["IS"],
                            "IS_nomfg": winner["IS_nomfg"], "IS_cost15": winner["IS_cost15"]} if winner else None),
                   verdict=verdict, costs=dict(micro=MICRO, amort=AMORT, toggle="2 x micro RT per episode (entry+exit)")),
              open("results/r65_shortint_is.json", "w"), indent=1, default=float)
    raise SystemExit

# ------------------------------------------------------------------ --unseal: one shot on the recorded winner only
isj = json.load(open("results/r65_shortint_is.json"))
if not isj.get("winner") or not isj["verdict"].get("is_pass"):
    raise SystemExit("no IS-passed winner recorded; the seal stays closed.")
reg, grp = isj["winner"]["reg"], isj["winner"]["group"]
sub = cell(reg, grp); c15 = cell(reg, grp, mult=1.5); high = cell("HIGH", grp)
o, oh = sub[sub.oos], high[high.oos]
res = stats(o.pnl, o.atr); r15 = stats(c15[c15.oos].pnl, c15[c15.oos].atr); rh = stats(oh.pnl, oh.atr)
rnm = stats(o.pnl[o.nomfg], o.atr[o.nomfg])
PASS = (res.get("n", 0) >= 40 and (res.get("avg_R") or -1) > 0 and (res.get("t") or -9) >= 2
        and (res.get("pf") or 0) >= 1.15 and (r15.get("avg_R") or -1) > 0)
confounded = (rh.get("avg_R") or -9e9) >= (res.get("avg_R") or -9e9)
print(f"=== ONE-SHOT OOS on {reg} {grp} (burned now; sessions from {OOS_START}) ===")
print(f"n {res.get('n')} WR {res.get('wr', 0)*100:.1f}% PF {res.get('pf', float('nan')):.2f} avgR {res.get('avg_R', float('nan')):+.3f} "
      f"t {res.get('t', float('nan')):+.2f} halves {res.get('halves')}; cost x1.5 avgR {r15.get('avg_R', float('nan')):+.3f}")
print(f"qualifier (e): OOS HIGH avgR {rh.get('avg_R', float('nan')):+.3f} (n {rh.get('n')}); outside PMI<50: avgR {rnm.get('avg_R', float('nan')):+.3f} (n {rnm.get('n')})")
print(f"OOS GATE: {'PASS' if PASS else 'FAIL'}{' - PASS-CONFOUNDED (HIGH >= LOW on OOS): watch-item cap' if PASS and confounded else ''}")
json.dump(dict(cell=dict(reg=reg, group=grp), oos=res, oos_cost15=r15, oos_high_control=rh, oos_nomfg=rnm,
               gate_pass=bool(PASS), pass_confounded=bool(PASS and confounded), episodes=episodes(o) if len(o) else []),
          open("results/r65_shortint_oos.json", "w"), indent=1, default=float)
