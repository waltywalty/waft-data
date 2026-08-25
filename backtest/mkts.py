"""Shared market scaffolding for the multi-market rounds: the Mkt wrapper
(fast lookups, ET clock, day list), loaders for XAU/SPX/NDX/RTY, the
stop/target path scanner, and the standard cell scorer with era splits.

Micro-futures context carried per market (for point-target rounds):
  XAU ~ MGC ($10/pt/contract), SPX ~ MES ($5/pt), NDX ~ MNQ ($2/pt),
  RTY ~ M2K ($5/pt). Prices here are spot/CFD proxies of those contracts.
"""
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
POINT_VALUE = {"XAU": 10.0, "SPX": 5.0, "NDX": 2.0, "RTY": 5.0}
MICRO = {"XAU": "MGC", "SPX": "MES", "NDX": "MNQ", "RTY": "M2K"}


class Mkt:
    def __init__(self, name, df, cost, os_start):
        self.name, self.cost = name, cost
        self.os_start = pd.Timestamp(os_start)
        self.ix = df.index
        self.o, self.h, self.l, self.c = (df[x].values for x in ("open", "high", "low", "close"))
        self.v = df["volume"].values.astype(float) if "volume" in df else np.zeros(len(df))
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


def load_mkts(names=("XAU", "SPX", "NDX", "RTY")):
    import engine as gold_engine, index_data
    out = []
    spec = {"XAU": (lambda: gold_engine.load_bars(), 0.30, "2024-01-01"),
            "SPX": (lambda: index_data.load("SPX"), 0.6, "2020-01-01"),
            "NDX": (lambda: index_data.load("NDX"), 2.0, "2021-01-01"),
            "RTY": (lambda: index_data.load("RTY"), 0.4, "2017-01-01")}
    for n in names:
        f, cost, oss = spec[n]
        out.append(Mkt(n, f(), cost, oss))
    return out


def hit(M, j0, j1, side, stop, target):
    """First stop/target touch in bars [j0, j1); conservative stop-first."""
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


def rth_features(M):
    """Per-day causal features from RTH sessions: prior-day H/L/close, ATR14,
    plus prior full-day (24h) H/L. Row for day D uses sessions ending <= D-1."""
    rth = (M.mins >= 9 * 60 + 30) & (M.mins < 16 * 60)
    day = pd.Series(M.et.date, index=M.ix)
    hh = pd.Series(M.h, index=M.ix)
    ll = pd.Series(M.l, index=M.ix)
    cc = pd.Series(M.c, index=M.ix)
    g = pd.DataFrame({"h": hh[rth], "l": ll[rth], "c": cc[rth]}).groupby(day[rth])
    d = pd.DataFrame({"rth_h": g.h.max(), "rth_l": g.l.min(), "rth_c": g.c.last(),
                      "n": g.size()})
    d = d[d.n >= 40]
    d.index = pd.to_datetime(d.index)
    tr = pd.concat([d.rth_h - d.rth_l, (d.rth_h - d.rth_c.shift(1)).abs(),
                    (d.rth_l - d.rth_c.shift(1)).abs()], axis=1).max(axis=1)
    d["atr14"] = tr.rolling(14).mean()
    out = pd.DataFrame({"p_h": d.rth_h.shift(1), "p_l": d.rth_l.shift(1),
                        "p_c": d.rth_c.shift(1), "p_atr": d.atr14.shift(1)})
    return out


def score(M, rows):
    """Standard cell metrics dict, or None if too few trades."""
    if len(rows) < 30:
        return None
    d = pd.DataFrame(rows)
    d["day"] = pd.to_datetime(d.day)
    p = d.pnl
    pct = p / d.entry * 100
    pfx = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
    a, b = d[d.day < M.os_start], d[d.day >= M.os_start]
    pa = a.pnl / a.entry * 100
    return d, dict(
        n=len(d), win=float((p > 0).mean()), pf=pfx(p), exp=float(p.mean()),
        t=float(pct.mean() / pct.std() * np.sqrt(len(p))) if pct.std() else 0.0,
        pf_zero_cost=pfx(p + M.cost),
        is_pf=pfx(a.pnl) if len(a) > 20 else np.nan,
        is_t=float(pa.mean() / pa.std() * np.sqrt(len(a))) if len(a) > 20 and pa.std() else 0.0,
        is_n=len(a), os_pf=pfx(b.pnl) if len(b) > 20 else np.nan, os_n=len(b))


def show(M, label, rows, sink=None, family=""):
    r = score(M, rows)
    if r is None:
        print(f"   {M.name} {label:52s} too few trades ({len(rows)})")
        return None
    d, s = r
    print(f"   {M.name} {label:52s} n={s['n']:>5} win={s['win']*100:4.1f}% PF={s['pf']:.3f} "
          f"t={s['t']:+.2f} | PF0={s['pf_zero_cost']:.3f} | IS {s['is_pf']:.3f} OS {s['os_pf']:.3f}")
    if sink is not None:
        sink.append({"mkt": M.name, "family": family, "label": label, **s})
    return d
