"""Round 72A step 3, attempt 36 (r55_fix) REVERSED, IN-SAMPLE ONLY.
Copies the data build from backtest/run_r55_fix.py, truncates the price
series to dates strictly BEFORE the runner's IS cut (days[int(len*0.75)])
before any return is computed. No OOS file is opened, nothing is unsealed."""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
COST = 0.35  # runner's cost, 1x micro round trip

m15 = pd.read_csv("data/XAUUSD_m15_ejtrader.csv", parse_dates=["Date"])
m15_px = pd.Series(m15.close.values / 100.0, index=m15.Date - pd.Timedelta(hours=7)).sort_index()
f5 = pd.read_csv("data/XAUUSD_5m.csv")
f5_px = pd.Series(f5.Close.values,
                  index=pd.to_datetime(f5.Date.astype(str) + " " + f5.Time.astype(str))).sort_index()
cutover = f5_px.index[0]
px = pd.concat([m15_px[m15_px.index < cutover], f5_px]).sort_index()
px = px[~px.index.duplicated()]
days = sorted(set(px.index.date))
cutd = days[int(len(days) * 0.75)]          # runner's IS cut, same formula
print(f"full series {px.index[0]}..{px.index[-1]}, {len(days)} days; IS CUT DATE = {cutd} (IS = dates < cut)")

# ---- OOS FIREWALL: drop every bar on/after the cut before anything else ----
px = px[px.index.date < cutd]
print(f"IS-only series {px.index[0]}..{px.index[-1]}, {len(px)} bars")

day = px.groupby(px.index.date)
rng = day.max() - day.min()
atr20 = rng.rolling(20).mean().shift(1)

def marks(hh, mm):
    out = {}
    for d0, g in px.groupby(px.index.date):
        tgt = pd.Timestamp(str(d0)) + pd.Timedelta(hours=hh, minutes=mm)
        i = g.index.searchsorted(tgt)
        if i < len(g) and (g.index[i] - tgt).total_seconds() <= 30 * 60:
            out[d0] = g.iloc[i]
    return pd.Series(out)

TIMES = [(7,0),(7,30),(8,0),(8,30),(9,0),(9,30),(10,0),(10,30),(11,0),(11,30),(12,0),
         (6,0),(6,30)]
M = {t: marks(*t) for t in TIMES}

def build(e_t, x_t, side):
    e, x = M[e_t], M[x_t]
    j = pd.concat([e, x], axis=1, keys=["e", "x"]).dropna()
    j["atr"] = [atr20.get(k, np.nan) for k in j.index]
    j = j[np.isfinite(j.atr) & (j.atr > 0)]
    j["gross"] = side * (j.x - j.e)
    return j

def st(pnl, atr):
    r = (np.asarray(pnl, float) / np.asarray(atr, float)); p = np.asarray(pnl, float)
    ok = np.isfinite(r); r, p = r[ok], p[ok]
    m = len(r)//2
    w, ls = p[p > 0], p[p <= 0]
    return dict(n=len(r), avgR=r.mean(), t=r.mean()/r.std()*np.sqrt(len(r)) if r.std() > 0 else np.nan,
                wr=(p > 0).mean(), pf=(w.sum()/abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

def report(name, j):
    out = {}
    for k in (1.0, 1.5, 2.0):
        out[k] = st(j.gross - k*COST, j.atr)
    g = st(j.gross, j.atr)
    r1 = (j.gross - COST)/j.atr
    yrs = pd.Series(r1.values, index=pd.to_datetime(j.index)).groupby(lambda d: d.year).mean()
    ysign = " ".join(f"{y}:{'+' if v>0 else '-'}" for y, v in yrs.items())
    s1 = out[1.0]
    print(f"{name:>22} | n {s1['n']:>5} | gross avgR {g['avgR']:+.4f} t {g['t']:+.2f} | "
          f"x1 avgR {s1['avgR']:+.4f} t {s1['t']:+.2f} WR {s1['wr']*100:.1f}% PF {s1['pf']:.3f} halves {s1['halves']} | "
          f"x1.5 avgR {out[1.5]['avgR']:+.4f} | x2 avgR {out[2.0]['avgR']:+.4f} t {out[2.0]['t']:+.2f}")
    print(f"{'':>22}   per-year (x1): {ysign}")
    return out, g, yrs

print("\n=== REVERSED selectable cells (IS, net of cost SUBTRACTED) ===")
REV = [("rS1 LONG 09:00->10:00", (9,0), (10,0), +1),
       ("rS2 LONG 09:30->10:00", (9,30), (10,0), +1),
       ("rL1 SHORT 10:00->10:30", (10,0), (10,30), -1),
       ("rL2 SHORT 10:00->11:00", (10,0), (11,0), -1)]
res = {}
for name, e, x, s in REV:
    j = build(e, x, s); res[name] = (report(name, j), j)

print("\n=== UNCONDITIONAL CONTROL ===")
print("The reversed cell trades EVERY eligible IS session in the same window (no filter),")
print("so the always-long / always-short control over the same window IS the same sample.")
for name, e, x, s in REV:
    j = build(e, x, s)
    cr = (j.gross - COST)/j.atr; rr = cr  # identical by construction
    d = rr - cr
    print(f"{name:>22} control n {len(cr)} avgR {cr.mean():+.4f} t {cr.mean()/cr.std()*np.sqrt(len(cr)):+.2f} | "
          f"diff (paired by date) avgR {d.mean():+.4f} t {'0.00 (zero variance, identical samples)'}")

print("\n=== GRADIENT: window width ladder, reversed, anchored on the 10:00 ET fix (IS, x1) ===")
print("pre-fix LONG (reversed S): width 30/60/90/120/180/240 min ending 10:00")
for e in [(9,30),(9,0),(8,30),(8,0),(7,0),(6,0)]:
    j = build(e, (10,0), +1); s = st(j.gross - COST, j.atr); g = st(j.gross, j.atr)
    print(f"   LONG {e[0]:02d}:{e[1]:02d}->10:00 | n {s['n']} gross {g['avgR']:+.4f} net x1 {s['avgR']:+.4f} t {s['t']:+.2f}")
print("post-fix SHORT (reversed L): width 30/60/90/120 min starting 10:00")
for x in [(10,30),(11,0),(11,30),(12,0)]:
    j = build((10,0), x, -1); s = st(j.gross - COST, j.atr); g = st(j.gross, j.atr)
    print(f"   SHORT 10:00->{x[0]:02d}:{x[1]:02d} | n {s['n']} gross {g['avgR']:+.4f} net x1 {s['avgR']:+.4f} t {s['t']:+.2f}")

print("\n=== PLACEBO: family's -2h shifted diagnostics, reversed (IS, x1) ===")
for name, e, x, s in [("rdS1 LONG 07:00->08:00",(7,0),(8,0),+1), ("rdS2 LONG 07:30->08:00",(7,30),(8,0),+1),
                      ("rdL1 SHORT 08:00->08:30",(8,0),(8,30),-1), ("rdL2 SHORT 08:00->09:00",(8,0),(9,0),-1)]:
    j = build(e, x, s); report(name, j)
