# Forward auto-journal contract (frozen 2026-09-02)

Purpose: compute the paper trades of the five tracked streams from data fetched at each
scheduled check-in, so nobody has to journal by hand. Rows go into the Asia Gold Trade
Journal artifact (af9114c9) tagged src="auto". The rules are the FROZEN specs in the
journal footer / goal ledger; this code must reproduce the archived backtest trades on
the archived data before it is trusted forward.

## Inputs (backtest/data/forward/, written by the main session at each check-in)

IBKR price-history JSON exactly as the MCP tool returns it: object with parallel arrays
`time` (ISO-8601 UTC strings, BAR START), `open`, `high`, `low`, `close`, plus metadata
keys (`chart_step`, `source`, ...). Several pulls of the same series may exist; loaders
must concatenate all files matching the glob, sort by time, drop duplicate timestamps.

| glob | series | step | typical span |
|---|---|---|---|
| xauusd_5m_*.json | IBKR CMDTY XAUUSD conid 69067924, midpoint | 5m, outside_rth | one week per file |
| xauusd_daily_*.json | same, daily bars (22:00 UTC bar start) | 1d | 3 months |
| audusd_5m_*.json | IBKR CASH AUD.USD conid 14433401, midpoint | 5m | one week per file |
| audusd_daily_*.json | same, daily (21:15 UTC bar start) | 1d | 3 months |
| spx_daily_*.json / ndx_daily_*.json / rut_daily_*.json | IBKR IND 416904 CBOE / 416843 NASDAQ / 416888 RUSSELL, last, RTH | 1d (13:30 UTC bar start = cash open) | 1 year |
| hk33_m15.csv | re-curl of raw.githubusercontent.com/user1-2-3-4/oanda-data-collector/main/data/indices/HK33_M15.csv (same format as data/HK33_M15.csv; UTC; first bar of day 01:15 UTC) | 15m | full history, live-updated |
| hsi_fut_15m_*.json | IBKR HKFE HSI FRONT-MONTH FUTURE (FUT), FIFTEEN_MINS, outside_rth true, one file per weekly pull, top-level key "contract" (e.g. HSIU6); at a roll the later file's bars win on overlapping timestamps | 15m | one week per file |
| ism_pmi.json | list of {"release": "YYYY-MM-DD", "month": "YYYY-MM", "value": float} maintained by the main session from the ISM press release (via web search) | monthly | all releases since 2026-08 |

Declared substitutions vs the backtests (recorded in the ledger): the XAU corr gate uses
IBKR daily gold (22:00 UTC day boundary) and IBKR AUD.USD daily instead of Athens-day
gold and FRED noon AUD; gold prices are IBKR London Gold midpoint instead of the
backtest's CFD feed; index closes are cash indices (SPX/NDX/RUT) standing in for
MES/MNQ/M2K.

## Output: journal rows

Each leg exposes `rows(data_dir) -> list[dict]` with dict keys
`date` (YYYY-MM-DD, the trade's session date as defined below), `instr` (XAU | XAUAUD |
MHI | D7 | PMI), `side` ("L"|"S"), `entry`, `stop`, `exit` (floats), `note` (short
string), `src` ("auto"). P&L is computed by the page as side*(exit-entry); do NOT
subtract costs in the rows (the monthly review applies the stream's cost model).
Dedup key = (date, instr, note). Legs may also expose `status(data_dir) -> str` for
open positions / regime state used in the monthly report.

## Leg rules (frozen)

XAU: trades.generate(gold5m, L=60, stop_r=2.0, cost=0.30, entry_cutoff_ldn=8) on the
forward 5m frame (engine.load_bars format: UTC index, open/high/low/close/volume),
kept only on days where the 20-day daily log-return correlation gold vs AUDUSD, lagged
one day (deployable.py lines 9-17), is <= 0.5. date = HKT session date; note = reason
("time"|"stop") + "|60m"; stop = entry - side*2*range.
XAUAUD: every XAU trade converted with AUDUSD at t_fill (entry, stop) and t_out (exit):
price_aud = price_usd / audusd; stop_aud = entry_aud * (1 - side*2*range/entry_usd)
(same stop %); note = "half|" + XAU note.
MHI: run_hsi.py H-A fade, frozen cell t0.3_s0.5_c1600: push = 01:15 UTC 15m bar
close-open; ATR14 = mean of prior 14 daily ranges (shift 1); when |push|/ATR14 >= 0.3,
enter at the 01:30 UTC bar open AGAINST the push; stop = pre_hi + 0.5*pre_rng (short)
or pre_lo - 0.5*pre_rng (long), checked on 15m highs/lows through 08:00 UTC; else exit
at the last close before 08:00 UTC. date = HKT date; note = "fade|" + ("stop"|"time").
MHIF: the MHI rule above, unchanged, evaluated on the futures files instead of the CFD
(leg_mhi_fut imports leg_mhi's rule; note = "fade|stop|<contract>" or "fade|time|<contract>").
Added 2026-09-03 after the futures fidelity check: the CFD has no pre-open auction print,
so MHI (CFD) and MHIF (futures) trigger on different sessions; MHIF is the promotion
evidence, MHI continues for comparison.
D7: run_r28b_d7.py d7_trades on SPX daily closes: enter at the close when close > SMA200
and close <= 7-day rolling closing low; exit at the first close >= 7-day rolling closing
high; long only, no stop (stop = entry in the row). Emit a row only when a trade CLOSES
(date = exit date, note = "d7|<bars> bars"); status() reports an open position.
PMI: regime active for sessions strictly after a release with value < 50, until the
first session after a release >= 50. For each calendar month with any active session,
one row per leg (SPX, NDX, RUT): entry = the close of the last session BEFORE the first
active session of that month, exit = close of the last active session of the month,
side L, stop = entry, note = "<leg>|<n> sessions". date = last active session date.
