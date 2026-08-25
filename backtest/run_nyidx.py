"""The NY pre-open/open strategy families on the index CFDs (SPX, NDX, RTY).

Families (one engine per family, shared causal day-features):
  A. Zarattini first-bar direction: 09:30-09:35 ET bar, enter at its close in
     its direction, stop at bar extreme or 0.10 x ATR14, EoD or 10R target.
     This is the published QQQ strategy, replicated as closely as the data allows.
  B. Opening-range breakout: 15/30/60m range, first 5m close beyond, follow AND
     fade, stop at far side, exits EoD / +2h / prev-day-extreme target.
  C. Judas sweep: daily sma20 bias (lag-1), sweep of prior-RTH or overnight
     extremes against the bias, 5m reclaim confirm; open window (09:30-11:30)
     and pre-open window (08:00-09:30, CFDs trade continuously).
  D. Mean reversion at the open: 5m z-score (n=20), close-back trigger,
     entries 09:30-11:30 ET only, mean target, 1-sigma stop, 2h timeout.

Splits: in-sample = the Oanda era (<=2019; RTY <=2016), out-of-sample = after.
The honest-OOS panel ranks every cell on IS t only, then reads OS.
Costs: round trip 0.6 / 2.0 / 0.4 index points (SPX/NDX/RTY), sensitivity x0, x2.
"""
import pandas as pd, numpy as np, warnings, json, pickle
import index_data
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
IDX = {"SPX": 0.6, "NDX": 2.0, "RTY": 0.4}          # round-trip cost, index points
OS_START = {"SPX": pd.Timestamp("2020-01-01"), "NDX": pd.Timestamp("2021-01-01"),
            "RTY": pd.Timestamp("2017-01-01")}
OUT = {"cells": []}


class Frame:
    """5m bars + fast lookups + causal per-day features."""

    def __init__(self, key):
        b = index_data.load(key)
        self.key, self.cost = key, IDX[key]
        self.ix = b.index
        self.o, self.h, self.l, self.c = (b[x].values for x in ("open", "high", "low", "close"))
        self.feat = self._features(b)

    def at(self, t):
        i = self.ix.searchsorted(t)
        if i < len(self.ix) and self.ix[i] == t:
            return float(self.o[i])
        if i > 0 and (t - self.ix[i - 1]) <= pd.Timedelta(minutes=30):
            return float(self.c[i - 1])
        return None

    def rng(self, t0, t1):
        """[t0, t1): indices of bars opening in the window."""
        return self.ix.searchsorted(t0), self.ix.searchsorted(t1)

    def _features(self, b):
        et = b.index.tz_convert(NY)
        mins = et.hour * 60 + et.minute
        rth = (mins >= 9 * 60 + 30) & (mins < 16 * 60)
        day = pd.Series(et.date, index=b.index)
        g = b[rth].groupby(day[rth])
        d = pd.DataFrame({"rth_h": g.high.max(), "rth_l": g.low.min(),
                          "rth_c": g.close.last(), "n": g.size()})
        d = d[d.n >= 60]
        d.index = pd.to_datetime(d.index)
        tr = pd.concat([d.rth_h - d.rth_l, (d.rth_h - d.rth_c.shift(1)).abs(),
                        (d.rth_l - d.rth_c.shift(1)).abs()], axis=1).max(axis=1)
        d["atr14"] = tr.rolling(14).mean()
        s = d.rth_c.rolling(20).mean()
        d["bias"] = np.where(d.rth_c > s, 1, np.where(d.rth_c < s, -1, 0))
        # everything below is FOR day D, from data known before D's open
        d["p_h"] = d.rth_h.shift(1)
        d["p_l"] = d.rth_l.shift(1)
        d["p_c"] = d.rth_c.shift(1)
        d["p_atr"] = d.atr14.shift(1)
        d["p_bias"] = pd.Series(d.bias).shift(1).fillna(0).astype(int)
        return d

    def day_times(self, day):
        f = lambda h, m=0: pd.Timestamp(day.year, day.month, day.day, h, m, tz=NY).tz_convert("UTC")
        return f(9, 30), f(16, 0), f(8, 0), f(4, 0)


def hit_scan(F, j0, j1, side, stop, target):
    """First stop/target touch in bars [j0, j1); conservative stop-first."""
    if j1 <= j0:
        return None, "time", None
    none_ = np.zeros(j1 - j0, bool)
    hs = none_ if stop is None else ((F.l[j0:j1] <= stop) if side == 1 else (F.h[j0:j1] >= stop))
    ht = none_ if target is None else ((F.h[j0:j1] >= target) if side == 1 else (F.l[j0:j1] <= target))
    any_ = hs | ht
    if not any_.any():
        return None, "time", None
    k = int(np.argmax(any_))
    if hs[k]:
        return stop, "stop", F.ix[j0 + k]
    return target, "target", F.ix[j0 + k]


def close_trade(F, day, side, entry, t_fill, stop, target, t_exit, cost):
    j0, j1 = F.rng(t_fill, t_exit)
    px, why, t_out = hit_scan(F, j0, j1, side, stop, target)
    if px is None:
        px = F.at(t_exit)
        if px is None:
            return None
        why, t_out = "time", t_exit
    return dict(day=day, side=side, entry=entry, exit=float(px), why=why,
                t_fill=t_fill, t_out=t_out, pnl=side * (px - entry) - cost)


def stats(rows):
    if len(rows) < 30:
        return None
    d = pd.DataFrame(rows)
    p = d.pnl
    pct = p / d.entry * 100
    return dict(n=len(d), win=float((p > 0).mean()),
                pf=float(p[p > 0].sum() / max(-p[p <= 0].sum(), 1e-9)),
                exp=float(p.mean()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0)


def cell(F, family, label, rows):
    s = stats(rows)
    if not s:
        print(f"   {F.key} {label:44s} too few trades ({len(rows)})")
        return
    d = pd.DataFrame(rows)
    d["day"] = pd.to_datetime(d.day)
    a, b = d[d.day < OS_START[F.key]], d[d.day >= OS_START[F.key]]
    pfx = lambda s_: float(s_[s_ > 0].sum() / max(-s_[s_ <= 0].sum(), 1e-9))
    p0 = d.pnl + F.cost                                 # zero-cost re-price
    is_pf = pfx(a.pnl) if len(a) > 20 else np.nan
    os_pf = pfx(b.pnl) if len(b) > 20 else np.nan
    pct_a = a.pnl / a.entry * 100
    is_t = float(pct_a.mean() / pct_a.std() * np.sqrt(len(a))) if len(a) > 20 and pct_a.std() else 0.0
    print(f"   {F.key} {label:44s} n={s['n']:>5} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
          f"t={s['t']:+.2f} | PF0={pfx(p0):.3f} | IS {is_pf:.3f} OS {os_pf:.3f}")
    OUT["cells"].append({"idx": F.key, "family": family, "label": label, **s,
                         "pf_zero_cost": pfx(p0), "is_pf": float(is_pf),
                         "is_t": is_t, "is_n": len(a),
                         "os_pf": float(os_pf), "os_n": len(b)})


def days_of(F):
    return [d for d in F.feat.index if np.isfinite(F.feat.at[d, "p_atr"])]


# ---------------------------------------------------------------- families
def zarattini(F):
    for stop_kind in ("bar", "atr10"):
        for tgt in (None, 10.0):
            rows = []
            for d in days_of(F):
                t_open, t_eod, _, _ = F.day_times(d)
                i = F.ix.searchsorted(t_open)
                if i >= len(F.ix) or F.ix[i] != t_open:
                    continue
                o, c = F.o[i], F.c[i]
                hi, lo = F.h[i], F.l[i]
                if c == o:
                    continue
                side = 1 if c > o else -1
                entry, t_fill = float(c), t_open + pd.Timedelta(minutes=5)
                if stop_kind == "bar":
                    stop = float(lo if side == 1 else hi)
                else:
                    stop = entry - side * 0.10 * float(F.feat.at[d, "p_atr"])
                R = side * (entry - stop)
                if R <= 0:
                    continue
                target = entry + side * tgt * R if tgt else None
                tr = close_trade(F, d, side, entry, t_fill, stop, target, t_eod, F.cost)
                if tr:
                    rows.append(tr)
            lbl = f"first-bar, stop {stop_kind}, {'10R target' if tgt else 'EoD'}"
            cell(F, "zarattini", lbl, rows)


def orb(F):
    for R in (15, 30, 60):
        for fade in (False, True):
            for exit_spec in ("eod", "+2h", "prev_day"):
                rows = []
                for d in days_of(F):
                    t_open, t_eod, _, _ = F.day_times(d)
                    t_rend = t_open + pd.Timedelta(minutes=R)
                    j0, j1 = F.rng(t_open, t_rend)
                    if j1 - j0 < R // 5:
                        continue
                    rh, rl = float(F.h[j0:j1].max()), float(F.l[j0:j1].min())
                    if rh <= rl:
                        continue
                    # first 5m close beyond, within 120 minutes of the range end
                    k0, k1 = F.rng(t_rend, t_rend + pd.Timedelta(minutes=120))
                    brk_mask = (F.c[k0:k1] > rh) | (F.c[k0:k1] < rl)
                    if not brk_mask.any():
                        continue
                    k = k0 + int(np.argmax(brk_mask))
                    brk = 1 if F.c[k] > rh else -1
                    entry = float(F.c[k])
                    t_fill = F.ix[k] + pd.Timedelta(minutes=5)
                    side = -brk if fade else brk
                    stop = (rl if side == 1 else rh) if not fade else entry + brk * (rh - rl)
                    target, t_exit = None, t_eod
                    if exit_spec == "+2h":
                        t_exit = min(t_eod, t_fill + pd.Timedelta(hours=2))
                    elif exit_spec == "prev_day":
                        lv = F.feat.at[d, "p_h"] if side == 1 else F.feat.at[d, "p_l"]
                        if not np.isfinite(lv) or side * (lv - entry) < 0.25 * (rh - rl):
                            continue
                        target = float(lv)
                    tr = close_trade(F, d, side, entry, t_fill, stop, target, t_exit, F.cost)
                    if tr:
                        rows.append(tr)
                lbl = f"ORB {R}m {'fade' if fade else 'follow'} / {exit_spec}"
                cell(F, "orb_fade" if fade else "orb", lbl, rows)


def judas(F):
    for window in ("open", "preopen"):
        for tgt in ("2R", "eod"):
            rows = []
            for d in days_of(F):
                t_open, t_eod, t_pre, _ = F.day_times(d)
                b = int(F.feat.at[d, "p_bias"])
                if b == 0:
                    continue
                w0, w1 = (t_open, t_open + pd.Timedelta(hours=2)) if window == "open" \
                    else (t_pre, t_open)
                lvs = [F.feat.at[d, "p_l" if b == 1 else "p_h"]]
                # overnight extreme up to the window start (causal)
                j0, j1 = F.rng(w0 - pd.Timedelta(hours=16), w0)
                if j1 > j0:
                    lvs.append(float(F.l[j0:j1].min() if b == 1 else F.h[j0:j1].max()))
                lvs = [x for x in lvs if np.isfinite(x)]
                if not lvs:
                    continue
                lv = max(lvs) if b == 1 else min(lvs)      # nearest pool first
                k0, k1 = F.rng(w0, w1)
                if k1 <= k0:
                    continue
                sw = (F.l[k0:k1] <= lv) if b == 1 else (F.h[k0:k1] >= lv)
                if not sw.any():
                    continue
                ks = k0 + int(np.argmax(sw))
                # reclaim: first close back on the bias side within 60 min
                r1 = min(k1, ks + 12)
                rc = (F.c[ks:r1] > lv) if b == 1 else (F.c[ks:r1] < lv)
                if not rc.any():
                    continue
                kr = ks + int(np.argmax(rc))
                entry = float(F.c[kr])
                t_fill = F.ix[kr] + pd.Timedelta(minutes=5)
                ext = float(F.l[ks:kr + 1].min() if b == 1 else F.h[ks:kr + 1].max())
                stop = ext
                Rd = b * (entry - stop)
                if Rd < 0.0005 * entry:
                    continue
                target = entry + b * 2 * Rd if tgt == "2R" else None
                tr = close_trade(F, d, b, entry, t_fill, stop, target, t_eod, F.cost)
                if tr:
                    rows.append(tr)
            cell(F, "judas", f"judas {window} / {tgt}", rows)


def meanrev(F):
    for k in (2.0, 2.6):
        rows = []
        c5 = pd.Series(F.c, index=F.ix)
        m = c5.rolling(20).mean().values
        sd = c5.rolling(20).std().values
        z = (F.c - m) / np.where(sd > 0, sd, np.nan)
        et = F.ix.tz_convert(NY)
        mins = et.hour * 60 + et.minute
        okh = (mins >= 9 * 60 + 30) & (mins < 11 * 60 + 30)
        cand = np.zeros(len(z), dtype=int)
        zp = np.roll(z, 1)
        zp[0] = np.nan
        cand[np.where(okh & np.isfinite(z) & np.isfinite(zp) & (zp <= -k) & (z > -k) & (z < 0))] = 1
        cand[np.where(okh & np.isfinite(z) & np.isfinite(zp) & (zp >= k) & (z < k) & (z > 0))] = -1
        busy_until = F.ix[0]
        for i in np.nonzero(cand)[0]:
            t_sig = F.ix[i]
            t_fill = t_sig + pd.Timedelta(minutes=5)
            if t_fill < busy_until:
                continue
            side = int(cand[i])
            entry, mu, sig = float(F.c[i]), float(m[i]), float(sd[i])
            if side * (mu - entry) <= 0:
                continue
            d = pd.Timestamp(t_sig.tz_convert(NY).date())
            _, t_eod, _, _ = F.day_times(d)
            t_exit = min(t_eod, t_fill + pd.Timedelta(hours=2))
            if t_exit <= t_fill:
                continue
            tr = close_trade(F, d, side, entry, t_fill, entry - side * sig, mu, t_exit, F.cost)
            if tr:
                busy_until = tr["t_out"] + pd.Timedelta(minutes=5)
                rows.append(tr)
        cell(F, "meanrev", f"open-hours z fade k={k:.1f}", rows)


for key in ("SPX", "NDX", "RTY"):
    F = Frame(key)
    print(f"\n================ {key} ({len(F.feat)} sessions, cost {F.cost} pts) ================")
    print(" --- A. Zarattini first-bar ---")
    zarattini(F)
    print(" --- B. Opening-range breakout, follow and fade ---")
    orb(F)
    print(" --- C. Judas sweep ---")
    judas(F)
    print(" --- D. Mean reversion at the open ---")
    meanrev(F)

print("\n=== HONEST OOS: rank all cells on in-sample t, read out-of-sample ===")
sc = pd.DataFrame([c for c in OUT["cells"] if np.isfinite(c["os_pf"]) and c["is_n"] > 40])
top10 = sc.sort_values("is_t", ascending=False).head(10)
for _, r in top10.iterrows():
    print(f"   {r['idx']} {r['label']:44s} IS n={r['is_n']:>5} PF={r['is_pf']:.3f} "
          f"t={r['is_t']:+.2f} | OS n={r['os_n']:>4} PF={r['os_pf']:.3f}")
print(f"   honest top-10 median OS PF {top10.os_pf.median():.3f}; "
      f"population ({len(sc)}) median OS PF {sc.os_pf.median():.3f}")
OUT["isos"] = {"top10": top10.to_dict("records"),
               "honest_median_os_pf": float(top10.os_pf.median()),
               "population_median_os_pf": float(sc.os_pf.median()), "n_cells": int(len(sc))}

json.dump(OUT, open("results/nyidx.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} cells scored. written: results/nyidx.json")
