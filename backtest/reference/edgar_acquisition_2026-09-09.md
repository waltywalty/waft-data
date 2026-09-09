# Corporate-calendar acquisition (EDGAR earnings-release dates) - 2026-09-09

Signal-side acquisition only; no returns computed. Data under `backtest/data/earnings/`
(gitignored); scripts `backtest/acq/edgar_parse_earnings.py` (local) and the VM script recorded
below.

## Route

Alpha Vantage `EARNINGS` serves reportedDate + reportTime back to 1996, but the free key is
capped at 25 requests/day (rate-limit message recorded by the fetch agent; 3 of 24 names landed:
AAPL, ABT, AMAT - kept as the cross-check feed). The primary source was used instead: EDGAR's
per-registrant submissions index, `https://data.sec.gov/submissions/CIK##########.json` (+ the
older `CIK-submissions-NNN.json` blocks it references), fetched from the Kernel VM with a
declared User-Agent at <= 8 requests/s. Tickers -> CIK via `sec.gov/files/company_tickers.json`
(Berkshire is `BRK-B` there). Kept rows: forms 8-K, 8-K/A, 10-Q, 10-K (+/A, T) with filingDate,
reportDate (fiscal period end), acceptanceDateTime (UTC), Items, accession. 93/93 tickers
resolved; 42,630 rows; plus 2,261 rows from nine PREDECESSOR registrants whose history sits
under a retired CIK (Exxon Mobil Corp 34088 -> ExxonMobil Holdings 2026; BlackRock Inc 1364742
-> 2024 holding company; TWDC Enterprises 1001039 -> Disney 2019; Linde Inc/Praxair 884905;
Google Inc 1288776 for GOOG/GOOGL; Broadcom Ltd 1649338 and Avago 1441634; Eaton Corp 31277).
Transfers gzip+base64, md5-verified (abc5db60..., 6786e4c9...).

## Derived calendar

`earnings_dates.csv`: an earnings release = an 8-K whose Items include 2.02 (Results of
Operations; the item exists since 2003-03). 8,167 releases, 93 tickers, median 91 per name,
2004-10 .. 2026-08; session from the acceptance timestamp in ET: pre-open 3,963 / post-close
3,480 / intraday 724 (intraday acceptances are mostly press releases furnished during the
session or amended filings - treat "intra" as unknown timing).

Cross-check vs Alpha Vantage reportedDate (2004+): AAPL 88/91 exact, ABT 88/91, AMAT 85/91
(86 within a day). Misses: all pre-2004-10 rows (the submissions index carries Items only from
late 2004) and two AMAT quarters furnished under Item 7.01 instead of 2.02. The calendar is
~97% complete for 2005+; any aggregate must use the covered set as its denominator per date.
Genuine late starts (IPO/spin): META 2012, ABBV 2013, TSLA 2010, V 2008, MA 2006, PM 2008,
NOW/PANW 2012, ANET 2014, CRWD/UBER 2019, PLTR 2020, GEV 2024, SNDK 2025, MRVL 2021 (re-
domicile). ORCL/BLK/AVGO start 2006/2006/2009 under the CIKs available.

## VM script (verbatim logic)

For each ticker: GET submissions/CIK{cik}.json; blocks = [filings.recent] + each
filings.files[i].name; keep rows whose form is in the set above; sleep 0.12 s between requests.
Predecessor pass: same, over the fixed (ticker, CIK) list above.
