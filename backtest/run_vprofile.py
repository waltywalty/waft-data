"""Round 11-D: volume-profile value-area reversion with absorption confirmation.

The user's spec, made mechanical (long side; shorts mirrored at the VAH):

  profile  : volume histogram over a completed window (variants: prior RTH
             session, overnight 16:00->09:30, prior 24h), 40 price bins,
             volume placed at each bar's typical price. POC = modal bin;
             value area = smallest POC-centred bin set holding 70% of volume.
  breakdown: first 15-minute block (anchored 09:30 ET) closing below the VAL.
  absorption (the "no one is really selling" test, on/off variant):
             the breakdown block's volume must be BELOW the previous block's -
             declining volume into the break.
  reclaim  : a later 15m block closing back inside the value area on GROWING
             volume - block volume above the breakdown block's (on/off).
  entry    : at the reclaim close. stop: the extreme low made below the VAL.
  targets  : POC, the opposite value-area edge, or EoD hold. Flat at 16:00.

One trade per day, first side to trigger. Tick-volume caveat: CFD volume is
tick count, not contract volume - stated wherever volume gates a decision.
"""
import pandas as pd, numpy as np, warnings, json
import mkts
warnings.filterwarnings("ignore")

OUT = {"cells": []}
NBINS = 40


def value_area(M, j0, j1):
    if j1 - j0 < 20:
        return None
    tp = (M.h[j0:j1] + M.l[j0:j1] + M.c[j0:j1]) / 3
    v = M.v[j0:j1]
    lo, hi = tp.min(), tp.max()
    if hi <= lo or v.sum() <= 0:
        return None
    edges = np.linspace(lo, hi, NBINS + 1)
    idx = np.clip(np.digitize(tp, edges) - 1, 0, NBINS - 1)
    hist = np.bincount(idx, weights=v, minlength=NBINS)
    poc = int(np.argmax(hist))
    total = hist.sum()
    covered = hist[poc]
    a = b = poc
    while covered < 0.70 * total:
        up = hist[b + 1] if b + 1 < NBINS else -1
        dn = hist[a - 1] if a - 1 >= 0 else -1
        if up >= dn:
            b += 1
            covered += max(up, 0)
        else:
            a -= 1
            covered += max(dn, 0)
        if a == 0 and b == NBINS - 1:
            break
    ctr = (edges[:-1] + edges[1:]) / 2
    return dict(poc=float(ctr[poc]), val=float(edges[a]), vah=float(edges[b + 1]))


def day_windows(M, day):
    rth0, rth1 = M.nyt(day, 9, 30), M.nyt(day, 16)
    prev = day - pd.Timedelta(days=1)
    # walk back to the previous day that actually has RTH bars (weekends)
    for _ in range(4):
        p0, p1 = M.nyt(prev, 9, 30), M.nyt(prev, 16)
        if M.ix.searchsorted(p1) - M.ix.searchsorted(p0) >= 40:
            break
        prev -= pd.Timedelta(days=1)
    return {"prior_rth": (M.nyt(prev, 9, 30), M.nyt(prev, 16)),
            "overnight": (M.nyt(prev, 16), rth0),
            "prior_24h": (M.nyt(prev, 9, 30), rth0)}, rth0, rth1


def vp_day(M, day, window, need_absorb, need_grow, target):
    wins, rth0, rth1 = day_windows(M, day)
    w0, w1 = wins[window]
    j0, j1 = M.rng(w0, w1)
    va = value_area(M, j0, j1)
    if va is None:
        return None
    s0, s1 = M.rng(rth0, rth1)
    if s1 - s0 < 40:
        return None
    # 15m blocks anchored on the open
    blocks = []
    for b in range(s0, s1 - 2, 3):
        b1 = min(b + 3, s1)
        blocks.append(dict(j0=b, j1=b1, c=float(M.c[b1 - 1]),
                           lo=float(M.l[b:b1].min()), hi=float(M.h[b:b1].max()),
                           v=float(M.v[b:b1].sum())))
    state, side, kb = 0, 0, None
    for i, bl in enumerate(blocks):
        if state == 0:
            if bl["c"] < va["val"]:
                side, kb, state = 1, i, 1                # breakdown -> look for long
            elif bl["c"] > va["vah"]:
                side, kb, state = -1, i, 1
            if state == 1 and need_absorb and i > 0 and bl["v"] >= blocks[i - 1]["v"]:
                state, side = 0, 0                       # volume not declining: no setup
            continue
        if state == 1:
            inside = va["val"] <= bl["c"] <= va["vah"]
            if inside:
                if need_grow and bl["v"] <= blocks[kb]["v"]:
                    continue                             # wait for a growing-volume reclaim
                entry = bl["c"]
                ext = min(b2["lo"] for b2 in blocks[kb:i + 1]) if side == 1 \
                    else max(b2["hi"] for b2 in blocks[kb:i + 1])
                if side * (entry - ext) <= 0.0003 * entry:
                    return None
                tgt = None
                if target == "poc":
                    tgt = va["poc"]
                elif target == "va_opp":
                    tgt = va["vah"] if side == 1 else va["val"]
                if tgt is not None and side * (tgt - entry) <= 0:
                    return None
                jf = bl["j1"]
                px, why, _ = mkts.hit(M, jf, s1, side, ext, tgt)
                if px is None:
                    px = float(M.c[s1 - 1])
                    why = "time"
                return dict(day=day, side=side, entry=entry, why=why,
                            pnl=side * (px - entry) - M.cost)
            # gave up: opposite VA edge broken while waiting -> dead setup
            if (side == 1 and bl["c"] < va["val"] - 2 * (va["vah"] - va["val"])) or \
               (side == -1 and bl["c"] > va["vah"] + 2 * (va["vah"] - va["val"])):
                return None
    return None


for M in mkts.load_mkts():
    print(f"\n================ {M.name} ================")
    for window in ("prior_rth", "overnight", "prior_24h"):
        for absorb, grow, vl in ((False, False, "no volume gates"),
                                 (True, True, "absorb+grow gates")):
            for target in ("poc", "va_opp", "eod"):
                rows = []
                for d in M.days:
                    tr = vp_day(M, pd.Timestamp(d), window, absorb, grow, target)
                    if tr:
                        rows.append(tr)
                mkts.show(M, f"{window} / {vl} / target {target}",
                          rows, OUT["cells"], f"vp_{window}")

print("\n=== HONEST OOS across all cells ===")
sc = pd.DataFrame([c for c in OUT["cells"] if np.isfinite(c.get("os_pf", np.nan)) and c["is_n"] > 40])
if len(sc):
    top = sc.sort_values("is_t", ascending=False).head(8)
    for _, r in top.iterrows():
        print(f"   {r['mkt']} {r['label']:52s} IS PF={r['is_pf']:.3f} t={r['is_t']:+.2f} | OS PF={r['os_pf']:.3f}")
    print(f"   top-8 median OS PF {top.os_pf.median():.3f}; population ({len(sc)}) {sc.os_pf.median():.3f}")
    OUT["isos"] = {"top8": top.to_dict("records"), "honest_median": float(top.os_pf.median()),
                   "population_median": float(sc.os_pf.median()), "n_cells": int(len(sc))}
json.dump(OUT, open("results/vprofile.json", "w"), indent=1, default=str)
print(f"\n{len(OUT['cells'])} cells. written: results/vprofile.json")
