# waft-data

Live market-data relay (see root `README.md`) plus the trading-strategy research in
`backtest/`.

## backtest/

Five years of XAUUSD research into an Asia-open (09:30 HKT) range-breakout rule, its
gold/AUDUSD correlation filter, position sizing, instrument choice, and an MQL5 EA.
`backtest/README.md` is the index; each round has a generated HTML report under
`backtest/results/`.

Data is not committed — run `backtest/fetch_data.sh` first (~45 MB).

## Research standards for this repo

`backtest/reference/README.md` holds the loop-engineering framework and our assessment of
it. Read it before starting new strategy work. The short version of the house rules:

- Establish data provenance empirically before trusting it — timezone from the data itself,
  prices cross-checked against a second feed and known history.
- Hold out the last 20–30% of data before any searching; never touch it until the gate.
- Judge parameters by the **gradient**, not the peak. A spike is overfitting; a smooth slope
  is a real effect.
- Every filter must hold in **both** halves of an in-sample/out-of-sample split with the same
  sign. Most do not, and that is the expected outcome.
- Correct for multiple testing with a max-statistic randomisation test; quote Bonferroni
  alongside it. Count every test run, including the ones that failed.
- Model costs and slippage explicitly and always run a sensitivity on them — several results
  in this repo are positive gross and negative net.
- Report negative results as prominently as positive ones. Most of this repo is negative
  results, and that is the useful part.
