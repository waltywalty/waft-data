"""Systematic filter screen. A filter only counts if its edge has the SAME SIGN
in-sample and out-of-sample (base-rate differences between the two eras make raw
OS profit factors meaningless on their own)."""
import pandas as pd, numpy as np, engine, entries, filters as F

t30 = F.build(30, "london_close")
t15 = F.build(15, "london_close")
t5  = F.build(5,  "london_close")

def screen(t, name):
    t = t.copy()
    # quantile buckets so every bucket is populated
    t["rng_q"] = pd.qcut(t.range_size / t.atr14, 3, labels=["narrow", "mid", "wide"])
    t["dly_q"] = pd.qcut(t.groupby(level=0).cumcount() * 0 + t.index.map(lambda i: 0) + 0, 1, labels=["x"]) \
                 if False else None
    base_is = t[~t.is_os].pnl_pct.mean(); base_os = t[t.is_os].pnl_pct.mean()
    print(f"\n{'='*104}\n{name}  base expectancy  IS {base_is*100:+.2f} bp/trade   OS {base_os*100:+.2f} bp/trade")
    print(f"{'filter bucket':<34}{'IS n':>6}{'IS PF':>7}{'IS lift(bp)':>13}{'OS n':>7}{'OS PF':>7}{'OS lift(bp)':>13}  {'consistent?':>11}")
    tests = []
    def add(label, mask):
        tests.append((label, mask))
    add("range narrow (Q1 vs ATR)", t.rng_q == "narrow")
    add("range wide (Q3 vs ATR)", t.rng_q == "wide")
    add("with daily EMA20>EMA50 trend", t.trend_align == 1)
    add("against daily trend", t.trend_align == 0)
    add("with 5-day momentum", t.mom_align == 1)
    add("against 5-day momentum", t.mom_align == 0)
    add("with prior-day direction", t.prevdir_align == 1)
    add("with overnight gap", t.gap_align == 1)
    add("against overnight gap", t.gap_align == 0)
    add("breaks prior-day extreme", t.clears_prev == 1)
    add("low vol regime", t.atr_pct < .33)
    add("high vol regime", t.atr_pct >= .66)
    add("open in lower 1/3 of prev day", t.loc_in_prev < .33)
    add("open in upper 1/3 of prev day", t.loc_in_prev > .67)
    add("long only", t.side == 1)
    add("short only", t.side == -1)
    for i, d in enumerate("Mon Tue Wed Thu Fri".split()):
        add(f"weekday: {d}", t.dow == i)
    n_consistent = 0
    for label, mask in tests:
        a, b = t[mask & ~t.is_os], t[mask & t.is_os]
        if len(a) < 40 or len(b) < 25:
            continue
        pf = lambda x: (x.pnl_usd[x.pnl_usd > 0].sum() / max(-x.pnl_usd[x.pnl_usd <= 0].sum(), 1e-9))
        la, lb = (a.pnl_pct.mean() - base_is) * 100, (b.pnl_pct.mean() - base_os) * 100
        ok = "YES" if (la > 0 and lb > 0) else ("no" if (la * lb) < 0 else "-")
        n_consistent += ok == "YES"
        print(f"{label:<34}{len(a):>6}{pf(a):>7.2f}{la:>13.1f}{len(b):>7}{pf(b):>7.2f}{lb:>13.1f}  {ok:>11}")
    print(f"  -> {n_consistent} of {len([1 for l,m in tests if len(t[m&~t.is_os])>=40 and len(t[m&t.is_os])>=25])} filters improved on the base in BOTH halves"
          f" (pure chance would give ~25%)")

screen(t30, "30-MINUTE OPENING RANGE, exit London close")
screen(t15, "15-MINUTE OPENING RANGE, exit London close")
screen(t5,  "5-MINUTE OPENING RANGE, exit London close")
