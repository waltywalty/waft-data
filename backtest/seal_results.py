"""Move every "OOS_sealed*" block out of results/*.json into results/sealed/<name>.sealed.json.

Round 72A firewall finding (ledger 2026-09-12): the r42-r63 runners wrote the sealed
out-of-sample statistics next to the in-sample ones in the same JSON, so any agent that
opens an IS results file sees holdout numbers. This script leaves a marker string in place
of each block and stores the blocks under results/sealed/, which every agent prompt must
list as off-limits. Idempotent; run from backtest/.  --check only reports.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SEALED = os.path.join(RES, "sealed")
MARK = "SEALED: moved to results/sealed/ by seal_results.py (Round 72A firewall)"


def extract(obj, path, out):
    """Recursively replace OOS_sealed* keys with the marker; collect them into out[path]."""
    n = 0
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if isinstance(k, str) and k.startswith("OOS_sealed") and obj[k] != MARK:
                out["/".join(path + [k])] = obj[k]
                obj[k] = MARK
                n += 1
            else:
                n += extract(obj[k], path + [str(k)], out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            n += extract(v, path + [str(i)], out)
    return n


def main(check=False):
    os.makedirs(SEALED, exist_ok=True)
    total_files = total_blocks = 0
    for f in sorted(glob.glob(os.path.join(RES, "*.json"))):
        d = json.load(open(f))
        out = {}
        n = extract(d, [], out)
        if not n:
            continue
        total_files += 1; total_blocks += n
        name = os.path.basename(f)[:-5]
        if check:
            print(f"{name}: {n} block(s) would move"); continue
        sp = os.path.join(SEALED, name + ".sealed.json")
        prior = json.load(open(sp)) if os.path.exists(sp) else {}
        prior.update(out)
        json.dump(prior, open(sp, "w"), indent=1, default=str)
        json.dump(d, open(f, "w"), indent=1, default=str)
        print(f"{name}: moved {n} block(s) -> results/sealed/{name}.sealed.json")
    print(f"{'would move' if check else 'moved'} {total_blocks} blocks from {total_files} files")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
