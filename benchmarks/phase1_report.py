"""Tables of a phase 1 measurement (benchmarks/phase1_bench.py), as Markdown.

Usage, from the repository root:
  python benchmarks/phase1_report.py benchmarks/results_0.9/baseline_0.8.0.jsonl
"""
import json
import sys
from collections import Counter, defaultdict

import numpy as np

FEYN_LIKE = [("F41", "feyn", None), ("F41N1", "feyn_n1", None),
             ("F41N10", "feyn_n10", None), ("TF78", "tf", None),
             ("TF78 main", "tf", "main"), ("TF78 bonus", "tf", "bonus"),
             ("TS14 test", "ts", "test"), ("TS14 ood", "ts", "ood")]
REAL_LIKE = [("R6", "real"), ("R7raw", "realraw"), ("TR25", "tr"),
             ("TR25raw", "trraw"), ("TS14", "ts")]
BUDGET = 30.0


def _med(v):
    v = [x for x in v if x is not None and np.isfinite(x)]
    return float(np.median(v)) if v else float("nan")


def _g(x):
    return "%.3g" % x if np.isfinite(x) else "n/a"


def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def feyn_rows(recs, kind, sel):
    rr = [r for r in recs if r["kind"] == kind]
    if kind == "tf" and sel:
        rr = [r for r in rr if r.get("family") == sel]
    if kind == "ts":
        rr = [r for r in rr if r["split"] == sel and "status" in r]
    return rr


def run_facts(recs):
    c = Counter
    out = ["| | |", "|---|---|"]
    out.append("| fits recorded | %d |" % len(recs))
    out.append("| crashes | %d |" % sum(1 for r in recs if r.get("status") == "CRASH"))
    for k in ("engine_version", "python", "numpy", "sklearn", "avx512",
              "npy_disable", "pythonhashseed"):
        vals = c(str(r.get(k)) for r in recs if r.get("status") != "CRASH")
        out.append("| %s | %s |" % (k, ", ".join("%s (%d)" % kv for kv in
                                                  sorted(vals.items()))))
    dates = sorted(r["date"] for r in recs if "date" in r)
    if dates:
        out.append("| first and last record | %s to %s |" % (dates[0], dates[-1]))
    return "\n".join(out)


def feyn_table(recs):
    out = ["| suite | fits | EXACT | NEAR | MISS | structure retrieved | "
           "median 1−R² | median time (s) | beyond budget, median / max (s) | "
           "median generations | formula_exact False |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, kind, sel in FEYN_LIKE:
        rr = feyn_rows(recs, kind, sel)
        if not rr:
            continue
        st = Counter(r.get("status") for r in rr)
        struct = ("%d" % sum(1 for r in rr if r.get("structure"))
                  if any("structure" in r for r in rr) else "")
        over = [r["time"] - BUDGET for r in rr if r.get("time_limit_reached")]
        out.append("| %s | %d | %d | %d | %d | %s | %s | %.1f | %s / %s | %.0f | %d |" % (
            name, len(rr), st["EXACT"], st["NEAR"], st["MISS"] + st["CRASH"],
            struct, _g(_med([r["err"] for r in rr])),
            _med([r["time"] for r in rr]),
            "%.2f" % _med(over) if over else "n/a",
            "%.2f" % max(over) if over else "n/a",
            _med([r.get("generations") for r in rr]),
            sum(1 for r in rr if r.get("formula_exact") is False)))
    return "\n".join(out)


def family_table(recs, kind="feyn"):
    by = defaultdict(list)
    for r in recs:
        if r["kind"] == kind:
            by[r.get("family", "?")].append(r)
    out = ["| family | equations | fits | EXACT | NEAR |", "|---|---|---|---|---|"]
    for fam in sorted(by):
        rr = by[fam]
        st = Counter(r.get("status") for r in rr)
        out.append("| %s | %d | %d | %d | %d |" % (
            fam, len({r["problem"] for r in rr}), len(rr), st["EXACT"], st["NEAR"]))
    return "\n".join(out)


def ood_table(recs):
    out = ["| suite | models not exact | median 1−R² out of domain | "
           "collapses (R² < 0) | worst R² |", "|---|---|---|---|---|"]
    for name, kind, sel in FEYN_LIKE:
        if kind == "ts":
            continue
        rr = [r for r in feyn_rows(recs, kind, sel)
              if r.get("status") != "EXACT" and "err_ood" in r]
        if not rr:
            continue
        e = [r["err_ood"] for r in rr]
        out.append("| %s | %d | %s | %d | %s |" % (
            name, len(rr), _g(_med(e)), sum(1 for x in e if x > 1.0),
            _g(1.0 - max(e))))
    return "\n".join(out)


def real_table(recs):
    out = ["| suite | split | fits | median R² | mean R² | collapses (R² < 0) | "
           "worst R² | formula_exact False |", "|---|---|---|---|---|---|---|---|"]
    for name, kind in REAL_LIKE:
        for split, pred in (("folds", lambda s: s.startswith("fold")),
                            ("test", lambda s: s == "test"),
                            ("out of domain", lambda s: s == "ood")):
            rr = [r for r in recs if r["kind"] == kind and pred(r["split"])]
            if not rr:
                continue
            r2 = np.array([r["r2"] for r in rr], dtype=float)
            out.append("| %s | %s | %d | %.3f | %.3g | %d | %s | %d |" % (
                name, split, len(rr), np.median(r2), np.mean(r2),
                int((r2 < 0).sum()), _g(r2.min()),
                sum(1 for r in rr if r.get("formula_exact") is False)))
    return "\n".join(out)


def main(path):
    recs = load(path)
    print("## Run\n")
    print(run_facts(recs))
    print("\n## Laws: decision bench, noise and frozen test set\n")
    print(feyn_table(recs))
    print("\n## F41 by family\n")
    print(family_table(recs, "feyn"))
    print("\n## Out of domain, models that are not exact\n")
    print(ood_table(recs))
    print("\n## Real data and Strogatz, R² on the test rows\n")
    print(real_table(recs))


if __name__ == "__main__":
    main(sys.argv[1])
