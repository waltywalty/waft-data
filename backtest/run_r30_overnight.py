"""Round 30: the overnight anomaly audit ("buy MU at close, sell at next open").

Pre-registered in reference/goal_ledger.md. Decompose buy-and-hold into
  overnight leg : buy at close, sell at next session's open  (the viral claim)
  intraday leg  : buy at open, sell at same session's close
  B&H           : close-to-close compounding (= overnight x intraday)

Instruments:
  MU   - Equibles daily 2020-01..2026-08 (columns date,open,close,adj; MU has
         no splits in the window; dividends omitted, conservative vs overnight).
  SPX/NDX - our own verified 5m CFD feeds (index_data.load, UTC). RTH cut:
         09:30 ET bar open / 15:55 ET bar close (16:00 cash close). 20-year
         long-sample check on the same decomposition. NDX has a 7.5-month feed
         hole in 2020; overnight returns spanning >5 calendar days are dropped.

Costs: the overnight strategy does one full round trip per session (MOC buy,
MOO sell - auction orders, so bps-level costs are the right model). Net grids
at {2, 5, 10} bps round-trip per day. B&H pays nothing.

Outputs: results/r30_overnight.json
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")


def legs_from_daily(open_, close):
    on = (open_ / close.shift(1) - 1).dropna()          # close[t-1] -> open[t]
    intra = (close / open_ - 1).reindex(on.index)       # open[t]  -> close[t]
    bh = (close / close.shift(1) - 1).reindex(on.index)
    return on, intra, bh


def stats(r, bps_rt=0.0):
    r = r - bps_rt / 1e4
    eq = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = ((eq.cummax() - eq) / eq.cummax()).max()
    t = r.mean() / r.std() * np.sqrt(len(r)) if r.std() > 0 else np.nan
    return dict(final=float(eq.iloc[-1]), cagr=float(cagr), max_dd=float(dd),
                sharpe=float(r.mean() / r.std() * np.sqrt(252)),
                mean_bps=float(r.mean() * 1e4), t=float(t),
                hit=float((r > 0).mean()), n=int(len(r)))


def halves(r):
    m = len(r) // 2
    a, b = r.iloc[:m], r.iloc[m:]
    def block(x):
        return dict(mean_bps=float(x.mean() * 1e4),
                    t=float(x.mean() / x.std() * np.sqrt(len(x))),
                    span=f"{x.index[0]:%Y-%m}..{x.index[-1]:%Y-%m}")
    return dict(first=block(a), second=block(b),
                same_sign=bool(np.sign(a.mean()) == np.sign(b.mean())))


COSTS = [0, 2, 5, 10]
out = {}

# ------------------------------------------------------------------ MU
mu = pd.read_csv("data/MU_daily_equibles.csv", parse_dates=["date"]).set_index("date")
on, intra, bh = legs_from_daily(mu.open, mu.close)
worst = on.idxmin()
out["MU"] = dict(
    span=f"{on.index[0]:%Y-%m-%d}..{on.index[-1]:%Y-%m-%d}",
    overnight={f"{c}bps": stats(on, c) for c in COSTS},
    intraday=stats(intra),
    buyhold=stats(bh),
    halves_overnight=halves(on),
    worst_gap=dict(date=str(worst.date()), ret=float(on.min()),
                   best=float(on.max()), best_date=str(on.idxmax().date())),
)

# yearly overnight-vs-intraday mean (era stability at annual grain)
ymu = pd.DataFrame({"on": on, "intra": intra}).groupby(on.index.year).mean() * 1e4
out["MU"]["yearly_mean_bps"] = {str(y): dict(on=float(v.on), intra=float(v.intra))
                                for y, v in ymu.iterrows()}

# ------------------------------------------------------------ SPX / NDX
for idx in ("SPX", "NDX"):
    b = index_data.load(idx)
    et = b.tz_convert("America/New_York")
    hm = et.index.hour * 100 + et.index.minute
    d = et.index.date
    opens = pd.Series(et.open[hm == 930].values,
                      index=pd.to_datetime(et.index.date[hm == 930]))
    closes = pd.Series(et.close[hm == 1555].values,
                       index=pd.to_datetime(et.index.date[hm == 1555]))
    opens, closes = opens[~opens.index.duplicated()], closes[~closes.index.duplicated()]
    days = opens.index.intersection(closes.index)
    o, c = opens[days], closes[days]
    on_i = (o / c.shift(1) - 1).dropna()
    gapd = pd.Series(days, index=days).diff().dt.days.reindex(on_i.index)
    on_i = on_i[gapd <= 5]                        # drop the NDX feed hole etc.
    intra_i = (c / o - 1).reindex(on_i.index)
    bh_i = (on_i + 1) * (intra_i + 1) - 1
    out[idx] = dict(
        span=f"{on_i.index[0]:%Y-%m-%d}..{on_i.index[-1]:%Y-%m-%d}",
        overnight={f"{c_}bps": stats(on_i, c_) for c_ in COSTS},
        intraday=stats(intra_i),
        buyhold=stats(bh_i),
        halves_overnight=halves(on_i),
    )

json.dump(out, open("results/r30_overnight.json", "w"), indent=1, default=float)

for k in ("MU", "SPX", "NDX"):
    v = out[k]
    print(f"\n=== {k}  {v['span']} ===")
    print(f"{'leg':>22} {'final':>9} {'CAGR':>8} {'maxDD':>7} {'Sharpe':>7} {'bps/d':>7} {'t':>6} {'hit':>6}")
    rows = [("buy & hold", v["buyhold"]), ("intraday (open->close)", v["intraday"])]
    rows += [(f"overnight net {c}bps", v["overnight"][f"{c}bps"]) for c in COSTS]
    for lbl, s in rows:
        print(f"{lbl:>22} {s['final']:>8.2f}x {s['cagr']*100:>+7.1f}% {s['max_dd']*100:>6.1f}% "
              f"{s['sharpe']:>7.2f} {s['mean_bps']:>+7.1f} {s['t']:>+6.2f} {s['hit']*100:>5.1f}%")
    h = v["halves_overnight"]
    print(f"  halves (gross): {h['first']['span']} {h['first']['mean_bps']:+.1f}bps t{h['first']['t']:+.2f} | "
          f"{h['second']['span']} {h['second']['mean_bps']:+.1f}bps t{h['second']['t']:+.2f} | "
          f"same sign: {h['same_sign']}")
    if k == "MU":
        w = v["worst_gap"]
        print(f"  worst single gap {w['ret']*100:+.1f}% on {w['date']}; best {w['best']*100:+.1f}% on {w['best_date']}")
        print("  yearly mean bps (overnight / intraday):")
        for y, m in v["yearly_mean_bps"].items():
            print(f"    {y}: {m['on']:+7.1f} / {m['intra']:+7.1f}")
