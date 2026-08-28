#!/usr/bin/env python3
"""WaFT free-data fetcher.

Runs beside the Webull fetcher, does not replace it. Webull still supplies HK
cash equities (the one thing Walton is entitled to); this supplies everything
the US entitlement refused.

What the probe established on 2026-07-29:
  Yahoo via yfinance   ES/RTY/NQ/YM + cash + macro, ~10-15 min delayed   PASS
  CNBC quote service   .VIX near-live, .HSI, .SPX, .RUT, @CL.1           PASS
  CNBC @ES.1/@RTY.1    code 1 - CME equity index futures not served      FAIL
  Cboe delayed CDN     yesterday's close only, redundant                 skip
  Stooq                404 from this droplet                             skip
  FRED fredgraph.csv   times out from this droplet even at 45s           skip
  treasury.gov curve   daily, whole curve                                PASS

The delay does not hurt what these numbers are for. An overnight range is built
over eight hours; being fifteen minutes late tells you the same range. What a
delayed feed cannot give is the last tick -- and Walton has that on his screen.

Writes  data/latest/free.json  and  data/latest/free-bars.json,  commits, pushes.

Also keeps an append-only archive beside them, because latest/ is overwritten
every cycle and so remembers nothing:
    data/archive/bars/YYYY-MM-DD.jsonl     one line per closed 5-minute bar
    data/archive/quotes/YYYY-MM-DD.jsonl   one cross-asset snapshot per 5 minutes
    data/archive/state.json                newest bar written per symbol

Self-test with no network:  python3 freefetch.py --selftest
"""
import json, os, sys, time, math, datetime, subprocess, urllib.request, urllib.error
import logging

BASE = os.environ.get("WAFT_BASE", "/opt/waft")
DATA = os.path.join(BASE, "data")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
UTC = datetime.timezone.utc

# Futures first -- these are the actual contracts he trades, not proxies.
FUT = {"ES=F": "ES", "RTY=F": "RTY", "NQ=F": "NQ", "YM=F": "YM"}
CASH = {"^GSPC": "SPX", "^RUT": "RUT", "^NDX": "NDX", "^VIX": "VIX", "^HSI": "HSI"}
MACRO = {"CL=F": "CRUDE", "GC=F": "GOLD", "DX-Y.NYB": "DXY", "^TNX": "US10Y"}
ALL = {}
ALL.update(FUT); ALL.update(CASH); ALL.update(MACRO)
BAR_KEYS = ("ES", "RTY", "NQ", "YM", "HSI")   # widened 7 Aug 2026 - the 5m download already fetches all of these

CNBC = ("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
        "?symbols={}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1"
        "&output=json&events=1")
CNBC_HDR = {"Referer": "https://www.cnbc.com/quotes/", "Origin": "https://www.cnbc.com",
            "Accept": "application/json, text/plain, */*", "User-Agent": UA}
CNBC_SYMS = {".VIX": "VIX", ".HSI": "HSI", ".SPX": "SPX", ".RUT": "RUT", "@CL.1": "CRUDE"}


_QUIET = False


def log(msg):
    # The self-test runs at the top of every cron cycle, and the archive checks
    # inside it call the real archive() against a temp dir. Their log lines are
    # true but meaningless -- "+3 bars" that never existed. Muted so the cron log
    # stays a record of what actually happened.
    if _QUIET:
        return
    print("%s %s" % (datetime.datetime.now(UTC).strftime("%H:%M:%S"), msg), flush=True)


# ------------------------------------------------------------- pure helpers ---
def num(v):
    if v is None:
        return None
    try:
        f = float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def parse_ts(s, fmts):
    for f in fmts:
        try:
            d = datetime.datetime.strptime(str(s), f)
            return (d if d.tzinfo else d.replace(tzinfo=UTC)).timestamp()
        except (ValueError, TypeError):
            continue
    return None


def parse_cnbc(body):
    """-> (px, ts, name). px None when the payload has no usable quote."""
    d = json.loads(body)
    res = d.get("FormattedQuoteResult") or d.get("QuickQuoteResult") or {}
    q = res.get("FormattedQuote") or res.get("QuickQuote") or []
    if isinstance(q, dict):
        q = [q]
    if not q:
        return None, None, "no quote"
    q = q[0]
    px = num(q.get("last")) or num(q.get("last_trade")) or num(q.get("previous_day_closing"))
    ts = None
    for k in ("last_time", "last_time_msec", "cacheServerTime"):
        v = q.get(k)
        if not v:
            continue
        sv = str(v)
        if sv.isdigit() and len(sv) >= 12:
            ts = int(sv) / 1000.0
            break
        ts = parse_ts(sv, ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                           "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"))
        if ts:
            break
    return px, ts, str(q.get("name") or q.get("symbol") or "")[:40]


def parse_treasury(body):
    """-> dict of tenor -> yield, plus the row date. Whole curve, daily."""
    lines = [l for l in body.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return {}, None
    hdr = [h.strip().strip('"') for h in lines[0].split(",")]
    row = [v.strip().strip('"') for v in lines[1].split(",")]
    d = dict(zip(hdr, row))
    out = {}
    for col, key in (("1 Mo", "M1"), ("3 Mo", "M3"), ("6 Mo", "M6"), ("1 Yr", "Y1"),
                     ("2 Yr", "Y2"), ("5 Yr", "Y5"), ("10 Yr", "Y10"), ("30 Yr", "Y30")):
        v = num(d.get(col))
        if v is not None:
            out[key] = v
    if "Y10" in out and "Y2" in out:
        out["S2s10s"] = round(out["Y10"] - out["Y2"], 3)
    return out, parse_ts(d.get("Date", ""), ("%m/%d/%Y", "%Y-%m-%d"))


def overnight_start(now_ts):
    """Most recent 20:00 UTC (16:00 ET, the US cash close in July) before now.

    The overnight session is the window that decides how the US open behaves,
    and it is the one thing a fifteen-minute delay leaves completely intact.
    """
    n = datetime.datetime.fromtimestamp(now_ts, UTC)
    cut = n.replace(hour=20, minute=0, second=0, microsecond=0)
    if cut > n:
        cut -= datetime.timedelta(days=1)
    return cut.timestamp()


def summarise(bars, now_ts, prev_close=None):
    """bars: list of (ts, o, h, l, c, v) ascending. -> quote dict.

    Pure, so it can be tested without pandas or a network.
    """
    bars = [b for b in bars if b[4] is not None]
    if not bars:
        return None
    last_ts, _, _, _, last_px, _ = bars[-1]
    on = overnight_start(now_ts)
    on_bars = [b for b in bars if b[0] >= on]
    d1 = [b for b in bars if b[0] >= now_ts - 86400]
    q = {
        "px": round(last_px, 4),
        "ts": int(last_ts),
        "age_s": max(0, int(now_ts - last_ts)),
        "bars": len(bars),
    }
    if on_bars:
        q["on_high"] = round(max(b[2] for b in on_bars), 4)
        q["on_low"] = round(min(b[3] for b in on_bars), 4)
        q["on_open"] = round(on_bars[0][1], 4)
        rng = q["on_high"] - q["on_low"]
        q["on_range"] = round(rng, 4)
        # where in the overnight range are we sitting? 0 = at the low, 1 = at the high.
        q["on_pos"] = round((last_px - q["on_low"]) / rng, 3) if rng > 0 else None
    if d1:
        q["d1_high"] = round(max(b[2] for b in d1), 4)
        q["d1_low"] = round(min(b[3] for b in d1), 4)
    if prev_close:
        q["prev_close"] = round(prev_close, 4)
        q["chg"] = round(last_px - prev_close, 4)
        q["chg_pct"] = round((last_px - prev_close) / prev_close * 100, 3) if prev_close else None
    return q


# --------------------------------------------------------------- networking ---
def get(url, timeout=25, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def frame_to_bars(df, tkr):
    """yfinance frame -> [(ts,o,h,l,c,v)]. Handles flat and MultiIndex columns."""
    import pandas as pd
    if df is None or len(df) == 0:
        return []
    sub = df
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = set(df.columns.get_level_values(0))
        if tkr in lvl0:
            sub = df[tkr]
        else:
            lvl1 = set(df.columns.get_level_values(1))
            if tkr in lvl1:
                sub = df.xs(tkr, axis=1, level=1)
            else:
                return []
    cols = {c.lower(): c for c in sub.columns}
    need = [cols.get(k) for k in ("open", "high", "low", "close")]
    if any(c is None for c in need):
        return []
    vcol = cols.get("volume")
    idx = sub.index
    try:
        idx = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    except (AttributeError, TypeError):
        pass
    out = []
    for i in range(len(sub)):
        try:
            c = num(sub[need[3]].iloc[i])
            if c is None:
                continue
            out.append((idx[i].timestamp(),
                        num(sub[need[0]].iloc[i]), num(sub[need[1]].iloc[i]),
                        num(sub[need[2]].iloc[i]), c,
                        num(sub[vcol].iloc[i]) if vcol else None))
        except Exception:
            continue
    return out


PREV_CACHE = os.path.join(BASE, "prevclose.json")
PREV_TTL = 1800          # a previous close changes once a day; don't re-ask every cycle


def prev_closes(now_ts, yf):
    """Cached previous closes. Halves the load we put on Yahoo per cycle."""
    try:
        with open(PREV_CACHE) as f:
            c = json.load(f)
        if now_ts - c.get("ts", 0) < PREV_TTL and c.get("map"):
            return c["map"]
    except Exception:
        pass
    out = {}
    try:
        dly = yf.download(list(ALL.keys()), period="7d", interval="1d", group_by="ticker",
                          auto_adjust=False, progress=False, threads=False)
        for tkr, key in ALL.items():
            db = frame_to_bars(dly, tkr)
            if len(db) >= 2:
                out[key] = db[-2][4]
            elif db:
                out[key] = db[0][4]
        if out:
            with open(PREV_CACHE, "w") as f:
                json.dump({"ts": now_ts, "map": out}, f)
    except Exception as e:
        log("  prev_close refresh failed: %s" % type(e).__name__)
        try:
            with open(PREV_CACHE) as f:
                return json.load(f).get("map", {})       # stale beats nothing
        except Exception:
            pass
    return out


def fetch_yahoo(now_ts):
    """One batched intraday download, plus a cached daily one. -> (quotes, bars)."""
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    import yfinance as yf
    quotes, barsout = {}, {}
    df = yf.download(list(ALL.keys()), period="2d", interval="5m", group_by="ticker",
                     auto_adjust=False, progress=False, threads=False)
    prevmap = prev_closes(now_ts, yf)
    for tkr, key in ALL.items():
        bars = frame_to_bars(df, tkr)
        q = summarise(bars, now_ts, prevmap.get(key))
        if q:
            q["src"] = "yahoo"
            quotes[key] = q
            if key in BAR_KEYS:
                barsout[key] = [[int(b[0]), b[1], b[2], b[3], b[4], b[5]] for b in bars[-96:]]
    return quotes, barsout


def fetch_cnbc(now_ts):
    out = {}
    for sym, key in CNBC_SYMS.items():
        try:
            code, body = get(CNBC.format(sym.replace("@", "%40")), headers=CNBC_HDR)
            px, ts, name = parse_cnbc(body)
            if px is not None:
                out[key] = {"px": round(px, 4), "ts": int(ts) if ts else None,
                            "age_s": max(0, int(now_ts - ts)) if ts else None,
                            "src": "cnbc", "name": name}
        except Exception as e:
            log("  cnbc %s: %s" % (sym, type(e).__name__))
    return out


def fetch_rates(now_ts):
    try:
        yr = datetime.datetime.now(UTC).year
        url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
               "daily-treasury-rates.csv/%d/all?type=daily_treasury_yield_curve"
               "&field_tdr_date_value=%d&page&_format=csv" % (yr, yr))
        _, body = get(url, timeout=45)
        curve, ts = parse_treasury(body)
        if curve:
            curve["ts"] = int(ts) if ts else None
            curve["src"] = "treasury.gov"
            return curve
    except Exception as e:
        log("  treasury: %s" % type(e).__name__)
    return {}


# ------------------------------------------------------------------ calendar ---
# The dashboard's catalyst board used to be a hand-written list, which meant it
# ran dry two days after every brief. This makes the FACTS self-refreshing: what
# is scheduled, when, and how big the market thinks it is. The judgement -- which
# contract an event moves, how far it can travel, why it matters -- stays in the
# dashboard, because that half is not a fact and must not be dressed as one.
CAL_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CAL_EVERY = 3600                  # a weekly file; hourly is already generous
CAL_CCY = ("USD", "EUR", "GBP", "JPY", "CNY")    # what moves ES, RTY and HSI
CAL_MIN_IMP = 2                   # Medium and up. Low is noise on a phone screen.
IMPACT = {"high": 3, "medium": 2, "low": 1, "holiday": 0, "non-economic": 0}


def iso_epoch(s):
    """ISO-8601 with or without an offset -> epoch. None on anything else."""
    if not isinstance(s, str) or not s.strip():
        return None
    try:
        d = datetime.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.timestamp()


def parse_calendar(body, now, back=6 * 3600, fwd=14 * 86400):
    """Weekly calendar JSON -> normalised events, UTC-stamped, soonest first.

    Keeps a few hours of the past so the board can say what just landed, and caps
    the future so a malformed file cannot fill the page with next month.
    """
    try:
        raw = json.loads(body)
    except ValueError:
        return []
    if not isinstance(raw, list):
        return []
    out = []
    for e in raw:
        if not isinstance(e, dict):
            continue
        ccy = (e.get("country") or "").strip().upper()
        imp = IMPACT.get((e.get("impact") or "").strip().lower(), 0)
        title = " ".join((e.get("title") or "").split())
        ts = iso_epoch(e.get("date"))
        if (not title or ccy not in CAL_CCY or imp < CAL_MIN_IMP
                or ts is None or ts < now - back or ts > now + fwd):
            continue
        ev = {"t": datetime.datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "e": int(ts), "n": title, "c": ccy, "i": imp}
        for src, dst in (("forecast", "f"), ("previous", "p")):
            v = (e.get(src) or "").strip()
            if v:
                ev[dst] = v
        out.append(ev)
    out.sort(key=lambda x: (x["e"], x["n"]))
    # The feed sometimes carries the same release twice as it gets revised. Same
    # name at the same minute is the same event.
    ded, seen = [], set()
    for ev in out:
        k = (ev["e"], ev["n"])
        if k not in seen:
            seen.add(k)
            ded.append(ev)
    return ded


def cal_due(path, now):
    """The file's own mtime is the only state this needs, so a restart cannot
    make it forget and re-fetch on every three-minute cycle."""
    try:
        return now - os.path.getmtime(path) >= CAL_EVERY
    except OSError:
        return True


def fetch_calendar(now):
    st, body = get(CAL_URL, timeout=25)
    if st != 200:
        raise RuntimeError("HTTP %s" % st)
    return parse_calendar(body, now)


def merge(yahoo_q, cnbc_q):
    """Yahoo is the base. CNBC overrides only when it is meaningfully fresher.

    Both agreed to the cent on HSI in the probe, so this is about latency, not
    disagreement -- take whichever saw the market more recently.
    """
    out = dict(yahoo_q)
    for key, c in cnbc_q.items():
        y = out.get(key)
        if y is None:
            out[key] = c
            continue
        ya, ca = y.get("age_s"), c.get("age_s")
        if ca is not None and (ya is None or ca + 120 < ya):
            merged = dict(y)
            merged.update({"px": c["px"], "ts": c["ts"], "age_s": ca,
                           "src": "cnbc", "yahoo_px": y.get("px")})
            out[key] = merged
        else:
            y["cnbc_px"] = c["px"]
    return out


# ---------------------------------------------------------------- git output ---
def git(*args, check=False):
    return subprocess.run(["git"] + list(args), cwd=DATA, capture_output=True,
                          text=True, timeout=120, check=check)


# ------------------------------------------------------------------ archive ---
# latest/free*.json are overwritten every cycle, so nothing about the past
# survives there. Until now the only record was the commit history itself -- a
# 29-hour volume profile had to be reconstructed by walking 1,839 commits and
# deduplicating 328,320 overlapping bar observations. That works once. It is not
# a storage format.
#
# So: an append-only archive beside them. Two rules make it cheap in git.
#
#   1. Append, never rewrite. A file that only grows delta-compresses to almost
#      nothing between commits; a file rewritten 1,440 times a day does not.
#   2. Write a bar ONLY once it is closed. Yahoo republishes the in-progress bar
#      every cycle with growing volume and a widening range, so an eager append
#      would write the same bar 5 times with 5 different values. The newest bar
#      in each series is therefore always held back -- by the time it is written
#      it is final and never needs revising.
#
# One line per closed 5-minute bar: ~576 lines a day for ES+RTY, about 45 KB.
ARCH = os.path.join(DATA, "archive")
STATE = os.path.join(ARCH, "state.json")
QUOTE_EVERY = 300                  # sample the cross-asset snapshot on the bar grid


def _day(ts):
    return datetime.datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")


def _load_state():
    try:
        with open(STATE) as f:
            s = json.load(f)
        return {"bars": dict(s.get("bars") or {}), "quote": s.get("quote") or 0}
    except (OSError, ValueError):
        return {"bars": {}, "quote": 0}


def append_bars(bars, state):
    """Append closed bars, newest-per-symbol held back. -> lines written."""
    out, written = {}, 0
    for sym, rows in (bars or {}).items():
        if not rows:
            continue
        seen = state["bars"].get(sym, 0)
        # rows[:-1] -- the last one is still forming and will be revised.
        for r in sorted(rows, key=lambda x: x[0])[:-1]:
            ts = int(r[0])
            if ts <= seen or r[4] is None:
                continue
            out.setdefault(_day(ts), []).append(
                json.dumps({"s": sym, "t": ts, "o": r[1], "h": r[2],
                            "l": r[3], "c": r[4], "v": r[5]},
                           separators=(",", ":")))
            state["bars"][sym] = ts
            written += 1
    for day, lines in out.items():
        p = os.path.join(ARCH, "bars", day + ".jsonl")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as f:
            f.write("\n".join(lines) + "\n")
    return written


def append_quotes(payload, state, now):
    """One compact cross-asset line per five minutes. Prices only -- everything
    else in free.json is derived and can be recomputed from these."""
    if now - state["quote"] < QUOTE_EVERY:
        return 0
    row = {"t": int(now), "q": {}}
    for k, q in (payload.get("quotes") or {}).items():
        px = num(q.get("px"))
        if px is not None:
            row["q"][k] = px
    if not row["q"]:
        return 0
    r = payload.get("rates") or {}
    y = {k: num(v) for k, v in r.items() if isinstance(k, str) and k.startswith(("Y", "M", "S"))}
    y = {k: v for k, v in y.items() if v is not None}
    if y:
        row["y"] = y
    p = os.path.join(ARCH, "quotes", _day(now) + ".jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")
    state["quote"] = int(now)
    return 1


def archive(payload, bars, now):
    state = _load_state()
    try:
        nb = append_bars(bars, state)
        nq = append_quotes(payload, state, now)
    except OSError as e:
        log("  archive write failed (%s) - latest/ is unaffected" % e)
        return
    os.makedirs(ARCH, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, sort_keys=True)
    os.replace(tmp, STATE)             # atomic: a torn state file would re-append
    if nb or nq:
        log("  archive: +%d bars, +%d quote rows" % (nb, nq))


def publish(payload, bars, now=None, cal=None):
    if not os.path.isdir(os.path.join(DATA, ".git")):
        log("  no data repo at %s - wrote nothing" % DATA)
        return False
    latest = os.path.join(DATA, "latest")
    os.makedirs(latest, exist_ok=True)
    # Only ever written when we actually parsed events. A failed fetch must leave
    # yesterday's calendar standing -- a stale calendar is useful, a blank one is
    # a dashboard card that says "nothing scheduled" on the morning of an FOMC.
    # No separate archive: the file changes rarely, so git history IS its archive.
    if cal:
        with open(os.path.join(latest, "calendar.json"), "w") as f:
            json.dump({"ts": payload["ts"], "ts_epoch": payload["ts_epoch"],
                       "src": "faireconomy weekly", "n": len(cal), "events": cal},
                      f, indent=1)
    # Archive before staging, so the day's new lines ride the same commit as the
    # latest/ files rather than lagging a cycle behind them.
    archive(payload, bars, now if now is not None else time.time())
    with open(os.path.join(latest, "free.json"), "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
    with open(os.path.join(latest, "free-bars.json"), "w") as f:
        json.dump({"ts": payload["ts"], "interval": "5m", "bars": bars}, f)
    git("add", "-A")
    if not git("diff", "--cached", "--quiet").returncode:
        return True                      # nothing changed, nothing to push
    git("commit", "-q", "-m", "free %s" % payload["ts"])
    if git("push", "-q", "origin", "main").returncode:
        git("fetch", "-q", "origin", "main")
        git("rebase", "-q", "-X", "ours", "origin/main")
        if git("push", "-q", "origin", "main").returncode:
            log("  push failed twice - will retry next cycle")
            return False
    return True


# ----------------------------------------------------------------- self-test ---
def selftest():
    fails, ran = [], [0]

    def chk(n, got, want):
        ran[0] += 1
        if got != want:
            fails.append("%s: got %r want %r" % (n, got, want))

    # overnight_start: 20:00 UTC boundary in both directions
    t = datetime.datetime(2026, 7, 29, 8, 41, tzinfo=UTC).timestamp()
    chk("on.before20", datetime.datetime.fromtimestamp(overnight_start(t), UTC).isoformat(),
        "2026-07-28T20:00:00+00:00")
    t2 = datetime.datetime(2026, 7, 29, 22, 5, tzinfo=UTC).timestamp()
    chk("on.after20", datetime.datetime.fromtimestamp(overnight_start(t2), UTC).isoformat(),
        "2026-07-29T20:00:00+00:00")

    # summarise: build 5m bars from 2026-07-28 18:00 UTC forward
    base = datetime.datetime(2026, 7, 28, 18, 0, tzinfo=UTC).timestamp()
    bars = []
    for i in range(200):                      # 200 * 5m = 16h40m, crosses the 20:00 cut
        ts = base + i * 300
        c = 7400 + i * 0.5
        bars.append((ts, c - 0.25, c + 2, c - 2, c, 100))
    now = bars[-1][0] + 60
    q = summarise(bars, now, prev_close=7390.0)
    chk("sum.px", q["px"], bars[-1][4])
    chk("sum.age", q["age_s"], 60)
    # first bar at/after 20:00 UTC is i=24 -> close 7412.0, so its open is 7411.75
    chk("sum.on_open", q["on_open"], 7411.75)
    chk("sum.on_high", q["on_high"], round(bars[-1][4] + 2, 4))
    chk("sum.chg", q["chg"], round(bars[-1][4] - 7390.0, 4))
    chk("sum.pos_at_high", q["on_pos"] is not None and q["on_pos"] > 0.9, True)
    chk("sum.d1", q["d1_high"] is not None, True)
    # degenerate inputs must not raise
    chk("sum.empty", summarise([], now), None)
    chk("sum.allnone", summarise([(now, None, None, None, None, None)], now), None)
    flat = [(now - 300 * i, 100, 100, 100, 100, 1) for i in range(5)][::-1]
    chk("sum.flat_pos", summarise(flat, now)["on_pos"], None)   # zero range, no divide

    # CNBC: the two shapes seen live, plus the failure shape the probe returned
    ok = json.dumps({"FormattedQuoteResult": {"FormattedQuote": [
        {"symbol": ".VIX", "name": "CBOE Volatility Index", "last": "18.25",
         "last_time": "2026-07-29T04:41:01.000-0400"}]}})
    px, ts, name = parse_cnbc(ok)
    chk("cnbc.px", px, 18.25)
    chk("cnbc.ts", ts is not None, True)
    chk("cnbc.name", name, "CBOE Volatility Index")
    chk("cnbc.code1", parse_cnbc('{"FormattedQuoteResult":{"FormattedQuote":[{"symbol":"@ES.1","code":1}]}}')[0], None)
    chk("cnbc.dict", parse_cnbc(json.dumps({"QuickQuoteResult": {"QuickQuote":
        {"last": "2953.8", "last_time_msec": "1785055260000"}}}))[0], 2953.8)
    chk("cnbc.empty", parse_cnbc('{"FormattedQuoteResult":{"FormattedQuote":[]}}')[0], None)

    # treasury
    tb = ('Date,"1 Mo","3 Mo","6 Mo","1 Yr","2 Yr","5 Yr","10 Yr","30 Yr"\n'
          '07/28/2026,4.30,4.28,4.25,4.20,4.11,4.35,4.61,5.10\n')
    curve, cts = parse_treasury(tb)
    chk("tsy.y10", curve["Y10"], 4.61)
    chk("tsy.2s10s", curve["S2s10s"], 0.5)
    chk("tsy.ts", cts is not None, True)
    chk("tsy.empty", parse_treasury("")[0], {})

    # merge: CNBC wins only when it is >2 min fresher
    y = {"VIX": {"px": 18.4, "age_s": 900, "src": "yahoo"},
         "HSI": {"px": 25807.92, "age_s": 60, "src": "yahoo"}}
    c = {"VIX": {"px": 18.25, "age_s": 12, "src": "cnbc", "ts": 1, "name": "v"},
         "HSI": {"px": 25807.92, "age_s": 30, "src": "cnbc", "ts": 1, "name": "h"}}
    m = merge(y, c)
    chk("merge.vix_takes_cnbc", m["VIX"]["src"], "cnbc")
    chk("merge.vix_keeps_yahoo_px", m["VIX"]["yahoo_px"], 18.4)
    chk("merge.hsi_stays_yahoo", m["HSI"]["src"], "yahoo")
    chk("merge.hsi_records_cnbc", m["HSI"]["cnbc_px"], 25807.92)
    chk("merge.cnbc_only", merge({}, {"CRUDE": c["VIX"]})["CRUDE"]["src"], "cnbc")

    # archive: append-only, no duplicates, in-progress bar held back
    import tempfile, shutil
    global ARCH, STATE, _QUIET
    keep = (ARCH, STATE, _QUIET)
    tmpd = tempfile.mkdtemp(prefix="waft-arch-")
    try:
        _QUIET = True
        ARCH = tmpd
        STATE = os.path.join(tmpd, "state.json")
        t = 1785391200
        mk = lambda i: [t + i * 300, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 500.0]
        rows = [mk(i) for i in range(4)]
        pay = {"quotes": {"ES": {"px": 7407.5}, "VIX": {"px": 18.2}, "X": {"px": None}},
               "rates": {"Y10": 4.61, "S2s10s": 0.5, "asof": "07/28/2026"}}

        archive(pay, {"ES": rows}, t + 1200)
        f1 = os.path.join(tmpd, "bars", _day(t) + ".jsonl")
        got = [json.loads(x) for x in open(f1)]
        chk("arch.holds_back_open_bar", len(got), 3)
        chk("arch.first_ts", got[0]["t"], t)
        chk("arch.values", (got[2]["c"], got[2]["v"]), (102.5, 500.0))

        # same cycle again: nothing new, and the open bar still is not written
        archive(pay, {"ES": rows}, t + 1200)
        chk("arch.idempotent", len(open(f1).read().strip().split("\n")), 3)

        # next cycle: the bar that was open has closed, one more appears
        rows2 = rows + [mk(4)]
        archive(pay, {"ES": rows2}, t + 1800)
        got = [json.loads(x) for x in open(f1)]
        chk("arch.appends_on_close", [g["t"] for g in got], [t + i * 300 for i in range(4)])

        # a bar that crosses midnight UTC lands in the next day's file
        tm = int(datetime.datetime(2026, 7, 31, 23, 55, tzinfo=UTC).timestamp())
        archive(pay, {"RTY": [[tm, 1, 2, 0, 1.5, 9.0], [tm + 300, 1, 2, 0, 1.5, 9.0],
                              [tm + 600, 1, 2, 0, 1.5, 9.0]]}, tm + 900)
        chk("arch.day_rollover", sorted(os.listdir(os.path.join(tmpd, "bars"))),
            ["2026-07-30.jsonl", "2026-07-31.jsonl", "2026-08-01.jsonl"])

        q = os.path.join(tmpd, "quotes", _day(t) + ".jsonl")
        qrows = [json.loads(x) for x in open(q)]
        # five archive() calls above, but the sampler only writes on the 5-minute
        # grid: the repeat call at t+1200 is skipped, t+1800 is not.
        chk("arch.quote_sampled_on_grid", [r["t"] for r in qrows], [t + 1200, t + 1800])
        chk("arch.quote_drops_null", sorted(qrows[0]["q"]), ["ES", "VIX"])
        chk("arch.quote_keeps_curve", qrows[0]["y"], {"Y10": 4.61, "S2s10s": 0.5})

        # state survives a restart: reload from disk, nothing re-appended
        archive(pay, {"ES": rows2}, t + 2400)
        chk("arch.state_persists", len(open(f1).read().strip().split("\n")), 4)
    finally:
        ARCH, STATE, _QUIET = keep
        shutil.rmtree(tmpd, ignore_errors=True)

    # calendar: the shape the live feed actually returns, plus every way it can
    # be wrong. now = 2026-07-30 12:00 UTC.
    cnow = datetime.datetime(2026, 7, 30, 12, 0, tzinfo=UTC).timestamp()
    cbody = json.dumps([
        {"title": "Core PCE Price Index m/m", "country": "USD",
         "date": "2026-07-30T08:30:00-04:00", "impact": "High",
         "forecast": "0.3%", "previous": "0.2%"},
        {"title": "Advance GDP q/q", "country": "USD",
         "date": "2026-07-30T08:30:00-04:00", "impact": "High",
         "forecast": "2.1%", "previous": "3.8%"},
        {"title": "Core PCE Price Index m/m", "country": "USD",      # dupe
         "date": "2026-07-30T08:30:00-04:00", "impact": "High"},
        {"title": "  Unemployment   Claims ", "country": "USD",      # sloppy spacing
         "date": "2026-07-30T08:30:00-04:00", "impact": "Medium", "forecast": ""},
        {"title": "SPPI y/y", "country": "JPY",                      # too small
         "date": "2026-07-31T00:00:00-04:00", "impact": "Low"},
        {"title": "Cash Rate", "country": "AUD",                     # wrong currency
         "date": "2026-07-31T00:30:00-04:00", "impact": "High"},
        {"title": "Bank Holiday", "country": "GBP",                  # not an event
         "date": "2026-08-03T00:00:00-04:00", "impact": "Holiday"},
        {"title": "Long gone", "country": "USD",                     # outside the window
         "date": "2026-07-20T08:30:00-04:00", "impact": "High"},
        {"title": "Far future", "country": "USD",
         "date": "2027-07-20T08:30:00-04:00", "impact": "High"},
        {"title": "No date", "country": "USD", "date": "", "impact": "High"},
        "not even a dict",
    ])
    cev = parse_calendar(cbody, cnow)
    chk("cal.kept", [e["n"] for e in cev],
        ["Advance GDP q/q", "Core PCE Price Index m/m", "Unemployment Claims"])
    chk("cal.utc", cev[0]["t"], "2026-07-30T12:30:00Z")
    chk("cal.impact", [e["i"] for e in cev], [3, 3, 2])
    chk("cal.forecast", cev[1]["f"], "0.3%")
    chk("cal.blank_forecast_dropped", "f" in cev[2], False)
    chk("cal.sorted", cev == sorted(cev, key=lambda e: (e["e"], e["n"])), True)
    # a past event inside the look-back window is kept, so the board can say what
    # just landed rather than pretending the morning never happened
    chk("cal.recent_past", len(parse_calendar(json.dumps([
        {"title": "Just landed", "country": "USD", "impact": "High",
         "date": "2026-07-30T04:00:00-04:00"}]), cnow)), 1)
    chk("cal.garbage", parse_calendar("<html>404</html>", cnow), [])
    chk("cal.not_a_list", parse_calendar('{"error":"nope"}', cnow), [])
    chk("cal.empty", parse_calendar("[]", cnow), [])
    chk("iso.offset", iso_epoch("2026-07-30T08:30:00-04:00"), cnow + 1800)
    chk("iso.zulu", iso_epoch("2026-07-30T12:30:00Z"), cnow + 1800)
    chk("iso.naive_is_utc", iso_epoch("2026-07-30T12:30:00"), cnow + 1800)
    chk("iso.junk", iso_epoch("next tuesday"), None)
    chk("iso.none", iso_epoch(None), None)
    # cadence: a missing file is always due, a just-written one is not, and one
    # older than the interval is again
    chk("cal.due_when_absent", cal_due("/nonexistent/waft/calendar.json", time.time()), True)
    cfd, cpath = tempfile.mkstemp(prefix="waft-cal-")
    os.close(cfd)
    try:
        chk("cal.not_due_when_fresh", cal_due(cpath, time.time()), False)
        chk("cal.due_when_stale", cal_due(cpath, time.time() + CAL_EVERY + 1), True)
    finally:
        os.unlink(cpath)

    chk("num.comma", num("1,234.5"), 1234.5)
    chk("num.nan", num(float("nan")), None)
    chk("num.junk", num("N/D"), None)

    print("self-test: %d checks, %d failed" % (ran[0], len(fails)))
    for f in fails:
        print("   FAIL " + f)
    return 1 if fails else 0


if "--selftest" in sys.argv:
    sys.exit(selftest())


# ---------------------------------------------------------------------- main ---
def main():
    t0 = time.time()
    now = time.time()
    if selftest():
        log("parsers failed self-test - refusing to publish")
        return 2

    quotes, bars = {}, {}
    try:
        quotes, bars = fetch_yahoo(now)
        log("yahoo: %d quotes, %d bar series" % (len(quotes), len(bars)))
    except Exception as e:
        log("yahoo FAILED: %s: %s" % (type(e).__name__, e))

    cnbc = {}
    try:
        cnbc = fetch_cnbc(now)
        log("cnbc: %d quotes" % len(cnbc))
    except Exception as e:
        log("cnbc FAILED: %s" % type(e).__name__)

    quotes = merge(quotes, cnbc)
    rates = fetch_rates(now)

    # Slow-moving, so it gets its own cadence rather than riding every cycle.
    cal = None
    if cal_due(os.path.join(DATA, "latest", "calendar.json"), now):
        try:
            cal = fetch_calendar(now) or None
            log("calendar: %s" % ("%d events" % len(cal) if cal
                                  else "parsed empty - keeping the previous file"))
        except Exception as e:
            log("calendar FAILED: %s: %s - keeping the previous file" % (type(e).__name__, e))

    fresh = [q["age_s"] for k, q in quotes.items()
             if k in ("ES", "RTY") and q.get("age_s") is not None]
    payload = {
        "ts": datetime.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ts_epoch": int(now),
        "quotes": quotes,
        "rates": rates,
        "meta": {
            "sources": {"us_index": "yahoo_delayed", "vix": "cnbc", "rates": "treasury.gov"},
            "futures_age_s": min(fresh) if fresh else None,
            "note": "US index futures are exchange-delayed ~15min. Overnight ranges and "
                    "levels are unaffected by the delay; the last tick is.",
            "took_s": round(time.time() - t0, 1),
        },
    }
    if not quotes:
        # Never overwrite good data with an empty file. A transient Yahoo outage
        # should leave the last known-good quotes standing, not blank them.
        log("no quotes this cycle - leaving the previous free.json in place")
        return 1

    okpush = publish(payload, bars, now, cal)
    log("done: %d quotes, %d rate tenors, futures_age=%ss, push=%s, %.1fs"
        % (len(quotes), max(0, len(rates) - 2), payload["meta"]["futures_age_s"],
           "ok" if okpush else "deferred", time.time() - t0))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log("FATAL %s: %s" % (type(e).__name__, e))
        sys.exit(1)
