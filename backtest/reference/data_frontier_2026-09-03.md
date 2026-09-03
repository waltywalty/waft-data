# Data frontier probe — 2026-09-03

Scope: establish which genuinely NEW data classes are reachable from this session right
now, at what depth/resolution/format. **No returns, hit rates or backtests were computed.**
Sample pulls (first/last rows, with the exact call in a `#` header line) are under
`backtest/data/probe/`. Nothing is committed.

Context: Round 64 sweep closed with the on-disk frontier exhausted (ledger tail); Equibles
was already down at the end of attempt 48.

## 0. Network reality of this VM (read first)

Every direct HTTPS host tested is refused at the egress proxy with
`curl: (56) CONNECT tunnel failed, response 403` / agent-proxy `connect_rejected —
gateway answered 403 to CONNECT (policy denial or upstream failure)`:
deribit.com, www.deribit.com, test.deribit.com, history.deribit.com, api.binance.com,
fapi.binance.com, cdn.cboe.com, www.cboe.com, fred.stlouisfed.org, api.stlouisfed.org,
query1.finance.yahoo.com, stooq.com, www.cftc.gov, publicreporting.cftc.gov,
data.nasdaq.com, cdn.alphavantage.co, www.alphavantage.co (and, from the proxy's own log
earlier today, api.finra.org / www.finra.org / cdn.finra.org). **The only data paths that
work are the MCP servers (IBKR, Alpha Vantage) and a Kernel browser.** The on-disk
`BTC_DVOL_deribit.csv` (2021-03-24..2026-08-29 daily) and `BTC_funding_binance.csv`
(2020-01-01..2026-07-31, 8h) were therefore fetched by a non-curl route earlier
(ledger line ~4077); the "Deribit worked before" premise does not hold for curl today.

## 1. Interactive Brokers (MCP) — what worked, exactly

Resolution chain that works: `search_contracts(query=<root>)` -> take the row whose
`symbol` == root and whose sections include FUT -> `underlying_contract_id` ->
`search_futures(underlying_contract_id, include_expired=true)` -> per-expiry
`contract_id` + `exchange` -> `get_price_history(contract_id, security_type="FUT",
exchange=<from ladder>, step, period | step_count, outside_rth=true)`.

Underlying ids resolved: VIX 13455763 (CBOE; sections IND/FUT/FOP/OPT), GC 17340718
(COMEX), ES 11004968 (CME), NQ 11004958 (CME), HSI 1328298 (HKFE; IND/FUT/OPT).

Global quirks observed:
- `period` x `step` above 3500 points is rejected (`"Combination of period and step will
  provide more then allowed 3500 data points"`); use `step_count` (<=3500) instead.
- Daily bars on CME/COMEX/CFE are stamped at the PRIOR calendar day 22:00Z (summer) /
  23:00Z (winter) — the bar labelled `2026-09-02T22:00Z` is trade date 2026-09-03. HKFE
  daily bars are stamped at the T+1 session open (09:15Z = 17:15 HKT, 09:00Z from
  2026-07-20). Map to exchange trade dates explicitly before any join.
- `volume` on ACTIVE CFE VX contracts is 0 for every bar except the last ~6 (front and
  second alike); on EXPIRED contracts it is populated end-to-end. Treat VX volume from
  active pulls as missing, not zero.
- Deferred months carry daily OHLC that are settlement marks (O=H=L=C, volume 0) until
  they become liquid — usable for term structure, but they are settlements, not trades.
- `delayed: 600` on CME/COMEX/CFE (10-min delayed data); HKFE FUT responses carry no
  `delayed` field (served real-time); HKFE cash index is `delayed: 900`.
- Results over ~50 KB are written by the harness to a local tool-results file; parse
  with python rather than reading inline.
- `search_futures(include_expired=true)` only lists contracts expired within roughly the
  last 12 months (oldest listed: VX38U5 2025-09-24, GCU5 2025-09-26, ESU5 2025-09-19,
  NQU5 2025-09-19, HSIU5 2025-09-29). Older contract ids are not discoverable through the
  ladder (not probed: whether `search_contracts("ESZ4")` resolves them).

### 1.1 VIX futures (CFE, root VX)  — REACHABLE, incl. expired

| contract | id | pull | first bar | last bar | n | note |
|---|---|---|---|---|---|---|
| VXU6 front (exp 2026-09-16) | 840544671 | ONE_DAY, ONE_YEAR | 2025-12-21 | 2026-09-02 | 175 | volume 0 except last 6 bars |
| VXV6 second (exp 2026-10-21) | 849243131 | ONE_DAY, ONE_YEAR | 2026-01-25 | 2026-09-02 | 154 | same volume quirk |
| VXQ6 EXPIRED 2026-08-19 | 833649190 | ONE_DAY, ONE_YEAR | 2025-11-23 | 2026-08-18 | 185 | volume populated 1..120k |
| VXM6 EXPIRED 2026-06-17 | 816186011 | ONE_DAY, ONE_YEAR | 2025-09-21 | 2026-06-16 | 186 | volume populated |

Each VX monthly carries ~9 months of daily marks (from listing to expiry). Ladder has 64
entries incl. weeklies (VX##), monthlies VXV5..VXK7. Depth of a stitched front/second
series from IBKR alone: the oldest listed expiry (VXV5, exp 2025-10-22) should start
~Jan-2025 (not pulled) -> ~1.5-1.7 years of daily term structure; nothing older is
addressable. Intraday (15m/1h) on VX not probed.

### 1.2 COMEX gold futures (root GC) — REACHABLE, deep

| contract | id | pull | first bar | last bar | n | note |
|---|---|---|---|---|---|---|
| GCZ6 active Dec-26 | 462941472 | ONE_DAY, FIVE_YEARS | 2021-09-06 | 2026-09-02 | 1269 | full 5y (period cap, not data cap); vol>0 from 2022-01 |
| GCZ5 EXPIRED 2025-12-29 | 397594951 | ONE_DAY, FIVE_YEARS | 2021-09-06 | 2025-12-29 | 1099 | 4.3y; max vol 544k |
| GCM6 EXPIRED 2026-06-26 | 430360630 | ONE_DAY, TWO_YEARS | 2024-09-03 | 2026-06-25 | ~455 | vol ~0 until 2026-04 |
| GCG7 second active (Feb-27) | 765079322 | ONE_DAY, ONE_YEAR | 2025-09-03 | 2026-09-02 | 252 | settlement marks, vol 0-2.3k |

Per-contract daily depth on GC is >= 5 years for the Dec contracts (Dec is listed years
ahead). A front/second/third daily-close term structure is constructible for the whole
5-year window on the Dec/Jun legs; Feb/Apr/Aug/Oct legs are listed ~1-2 years ahead.
Ladder: 46 contracts out to GCM2 (2032). Intraday on GC not probed here (MGCZ6_30m.csv
on disk shows 30m works).

### 1.3 ES / NQ calendar (root ES, NQ) — PARTIALLY reachable

| contract | id | pull | first bar | last bar | n | note |
|---|---|---|---|---|---|---|
| ESZ5 EXPIRED 2025-12-19 | 495512563 | ONE_DAY, FIVE_YEARS | 2021-09-06 | 2025-12-23 | 1097 | vol>0 from 2024-01-17 |
| ESH6 EXPIRED 2026-03-20 | 649180695 | ONE_DAY, FIVE_YEARS | 2023-08-20 | 2026-03-25 | ~650 | front-month vol 1-2M/day from 2025-12 |
| ESH6 EXPIRED | 649180695 | TWO_HOURS, step_count 3400 | 2025-07-10 | 2026-03-20 | 2011 | intraday reaches ~8 months pre-expiry |
| ESZ6 active (not yet front) | 515416632 | ONE_DAY, FIVE_YEARS | 2025-09-03 | 2026-09-02 | 252 | only 1y served despite 5y request |
| NQZ5 EXPIRED 2025-12-19 | 563947738 | ONE_DAY, FIVE_YEARS | 2022-11-13 | 2025-12-23 | ~780 | 3y of marks |

On-disk JSONs (`ES_Z5/H6/M6_2h_ibkr.json`, `ES_U6_1h_ibkr.json`) span 2025-07-07 ->
each contract's expiry (Z5 2025-12-19, H6 2026-03-20, M6 2026-06-18, U6 -> 2026-08-28).
IBKR intraday cannot extend them further back (the 2h pull on ESH6 also starts
2025-07-10); IBKR DAILY can extend each leg back 2.5-4.3 years. Front-vs-next daily
spread is constructible only where BOTH legs are in the ladder: oldest listed front is
ESU5/NQU5 (exp 2025-09-19), so the pairable window is ~mid-2025 -> now (~15 months).
Older pairs need contract ids the ladder does not expose (follow-up: try
`search_contracts("ESZ4")`-style lookups).

### 1.4 HSI futures (HKFE, root HSI) — REACHABLE incl. the 09:15-09:30 HKT pre-open

| contract | id | pull | first bar | last bar | n | note |
|---|---|---|---|---|---|---|
| HSI cash index | 1328298 (IND) | FIFTEEN_MINS, ONE_WEEK, outside_rth | 2026-08-28 01:30Z | 2026-09-03 06:45Z | 112 | first bar 09:30 HKT: NO pre-open; lunch gap 04:00-05:00Z; delayed 900 |
| HSIU6 front (exp 2026-09-29) | 810760513 | FIFTEEN_MINS, ONE_WEEK, outside_rth | 2026-08-27 09:00Z | 2026-09-03 07:00Z | 345 | day session first bar **01:15Z = 09:15 HKT** (vol 4130 on 08-28), last 08:15Z (16:15 HKT); after-hours 09:00Z..18:45Z (17:00-02:45 HKT); real-time |
| HSIU6 front daily | 810760513 | ONE_DAY, FIVE_YEARS | 2025-08-29 | 2026-09-02 | 253 | only 1y served |
| HSIQ6 EXPIRED 2026-08-28 | 878716631 | ONE_DAY, ONE_YEAR | 2026-04-30 | 2026-08-27 | 82 | served (4 months, listing->expiry) |
| HSIZ5 EXPIRED 2025-12-30 | 419696427 | ONE_DAY (ONE_YEAR / TWO_YEARS / step_count 120) | — | — | — | `Error invoking method: An error occurred. Please try again later.` x3 |
| HSIU5 EXPIRED 2025-09-29 | 726172385 | ONE_DAY, ONE_YEAR | — | — | — | same error |

So: the pre-open auction window (09:15-09:30 HKT) exists as a 15m bar on the HKFE
futures and not on the cash index (nor on the on-disk HK33/HK50 CFD 15m files, which are
broker feeds). Depth: HSI monthlies carry ~4 months each; expired contracts older than
~8 months are not served, one expired 6 days ago is. The stitched pre-open series is
therefore reachable for roughly the last 6-12 months only (exact cutoff between
HSIF6 exp 2026-01-29 and HSIZ5 — not probed). 15m x 3500-point cap ~ 45-50 HKFE
sessions per pull (day+night ~ 70 bars/day) -> ~6-8 pulls per contract.

## 2. Alpha Vantage (MCP) — daily macro/commodity series

Key facts: free key = 25 requests/day and 1 request/second; PARALLEL MCP calls trip the
burst limit (6 of the first 9 calls returned the rate-limit error) — serialize, one per
turn. Responses > 32k tokens come back as a preview (`sample_data`, ~3500-3800 rows) +
`data_url` on cdn.alphavantage.co (proxy-blocked) — the server's note says
`return_full_data=true` skips the preview truncation and the harness then saves the whole
CSV to the tool-results file (not verified today; budget). Missing values are `.`.

| series | call | interval options | rows | earliest | latest | notes |
|---|---|---|---|---|---|---|
| TREASURY_YIELD 2year | interval=daily, maturity=2year | daily/weekly/monthly | 13,113 | ~1976-06 (13.1k trading days) | 2026-09-01 (4.39) | NEW on disk (10y exists as UST10Y_daily_av.csv) |
| TREASURY_YIELD 10year | interval=daily, maturity=10year | daily/weekly/monthly | 16,873 | 1962-01-02 | 2026-09-01 (4.79) | also 3month/5year/7year/30year |
| FEDERAL_FUNDS_RATE | interval=daily | daily/weekly/monthly | 26,363 | 1954-07-01 | 2026-09-01 (3.63) | 7-day calendar (weekends carried) |
| CPI | interval=monthly | monthly/semiannual ONLY | 1,363 | 1913-01-01 | 2026-07-01 | 2025-10-01 = `.` (shutdown month) |
| WTI | interval=daily | daily/weekly/monthly | 10,611 | 1986-01-02 | 2026-09-01 | already on disk (WTI_daily_av.csv) |
| BRENT | interval=daily | daily/weekly/monthly | 10,252 | 1987-05-20 | 2026-09-01 (96.02) | NEW; 2026-08-31 = `.` |
| NATURAL_GAS | interval=daily | daily/weekly/monthly | 7,738 | 1997-01-07 | 2026-09-01 (2.9) | NEW; Henry Hub spot |
| COPPER | interval=monthly | monthly/quarterly/annual ONLY | 559 (415 non-missing) | 1992-01 (all `.` 1980-1991) | 2026-07-01 | monthly-average USD/t; NO daily |
| GOLD_SILVER_HISTORY GOLD | symbol=GOLD, interval=daily | daily/weekly/monthly | 5,385 | ~2011-12 (7-day calendar) | 2026-09-02 (4322.67) | includes weekends; SILVER not pulled (SILVER_daily_av.csv on disk) |

Earliest dates for the >3.5k-row series are inferred from row counts (preview shows the
newest ~3.6k rows; e.g. 2y preview bottoms at 2012-02-16) — confirm with a
`return_full_data=true` pull before use.

## 3. Equibles (MCP) — DOWN (protocol mismatch, not transient)

Every call today (`GetMarketStatus`, `SearchEconomicIndicators(query="fed funds")`,
`GetVixHistory(startDate=2026-08-01)`) fails client-side with:

> MCP server "Equibles" returned a malformed result that failed schema validation:
> Invalid result for tools/call: missing required resultType — servers implementing
> protocol revision 2026-07-28 MUST include it (the absent-means-complete bridge applies
> only to earlier-revision servers)

This is the server advertising the 2026-07-28 MCP revision without emitting the required
field — every tool will fail until Equibles ships a fix. Not probed as a consequence:
GetFailsToDeliver (SPY), GetShortVolume (SPY daily), GetInsiderTransactions,
GetMarketWideCongressionalActivity, GetIpoFeed. Note there is no `GetEarningsCalendar`
tool; nearest are `GetEconomicCalendar`, `GetEarningsCallEvent`,
`GetUpcomingInvestorEvents`. Also unavailable until fixed: `GetCftcPositioning`,
`GetShortInterest` (attempt-48 source), `GetPutCallRatios`, `GetOffExchangeVolume`.

## 4. Deribit — UNREACHABLE from the VM (see section 0)

Endpoints attempted (all `CONNECT 403`): `/api/v2/public/get_volatility_index_data`
(resolution 1D, 3600, 60), `/api/v2/public/get_funding_rate_history`,
`/api/v2/public/get_funding_chart_data`, `/api/v2/public/get_historical_volatility`.
For the main session, via a Kernel browser: `get_volatility_index_data` accepts
resolution 1/60/3600/43200/1D with `continuation` paging (DVOL history begins
2021-03-24, matching the on-disk file); `get_funding_rate_history(instrument_name,
start_timestamp, end_timestamp)` returns 8h funding points (BTC-PERPETUAL since
2018-08); `get_historical_volatility(currency)` returns realized vol (hourly, ~1 year);
`get_funding_chart_data(length=8h|24h|1m)` is recent-only. Deribit exposes NO public
historical option-IV term-structure endpoint — a term structure has to be built from
live `get_instruments` + `ticker` snapshots going forward, or bought from an archive.
None of this was verified today.

## 5. CBOE — not opened (proxy-blocked; Kernel browser only)

Additional `cdn.cboe.com/api/global/us_indices/daily_prices/{SYM}_History.csv` symbols
that would add a class not on disk (on disk already: VIX, VIX9D, VIX3M, SKEW, GVZ, COR1M,
COR3M, and the pre-2019-10 equity/total put-call archives):
- **VVIX** — vol-of-vol; daily from 2006-03. Mechanism: hedging-demand/convexity regime,
  distinct from the VIX level and the 9D/3M curve already tried.
- **VIX1D** — 1-day vol; official from 2022-05 (short). Mechanism: 0DTE-era same-day
  risk premium for the MES/MNQ Asia-session families; too short for the IS/OOS rule alone.
- **VXN** — Nasdaq-100 vol from 2001; VXN-VIX spread = NDX-vs-SPX relative fear, ties to
  the NDX-alone sub-cells used in attempts 46-48.
- **RVX** — Russell 2000 vol from 2004; RVX-VIX = small-cap stress (RTY_5m ends 2020-05,
  so limited instrument use).
- **VXTLT** — TLT (20y Treasury) vol, from 2013; rates-vol regime for the auction/FOMC
  families. (Cboe also lists **TYVIX** history to 2020.)
- **VXEEM / VXFXI** — EM and China-ETF vol (VXFXI 2011->2019 discontinued); the only
  CBOE vol gauges with a direct HSI/CNH link for the Asia-open family.
- **OVX** (oil vol, 2007), **VXSLV** (silver vol, 2011) — commodity-vol regime beside GVZ.
- **VIX6M, VIX1Y** — complete the VIX curve beyond 9D/1M/3M.
- **Equity put/call post-2019-10**: the on-disk `cboe_equitypc.csv` ends 2019-10-04 (the
  legacy archive). Post-2019 daily P/C by product lives in Cboe's "market statistics"
  daily CSVs (`cdn.cboe.com/data/us/options/market_statistics/daily/`), a different
  archive; exact filename pattern to confirm in the browser.

## 6. Verdict — new data classes actually reachable now

| source | series | reachable | earliest | latest | resolution | sample rows | notes |
|---|---|---|---|---|---|---|---|
| IBKR | VX front/second (CFE) | yes | ~Sep-2025 (front); ~Jan-2025 est. via oldest listed expiry | 2026-09-02 | daily (intraday unprobed) | 175 / 154 | expired contracts served; ~9 months per contract; volume unusable on active pulls |
| IBKR | VX expired (VXM6, VXQ6) | yes | 2025-09-21 / 2025-11-23 | 2026-06-16 / 2026-08-18 | daily | 186 / 185 | ladder lists only ~12 months of expiries |
| IBKR | GC front/second/third (COMEX) | yes | 2021-09-06 (GCZ5, GCZ6) | 2026-09-02 | daily | 1269 / 1099 / 252 | >= 5y per Dec contract; deferred = settlement marks |
| IBKR | ES front vs next | partial | pairable from ~2025-06; single legs to 2021-09 | 2026-09-02 | daily; 2h from 2025-07 | 1097 / 650 / 2011 | older front ids not in ladder |
| IBKR | NQ front vs next | partial | pairable from ~2025-06; NQZ5 to 2022-11 | 2025-12-23 | daily | ~780 | as ES |
| IBKR | HSI FUT 15m incl. 09:15 pre-open | yes | ~6-12 months (monthlies; >8-month-old expiries error) | 2026-09-03 | 15m, real-time | 345 | cash index has no pre-open bars |
| IBKR | HSI FUT daily | yes | 2025-08-29 | 2026-09-02 | daily | 253 | HKFE daily stamped at T+1 open |
| AV | UST 2y daily | yes | ~1976 | 2026-09-01 | daily | 13,113 | serialize calls; `.` = missing |
| AV | UST 10y daily | yes | 1962-01-02 | 2026-09-01 | daily | 16,873 | on disk already |
| AV | Fed funds effective | yes | 1954-07-01 | 2026-09-01 | daily (7-day) | 26,363 | |
| AV | CPI | yes | 1913-01 | 2026-07 | monthly only | 1,363 | 2025-10 missing |
| AV | Brent | yes | 1987-05-20 | 2026-09-01 | daily | 10,252 | |
| AV | Henry Hub gas | yes | 1997-01-07 | 2026-09-01 | daily | 7,738 | |
| AV | Copper | yes | 1992-01 | 2026-07 | monthly only | 415 | |
| AV | Gold (AV) | yes | ~2011-12 | 2026-09-02 | daily, 7-day calendar | 5,385 | |
| Equibles | all | **no** | — | — | — | — | schema error, every tool |
| Deribit | DVOL / funding / RV | **no (VM)** | — | — | — | — | CONNECT 403; Kernel only |
| CBOE | VVIX/VIX1D/VXN/RVX/VXTLT/VXEEM/OVX/PC | not opened | — | — | daily | — | Kernel only |

Call log (for the test-count discipline; no returns computed): IBKR search_contracts x5,
search_futures x5, get_price_history x20 (4 HKFE errors, 1 point-cap rejection);
Alpha Vantage x15 (6 rate-limited, 9 served); Equibles x3 (3 failed); curl ~25 (all
refused).
