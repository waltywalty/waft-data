# Reference: loop engineering framework

Source: *How Quants Use Loop Engineering to Find Trades That Actually Work (The Full Framework)*,
saved here as `loop-engineering-framework.pdf` (plain text in `.txt`). Retail-facing guide
promoting a Skool community; it says itself that it is a simplified version of what firms do.
That does not make it wrong — the core of it is sound and standard.

## The framework in one screen

**The loop**, repeated 3–5 rounds, capped at 5:

1. **Generate** 10–20 variations of a core idea.
2. **Backtest** each on in-sample data only.
3. **Score** with ICIR. Kill anything below 0.3.
4. **Analyse the failures** — what conditions broke them, what assumptions were wrong.
5. **Select** survivors, feed the failure analysis back into generation as constraints.

Then one **out-of-sample gate** on data held back from the very beginning:
ICIR must hold (a drop of more than 50% means overfit), the decay profile must hold,
and significance must survive a **Bonferroni correction for every strategy tested across
all rounds**.

**Scoring — IC and ICIR.** IC is the correlation between what the signal predicted and what
happened. ICIR = mean(IC) / sd(IC) across periods. Bands: >0.5 strong, 0.3–0.5 moderate,
<0.3 probably noise. The point is consistency: a steady IC of 0.03 beats +0.15 then −0.10.

**Decay — signal half-life.** Autocorrelation of the signal at lags 1/5/10/20/50 days; fit
the decay; estimate the half-life. Reject anything whose half-life is shorter than the
holding period. A signal that dies in 2 days cannot pay for the cost of acting on it.

**Never**: optimise to one magic parameter (real edges work across a *range*); let any
out-of-sample data leak into the loop; run without a round cap; skip the multiple-testing
correction.

## What we adopted, and what it changed

Applied to the XAUUSD Asia-open rule in `../loop_metrics.py`:

| Metric | Result | Verdict |
|---|---|---|
| ICIR (monthly, 58 months) | **+0.340** (mean IC +0.081, 64% of months positive, t = 2.59) | "Moderate" band |
| ICIR of the raw breakout direction alone | **+0.041** | Noise — confirms round one independently |
| Signal half-life | **27 days** against a 0.45-day hold | Passes the ≥5-day rule by ~60× |
| Bonferroni, 18 tests | needs p < 0.00278, we have **p = 0.00586** | **FAILS** |
| Bonferroni, 100+ tests | needs p < 0.00050 | **FAILS** |

Two things worth carrying forward:

1. **The ICIR split is the cleanest confirmation we have** that the edge lives in the
   correlation filter and not in the breakout. 0.340 for the filtered signal against 0.041
   for direction alone, computed a completely different way from the profit factors.
2. **The framework's own gate rejects our strategy.** By its stated Bonferroni rule we do not
   pass at any plausible test count. We used a max-statistic randomisation test instead
   (corrected p = 0.036), which is the correlation-aware analogue and the better tool here
   because our configurations are highly overlapping — Bonferroni assumes independence and
   over-penalises. But the honest summary is: *one reasonable correction passes us, the
   stricter standard one does not.* Size accordingly.

## Where it is thinner than it looks

- **ICIR is a cross-sectional metric.** The textbook version ranks hundreds of assets each
  period and correlates ranks with forward returns. We have one asset and a time series, so
  our IC is a legitimate adaptation but the 0.5/0.3 bands are not calibrated for it. Do not
  treat them as a hard gate.
- **Bonferroni ignores test correlation.** With overlapping configurations it is the wrong
  correction and will reject real edges. Prefer a randomisation/max-statistic test; quote
  Bonferroni alongside it for honesty, not instead of it.
- **The "half-life > 5 days" rule is calibrated for daily-rebalanced factors.** What matters
  is half-life relative to *your* holding period, which is the version we used.
- **It says nothing about the things that killed most of our candidates**: transaction costs,
  execution realism, position sizing and risk of ruin, data validation (timezone
  identification, cross-feed price checks), and instrument granularity. Those are not
  optional extras — costs alone turned several of our positive gross results negative.

## Checklist for the next strategy

- [ ] Hold back the last 20–30% of data before touching anything. Never look at it.
- [ ] Validate the data first: timezone established empirically, prices cross-checked
      against a second feed and against known history.
- [ ] Generate a batch of variants; do not hand-tune one.
- [ ] Score with ICIR *and* profit factor *and* a t-stat. Report all three.
- [ ] Compute the signal half-life; require it to exceed the holding period.
- [ ] Check the parameter *gradient*, not the peak — a spike is overfit, a slope is real.
- [ ] Model costs and slippage explicitly, and run a sensitivity on them.
- [ ] Cap the loop at 5 rounds; count every test you ran.
- [ ] At the gate: max-statistic randomisation, Bonferroni quoted alongside, IS/OS split,
      and a placebo that shuffles the labels while preserving their structure.
- [ ] Then paper trade 4–8 weeks before any real money.
