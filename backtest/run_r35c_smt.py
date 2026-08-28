"""Round 35c: SMT divergence, the user's refined three-phase spec (frozen in
reference/goal_ledger.md). Event: shared trend -> driver shocks against it
while the target holds flat -> driver eases -> does the target snap harder
than when it had responded normally? Outputs results/r35c_smt.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

N1, KSHOCK, KTRIG, WTRIG = 20, 4, 2, 8
ZSHOCK, ZFLAT, ZRESP = 1.5, 0.5, 1.0


def load_ej(name, scale=1.0):
    df = pd.read_csv(f"data/{name}")
    ts = pd.to_datetime(df.iloc[:, 0]).dt.tz_localize("Europe/Athens", ambiguous="NaT",
                                                      nonexistent="NaT").dt.tz_convert("UTC")
    s = pd.Series(df.close.values / scale, index=ts)
    return s[~s.index.isna()][~s.index.duplicated()].sort_index()


def load_fred(name):
    df = pd.read_csv(f"data/{name}")
    s = pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values,
                  index=pd.to_datetime(df.iloc[:, 0]))
    return s.dropna().sort_index()


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 8 or len(b) < 8:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def halves(x):
    m = len(x) // 2
    return [float(np.sign(np.mean(x[:m]))), float(np.sign(np.mean(x[m:])))] if m > 4 else [np.nan, np.nan]


def scan(T, D, label, out):
    lt, ld = np.log(T), np.log(D)
    rT, rD = lt.diff(), ld.diff()
    rel = np.sign(rT.corr(rD))
    z4T = lt.diff(KSHOCK) / lt.diff(KSHOCK).rolling(250).std()
    z4D = ld.diff(KSHOCK) / ld.diff(KSHOCK).rolling(250).std()
    tr20T = lt.diff(N1).shift(KSHOCK)
    tr20D = ld.diff(N1).shift(KSHOCK)
    d2 = ld.diff(KTRIG)
    n = len(T)
    ev_j, cv_j, ev_s, cv_s = [], [], [], []
    i = 300
    sT, sD = np.sign(tr20T.values), np.sign(tr20D.values)
    z4Tv, z4Dv, d2v = z4T.values, z4D.values, d2.values
    while i < n - 30:
        s = sT[i]
        if s != 0 and s == sD[i] and np.isfinite(z4Dv[i]) and np.sign(z4Dv[i]) == -s and abs(z4Dv[i]) >= ZSHOCK:
            kind = None
            if np.isfinite(z4Tv[i]) and abs(z4Tv[i]) <= ZFLAT:
                kind = "ev"                                # target held flat
            elif np.isfinite(z4Tv[i]) and np.sign(z4Tv[i]) == rel * (-s) and abs(z4Tv[i]) >= ZRESP:
                kind = "cv"                                # target responded normally
            if kind:
                for j in range(i + 1, min(i + 1 + WTRIG, n - 30)):
                    if np.sign(d2v[j]) == s:               # driver eases back
                        (ev_j if kind == "ev" else cv_j).append(j)
                        (ev_s if kind == "ev" else cv_s).append(s)
                        break
                i += KSHOCK
        i += 1
    for h in (8, 24):
        fwd = lt.diff(h).shift(-h).values
        def outc(js, ss):
            # claim: target snaps OPPOSITE its relation-implied shock response
            return [fwd[j] * (rel * s) * 1e4 for j, s in zip(js, ss)
                    if j + h < n and np.isfinite(fwd[j])]
        evv, cvv = np.array(outc(ev_j, ev_s)), np.array(outc(cv_j, cv_s))
        out[f"{label} h{h}"] = dict(
            n_ev=int(len(evv)), n_ctrl=int(len(cvv)),
            ev_bps=float(evv.mean()) if len(evv) else np.nan,
            ctrl_bps=float(cvv.mean()) if len(cvv) else np.nan,
            t=welch(evv, cvv), halves=halves(evv), rel=int(rel))


# ---- intraday frames: gold vs synthetic DXY (EUR+JPY legs) --------------------
g = load_ej("XAUUSD_m15_ejtrader.csv", 100.0)
e = load_ej("EURUSD_m15_ejtrader.csv")
j = load_ej("USDJPY_m15_ejtrader.csv")
if e.median() > 100:
    e = e / 1e5
if j.median() > 1000:
    j = j / 100
idx = g.index.intersection(e.index).intersection(j.index)
g, e, j = g[idx], e[idx], j[idx]
dxy = np.exp((0.809 * (-np.log(e).diff()) + 0.191 * np.log(j).diff()).fillna(0).cumsum())

out = {}
for freq, lbl in (("15min", "XAU/synDXY 15m"), ("1h", "XAU/synDXY 1H"), ("4h", "XAU/synDXY 4H")):
    gt = g.resample(freq).last().dropna()
    dt = dxy.resample(freq).last().reindex(gt.index).dropna()
    gt = gt.reindex(dt.index)
    scan(gt, dt, lbl, out)

# ---- daily frames -------------------------------------------------------------
eur = load_fred("EURUSD_daily_fred.csv")
jpy = load_fred("JPYUSD_daily_fred.csv")
gbp = load_fred("GBPUSD_daily_fred.csv")
cad = load_fred("CADUSD_daily_fred.csv")      # DEXCAUS = USD/CAD already
chf = load_fred("CHFUSD_daily_fred.csv")
common = eur.index.intersection(jpy.index).intersection(gbp.index).intersection(cad.index).intersection(chf.index)
w = {"eur": .576, "jpy": .136, "gbp": .119, "cad": .091, "chf": .036}
tot = sum(w.values())
rdxy = (w["eur"] * (-np.log(eur[common]).diff()) + w["jpy"] * np.log(jpy[common]).diff()
        + w["gbp"] * (-np.log(gbp[common]).diff()) + w["cad"] * np.log(cad[common]).diff()
        + w["chf"] * np.log(chf[common]).diff()) / tot
dxyD = np.exp(rdxy.fillna(0).cumsum())

gd_ej = g.resample("1D").last().dropna()
gd_ej.index = gd_ej.index.tz_localize(None)
col = pd.read_csv("data/XAUUSD_H1_collector.csv")
gc = pd.Series(col.close.values, index=pd.to_datetime(col.datetime, utc=True)).resample("1D").last().dropna()
gc.index = gc.index.tz_localize(None)
goldD = pd.concat([gd_ej[gd_ej.index < "2022-03-01"], gc[gc.index >= "2022-03-01"]]).sort_index()

wti = pd.read_csv("data/WTI_daily_av.csv")
wti = pd.Series(pd.to_numeric(wti.value, errors="coerce").values,
                index=pd.to_datetime(wti.timestamp)).dropna().sort_index()

def align(a, b):
    ix = a.index.intersection(b.index)
    return a[ix], b[ix]

gD, dD = align(goldD, dxyD)
scan(gD, dD, "XAU/synDXY D", out)
eD, cD = align(eur, cad)
scan(eD, cD, "EURUSD/USDCAD D", out)
scan(cD, eD, "USDCAD/EURUSD D", out)
gW, wD = align(goldD, wti)
scan(gW, wD, "XAU/WTI D", out)

json.dump(out, open("results/r35c_smt.json", "w"), indent=1, default=float)
print(f"{'cell':>22} {'rel':>4} {'n_ev':>5} {'n_ct':>5} {'event':>8} {'control':>8} {'t(diff)':>8} {'halves':>14}")
for k, v in out.items():
    print(f"{k:>22} {v['rel']:>4} {v['n_ev']:>5} {v['n_ctrl']:>5} {v['ev_bps']:>+7.1f}b "
          f"{v['ctrl_bps']:>+7.1f}b {v['t']:>+8.2f} {str(v['halves']):>14}")
