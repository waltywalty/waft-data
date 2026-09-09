
### Publication lag, from the archive's own Last-Modified headers

| File (settlement half-month) | Last-Modified (UTC) | Lag from last settlement date in the file |
|---|---|---|
| cnsfails202301a (Jan 1-15, 2023) | Mon 30 Jan 2023 13:38 | 15 days |
| cnsfails202301b (Jan 16-31, 2023) | Wed 15 Feb 2023 16:15 | 15 days |
| cnsfails202506a (Jun 1-15, 2025) | Mon 30 Jun 2025 12:38 | 15 days |
| cnsfails202506b (Jun 16-30, 2025) | Tue 15 Jul 2025 12:13 | 15 days |
| cnsfails202608a (Aug 1-15, 2026) | Mon 31 Aug 2026 11:54 | 16 days |
| cnsfails201501a/b, 201807a/b | Sat 19 Dec 2020 (site migration re-stamp) | not informative |

Schedule: the first-half file is posted on the last business day of the same month, the
second-half file on the 15th of the following month. A settlement date is therefore public
15 to 30 calendar days later (earliest day of a half-month waits ~30 days, the last day ~15).
For any spec: signal known at the file's posting date = (end of month for days 1-15, the 15th
of the next month for days 16-EOM); entries earlier than that are lookahead. Rule 204
close-outs (T+1 after settlement; T+6 for bona-fide market making) are complete long before
the file is posted, so the buy-in event itself is never tradeable from this feed.

## FINRA daily Reg SHO short volume (CNMS consolidated file), 2019-01-02 .. 2026-09-04

- Source: `cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`, pipe-delimited
  `Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market` with ONE row per symbol
  per day and Market a comma list of reporting facilities (e.g. `B,Q,N`). Filtered in the VM
  to the same 96 symbols. 1,930 sessions; every weekday in the span is either present or one
  of the 75 exchange holidays that returned 403 (the list matches the NYSE calendar exactly,
  including 2025-01-09, the national day of mourning). Three range-boundary days the workers
  skipped (the VM clock is EDT, so a fixed-86400s date stepper slips one day at each DST
  change - a recorded trap) and one timed-out day (2025-05-27) were re-fetched individually.
- Transfer: one gzip (2,506,623 bytes, md5 f5a4ed7372d3940e97a687de75e50bbf) in nine chunks,
  md5-verified; 178,812 rows after the four re-fetched days, 95 symbols.
- Depth: the CDN returns 403 for every date before 2019 (probed 2012, 2015, 2016, 2017,
  2018); the legacy host regsho.finra.org redirects to the catalog page; the FINRA Query API
  dataset `otcMarket/regShoDaily` holds only 2026 partitions (date filters for 2019, 2024 or
  earlier return 204). **2019+ is the reachable depth for daily short volume.**
- Missing symbol: FINRA spells Berkshire class B `BRK/B` (the filter carried BRKB, BRK.B,
  BRK B, BRK-B). Not re-pulled; the SHV basket is 92 names + SPY/QQQ/IWM.
- CROSS-CHECK against the second feed (Equibles GetShortVolume, 2020-01-02..2026-09-03):
  SPY 1,673/1,673 and QQQ 1,673/1,673 dates match EXACTLY on short volume AND total volume.
  NVDA matches on 559 dates (post 2024-06-10) and differs by exactly the cumulative split
  factor before: the PRIMARY file is UNADJUSTED share counts (30,326,520 restated vs 758,163
  raw on 2020-01-02 = 40x = 4:1 x 10:1). So: ratios (short/total) are split-invariant; any
  spec on share counts must apply the split calendar or use ratios / trailing percentiles.
- Format drift in the source: from some date between 2026-01-02 and 2026-04-01 FINRA's own
  file carries FRACTIONAL share volumes (e.g. `214902.130753`); the parser keeps floats.
- Publication lag: next business day (FINRA posts the daily file after the close of T+1's
  processing); state T+1 in any spec.

## What this changes for the parked class

Both reopening conditions of 2026-09-04 are met from primary sources: FTD depth is 14.6
years (IS/OOS at 75/25 = 2012-01..2022-11 / 2022-12..2026-08, with the OOS ending BEFORE the
attempt-44 2025 contraction episode only partially - disclose), and the basket short volume
is persisted for 7.7 years (2019+; its 75/25 split puts the OOS at 2024-11..2026-09, inside
the attempt-48 confound - any SHV spec must address that by construction). IWM is now real
in both series. Registration goes through the proposer -> two adversarial critics -> ledger
path; nothing on the return side has been computed.

## Post-proposal fix (same day): two half-months were missing from the first pull

The proposer's signal-side coverage check found 2019-10a with a single settlement date and
2023-08b with none. Cause: the SEC index links those two files under non-standard names,
`cnsfails201910a_0.zip` and `cnsfails202308b_0.zip` (re-uploads), which the strict
`cnsfails20YYMM[ab].zip` pattern in the first URL harvest excluded; every other half-month
2012-01..2026-08 has a standard name. Both were fetched (HTTP 200; the 2023-08b zip's inner
text file is mislabeled `cnsfails202309a.txt` but holds settlement dates 2023-08-15..31),
filtered, and appended: 1,100 basket rows (411 + 689), md5-verified. FTD is now 199,910 rows,
and every one of the 351 half-months has >= 6 dated rows for each of SPY, QQQ and IWM. The
bootstrap script's pattern now accepts the `_0` suffix.
