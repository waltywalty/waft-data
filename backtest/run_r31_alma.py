"""Round 31: replicate the "ALMA Averaging Strategy" (Russell 6H, long only).

Claimed: 76% WR, PF 2.8, maxDD 20%, avg win +2.5% / avg loss -2.3%,
~25-bar winner holds, 306 trades. Spec frozen per the pre-registration in
reference/goal_ledger.md (conventions documented there; the Idea is silent
on band length, execution timing, and account sizing).

Mechanics per frozen spec:
  bars    : RTY 5m -> 6H, anchored 05:00 UTC (Idea's own fill stamps)
  ALMA    : window 3, offset 0.85, sigma 2, on closes
  entry   : close < ALMA - 2*SD(close,3) -> buy 25% tranche next open
  adds    : further qualifying closes >=1% below last fill, max 4 tranches
  exit    : close >= 1.01*ALMA -> sell all next open
  stop    : intrabar low <= 0.90 * avg entry -> flat at stop price
  costs   : 0.4 RTY pts round trip per tranche (house), zero-cost diagnostic
  account : tranche = 25% of account notional; per-trade return on account

Cells: 6H (primary), 8H, anchor-0 6H, SD-length-20 6H; each at cost/zerocost;
halves on the primary. Outputs results/r31_alma.json.
"""
import pandas as pd, numpy as np, json, warnings, index_data
warnings.filterwarnings("ignore")

COST = 0.4          # pts RT per tranche
STOP = 0.10
MINDIFF = 0.01
MAXT = 4


def alma(x, window=3, offset=0.85, sigma=2.0):
    m = offset * (window - 1)
    s = window / sigma
    w = np.exp(-((np.arange(window) - m) ** 2) / (2 * s * s))
    w /= w.sum()
    return x.rolling(window).apply(lambda v: float(np.dot(v, w)), raw=True)


def make_bars(freq, anchor):
    r = index_data.load("RTY")
    return (r.resample(freq, offset=f"{anchor}h")
             .agg(open=("open", "first"), high=("high", "max"),
                  low=("low", "min"), close=("close", "last"))
             .dropna(subset=["open"]))


def run(bars, entry_qual, baseline, cost=COST, spacing=MINDIFF):
    """entry_qual: bool Series - this close qualifies for a tranche.
    baseline: the ALMA series used for the exit (close >= 1.01*baseline).
    spacing: min fractional gap below last fill for an add (0 = every bar)."""
    c = bars.close
    a = baseline
    o, h, l = bars.open.values, bars.high.values, bars.low.values
    qual = entry_qual.values
    cv, av = c.values, a.values
    n = len(bars)
    fills, trades = [], []          # fills: (price, frac, bar_index)
    pend_entry = pend_exit = False
    for i in range(25, n):
        # execute orders queued on the previous close
        if pend_exit and fills:
            avg = sum(p * f for p, f, _ in fills) / sum(f for p, f, _ in fills)
            size = sum(f for p, f, _ in fills)
            ret = size * ((o[i] - avg) / avg) - cost * size / avg * len(fills)
            trades.append(dict(t=bars.index[i], ret=ret, avg=avg, ntr=len(fills),
                               bars=i - fills[0][2], kind="flip"))
            fills = []
        if pend_entry and len(fills) < MAXT:
            if not fills or o[i] <= fills[-1][0] * (1 - spacing):
                fills.append((o[i], 0.25, i))
        pend_entry = pend_exit = False
        # intrabar hard stop on the open position
        if fills:
            avg = sum(p * f for p, f, _ in fills) / sum(f for p, f, _ in fills)
            if l[i] <= avg * (1 - STOP):
                size = sum(f for p, f, _ in fills)
                px = avg * (1 - STOP)
                ret = size * ((px - avg) / avg) - cost * size / avg * len(fills)
                trades.append(dict(t=bars.index[i], ret=ret, avg=avg,
                                   ntr=len(fills), bars=i - fills[0][2], kind="stop"))
                fills = []
                continue
        # signals on this close
        if not np.isfinite(av[i]):
            continue
        if fills and cv[i] >= av[i] * (1 + MINDIFF):
            pend_exit = True
        elif qual[i]:
            pend_entry = True
    return pd.DataFrame(trades)


def score(tr, bars):
    if not len(tr):
        return dict(n=0)
    r = tr.ret
    win, loss = r[r > 0], r[r <= 0]
    pf = win.sum() / abs(loss.sum()) if len(loss) and loss.sum() < 0 else np.inf
    eq = (1 + r).cumprod()
    dd = ((eq.cummax() - eq) / eq.cummax()).max()
    yrs = (bars.index[-1] - bars.index[0]).days / 365.25
    return dict(n=int(len(r)), wr=float((r > 0).mean()), pf=float(pf),
                total=float(eq.iloc[-1]), cagr=float(eq.iloc[-1] ** (1 / yrs) - 1),
                max_dd=float(dd),
                avg_win=float(win.mean()) if len(win) else np.nan,
                avg_loss=float(loss.mean()) if len(loss) else np.nan,
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                stops=int((tr.kind == "stop").sum()),
                med_bars_win=float(tr.loc[r > 0, "bars"].median()) if len(win) else np.nan,
                avg_tranches=float(tr.ntr.mean()))


def specs(bars):
    """The under-determined dimensions of the Idea, as documented cells.
    Literal band (ALMA3 - 2*SD3) fires ZERO times in 15.4y (max z-score on
    3 points ~1.15 < 2) so the stated spec cannot be what their template
    runs; each cell below is one defensible completion of the text."""
    c = bars.close
    a3, a20 = alma(c, 3), alma(c, 20)
    sd20 = c.rolling(20).std()
    return {
        "band3": (c < a3 - 2 * c.rolling(3).std(), a3),      # literal
        "band20": (c < a3 - 2 * sd20, a3),                   # SD len -> 20
        "mindiff": (c <= a3 * (1 - MINDIFF), a3),            # 1% below ALMA3
        "band20/20": (c < a20 - 2 * sd20, a20),              # both len 20
    }


out = {}
b6, b6a0, b8 = make_bars("6h", 5), make_bars("6h", 0), make_bars("8h", 5)
sig6, sig6a0, sig8 = specs(b6), specs(b6a0), specs(b8)
cells = {
    "6H band3 cost": (b6, *sig6["band3"], COST, MINDIFF),
    "6H band20 cost": (b6, *sig6["band20"], COST, MINDIFF),
    "6H band20/20 cost": (b6, *sig6["band20/20"], COST, MINDIFF),
    "6H mindiff cost": (b6, *sig6["mindiff"], COST, MINDIFF),      # headline: n matches claim
    "6H mindiff zerocost": (b6, *sig6["mindiff"], 0.0, MINDIFF),
    "6H mindiff nospace": (b6, *sig6["mindiff"], COST, 0.0),
    "6H mindiff anchor0": (b6a0, *sig6a0["mindiff"], COST, MINDIFF),
    "8H mindiff cost": (b8, *sig8["mindiff"], COST, MINDIFF),
    "8H mindiff zerocost": (b8, *sig8["mindiff"], 0.0, MINDIFF),
}
for name, (bars, q, base, cost, sp) in cells.items():
    tr = run(bars, q, base, cost, sp)
    out[name] = score(tr, bars)
    if name == "6H mindiff cost" and len(tr):
        m = len(tr) // 2
        out["6H halves"] = {
            "first": score(tr.iloc[:m].reset_index(drop=True), bars),
            "second": score(tr.iloc[m:].reset_index(drop=True), bars)}
        tr.assign(t=tr.t.astype(str)).to_json("results/r31_trades.json", orient="records")
        # house drift null for long-only systems: random long entries with the
        # trade's own hold length and size; does the ALMA timing beat drift?
        rng = np.random.default_rng(31)
        cv = b6.close.values
        holds = tr.bars.clip(lower=1).astype(int).values
        sizes = (tr.ntr * 0.25).values
        actual = tr.ret.sum()
        nulls = []
        for _ in range(2000):
            st = rng.integers(25, len(cv) - holds.max() - 1, size=len(holds))
            nulls.append(np.sum(sizes * (cv[st + holds] / cv[st] - 1)))
        out["drift_null"] = dict(actual=float(actual),
                                 null_mean=float(np.mean(nulls)),
                                 p=float(np.mean(np.array(nulls) >= actual)))

json.dump(out, open("results/r31_alma.json", "w"), indent=1, default=float)

print(f"{'cell':>22} {'n':>5} {'WR':>6} {'PF':>6} {'total':>7} {'CAGR':>7} {'maxDD':>7} "
      f"{'avgW':>6} {'avgL':>6} {'t':>6} {'stops':>5}")
for name in cells:
    s = out[name]
    if s["n"] == 0:
        print(f"{name:>22}  no trades"); continue
    print(f"{name:>22} {s['n']:>5} {s['wr']*100:>5.1f}% {s['pf']:>6.2f} {s['total']:>6.2f}x "
          f"{s['cagr']*100:>+6.1f}% {s['max_dd']*100:>6.1f}% {s['avg_win']*100:>+5.2f}% "
          f"{s['avg_loss']*100:>+5.2f}% {s['t']:>+6.2f} {s['stops']:>5}")
print("\nclaimed:                306  76.0%   2.80             20.0%  +2.50% -2.30%")
h = out.get("6H halves")
if h:
    for k in ("first", "second"):
        s = h[k]
        print(f"  {k:>6} half: n {s['n']}  WR {s['wr']*100:.1f}%  PF {s['pf']:.2f}  t {s['t']:+.2f}")
