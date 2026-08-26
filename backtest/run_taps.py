"""Round 14: two eyeball hypotheses about the Asia-range lines, tested properly.

H1 PING-PONG. After the range completes (10:30 HKT), price that taps one teal line
tends to tap the other before the 16:00-NY close - claimed strongest when the day is
not strongly directional. Descriptive: P(tap both | first tap), by causal trend
proxies and corr regime. Economics: fade the first tap toward the other line
(enter at the close of the tap bar, target = other line, stop = {0.5, 1.0} x range
width beyond the tapped line, flat 16:00 NY, $0.30 cost).

H2 MAGNET. When a teal line lands within tolerance of yesterday's high/low or the
prior NY session's high/low, it acts as a mean-reversion magnet. Descriptive:
line re-crossing counts, confluent vs not. Economics: when a 5m bar closes >= 0.5 x
range width away from a confluent line, enter toward it, target the line, symmetric
stop, flat 16:00 NY.

Pre-registered before running; every cell in the ledger; halves split at 2024-01-01.
"""
import pandas as pd, numpy as np, engine, json, warnings
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

HK, NY = ZoneInfo("Asia/Hong_Kong"), ZoneInfo("America/New_York")
COST = 0.30
pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def met(pnl, entry):
    pnl = np.asarray(pnl, float); entry = np.asarray(entry, float)
    if len(pnl) < 15:
        return dict(n=len(pnl), pf=np.nan, win=np.nan, exp=np.nan, t=np.nan)
    p = pnl / entry * 100
    return dict(n=len(pnl), pf=pfv(pd.Series(pnl)), win=float((pnl > 0).mean()),
                exp=float(pnl.mean()), t=float(p.mean() / p.std() * np.sqrt(len(p))))

g = engine.load_bars()
hk = g.copy()
hk.index = hk.index.tz_convert(HK)
hk["d"] = hk.index.date
ny_t = g.index.tz_convert(NY)
g2 = g.copy(); g2["ny_h"] = ny_t.hour; g2["ny_m"] = ny_t.minute
g2["hk_date"] = hk.index.date

# daily context (prior-day levels, ATR, trend proxies) on HKT days
days = []
for d, day in hk.groupby("d"):
    days.append(dict(d=d, hi=day.high.max(), lo=day.low.min(),
                     op=day.open.iloc[0], cl=day.close.iloc[-1]))
D = pd.DataFrame(days).set_index("d")
D["rng"] = D.hi - D.lo
D["atr14"] = D.rng.rolling(14).mean().shift(1)
D["ret1"] = (D.cl / D.cl.shift(1) - 1).shift(1)               # yesterday's return
D["ret3"] = (D.cl / D.cl.shift(3) - 1).shift(1)               # prior 3-day return
D["prev_hi"] = D.hi.shift(1); D["prev_lo"] = D.lo.shift(1)
D["prev_rng_atr"] = (D.rng / D.rng.rolling(14).mean()).shift(1)

# prior NY-session (09:30-16:00 NY) high/low, mapped to the NEXT HKT day
nys = g[(g2.ny_h * 60 + g2.ny_m >= 570) & (g2.ny_h < 16)]
nyd = nys.groupby(ny_t[(g2.ny_h * 60 + g2.ny_m >= 570) & (g2.ny_h < 16)].date).agg(
    ny_hi=("high", "max"), ny_lo=("low", "min"))
# NY session of calendar day X is "prior" for the HKT day that starts X 21:30 ET -> X+1 HKT
nyd.index = pd.to_datetime(nyd.index) + pd.Timedelta(days=1)
nyd.index = nyd.index.date

# deployed corr series for regime splits
import trades as TR
Corr = TR.corr_series(g)

rows = []
for d, day in hk.groupby("d"):
    r = day.between_time("09:30", "10:29")
    if len(r) < 10:
        continue
    rH, rL = r.high.max(), r.low.min()
    width = rH - rL
    if width <= 0:
        continue
    after = day[day.index > r.index[-1]]
    # cap at 16:00 NY of the same HKT day
    aft_ny = after.index.tz_convert(NY)
    cut = aft_ny.hour * 60 + aft_ny.minute <= 16 * 60
    after = after[cut]
    if len(after) < 30:
        continue
    hi_tap = after.index[after.high >= rH]
    lo_tap = after.index[after.low <= rL]
    t_hi = hi_tap[0] if len(hi_tap) else None
    t_lo = lo_tap[0] if len(lo_tap) else None
    if t_hi is None and t_lo is None:
        first, other_hit, gap_h = None, None, None
    elif t_lo is None or (t_hi is not None and t_hi < t_lo):
        first = "hi"; nxt = lo_tap[lo_tap > t_hi]
        other_hit = len(nxt) > 0
        gap_h = (nxt[0] - t_hi).total_seconds() / 3600 if other_hit else None
    else:
        first = "lo"; nxt = hi_tap[hi_tap > t_lo]
        other_hit = len(nxt) > 0
        gap_h = (nxt[0] - t_lo).total_seconds() / 3600 if other_hit else None

    ctx = D.loc[d] if d in D.index else None
    prev = dict(prev_hi=np.nan, prev_lo=np.nan)
    if ctx is not None:
        prev = dict(prev_hi=ctx.prev_hi, prev_lo=ctx.prev_lo)
    nyrow = nyd.loc[d] if d in nyd.index else None
    rows.append(dict(d=d, rH=rH, rL=rL, width=width, first=first,
                     other_hit=other_hit, gap_h=gap_h,
                     t_first=(t_hi if first == "hi" else t_lo) if first else None,
                     atr=ctx.atr14 if ctx is not None else np.nan,
                     ret1=ctx.ret1 if ctx is not None else np.nan,
                     ret3=ctx.ret3 if ctx is not None else np.nan,
                     prev_rng_atr=ctx.prev_rng_atr if ctx is not None else np.nan,
                     prev_hi=prev["prev_hi"], prev_lo=prev["prev_lo"],
                     ny_hi=nyrow.ny_hi if nyrow is not None else np.nan,
                     ny_lo=nyrow.ny_lo if nyrow is not None else np.nan))
T = pd.DataFrame(rows)
T["day_n"] = pd.to_datetime(T.d).dt.normalize()
T["corr"] = T.day_n.map(Corr)
T["os"] = T.day_n >= "2024-01-01"
T = T.dropna(subset=["corr", "ret3", "atr"]).reset_index(drop=True)

out = {"ledger": 0}

# ---------------------------------------------------------------- H1 descriptive
tap = T[T.first_.notna()] if hasattr(T, "first_") else T[T["first"].notna()]
def pboth(x):
    return float(x.other_hit.mean()), len(x)
p_all, n_all = pboth(tap)
calm = tap[np.abs(tap.ret3) <= np.nanmedian(np.abs(T.ret3))]
trend = tap[np.abs(tap.ret3) > np.nanmedian(np.abs(T.ret3))]
hi_c = tap[tap["corr"] > 0.5]; lo_c = tap[tap["corr"] <= 0.5]
desc = dict(all=pboth(tap), calm3=pboth(calm), trend3=pboth(trend),
            corr_hi=pboth(hi_c), corr_lo=pboth(lo_c),
            gap_med_h=float(tap[tap.other_hit].gap_h.median()))
# gradient of P(both) over |ret3| deciles
qb = pd.qcut(np.abs(tap.ret3), 10, duplicates="drop")
desc["grad_ret3"] = [float(x.other_hit.mean()) for _, x in tap.groupby(qb)]
out["h1_desc"] = desc
print("H1 P(tap other | first tap):")
for k, v in desc.items():
    print(f"  {k}: {v}")

# ---------------------------------------------------------------- H1 economics
bars = {d: day for d, day in hk.groupby("d")}
def fade_trades(sub, stop_mult):
    pnl, entry, dayl = [], [], []
    for _, r in sub.iterrows():
        day = bars[r.d]
        aft = day[day.index > r.t_first]
        aft_ny = aft.index.tz_convert(NY)
        aft = aft[aft_ny.hour * 60 + aft_ny.minute <= 16 * 60]
        if len(aft) < 2:
            continue
        e = aft.open.iloc[0]                    # enter next bar open after tap bar
        if r["first"] == "hi":                  # fade down toward rL
            tgt, stp, sgn = r.rL, r.rH + stop_mult * r.width, -1
        else:
            tgt, stp, sgn = r.rH, r.rL - stop_mult * r.width, +1
        res = None
        for _, b in aft.iterrows():
            hit_t = b.low <= tgt if sgn < 0 else b.high >= tgt
            hit_s = b.high >= stp if sgn < 0 else b.low <= stp
            if hit_t and hit_s:
                res = stp; break                # ambiguous bar -> assume stop (worst case)
            if hit_s: res = stp; break
            if hit_t: res = tgt; break
        px = res if res is not None else aft.close.iloc[-1]
        pnl.append(sgn * (px - e) - COST - (0.30 if res == stp else 0))
        entry.append(e); dayl.append(r.day_n)
    return pd.DataFrame(dict(pnl=pnl, entry=entry, day=dayl))

h1 = {}
for label, sub in (("all", tap), ("calm3", calm), ("corr_hi", hi_c),
                   ("calm3_corr_hi", calm[calm["corr"] > 0.5])):
    for sm in (0.5, 1.0):
        f = fade_trades(sub, sm)
        f["os"] = pd.to_datetime(f.day) >= "2024-01-01"
        m = met(f.pnl, f.entry)
        m["is_"] = met(f.pnl[~f.os], f.entry[~f.os])
        m["os_"] = met(f.pnl[f.os], f.entry[f.os])
        h1[f"{label}_s{sm}"] = m
        out["ledger"] += 1
        print(f"H1 fade {label} stop{sm}: n={m['n']} PF {m['pf']:.3f} t {m['t']:+.2f} "
              f"(IS {m['is_']['t']:+.2f} / OS {m['os_']['t']:+.2f})")
out["h1_econ"] = h1

# ---------------------------------------------------------------- H2 confluence
def confluent(row, tol):
    lev = [row.prev_hi, row.prev_lo, row.ny_hi, row.ny_lo]
    lines = []
    for line, nm in ((row.rH, "hi"), (row.rL, "lo")):
        if any(np.isfinite(l) and abs(line - l) <= tol * line for l in lev):
            lines.append(nm)
    return lines

def crossings(day, line, t0):
    aft = day[day.index > t0]
    aft_ny = aft.index.tz_convert(NY)
    aft = aft[aft_ny.hour * 60 + aft_ny.minute <= 16 * 60]
    if len(aft) < 2:
        return np.nan
    above = aft.close > line
    return int((above != above.shift()).sum() - 1)

TOL = 0.0010
cross_c, cross_n = [], []
mag_trades = {0.5: [], 0.75: []}
non_trades = {0.5: []}
for _, r in T.iterrows():
    day = bars[r.d]
    rng_bars = day.between_time("09:30", "10:29")
    t0 = rng_bars.index[-1]
    conf = confluent(r, TOL)
    for nm, line in (("hi", r.rH), ("lo", r.rL)):
        c = crossings(day, line, t0)
        if np.isfinite(c):
            (cross_c if nm in conf else cross_n).append(c)
    # magnet fade: first 5m close >= k*width away from a confluent line -> revert
    for k in mag_trades:
        for nm in conf:
            line = r.rH if nm == "hi" else r.rL
            aft = day[day.index > t0]
            aft_ny = aft.index.tz_convert(NY)
            aft = aft[aft_ny.hour * 60 + aft_ny.minute <= 16 * 60]
            trig = aft[np.abs(aft.close - line) >= k * r.width]
            if not len(trig):
                continue
            t1 = trig.index[0]
            e = aft[aft.index > t1]
            if len(e) < 2:
                continue
            ent = e.open.iloc[0]
            sgn = +1 if trig.close.iloc[0] < line else -1     # toward the line
            tgt = line
            stp = ent - sgn * k * r.width
            res = None
            for _, b in e.iterrows():
                hit_t = b.high >= tgt if sgn > 0 else b.low <= tgt
                hit_s = b.low <= stp if sgn > 0 else b.high >= stp
                if hit_s: res = stp; break
                if hit_t: res = tgt; break
            px = res if res is not None else e.close.iloc[-1]
            mag_trades[k].append(dict(pnl=sgn * (px - ent) - COST - (0.30 if res == stp else 0),
                                      entry=ent, day=r.day_n, corr=r["corr"]))
    # same trade on NON-confluent lines at k=0.5, as the control arm
    for nm in ("hi", "lo"):
        if nm in conf:
            continue
        line = r.rH if nm == "hi" else r.rL
        aft = day[day.index > t0]
        aft_ny = aft.index.tz_convert(NY)
        aft = aft[aft_ny.hour * 60 + aft_ny.minute <= 16 * 60]
        trig = aft[np.abs(aft.close - line) >= 0.5 * r.width]
        if not len(trig):
            continue
        t1 = trig.index[0]
        e = aft[aft.index > t1]
        if len(e) < 2:
            continue
        ent = e.open.iloc[0]
        sgn = +1 if trig.close.iloc[0] < line else -1
        stp = ent - sgn * 0.5 * r.width
        res = None
        for _, b in e.iterrows():
            hit_t = b.high >= line if sgn > 0 else b.low <= line
            hit_s = b.low <= stp if sgn > 0 else b.high >= stp
            if hit_s: res = stp; break
            if hit_t: res = line; break
        px = res if res is not None else e.close.iloc[-1]
        non_trades[0.5].append(dict(pnl=sgn * (px - ent) - COST - (0.30 if res == stp else 0),
                                    entry=ent, day=r.day_n))

out["h2_desc"] = dict(
    n_conf_lines=len(cross_c), n_non_lines=len(cross_n),
    cross_conf_mean=float(np.mean(cross_c)), cross_non_mean=float(np.mean(cross_n)),
    cross_conf_med=float(np.median(cross_c)), cross_non_med=float(np.median(cross_n)))
print(f"\nH2 crossings: confluent lines {np.mean(cross_c):.2f} mean "
      f"({len(cross_c)} lines) vs non-confluent {np.mean(cross_n):.2f} ({len(cross_n)})")

h2 = {}
for k, lst in mag_trades.items():
    f = pd.DataFrame(lst)
    if not len(f):
        continue
    f["os"] = pd.to_datetime(f.day) >= "2024-01-01"
    m = met(f.pnl, f.entry)
    m["is_"] = met(f.pnl[~f.os], f.entry[~f.os]); m["os_"] = met(f.pnl[f.os], f.entry[f.os])
    h2[f"conf_k{k}"] = m; out["ledger"] += 1
    print(f"H2 magnet conf k={k}: n={m['n']} PF {m['pf']:.3f} t {m['t']:+.2f} "
          f"(IS {m['is_']['t']:+.2f} / OS {m['os_']['t']:+.2f})")
    hc = f[f.get("corr", pd.Series(index=f.index)).gt(0.5)] if "corr" in f else f.iloc[0:0]
    if len(hc) >= 15:
        m2 = met(hc.pnl, hc.entry); h2[f"conf_k{k}_corrhi"] = m2; out["ledger"] += 1
        print(f"   corr>0.5 subset: n={m2['n']} PF {m2['pf']:.3f} t {m2['t']:+.2f}")
fn = pd.DataFrame(non_trades[0.5])
fn["os"] = pd.to_datetime(fn.day) >= "2024-01-01"
mn = met(fn.pnl, fn.entry)
mn["is_"] = met(fn.pnl[~fn.os], fn.entry[~fn.os]); mn["os_"] = met(fn.pnl[fn.os], fn.entry[fn.os])
h2["non_k0.5"] = mn; out["ledger"] += 1
print(f"H2 magnet NON-confluent k=0.5 (control): n={mn['n']} PF {mn['pf']:.3f} t {mn['t']:+.2f} "
      f"(IS {mn['is_']['t']:+.2f} / OS {mn['os_']['t']:+.2f})")
out["h2_econ"] = h2

json.dump(out, open("results/taps.json", "w"), indent=1, default=str)
print(f"\nledger {out['ledger']} cells; written results/taps.json")
