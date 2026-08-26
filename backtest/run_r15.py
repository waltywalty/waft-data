"""Round 15: the researched battery. Families per reference/round15_prereg.md.

F1 intraday momentum (last half-hour) on SPX/NDX/RTY, Gao r1 and Baltussen
   rest-of-day signals, vol-conditioned.
F2 turn-of-month, McConnell-Xu and Etula windows.
F3 TSMOM overlay on the deployed gold trades.
F4 session-split of the deployed trades' P&L (descriptive).
F5 opening gap fill on SPX/NDX.

All specs were fixed in the pre-registration before this file ran.
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
import mkts

pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def met(pnl_pct):
    x = np.asarray(pnl_pct, float)
    x = x[np.isfinite(x)]
    if len(x) < 15:
        return dict(n=len(x), pf=np.nan, win=np.nan, mean_bps=np.nan, t=np.nan)
    return dict(n=len(x), pf=pfv(pd.Series(x)), win=float((x > 0).mean()),
                mean_bps=float(x.mean() * 1e4),
                t=float(x.mean() / x.std() * np.sqrt(len(x))))

out = {"ledger": 0}
MK = mkts.load_mkts(("SPX", "NDX", "RTY"))

# ---- per-market RTH frame: prior close, 10:00, 15:30, 16:00, 09:30/09:35 opens
def rth_frame(M):
    rows = []
    for d in M.days:
        t0930 = M.nyt(pd.Timestamp(d), 9, 30)
        px = {k: M.at(M.nyt(pd.Timestamp(d), h, m))
              for k, (h, m) in dict(o0930=(9, 30), o0935=(9, 35), t1000=(10, 0),
                                    t1200=(12, 0), t1530=(15, 30), c1600=(16, 0)).items()}
        if any(v is None for v in px.values()):
            continue
        rows.append(dict(d=pd.Timestamp(d), **px))
    F = pd.DataFrame(rows).set_index("d")
    F["prev_c"] = F.c1600.shift(1)
    F["ret_d"] = F.c1600 / F.prev_c - 1
    F["rv10"] = F.ret_d.rolling(10).std().shift(1)          # causal trailing vol
    F["rv_hi"] = F.rv10 > F.rv10.rolling(500, min_periods=100).median().shift(1)
    return F.dropna(subset=["prev_c"])

FR = {M.name: rth_frame(M) for M in MK}
for M in MK:
    print(f"{M.name}: {len(FR[M.name])} RTH days {FR[M.name].index.min().date()}..{FR[M.name].index.max().date()}")

HALF = pd.Timestamp("2016-01-01")

def slices(F, pnl):
    x = pd.Series(pnl, index=F.index).dropna()
    return dict(all=met(x), h1=met(x[x.index < HALF]), h2=met(x[x.index >= HALF]),
                recent=met(x[x.index >= "2021-01-01"]))

# ---------------------------------------------------------------- F1
f1 = {}
for M in MK:
    F = FR[M.name].dropna(subset=["rv10"])
    cost = M.cost / F.c1600                       # round trip in index pts -> frac
    last30 = F.c1600 / F.t1530 - 1
    for sig_name, sig in (("gao_r1", F.t1000 / F.prev_c - 1),
                          ("rod", F.t1530 / F.prev_c - 1)):
        pnl = np.sign(sig) * last30 - cost
        f1[f"{M.name}_{sig_name}"] = slices(F, pnl)
        f1[f"{M.name}_{sig_name}_hivol"] = slices(F[F.rv_hi], pnl[F.rv_hi])
        f1[f"{M.name}_{sig_name}_lovol"] = slices(F[~F.rv_hi], pnl[~F.rv_hi])
        out["ledger"] += 3
out["f1"] = f1
print("\nF1 last-half-hour timing (mean bps/trade, t):")
for k, v in f1.items():
    a = v["all"]
    print(f"  {k:>18}: n={a['n']:>4} {a['mean_bps']:+6.2f}bps t {a['t']:+5.2f} "
          f"| h1 t {v['h1']['t']:+5.2f} h2 t {v['h2']['t']:+5.2f} recent t {v['recent']['t']:+5.2f}")

# ---------------------------------------------------------------- F2
f2 = {}
for M in MK:
    F = FR[M.name]
    ym = F.index.to_period("M")
    pos_mx = np.zeros(len(F), bool)
    pos_et = np.zeros(len(F), bool)
    idx = np.arange(len(F))
    for m in ym.unique():
        in_m = idx[ym == m]
        nxt = idx[ym == m + 1]
        if len(in_m) < 5 or len(nxt) < 4:
            continue
        # V1: hold from close of 2nd-to-last day of m through close of 3rd day of m+1
        pos_mx[in_m[-1]] = True                      # last day of m
        pos_mx[nxt[:3]] = True                       # first 3 days of m+1
        # V2: hold from close of T-3 through close of T+2
        pos_et[in_m[-2:]] = True
        pos_et[nxt[:2]] = True
    for nm, pos in (("mx", pos_mx), ("etula", pos_et)):
        pnl = np.where(pos, F.ret_d, np.nan)         # daily close-to-close while held
        f2[f"{M.name}_{nm}"] = slices(F, pnl)
        out["ledger"] += 1
out["f2"] = f2
print("\nF2 turn-of-month (per held day):")
for k, v in f2.items():
    a = v["all"]
    print(f"  {k:>12}: n={a['n']:>4} {a['mean_bps']:+6.2f}bps t {a['t']:+5.2f} "
          f"| h1 {v['h1']['t']:+5.2f} h2 {v['h2']['t']:+5.2f}")

# non-TOM benchmark days for context
for M in MK:
    F = FR[M.name]
    print(f"  {M.name} all-days mean {F.ret_d.mean()*1e4:+.2f}bps")

# ---------------------------------------------------------------- F3 + F4
import engine, trades as TR
from zoneinfo import ZoneInfo
gold = engine.load_bars()
dep = pd.read_pickle("results/trades_deployable.pkl")
gd = gold.close.tz_convert(ZoneInfo("Europe/Athens")).resample("1D").last()
gd = pd.Series(gd.values, index=pd.to_datetime([x.date() for x in gd.index])).dropna()

f3 = {}
dep["day_n"] = pd.to_datetime(dep.day).dt.normalize()
for lb in (63, 126, 189, 252):
    trend = np.sign(gd.pct_change(lb)).shift(1)
    tr = dep.day_n.map(trend.reindex(pd.date_range(gd.index.min(), gd.index.max())).ffill())
    agree = (dep.side == tr)
    for nm, mask in (("agree", agree), ("against", ~agree)):
        x = dep[mask & tr.notna()]
        p = (x.pnl_oz / x.entry * 100)
        m = met(p / 100)
        m["is_t"] = met((x[x.day_n < "2024-01-01"].pnl_oz / x[x.day_n < "2024-01-01"].entry))["t"] if len(x[x.day_n < "2024-01-01"]) >= 15 else np.nan
        m["os_t"] = met((x[x.day_n >= "2024-01-01"].pnl_oz / x[x.day_n >= "2024-01-01"].entry))["t"] if len(x[x.day_n >= "2024-01-01"]) >= 15 else np.nan
        f3[f"lb{lb}_{nm}"] = m
        out["ledger"] += 1
out["f3"] = f3
print("\nF3 TSMOM overlay on deployed trades:")
for k, v in f3.items():
    print(f"  {k:>14}: n={v['n']:>3} PF {v['pf']:.3f} t {v['t']:+5.2f} "
          f"(IS {v['is_t']:+5.2f} / OS {v['os_t']:+5.2f})" if v["n"] >= 15 else f"  {k}: n={v['n']}")

# F4 session split: entry->07:00 UTC, 07:00->14:00 UTC, 14:00->exit, on actual prices
close_at = lambda t: float(gold.close.iloc[min(gold.index.searchsorted(t), len(gold) - 1)])
splits = []
for _, r in dep.iterrows():
    cp1 = r.day_n.tz_localize("UTC") + pd.Timedelta(hours=7)
    cp2 = r.day_n.tz_localize("UTC") + pd.Timedelta(hours=14)
    marks = [r.entry]
    for cp in (cp1, cp2):
        if r.t_fill < cp < r.t_out:
            marks.append(close_at(cp))
        else:
            marks.append(marks[-1] if cp <= r.t_fill else None)
    # None means the trade ended before this checkpoint -> remaining segs at exit
    m1 = marks[1] if marks[1] is not None else r.exit
    m2 = marks[2] if marks[2] is not None else r.exit
    if marks[1] is None:
        m2 = r.exit
    seg1 = r.side * (m1 - r.entry)
    seg2 = r.side * (m2 - m1)
    seg3 = r.side * (r.exit - m2)
    splits.append((seg1, seg2, seg3))
S = pd.DataFrame(splits, columns=["to_ldn", "ldn_to_fix", "fix_to_exit"])
out["f4"] = dict(mean=S.mean().round(3).to_dict(), sum=S.sum().round(1).to_dict(),
                 share=(S.sum() / S.sum().sum()).round(3).to_dict())
print("\nF4 session split of deployed P&L ($/oz mean per trade):")
print(S.mean().round(3).to_string())
print("share of total:", (S.sum() / S.sum().sum()).round(3).to_dict())

# ---------------------------------------------------------------- F5
f5 = {}
for M in MK:
    if M.name == "RTY":
        continue
    F = FR[M.name]
    gap = F.o0930 / F.prev_c - 1
    filled, filled_noon = [], []
    econ = {b: [] for b in ("small", "mid", "large")}
    for d, r in F.iterrows():
        g = gap.loc[d]
        if not np.isfinite(g) or abs(g) < 0.0005:
            continue
        b = "small" if abs(g) <= 0.002 else ("mid" if abs(g) <= 0.005 else "large")
        j0, j1 = M.rng(M.nyt(d, 9, 30), M.nyt(d, 16, 0))
        jn = M.ix.searchsorted(M.nyt(d, 12, 0))
        tgt = r.prev_c
        seg_h, seg_l = M.h[j0:j1], M.l[j0:j1]
        hit = np.where((seg_l <= tgt) & (seg_h >= tgt))[0]
        filled.append((b, len(hit) > 0))
        filled_noon.append((b, len(hit) > 0 and (j0 + hit[0]) < jn))
        # economics: enter at 09:35 close toward fill, stop 2x gap, exit 12:00
        e = r.o0935
        sgn = -np.sign(g)                      # gap up -> short toward fill
        stop = e - sgn * 2 * abs(g) * e
        j2 = M.ix.searchsorted(M.nyt(d, 9, 35))
        res = None
        for j in range(j2, jn):
            if (sgn > 0 and M.l[j] <= stop) or (sgn < 0 and M.h[j] >= stop):
                res = stop; break
            if (sgn > 0 and M.h[j] >= tgt) or (sgn < 0 and M.l[j] <= tgt):
                res = tgt; break
        px = res if res is not None else (M.c[jn - 1] if jn - 1 < len(M.c) else e)
        econ[b].append((d, (sgn * (px - e) - M.cost) / e))
    fl = pd.DataFrame(filled, columns=["b", "f"])
    fn = pd.DataFrame(filled_noon, columns=["b", "f"])
    f5[M.name] = dict(fill_rate=fl.groupby("b").f.mean().round(3).to_dict(),
                      fill_by_noon=fn.groupby("b").f.mean().round(3).to_dict(),
                      n=fl.groupby("b").f.count().to_dict())
    for b, lst in econ.items():
        if not lst:
            continue
        e = pd.DataFrame(lst, columns=["d", "p"]).set_index("d")
        f5[M.name][f"econ_{b}"] = slices(e, e.p)
        out["ledger"] += 1
out["f5"] = f5
print("\nF5 gap fill:")
for mk, v in f5.items():
    print(f"  {mk}: fill {v['fill_rate']} | by noon {v['fill_by_noon']} | n {v['n']}")
    for b in ("small", "mid", "large"):
        if f"econ_{b}" in v:
            a = v[f"econ_{b}"]["all"]
            print(f"     fade {b}: n={a['n']} {a['mean_bps']:+6.2f}bps t {a['t']:+5.2f} "
                  f"(h1 {v[f'econ_{b}']['h1']['t']:+5.2f} h2 {v[f'econ_{b}']['h2']['t']:+5.2f})")

json.dump(out, open("results/r15.json", "w"), indent=1, default=str)
print(f"\nledger {out['ledger']} cells; written results/r15.json")
