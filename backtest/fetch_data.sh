#!/usr/bin/env bash
# Re-download the price data (kept out of git — ~35 MB).
#   XAUUSD_5m.csv          5-minute spot gold, 2020-08-21..2025-08-01, UTC timestamps
#   XAUUSD_m15_ejtrader.csv 15-minute spot gold from an independent feed, used only to
#                           cross-validate prices and confirm the timezone
set -euo pipefail
cd "$(dirname "$0")/data"
curl -fL --retry 3 -o XAUUSD_5m.csv \
  https://raw.githubusercontent.com/ilahuerta-IA/backtrader-pullback-window-xauusd/main/data/XAUUSD_5m_5Yea.csv
curl -fL --retry 3 -o XAUUSD_m15_ejtrader.csv \
  https://raw.githubusercontent.com/ejtraderLabs/historical-data/master/XAUUSD/XAUUSDm15.csv
wc -l XAUUSD_5m.csv XAUUSD_m15_ejtrader.csv
