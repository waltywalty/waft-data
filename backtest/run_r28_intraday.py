"""Round 28, intraday group: Zarattini noise-area momentum, Momentum Pinball,
Market Profile 80% rule. Frozen published parameters per the registration.
Port conventions documented: XAU session = 01:30 UTC open, flat 16:00 NY;
XAU 'first hour' = 01:30-02:30 UTC; VWAP uses tick volume (all we have).
Also: Holy Grail re-scored on H1 XAU/SPX because daily setups were too rare
(n 1-18) - the book claims all timeframes; addition documented, counted.
"""
import pandas as pd, numpy as np, json, warnings, engine, index_data, indicators as I
from zoneinfo import ZoneInfo
warnings.filterwarnings("ignore")
NY = ZoneInfo("America/New_York")
COST = {"XAU": 0.30, "SPX": 0.6, "NDX": 2.0, "RTY": 0.4}
pf = lambda s: float(s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9))

def get_bars(mkt):
    return engine.load_bars() if mkt == "XAU" else index_data.load(mkt)

def sessions(mkt, b):
    """Yield (t_open, t_close, frame) per session."""
    if mkt == "XAU":
        for day, _ in b.groupby(b.index.date):
            d = pd.Timestamp(day)
            t0 = pd.Timestamp(d.year, d.month, d.day, 1, 30, tz="UTC")
            t1 = pd.Timestamp(d.year, d.month, d.day, 16, 0, tz=NY).tz_convert("UTC")
            s = b.loc[t0:t1]
            if len(s) > 30:
                yield t0, t1, s
    else:
        et = b.index.tz_convert(NY)
        mins = et.hour * 60 + et.minute
        rth = b[(mins >= 570) & (mins < 960)]
        for day, s in rth.groupby(rth.index.tz_convert(NY).date):
            if len(s) > 30:
                yield s.index[0], s.index[-1], s

def score(tr, split):
    if len(tr) < 25:
        return dict(n=len(tr))
    t = pd.DataFrame(tr)
    p = t.pnl / t.entry * 100
    d = dict(n=len(t), pf=pf(t.pnl), win=float((t.pnl > 0).mean()), exp=float(t.pnl.mean()),
             t=float(p.mean() / p.std() * np.sqrt(len(p))))
    for nm, m in (("h1", t.day < split), ("h2", t.day >= split)):
        x = t[m]
        d[nm] = dict(n=len(x), pf=pf(x.pnl) if len(x) > 10 else np.nan)
    return d

out = {}
SPLITS = {"XAU": pd.Timestamp("2023-01-01", tz="UTC"),
          "SPX": pd.Timestamp("2015-01-01", tz="UTC"),
          "NDX": pd.Timestamp("2015-01-01", tz="UTC"),
          "RTY": pd.Timestamp("2015-01-01", tz="UTC")}

# ================ 1. Zarattini noise-area intraday momentum
def zarattini(mkt, cost_mult=1.0):
    b = get_bars(mkt)
    sess = list(sessions(mkt, b))
    # per-slot sigma over trailing 14 sessions: |price(t)-open|/open by slot index
    hist = []          # list of dict slot->absmove
    trades = []
    prior_close = None
    for t0, t1, s in sess:
        op = float(s.open.iloc[0])
        slots = ((s.index - t0).total_seconds() // 300).astype(int)
        absmove = pd.Series((s.close.values / op - 1), index=slots).abs()
        if len(hist) >= 14:
            sig = pd.DataFrame(hist[-14:]).mean(axis=0)     # slot -> sigma
            up = pd.Series(op * (1 + sig.reindex(slots).values), index=s.index)
            dn = pd.Series(op * (1 - sig.reindex(slots).values), index=s.index)
            if prior_close is not None:
                gap = op - prior_close
                if gap < 0: up = up - gap          # gap-down: raise upper band
                if gap > 0: dn = dn - gap          # gap-up: lower the lower band
            v = s.volume.replace(0, 1.0)
            tp = (s.high + s.low + s.close) / 3
            vwap = (tp * v).cumsum() / v.cumsum()
            mins_of = ((s.index - t0).total_seconds() // 60).astype(int)
            is_mark = (mins_of % 30 == 29) | (mins_of % 30 == 0)   # ~HH:00/HH:30 on 5m grid
            pos, entry_px, day_pnl_legs = 0, None, []
            for i in range(len(s)):
                if not is_mark[i]:
                    continue
                c = float(s.close.iloc[i]); u = float(up.iloc[i]); l = float(dn.iloc[i]); vw = float(vwap.iloc[i])
                if pos == 0:
                    if c > u: pos, entry_px = 1, c
                    elif c < l: pos, entry_px = -1, c
                elif pos == 1:
                    trail = max(u, vw)
                    if c < trail:
                        day_pnl_legs.append((entry_px, c - entry_px)); pos = 0
                        if c < l: pos, entry_px = -1, c
                elif pos == -1:
                    trail = min(l, vw)
                    if c > trail:
                        day_pnl_legs.append((entry_px, entry_px - c)); pos = 0
                        if c > u: pos, entry_px = 1, c
            if pos != 0:
                c = float(s.close.iloc[-1])
                day_pnl_legs.append((entry_px, (c - entry_px) if pos == 1 else (entry_px - c)))
            for e, g in day_pnl_legs:
                trades.append(dict(day=t0, entry=e, pnl=g - COST[mkt] * cost_mult))
        hist.append(absmove.groupby(level=0).last())
        prior_close = float(s.close.iloc[-1])
    return trades

for mkt in ("SPX", "NDX", "RTY", "XAU"):
    tr = zarattini(mkt)
    out[f"ZAR_{mkt}"] = score(tr, SPLITS[mkt])
# cost sensitivity on SPX and XAU
for mkt in ("SPX", "XAU"):
    for m_ in (0.0, 2.0):
        out[f"ZAR_{mkt}_cost_x{m_}"] = score(zarattini(mkt, m_), SPLITS[mkt])

# ================ 2. Momentum Pinball
def pinball(mkt):
    b = get_bars(mkt)
    sess = list(sessions(mkt, b))
    closes = pd.Series([float(s.close.iloc[-1]) for _, _, s in sess],
                       index=[t0 for t0, _, _ in sess])
    lbr = I.rsi(closes.pct_change(), 3)      # RSI(3) of ROC(1)
    trades = []
    for k in range(1, len(sess) - 1):
        v = lbr.iloc[k]
        if not np.isfinite(v) or (30 <= v <= 70):
            continue
        t0, t1, s = sess[k + 1]
        first_hour = s[s.index < t0 + pd.Timedelta(hours=1)]
        rest = s[s.index >= t0 + pd.Timedelta(hours=1)]
        if len(first_hour) < 6 or len(rest) < 10:
            continue
        fh_hi, fh_lo = float(first_hour.high.max()), float(first_hour.low.min())
        side = 1 if v < 30 else -1
        trig = fh_hi if side > 0 else fh_lo
        stop = fh_lo if side > 0 else fh_hi
        filled = None
        for bar in rest.itertuples():
            if filled is None:
                if (side > 0 and bar.high >= trig) or (side < 0 and bar.low <= trig):
                    filled = trig
                continue
            if (side > 0 and bar.low <= stop) or (side < 0 and bar.high >= stop):
                trades.append(dict(day=t0, entry=filled,
                                   pnl=side * (stop - filled) - COST[mkt]))
                filled = "done"; break
        if filled not in (None, "done"):
            # exit next session close (1-day hold, frozen)
            if k + 2 < len(sess):
                nx_close = float(sess[k + 2][2].close.iloc[-1])
                trades.append(dict(day=t0, entry=filled,
                                   pnl=side * (nx_close - filled) - COST[mkt]))
    return trades

for mkt in ("XAU", "SPX"):
    out[f"PIN_{mkt}"] = score(pinball(mkt), SPLITS[mkt])

# ================ 3. Market Profile 80% rule
def rule80(mkt):
    b = get_bars(mkt)
    sess = list(sessions(mkt, b))
    trades, fills, setups = [], 0, 0
    prev_va = None
    for t0, t1, s in sess:
        if prev_va is not None:
            val, vah = prev_va
            op = float(s.open.iloc[0])
            if op > vah or op < val:
                # 30m sub-bars
                s30 = s.resample("30min", origin=t0).agg(close=("close", "last"),
                                                         high=("high", "max"),
                                                         low=("low", "min")).dropna()
                inside = (s30.close <= vah) & (s30.close >= val)
                trig_i = None
                for i in range(1, len(s30)):
                    if inside.iloc[i] and inside.iloc[i - 1]:
                        trig_i = i; break
                if trig_i is not None and trig_i < len(s30) - 2:
                    setups += 1
                    side = 1 if op < val else -1      # traversing up from below / down from above
                    entry = float(s30.close.iloc[trig_i])
                    tgt = vah if side > 0 else val
                    width = vah - val
                    stop = (val - 0.25 * width) if side > 0 else (vah + 0.25 * width)
                    path = s.loc[s30.index[trig_i] + pd.Timedelta(minutes=30):]
                    exit_px, filled_tgt = None, False
                    for bar in path.itertuples():
                        if (side > 0 and bar.low <= stop) or (side < 0 and bar.high >= stop):
                            exit_px = stop; break
                        if (side > 0 and bar.high >= tgt) or (side < 0 and bar.low <= tgt):
                            exit_px = tgt; filled_tgt = True; break
                    if exit_px is None and len(path):
                        exit_px = float(path.close.iloc[-1])
                    if exit_px is not None:
                        fills += filled_tgt
                        trades.append(dict(day=t0, entry=entry,
                                           pnl=side * (exit_px - entry) - COST[mkt]))
        # today's value area for tomorrow (70% volume around POC, 5m bins)
        pr = ((s.high + s.low) / 2).values
        vv = s.volume.values.astype(float)
        if vv.sum() <= 0:
            vv = np.ones_like(vv)
        lo, hi = pr.min(), pr.max()
        bins = np.linspace(lo, hi, 60)
        which = np.clip(np.digitize(pr, bins) - 1, 0, 58)
        vol_at = np.zeros(59)
        for w, v_ in zip(which, vv):
            vol_at[w] += v_
        poc = int(vol_at.argmax())
        need = 0.70 * vol_at.sum()
        a_, b_ = poc, poc
        got = vol_at[poc]
        while got < need and (a_ > 0 or b_ < 58):
            up_v = vol_at[b_ + 1] if b_ < 58 else -1
            dn_v = vol_at[a_ - 1] if a_ > 0 else -1
            if up_v >= dn_v: b_ += 1; got += max(up_v, 0)
            else: a_ -= 1; got += max(dn_v, 0)
        prev_va = (bins[a_], bins[min(b_ + 1, 58)])
    return trades, (fills / setups if setups else np.nan), setups

for mkt in ("SPX", "XAU"):
    tr, fill_rate, setups = rule80(mkt)
    out[f"R80_{mkt}"] = score(tr, SPLITS[mkt])
    out[f"R80_{mkt}"]["claimed_80pct_fill_rate_actual"] = float(fill_rate)
    out[f"R80_{mkt}"]["setups"] = setups

# ================ 4. Holy Grail on H1 (documented addition; daily too rare)

def holy_grail_h1(mkt):
    b = get_bars(mkt)
    h = b.resample("1h").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last")).dropna()
    a, _, _ = I.adx(h, 14)
    ema20 = I.ema(h.close, 20)
    sh, sl = I.swing_pivots(h, 2)
    tr = []
    H, L, C = h.high.values, h.low.values, h.close.values
    for i in range(30, len(h) - 11):
        if not (a.iloc[i] > 30 and a.iloc[i] > a.iloc[i - 1]):
            continue
        touch = L[i] <= ema20.iloc[i] <= H[i]
        if not touch:
            continue
        up = C[i] > ema20.iloc[i - 5]
        if up:
            trig, stop, tgt = H[i], L[i], sh.iloc[i]
            if not np.isfinite(tgt) or tgt <= trig or H[i + 1] < trig:
                continue
            exit_px = None
            for j in range(i + 1, min(i + 11, len(h))):
                if L[j] <= stop: exit_px = stop; break
                if H[j] >= tgt: exit_px = tgt; break
            if exit_px is None: exit_px = C[min(i + 10, len(h) - 1)]
            tr.append(dict(day=h.index[i + 1], entry=trig, pnl=exit_px - trig - COST[mkt]))
        else:
            trig, stop, tgt = L[i], H[i], sl.iloc[i]
            if not np.isfinite(tgt) or tgt >= trig or L[i + 1] > trig:
                continue
            exit_px = None
            for j in range(i + 1, min(i + 11, len(h))):
                if H[j] >= stop: exit_px = stop; break
                if L[j] <= tgt: exit_px = tgt; break
            if exit_px is None: exit_px = C[min(i + 10, len(h) - 1)]
            tr.append(dict(day=h.index[i + 1], entry=trig, pnl=trig - exit_px - COST[mkt]))
    return tr

for mkt in ("XAU", "SPX"):
    out[f"HG_{mkt}_H1"] = score(holy_grail_h1(mkt), SPLITS[mkt])

json.dump(out, open("results/r28_intraday.json", "w"), indent=1, default=str)
print(f"{'cell':>18} {'n':>6} {'PF':>7} {'win%':>6} {'t':>7}  halves / extras")
for k, v in out.items():
    if "pf" in v:
        ex = ""
        if "claimed_80pct_fill_rate_actual" in v:
            ex = f"  VA-fill rate {v['claimed_80pct_fill_rate_actual']*100:.0f}% (claim 80%, setups {v['setups']})"
        print(f"{k:>18} {v['n']:>6} {v['pf']:>7.3f} {v['win']*100:>5.1f} {v['t']:>+7.2f}  "
              f"{v['h1']['pf'] if v['h1']['pf']==v['h1']['pf'] else 0:.2f}/"
              f"{v['h2']['pf'] if v['h2']['pf']==v['h2']['pf'] else 0:.2f}{ex}")
    else:
        print(f"{k:>18} {v['n']:>6}  (too few)")
