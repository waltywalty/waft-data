"""MGC vs spot, across account sizes."""
import pandas as pd, numpy as np, mgc, portfolio as P, warnings, json
warnings.filterwarnings("ignore")
d = pd.read_pickle("results/trades_filtered_2r.pkl")
m = mgc.prepare(d, cost_oz=0.40)

print("=== A. THE SAME RULE ON MGC, BY ACCOUNT SIZE (1% risk target, 2R stop) ===")
print(f"{'account':>10}{'trades taken':>14}{'skipped':>9}{'avg lots':>10}{'final':>13}"
      f"{'CAGR':>9}{'maxDD':>8}{'worst':>8}")
rows = []
for acct in (2000, 5000, 10000, 25000, 50000, 100000):
    r = mgc.simulate(m, acct, "risk", 0.01)
    curve = r.pop("curve"); rows.append({"acct": acct, "risk": 0.01, **r})
    print(f"{acct:>10,}{r['taken']:>14}{r['skipped']:>9}{r['avg_contracts']:>10.1f}"
          f"{r['final']:>13,.0f}{r['cagr']*100:>8.1f}%{r['max_dd']*100:>7.1f}%"
          f"{r['worst_trade']*100:>7.1f}%")

print("\n=== B. SAME, AT 2% RISK ===")
print(f"{'account':>10}{'trades taken':>14}{'skipped':>9}{'avg lots':>10}{'final':>13}"
      f"{'CAGR':>9}{'maxDD':>8}{'worst':>8}")
for acct in (2000, 5000, 10000, 25000, 50000):
    r = mgc.simulate(m, acct, "risk", 0.02)
    r.pop("curve"); rows.append({"acct": acct, "risk": 0.02, **r})
    print(f"{acct:>10,}{r['taken']:>14}{r['skipped']:>9}{r['avg_contracts']:>10.1f}"
          f"{r['final']:>13,.0f}{r['cagr']*100:>8.1f}%{r['max_dd']*100:>7.1f}%"
          f"{r['worst_trade']*100:>7.1f}%")

print("\n=== C. $2,000 ON MGC: WHAT ACTUALLY HAPPENS ===")
for label, mode, risk in (("1% risk target", "risk", 0.01), ("2% risk target", "risk", 0.02),
                          ("5% risk target", "risk", 0.05), ("max margin (all-in)", "allin", None)):
    r = mgc.simulate(m, 2000, mode, risk or 0.01)
    r.pop("curve")
    print(f"  {label:22s} took {r['taken']:>4} of {r['taken']+r['skipped']}, "
          f"final ${r['final']:>9,.0f}, CAGR {r['cagr']*100:>7.1f}%, maxDD {r['max_dd']*100:>5.1f}%, "
          f"worst trade {r['worst_trade']*100:>6.1f}%, ruin {r['ruin'] or '-'}")

print("\n=== D. MGC vs SPOT CFD AT THE SAME ACCOUNT SIZE (1% risk, 2R stop) ===")
print(f"{'account':>10}{'MGC final':>12}{'MGC CAGR':>10}{'MGC DD':>8}   |"
      f"{'spot final':>12}{'spot CAGR':>11}{'spot DD':>9}{'  spot trades taken':>20}")
cmp_rows = []
sp = d.copy()
sp["pnl_oz"] = sp.pnl_oz - np.where(sp.reason == "stop", 0.30, 0.0)   # CFD: $0.30 slip
for acct in (2000, 5000, 10000, 25000, 50000):
    a = mgc.simulate(m, acct, "risk", 0.01)
    b = P.simulate(sp, "risk", 0.01, 20.0, start=acct)
    a.pop("curve"); b.pop("curve")
    cmp_rows.append({"acct": acct, "mgc": a, "spot": b})
    print(f"{acct:>10,}{a['final']:>12,.0f}{a['cagr']*100:>9.1f}%{a['max_dd']*100:>7.1f}%   |"
          f"{b['final']:>12,.0f}{b['cagr']*100:>10.1f}%{b['max_dd']*100:>8.1f}%{len(sp):>20}")

print("\n=== E. COST SENSITIVITY ON MGC ($25,000 account, 1% risk) ===")
for c in (0.20, 0.30, 0.40, 0.60, 0.80):
    mm = mgc.prepare(d, cost_oz=c)
    r = mgc.simulate(mm, 25000, "risk", 0.01); r.pop("curve")
    print(f"  ${c:.2f}/oz round trip (${c*10:.2f}/contract): final ${r['final']:>10,.0f}  "
          f"CAGR {r['cagr']*100:>6.1f}%")

print("\n=== F. TICK ROUNDING: does the $0.10 grid change anything? ===")
raw = d.side * (d.exit - d.entry) - 0.40   # same cost, unrounded prices
rnd = m.pnl_oz_f
print(f"  mean P&L/oz  raw ${raw.mean():+.4f}  vs tick-rounded ${rnd.mean():+.4f}  "
      f"(difference ${rnd.mean()-raw.mean():+.4f})")
pf = lambda s: s[s > 0].sum() / max(-s[s <= 0].sum(), 1e-9)
print(f"  profit factor  raw {pf(raw):.4f}  vs tick-rounded {pf(rnd):.4f}")

json.dump({"by_acct": rows, "cmp": cmp_rows,
           "per_contract": {"notional": float(m.notional.mean()),
                            "margin6": float((m.notional * .06).mean()),
                            "risk": float(m.risk_per_contract.mean()),
                            "risk_med": float(m.risk_per_contract.median()),
                            "risk_p90": float(m.risk_per_contract.quantile(.9))}},
          open("results/mgc.json", "w"), indent=1)
