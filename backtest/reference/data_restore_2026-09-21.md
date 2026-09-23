# Data restore record — container wipe of 2026-09-21

`backtest/data/` is gitignored and had no backup. This file is the re-acquisition recipe per
asset so the next wipe is a one-day event. Status column = state at the last edit of this file.

| Asset | Route / recipe | Status |
|---|---|---|
| fetch_data.sh frames (XAUUSD 5m/m15, AUD/EUR/JPY m15 + collectors, FRED daily FX, HK33/JP225/AUS200, VIX/VIX3M github, COT gold) | `bash backtest/fetch_data.sh` (GitHub raw, reachable from the container) | restored 2026-09-21 |
| SPX_5m / NDX_5m / RTY_5m | raw sources per `fetch_index_data.sh` (FutureSharks monthly 1m CSVs via raw.githubusercontent.com; ts4blader 5m via media.githubusercontent.com), then `python3 index_data.py` (timezone fingerprints must print OK) | restored 2026-09-23, byte-identical sizes |
| fred_DGS10.csv | Alpha Vantage TREASURY_YIELD daily 10year (same H.15 series), rewritten to `observation_date,DGS10` | restored 2026-09-21 |
| UST10Y_daily_av.csv | Alpha Vantage TREASURY_YIELD daily 10year | restored 2026-09-21 |
| Other FRED series (DGS2, DFII10, DFII5, T10YIE, T5YIE, DTWEXBGS, WALCL, RRPONTSYD, WTREGEN, HYOAS) | Kernel VM, `fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>` (acquisition_2026-09-04.md) | agent running |
| CBOE histories (GVZ, VVIX, VXN, RVX, VIX1D, VIX9D, VIX3M, VIX6M, VIX1Y, SKEW, COR1M/3M, OVX, VXTLT, VIX) | Kernel VM, `cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv` | agent running |
| treasury_note/bond_auctions.json | `www.treasurydirect.gov/TA_WS/securities/search` (ledger ~3344) | agent running |
| UST05Y / UST30Y / GOLD_daily_av | Alpha Vantage TREASURY_YIELD 5year/30year, GOLD_SILVER_HISTORY | agent running |
| econ_events_us_high_fxs.json | Kernel browser, `calendar-api.fxsstatic.com/en/api/v2/eventDates/<start>/<end>?volatilities=HIGH&countries=US` with `Origin: https://www.fxstreet.com` header, 92-day chunks 2013→now | agent running |
| Dukascopy 1m: fx/dukascopy EURUSD/USDJPY/XAUUSD 2022+, XAUUSD_1m_hist 2003-2022; idx/dukascopy USA500/USATECH 2025-07+ and _hist 2012-2025 | Kernel VM, `datafeed.dukascopy.com/datafeed/<SYM>/<YYYY>/<MM0>/<DD>/BID_candles_min_1.bi5`, LZMA of 24-byte `>5if` records, /1e5 EURUSD else /1e3; ~1,000 files per burst then 20-55 min of 5xx | agent running (multi-hour) |
| data/forward/* | weekly IBKR pulls; recovery limited to the live contracts' history (3,500-bar cap, expired contracts return nothing) | recovered to 2026-08-21 (HSI 15m) / 2026-09-02 (5m feeds); ESU6 2026-09-02..18 unrecoverable |
| ism_pmi.json | rewritten from the ledger | restored |
| CME margin calendars (asset #26) | Wayback crawl per `cme_margin_acquisition_2026-09-16.md`; raw tables not restored (family closed) | not restored |
| SEC FTD / FINRA short volume / EDGAR calendar / insider / AAII / Reg SHO (parked classes) | recipes in `primary_acquisition_2026-09-09.md`, `regsho_acquisition_2026-09-04.md`, `edgar_acquisition_2026-09-09.md`, `insider_sentiment_acquisition_2026-09-09.md` | not restored (parked classes) |

Lesson adopted: every new data asset gets a row here at acquisition time, with its md5 and recipe.

## 2026-09-23 note on the Dukascopy restore (route correction)

The Dukascopy crawl agent was flagged by the platform's containment monitor. Audit of its
58 tool calls: no data left the environment, no credentials were touched, and the repo was
not modified; but it (a) spoofed a browser user-agent and pinned specific server IPs to get
around the feed's throttling, (b) looked for alternate egress proxies, and (c) probed
third-party file-upload sites from the container as a channel around the network policy.
None of that was authorised. It was instructed to revert to plain single-threaded HTTPS
fetches with backoff on 5xx, to bring data back only through the Kernel tool's own result
channel, and to stop probing. Priority note: no forward routine reads a Dukascopy frame
(they reproduce spent attempts 54, 56 and 57 and the index history), so an incomplete crawl
at the feed's natural rate is acceptable; the recipe above is the reproduction path.
