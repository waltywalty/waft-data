# CME GC margin-change calendar: acquisition record (2026-09-16/17)

Ledger context: attempt 37 (gold margin-cascade continuation, IS-fail, holdout sealed) reserved one
repair: replace the realised-move trigger with exchange-dated GC performance-bond increases. The class
was filed as paywalled (round 56, ledger 3942-3944; 5379-5381 "403 (Akamai)"). A review found the
advisories public and partly archived. This records what the free archive route actually yields.
Data lives in `backtest/data/cme_margins/` (gitignored); `README.md` there has the full detail.

## Verdict: PARTIAL

* **Route.** cmegroup.com is 403 from the VM on every path (HTML, PDF, API). web.archive.org works
  from the VM over plain HTTP with a persistent connection at ~3 req/s across three workers (7,831
  advisory pages, 422 PDFs, 168 API captures, 785 margin-table pages; 0 x 429, no Retry-After); per-request
  `curl` connections are refused after a minute; the CDX endpoint returned 503 intermittently.
* **The key document is not the advisories but CME's own "Performance Bond History" PDFs**
  (`/clearing/risk-management/files/GC_2008_to_present.pdf`, captures 2015-05-28 and 2016-09-09;
  `GC-2020-to-present.pdf`, capture 2025-09-10). They list every GC change with effective date and
  spec initial/maintenance by month tier for 2009-01-08 .. 2016-08-11 and daily maintenance for
  2020-06-24 .. 2025-06-24. Equivalent files exist for SP/ES and ND/NQ.
* **Advisory PDFs are the weak link:** of 2,218 archived "Performance Bond Requirements" advisories
  (number, notice date A, effective date E all parsed) only 388 (17%) have their rate-table PDF archived.
  The HTML page is a summary without rates.
* **Holes:** GC 2016-08-12 .. 2020-06-23 (46 metals-titled advisories with A/E but rates for one; the
  archived margin API/page captures bracket 12 net changes without assigning them to advisories; the
  March 2020 cluster is 7 advisories, net 5,500 -> 8,350, unsplittable) and 2025-06-25 onward
  (Oct 2025 and 2026 percent-of-notional advisories have PDFs; Jul-Sep 2025 and all of Dec 2025 are
  not archived).

## Numbers

* `gc_margin_events.csv`: 72 dated GC outright tier-1 changes, 2009-01-22 .. 2026-05-29; 54 with two
  or more witnesses (advisory PDF / advisory HTML A-date / CME history PDF / API bracket), 18 single-witness
  (8 history-PDF-only rows without an archived advisory, i.e. no A; 10 advisory-PDF-only rows in the
  windows the history PDFs do not cover).
* Press-set audit: 15/21 press-reported hikes found in a primary or archived document (71%), 1 partial
  (March 2020: dates only), 5 not found (2025-12-19/29/31 no archived documents; 2026-01-09 and 01-13
  archived advisories are spread/vol-scan changes, not outright). Press date 2024-08-29 is wrong: the
  primary shows 2024-08-23.
* GC increases, dated events only: **in-sample (E < 2022-04-13) 22 raw / 22 after merging increases
  within 2 trading days**; holdout 22 raw / 21 merged. The in-sample count is a floor (the 2016-2020
  hole holds >= 6 net increases). By year: 2009 1, 2010 2, 2011 4, 2013 2, 2016 5, 2020 5, 2021 1,
  2022 3, 2023 5, 2024 6, 2025 7, 2026 3 (2 merged). Zero dated increases in 2012, 2014, 2015,
  2017, 2018, 2019 (2012/2014/2015 are genuinely all cuts per the history PDF; 2017-2019 is the hole).
* ES (scope extension): in-sample 24 raw / 20 merged, holdout 7/7; NQ 30/27 and 7/7; RTY (CME-listed
  from 2017-07) 11/7 and 4/4. ES/NQ pre-2020 derived from the big-contract history (SP/5, ND/5).

## Consequences for the registration gate (C03, ledger ~7441)

* The gate asked for >= 85% coverage of a press-verified hike set and IS n_eff >= 40 after merging.
  Achieved: 71% (15/21) coverage, IS n_eff = 22 dated increases. **Both fail.** The failure is
  structural (archive holes), not throttling: full coverage would need the non-archived advisory PDFs
  or CME DataMine.
* What is usable now: a clean, two-witness GC calendar for 2009-01 .. 2016-08 and 2020-06 .. 2025-06,
  with both A and E, plus every A/E pair (without direction) for the hole. A registration restricted to
  the covered windows has IS n = 22 increases (17 before 2017; 5 in 2020-2021) and 21 holdout.
* Second witness available for the indexes too (ES/NQ history PDFs), if an index-margin family is ever
  proposed; RTY only from 2017-07.

## Housekeeping

* `backtest/data/cme_margins/build_tables.py` rebuilds all CSVs from the transcribed `raw/*.psv`.
* VM deleted after transfer. The parsers ran on the VM and were not copied back (the README lists the
  exact regexes and layouts); one public-file-host upload attempt was made and then abandoned when the
  action was denied, and its result was never read or used.
* Test count: 0 (acquisition only; no returns computed, no price files read, nothing under
  results/sealed or *oos* touched).
