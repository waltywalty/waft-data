"""Does MGC track spot gold closely enough that a spot-derived signal carries over?

Compares COMEX Micro Gold (MGCZ6, the active contract) against the spot gold
quotes this repo's own relay recorded over the same days.
"""
import pandas as pd, numpy as np, json

f = pd.read_csv("data/MGCZ6_30m.csv", parse_dates=["ts"]).set_index("ts").close
spot = pd.Series(json.load(open("/tmp/waft_gold_30m.json")))
spot.index = pd.to_datetime([int(k) for k in spot.index], unit="s")

j = pd.concat([f.rename("fut"), spot.rename("spot")], axis=1, join="inner").dropna()
print(f"matched 30-minute observations: {len(j)}  ({j.index.min()} .. {j.index.max()} UTC)")

b = j.fut - j.spot
print(f"\n=== BASIS (MGC Dec-26 minus spot) ===")
print(f"  mean ${b.mean():+.2f}   sd ${b.std():.2f}   range ${b.min():+.2f} to ${b.max():+.2f}")
print(f"  as a share of price: {b.mean()/j.spot.mean()*100:+.3f}%")
print(f"  drift across the 3 days: ${b.iloc[:8].mean():+.2f} at the start -> ${b.iloc[-8:].mean():+.2f} at the end")

print(f"\n=== DO THE MOVES MATCH? (this is the load-bearing question) ===")
for shift in (0, 1, -1):
    x = j.copy()
    x["fut"] = x.fut.shift(shift)
    d = x.dropna().diff().dropna()
    if len(d) < 20: continue
    lab = {0: "aligned", 1: "futures lagged 30m", -1: "futures led 30m"}[shift]
    print(f"  {lab:20s} corr of 30-min changes = {d.fut.corr(d.spot):+.4f}")
d = j.diff().dropna()
beta = np.polyfit(d.spot, d.fut, 1)
resid = d.fut - (beta[0] * d.spot + beta[1])
print(f"  regression slope (futures per $1 of spot) = {beta[0]:.4f}")
print(f"  residual sd = ${resid.std():.2f} per 30-min bar  "
      f"({resid.std()/0.10:.1f} MGC ticks)")
print(f"  mean |30-min move| = ${d.spot.abs().mean():.2f}; tracking error is "
      f"{resid.std()/d.spot.abs().mean()*100:.0f}% of a typical move")

print(f"\n=== WHAT THIS MEANS FOR THE BACKTEST ===")
print(f"  A trade's P&L is a difference of two prices. The basis cancels out of any")
print(f"  same-session trade to within its drift, which over these 3 days was "
      f"${abs(b.iloc[-8:].mean()-b.iloc[:8].mean()):.2f}/day,")
print(f"  or ${abs(b.iloc[-8:].mean()-b.iloc[:8].mean())/24*14:.2f} over a typical 14-hour hold.")
print(f"  Set against an average trade of about $2/oz, that is a rounding error but not zero.")
