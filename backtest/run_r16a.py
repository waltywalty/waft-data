"""Round 16A: the meta-law transplant, per reference/goal_ledger.md.

If edges live where price discovery is slow (Asia gold works, London/NY dead),
then US indices during ASIAN hours should behave like gold at the Asia open.
Construction mirrors the deployed gold rule: 60m range from 01:30 UTC, first
60m block close beyond enters, stop 2x range, exit at the London open or the
NY open (their discovery restarts). SPX and NDX 5m, 2005-2025.

Gates: none / high realized-vol tercile (14d daily-range mean, lag-1).
VIX gate deferred until the data agent lands. Halves at 2015-01-01.
Costs: SPX 0.6, NDX 2.0 points (mkts.py convention).
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")
from zoneinfo import ZoneInfo

LDN, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")
pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def met(f):
    if len(f) < 15:
        return dict(n=len(f), pf=np.nan, win=np.nan, exp=np.nan, t=np.nan)
    p = f.pnl / f.entry * 100
    return dict(n=len(f), pf=pfv(f.pnl), win=float((f.pnl > 0).mean()),
                exp=float(f.pnl.mean()), t=float(p.mean() / p.std() * np.sqrt(len(p))))

out = {"ledger": 0}
MID = pd.Timestamp("2015-01-01", tz="UTC")

for name, cost in (("SPX", 0.6), ("NDX", 2.0)):
    g = index_data.load(name)
    g = g[~g.index.duplicated()]
    days = pd.Series(g.index.date, index=g.index)
    # realized-vol state: 14d mean daily range, lag-1
    drng = g.high.groupby(days.values).max() - g.low.groupby(days.values).min()
    drng.index = pd.to_datetime(drng.index)
    rv = (drng / drng.rolling(60).mean()).rolling(14).mean().shift(1)
    rv_terc = rv.rank(pct=True)

    trades = []
    for d, day in g.groupby(days.values):
        t0 = pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=1, minutes=30)
        t1 = t0 + pd.Timedelta(hours=1)
        rng = day[(day.index >= t0) & (day.index < t1)]
        if len(rng) < 8:
            continue
        rH, rL = rng.high.max(), rng.low.min()
        width = rH - rL
        if width <= 0:
            continue
        ldn_open = pd.Timestamp(d.year, d.month, d.day, 8, 0, tz=LDN).tz_convert("UTC")
        ny_open = pd.Timestamp(d.year, d.month, d.day, 9, 30, tz=NY).tz_convert("UTC")
        after = day[day.index >= t1]
        # 60m blocks: 12 x 5m bars
        entry = sgn = t_entry = None
        for b0 in pd.date_range(t1, ldn_open - pd.Timedelta(hours=1), freq="1h"):
            blk = after[(after.index >= b0) & (after.index < b0 + pd.Timedelta(hours=1))]
            if len(blk) < 8:
                continue
            c = blk.close.iloc[-1]
            if c > rH or c < rL:
                sgn = 1 if c > rH else -1
                entry = c
                t_entry = blk.index[-1]
                break
        if entry is None:
            continue
        stop = entry - sgn * 2 * width
        for exit_nm, t_exit in (("ldn", ldn_open), ("ny", ny_open)):
            path = day[(day.index > t_entry) & (day.index <= t_exit)]
            if len(path) < 3:
                continue
            res = None
            hit = path[(path.low <= stop)] if sgn > 0 else path[(path.high >= stop)]
            if len(hit):
                res = stop
            px = res if res is not None else path.close.iloc[-1]
            trades.append(dict(day=pd.Timestamp(d), exit=exit_nm, sgn=sgn, entry=entry,
                               pnl=sgn * (px - entry) - cost,
                               stopped=res is not None,
                               rv=rv_terc.get(pd.Timestamp(d), np.nan)))
    T = pd.DataFrame(trades)
    T["day"] = pd.to_datetime(T.day).dt.tz_localize("UTC")
    out[name] = {}
    for exit_nm in ("ldn", "ny"):
        sub = T[T.exit == exit_nm]
        for gate_nm, gsub in (("all", sub), ("rv_hi", sub[sub.rv >= 2 / 3]),
                              ("rv_lo", sub[sub.rv < 1 / 3])):
            m = met(gsub)
            m["h1"] = met(gsub[gsub.day < MID])
            m["h2"] = met(gsub[gsub.day >= MID])
            m["stopped"] = float(gsub.stopped.mean()) if len(gsub) else np.nan
            out[name][f"{exit_nm}_{gate_nm}"] = m
            out["ledger"] += 1
            if m["n"] >= 15:
                print(f"{name} {exit_nm:>3} {gate_nm:>6}: n={m['n']:>5} PF {m['pf']:.3f} "
                      f"t {m['t']:+6.2f} (h1 {m['h1']['t']:+5.2f} / h2 {m['h2']['t']:+5.2f}) "
                      f"stopped {m['stopped']*100:.0f}%")

json.dump(out, open("results/r16a.json", "w"), indent=1, default=str)
print(f"\nledger {out['ledger']} cells; written results/r16a.json")
