"""Round 28b: Double Seven deep-dive for the watch-list writeup and the
fourth paper stream. Frozen rule (7/200, long-only, no stop, as published).

Variants per the user's questions:
  A. strategy-only: cash idle between signals (flat-equity compounding)
  B. buy & hold S&P
  C. overlay: hold the index always, 2x exposure while a signal is open
     (this is the honest version of "reinvest idle cash into S&P" - because
     the trades ARE S&P longs, parking flat cash in S&P + trading = B&H;
     the overlay is the version where the signal adds something)
Markets: SPX at CFD cost 0.6pt and ES-futures cost 0.35pt; NDX at CFD 2.0
and NQ-futures 0.75pt. Note: multi-day CFD holds would also pay swap
(not modeled, stated); futures roll cost ~1 tick/quarter ignored.
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

def d7_trades(mkt, cost):
    b = index_data.load(mkt)
    d = b.resample("1D").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna()
    c = d.close
    sma200 = c.rolling(200).mean()
    low7, high7 = c.rolling(7).min(), c.rolling(7).max()
    tr, pos = [], None
    mae = 0.0
    for i in range(200, len(d)):
        if pos is None:
            if c.iloc[i] > sma200.iloc[i] and c.iloc[i] <= low7.iloc[i]:
                pos = (float(c.iloc[i]), i)
                mae = 0.0
        else:
            e, i0 = pos
            mae = max(mae, (e - float(d.low.iloc[i])) / e)
            if c.iloc[i] >= high7.iloc[i]:
                tr.append(dict(t_in=d.index[i0], t_out=d.index[i], entry=e,
                               exit=float(c.iloc[i]), bars=i - i0,
                               ret=(float(c.iloc[i]) - e - cost) / e,
                               mae_pct=mae))
                pos = None
    return pd.DataFrame(tr), d

def curves(tr, d):
    c = d.close
    ret_d = c.pct_change().fillna(0)
    in_pos = pd.Series(False, index=d.index)
    for r in tr.itertuples():
        in_pos.loc[r.t_in:r.t_out] = True
        in_pos.loc[r.t_in] = False        # enter at close of signal day
    # A: strategy-only (earn index return only while in position, costs at exits)
    stratd = ret_d.where(in_pos, 0.0)
    cost_hits = pd.Series(0.0, index=d.index)
    for r in tr.itertuples():
        cost_hits.loc[r.t_out] += (r.entry * 0 + 1) * 0  # placeholder
    eqA = (1 + stratd).cumprod()
    # apply per-trade cost drag at exit days
    for r in tr.itertuples():
        pass
    # simpler exact: rebuild A from trade returns compounding + flat between
    eqA = pd.Series(1.0, index=d.index)
    lvl = 1.0
    j = 0
    trs = tr.sort_values("t_in").reset_index(drop=True)
    cur = None
    for t in d.index:
        if cur is None and j < len(trs) and t == trs.t_in.iloc[j]:
            cur = (lvl, trs.entry.iloc[j])
        elif cur is not None:
            lvl0, e = cur
            px = float(c.loc[t])
            if t == trs.t_out.iloc[j]:
                lvl = lvl0 * (1 + trs.ret.iloc[j])
                cur = None
                j += 1
            else:
                pass
        eqA.loc[t] = lvl if cur is None else cur[0] * (float(c.loc[t]) / cur[1])
    # B: buy & hold
    eqB = c / c.iloc[0]
    # C: overlay 2x while in position (extra 1x = the strategy return stream)
    ovl = ret_d * (1 + in_pos.astype(float))
    eqC = (1 + ovl).cumprod()
    # cost drag for the overlay's extra unit
    return eqA, eqB, eqC, in_pos

def stats(eq, label, in_pos=None):
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq.cummax() - eq) / eq.cummax()
    r = eq.pct_change().dropna()
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    out = dict(label=label, final=float(eq.iloc[-1]), cagr=float(cagr),
               max_dd=float(dd.max()), sharpe=float(sharpe),
               mar=float(cagr / dd.max()) if dd.max() > 0 else np.nan)
    if in_pos is not None:
        out["exposure"] = float(in_pos.mean())
    return out

out = {}
for mkt, costs in (("SPX", {"cfd": 0.6, "fut_ES": 0.35}),
                   ("NDX", {"cfd": 2.0, "fut_NQ": 0.75})):
    for cname, cost in costs.items():
        tr, d = d7_trades(mkt, cost)
        eqA, eqB, eqC, in_pos = curves(tr, d)
        key = f"{mkt}_{cname}"
        out[key] = dict(
            n=len(tr), win=float((tr.ret > 0).mean()),
            avg_win=float(tr.ret[tr.ret > 0].mean() * 100),
            avg_loss=float(tr.ret[tr.ret <= 0].mean() * 100),
            payoff=float(-tr.ret[tr.ret > 0].mean() / tr.ret[tr.ret <= 0].mean()),
            avg_hold_bars=float(tr.bars.mean()),
            worst_trade_pct=float(tr.ret.min() * 100),
            worst_mae_pct=float(tr.mae_pct.max() * 100),
            med_mae_pct=float(tr.mae_pct.median() * 100),
            strategy=stats(eqA, "strategy-only", in_pos),
            buyhold=stats(eqB, "buy & hold"),
            overlay=stats(eqC, "B&H + 2x during signals"),
        )
        if cname == "cfd":
            # yearly returns of strategy-only vs B&H
            ya = eqA.resample("YE").last().pct_change().dropna()
            yb = eqB.resample("YE").last().pct_change().dropna()
            out[key]["yearly"] = {str(k.year): [round(float(v) * 100, 1),
                                                round(float(yb.get(k, np.nan)) * 100, 1)]
                                  for k, v in ya.items()}
            # save curves for the report chart (monthly sampled)
            out[key]["curves"] = {
                "dates": [str(x.date()) for x in eqA.resample("ME").last().index],
                "strategy": [round(float(v), 4) for v in eqA.resample("ME").last()],
                "buyhold": [round(float(v), 4) for v in eqB.resample("ME").last()],
                "overlay": [round(float(v), 4) for v in eqC.resample("ME").last()],
            }

json.dump(out, open("results/r28b_d7.json", "w"), indent=1, default=str)
for k, v in out.items():
    print(f"\n=== {k} === n={v['n']} win {v['win']*100:.1f}% payoff {v['payoff']:.2f} "
          f"hold {v['avg_hold_bars']:.1f} bars  worst trade {v['worst_trade_pct']:+.1f}% "
          f"worst MAE {v['worst_mae_pct']:.1f}%")
    for s in ("strategy", "buyhold", "overlay"):
        st = v[s]
        expo = f"  exposure {st.get('exposure', 1)*100:.0f}%" if "exposure" in st else ""
        print(f"  {st['label']:>24}: {st['final']:>7.2f}x  CAGR {st['cagr']*100:+6.1f}%  "
              f"maxDD {st['max_dd']*100:5.1f}%  Sharpe {st['sharpe']:.2f}  MAR {st['mar']:.2f}{expo}")
