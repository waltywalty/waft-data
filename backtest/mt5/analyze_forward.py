"""Score the forward test from the EA's v2 log - push-button, no judgement calls.

Usage:
    python3 analyze_forward.py AsiaOpenGold_forward_v2.csv [--deals deals.csv]

The v2 CSV (one line per trade, written by EA v1.20 after the 16:00-NY exit
time) is self-sufficient for the three candidates:

  1. rvol gate        - rvol_pass rows vs all rows (no-stop proxy P&L from
                        entry to close_px; pass --deals for the exact deployed
                        P&L per date: a CSV with columns date,pnl exported
                        from the MT5 account history)
  2. inside-day gate  - same comparison on inside_day == 1
  3. London add-leg   - dir * (close_px - ldn_px) on ldn_in_profit == 1 rows
     NY re-entry      - dir * (close_px - ny_px)  on ny_in_profit == 1 rows

Costs: $0.30/oz round trip on every leg. The promotion bar (per the playbook):
6-12 months of data AND the gated subset beating the base. Below ~60 logged
trades this script refuses to issue a verdict - it prints the tally and says
"keep logging".
"""
import sys
import numpy as np
import pandas as pd

COST = 0.30
MIN_TRADES = 60


def stats(p):
    p = pd.Series(p).dropna()
    if len(p) == 0:
        return None
    pf = float(p[p > 0].sum() / max(-p[p <= 0].sum(), 1e-9))
    t = float(p.mean() / p.std() * np.sqrt(len(p))) if p.std() else 0.0
    return dict(n=len(p), mean=float(p.mean()), pf=pf, t=t,
                win=float((p > 0).mean()))


def line(lbl, s):
    if s is None:
        print(f"  {lbl:34s} no rows")
        return
    print(f"  {lbl:34s} n={s['n']:>4} win={s['win']*100:4.1f}% "
          f"mean={s['mean']:+.2f} $/oz  PF={s['pf']:.3f}  t={s['t']:+.2f}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "AsiaOpenGold_forward_v2.csv"
    d = pd.read_csv(path)
    d.columns = [c.strip() for c in d.columns]
    d["date"] = pd.to_datetime(d["date"])
    for c in ("entry", "ldn_px", "ny_px", "close_px", "rvol"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    n = len(d)
    span = (d.date.max() - d.date.min()).days if n else 0
    print(f"log: {n} trades over {span} days ({d.date.min():%Y-%m-%d} .. {d.date.max():%Y-%m-%d})")

    # base P&L: exact if a deals export is supplied, else the no-stop proxy
    base_lbl = "no-stop proxy (entry -> 16:00)"
    d["base_pnl"] = d.dir * (d.close_px - d.entry) - COST
    if "--deals" in sys.argv:
        deals = pd.read_csv(sys.argv[sys.argv.index("--deals") + 1])
        deals["date"] = pd.to_datetime(deals["date"])
        d = d.merge(deals[["date", "pnl"]], on="date", how="left")
        if d.pnl.notna().mean() > 0.8:
            d["base_pnl"] = d.pnl
            base_lbl = "actual deployed P&L (deals export)"
        else:
            print("  WARNING: deals file matched <80% of dates; using the proxy")
    print(f"base P&L source: {base_lbl}\n")

    print("=== candidate 1/2: gates on the original trade ===")
    line("base (all trades)", stats(d.base_pnl))
    line("rvol_pass == 1", stats(d[d.rvol_pass == 1].base_pnl))
    line("inside_day == 1", stats(d[d.inside_day == 1].base_pnl))

    print("\n=== candidate 3: checkpoint legs (exact from the log) ===")
    ldn = d[(d.ldn_in_profit == 1) & d.ldn_px.gt(0) & d.close_px.gt(0)]
    line("London 08:00 add-leg", stats(ldn.dir * (ldn.close_px - ldn.ldn_px) - COST))
    ny = d[(d.ny_in_profit == 1) & d.ny_px.gt(0) & d.close_px.gt(0)]
    line("NY 09:30 re-entry leg", stats(ny.dir * (ny.close_px - ny.ny_px) - COST))

    print("\n=== verdict ===")
    if n < MIN_TRADES:
        print(f"  {n} trades logged; the bar is {MIN_TRADES}+ (about 4-6 months).")
        print("  Keep logging - no verdict yet, and no peeking-based decisions.")
        return
    base = stats(d.base_pnl)
    # gates are judged AGAINST the base (same trade, subset of days); the
    # add-leg is a different, shorter trade - its bar is standalone quality
    for lbl, sub in (("rvol gate", stats(d[d.rvol_pass == 1].base_pnl)),
                     ("inside-day gate", stats(d[d.inside_day == 1].base_pnl))):
        if sub is None or sub["n"] < 25:
            print(f"  {lbl}: fewer than 25 gated trades - keep logging.")
            continue
        beat = sub["mean"] > base["mean"] and sub["pf"] > 1.0
        print(f"  {lbl}: {'BEATS the base so far' if beat else 'does NOT beat the base'} "
              f"(gated mean {sub['mean']:+.2f} vs base {base['mean']:+.2f}); "
              f"promotion needs this to hold at the 6-12-month mark, decided once, "
              f"not monitored daily.")
    sub = stats(ldn.dir * (ldn.close_px - ldn.ldn_px) - COST)
    if sub is None or sub["n"] < 25:
        print("  London add-leg: fewer than 25 legs - keep logging.")
    else:
        ok = sub["mean"] > 0 and sub["pf"] > 1.0
        print(f"  London add-leg (standalone bar): "
              f"{'PROFITABLE so far' if ok else 'NOT profitable'} "
              f"(mean {sub['mean']:+.2f}, PF {sub['pf']:.3f} vs backtest 1.59); "
              f"promotion needs PF > 1 with the sign holding at the "
              f"6-12-month mark, decided once.")


if __name__ == "__main__":
    main()
