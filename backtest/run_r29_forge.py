"""Round 29: pinescriptforge RTY audit. 12 strategies at their stated rules;
UNSTATED parameters take TradingView defaults (documented in the ledger).
Operating TF: 1H. Signals on closed bars, fill next bar open, one position
per strategy, both sides. Cost 0.4 pt RT (house model; zero-cost reported).
Windows: primary 2005-2020, secondary 2025-03..2026-04 (TopstepX).
"""
import pandas as pd, numpy as np, json, warnings, index_data, indicators as I
warnings.filterwarnings("ignore")
COST = 0.4
pfv = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def h1_frames():
    r = index_data.load("RTY")
    h = r.resample("1h").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last"),
                             volume=("volume", "sum")).dropna()
    t = pd.read_csv("data/RTY_1h_topstepx_axb0306.csv", parse_dates=["datetime"]).set_index("datetime").sort_index()
    t = t[["open", "high", "low", "close", "volume"]]
    return {"2005-2020": h, "2025-2026": t}

# ---------------------------------------------------------------- signal engines
# each returns a Series of desired position (+1/0/-1) evaluated on CLOSED bars
def sig_sar(df):
    # Parabolic SAR (0.02/0.2) + EMA100 filter; SAR flip is entry AND exit
    hi, lo = df.high.values, df.low.values
    n = len(df)
    sar = np.zeros(n); trend = np.zeros(n)
    af, ep = 0.02, hi[0]
    sar[0], trend[0] = lo[0], 1
    for i in range(1, n):
        prev = sar[i - 1]
        if trend[i - 1] > 0:
            s = prev + af * (ep - prev)
            s = min(s, lo[i - 1], lo[i - 2] if i > 1 else lo[i - 1])
            if lo[i] < s:
                trend[i] = -1; sar[i] = ep; ep = lo[i]; af = 0.02
            else:
                trend[i] = 1; sar[i] = s
                if hi[i] > ep: ep = hi[i]; af = min(af + 0.02, 0.2)
        else:
            s = prev + af * (ep - prev)
            s = max(s, hi[i - 1], hi[i - 2] if i > 1 else hi[i - 1])
            if hi[i] > s:
                trend[i] = 1; sar[i] = ep; ep = hi[i]; af = 0.02
            else:
                trend[i] = -1; sar[i] = s
                if lo[i] < ep: ep = lo[i]; af = min(af + 0.02, 0.2)
    ema100 = I.ema(df.close, 100)
    pos = pd.Series(0.0, index=df.index)
    pos[(trend > 0) & (df.close > ema100)] = 1
    pos[(trend < 0) & (df.close < ema100)] = -1
    return pos

def sig_dema(df):
    def dema(s, n):
        e1 = I.ema(s, n); return 2 * e1 - I.ema(e1, n)
    f, s = dema(df.close, 9), dema(df.close, 21)
    return pd.Series(np.where(f > s, 1.0, -1.0), index=df.index)

def sig_vortex(df, n=14):
    tr = I.true_range(df)
    vmp = (df.high - df.low.shift()).abs().rolling(n).sum()
    vmm = (df.low - df.high.shift()).abs().rolling(n).sum()
    trn = tr.rolling(n).sum()
    vip, vim = vmp / trn, vmm / trn
    adx, _, _ = I.adx(df, 14)
    pos = pd.Series(0.0, index=df.index)
    pos[(vip > vim) & (vip > 1.0) & (adx > 20)] = 1
    pos[(vim > vip) & (vim > 1.0) & (adx > 20)] = -1
    return pos

def sig_aroon(df, n=14):
    up = df.high.rolling(n + 1).apply(lambda x: 100 * x.argmax() / n, raw=True)
    dn = df.low.rolling(n + 1).apply(lambda x: 100 * x.argmin() / n, raw=True)
    pos = pd.Series(np.nan, index=df.index)
    pos[(up > 70) & (dn < 30)] = 1
    pos[(dn > 70) & (up < 30)] = -1
    pos[(up - 50).abs().lt(10) & (dn - 50).abs().lt(10)] = 0   # converged -> flat
    return pos.ffill().fillna(0)

def sig_zlema(df, n=21):
    lag = (n - 1) // 2
    z = I.ema(2 * df.close - df.close.shift(lag), n)
    pos = pd.Series(np.nan, index=df.index)
    pos[(z > z.shift()) & (df.close > z)] = 1
    pos[(z < z.shift()) & (df.close < z)] = -1
    pos[(df.close < z) & (pos.ffill() == 1)] = 0
    pos[(df.close > z) & (pos.ffill() == -1)] = 0
    return pos.ffill().fillna(0)

def sig_hull(df, n=16):
    def wma(s, m):
        w = np.arange(1, m + 1)
        return s.rolling(m).apply(lambda x: (x * w).sum() / w.sum(), raw=True)
    h = wma(2 * wma(df.close, n // 2) - wma(df.close, n), int(np.sqrt(n)))
    rising = h > h.shift()
    pos = pd.Series(np.nan, index=df.index)
    pos[rising & (df.close > h)] = 1
    pos[~rising & (df.close < h)] = -1
    return pos.ffill().fillna(0)

def sig_heikin(df):
    ha_c = (df.open + df.high + df.low + df.close) / 4
    ha_o = ha_c.copy()
    for i in range(1, len(df)):
        ha_o.iloc[i] = (ha_o.iloc[i - 1] + ha_c.iloc[i - 1]) / 2
    ha_h = pd.concat([df.high, ha_o, ha_c], axis=1).max(axis=1)
    ha_l = pd.concat([df.low, ha_o, ha_c], axis=1).min(axis=1)
    rng = (ha_h - ha_l).replace(0, np.nan)
    no_lower = (pd.concat([ha_o, ha_c], axis=1).min(axis=1) - ha_l) / rng < 0.1
    no_upper = (ha_h - pd.concat([ha_o, ha_c], axis=1).max(axis=1)) / rng < 0.1
    doji = ((ha_h - pd.concat([ha_o, ha_c], axis=1).max(axis=1)) / rng > 0.25) & \
           ((pd.concat([ha_o, ha_c], axis=1).min(axis=1) - ha_l) / rng > 0.25)
    ema50 = I.ema(df.close, 50)
    pos = pd.Series(np.nan, index=df.index)
    pos[(ha_c > ha_o) & no_lower & (df.close > ema50)] = 1
    pos[(ha_c < ha_o) & no_upper & (df.close < ema50)] = -1
    pos[doji] = 0
    return pos.ffill().fillna(0)

def sig_rainbow(df, third=3):
    layers = [I.sma(df.close, 2)]
    for _ in range(9):
        layers.append(I.sma(layers[-1], 2))
    L = pd.concat(layers, axis=1)
    bull = pd.Series(True, index=df.index)
    bear = pd.Series(True, index=df.index)
    for i in range(9):
        bull &= L.iloc[:, i] > L.iloc[:, i + 1]
        bear &= L.iloc[:, i] < L.iloc[:, i + 1]
    third_layer = L.iloc[:, third - 1]
    mid = L.iloc[:, 4]
    pos = pd.Series(np.nan, index=df.index)
    pos[bull & (df.low <= third_layer)] = 1
    pos[bear & (df.high >= third_layer)] = -1
    cross_exit = (L.iloc[:, 0] < mid) | (L.iloc[:, 2] < mid)
    cross_exit_s = (L.iloc[:, 0] > mid) | (L.iloc[:, 2] > mid)
    pos[cross_exit & (pos.ffill() == 1)] = 0
    pos[cross_exit_s & (pos.ffill() == -1)] = 0
    return pos.ffill().fillna(0)

def sig_marubozu(df):
    rng = (df.high - df.low).replace(0, np.nan)
    body_top = pd.concat([df.open, df.close], axis=1).max(axis=1)
    body_bot = pd.concat([df.open, df.close], axis=1).min(axis=1)
    maru = ((df.high - body_top) / rng < 0.1) & ((body_bot - df.low) / rng < 0.1) & \
           (df.volume > df.volume.rolling(20).mean())
    up = maru & (df.close > df.open)
    dn = maru & (df.close < df.open)
    mid = (df.high + df.low) / 2
    pos = pd.Series(0.0, index=df.index)
    tgt = pd.Series(np.nan, index=df.index)
    stp = pd.Series(np.nan, index=df.index)
    state = 0; m_mid = m_tgt = m_stp = np.nan; wait = 0
    o, h, l, cvals = df.open.values, df.high.values, df.low.values, df.close.values
    midv, rngv = mid.values, (df.high - df.low).values
    upv, dnv = up.values, dn.values
    out = np.zeros(len(df))
    for i in range(1, len(df)):
        if state == 0:
            if upv[i - 1] or dnv[i - 1]:
                sgn = 1 if upv[i - 1] else -1
                m_mid, m_r = midv[i - 1], rngv[i - 1]
                m_tgt = m_mid + sgn * m_r
                m_stp = (l[i - 1] if sgn > 0 else h[i - 1])
                # pullback to midpoint within next 5 bars
                for j in range(i, min(i + 5, len(df))):
                    pass
                state = sgn; wait = 5
        if state != 0 and wait > 0:
            if (state > 0 and l[i] <= m_mid) or (state < 0 and h[i] >= m_mid):
                out[i] = state; wait = -1     # in position
            else:
                wait -= 1
                if wait == 0: state = 0
        elif state != 0 and wait == -1:
            out[i] = state
            if (state > 0 and (h[i] >= m_tgt or l[i] <= m_stp)) or \
               (state < 0 and (l[i] <= m_tgt or h[i] >= m_stp)):
                state = 0; out[i] = 0
    return pd.Series(out, index=df.index)

def sig_htf_ltf(df):
    d = df.resample("1D").agg(close=("close", "last")).dropna()
    ema50d = I.ema(d.close, 50).shift(1)      # closed daily bars only
    bias = pd.Series(np.where(d.close.shift(1) > ema50d, 1.0, -1.0), index=d.index)
    bias_h = bias.reindex(df.index.normalize()).values
    sh, sl = I.swing_pivots(df, 2)
    pos = pd.Series(np.nan, index=df.index)
    near_sup = df.low <= sl * 1.001
    near_res = df.high >= sh * 0.999
    pos[(bias_h > 0) & near_sup] = 1
    pos[(bias_h < 0) & near_res] = -1
    # exit at opposite level
    pos[(pos.ffill() == 1) & near_res] = 0
    pos[(pos.ffill() == -1) & near_sup] = 0
    return pos.ffill().fillna(0)

def sig_elder(df):
    d = df.resample("1D").agg(open=("open", "first"), high=("high", "max"),
                              low=("low", "min"), close=("close", "last")).dropna()
    w = d.resample("W").agg(close=("close", "last")).dropna()
    macd = I.ema(w.close, 12) - I.ema(w.close, 26)
    hist = macd - I.ema(macd, 9)
    w_rising = (hist > hist.shift()).shift(1)        # closed weekly bars
    rsi_d = I.rsi(d.close, 14).shift(1)
    prev_hi = d.high.shift(1)
    prev_lo = d.low.shift(1)
    wr = w_rising.reindex(df.index, method="ffill")
    rd = rsi_d.reindex(df.index.normalize()).values
    ph = prev_hi.reindex(df.index.normalize()).values
    pl = prev_lo.reindex(df.index.normalize()).values
    pos = pd.Series(np.nan, index=df.index)
    pos[(wr == True) & (rd < 40) & (df.close.values > ph)] = 1
    pos[(wr == False) & (rd > 60) & (df.close.values < pl)] = -1
    pos[(pos.ffill() == 1) & ((wr == False) | (rd >= 80))] = 0
    pos[(pos.ffill() == -1) & ((wr == True) | (rd <= 20))] = 0
    return pos.ffill().fillna(0)

STRATS = {
    "SAR_reversal": (sig_sar, dict(pf=2.19, win=49.4, ret=725)),
    "DEMA_9_21": (sig_dema, dict(pf=2.55, win=58.6, ret=891)),
    "Vortex": (sig_vortex, dict(pf=2.19, win=51.3, ret=498)),
    "Aroon": (sig_aroon, dict(pf=1.99, win=50.6, ret=257)),
    "ZLEMA": (sig_zlema, dict(pf=2.26, win=55.3, ret=599)),
    "Hull": (sig_hull, dict(pf=1.57, win=44.2, ret=494)),
    "HeikinAshi": (sig_heikin, dict(pf=1.64, win=51.2, ret=196)),
    "Rainbow_1": (lambda df: sig_rainbow(df, 3), dict(pf=2.66, win=52.6, ret=1323)),
    "Rainbow_dup": (lambda df: sig_rainbow(df, 4), dict(pf=1.82, win=48.5, ret=599)),
    "Marubozu": (sig_marubozu, dict(pf=2.24, win=51.8, ret=648)),
    "HTF_LTF": (sig_htf_ltf, dict(pf=1.83, win=54.1, ret=607)),
    "Elder": (sig_elder, dict(pf=1.76, win=47.4, ret=435)),
}

def run(df, sigfn, cost):
    pos = sigfn(df).shift(1).fillna(0)         # fill next bar (one-bar delay)
    o = df.open.values
    p = pos.values
    trades = []
    entry = None
    for i in range(1, len(df)):
        if entry is None and p[i] != 0 and p[i - 1] == 0:
            entry = (p[i], o[i], df.index[i])
        elif entry is not None and p[i] != entry[0]:
            side, e, t0 = entry
            trades.append(dict(day=t0, pnl=side * (o[i] - e) - cost, entry=e))
            entry = (p[i], o[i], df.index[i]) if p[i] != 0 else None
    if entry is not None:
        side, e, t0 = entry
        trades.append(dict(day=t0, pnl=side * (o[-1] - e) - cost, entry=e))
    t = pd.DataFrame(trades)
    if len(t) < 20:
        return dict(n=len(t))
    pct = t.pnl / t.entry * 100
    mid = t.day.iloc[len(t) // 2]
    return dict(n=len(t), pf=pfv(t.pnl), win=float((t.pnl > 0).mean()),
                exp=float(t.pnl.mean()),
                t=float(pct.mean() / pct.std() * np.sqrt(len(pct))),
                ret_pct=float((pct / 100).sum() * 100),
                h1_pf=pfv(t[t.day <= mid].pnl), h2_pf=pfv(t[t.day > mid].pnl))

frames = h1_frames()
out = {}
for name, (fn, claim) in STRATS.items():
    for wname, df in frames.items():
        try:
            out[f"{name}|{wname}"] = run(df, fn, COST)
        except Exception as ex:
            out[f"{name}|{wname}"] = dict(error=str(ex)[:120])
    try:
        out[f"{name}|2005-2020|zerocost"] = run(frames["2005-2020"], fn, 0.0)
    except Exception as ex:
        out[f"{name}|2005-2020|zerocost"] = dict(error=str(ex)[:120])
    out[f"{name}|claim"] = claim

json.dump(out, open("results/r29_forge.json", "w"), indent=1, default=str)

print(f"{'strategy':>13} | {'claimed PF/win':>14} | {'2005-20 PF/win/t (n)':>24} | "
      f"{'zerocost PF':>11} | {'2025-26 PF (n)':>14}")
for name, (fn, claim) in STRATS.items():
    a = out.get(f"{name}|2005-2020", {})
    z = out.get(f"{name}|2005-2020|zerocost", {})
    b = out.get(f"{name}|2025-2026", {})
    fa = (f"{a['pf']:.2f}/{a['win']*100:.0f}%/{a['t']:+.1f} ({a['n']})"
          if "pf" in a else str(a)[:24])
    fz = f"{z['pf']:.2f}" if "pf" in z else "-"
    fb = f"{b['pf']:.2f} ({b['n']})" if "pf" in b else f"n={b.get('n', '?')}"
    print(f"{name:>13} | {claim['pf']:.2f}/{claim['win']:.0f}%{'':>4} | {fa:>24} | {fz:>11} | {fb:>14}")
