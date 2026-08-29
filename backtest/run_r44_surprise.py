"""Round 44 attempt 17: macro-surprise post-announcement drift (frozen per
goal_ledger.md). Outputs results/r44_surprise.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")
src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
load_frame = ns["load_frame"]
MICRO = {"SPX": 0.35, "NDX": 1.0, "RTY": 0.35, "GOLD": 0.35}

POS = {"Nonfarm Payrolls", "Gross Domestic Product Annualized", "Retail Sales (MoM)",
       "Retail Sales Control Group", "ISM Manufacturing PMI", "ISM Services PMI",
       "Durable Goods Orders"}
NEG = {"Consumer Price Index (YoY)", "Consumer Price Index (MoM)",
       "Consumer Price Index ex Food & Energy (YoY)",
       "Consumer Price Index ex Food & Energy (MoM)"}

raw = open("data/econ_events_us_high_fxs.json").read()
d = json.loads(raw[raw.find('{'):])
if "result" in d: d = d["result"]
evs = []
for e in d["events"]:
    if e["n"] not in POS and e["n"] not in NEG: continue
    if e["dev"] is None or e["a"] is None or e["c"] is None: continue
    sgn = 1 if e["n"] in POS else -1
    evs.append(dict(t=pd.Timestamp(e["d"]), name=e["n"], dev=float(e["dev"]),
                    cls="growth" if sgn > 0 else "inflation",
                    dir=int(np.sign(e["dev"])) * sgn))
evs = [e for e in evs if e["dir"] != 0]
# collisions: same timestamp -> keep largest |dev|
bytime = {}
for e in evs:
    k = e["t"]
    if k not in bytime or abs(e["dev"]) > abs(bytime[k]["dev"]):
        bytime[k] = e
evs = sorted(bytime.values(), key=lambda e: e["t"])
print(f"usable surprise events: {len(evs)} ({sum(1 for e in evs if e['cls']=='growth')} growth, "
      f"{sum(1 for e in evs if e['cls']=='inflation')} inflation)")

def stats(pnl, atr):
    p, r = np.asarray(pnl, float), np.asarray(pnl, float) / np.asarray(atr, float)
    ok = np.isfinite(r); p, r = p[ok], r[ok]
    if len(p) < 10: return dict(n=int(len(p)))
    w, ls = p[p > 0], p[p <= 0]; m = len(r) // 2
    return dict(n=int(len(p)), wr=float((p > 0).mean()),
                pf=float(w.sum() / abs(ls.sum())) if len(ls) and ls.sum() < 0 else np.inf,
                avg_R=float(r.mean()),
                t=float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else np.nan,
                halves=[float(np.sign(r[:m].mean())), float(np.sign(r[m:].mean()))])

frames, split = {}, {}
for idx in ("SPX", "NDX", "RTY", "GOLD"):
    b = load_frame(idx).tz_convert("UTC")
    atr = (b.groupby("skey").high.max() - b.groupby("skey").low.min()).rolling(20).mean().shift(1)
    keys = sorted(atr.index)
    cutd = keys[int(len(keys) * 0.75)]
    frames[idx] = (b, atr, cutd)
    split[idx] = str(cutd)

def run_cell(th, hold):
    subs = []
    for idx, (b, atr, cutd) in frames.items():
        pnls, atrs, ooss, clss = [], [], [], []
        ix = b.index
        for e in evs:
            if abs(e["dev"]) < th: continue
            i0 = ix.searchsorted(e["t"] + pd.Timedelta(minutes=5))
            if i0 >= len(ix) or (ix[i0] - e["t"]) > pd.Timedelta(hours=2): continue
            skey = b.skey.iloc[i0]
            a20 = atr.get(skey, np.nan)
            if not np.isfinite(a20) or a20 <= 0: continue
            entry = b.close.iloc[i0]
            if hold == "60m":
                i1 = ix.searchsorted(ix[i0] + pd.Timedelta(minutes=60))
                if i1 >= len(ix): continue
                exitpx = b.close.iloc[min(i1, len(ix) - 1)]
            else:
                day = b[b.skey == skey]
                hm = day.index.tz_convert("America/New_York")
                m16 = day[(hm.hour * 100 + hm.minute) < 1600]
                if not len(m16): continue
                exitpx = m16.close.iloc[-1]
            pnls.append(e["dir"] * (exitpx - entry) - MICRO[idx])
            atrs.append(a20); ooss.append(skey >= cutd); clss.append(e["cls"])
        subs.append(pd.DataFrame(dict(pnl=pnls, atr=atrs, oos=ooss, cls=clss, idx=idx)))
    return pd.concat(subs, ignore_index=True)

rows = []
for th in (0.5, 1.0):
    for hold in ("60m", "close"):
        sub = run_cell(th, hold)
        sidx = sub[sub.idx != "GOLD"]
        rows.append(dict(th=th, hold=hold,
                         IS=stats(sidx.pnl[~sidx.oos], sidx.atr[~sidx.oos]),
                         IS_growth=stats(sidx.pnl[~sidx.oos & (sidx.cls == "growth")],
                                         sidx.atr[~sidx.oos & (sidx.cls == "growth")]),
                         IS_infl=stats(sidx.pnl[~sidx.oos & (sidx.cls == "inflation")],
                                       sidx.atr[~sidx.oos & (sidx.cls == "inflation")]),
                         IS_gold=stats(sub[(sub.idx == "GOLD") & ~sub.oos].pnl,
                                       sub[(sub.idx == "GOLD") & ~sub.oos].atr),
                         OOS_sealed=stats(sidx.pnl[sidx.oos], sidx.atr[sidx.oos]), _sub=sub))

print("\n=== IS grid (indices pooled; growth/inflation/gold diagnostics) ===")
print(f"{'th':>4} {'hold':>6} | {'n':>4} {'WR':>6} {'PF':>5} {'avgR':>7} {'t':>6} {'halves':>12} | {'grow':>7} {'infl':>7} {'gold':>7}")
for r in rows:
    a = r["IS"]
    if a.get("n", 0) < 10: continue
    g, f, gd = r["IS_growth"], r["IS_infl"], r["IS_gold"]
    print(f"{r['th']:>4} {r['hold']:>6} | {a['n']:>4} {a['wr']*100:>5.1f}% {a['pf']:>5.2f} "
          f"{a['avg_R']:>+7.3f} {a['t']:>+6.2f} {str(a['halves']):>12} | "
          f"{g.get('avg_R', float('nan')):>+7.3f} {f.get('avg_R', float('nan')):>+7.3f} {gd.get('avg_R', float('nan')):>+7.3f}")

ranked = sorted([r for r in rows if r["IS"].get("n", 0) >= 120],
                key=lambda r: -(r["IS"].get("t") or -99))
winner, npos = None, ""
for cand in ranked:
    if (cand["IS"].get("t") or -9) < 2: break
    nb = [r for r in rows if sum(r[x] == cand[x] for x in ("th", "hold")) == 1
          and r["IS"].get("n", 0) >= 30]
    pos = sum(1 for r in nb if (r["IS"].get("avg_R") or -1) > 0)
    if len(nb) == 0 or pos >= len(nb) / 2:
        winner, npos = cand, f"{pos}/{len(nb)}"
        break

if winner is None:
    print("\nNo cell passes the IS floor; family fails at IS, OOS not opened.")
    json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
                   winner=None, gate_pass=False),
              open("results/r44_surprise.json", "w"), indent=1, default=float)
    raise SystemExit

print(f"\nSELECTED: th{winner['th']} {winner['hold']} (neighbors positive {npos})")
sub = winner["_sub"]
oos = sub[sub.oos & (sub.idx != "GOLD")]
o = stats(oos.pnl, oos.atr)
print(f"\n=== ONE-SHOT OOS (indices pooled, burned now) ===")
print(f"n {o.get('n')} WR {o.get('wr',0)*100:.1f}% PF {o.get('pf',float('nan')):.2f} "
      f"avgR {o.get('avg_R',float('nan')):+.3f} t {o.get('t',float('nan')):+.2f} halves {o.get('halves')}")
per = {}
for idx in frames:
    s = sub[sub.oos & (sub.idx == idx)]
    per[idx] = stats(s.pnl, s.atr); v = per[idx]
    if v.get("n", 0) >= 10:
        tag = " (diagnostic)" if idx == "GOLD" else ""
        print(f"  {idx}: n {v['n']} WR {v['wr']*100:.1f}% PF {v['pf']:.2f} avgR {v['avg_R']:+.3f} t {v['t']:+.2f}{tag}")
c15 = stats(oos.pnl - 0.5 * oos.idx.map(MICRO), oos.atr)
print(f"cost x1.5: avgR {c15.get('avg_R',float('nan')):+.3f} t {c15.get('t',float('nan')):+.2f}")
PASS = (o.get("n", 0) >= 40 and (o.get("avg_R") or -1) > 0 and (o.get("t") or -9) >= 2
        and (o.get("pf") or 0) >= 1.15 and (c15.get("avg_R") or -1) > 0)
print(f"\nOOS GATE: {'PASS' if PASS else 'FAIL'}")
json.dump(dict(split=split, grid=[{x: v for x, v in r.items() if not x.startswith("_")} for r in rows],
               winner={x: winner[x] for x in ("th", "hold", "IS")},
               oos_pooled=o, oos_per_instrument=per, oos_cost15=c15, gate_pass=bool(PASS)),
          open("results/r44_surprise.json", "w"), indent=1, default=float)
