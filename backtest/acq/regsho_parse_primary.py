"""Parse the primary-source Reg SHO pulls fetched through the Kernel VM (2026-09-09).

Inputs (this directory, written by the VM loops in vm_bootstrap.sh):
  ftd_all.csv  SEC fails-to-deliver, basket-filtered: settlement_date(YYYYMMDD),cusip,symbol,quantity,price
               (SEC half-month files cnsfailsYYYYMM[ab].zip; QUANTITY = outstanding fail balance on the
               settlement date; PRICE = prior close as published; rows only exist where a fail exists)
  shv_all.csv  FINRA daily Reg SHO short-volume, basket-filtered: date(YYYYMMDD),symbol,short,exempt,total,market-list
               (one row per symbol per date; the Market field is a comma list such as B,Q,N, so it spills into extra CSV columns)
Outputs:
  ftd/<SYMBOL>.csv   settlement_date,quantity,price            (one row per settlement date with a fail)
  shv/<SYMBOL>.csv   date,short_volume,short_exempt_volume,total_volume,short_pct   (facilities summed)
Signal-side only: nothing here touches returns.
"""
import csv, os, sys
from collections import defaultdict

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "regsho")  # gitignored data dir


def norm_sym(s):
    s = s.strip().upper()
    return {"BRK.B": "BRKB", "BRK B": "BRKB", "BRK-B": "BRKB"}.get(s, s)


def parse_ftd():
    path = os.path.join(HERE, "ftd_all.csv")
    if not os.path.exists(path):
        return 0
    rows = defaultdict(dict)
    n = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or line.startswith("SETTLEMENT"):
                continue
            p = line.split(",")
            if len(p) < 5 or not p[0].isdigit():
                continue
            d, cusip, sym, qty, px = p[0], p[1], norm_sym(p[2]), p[3], p[4]
            date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            try:
                qty = int(qty); px = float(px) if px not in ("", ".") else float("nan")
            except ValueError:
                continue
            # a symbol can appear twice on one settlement date across CUSIPs (re-listings); keep the larger
            if date not in rows[sym] or qty > rows[sym][date][0]:
                rows[sym][date] = (qty, px)
            n += 1
    os.makedirs(os.path.join(HERE, "ftd"), exist_ok=True)
    for sym, d in rows.items():
        with open(os.path.join(HERE, "ftd", f"{sym}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["settlement_date", "quantity", "price"])
            for date in sorted(d):
                w.writerow([date, d[date][0], d[date][1]])
    return n


def parse_shv():
    path = os.path.join(HERE, "shv_all.csv")
    if not os.path.exists(path):
        return 0
    agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    n = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            p = line.split(",")
            if len(p) < 5 or not p[0].isdigit():
                continue
            d, sym = p[0], norm_sym(p[1])
            date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            try:   # 2026 files carry fractional share volumes (FINRA's own file does); keep as float
                s, e, t = float(p[2]), float(p[3]), float(p[4])
            except ValueError:
                continue
            a = agg[sym][date]; a[0] += s; a[1] += e; a[2] += t   # one row per date/symbol; Market is a list (B,Q,N)
            n += 1
    os.makedirs(os.path.join(HERE, "shv"), exist_ok=True)
    for sym, d in agg.items():
        with open(os.path.join(HERE, "shv", f"{sym}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "short_volume", "short_exempt_volume", "total_volume", "short_pct"])
            for date in sorted(d):
                s, e, t = d[date]
                w.writerow([date, round(s, 3), round(e, 3), round(t, 3), round(100.0 * s / t, 2) if t else ""])
    return n


if __name__ == "__main__":
    nf = parse_ftd(); ns = parse_shv()
    print(f"ftd rows {nf}, symbols {len(os.listdir(os.path.join(HERE,'ftd'))) if os.path.isdir(os.path.join(HERE,'ftd')) else 0}")
    print(f"shv rows {ns}, symbols {len(os.listdir(os.path.join(HERE,'shv'))) if os.path.isdir(os.path.join(HERE,'shv')) else 0}")
