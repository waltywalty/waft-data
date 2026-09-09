#!/bin/bash
# Bootstrap for the Kernel cloud-browser VM (run via exec_command bash -c "$(cat this)").
# Builds the SEC fails-to-deliver URL list from the SEC index page and launches a detached
# loop that downloads each half-month zip, keeps only rows for the basket symbols, and
# appends to /tmp/work/ftd_all.csv. Year files are pulled back with base64.
mkdir -p /tmp/work && cd /tmp/work
printf '%s\n' SPY QQQ IWM AAPL ABBV ABT ADI AMAT AMD AMGN AMZN ANET APH AVGO AXP BA BAC BKNG BLK BMY BRKB 'BRK.B' 'BRK B' 'BRK-B' C CAT COF COP COST CRM CRWD CSCO CVS CVX DE DHR DIS ETN GE GEV GILD GOOG GOOGL GS HD IBM INTC ISRG JNJ JPM KLAC KO LIN LLY LRCX MA MCD META MRK MRVL MS MSFT MU NEE NEM NFLX NOW NVDA ORCL PANW PEP PFE PG PGR PLD PLTR PM QCOM RTX SCHW SNDK SPGI STX T TJX TMO TSLA TXN UBER UNH UNP V VRTX VZ WDC WELL WFC WMT XOM > syms.txt
UA='waft-data research (rogerlgk@gmail.com)'
curl -sS -A "$UA" --max-time 60 https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data -o ftdpage.html
grep -o 'href="[^"]*cnsfails20[0-9][0-9][0-9][0-9][ab][^"]*\.zip"' ftdpage.html   # accepts the SEC's _0 re-upload names | sed 's#href="##; s#"$##; s#^#https://www.sec.gov#' \
 | awk '{n=match($0,/cnsfails[0-9]+/); y=substr($0,n+8,4); if (y>=2012) print}' | sort -u -t/ -k7 > sec_urls.txt
cat > ftd2.sh <<'EOT'
#!/bin/bash
set -u
cd /tmp/work
UA="waft-data research (rogerlgk@gmail.com)"
: > ftd_all.csv; : > ftd2.log
while read -r u; do
  f=$(basename "$u")
  code=$(curl -sS -A "$UA" -o "$f" -w '%{http_code}' --max-time 120 "$u")
  if [ "$code" = "200" ]; then
    n=$(unzip -p "$f" | LC_ALL=C awk -F'|' 'NR==FNR{s[$1]=1;next} ($3 in s){print $1","$2","$3","$4","$6}' syms.txt - | tee -a ftd_all.csv | wc -l)
    echo "$f 200 rows=$n" >> ftd2.log
  else
    echo "$f $code" >> ftd2.log
  fi
  rm -f "$f"; sleep 0.3
done < sec_urls.txt
echo ALLDONE >> ftd2.log
EOT
chmod +x ftd2.sh; setsid nohup bash ftd2.sh > ftd2.out 2>&1 < /dev/null &
wc -l sec_urls.txt; head -1 sec_urls.txt; tail -1 sec_urls.txt
