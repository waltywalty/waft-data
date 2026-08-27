"""Sequential decision boundaries (Wald SPRT) for the forward-test streams.

Replaces the fixed 6-12-month wait with pre-registered sequential boundaries:
each stream's trades update a log-likelihood ratio; crossing the upper bound
PROMOTES (edge confirmed at the stated error rates), crossing the lower bound
KILLS. Between bounds: keep collecting. This is not peeking - SPRT controls
alpha and beta by construction, and the boundaries are frozen here, now,
before any forward trade exists.

Model per stream: trades are Bernoulli wins with the stream's backtest payoff
ratio b (avg win / avg loss) held fixed. H0 = no edge (PF = 1 at that payoff,
i.e. p0 = 1/(1+b)); H1 = the backtest edge (p1 = backtest win rate).
alpha = beta = 0.10. Simplification declared: iid Bernoulli with fixed payoff
is a monitoring approximation; promotion additionally requires the execution-
quality check (entries at 60m closes, stops correct) to pass.

Usage:
  python sprt.py                          # boundaries + expected decision times
  python sprt.py W L W W L ...            # score a single stream's sequence
The monthly routine feeds each journal stream's W/L sequence through this.
"""
import sys
import numpy as np

STREAMS = {
    # name: (p1 = backtest win rate, b = payoff ratio, trades/year, source)
    "XAU":    (0.402, 1.96, 140, "652-trade backtest, PF 1.320"),
    "XAUAUD": (0.402, 1.96, 140, "same signals as XAU (dual-denominator leg)"),
    "MHI":    (0.760, 0.64, 10,  "43-trade watch item, PF 2.02 - boundaries only advisory below n=80"),
    "D7":     (0.802, 0.57, 13,  "253-trade SPX replication (r28), PF 2.30 - watch item 4, frozen 7/200"),
}
ALPHA = BETA = 0.10
A = np.log((1 - BETA) / ALPHA)      # promote when LLR >= A
B = np.log(BETA / (1 - ALPHA))      # kill when LLR <= B


def params(name):
    p1, b, peryr, src = STREAMS[name]
    p0 = 1.0 / (1.0 + b)
    lw = np.log(p1 / p0)            # LLR increment for a win
    ll = np.log((1 - p1) / (1 - p0))
    return p0, p1, lw, ll, peryr, src


def score(name, seq):
    p0, p1, lw, ll, peryr, src = params(name)
    llr = sum(lw if s == "W" else ll for s in seq)
    state = "PROMOTE" if llr >= A else ("KILL" if llr <= B else "continue")
    return llr, state


def expected_n(name, truth, sims=20000, seed=7):
    p0, p1, lw, ll, peryr, _ = params(name)
    p = p1 if truth == "H1" else p0
    rng = np.random.default_rng(seed)
    ns = []
    for _ in range(sims):
        llr, n = 0.0, 0
        while B < llr < A and n < 2000:
            llr += lw if rng.random() < p else ll
            n += 1
        ns.append(n)
    return np.median(ns), np.percentile(ns, 90)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in STREAMS:
        name, seq = sys.argv[1], [s.upper() for s in sys.argv[2:]]
        llr, state = score(name, seq)
        print(f"{name}: n={len(seq)}, LLR {llr:+.2f} (promote >= {A:+.2f}, kill <= {B:+.2f}) -> {state}")
        sys.exit(0)
    print(f"SPRT boundaries (alpha=beta={ALPHA}): promote at LLR >= {A:+.2f}, kill at <= {B:+.2f}\n")
    for name in STREAMS:
        p0, p1, lw, ll, peryr, src = params(name)
        n1, n1_90 = expected_n(name, "H1")
        n0, n0_90 = expected_n(name, "H0")
        print(f"{name} ({src})")
        print(f"  H0 win rate {p0:.3f} vs H1 {p1:.3f}; per trade: win {lw:+.3f}, loss {ll:+.3f}")
        print(f"  if the edge is REAL : median {n1:.0f} trades to promote (p90 {n1_90:.0f}) "
              f"~ {n1/peryr*12:.1f} months at {peryr}/yr")
        print(f"  if the edge is DEAD : median {n0:.0f} trades to kill (p90 {n0_90:.0f}) "
              f"~ {n0/peryr*12:.1f} months")
        print()
