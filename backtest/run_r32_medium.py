"""Round 32a: claims audit of Medium "Automated Trading Strategy #60"
(Celan Bryant, Jan 2023; recovered from the 2024-10 Wayback capture - the
live page is Cloudflare-blocked and the rules/indicators are paywalled, so
nothing is runnable; this script re-derives every checkable number in the
two published NinjaTrader tables and tests the pre-registered predictions
about the "combined max drawdown" figure and the sizing formula).
Outputs results/r32_medium.json."""
import json
import numpy as np

# Table 1 rows: (instr, net, gross_win, gross_loss, pf, maxdd, trades, wr, tick_usd)
T = [
    ("EMD", 129460, 336340, 206880, 1.63, 19540, 581, 0.5628, 10.00),
    ("ES",   69950, 250050, 180100, 1.39, 16625, 642, 0.5732, 12.50),
    ("NQ",  120145, 481265, 361120, 1.33, 33760, 466, 0.4142,  5.00),
    ("RTY",  32800, 117860,  85060, 1.39,  6035, 526, 0.5247,  5.00),
    ("YM",   56620, 154895,  98275, 1.58,  8865, 517, 0.5667,  5.00),
]
CLAИM = None  # guard against typos
claimed = dict(net=408975, gross_win=1340410, gross_loss=931435, pf=1.44,
               maxdd=16660.24, trades=2732, wr=0.5333, nq_winloss=2.56,
               comb_winloss=1.24, t2_maxdd=83301.18)

net = sum(r[1] for r in T); gw = sum(r[2] for r in T); gl = sum(r[3] for r in T)
ntr = sum(r[6] for r in T)
wins = sum(r[6] * r[7] for r in T); losses = ntr - wins
out = dict(sums=dict(
    net=[net, claimed["net"], net == claimed["net"]],
    gross_win=[gw, claimed["gross_win"], gw == claimed["gross_win"]],
    gross_loss=[gl, claimed["gross_loss"], gl == claimed["gross_loss"]],
    pf=[round(gw / gl, 3), claimed["pf"]],
    trades=[ntr, claimed["trades"], ntr == claimed["trades"]],
    weighted_wr=[round(wins / ntr, 4), claimed["wr"]]))

# --- the combined "max drawdown" figure ---
dds = [r[5] for r in T]
out["drawdown"] = dict(
    per_instrument=dds, summed=sum(dds), mean=float(np.mean(dds)),
    claimed_combined=claimed["maxdd"],
    claimed_over_mean=float(claimed["maxdd"] / np.mean(dds)),
    worst_single=max(dds),
    table2_combined=claimed["t2_maxdd"],
    table2_is_5x_table1=bool(abs(claimed["t2_maxdd"] - 5 * claimed["maxdd"]) < 0.1),
    cents_possible=bool((claimed["maxdd"] * 100) % 125 == 0),  # all P&L multiples of $1.25
    note="claimed combined DD (16,660) < worst single instrument DD (NQ "
         "33,760): impossible for a portfolio equity curve that includes NQ "
         "unless other sleeves rally >17K exactly through NQ's trough; it is "
         "~0.98x the MEAN of the five DDs and scales exactly 5x in Table 2 - "
         "a derived average, not a portfolio drawdown. The .24 cents cannot "
         "arise from these contracts' tick values.")

# --- win/loss (avg win / avg loss) claims ---
nq = T[2]
nq_w = nq[6] * nq[7]; nq_l = nq[6] - nq_w
out["winloss"] = dict(
    nq_actual=round((nq[2] / nq_w) / (nq[3] / nq_l), 2), nq_claimed=2.56,
    combined_actual=round((gw / wins) / (gl / losses), 2), combined_claimed=1.24)

# --- the sizing formula's risk understatement ---
# author: $1M / avg DD ($16.66K -> $20K) = 50 contracts, halved to 25 (5 per mkt)
# at 5 lots/instrument their own Table 2 shows NQ alone drawing $168,800; if
# the five correlated sleeves draw down together (2022: they did), portfolio
# risk is bounded by the sum, not the mean.
out["sizing"] = dict(
    formula="account / average per-instrument DD",
    implied_risk_25_lots=claimed["t2_maxdd"],
    summed_dd_25_lots=5 * sum(dds),
    understatement=float(5 * sum(dds) / claimed["t2_maxdd"]),
    pct_of_1M_account=float(5 * sum(dds) / 1e6))

json.dump(out, open("results/r32_medium.json", "w"), indent=1, default=float)

print("sums (derived vs claimed):")
for k, v in out["sums"].items():
    print(f"  {k:>12}: {v[0]} vs {v[1]}" + ("  OK" if len(v) < 3 or v[2] else "  MISMATCH"))
d = out["drawdown"]
print(f"\ncombined maxDD claimed {d['claimed_combined']:,} = {d['claimed_over_mean']:.2f}x the "
      f"MEAN of per-instrument DDs (mean {d['mean']:,.0f}, sum {d['summed']:,}, worst single "
      f"{d['worst_single']:,})")
print(f"Table 2 combined DD is exactly 5x Table 1: {d['table2_is_5x_table1']}; "
      f".24 cents possible from tick values: {d['cents_possible']}")
w = out["winloss"]
print(f"win/loss: NQ actual {w['nq_actual']} vs claimed {w['nq_claimed']}; "
      f"combined actual {w['combined_actual']} vs claimed {w['combined_claimed']}")
s = out["sizing"]
print(f"sizing: 25-lot risk shown as ${s['implied_risk_25_lots']:,.0f}; summed per-instrument "
      f"DDs ${s['summed_dd_25_lots']:,} = {s['understatement']:.1f}x more = "
      f"{s['pct_of_1M_account']*100:.0f}% of the $1M account")
