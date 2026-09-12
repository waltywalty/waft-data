# identity check: registered-direction IS cells from my build must match results JSON IS block
import runpy, numpy as np, pandas as pd, sys, io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_15.py")
frames, MICRO, st = g["frames"], g["MICRO"], g["st"]
for mult, fname in ((None, "any"), (0.5, "0.5sig")):
    for xcol, hname in (("c12", "0930-1200"), ("cEnd", "0930-close")):
        subs = []
        for idx, d in frames.items():
            agree = (np.sign(d.rj) == np.sign(d.rh)) & (np.sign(d.rj) != 0)
            m = agree & np.isfinite(d[xcol])
            if mult: m &= (d.rj.abs() >= 0.5 * d.sj) & (d.rh.abs() >= 0.5 * d.sh)
            side = np.sign(d.rj[m]); pnl = side * (d[xcol][m] - d.o[m]) - MICRO[idx]
            subs.append(pd.DataFrame(dict(pnl=pnl, atr=d.atr20[m])))
        s = pd.concat(subs); a = st(s.pnl, s.atr)
        print(fname, hname, "MY REGISTERED IS: n", a["n"], "avgR %+.4f t %+.2f pf %.2f halves %s" % (a["avgR"], a["t"], a["pf"], a["halves"]))
