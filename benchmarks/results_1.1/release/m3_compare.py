"""M3 of the second candidate against the first: python m3_compare.py FIRST_DIR SECOND_DIR.

Each record of M3 is compared with its counterpart once times, dates and the
paths of the environments and output folders are masked. A file listed as
"same" holds the same laws, formulas, errors, sizes and counts; the others are
printed line by line.
"""
import json
import os
import re
import sys

MASKS = [
    (re.compile(r"/venv11b?x?/"), "/venvX/"),
    (re.compile(r"/rel11(c2)?/"), "/relX/"),
    (re.compile(r"/work11(c2)?/"), "/workX/"),
    (re.compile(r'"seconds": \d+(\.\d+)?'), '"seconds": T'),
    (re.compile(r"\(\s*\d+(\.\d+)?\s*s\)"), "(T s)"),
    (re.compile(r"\b\d+(\.\d+)?\s?s\b"), "T s"),
    (re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d(\.\d+)?)?"), "DATE"),
]
TIME_KEYS = {"time", "date", "seconds", "elapsed", "t", "wall", "duration", "fit_s", "time_s"}


def mask(line):
    for pat, rep in MASKS:
        line = pat.sub(rep, line)
    return line


def strip_times(obj):
    if isinstance(obj, dict):
        return {k: strip_times(v) for k, v in obj.items() if k not in TIME_KEYS and not k.endswith(("_s", "_t"))}
    if isinstance(obj, list):
        return [strip_times(v) for v in obj]
    if isinstance(obj, str):
        return mask(obj)
    return obj


def lines(path):
    with open(path, errors="replace") as f:
        raw = f.read().splitlines()
    if path.endswith((".jsonl", ".json")):
        out = []
        for line in raw:
            try:
                out.append(json.dumps(strip_times(json.loads(line)), sort_keys=True))
            except ValueError:
                out.append(mask(line))
        return out
    return [mask(line) for line in raw]


def main(first, second):
    names = sorted(os.path.relpath(os.path.join(d, f), second)
                   for d, _, fs in os.walk(second) for f in fs)
    for name in names:
        a, b = os.path.join(first, name), os.path.join(second, name)
        if not os.path.exists(a):
            print("new      %s" % name)
            continue
        la, lb = lines(a), lines(b)
        if la == lb:
            print("same     %s" % name)
            continue
        print("differs  %s" % name)
        for i in range(max(len(la), len(lb))):
            x = la[i] if i < len(la) else "<none>"
            y = lb[i] if i < len(lb) else "<none>"
            if x != y:
                print("    first : %s" % x[:240])
                print("    second: %s" % y[:240])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
