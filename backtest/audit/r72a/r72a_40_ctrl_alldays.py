import runpy, numpy as np, pandas as pd, sys, io
from scipy import stats as st
buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
g = runpy.run_path("/tmp/claude-0/-home-user-waft-data/879e730b-d453-5229-8ba4-0dc113b1f3e1/scratchpad/r72a/r72a_40.py")
sys.stdout = old
c, kpos, sig63, IS_DAYS, R, run = g["c"], g["kpos"], g["sig63"], g["IS_DAYS"], g["R"], g["run"]
rows = []
for k in IS_DAYS:
    i = kpos[k]
    if i + 1 >= len(c): continue
    s = sig63.iloc[i]
    if not np.isfinite(s) or s <= 0: continue
    rows.append((k, np.log(c.iloc[i+1]/c.iloc[i])*1e4, s))
dfa = pd.DataFrame(rows, columns=["date","gross","sig"])
ra = R(dfa, 1, 1.0); rc = R(run(0.9, 1.01, +1, 1), 1, 1.0)
print(f"CTRL always-long/1d ALL IS days: n {len(ra)} avgR {ra.mean():+.4f} ({(dfa.gross-5).mean():+.1f}bps) t {ra.mean()/ra.std(ddof=1)*np.sqrt(len(ra)):+.2f}")
tW, p = st.ttest_ind(rc, ra, equal_var=False)
print(f"reversed hi_long/1d - all-days ctrl: diff {rc.mean()-ra.mean():+.4f}, Welch t {tW:+.2f}")
