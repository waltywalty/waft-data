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

# Round 15b: Hang Seng + Asian partners
# HSI CFD (Oanda collector, live-updated hourly; UTC timestamps; day opens 01:15 UTC = 09:15 HKT)
for f in HK33_H1 HK33_M15 HK33_M5 JP225_H1; do
  curl -fL --retry 3 -sSO "https://raw.githubusercontent.com/user1-2-3-4/oanda-data-collector/main/data/indices/$f.csv"
done
# HK50 15m 2022-02..2024-04 + China partners (Yuan archive; chunked files -> concat):
#   git clone --depth 1 --filter=blob:none --sparse https://github.com/No-Trade-No-Life/Yuan-Public-Data.git
#   git -C Yuan-Public-Data sparse-checkout set OHLC/HK50 OHLC/CHCUSD OHLC/HSCHKD OHLC/CFFEX_IF
#   then concat each OHLC/<SYM>/<TF>/*.csv (drop_duplicates on time, sort) into
#   <SYM>_<TF>_yuan.csv - see run_hsi.py header for the exact frames used.

# Round 16: VIX/VIX3M (CBOE mirrors), USDJPY, AUS200, JP225 1m history
curl -fL --retry 3 -o VIX_daily_github.csv "https://raw.githubusercontent.com/datasets/finance-vix/main/data/vix-daily.csv"
curl -fL --retry 3 -o VIX3M_daily_github.csv "https://raw.githubusercontent.com/ahsub/ko-aggregator/main/data/raw_data/VIX3M_History.csv"
for f in USDJPY_M15 USDJPY_H1; do curl -fL --retry 3 -sSO "https://raw.githubusercontent.com/user1-2-3-4/oanda-data-collector/main/data/forex/$f.csv"; done
curl -fL --retry 3 -sSO "https://raw.githubusercontent.com/user1-2-3-4/oanda-data-collector/main/data/indices/AUS200_H1.csv"
# JP225 1m 2005-2020 (FutureSharks, ~150 MB, monthly files concatenated):
#   for y in $(seq 2005 2020); do for m in $(seq 1 12); do
#     curl -sf ".../FutureSharks/financial-data/master/pyfinancialdata/data/currencies/oanda/JP225_USD/$y/oanda-JP225_USD-$y-$m.csv" >> JP225_1m_futuresharks.csv
#   done; done
