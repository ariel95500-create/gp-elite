"""L1 targeted verification: the TP and TPT10 models of the corrected wheel
against those of 1.4.0 in M2.

Every field of each record is compared except the three that describe the run
rather than the fit: the time, the date and the path of the engine file.
The plan expects the 800 records to be identical on every other field.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M2 = HERE.parent / "m2"
SKIP = {"time", "date", "engine_file"}
KEY = ("exp", "n", "noise", "draw", "arm")


def load(path):
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            k = tuple(r[f] for f in KEY)
            if k in out:
                raise SystemExit(f"duplicate record {k} in {path.name}")
            out[k] = r
    return out


def compare(name, measured, corrected):
    a, b = load(measured), load(corrected)
    lines = [f"{name}: {len(a)} records in M2 ({measured.name}), "
             f"{len(b)} with the corrected wheel ({corrected.name})"]
    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    if only_a:
        lines.append(f"  only in M2: {len(only_a)}, first {only_a[0]}")
    if only_b:
        lines.append(f"  only in the corrected run: {len(only_b)}, first {only_b[0]}")
    diffs = []
    for k in sorted(set(a) & set(b)):
        ra, rb = a[k], b[k]
        fields = sorted((set(ra) | set(rb)) - SKIP)
        bad = [f for f in fields if ra.get(f, "<absent>") != rb.get(f, "<absent>")]
        if bad:
            diffs.append((k, bad))
    for k, bad in diffs[:20]:
        lines.append(f"  differs {k}: {', '.join(bad)}")
        for f in bad[:3]:
            lines.append(f"    {f}: M2 {a[k].get(f, '<absent>')!r} / corrected "
                         f"{b[k].get(f, '<absent>')!r}")
    same = len(set(a) & set(b)) - len(diffs)
    lines.append(f"  identical on every field but time, date and engine file: "
                 f"{same} of {len(set(a) | set(b))}")
    versions = sorted({r.get("engine_version") for r in b.values()})
    files = sorted({r.get("engine_file") for r in b.values()})
    lines.append(f"  corrected run engine: {versions} {files}")
    ok = not (only_a or only_b or diffs)
    return ok, lines


def main():
    out = []
    all_ok = True
    for name, m2, l1 in (("TP", "tp_1.4.0.jsonl", "tp_l1.jsonl"),
                         ("TPT10", "tpt10_1.4.0.jsonl", "tpt10_l1.jsonl")):
        ok, lines = compare(name, M2 / m2, HERE / l1)
        all_ok &= ok
        out += lines
    out.append("ALL IDENTICAL" if all_ok else "DIFFERENCES FOUND")
    text = "\n".join(out) + "\n"
    (HERE / "compare_tp_l1.txt").write_text(text)
    sys.stdout.write(text)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
