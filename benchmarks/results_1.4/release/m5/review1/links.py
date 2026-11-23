"""M5 review 1 (read-only): do the links and the paths named by the
documents of 1.4.0 exist in the working tree?

  python3 -I links.py REPO_ROOT

For each document (Markdown files, and the Markdown cells of the notebooks):
- every Markdown link [text](target): a relative target is resolved from the
  document's folder; a link to github.com/ariel95500-create/gp-elite (blob or
  tree, branch main), to raw.githubusercontent.com or to Colab is mapped to the
  working tree; other hosts are listed, not checked (no network);
- every path in backticks that looks like a repository path (it holds a "/"
  and starts with a known top folder, or ends in a known extension) is checked
  from the repository root and from the document's folder.
"""
import json
import os
import re
import sys

DOCS = ["README.md", "README.fr.md", "CHANGELOG.md", "LIMITATIONS.md", "LIMITATIONS.fr.md",
        "paper/paper.md", "docs/usage.md", "docs/units.md", "docs/robust.md",
        "docs/examples.md", "docs/measurements.md", "docs/features.md",
        "docs/fr/utilisation.md", "docs/fr/unites.md", "docs/fr/robuste.md",
        "docs/fr/exemples.md", "docs/fr/mesures.md", "docs/fr/caracteristiques.md",
        "examples/case_studies/README.md", "benchmarks/results_1.4/release/README.md",
        "benchmarks/results_1.1/DIAGNOSTIC_TP.md",
        "examples/tp_six_lois.ipynb", "examples/tp_regression_symbolique.ipynb",
        "examples/quickstart.ipynb", "examples/quickstart.fr.ipynb",
        "examples/case_studies/kepler_units.ipynb", "examples/case_studies/kepler_units.fr.ipynb",
        "examples/case_studies/hubble_1929.ipynb", "examples/case_studies/hubble_1929.fr.ipynb",
        "examples/case_studies/nikuradse_full.ipynb", "examples/case_studies/nikuradse_full.fr.ipynb"]
GH = [r"https://github\.com/ariel95500-create/gp-elite/(?:blob|tree)/main/([^)#\s]*)",
      r"https://raw\.githubusercontent\.com/ariel95500-create/gp-elite/main/([^)#\s]*)",
      r"https://colab\.research\.google\.com/github/ariel95500-create/gp-elite/blob/main/([^)#\s]*)"]
TOP = ("benchmarks/", "examples/", "docs/", "gp_elite/", "tests/", "paper/", "release_",
       "results_", "m2/", "m3/", "m4/", "l1/", "n2b/", "../")
EXT = (".md", ".py", ".txt", ".jsonl", ".ipynb", ".csv", ".json", ".sh", ".cff", ".png")


def text_of(path):
    if path.endswith(".ipynb"):
        nb = json.load(open(path, encoding="utf-8"))
        return "\n".join("".join(c.get("source", [])) for c in nb["cells"]
                         if c.get("cell_type") == "markdown")
    return open(path, encoding="utf-8").read()


def main(root):
    bad, other = [], set()
    for doc in DOCS:
        p = os.path.join(root, doc)
        t = text_of(p)
        if doc == "CHANGELOG.md":
            t = t.split("\n## 1.3.0")[0]
        here = os.path.dirname(p)
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", t):
            tgt = m.group(1)
            hit = None
            for g in GH:
                mm = re.match(g, tgt)
                if mm:
                    hit = os.path.join(root, mm.group(1))
            if hit is not None:
                if not os.path.exists(hit.rstrip("/") or root):
                    bad.append((doc, "link", tgt))
            elif re.match(r"https?://", tgt):
                other.add(tgt.split("#")[0])
            elif tgt.startswith("#"):
                pass
            else:
                q = os.path.normpath(os.path.join(here, tgt.split("#")[0]))
                if not os.path.exists(q):
                    bad.append((doc, "relative link", tgt))
        for m in re.finditer(r"`([^`\s]+)`", t):
            s = m.group(1).rstrip(".,;:)")
            if "/" not in s or "://" in s or s.startswith("/venv") or "*" in s:
                continue
            if not (s.startswith(TOP) or s.endswith(EXT) or s.endswith("/")):
                continue
            cands = [os.path.join(root, s), os.path.join(here, s),
                     os.path.join(root, "benchmarks", s),
                     os.path.join(root, "benchmarks/results_1.4/release", s)]
            if not any(os.path.exists(os.path.normpath(c)) for c in cands):
                bad.append((doc, "path in backticks", s))
    print("not found in the working tree:")
    for x in bad:
        print("  %-45s %-18s %s" % x)
    print("\nother hosts, not checked (no network): %d" % len(other))
    for o in sorted(other):
        print("  " + o)


if __name__ == "__main__":
    main(sys.argv[1])
