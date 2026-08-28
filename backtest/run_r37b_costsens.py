"""Round 37b: cost sensitivity on the r37 scalp cells (house-rule addendum).
Same signals, same execution, same 48 cells - rescored at three cost levels:
  house  : the r37 registered costs (CFD-spread convention)
  micro  : best-case all-in micro futures round trip (commission + exchange
           fees at a cheap futures broker + one tick of spread crossing):
           MES ~$1.5/RT /$5pt + 0.25 spread ~ 0.35 SPX pts
           MNQ ~$1.5/RT /$2pt + 1-2 tick spread ~ 1.0 NDX pts
           M2K ~$1.5/RT /$5pt + 1-2 tick spread ~ 0.35 RTY pts
           MGC ~$2.4/RT /$10pt + 1-3 tick spread ~ 0.35 gold pts
  zero   : free trading - the theoretical bound no broker can beat
Outputs results/r37b_costsens.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
TP, SLS = ns["TP"], ns["SLS"]

COSTS = {"house": {"SPX": 0.6, "NDX": 2.0, "RTY": 0.4, "GOLD": 0.6},
         "micro": {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35},
         "zero": {"SPX": 0.0, "NDX": 0.0, "RTY": 0.0, "GOLD": 0.0}}

out = {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = ns["load_frame"](idx)
    rth = ns["rth_of"](b)
    rth_by_day = {k: g for k, g in rth.groupby("skey")}
    q = ns["resample_15m"](b)
    fams = {"sweep-reclaim": ns["sig_sweep"](b), "displacement": ns["sig_disp"](q),
            "absorption": ns["sig_absorb"](q)}
    out[idx] = {}
    for fam, sigs in fams.items():
        gross = ns["run_family"](sigs, rth_by_day, 0.0)   # cost applied at scoring
        out[idx][fam] = {}
        for cell, pnls in gross.items():
            p = np.asarray(pnls, float)
            out[idx][fam][cell] = {lvl: ns["score"](p - c[idx]) for lvl, c in COSTS.items()}
    print(f"{idx} done")

json.dump(out, open("results/r37b_costsens.json", "w"), indent=1, default=float)
for idx, fams in out.items():
    print(f"\n=== {idx} (TP +10; avg pts/trade and t at each cost level) ===")
    print(f"{'family':>14} {'cell':>9} {'n':>6} | {'house':>7} {'t':>6} | {'micro':>7} {'t':>6} | {'zero':>7} {'t':>6}")
    for fam, cells in fams.items():
        for cell, lv in cells.items():
            if lv["house"]["n"] == 0:
                continue
            h, m, z = lv["house"], lv["micro"], lv["zero"]
            print(f"{fam:>14} {cell:>9} {h['n']:>6} | {h['avg']:>+7.2f} {h['t']:>+6.2f} | "
                  f"{m['avg']:>+7.2f} {m['t']:>+6.2f} | {z['avg']:>+7.2f} {z['t']:>+6.2f}")
