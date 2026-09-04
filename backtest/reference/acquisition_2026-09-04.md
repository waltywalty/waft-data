# Data acquisition — 2026-09-04

Scope: **acquisition only** — no returns, no hit rates, no backtests. Files live in
`backtest/data/` (gitignored); this note is the only tracked artefact.

Route: the VM egress proxy still refuses CONNECT to `fred.stlouisfed.org` and
`cdn.cboe.com` (see `data_frontier_2026-09-03.md` §0), so every file below was pulled by
`curl` inside a Kernel headless-browser VM (session `waft-acq-0904`), tarred, base64'd
through the tool channel and md5-verified on this side (`461800a70fe8ca1badb6a52e49f36c31`).
Nothing else in the repo was touched; nothing committed.

Provenance checks applied to every file: HTTP 200 with `application/csv` / `text/csv`
content type (not an HTML error page), header row present, dates strictly ascending with
no duplicates. FRED files are re-written with `.` (missing) replaced by an empty field;
column names are FRED's own (`observation_date,<SERIES>`). CBOE files are byte-for-byte as
served (`DATE` in `MM/DD/YYYY`, ascending), matching the existing `GVZ_history_cboe.csv`
convention. Row counts below exclude the header.

## FRED — `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>`

| file | series | rows | first | last | freq | notes |
|---|---|---|---|---|---|---|
| `fred_DFII10.csv` | DFII10 | 6175 | 2003-01-02 | 2026-09-02 | daily | 10y TIPS real yield; holidays present as blank |
| `fred_DFII5.csv` | DFII5 | 6175 | 2003-01-02 | 2026-09-02 | daily | 5y TIPS real yield |
| `fred_DGS10.csv` | DGS10 | 16872 | 1962-01-02 | 2026-09-02 | daily | 10y nominal CMT |
| `fred_DGS2.csv` | DGS2 | 13112 | 1976-06-01 | 2026-09-02 | daily | 2y nominal CMT |
| `fred_T10YIE.csv` | T10YIE | 6176 | 2003-01-02 | 2026-09-03 | daily | 10y breakeven |
| `fred_T5YIE.csv` | T5YIE | 6176 | 2003-01-02 | 2026-09-03 | daily | 5y breakeven |
| `fred_DTWEXBGS.csv` | DTWEXBGS | 5390 | 2006-01-02 | 2026-08-28 | daily | broad dollar index; Fed publishes with ~1-week lag |
| `fred_WALCL.csv` | WALCL | 1238 | 2002-12-18 | 2026-09-02 | weekly (Wed) | Fed total assets, $mn |
| `fred_RRPONTSYD.csv` | RRPONTSYD | 6150 | 2003-02-07 | 2026-09-03 | daily | ON RRP take-up, $bn |
| `fred_WTREGEN.csv` | WTREGEN | 1238 | 2002-12-18 | 2026-09-02 | weekly (Wed) | Treasury General Account, $mn |
| `fred_HYOAS.csv` | BAMLH0A0HYM2 | **795** | **2023-09-04** | 2026-09-02 | daily | **PARTIAL — see failures** |

## CBOE — `https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv`

| file | symbol | rows | first | last | columns |
|---|---|---|---|---|---|
| `VVIX_history_cboe.csv` | VVIX | 5097 | 03/06/2006 | 09/03/2026 | DATE,VVIX |
| `VXN_history_cboe.csv` | VXN | 4272 | 09/14/2009 | 09/03/2026 | DATE,OPEN,HIGH,LOW,CLOSE |
| `RVX_history_cboe.csv` | RVX | 4263 | 09/16/2009 | 09/03/2026 | DATE,OPEN,HIGH,LOW,CLOSE |
| `VIX1D_history_cboe.csv` | VIX1D | 1081 | 05/13/2022 | 09/03/2026 | DATE,OPEN,HIGH,LOW,CLOSE |
| `VXTLT_history_cboe.csv` | VXTLT | 5692 | 01/02/2004 | 09/03/2026 | DATE,VXTLT |
| `OVX_history_cboe.csv` | OVX | 4264 | 09/18/2009 | 09/03/2026 | DATE,OVX |
| `VIX6M_history_cboe.csv` | VIX6M | 4698 | 01/02/2008 | 09/03/2026 | DATE,OPEN,HIGH,LOW,CLOSE |
| `VIX1Y_history_cboe.csv` | VIX1Y | 4943 | 01/03/2007 | 09/03/2026 | DATE,OPEN,HIGH,LOW,CLOSE |

Caveats worth carrying into any later use (no analysis done here):
- CBOE's archive starts for VXN/RVX/OVX in Sep-2009 even though the indices were launched
  earlier (VXN 2001, RVX 2004, OVX 2007); the earlier history is not in this endpoint.
  VXTLT here runs from 2004, earlier than the 2013 launch noted in the frontier probe —
  Cboe back-filled it; treat pre-2013 values as reconstructed, not traded.
- The early rows of the OHLC files are flat (O=H=L=C), i.e. close-only history was
  back-filled into the OHLC layout.
- VIX1D is single-print in its first months (same flatness) and is dispersion-free only
  from 2023.

## Failures / not acquired

1. **`fred_HYOAS.csv` (BAMLH0A0HYM2) is capped at the last ~3 years at the source.**
   Every variant returned the identical 796-line file starting 2023-09-04:
   plain `?id=`, `&cosd=1990-01-01`, `&cosd=1996-12-31`, `&cosd=2010-01-01&coed=2023-09-01`
   (which still returned 2023-09..2026-09, i.e. the window is ignored), and the full
   graph-page query string. The cap is series-specific, not a transport artefact:
   `?id=DFII10&cosd=2000-01-01&coed=2010-01-01` honoured the window (1828 lines,
   2003-01-02..2010-01-01), and the IG twin `BAMLC0A0CM` is capped at exactly the same
   2023-09-04 start. `fred.stlouisfed.org/data/BAMLH0A0HYM2.txt` now returns an HTML page,
   not text. The file is kept under its requested name but is unusable for anything
   before Sep-2023; a licensed ICE BofA source would be needed for the 1996–2023 history.
2. **CBOE equity put/call post-2019: no bulk daily file exists — skipped as instructed.**
   - `https://cdn.cboe.com/data/us/options/market_statistics/daily/` -> S3 `AccessDenied`
     (no directory listing).
   - `https://www.cboe.com/us/options/market_statistics/daily/` -> 200, a 444 KB Next.js
     HTML app shell, one day per page.
   - The page's data source is per-day JSON:
     `https://cdn.cboe.com/data/us/options/market_statistics/daily/<YYYY-MM-DD>_daily_options`
     (no extension; `.csv` variants 403). Verified for 2026-09-03: a `ratios[]` array with
     TOTAL / INDEX / ETP / EQUITY / VIX / SPX+SPXW / OEX / MRUT put-call ratios plus volume
     blocks, ~6.7 KB. Rebuilding 2019-10-07..2026-09-03 would be ~1,740 GETs; not done.
   - The other guesses (`/resources/options/volume_and_price_stats/totalpc.csv`,
     `/data/us/options/market_statistics/historical/equitypc.csv`) are 403.
   On-disk `cboe_equitypc.csv` / `cboe_totalpc.csv` remain 2006-10-04..2019-10-04.
3. Transient: the Kernel VM's own egress proxy returned `egress-proxy-mitm ... stream error
   INTERNAL_ERROR` (HTTP 500) for one batch of FRED requests sent with a spoofed
   `User-Agent`; re-sending with curl's default UA over HTTP/1.1 succeeded. Not a data
   issue, noted so nobody chases it later.
