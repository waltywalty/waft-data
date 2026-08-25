"""Round 10: the user's TradingView scripts, made mechanical and tested on
XAUUSD, SPX, NDX and RTY.

What each script contains that is actually testable:

  - "TJR-Style Sessions" draws session highs/lows only - no entry logic. Its
    testable content is the window set (NY AM trading against London-session
    levels), run here through the same CISD machinery as the others.
  - "ICT Venom" and "Silver Bullet" share one mechanism, CISD (change in the
    state of delivery): break of an opening range, then entry AGAINST the
    break when price closes back through the open of the candle run that
    produced it. Venom: OR 08:00-09:30 ET, trade to the close. Silver Bullet:
    OR 09:00-10:00, trade 10:00-11:00.
  - "Supertrend+RSI" is fully mechanical: Supertrend(10, 2.0) + RSI(14)
    crossing 55/45 inside NY hours, stop at the supertrend line (which trails),
    take profit at 2x the entry risk, flat at 17:00 ET. NOTE: in Pine v5/v6
    ta.supertrend returns direction -1 for an UPtrend, so the script's
    `upTrend = stDir == 1` trades longs when the supertrend is bearish. Both
    readings are tested: "as written" (inverted) and "as intended".

Costs: $0.30/oz gold, 0.6/2.0/0.4 index points round trip; every cell also
re-priced at zero cost. Splits: gold 2024+, SPX 2020+, NDX 2021+, RTY 2017+.
"""
import pandas as pd, numpy as np, warnings, json
import engine as gold_engine, index_data, trades
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
OUT = {"cells": []}


class Mkt:
    def __init__(self, name, df, cost, os_start):
        self.name, self.cost = name, cost
        self.os_start = pd.Timestamp(os_start)
        self.ix = df.index
        self.o, self.h, self.l, self.c = (df[x].values for x in ("open", "high", "low", "close"))
        self.et = df.index.tz_convert(NY)
        self.mins = self.et.hour * 60 + self.et.minute
        self.days = pd.unique(pd.Series(self.et.date))

    def rng(self, t0, t1):
        return self.ix.searchsorted(t0), self.ix.searchsorted(t1)

    def at(self, t):
        i = self.ix.searchsorted(t)
        if i < len(self.ix) and self.ix[i] == t:
            return float(self.o[i])
        if i > 0 and (t - self.ix[i - 1]) <= pd.Timedelta(minutes=30):
            return float(self.c[i - 1])
        return None

    def nyt(self, day, h, m=0):
        return pd.Timestamp(day.year, day.month, day.day, h, m, tz=NY).tz_convert("UTC")


def load_mkts():
    g = gold_engine.load_bars()
    mkts = [Mkt("XAU", g, 0.30, "2024-01-01"),
            Mkt("SPX", index_data.load("SPX"), 0.6, "2020-01-01"),
            Mkt("NDX", index_data.load("NDX"), 2.0, "2021-01-01"),
            Mkt("RTY", index_data.load("RTY"), 0.4, "2017-01-01")]
    return mkts


def cell(M, family, label, rows):
    if len(rows) < 30:
        print(f"   {M.name} {label:46s} too few trades ({len(rows)})")
        return
    d = pd.DataFrame(rows)
    d["day"] = pd.to_datetime(d.day)
    p = d.pnl
    pct = p / d.entry * 100
    pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
    a, b = d[d.day < M.os_start], d[d.day >= M.os_start]
    pa = a.pnl / a.entry * 100
    s = dict(n=len(d), win=float((p > 0).mean()), pf=pfx(p), exp=float(p.mean()),
             t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0,
             pf_zero_cost=pfx(p + M.cost),
             is_pf=pfx(a.pnl) if len(a) > 20 else np.nan,
             is_t=float(pa.mean() / pa.std() * np.sqrt(len(a))) if len(a) > 20 and pa.std() else 0.0,
             is_n=len(a), os_pf=pfx(b.pnl) if len(b) > 20 else np.nan, os_n=len(b))
    print(f"   {M.name} {label:46s} n={s['n']:>5} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
          f"t={s['t']:+.2f} | PF0={s['pf_zero_cost']:.3f} | IS {s['is_pf']:.3f} OS {s['os_pf']:.3f}")
    OUT["cells"].append({"mkt": M.name, "family": family, "label": label, **s})
    return d


def hit(M, j0, j1, side, stop, target):
    if j1 <= j0:
        return None, "time", None
    z = np.zeros(j1 - j0, bool)
    hs = z if stop is None else ((M.l[j0:j1] <= stop) if side == 1 else (M.h[j0:j1] >= stop))
    ht = z if target is None else ((M.h[j0:j1] >= target) if side == 1 else (M.l[j0:j1] <= target))
    a = hs | ht
    if not a.any():
        return None, "time", None
    k = int(np.argmax(a))
    return (stop, "stop", M.ix[j0 + k]) if hs[k] else (target, "target", M.ix[j0 + k])


# ============================================================ CISD reversal
# window sets: (OR start, OR end, break-scan start, trade end, label)
WINDOWS = {
    "venom":      ((8, 0), (9, 30), (9, 30), (16, 0), "Venom OR 08:00-09:30"),
    "silver":     ((9, 0), (10, 0), (10, 0), (11, 0), "Silver Bullet 10-11"),
    "silver_eod": ((9, 0), (10, 0), (10, 0), (16, 0), "Silver Bullet to EoD"),
    "tjr":        ((2, 0), (5, 0), (9, 30), (11, 0), "TJR: NY AM vs London"),
}


def cisd(M, wname, target):
    (oh, om), (eh, em), (sh, sm), (xh, xm), _ = WINDOWS[wname]
    rows = []
    for d in M.days:
        day = pd.Timestamp(d)
        t_or0, t_or1 = M.nyt(day, oh, om), M.nyt(day, eh, em)
        t_scan, t_end = M.nyt(day, sh, sm), M.nyt(day, xh, xm)
        j0, j1 = M.rng(t_or0, t_or1)
        if j1 - j0 < 6:
            continue
        orh, orl = float(M.h[j0:j1].max()), float(M.l[j0:j1].min())
        if orh <= orl:
            continue
        k0, k1 = M.rng(t_scan, t_end)
        if k1 <= k0:
            continue
        up = M.h[k0:k1] > orh
        dn = M.l[k0:k1] < orl
        if not (up.any() or dn.any()):
            continue
        ku = int(np.argmax(up)) if up.any() else 10 ** 9
        kd = int(np.argmax(dn)) if dn.any() else 10 ** 9
        brk = 1 if ku < kd else -1                       # first break side only
        kb = k0 + min(ku, kd)
        # CISD level: the open of the last opposite-body candle run before the
        # break (scan up to 5 bars back from the break bar)
        lvl = None
        for i in range(1, 6):
            j = kb - i
            if j < 0:
                break
            body = M.c[j] - M.o[j]
            if (brk == 1 and body < 0) or (brk == -1 and body > 0):
                jj = max(j - 1, 0)
                lvl = min(M.o[j], M.o[jj]) if brk == 1 else max(M.o[j], M.o[jj])
                break
        if lvl is None:
            continue
        # trigger: first close back through the CISD level after the break
        cf = (M.c[kb:k1] <= lvl) if brk == 1 else (M.c[kb:k1] >= lvl)
        if not cf.any():
            continue
        ke = kb + int(np.argmax(cf))
        side = -brk
        entry = float(M.c[ke])
        # stop: the extreme of the whole move from the OR start to the trigger
        stop = float(M.h[j0:ke + 1].max()) if brk == 1 else float(M.l[j0:ke + 1].min())
        R = side * (entry - stop)
        if R <= 0.0003 * entry:
            continue
        tgt = None
        if target == "2R":
            tgt = entry + side * 2 * R
        elif target == "or_opp":
            tgt = orl if side == -1 else orh
            if side * (tgt - entry) < 0.25 * R:
                continue
        t_fill = M.ix[ke] + pd.Timedelta(minutes=5)
        px, why, t_out = hit(M, M.ix.searchsorted(t_fill), k1, side, stop, tgt)
        if px is None:
            px = M.at(t_end)
            if px is None:
                continue
            why, t_out = "time", t_end
        rows.append(dict(day=day, entry=entry, side=side, why=why,
                         pnl=side * (px - entry) - M.cost))
    return rows


# ============================================================ Supertrend + RSI
def supertrend(M, length, mult):
    tr = np.maximum(M.h - M.l, np.maximum(abs(M.h - np.roll(M.c, 1)), abs(M.l - np.roll(M.c, 1))))
    tr[0] = M.h[0] - M.l[0]
    atr = pd.Series(tr).ewm(alpha=1 / length, adjust=False).mean().values
    hl2 = (M.h + M.l) / 2
    ub, lb = hl2 + mult * atr, hl2 - mult * atr
    n = len(M.c)
    fu, fl = ub.copy(), lb.copy()
    dirn = np.ones(n, dtype=int)                        # 1 = down, -1 = up (Pine)
    line = ub.copy()
    for i in range(1, n):
        fl[i] = max(lb[i], fl[i - 1]) if M.c[i - 1] > fl[i - 1] else lb[i]
        fu[i] = min(ub[i], fu[i - 1]) if M.c[i - 1] < fu[i - 1] else ub[i]
        if dirn[i - 1] == -1:                            # uptrend, line = lower
            dirn[i] = 1 if M.c[i] < fl[i] else -1
        else:
            dirn[i] = -1 if M.c[i] > fu[i] else 1
        line[i] = fl[i] if dirn[i] == -1 else fu[i]
    return line, dirn


def rsi(M, length=14):
    d = np.diff(M.c, prepend=M.c[0])
    up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / length, adjust=False).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / length, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values


def strsi(M, mult, st_len, r_hi, r_lo, as_written):
    line, dirn = supertrend(M, st_len, mult)
    r = rsi(M)
    rp = np.roll(r, 1)
    rp[0] = np.nan
    insess = (M.mins >= 8 * 60) & (M.mins < 17 * 60)
    # Pine semantics: direction -1 = uptrend. "As written" longs need stDir==1.
    up_ok = (dirn == 1) if as_written else (dirn == -1)
    dn_ok = (dirn == -1) if as_written else (dirn == 1)
    lsig = insess & up_ok & (rp <= r_hi) & (r > r_hi)
    ssig = insess & dn_ok & (rp >= r_lo) & (r < r_lo)
    rows = []
    pos, entry, e_day = 0, 0.0, None
    n = len(M.c)
    for i in range(1, n):
        if pos != 0:
            st_prev = line[i - 1]                       # levels set at prior close
            risk = abs(entry - st_prev)
            risk = max(risk, 0.0001 * entry)
            stop = entry - pos * risk
            tp = entry + pos * 2.0 * risk
            hit_s = (M.l[i] <= stop) if pos == 1 else (M.h[i] >= stop)
            hit_t = (M.h[i] >= tp) if pos == 1 else (M.l[i] <= tp)
            out = None
            if hit_s:
                out = stop
            elif hit_t:
                out = tp
            elif not insess[i]:                          # flatten at session end
                out = M.c[i]
            elif (pos == 1 and ssig[i]) or (pos == -1 and lsig[i]):
                out = M.c[i]                             # reversal at close
            if out is not None:
                rows.append(dict(day=e_day, entry=entry, side=pos,
                                 pnl=pos * (out - entry) - M.cost))
                pos = 0
        if pos == 0 and insess[i]:
            if lsig[i]:
                pos, entry, e_day = 1, float(M.c[i]), pd.Timestamp(M.et[i].date())
            elif ssig[i]:
                pos, entry, e_day = -1, float(M.c[i]), pd.Timestamp(M.et[i].date())
    return rows


# ============================================================ run everything
MK = load_mkts()
CORR = trades.corr_series(gold_engine.load_bars(), 20)

print("=== 1. CISD REVERSAL (Venom / Silver Bullet / TJR windows) ===")
gold_logs = {}
for M in MK:
    for w, spec in WINDOWS.items():
        for tgt in ("2R", "or_opp", "eod"):
            rows = cisd(M, w, tgt)
            d = cell(M, f"cisd_{w}", f"{spec[4]} / {tgt}", rows)
            if M.name == "XAU" and d is not None:
                gold_logs[(w, tgt)] = d

print("\n=== 2. SUPERTREND + RSI ===")
for M in MK:
    for lbl, params in (("ST(10,2.0) RSI 55/45", (2.0, 10, 55, 45)),
                        ("ST(10,3.0) RSI 55/45", (3.0, 10, 55, 45)),
                        ("ST(10,2.0) RSI 60/40", (2.0, 10, 60, 40))):
        for aw in (True, False):
            rows = strsi(M, *params, as_written=aw)
            tag = "as written (inverted)" if aw else "as intended"
            d = cell(M, "strsi", f"{lbl} {tag}", rows)
            if M.name == "XAU" and params == (2.0, 10, 55, 45) and d is not None:
                gold_logs[("strsi", tag)] = d

print("\n=== 3. GOLD: correlation-filter overlay on the fixed cells ===")
pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
ov = {}
for key in ((("venom", "2R")), (("silver", "2R")), (("strsi", "as intended"))):
    d = gold_logs.get(key)
    if d is None:
        continue
    d = d.copy()
    d["corr"] = d.day.map(CORR)
    d = d.dropna(subset=["corr"])
    lab = " / ".join(key)
    for f, m in (("corr<=0.5", d["corr"] <= 0.5), ("corr>0.5", d["corr"] > 0.5)):
        x = d[m]
        if len(x) > 25:
            print(f"   {lab:28s} {f:10s} n={len(x):>4} PF={pfx(x.pnl):.3f}")
            ov[f"{lab} {f}"] = {"n": len(x), "pf": pfx(x.pnl)}
OUT["gold_corr_overlay"] = ov

print("\n=== 4. HONEST OOS: rank all cells on in-sample t, read out-of-sample ===")
sc = pd.DataFrame([c for c in OUT["cells"] if np.isfinite(c.get("os_pf", np.nan)) and c["is_n"] > 40])
top10 = sc.sort_values("is_t", ascending=False).head(10)
for _, r in top10.iterrows():
    print(f"   {r['mkt']} {r['label']:46s} IS PF={r['is_pf']:.3f} t={r['is_t']:+.2f} "
          f"| OS n={r['os_n']:>4} PF={r['os_pf']:.3f}")
print(f"   honest top-10 median OS PF {top10.os_pf.median():.3f}; "
      f"population ({len(sc)}) median OS PF {sc.os_pf.median():.3f}")
OUT["isos"] = {"top10": top10.to_dict("records"),
               "honest_median_os_pf": float(top10.os_pf.median()),
               "population_median_os_pf": float(sc.os_pf.median()), "n_cells": int(len(sc))}

json.dump(OUT, open("results/tv_scripts.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} cells scored. written: results/tv_scripts.json")
