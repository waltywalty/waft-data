# Insider-transaction and retail-sentiment acquisition - 2026-09-09 (banked, not proposed on)

Signal-side acquisition only; no returns computed. Both classes were pulled after Round 68
closed and BEFORE the user's redirection to intraday families (same day); they are banked
as data assets and no proposer has been run on them. Data under `backtest/data/insider/`
and `backtest/data/sentiment/` (gitignored).

## SEC insider transactions (Forms 3/4/5 structured datasets)

- Source: `sec.gov/data-research/sec-markets-data/insider-transactions-data-sets`, 82
  quarterly zips 2006q1..2026q2 (`structureddata/.../YYYYqN_form345.zip`, 9-17 MB each),
  fetched from the Kernel VM with a declared User-Agent and filtered IN THE VM to the 102
  issuer CIKs of the 93-name basket incl. predecessor registrants (the same list as the EDGAR
  earnings pull). Kept tables: SUBMISSION (accession, filing date, period, document type,
  issuer CIK/symbol), NONDERIV_TRANS (transaction date, form type, code, timeliness, shares,
  price, acquired/disposed, shares owned after, direct/indirect, security title),
  REPORTINGOWNER (owner CIK, relationship, title). 82/82 quarters, 0 errors; transfer as one
  tarball (8,456,176 bytes, md5 5e72b7fae014c6a6738eb44050879c3b) in 29 chunks, verified.
- Size: 178,648 submissions, 463,570 non-derivative transaction rows, 180,551 owner rows.
  Transaction codes: S 276,479 / M 67,269 (option exercise) / F 44,762 (tax withholding) /
  A 41,098 (grant) / G 13,891 (gift) / C 7,278 / J 4,749 / P 4,566 (open-market purchase) /
  D 2,987. Open-market PURCHASES are rare in mega-caps (4.6k over 20 years) - the classic
  aggregate-insider claim (Seyhun; Lakonishok-Lee 2001; Jiang-Zaman 2010) is documented on
  the whole market and concentrates in small firms; on this basket it would be a sell-side
  (S vs P) object dominated by scheduled 10b5-1 sales. Dates are DD-MON-YYYY strings.
- Not proposed on: the user redirected the program to intraday families the same day. If a
  daily/weekly round reopens, the expected adjacency is the stress-rebound claim (#7/#8/#9:
  insider buying clusters in selloffs) - the attempt-49 D4 construction gate applies.

## AAII Investor Sentiment Survey (weekly)

- Source: `aaii.com/files/surveys/sentiment.xls` (public workbook, 1,314,304 bytes, md5
  370fae13f6e5ce1743ad3a0d3a9b52d2), sheet SENTIMENT: reported date (Thursdays), bullish /
  neutral / bearish shares, 8-week average, bull-bear spread, plus S&P 500 weekly high/low/
  close columns as published (used only as a date-alignment cross-check, never as a return
  source). Parsed with xlrd to `aaii_sentiment.csv`: 2,039 weekly rows 1987-07-24 ..
  2026-09-03, three 14-day gaps (1996-01, 2000-06, 2021-01), spread p5/p50/p95 = -0.25 /
  +0.07 / +0.36.
- NAAIM exposure index page is reachable but its data file is behind a script (not pulled);
  ICI weekly flows returned 403; NYSE market-data page 404.
- Not proposed on (same reason). Documented contrarian claim (Brown-Cliff 2004: weak
  short-horizon predictability) would be a monthly-horizon regime family with the same
  stress adjacency as above.
