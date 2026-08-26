"""Round 15b: the Hang Seng battery, per reference/round15_hsi_prereg.md.

Data: HK50 15m (Yuan archive, Feb 2022 - Apr 2024) spliced with HK33 15m
(Oanda collector, Apr 2024 - Aug 2026); partners JP225 (1h), China A50
(CHCUSD 1h), HSCEI (HSCHKD 1h), CSI300 futures (CFFEX_IF 1h).

Session facts verified below before any test: first bar of the day 01:15 UTC
(09:15 HKT derivatives open), cash open 01:30 UTC, lunch 04:00-05:00 UTC.
Halves split at the sample midpoint 2024-05-01. Cost 10 index points round
trip (sensitivity 5 / 15).
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

COST = 10.0
pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def met(pnl, entry, day=None):
    x = pd.Series(np.asarray(pnl, float))
    e = pd.Series(np.asarray(entry, float))
    if len(x) < 15:
        return dict(n=len(x), pf=np.nan, win=np.nan, exp=np.nan, t=np.nan)
    p = x / e * 100
    return dict(n=len(x), pf=pfv(x), win=float((x > 0).mean()), exp=float(x.mean()),
                t=float(p.mean() / p.std() * np.sqrt(len(p))))

# ---------------------------------------------------------------- load + splice
a = pd.read_csv("data/HK50_PT15M_yuan.csv")
a["ts"] = pd.to_datetime(a.time, utc=True)
a = a.set_index("ts")[["open", "high", "low", "close"]].sort_index()
b = pd.read_csv("data/HK33_M15.csv")
b["ts"] = pd.to_datetime(b.iloc[:, 0], utc=True)
b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()

# overlap cross-check (same instrument, different brokers)
ov = a.index.intersection(b.index)
if len(ov):
    diff = (a.loc[ov, "close"] - b.loc[ov, "close"]).abs()
    print(f"splice overlap: {len(ov)} bars, median |dClose| {diff.median():.1f} pts "
          f"({diff.median()/a.loc[ov,'close'].median()*1e4:.1f} bps)")
H = pd.concat([a[a.index < (b.index.min())], b]).sort_index()
H = H[~H.index.duplicated()]
print(f"spliced HSI 15m: {len(H)} bars {H.index.min()} -> {H.index.max()}")

# ---------------------------------------------------------------- verification
H["d"] = H.index.date
H["hm"] = H.index.hour * 100 + H.index.minute
first_bar = H.groupby("d").apply(lambda x: x.hm.iloc[0])
print("modal first bar of day (UTC hhmm):", first_bar.mode().iloc[0],
      f"({(first_bar == first_bar.mode().iloc[0]).mean()*100:.0f}% of days)")
rng = (H.high - H.low)
by_slot = rng.groupby(H.hm).median()
print("median 15m range by slot: 0115:", round(by_slot.get(115, np.nan), 1),
      " 0130 (cash open):", round(by_slot.get(130, np.nan), 1),
      " 0300:", round(by_slot.get(300, np.nan), 1),
      " lunch 0400:", round(by_slot.get(400, np.nan), 1))
assert first_bar.mode().iloc[0] == 115, "session structure not as expected"

days = sorted(H.d.unique())
daily_close = H.groupby("d").close.last()
daily_rng = H.groupby("d").high.max() - H.groupby("d").low.min()
atr14 = daily_rng.rolling(14).mean().shift(1)
MID = pd.Timestamp("2024-05-01").date()

out = {"ledger": 0, "splice_overlap_bps": float(diff.median()/a.loc[ov,'close'].median()*1e4) if len(ov) else None}

# ---------------------------------------------------------------- H-A
rows = []
for d, day in H.groupby("d"):
    pre = day[day.hm == 115]
    if not len(pre) or d not in atr14 or not np.isfinite(atr14[d]):
        continue
    sess = day[(day.hm >= 130) & (day.hm < 800)]
    if len(sess) < 15:
        continue
    o930 = sess.open.iloc[0]
    c1030 = sess[sess.hm < 230].close.iloc[-1] if len(sess[sess.hm < 230]) else np.nan
    c1200 = sess[sess.hm < 400].close.iloc[-1] if len(sess[sess.hm < 400]) else np.nan
    c1600 = sess.close.iloc[-1]
    rows.append(dict(d=d, push=pre.close.iloc[0] - pre.open.iloc[0],
                     pre_hi=pre.high.iloc[0], pre_lo=pre.low.iloc[0],
                     pre_rng=pre.high.iloc[0] - pre.low.iloc[0],
                     o930=o930, c1030=c1030, c1200=c1200, c1600=c1600,
                     atr=atr14[d]))
A = pd.DataFrame(rows).dropna(subset=["c1030", "c1600"])
A["push_n"] = A.push / A.atr
A["r1030"] = A.c1030 - A.o930
A["r1600"] = A.c1600 - A.o930
from scipy import stats as st
rho1, p1 = st.spearmanr(A.push, A.r1030)
rho2, p2 = st.spearmanr(A.push, A.r1600)
q = pd.qcut(A.push_n, 5, labels=False)
grad = A.groupby(q).r1030.mean().round(1).tolist()
out["ha_desc"] = dict(n=len(A), rho_1030=float(rho1), p_1030=float(p1),
                      rho_1600=float(rho2), p_1600=float(p2), grad_quintiles=grad)
print(f"\nH-A descriptive (n={len(A)} days):")
print(f"  spearman push vs 09:30->10:30: {rho1:+.3f} (p={p1:.3f});  vs 09:30->16:00: {rho2:+.3f} (p={p2:.3f})")
print(f"  mean 09:30->10:30 pts by push quintile (low->high): {grad}")

def fade(sub, stop_k, exit_col):
    pnl, ent = [], []
    for _, r in sub.iterrows():
        day = H[(H.d == r.d) & (H.hm >= 130) & (H.hm < 800)]
        if not len(day):
            continue
        sgn = -np.sign(r.push)
        e = day.open.iloc[0]
        stop = (r.pre_hi + stop_k * r.pre_rng) if sgn < 0 else (r.pre_lo - stop_k * r.pre_rng)
        lim = {"c1030": 230, "c1200": 400, "c1600": 800}[exit_col]
        res = None
        for _, bb in day[day.hm < lim].iterrows():
            if (sgn < 0 and bb.high >= stop) or (sgn > 0 and bb.low <= stop):
                res = stop
                break
        px = res if res is not None else r[exit_col]
        pnl.append(sgn * (px - e) - COST)
        ent.append(e)
    return pnl, ent

ha = {}
for trig in (0.3, 0.5):
    sub = A[np.abs(A.push_n) >= trig]
    for sk in (0.5, 1.0):
        for ex in ("c1030", "c1200", "c1600"):
            pnl, ent = fade(sub, sk, ex)
            dd = sub.d.values[:len(pnl)]
            f = pd.DataFrame(dict(pnl=pnl, ent=ent, d=sub.d.values[:len(pnl)]))
            m = met(f.pnl, f.ent)
            m["h1"] = met(f[f.d < MID].pnl, f[f.d < MID].ent)
            m["h2"] = met(f[f.d >= MID].pnl, f[f.d >= MID].ent)
            ha[f"t{trig}_s{sk}_{ex}"] = m
            out["ledger"] += 1
out["ha_econ"] = ha
print("\nH-A fade economics:")
for k, v in ha.items():
    if v["n"] >= 15:
        print(f"  {k:>18}: n={v['n']:>3} PF {v['pf']:.3f} t {v['t']:+5.2f} "
              f"(h1 {v['h1']['t']:+5.2f} / h2 {v['h2']['t']:+5.2f})")

# ---------------------------------------------------------------- H-B
hb = {}
for arm in ("break", "fade"):
    pnl, ent, dl = [], [], []
    for d, day in H.groupby("d"):
        sess = day[(day.hm >= 130) & (day.hm < 800)]
        rngb = sess[sess.hm < 230]
        if len(rngb) < 4 or len(sess) < 15:
            continue
        rH, rL = rngb.high.max(), rngb.low.min()
        width = rH - rL
        if width <= 0:
            continue
        after = sess[sess.hm >= 230].reset_index(drop=True)
        blocks = [after.iloc[i:i + 4] for i in range(0, len(after) - 3, 4)]
        e = sgn = None
        rest = None
        for bi, blk in enumerate(blocks):
            c = blk.close.iloc[-1]
            if c > rH or c < rL:
                brk = 1 if c > rH else -1
                sgn = brk if arm == "break" else -brk
                e = c
                rest = pd.concat(blocks[bi + 1:]) if bi + 1 < len(blocks) else None
                break
        if e is None or rest is None or not len(rest):
            continue
        stop = e - sgn * 2 * width
        res = None
        for _, bb in rest.iterrows():
            if (sgn > 0 and bb.low <= stop) or (sgn < 0 and bb.high >= stop):
                res = stop
                break
        px = res if res is not None else rest.close.iloc[-1]
        pnl.append(sgn * (px - e) - COST)
        ent.append(e)
        dl.append(d)
    f = pd.DataFrame(dict(pnl=pnl, ent=ent, d=dl))
    m = met(f.pnl, f.ent)
    m["h1"] = met(f[f.d < MID].pnl, f[f.d < MID].ent)
    m["h2"] = met(f[f.d >= MID].pnl, f[f.d >= MID].ent)
    hb[arm] = m
    out["ledger"] += 1
    print(f"\nH-B {arm}: n={m['n']} PF {m['pf']:.3f} t {m['t']:+.2f} "
          f"(h1 {m['h1']['t']:+.2f} / h2 {m['h2']['t']:+.2f})")
out["hb"] = hb

# ---------------------------------------------------------------- H-C
def daily_from(path, tcol=None):
    df = pd.read_csv(path)
    c0 = df.columns[0]
    df["ts"] = pd.to_datetime(df[c0] if tcol is None else df[tcol], utc=True)
    df = df.set_index("ts").sort_index()
    dc = df.close.groupby(df.index.date).last()
    dc.index = pd.to_datetime(dc.index)
    return np.log(pd.to_numeric(dc, errors="coerce")).diff().dropna()

h_ret = np.log(daily_close).diff().dropna()
h_ret.index = pd.to_datetime(h_ret.index)
partners = {"jp225": daily_from("data/JP225_H1.csv"),
            "a50": daily_from("data/CHCUSD_PT1H_yuan.csv", "time"),
            "hscei": daily_from("data/HSCHKD_PT1H_yuan.csv", "time"),
            "csi300": daily_from("data/CFFEX_IF_PT1H_yuan.csv", "time")}
best_arm = max(hb, key=lambda k: hb[k]["t"] if np.isfinite(hb[k]["t"]) else -9)
print(f"\nH-C gates on H-B better arm ({best_arm}):")
hc = {}
# rebuild the better arm's per-day pnl
arm = best_arm
pnl, ent, dl = [], [], []
for d, day in H.groupby("d"):
    sess = day[(day.hm >= 130) & (day.hm < 800)]
    rngb = sess[sess.hm < 230]
    if len(rngb) < 4 or len(sess) < 15:
        continue
    rH, rL = rngb.high.max(), rngb.low.min()
    width = rH - rL
    if width <= 0:
        continue
    after = sess[sess.hm >= 230].reset_index(drop=True)
    blocks = [after.iloc[i:i + 4] for i in range(0, len(after) - 3, 4)]
    e = sgn = rest = None
    for bi, blk in enumerate(blocks):
        c = blk.close.iloc[-1]
        if c > rH or c < rL:
            brk = 1 if c > rH else -1
            sgn = brk if arm == "break" else -brk
            e = c
            rest = pd.concat(blocks[bi + 1:]) if bi + 1 < len(blocks) else None
            break
    if e is None or rest is None or not len(rest):
        continue
    stop = e - sgn * 2 * width
    res = None
    for _, bb in rest.iterrows():
        if (sgn > 0 and bb.low <= stop) or (sgn < 0 and bb.high >= stop):
            res = stop
            break
    px = res if res is not None else rest.close.iloc[-1]
    pnl.append(sgn * (px - e) - COST)
    ent.append(e)
    dl.append(pd.Timestamp(d))
F = pd.DataFrame(dict(pnl=pnl, ent=ent, d=dl))
for k, pr in partners.items():
    j = pd.concat([h_ret.rename("h"), pr.rename("p")], axis=1, join="inner").dropna()
    C = (j.h.rolling(20).corr(j.p)
         .reindex(pd.date_range(j.index.min(), j.index.max())).ffill().shift(1))
    F[f"c_{k}"] = F.d.map(C)
    for thr in (0.3, 0.5, 0.7):
        for side in ("le", "ge"):
            sub = F[F[f"c_{k}"] <= thr] if side == "le" else F[F[f"c_{k}"] >= thr]
            m = met(sub.pnl, sub.ent)
            hc[f"{k}_{side}{thr}"] = m
            out["ledger"] += 1
    best = max((v for kk, v in hc.items() if kk.startswith(k) and v["n"] >= 40),
               key=lambda v: v["t"] if np.isfinite(v["t"]) else -9, default=None)
    if best:
        print(f"  {k}: best gated cell n={best['n']} PF {best['pf']:.3f} t {best['t']:+.2f} "
              f"(ungated t {out['hb'][best_arm]['t']:+.2f})")
out["hc"] = hc

json.dump(out, open("results/hsi.json", "w"), indent=1, default=str)
print(f"\nledger {out['ledger']} cells; written results/hsi.json")
