#!/usr/bin/env bash
# Re-download the US index intraday data (kept out of git — ~650 MB total).
#
#   SPX500_1m_oanda_futuresharks.csv  1-min S&P 500 CFD,     2005-01-02..2020-05-14, UTC timestamps
#   NAS100_1m_oanda_futuresharks.csv  1-min Nasdaq-100 CFD,  2005-01-02..2020-05-14, UTC timestamps
#   US2000_1m_oanda_futuresharks.csv  1-min Russell 2000 CFD 2005-01-02..2020-05-14, UTC timestamps
#       Source: github.com/FutureSharks/financial-data (MIT licence), Oanda feed.
#       Volume = Oanda tick count. Monthly files are concatenated and columns
#       reordered to time,open,high,low,close,volume.
#   US500_5m_ts4blader.csv            5-min S&P 500 CFD,     2020-01-02..2025-12-31, server time = fixed UTC+2
#   US100_5m_ts4blader.csv            5-min Nasdaq-100 CFD,  2021-01-04..2025-12-31, server time = fixed UTC+2
#       Source: github.com/ts4blader/market_data (no licence stated), MT5 broker
#       export stored in Git LFS — fetched via media.githubusercontent.com.
#       Volume = broker tick volume. UTC+2 offset was verified empirically by
#       cross-matching bars against the Oanda feed on 2020-01-15 and 2020-05-13.
#   RTY_5m_topstepx_axb0306.csv       5-min RTY futures,     2026-01-20..2026-04-15 (short, optional)
#   RTY_1h_topstepx_axb0306.csv       1-h  RTY futures,      2025-03-21..2026-04-15 (short, optional)
#       Source: github.com/axb0306/cme-futures-ohlc (no licence stated), TopstepX
#       feed, real contract volume. CAVEAT: not fully reproducible — the repo
#       appends nightly and encodes the end date in the filename, so the URLs
#       below are pinned to the snapshot fetched on 2026-08-25. If they 404,
#       list the RTY/ folder on GitHub for the current filenames. Failure of
#       this optional step does not abort the script.
#
# All targets are CFD data except the RTY files; none carry true exchange volume
# for the multi-year ranges. Russell 2000 has an intraday hole 2020-05..2025-03.
set -euo pipefail
cd "$(dirname "$0")/data"

# --- Oanda 1-minute CFDs (FutureSharks/financial-data) -----------------------
need_oanda=0
for inst in SPX500 NAS100 US2000; do
  [ -f "${inst}_1m_oanda_futuresharks.csv" ] || need_oanda=1
done
if [ "$need_oanda" = 1 ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  git clone --filter=blob:none --no-checkout \
    https://github.com/FutureSharks/financial-data.git "$tmp/fsdata"
  base=pyfinancialdata/data/currencies/oanda
  git -C "$tmp/fsdata" sparse-checkout set \
    $base/SPX500_USD $base/NAS100_USD $base/US2000_USD
  git -C "$tmp/fsdata" checkout HEAD -- \
    $base/SPX500_USD $base/NAS100_USD $base/US2000_USD
  for inst in SPX500 NAS100 US2000; do
    out=${inst}_1m_oanda_futuresharks.csv
    [ -f "$out" ] && continue
    src="$tmp/fsdata/$base/${inst}_USD"
    echo "time,open,high,low,close,volume" > "$out"
    # Monthly files are time,close,high,low,open,volume — reorder to OHLCV.
    # Iterate years then months numerically so rows stay chronological.
    for y in $(ls "$src" | sort -n); do
      for m in $(seq 1 12); do
        f="$src/$y/oanda-${inst}_USD-$y-$m.csv"
        [ -f "$f" ] && awk -F, 'NR>1{print $1","$5","$3","$4","$2","$6}' "$f"
      done
    done >> "$out"
    wc -l "$out"
  done
  rm -rf "$tmp"
  trap - EXIT
fi

# --- ts4blader 5-minute CFDs (Git LFS) ---------------------------------------
[ -f US500_5m_ts4blader.csv ] || curl -fL --retry 3 -o US500_5m_ts4blader.csv \
  https://media.githubusercontent.com/media/ts4blader/market_data/main/US500/US500_M5.csv
[ -f US100_5m_ts4blader.csv ] || curl -fL --retry 3 -o US100_5m_ts4blader.csv \
  https://media.githubusercontent.com/media/ts4blader/market_data/main/US100/US100_M5.csv

# --- RTY futures (optional, pinned snapshot — see header caveat) -------------
[ -f RTY_5m_topstepx_axb0306.csv ] || curl -fL --retry 3 -o RTY_5m_topstepx_axb0306.csv \
  https://raw.githubusercontent.com/axb0306/cme-futures-ohlc/main/RTY/RTY_5min_20260120_20260415.csv \
  || { rm -f RTY_5m_topstepx_axb0306.csv; echo "WARN: RTY 5m snapshot gone (filename advances nightly upstream); skipping"; }
[ -f RTY_1h_topstepx_axb0306.csv ] || curl -fL --retry 3 -o RTY_1h_topstepx_axb0306.csv \
  https://raw.githubusercontent.com/axb0306/cme-futures-ohlc/main/RTY/RTY_1h_20250321_20260415.csv \
  || { rm -f RTY_1h_topstepx_axb0306.csv; echo "WARN: RTY 1h snapshot gone (filename advances nightly upstream); skipping"; }

wc -l SPX500_1m_oanda_futuresharks.csv NAS100_1m_oanda_futuresharks.csv \
      US2000_1m_oanda_futuresharks.csv US500_5m_ts4blader.csv US100_5m_ts4blader.csv
