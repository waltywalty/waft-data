"""Build the earnings-release calendar from EDGAR filing indexes (acq via the Kernel VM,
2026-09-09): data/earnings/edgar_filings.csv holds every 8-K / 10-Q / 10-K row for the basket
(ticker,cik,form,filingDate,reportDate,acceptanceDateTime,items,accession).

An earnings release is an 8-K whose Items include 2.02 ("Results of Operations and Financial
Condition"; item required since 2003-03-28). Output data/earnings/earnings_dates.csv:
ticker, release_date (filingDate of the 8-K), accepted_utc (EDGAR acceptance timestamp), session
(pre = accepted before 09:30 ET on a trading day, post = after 16:00 ET, intra otherwise),
period (reportDate = fiscal period end when EDGAR carries it). Signal side only.
Cross-check: the three Alpha Vantage EARNINGS files (AAPL/ABT/AMAT) give reportedDate/reportTime.
"""
import csv, json, os, datetime as dt
from zoneinfo import ZoneInfo

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "earnings")
ET = ZoneInfo("America/New_York")


def parse():
    rows = list(csv.DictReader(open(os.path.join(HERE, "edgar_filings.csv"))))
    out = []
    for r in rows:
        if not r["form"].startswith("8-K"): continue
        items = r["items"] or ""
        if "2.02" not in [x.strip() for x in items.split(",")]: continue
        acc = r["acceptanceDateTime"]
        sess = ""
        try:
            t = dt.datetime.strptime(acc, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.timezone.utc).astimezone(ET)
            hm = t.hour * 100 + t.minute
            sess = "pre" if hm < 930 else ("post" if hm >= 1600 else "intra")
            acc_local = t.strftime("%Y-%m-%d %H:%M ET")
        except Exception:
            acc_local = acc
        out.append(dict(ticker=r["ticker"], release_date=r["filingDate"], accepted=acc_local, session=sess,
                        period=r["reportDate"], accession=r["accession"]))
    out.sort(key=lambda x: (x["ticker"], x["release_date"]))
    with open(os.path.join(HERE, "earnings_dates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    return out


def crosscheck(out):
    for sym in ("AAPL", "ABT", "AMAT"):
        p = os.path.join(HERE, f"{sym}.json")
        if not os.path.exists(p): continue
        av = {q["reportedDate"]: q.get("reportTime") for q in json.load(open(p))["quarterlyEarnings"]}
        ed = {r["release_date"]: r["session"] for r in out if r["ticker"] == sym}
        avd = sorted(d for d in av if d >= "2004-01-01"); edd = sorted(ed)
        exact = sum(d in ed for d in avd)
        near = sum(any(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(e)).days) <= 1 for e in edd) for d in avd)
        print(f"{sym}: AV dates 2004+ {len(avd)}, EDGAR 8-K 2.02 {len(edd)} ({edd[0] if edd else '-'}..{edd[-1] if edd else '-'}); "
              f"exact match {exact}, within 1 day {near}; AV-only {[d for d in avd if not any(abs((dt.date.fromisoformat(d)-dt.date.fromisoformat(e)).days)<=1 for e in edd)][:5]}")


if __name__ == "__main__":
    o = parse()
    from collections import Counter
    c = Counter(r["ticker"] for r in o)
    print(f"{len(o)} earnings releases, {len(c)} tickers; per-ticker min/median/max "
          f"{min(c.values())}/{sorted(c.values())[len(c)//2]}/{max(c.values())}")
    first = {}
    for r in o: first.setdefault(r["ticker"], r["release_date"])
    late = {k: v for k, v in first.items() if v > "2006-01-01"}
    print("tickers whose first 8-K 2.02 is after 2006:", late)
    print("session split:", Counter(r["session"] for r in o))
    crosscheck(o)
