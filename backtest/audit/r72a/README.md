# Round 72A inversion audit - reversed-scoring scripts (2026-09-12)

One script per candidate family (22), written by the audit's scoring agents and copied here
verbatim from the session scratchpad so every reversed number in
`results/r72a_inversion_audit.md` is reproducible. Each script re-uses the original runner's
data-build functions, restricts to the runner's own in-sample cut, flips the registered
direction, subtracts 1x / 1.5x / 2x micro costs, and scores the unconditional control, halves,
the reversed parameter ladder and the reversed placebo. Run from `backtest/`:

    python3 audit/r72a/r72a_<attempt>.py

No script sets `UNSEAL_OK` or passes `--unseal`; none reads sessions after the IS cut.
Rules and result: `reference/goal_ledger.md`, Round 72A. Verdict: 0 of 22 survive the bar.
