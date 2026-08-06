#!/usr/bin/env python3
"""WaFT data relay — pulls Webull market data and pushes it to a private GitHub repo.

Runs once per invocation (cron calls it every minute). Data-only: imports only the
SDK's data client; no trade endpoints are ever touched.
"""
import os, sys, json, csv, subprocess, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE / "data"          # the git repo checkout that gets pushed
CONF = BASE / "config.env"

def load_env(path):
    env = {}
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

env = load_env(CONF)
APP_KEY = env["WEBULL_APP_KEY"]
APP_SECRET = env["WEBULL_APP_SECRET"]
REGION = env.get("WEBULL_REGION", "hk")
US_SYMBOLS = [s.strip() for s in env.get("US_SYMBOLS", "SPY,IWM,QQQ,DIA").split(",") if s.strip()]
HK_SYMBOLS = [s.strip() for s in env.get("HK_SYMBOLS", "").split(",") if s.strip()]
BAR_COUNT = env.get("BAR_COUNT", "120")

os.environ.setdefault("WEBULL_OPENAPI_TOKEN_DIR", str(BASE / "token"))

from webull.core.client import ApiClient
from webull.data.data_client import DataClient
from webull.data.common.category import Category
from webull.data.common.timespan import Timespan

now = datetime.datetime.now(datetime.timezone.utc)
stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
today = now.strftime("%Y%m%d")

status = {"ts": stamp, "ok": [], "errors": []}
quotes = {"ts": stamp, "symbols": {}}

api = ApiClient(APP_KEY, APP_SECRET, REGION)
dc = DataClient(api)

def fetch_symbol(sym, category):
    try:
        r = dc.market_data.get_snapshot(sym, category)
        if r.status_code == 200:
            payload = r.json()
            quotes["symbols"][sym] = {"category": category, "snapshot": payload}
            status["ok"].append(f"snap:{sym}")
        else:
            status["errors"].append(f"snap:{sym}:{r.status_code}:{str(r.text)[:120]}")
    except Exception as e:
        status["errors"].append(f"snap:{sym}:EXC:{str(e)[:120]}")
    try:
        r = dc.market_data.get_history_bar(sym, category, Timespan.M1.name, count=BAR_COUNT)
        if r.status_code == 200:
            bars = r.json()
            out = DATA / "bars" / f"{sym}_1m_{today}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"ts": stamp, "symbol": sym, "bars": bars}))
            status["ok"].append(f"bars:{sym}")
        else:
            status["errors"].append(f"bars:{sym}:{r.status_code}:{str(r.text)[:120]}")
    except Exception as e:
        status["errors"].append(f"bars:{sym}:EXC:{str(e)[:120]}")

for sym in US_SYMBOLS:
    fetch_symbol(sym, Category.US_STOCK.name)
for sym in HK_SYMBOLS:
    fetch_symbol(sym, Category.HK_STOCK.name)

(DATA / "latest").mkdir(parents=True, exist_ok=True)
(DATA / "meta").mkdir(parents=True, exist_ok=True)
(DATA / "latest" / "quotes.json").write_text(json.dumps(quotes, indent=1))
(DATA / "meta" / "status.json").write_text(json.dumps(status, indent=1))

# --- git push ---
def git(*args):
    return subprocess.run(["git", "-C", str(DATA)] + list(args),
                          capture_output=True, text=True, timeout=60)

git("add", "-A")
c = git("commit", "-m", f"waft {stamp} ok={len(status['ok'])} err={len(status['errors'])}")
p = git("push", "origin", "main")
if p.returncode != 0:
    sys.stderr.write("git push failed: " + p.stderr[-300:] + "\n")
    sys.exit(1)
print(f"{stamp} ok={len(status['ok'])} err={len(status['errors'])}")
