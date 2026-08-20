"""A $2,000 account traded through the filtered rule, sized several ways.

Mechanics: XAUUSD spot CFD, 1 unit = 1 troy ounce, notional = ounces x price.
Margin = notional / leverage. Costs of $0.30 per ounce per round trip are already
inside pnl_oz. Holds never cross the 17:00 New York rollover, so no swap is charged.
Liquidation is modelled generously: the account only dies when the floating loss
reaches 100% of equity. A real broker closes out around the 50% margin level, so
every ruin shown here would in practice have arrived sooner.
"""
import pandas as pd, numpy as np, engine, trades, warnings, json
warnings.filterwarnings("ignore")

START = 2000.0
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))


def simulate(tr, mode, param, leverage=20.0, start=START):
    """mode 'allin'   -> deploy the whole account as margin every trade
       mode 'risk'    -> risk `param` of equity, stop distance = 1 x range width
       mode 'fixed'   -> a constant `param` ounces every trade"""
    eq = start
    curve, sizes, rets = [], [], []
    ruin_on = None
    for r in tr.itertuples():
        if eq <= 0:
            curve.append((r.day, 0.0)); continue
        if mode == "allin":
            oz = eq * leverage / r.entry
        elif mode == "risk":
            # size off the ACTUAL stop distance recorded for the trade, not the raw
            # range width - otherwise a wider stop silently multiplies the risk taken
            sd = getattr(r, "stop_dist", np.nan)
            if not np.isfinite(sd):
                raise ValueError("risk sizing needs a trade set generated with a stop")
            oz = (eq * param) / max(sd, 0.01)
            oz = min(oz, eq * leverage / r.entry)       # margin cap
        else:
            oz = param
        # intratrade liquidation: floating loss reaches the whole account
        if oz * r.mae_oz >= eq:
            eq = 0.0
            ruin_on = ruin_on or r.day
            curve.append((r.day, 0.0)); sizes.append(oz); rets.append(-1.0)
            continue
        p = oz * r.pnl_oz
        rets.append(p / eq)
        eq = max(eq + p, 0.0)
        if eq <= 0 and ruin_on is None:
            ruin_on = r.day
        curve.append((r.day, eq)); sizes.append(oz)
    c = pd.Series([e for _, e in curve], index=[d for d, _ in curve])
    peak = c.cummax()
    dd = ((peak - c) / peak.replace(0, np.nan)).fillna(1.0)
    yrs = (pd.Timestamp(c.index[-1]) - pd.Timestamp(c.index[0])).days / 365.25
    rets = pd.Series(rets)
    return {
        "final": float(c.iloc[-1]),
        "total_ret": float(c.iloc[-1] / start - 1),
        "cagr": float((c.iloc[-1] / start) ** (1 / yrs) - 1) if c.iloc[-1] > 0 and yrs else -1.0,
        "max_dd": float(dd.max()),
        "ruin": str(ruin_on) if ruin_on else None,
        "worst_trade": float(rets.min()),
        "best_trade": float(rets.max()),
        "avg_oz": float(np.mean(sizes)) if sizes else 0.0,
        "max_oz": float(np.max(sizes)) if sizes else 0.0,
        "avg_notional": float(np.mean([o * e for o, e in zip(sizes, tr.entry[:len(sizes)])])),
        "sharpe": float(rets.mean() / rets.std() * np.sqrt(len(rets) / yrs)) if rets.std() else np.nan,
        "n": len(tr), "curve": c,
    }


if __name__ == "__main__":
    gold = engine.load_bars()
    corr = trades.corr_series(gold, 20)
    notstop = pd.read_pickle("results/trades_60_ny.pkl")            # time exit only
    withstop = trades.generate(gold, 60, stop_r=1.0)                # 1 x range stop
    withstop["corr"] = pd.to_datetime(withstop.day).map(corr)
    withstop = withstop.dropna(subset=["corr"])
    withstop.to_pickle("results/trades_60_ny_stop1r.pkl")

    print("=== trade sets ===")
    for nm, d in (("time exit only", notstop), ("with 1x-range stop", withstop)):
        f = d[d["corr"] <= 0.5]
        print(f"  {nm:20s} filtered n={len(f)} PF={pf(f.pnl_oz):.3f} "
              f"win={100*(f.pnl_oz>0).mean():.1f}% exp=${f.pnl_oz.mean():+.2f} "
              f"| stopped {100*(f.reason=='stop').mean():.0f}%")

    fa = notstop[notstop["corr"] <= 0.5].reset_index(drop=True)
    fs = withstop[withstop["corr"] <= 0.5].reset_index(drop=True)

    runs = [
        ("All-in, no leverage (1:1)",      fa, "allin", None, 1.0),
        ("All-in, 5:1",                    fa, "allin", None, 5.0),
        ("All-in, 20:1 (retail gold cap)", fa, "allin", None, 20.0),
        ("All-in, 100:1 (offshore)",       fa, "allin", None, 100.0),
        ("Risk 1% per trade, 1R stop",     fs, "risk", 0.01, 20.0),
        ("Risk 2% per trade, 1R stop",     fs, "risk", 0.02, 20.0),
        ("Risk 5% per trade, 1R stop",     fs, "risk", 0.05, 20.0),
        ("Fixed 0.1 oz every trade",       fs, "fixed", 0.1, 20.0),
    ]
    out, curves = [], {}
    print(f"\n=== $2,000 ACCOUNT, filtered rule (corr20 <= 0.5), Aug 2020 - Aug 2025 ===")
    print(f"{'sizing':<32}{'final $':>12}{'CAGR':>9}{'max DD':>9}{'worst trade':>13}"
          f"{'avg notional':>14}{'ruin':>12}")
    for label, tr, mode, param, lev in runs:
        r = simulate(tr, mode, param, lev)
        curves[label] = r.pop("curve")
        out.append({"label": label, **r})
        print(f"{label:<32}{r['final']:>12,.0f}{r['cagr']*100:>8.1f}%{r['max_dd']*100:>8.1f}%"
              f"{r['worst_trade']*100:>12.1f}%{r['avg_notional']:>14,.0f}"
              f"{(r['ruin'] or '-'):>12}")

    print("\n=== the same sizing WITHOUT the correlation filter ===")
    ua = notstop.reset_index(drop=True)
    us = withstop.reset_index(drop=True)
    for label, tr, mode, param, lev in [("All-in, 20:1", ua, "allin", None, 20.0),
                                        ("Risk 2% per trade", us, "risk", 0.02, 20.0),
                                        ("Risk 1% per trade", us, "risk", 0.01, 20.0)]:
        r = simulate(tr, mode, param, lev)
        curves["UNFILTERED " + label] = r.pop("curve")
        out.append({"label": "unfiltered: " + label, **r})
        print(f"  {label:<30}final ${r['final']:>10,.0f}  CAGR {r['cagr']*100:>6.1f}%  "
              f"maxDD {r['max_dd']*100:>5.1f}%  ruin {(r['ruin'] or '-')}")

    print("\n=== benchmark: $2,000 of gold, bought and held ===")
    p0, p1 = float(gold.close.iloc[0]), float(gold.close.iloc[-1])
    yrs = (gold.index[-1] - gold.index[0]).days / 365.25
    dl = gold.close.resample("1D").last().dropna()
    bh_dd = ((dl.cummax() - dl) / dl.cummax()).max()
    print(f"  ${2000*p1/p0:,.0f} final, CAGR {((p1/p0)**(1/yrs)-1)*100:.1f}%, max drawdown {bh_dd*100:.1f}%")

    json.dump({"runs": out,
               "curves": {k: {"x": [str(d) for d in v.index[::max(len(v)//220, 1)]],
                              "y": [round(float(z), 2) for z in v.values[::max(len(v)//220, 1)]]}
                          for k, v in curves.items()},
               "benchmark": {"final": 2000*p1/p0, "cagr": (p1/p0)**(1/yrs)-1, "dd": float(bh_dd)},
               "start": START}, open("results/portfolio.json", "w"), indent=1)
