
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
