"""Second review of M5: every path quoted in the added lines of the documents
since 5492296, checked against the tree (read-only).

python3 -I r7_paths.py
"""
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 5))
DOCS = ["README.md", "README.fr.md", "CHANGELOG.md", "LIMITATIONS.md", "LIMITATIONS.fr.md",
        "paper/paper.md", "benchmarks/results_1.1/DIAGNOSTIC_TP.md",
        "benchmarks/results_1.1/ROADMAP.md",
        "benchmarks/results_1.3/release/README.md",
        "benchmarks/results_1.3/release/m2/examine/README.md",
        "benchmarks/results_1.3/release/m3/examine/README.md",
        "examples/tp_six_lois.ipynb", "examples/tp_regression_symbolique.ipynb"]
PAT = re.compile(r"`([^`\s]+)`|\]\((https://github.com/[^)]+)\)")


def added_lines(doc):
    out = subprocess.run(["git", "-C", ROOT, "diff", "-U0", "5492296", "HEAD", "--", doc],
                         capture_output=True, text=True).stdout
    return [ln[1:] for ln in out.splitlines() if ln.startswith("+") and not ln.startswith("+++")]


def candidates(doc, text):
    base = os.path.dirname(os.path.join(ROOT, doc))
    for m in PAT.finditer(text):
        p = m.group(1) or m.group(2)
        if p.startswith("https://github.com/ariel95500-create/gp-elite/"):
            p = re.sub(r"^https://github.com/ariel95500-create/gp-elite/(tree|blob)/main/", "", p)
            yield p, [os.path.join(ROOT, p)]
            continue
        if "/" not in p or p.startswith("http") or "(" in p or "=" in p:
            continue
        p = p.rstrip(".,;:)")
        tries = [os.path.join(base, p), os.path.join(ROOT, p)]
        # paths quoted relative to a folder the text names, e.g. m2/..., m3/...
        for sub in ("benchmarks/results_1.3/release", "benchmarks/results_1.3",
                    "benchmarks/results_1.1", "benchmarks"):
            tries.append(os.path.join(ROOT, sub, p))
        yield p, tries


for doc in DOCS:
    lines = added_lines(doc) if doc != "benchmarks/results_1.1/ROADMAP.md" else \
        open(os.path.join(ROOT, doc)).read().splitlines()
    text = "\n".join(lines)
    seen = set()
    for p, tries in candidates(doc, text):
        if p in seen:
            continue
        seen.add(p)
        ok = [t for t in tries if os.path.exists(t)]
        first = os.path.exists(tries[0])
        print("%-5s %-45s %s%s" % ("ok" if ok else "MISS", doc, p,
                                  "" if first or not ok else "   (not relative to the document; found at %s)"
                                  % os.path.relpath(ok[0], ROOT)))
