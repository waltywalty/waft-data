"""The same rule traded as MGC (COMEX Micro Gold) instead of spot XAUUSD.

Contract mechanics
  size      10 troy ounces
  tick      $0.10 per ounce = $1.00 per contract
  session   Sun-Fri 18:00-17:00 ET with a 60-minute break at 17:00 ET.
            The trade opens at 09:30 HKT = 21:30 ET, about 3.5 hours into the
            session, and closes at 16:00 ET the same session - so it never
            crosses settlement and never needs a roll.
  margin    modelled as a percentage of notional (CME gold initial margin has
            run roughly 4-7% of notional; day-trade margin at many brokers is
            about half that).
  costs     $0.40 per ounce round trip = $4.00 per contract, covering IBKR-style
            commission and exchange fees (~$1.70/contract) plus roughly one tick
            of spread. Asia-session spreads are wider than the US day session.
"""
import pandas as pd, numpy as np

OZ = 10
TICK = 0.10

def tickr(p):
    return np.round(p / TICK) * TICK

def prepare(tr, cost_oz=0.40):
    """Re-price a spot trade log onto the futures tick grid and cost structure."""
    d = tr.copy()
    d["entry_f"] = tickr(d.entry)
    d["exit_f"] = tickr(d.exit)
    d["stop_dist_f"] = np.maximum(tickr(d.stop_dist), TICK)
    d["pnl_oz_f"] = d.side * (d.exit_f - d.entry_f) - cost_oz
    d["risk_per_contract"] = d.stop_dist_f * OZ
    d["notional"] = d.entry_f * OZ
    return d

def simulate(d, start, mode="risk", risk=0.01, margin_rate=0.06, max_contracts=None):
    eq = start
    curve, skipped, taken, sizes, rets = [], 0, 0, [], []
    ruin = None
    for r in d.itertuples():
        if eq <= 0:
            curve.append((r.day, 0.0)); continue
        afford = int(eq // (r.notional * margin_rate))       # margin-limited
        if mode == "risk":
            n = int((eq * risk) // r.risk_per_contract)
            n = min(n, afford)
        else:
            n = afford
        if max_contracts:
            n = min(n, max_contracts)
        if n < 1:
            skipped += 1
            curve.append((r.day, eq)); continue
        taken += 1; sizes.append(n)
        if n * OZ * r.mae_oz >= eq:                          # liquidated intratrade
            eq = 0.0; ruin = ruin or r.day
            rets.append(-1.0); curve.append((r.day, 0.0)); continue
        p = n * OZ * r.pnl_oz_f
        rets.append(p / eq)
        eq = max(eq + p, 0.0)
        if eq <= 0 and ruin is None: ruin = r.day
        curve.append((r.day, eq))
    c = pd.Series([e for _, e in curve], index=[x for x, _ in curve])
    peak = c.cummax()
    dd = ((peak - c) / peak.replace(0, np.nan)).fillna(1.0)
    yrs = (pd.Timestamp(c.index[-1]) - pd.Timestamp(c.index[0])).days / 365.25
    rets = pd.Series(rets)
    return {"start": start, "final": float(c.iloc[-1]),
            "cagr": float((c.iloc[-1] / start) ** (1 / yrs) - 1) if c.iloc[-1] > 0 else -1.0,
            "max_dd": float(dd.max()), "taken": taken, "skipped": skipped,
            "skip_rate": skipped / max(taken + skipped, 1),
            "avg_contracts": float(np.mean(sizes)) if sizes else 0.0,
            "max_contracts": int(np.max(sizes)) if sizes else 0,
            "worst_trade": float(rets.min()) if len(rets) else 0.0,
            "ruin": str(ruin) if ruin else None, "curve": c}
