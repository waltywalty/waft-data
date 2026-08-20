"""Use the sweep as an EXIT: how far away does the structure stop need to sit?"""
import pandas as pd, numpy as np, engine, sweep, warnings
warnings.filterwarnings("ignore")
bars = engine.load_bars()
rows = []
for L in (30, 60):
    for k in (2, 4, 8):
        for buf in (0.0, 0.5, 1.0):
            d = sweep.structure_stop(bars, L, swing_k=k, buffer_r=buf)
            for a in ("london_mid", "pre_ny", "ny_close"):
                s = sweep.stats(d, f"pnl_{a}")
                if not s: continue
                rows.append({"range": f"{L}m", "swing_k": k, "buffer_R": buf, "exit": a,
                             "n": s["n"], "win%": round(s["win"]*100, 1),
                             "PF": round(s["pf"], 3), "exp_$": round(s["exp"], 2),
                             "stopped%": round(d[f"stopped_{a}"].mean()*100, 0),
                             "t": round(s["t"], 2)})
r = pd.DataFrame(rows)
print("=== Sweep-as-exit (enter at breakout, exit when structure is swept) ===")
print(r.to_string(index=False))
print("\nBaseline (plain time exit, no structure stop):")
for L in (30, 60):
    for a in ("london_mid", "ny_close"):
        pass
for L in (30, 60):
    d0 = sweep.structure_stop(bars, L, buffer_r=99)   # buffer so wide it never stops
    for a in ("london_mid", "pre_ny", "ny_close"):
        s = sweep.stats(d0, f"pnl_{a}")
        if s:
            print(f"  {L}m / {a:11s} n={s['n']:4d} PF={s['pf']:.3f} win={s['win']*100:.1f}% exp=${s['exp']:+.2f}")
