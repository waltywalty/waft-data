# Reg SHO / flow-class acquisition - 2026-09-04

Executes the STANDING ORDER in `goal_ledger.md` (2026-09-03 data-frontier probe): probe
Equibles; when GetFailsToDeliver / GetShortVolume serve >= 5 years of depth, pull SPY/QQQ/IWM
and the 80-name basket's short volume. **Signal-side acquisition only - no strategy returns,
hit rates or backtests were computed.** Data and per-call raw responses live in
`backtest/data/regsho/` (not committed); `probe.md` there has the call-by-call detail.

Equibles was reachable: 60 calls, zero protocol errors (the 2026-09-03 "missing required
resultType" bug did not recur). Primary sources (cdn.finra.org, sec.gov) are blocked by the
egress proxy (CONNECT 403), so Equibles is the only route.

## Coverage table

| Series | Ticker | Earliest | Latest | Frequency | Rows on disk | Fields |
|---|---|---|---|---|---|---|
| Short volume (FINRA daily) | SPY | 2020-01-02 | 2026-09-03 | daily, every trading day | 1,677 | short_volume, short_exempt_volume, total_volume (FINRA TRF/off-exchange only, not consolidated), short_pct |
| Short volume | QQQ | 2020-01-02 | 2026-09-03 | daily | 1,677 | same |
| Short volume | NVDA (basket pilot) | 2020-01-02 | 2026-09-03 | daily, split-restated | 1,677 | same |
| Short volume | IWM | - | - | **not served** (server maps IWM to AAXJ) | 0 | - |
| Short volume | 79 remaining basket names | 2020-01-02 (per tool) | - | daily | 0 - pending, see below | same |
| Fails-to-deliver (SEC) | SPY | 2026-03-02 | 2026-08-14 | per settlement date with a fail (half-month batches, ~2wk lag) | 107 | quantity (outstanding balance), prior_close, value_usd |
| Fails-to-deliver | QQQ | 2026-03-02 | 2026-08-13 | as above | 107 | same |
| Fails-to-deliver | IWM | - | - | not served (AAXJ mismap; the 5 AAXJ rows the server returned are kept as ftd_IWM-MISMAPPED-TO-AAXJ.csv, not IWM data) | 0 | - |
| Off-exchange ATS/OTC (FINRA) | SPY | 2021-12-06 | 2026-07-27 | weekly, no gaps | 243 | ats_volume, ats_trades, non_ats_otc_volume, non_ats_otc_trades, total_off_exchange_volume |
| Off-exchange | QQQ | 2021-12-06 | 2026-07-27 | weekly | 243 | same |
| Off-exchange | IWM | - | - | not served | 0 | - |
| Insider transactions (Forms 4/5) | AAPL / JPM (depth probe) | 2019-12-27 / 2019-03-01 | 2026-09-01 / 2026-08-11 | transaction-level, filing date | 814 / 1,381 available, not pulled | date, insider, role, type (SEC code), shares, price, value, owned_after, security, ownership, 10b5-1 |
| Insider sentiment score | universe | snapshot | snapshot | trailing-90d leaderboard, no history | - | - |
| Congressional market-wide | - | trailing 365 d max | disclosure-date anchored | no historical anchor | - | - |
| IPO feed (S-1/F-1) | - | 2026-01-05 | 2026-09-03 | pipeline snapshot | 183 available | - |
| ETF profile / holdings | SPY | 2026-06-30 NPORT-P | snapshot | no shares-outstanding or flow history | - | - |

Integrity checks (parse_regsho.py + ad hoc): SPY/QQQ/NVDA share one 1,677-day trading
calendar; weekdays only; short_pct recomputes from short/total within 0.06 pp on all rows;
ATS + non-ATS == total on all off-exchange rows; qty x prior_close == value on all FTD rows;
NVDA volumes are continuous across the 2021-07-20 (4:1) and 2024-06-10 (10:1) splits, i.e.
the server's "restated onto today's split basis" claim holds.

## Which classes have >= 5 years of daily depth

- **Daily short volume: yes** - 6.7 years (2020-01-02 onward). This is the only Reg SHO-family
  class that clears the bar. It supports a **2020+** backtest, not 2005+ or 2010+.
- **Fails-to-deliver: no** - 6 months (2026-03-02 onward). Not backtestable.
- **Off-exchange volume: no** - weekly, 4.7 years.
- **Insider transactions: ~6.7 years** but transaction-level and 2019-12 onward, borderline;
  reachable, not pulled (depth-only by instruction).
- **Congressional aggregate, IPO feed, ETF flows: no** - snapshots or <= 12 months.

## Basket status and the reason it is partial

SPY, QQQ and NVDA are complete. The other 79 basket names (`data/regsho/pending.txt`) are
not pulled. Cause: every GetShortVolume response is returned inline by the harness (never
spilled to disk - the spill threshold is above the 500-row call maximum), so persisting a
response verbatim means re-emitting it; a full ticker is 4 windows / 1,677 rows / ~60 K output
tokens, and 79 tickers ~= 4.7 M output tokens, beyond one session. The server itself never
failed. The weekly routine can drain pending.txt at ~4 calls per ticker with the windows given
in that file; `parse_regsho.py` rebuilds all CSVs from `raw/`.

Failures: IWM (all three series - Equibles resolves it to AAXJ, a different iShares filer;
deterministic, not retried); BRKB unknown to GetShortVolume (BRK.B works). GEV and SNDK will
be short series (spin-offs, ~2024-04 and ~2025-02 starts).

## Implication for the standing order / Round 66

The Round 66 sweep restricted to Reg SHO classes can proceed on **daily short volume for
SPY/QQQ (2020-2026)** and NVDA; the FTD leg (the "forced close-out flow" mechanism named in
the standing order) is **not** available with backtestable depth - 6 months only - so any
close-out-flow claim would have to be built on short-volume proxies, which is a different and
weaker mechanism. The hold-out and in-sample/out-of-sample rules apply from the first look:
nothing in this acquisition looked at prices.
