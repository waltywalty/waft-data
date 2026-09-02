"""Forward auto-journal integrator (contract: forward/CONTRACT.md).

Collects rows from every leg, merges them into the journal artifact's state
(dedup key date|instr|note; hand-entered rows are never touched), writes the
updated page HTML for republishing, and prints the review summary the
scheduled check-ins report from.

Usage (cwd = backtest/):
  python3 forward/autojournal.py --journal <path to current journal html> \
      --out <path for updated html> [--data data/forward] [--dry]
"""
import argparse, importlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.dirname(HERE)
sys.path.insert(0, BT)
sys.path.insert(0, HERE)
os.chdir(BT)

LEGS = ["leg_xau", "leg_mhi", "leg_d7", "leg_pmi"]
# Forward evidence starts the day AFTER each stream's registration / archived data end.
# Rows dated earlier are backtest-window trades and are never journalled (see ledger,
# 2026-09-02 auto-journal protocol).
STREAM_START = {"XAU": "2026-08-27", "XAUAUD": "2026-08-27", "MHI": "2026-09-01",
                "D7": "2026-08-27", "PMI": "2026-09-02"}
STATE_RE = re.compile(r'(<script id="state" type="application/json">)(.*?)(</script>)', re.S)


def key(r):
    return f"{r['date']}|{r['instr']}|{r.get('note', '')}"


def collect(data_dir):
    rows, status, errors = [], {}, {}
    for name in LEGS:
        try:
            mod = importlib.import_module(name)
            got = mod.rows(data_dir) or []
            for r in got:
                r.setdefault("src", "auto")
                r.setdefault("note", "")
                for k in ("entry", "stop", "exit"):
                    r[k] = float(r[k])
            rows += got
            if hasattr(mod, "status"):
                status[name] = mod.status(data_dir)
        except Exception as e:  # a broken leg must not block the others
            errors[name] = f"{type(e).__name__}: {e}"
    return rows, status, errors


def merge(state, new_rows):
    have = {key(r) for r in state["trades"] if r.get("src") == "auto"}
    added = [r for r in new_rows if key(r) not in have]
    state["trades"] += added
    state["trades"].sort(key=lambda r: (r["date"], r["instr"]))
    return added


def sprt_lines(state):
    try:
        import sprt
    except Exception:
        return []
    out = []
    for ins in ("XAU", "XAUAUD", "MHI", "D7"):
        seq = ["W" if (1 if r["side"] == "L" else -1) * (r["exit"] - r["entry"]) > 0 else "L"
               for r in state["trades"] if r["instr"] == ins]
        if not seq or ins not in sprt.STREAMS:
            continue
        llr, st = sprt.score(ins, seq)
        out.append(f"{ins}: n {len(seq)}, W {seq.count('W')}, LLR {llr:+.2f} -> {st} "
                   f"(promote >= {sprt.A:+.2f}, kill <= {sprt.B:+.2f})")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data", default="data/forward")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    html = open(a.journal).read()
    m = STATE_RE.search(html)
    if not m:
        sys.exit("journal html has no state block")
    state = json.loads(m.group(2))
    before = len(state["trades"])

    rows, status, errors = collect(a.data)
    pre = [r for r in rows if r["date"] < STREAM_START.get(r["instr"], "0000")]
    rows = [r for r in rows if r["date"] >= STREAM_START.get(r["instr"], "0000")]
    added = merge(state, rows)

    per = {}
    for r in added:
        per[r["instr"]] = per.get(r["instr"], 0) + 1
    pre_per = {}
    for r in pre:
        pre_per[r["instr"]] = pre_per.get(r["instr"], 0) + 1
    print(f"pre-stream rows ignored: {len(pre)} "
          f"({', '.join(f'{k} {v}' for k, v in sorted(pre_per.items())) or 'none'})")
    print(f"legs: {len(rows)} candidate rows, {len(added)} new "
          f"({', '.join(f'{k} +{v}' for k, v in sorted(per.items())) or 'none'}); "
          f"journal {before} -> {len(state['trades'])} rows")
    for k, v in status.items():
        print(f"status {k}: {v}")
    for k, v in errors.items():
        print(f"ERROR {k}: {v}")
    for line in sprt_lines(state):
        print("sprt", line)
    for r in added:
        p = (1 if r["side"] == "L" else -1) * (r["exit"] - r["entry"])
        print(f"  + {r['date']} {r['instr']:<6} {r['side']} {r['entry']:.2f} -> {r['exit']:.2f} "
              f"{p:+.2f} {r.get('note', '')}")

    if a.dry:
        return
    new_html = html[:m.start(2)] + json.dumps(state) + html[m.end(2):]
    open(a.out, "w").write(new_html)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
