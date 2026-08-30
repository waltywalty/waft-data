"""Round 53 attempt 35: gold/silver RV cost-amortization repair (frozen per
reference/goal_ledger.md Round 53 registration). IS-ONLY script: OOS rows
are masked before any statistic; no OOS code path exists here.
Outputs results/r53_gsrv_repair_is.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
COST_BPS = 4.0

# --- pair construction, verbatim from run_r42p_gsrv.py ---
g = load_frame("GOLD")
grows = []
for skey, gg in g.groupby("skey"):
    hm = gg.hm.values
    c, o = gg.close.values, gg.open.values
    def at(t0):
        m = np.where(hm >= t0)[0]
        return o[m[0]] if len(m) else np.nan
    def lastb(t1):
        m = np.where(hm < t1)[0]
        return c[m[-1]] if len(m) else np.nan
    grows.append(dict(skey=skey, g930=at(930), g16=lastb(1600)))
gd = pd.DataFrame(grows).set_index("skey")

sv = pd.read_csv("data/XAGUSD_H1.csv")
ts = pd.to_datetime(sv.datetime, utc=True)
s = pd.Series(sv.close.values, index=ts).sort_index().tz_convert("America/New_York")
srows = {}
for day, gg in s.groupby(s.index.date):
    hh = gg.index.hour * 100 + gg.index.minute
    m16 = np.where(hh < 1600)[0]
    m930 = np.where(hh >= 900)[0]
    srows[day] = (gg.values[m930[0]] if len(m930) else np.nan,
                  gg.values[m16[-1]] if len(m16) else np.nan)
sd = pd.DataFrame.from_dict(srows, orient="index", columns=["s930", "s16"])

d = gd.join(sd, how="inner")
for col in d.columns:
    d[col] = pd.to_numeric(d[col], errors="coerce")
d = d.dropna(subset=["g16", "s16"])
d["rg"] = np.log(d.g16).diff()
d["rs"] = np.log(d.s16).diff()
d["spr"] = d.rg - d.rs
d["sig20"] = d.spr.rolling(20).std()
d["ev"] = d.spr.shift(1)
d["sig_prior"] = d.sig20.shift(1)
d = d[np.isfinite(d.ev) & np.isfinite(d.sig_prior) & (d.sig_prior > 0)]
cutd = d.index.tolist()[int(len(d) * 0.75)]
# IS-ONLY MASK: sealed rows leave the frame here and never return
d = d[d.index < cutd].copy()
print(f"IS pair sessions: {len(d)} (sealed rows dropped; cut {cutd})")
print("signal availability: complete at prior 16:00 ET close; entry next 09:30 ET - OK")

d["rth_leg"] = (np.log(d.g16) - np.log(d.g930)) - (np.log(d.s16) - np.log(d.s930))
spr_arr = d.spr.values
rth_arr = d.rth_leg.values
ev_arr, sig_arr = d.ev.values, d.sig_prior.values
n = len(d)


def run_cells(event_mask_fn, label):
    out = []
    for k_or_band in ((1.0,), (1.5,)) if label == "sel" else ((0.5,),):
        for H in (1, 3, 5):
            pnls, sigs = [], []
            busy = -1
            for i in range(n):
                if i <= busy or i + H - 1 >= n:
                    continue
                if not event_mask_fn(i, k_or_band[0]):
                    continue
                side = -np.sign(ev_arr[i])
                ret = rth_arr[i] + (spr_arr[i + 1:i + H].sum() if H > 1 else 0.0)
                pnls.append(side * ret * 1e4 - COST_BPS)
                sigs.append(sig_arr[i] * np.sqrt(H))
                busy = i + H - 1
            out.append((k_or_band[0], H, np.array(pnls), np.array(sigs)))
    return out


def stats(p, sig):
    r = p / (sig * 1e4)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_bps=float(p.mean()), gross_bps=float(p.mean() + COST_BPS),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])


sel_cells = run_cells(lambda i, k: abs(ev_arr[i]) >= k * sig_arr[i], "sel")
diag_cells = run_cells(lambda i, _: 0 < abs(ev_arr[i]) < 0.5 * sig_arr[i], "diag")

rows = [dict(k=k, H=H, IS=stats(p, s)) for k, H, p, s in sel_cells]
diag = [dict(band="sub0.5sig", H=H, IS=stats(p, s)) for _, H, p, s in diag_cells]

print("\n=== IS grid (spread bps net of 4bp RT; t on sigma*sqrt(H)-normalized) ===")
print(f"{'k':>10} {'H':>3} | {'n':>4} {'WR':>6} {'PF':>5} {'net bps':>8} {'gross':>7} {'t':>6} {'halves':>12}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{r['k']:>10} {r['H']:>3} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.2f} {a['gross_bps']:>+7.2f} {a['t']:>+6.2f} {str(a['halves']):>12}")
for r in diag:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    print(f"{'sub0.5sig':>10} {r['H']:>3} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_bps']:>+8.2f} {a['gross_bps']:>+7.2f} {a['t']:>+6.2f} {str(a['halves']):>12}  (diagnostic)")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, verdict = None, {}
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2:
        break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("k", "H")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_bps") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner = cand
        verdict["neighbors"] = f"{pos}/{len(nb)}"
        break

check = winner if winner else (max(rows, key=lambda r: r["IS"].get("t") or -99) if rows else None)
if check:
    dg = [r for r in diag if r["H"] == check["H"]]
    if dg and dg[0]["IS"].get("n", 0) >= 10:
        verdict["self_refuted"] = bool((dg[0]["IS"].get("gross_bps") or 9) >= (check["IS"].get("gross_bps") or -9))
    else:
        verdict["self_refuted"] = False

if winner is None or verdict.get("self_refuted"):
    why = "self-refuted (sub-threshold gross matches)" if verdict.get("self_refuted") else "no cell passes n>=120 & t>=2 & neighbors"
    print(f"\nIS VERDICT: FAIL - {why}; family dies at IS.")
    verdict["is_pass"] = False
else:
    print(f"\nSELECTED: k{winner['k']} H{winner['H']} (neighbors {verdict['neighbors']})")
    print("IS VERDICT: PASS - one OOS shot is earned")
    verdict["is_pass"] = True

json.dump(dict(grid=rows, diagnostics=diag,
               winner=({"k": winner["k"], "H": winner["H"], "IS": winner["IS"]} if winner else None),
               verdict=verdict),
          open("results/r53_gsrv_repair_is.json", "w"), indent=1, default=float)
