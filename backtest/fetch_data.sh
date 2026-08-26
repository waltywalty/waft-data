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

# AUDUSD, for the correlation-regime work
curl -fL --retry 3 -o AUDUSD_M5.csv \
  https://raw.githubusercontent.com/jaxontn/historical-Data/main/AUDUSD_M5.csv
curl -fL --retry 3 -o AUDUSD_m15_ejtrader.csv \
  https://raw.githubusercontent.com/ejtraderLabs/historical-data/master/AUDUSD/AUDUSDm15.csv
curl -fL --retry 3 -o AUDUSD_daily_fred.csv \
  https://raw.githubusercontent.com/unbalancedparentheses/forex-centuries/main/data/sources/fred/daily/fred_aud_usd.csv

# CNY (FRED DEXCHUS, yuan per dollar) for the China-reference test
curl -fL --retry 3 -o CNY_daily_fred.csv \
  https://raw.githubusercontent.com/unbalancedparentheses/forex-centuries/main/data/sources/fred/daily/fred_cny_usd.csv

# Round-13 correlation partners: more FRED daily FX (same mirror)
for p in eur_usd jpy_usd gbp_usd chf_usd cad_usd; do
  out="$(echo "$p" | tr -d '_' | tr 'a-z' 'A-Z')_daily_fred.csv"
  curl -fL --retry 3 -o "$out" \
    "https://raw.githubusercontent.com/unbalancedparentheses/forex-centuries/main/data/sources/fred/daily/fred_${p}.csv"
done
# Silver, WTI and the 10y yield came from Alpha Vantage daily endpoints
# (GOLD_SILVER_HISTORY / WTI / TREASURY_YIELD -> SILVER_daily_av.csv,
# WTI_daily_av.csv, UST10Y_daily_av.csv); re-pull them there if absent.
