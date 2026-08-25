# TradingView port of the Asia gold strategy

Two Pine v6 scripts, ported from the verified MT5 EA (`../mt5/AsiaOpenGold.mq5`):

| File | Type | Purpose |
|---|---|---|
| `AsiaOpenGold_indicator.pine` | indicator | Signals + status card + alerts, for **manual** execution through TradingView's native IBKR panel |
| `AsiaOpenGold_strategy.pine` | strategy | The full rule for the Strategy Tester, with webhook-ready JSON `alert_message`s for **automated** execution through a bridge |

Chart: XAUUSD (OANDA/your feed) or `MGC1!`, **5-minute timeframe** (other
timeframes shift the 60-minute block boundaries). AUDUSD symbol input must
match a feed whose daily bars close at 17:00 ET (OANDA's do).

## The three operating modes — and what IBKR actually supports

**TradingView's native IBKR connection is manual-only.** The broker panel
(live since 2022) places one-click orders you initiate; it does **not** route
Pine strategy orders or alerts. So "connecting IBKR and giving trading rights"
enables mode 1, not mode 3:

1. **Manual (works today, no extra services)** — run the indicator; when it
   fires (entries land 10:30–15:00 HKT), place the order through the IBKR
   panel with the stop from the status card, and attach a time-conditioned
   exit at 16:00 ET (IBKR order conditions support time) or answer the EXIT
   alert. One action per trading day.
2. **Semi-automated** — same, but with TradingView alerts (paid plan) pushed
   to your phone so nothing needs watching.
3. **Fully automated** — the strategy's `alert_message` JSON goes out via
   webhook (Pro plan or higher) to a bridge that talks to IBKR: a hosted
   service (TradersPost, PickMyTrade) or a self-hosted script against IB
   Gateway. The bridge is a new failure link (alert delivery, bridge uptime,
   gateway sessions) and usually a subscription; it is what "automation on
   TradingView" actually means.

## Instrument note

Through IBKR the natural instrument is **MGC** (micro gold futures, $10/pt) —
which brings back the account-size bar from rounds 4/11: roughly **$20–25k**
before 1%-risk sizing supports even one contract (a 2×-range stop is ~$100–200
of risk per contract). IBKR spot gold (XAUUSD) exists only for eligible
non-US clients. Below the size bar, the MT5/CFD route remains the one that
fits the risk plan.

## Before trusting it: reconciliation (house rule)

Pine was not compilable in the research environment — expect possibly a
trivial fix on first paste into the Pine editor. Then, before any live/demo
use:

1. Run the **strategy** on OANDA XAUUSD 5m over 2023–2025, filter ON,
   fixed qty 1.
2. Export the trade list and compare against the research set
   (`../results/trades_deployable.pkl`): same days, same directions, entries
   within feed-difference tolerance (~$0.5). TradingView's feed differs from
   the research CSV, so small P&L differences are expected; different *trades*
   are not.
3. Check the skip-share: the filter should stand aside ~40% of days. Far off
   → the AUDUSD feed or the daily-close alignment is wrong.
4. Watch one week of live bars: signals must appear only on closed 60-minute
   blocks and never repaint (the correlation uses `close[1]` of completed
   daily bars — the standard non-repaint idiom — but verify on your feed).

## What the port does NOT change

The rule, the filter, the exit, the sizing posture, and the forward-test
protocol are identical to the playbook. The v2 forward log (checkpoint
prices) is an MT5-EA feature; in TradingView modes the equivalent record is
your alert log + broker statements, or the bridge's logs in mode 3.
