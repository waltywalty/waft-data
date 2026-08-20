"""Check 1 of 3: the EA's calendar arithmetic, transliterated from the MQL5 line for line,
against Python's IANA timezone database. Every day from 2020 to 2026.

This is the part a compiler would never catch: an EA that computes the wrong hour compiles
perfectly and then trades an hour off for half the year.
"""
import datetime as dt
from zoneinfo import ZoneInfo

DAY = 86400

def dow_utc(t):                      # MQL5 DowUtc: 0 = Sunday
    return (dt.datetime.utcfromtimestamp(t).weekday() + 1) % 7

def nth_weekday_utc(year, month, weekday, n, hour):
    """Transliteration of NthWeekdayUtc()."""
    first = int(dt.datetime(year, month, 1, hour).replace(tzinfo=dt.timezone.utc).timestamp())
    if n > 0:
        shift = (weekday - dow_utc(first) + 7) % 7
        return first + (shift + (n - 1) * 7) * DAY
    ny = year + 1 if month == 12 else year
    nm = 1 if month == 12 else month + 1
    next_first = int(dt.datetime(ny, nm, 1, hour).replace(tzinfo=dt.timezone.utc).timestamp())
    last = next_first - DAY
    back = (dow_utc(last) - weekday + 7) % 7
    return last - back * DAY

def is_europe_dst(utc):
    y = dt.datetime.utcfromtimestamp(utc).year
    return nth_weekday_utc(y, 3, 0, -1, 1) <= utc < nth_weekday_utc(y, 10, 0, -1, 1)

def is_us_dst(utc):
    y = dt.datetime.utcfromtimestamp(utc).year
    return nth_weekday_utc(y, 3, 0, 2, 7) <= utc < nth_weekday_utc(y, 11, 0, 1, 6)

def london_offset(utc): return 1 if is_europe_dst(utc) else 0
def newyork_offset(utc): return -4 if is_us_dst(utc) else -5

LDN, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")

def truth_offset(ts, tz):
    return int(dt.datetime.fromtimestamp(ts, tz).utcoffset().total_seconds() // 3600)

bad_l = bad_n = 0; checked = 0
first_bad = []
t = int(dt.datetime(2020, 1, 1, 12, tzinfo=dt.timezone.utc).timestamp())
end = int(dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc).timestamp())
while t < end:
    checked += 1
    el, tl = london_offset(t), truth_offset(t, LDN)
    en, tn = newyork_offset(t), truth_offset(t, NY)
    if el != tl:
        bad_l += 1
        if len(first_bad) < 5: first_bad.append(("London", dt.datetime.utcfromtimestamp(t).date(), el, tl))
    if en != tn:
        bad_n += 1
        if len(first_bad) < 5: first_bad.append(("New York", dt.datetime.utcfromtimestamp(t).date(), en, tn))
    t += DAY

print(f"days checked            : {checked}  (2020-01-01 .. 2026-12-31, midday UTC)")
print(f"London offset mismatches: {bad_l}")
print(f"New York mismatches     : {bad_n}")
for b in first_bad: print("   ", b)

# the actual session anchors the EA computes
print("\nsession anchors the EA derives, spot-checked against the tz database:")
for d in ("2024-01-15", "2024-03-11", "2024-03-27", "2024-07-15", "2024-11-01", "2025-06-02"):
    day = int(dt.datetime.fromisoformat(d).replace(tzinfo=dt.timezone.utc).timestamp())
    cutoff = day + (8 - london_offset(day)) * 3600          # 08:00 London
    exit_  = day + (16 - newyork_offset(day)) * 3600        # 16:00 New York
    tc = dt.datetime.fromisoformat(d + "T08:00").replace(tzinfo=LDN).astimezone(dt.timezone.utc)
    te = dt.datetime.fromisoformat(d + "T16:00").replace(tzinfo=NY).astimezone(dt.timezone.utc)
    ok = (cutoff == int(tc.timestamp())) and (exit_ == int(te.timestamp()))
    print(f"  {d}: cutoff {dt.datetime.utcfromtimestamp(cutoff):%H:%M}Z, "
          f"exit {dt.datetime.utcfromtimestamp(exit_):%H:%M}Z   {'OK' if ok else 'MISMATCH'}")

# and 09:30 HKT on a broker clock, the trap from the report
print("\n09:30 Hong Kong on an EET/EEST broker clock:")
ATH = ZoneInfo("Europe/Athens")
for d in ("2024-01-15", "2024-07-15"):
    u = dt.datetime.fromisoformat(d + "T01:30").replace(tzinfo=dt.timezone.utc)
    print(f"  {d}: {u.astimezone(ATH):%H:%M} server, {u.astimezone(ZoneInfo('Asia/Hong_Kong')):%H:%M} HK")
