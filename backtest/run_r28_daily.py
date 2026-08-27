"""Round 28, daily-bar group: Double Seven, NR7 & ID/NR4, Hikkake (best
published form), Holy Grail, TTM Squeeze. Frozen published parameters,
pre-registered in the goal ledger. Indices 2005-2025 (dailies from the 5m
feeds), gold 2020-2025 (the long spliced series is close-only).

Conventions frozen in the registration: same-day trigger+stop resolves to
stop (conservative); costs are the round-trip figures used since round 9.
"""
import pandas as pd, numpy as np, json, warnings, engine, index_data, indicators as I
warnings.filterwarnings("ignore")
COST = {"XAU": 0.30, "SPX": 0.6, "NDX": 2.0, "RTY": 0.4}
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))
rng = np.random.default_rng(28)

def daily_frame(mkt):
    b = engine.load_bars() if mkt == "XAU" else index_data.load(mkt)
    d = b.resample("1D").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna()
    return d

def score(tr, mkt, split):
    if len(tr) < 25:
        return dict(n=len(tr))
    t = pd.DataFrame(tr)
    p = t.pnl / t.entry * 100
    d = dict(n=len(t), pf=pf(t.pnl), win=float((t.pnl > 0).mean()),
             exp=float(t.pnl.mean()),
             t=float(p.mean() / p.std() * np.sqrt(len(p))))
    for nm, m in (("h1", t.day < split), ("h2", t.day >= split)):
        x = t[m]
        d[nm] = dict(n=len(x), pf=pf(x.pnl) if len(x) > 10 else np.nan)
    return d

out = {}
frames = {m: daily_frame(m) for m in ("XAU", "SPX", "NDX", "RTY")}
splits = {"XAU": pd.Timestamp("2023-01-01", tz="UTC")}
for m in ("SPX", "NDX", "RTY"):
    splits[m] = pd.Timestamp("2015-01-01", tz="UTC")

# ---------------- 1. Double Seven (long-only, no stop, as published)
for mkt, d in frames.items():
    c = d.close
    sma200 = c.rolling(200).mean()
    low7 = c.rolling(7).min()
    high7 = c.rolling(7).max()
    tr, pos = [], None
    for i in range(200, len(d)):
        if pos is None:
            if c.iloc[i] > sma200.iloc[i] and c.iloc[i] <= low7.iloc[i]:
                pos = (float(c.iloc[i]), d.index[i])
        else:
            if c.iloc[i] >= high7.iloc[i]:
                e, t_in = pos
                tr.append(dict(day=d.index[i], entry=e, pnl=float(c.iloc[i]) - e - COST[mkt],
                               hold=(d.index[i] - t_in).days))
                pos = None
    out[f"D7_{mkt}"] = score(tr, mkt, splits[mkt])
    # drift null: same number/length of random long holds above the 200sma
    if len(tr) > 25:
        t = pd.DataFrame(tr)
        holds = [max(int(h), 1) for h in t.hold * 0.7 // 1]  # calendar->bar approx
        elig = np.where(c > sma200)[0]
        elig = elig[elig < len(d) - max(holds) - 1]
        sims = []
        for _ in range(2000):
            s = 0.0
            for h in holds:
                j = rng.choice(elig)
                jj = min(j + max(int(h * 5 / 7), 1), len(d) - 1)
                s += float(c.iloc[jj] - c.iloc[j]) - COST[mkt]
            sims.append(s)
        real = float(t.pnl.sum())
        out[f"D7_{mkt}"]["drift_null_p"] = float(np.mean(np.array(sims) >= real))

# ---------------- 2. NR7 and ID/NR4 breakout (stop entry, same-day close exit)
for pat in ("NR7", "IDNR4"):
    for mkt, d in frames.items():
        rngs = d.high - d.low
        if pat == "NR7":
            sig = rngs == rngs.rolling(7).min()
        else:
            sig = ((d.high < d.high.shift(1)) & (d.low > d.low.shift(1))
                   & (rngs == rngs.rolling(4).min()))
        tick = d.close.mean() * 1e-4
        tr = []
        for i in np.where(sig.fillna(False))[0]:
            if i + 1 >= len(d):
                continue
            hi, lo = float(d.high.iloc[i]), float(d.low.iloc[i])
            nx = d.iloc[i + 1]
            long_trig, short_trig = hi + tick, lo - tick
            hit_l, hit_s = nx.high >= long_trig, nx.low <= short_trig
            if not hit_l and not hit_s:
                continue
            # first side hit unknown from daily bars: open decides; else conservative
            if hit_l and (not hit_s or nx.open >= (hi + lo) / 2):
                side, entry, stop = 1, long_trig, short_trig
            else:
                side, entry, stop = -1, short_trig, long_trig
            stopped = (nx.low <= stop) if side > 0 else (nx.high >= stop)
            exit_px = stop if stopped else float(nx.close)
            tr.append(dict(day=d.index[i + 1], entry=entry,
                           pnl=side * (exit_px - entry) - COST[mkt]))
        out[f"{pat}_{mkt}"] = score(tr, mkt, splits[mkt])

# ---------------- 3. Hikkake, best published form (50-EMA filter, 10-bar exit)
for mkt, d in frames.items():
    ema50 = I.ema(d.close, 50)
    tr = []
    i = 2
    H, L, C = d.high.values, d.low.values, d.close.values
    while i < len(d) - 12:
        inside = H[i - 1] < H[i - 2] and L[i - 1] > L[i - 2]
        if inside:
            # bullish: bar i makes lower high AND lower low than inside bar
            if H[i] < H[i - 1] and L[i] < L[i - 1] and C[i - 1] < ema50.iloc[i - 1]:
                trig, stop = H[i - 1], L[i]
                for j in range(i + 1, min(i + 4, len(d) - 11)):
                    if H[j] >= trig:
                        stopped = any(L[k] <= stop for k in range(j, min(j + 10, len(d))))
                        exit_px = stop if stopped else C[min(j + 10, len(d) - 1)]
                        tr.append(dict(day=d.index[j], entry=trig,
                                       pnl=exit_px - trig - COST[mkt]))
                        break
            elif H[i] > H[i - 1] and L[i] > L[i - 1] and C[i - 1] > ema50.iloc[i - 1]:
                trig, stop = L[i - 1], H[i]
                for j in range(i + 1, min(i + 4, len(d) - 11)):
                    if L[j] <= trig:
                        stopped = any(H[k] >= stop for k in range(j, min(j + 10, len(d))))
                        exit_px = stop if stopped else C[min(j + 10, len(d) - 1)]
                        tr.append(dict(day=d.index[j], entry=trig,
                                       pnl=trig - exit_px - COST[mkt]))
                        break
        i += 1
    out[f"HIK_{mkt}"] = score(tr, mkt, splits[mkt])

# ---------------- 4. Holy Grail (ADX14>30 rising, 20EMA pullback)
for mkt, d in frames.items():
    a, _, _ = I.adx(d, 14)
    ema20 = I.ema(d.close, 20)
    sh, sl = I.swing_pivots(d, 2)
    tr = []
    H, L, C = d.high.values, d.low.values, d.close.values
    for i in range(30, len(d) - 11):
        if not (a.iloc[i] > 30 and a.iloc[i] > a.iloc[i - 1]):
            continue
        up = C[i] > ema20.iloc[i - 5]  # trend direction proxy: price vs ema a week ago
        touch = L[i] <= ema20.iloc[i] <= H[i]
        if not touch:
            continue
        if up:
            trig, stop, tgt = H[i], L[i], sh.iloc[i]
            if not np.isfinite(tgt) or tgt <= trig:
                continue
            if H[i + 1] >= trig:
                exit_px, done = None, False
                for j in range(i + 1, min(i + 11, len(d))):
                    if L[j] <= stop: exit_px = stop; done = True; break
                    if H[j] >= tgt: exit_px = tgt; done = True; break
                if not done: exit_px = C[min(i + 10, len(d) - 1)]
                tr.append(dict(day=d.index[i + 1], entry=trig, pnl=exit_px - trig - COST[mkt]))
        else:
            trig, stop, tgt = L[i], H[i], sl.iloc[i]
            if not np.isfinite(tgt) or tgt >= trig:
                continue
            if L[i + 1] <= trig:
                exit_px, done = None, False
                for j in range(i + 1, min(i + 11, len(d))):
                    if H[j] >= stop: exit_px = stop; done = True; break
                    if L[j] <= tgt: exit_px = tgt; done = True; break
                if not done: exit_px = C[min(i + 10, len(d) - 1)]
                tr.append(dict(day=d.index[i + 1], entry=trig, pnl=trig - exit_px - COST[mkt]))
    out[f"HG_{mkt}"] = score(tr, mkt, splits[mkt])

# ---------------- 5. TTM Squeeze (daily 4 markets + H1 XAU/SPX)
def ttm(df, mkt, split):
    m, bu, bl = I.bollinger(df.close, 20, 2.0)
    km, ku, kl = I.keltner(df, 20, 1.5)
    inb = (bu < ku) & (bl > kl)
    mid = ((df.high.rolling(20).max() + df.low.rolling(20).min()) / 2 + df.close.rolling(20).mean()) / 2
    dev = df.close - mid
    mom = dev.rolling(12).apply(lambda x: np.polyfit(np.arange(12), x, 1)[0], raw=True)
    tr = []
    C, H, L = df.close.values, df.high.values, df.low.values
    inb_v, mom_v = inb.values, mom.values
    i = 25
    while i < len(df) - 2:
        # squeeze of >=5 bars ending at i-1, fire at i
        if inb_v[i - 1] and not inb_v[i] and all(inb_v[i - k] for k in range(1, 6)):
            side = 1 if mom_v[i] > 0 else -1
            entry = float(C[i])
            win = slice(max(i - 6, 0), i)
            stop = float(df.low.iloc[win].min()) if side > 0 else float(df.high.iloc[win].max())
            exit_px = None
            for j in range(i + 1, len(df)):
                if (side > 0 and L[j] <= stop) or (side < 0 and H[j] >= stop):
                    exit_px = stop; break
                if j >= i + 2 and abs(mom_v[j]) < abs(mom_v[j - 1]) < abs(mom_v[j - 2]):
                    exit_px = float(C[j]); break
                if j > i + 40:
                    exit_px = float(C[j]); break
            if exit_px is not None:
                tr.append(dict(day=df.index[min(j, len(df) - 1)], entry=entry,
                               pnl=side * (exit_px - entry) - COST[mkt]))
            i = j
        i += 1
    return score(tr, mkt, split)

for mkt, d in frames.items():
    out[f"TTM_{mkt}_D"] = ttm(d, mkt, splits[mkt])
for mkt in ("XAU", "SPX"):
    b = engine.load_bars() if mkt == "XAU" else index_data.load(mkt)
    h = b.resample("1h").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna()
    out[f"TTM_{mkt}_H1"] = ttm(h, mkt, splits[mkt])

json.dump(out, open("results/r28_daily.json", "w"), indent=1, default=str)
print(f"{'cell':>12} {'n':>5} {'PF':>7} {'win%':>6} {'t':>7}  halves")
for k, v in out.items():
    if "pf" in v:
        extra = f"  drift-null p={v['drift_null_p']:.3f}" if "drift_null_p" in v else ""
        print(f"{k:>12} {v['n']:>5} {v['pf']:>7.3f} {v['win']*100:>5.1f} {v['t']:>+7.2f}  "
              f"{v['h1']['pf']:.2f}/{v['h2']['pf']:.2f}{extra}")
    else:
        print(f"{k:>12} {v['n']:>5}  (too few)")
