"""Round 43: TRUE ES vs CFD feed - euro-open window cross-validation (frozen
per goal_ledger.md). Window = 06:00->08:00 UTC (inside 01:00-04:00 ET year-
round). Outputs results/r43_esxfeed.json."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings("ignore")

FRONT = {"ES_Z5_2h_ibkr.json": ("2025-09-19", "2025-12-19"),
         "ES_H6_2h_ibkr.json": ("2025-12-19", "2026-03-20"),
         "ES_M6_2h_ibkr.json": ("2026-03-20", "2026-06-18"),
         "ES_U6_1h_ibkr.json": ("2026-06-18", "2026-12-31")}

es_win = {}
for fn, (a, z) in FRONT.items():
    d = json.load(open(f"data/{fn}"))
    t = pd.to_datetime(d["time"])
    df = pd.DataFrame(dict(t=t, o=d["open"], c=d["close"], v=d["volume"]))
    df = df[(df.t >= a) & (df.t < z) & (df.v > 0)]
    step_h = d["chart_step"] // 3600
    for _, r in df.iterrows():
        if r.t.hour == 6:
            # 2h bar 06-08 covers the window directly; 1h needs the 07:00 close
            if step_h == 2:
                es_win.setdefault(r.t.date(), [r.o, r.c])
            else:
                es_win.setdefault(r.t.date(), [r.o, None])
        elif step_h == 1 and r.t.hour == 7 and r.t.date() in es_win:
            es_win[r.t.date()][1] = r.c
es = pd.Series({k: (v[1] / v[0] - 1) * 1e4 for k, v in es_win.items()
                if v[1] is not None and v[0] > 0}).sort_index()

src = open("run_r37_scalps.py").read().split('if __name__ != "__main__"')[0]
ns = {}
exec(src, ns)
b = ns["load_frame"]("SPX").tz_convert("UTC")
hm = b.index.hour
cf = {}
for day, g in b.groupby(b.index.date):
    h = g.index.hour
    m = (h >= 6) & (h < 8)
    if m.sum() >= 12:                       # 5m bars: expect 24
        cf[day] = (g.close.values[len(m) - 1 - np.argmax(m[::-1])] /
                   g.open.values[np.argmax(m)] - 1) * 1e4
cfd = pd.Series(cf).sort_index()

common = es.index.intersection(cfd.index)
a, bb = es[common].astype(float), cfd[common].astype(float)
diff = a - bb
out = dict(n=int(len(common)),
           es_mean_bps=float(a.mean()), cfd_mean_bps=float(bb.mean()),
           corr=float(np.corrcoef(a, bb)[0, 1]),
           mean_diff_bps=float(diff.mean()),
           t_diff=float(diff.mean() / diff.std() * np.sqrt(len(diff))),
           es_t=float(a.mean() / a.std() * np.sqrt(len(a))),
           cfd_t=float(bb.mean() / bb.std() * np.sqrt(len(bb))))
json.dump(out, open("results/r43_esxfeed.json", "w"), indent=1)
print(f"common sessions: {out['n']}  ({common.min()} .. {common.max()})")
print(f"euro-open window (06-08 UTC) mean:  TRUE ES {out['es_mean_bps']:+.2f}bps (t {out['es_t']:+.2f})   "
      f"CFD {out['cfd_mean_bps']:+.2f}bps (t {out['cfd_t']:+.2f})")
print(f"daily correlation: {out['corr']:.3f}   mean difference ES-CFD: {out['mean_diff_bps']:+.2f}bps (t {out['t_diff']:+.2f})")
