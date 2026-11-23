"""Second review of M5 (1.4.0): do the paths and links named in the documents
exist in the repository?

  python3 -I links.py

For each document: Markdown links (relative, or to the repository on GitHub
at blob/main or tree/main), and paths in backticks that name a file or a
folder of the repository (they start with benchmarks/, examples/, docs/,
gp_elite/, tests/ or paper/, or are relative to the document's folder, as
release/README.md writes them). Notebooks: their Markdown cells. Prints
every path that does not exist.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
GH = "https://github.com/ariel95500-create/gp-elite/"
RAW = "https://raw.githubusercontent.com/ariel95500-create/gp-elite/main/"
DOCS = ["README.md", "README.fr.md", "CHANGELOG.md", "LIMITATIONS.md", "LIMITATIONS.fr.md",
        "paper/paper.md", "docs/usage.md", "docs/units.md", "docs/robust.md",
        "docs/examples.md", "docs/measurements.md", "docs/features.md",
        "docs/fr/utilisation.md", "docs/fr/unites.md", "docs/fr/robuste.md",
        "docs/fr/exemples.md", "docs/fr/mesures.md", "docs/fr/caracteristiques.md",
        "benchmarks/results_1.4/release/README.md", "benchmarks/results_1.1/DIAGNOSTIC_TP.md",
        "examples/case_studies/README.md"]
NBS = ["examples/tp_six_lois.ipynb", "examples/tp_regression_symbolique.ipynb",
       "examples/quickstart.ipynb", "examples/quickstart.fr.ipynb",
       "examples/case_studies/kepler_units.ipynb", "examples/case_studies/kepler_units.fr.ipynb",
       "examples/case_studies/hubble_1929.ipynb", "examples/case_studies/hubble_1929.fr.ipynb",
       "examples/case_studies/nikuradse_full.ipynb",
       "examples/case_studies/nikuradse_full.fr.ipynb"]
LINK = re.compile(r"\]\(([^)\s]+)\)")
TICK = re.compile(r"`([^`\s]+)`")
ROOTS = ("benchmarks/", "examples/", "docs/", "gp_elite/", "tests/", "paper/")


def text_of(path):
    full = os.path.join(REPO, path)
    if path.endswith(".ipynb"):
        nb = json.load(open(full, encoding="utf-8"))
        return "\n".join("".join(c.get("source", [])) for c in nb["cells"]
                         if c.get("cell_type") == "markdown")
    return open(full, encoding="utf-8").read()


def exists(p):
    return os.path.exists(os.path.join(REPO, os.path.normpath(p)))


def check(doc):
    base = os.path.dirname(doc)
    txt = text_of(doc)
    if doc == "CHANGELOG.md":                     # the 1.4.0 entry only
        txt = txt.split("\n## 1.3.0", 1)[0]
    bad = []
    for m in LINK.finditer(txt):
        url = m.group(1).split("#")[0]
        if not url:
            continue
        if url.startswith(GH):
            rest = url[len(GH):]
            for pre in ("blob/main/", "tree/main/"):
                if rest.startswith(pre):
                    p = rest[len(pre):]
                    if not exists(p):
                        bad.append(("link", url))
        elif url.startswith(RAW):
            if not exists(url[len(RAW):]):
                bad.append(("link", url))
        elif "://" not in url and not url.startswith("mailto:"):
            if not exists(os.path.join(base, url)):
                bad.append(("link", url))
    for m in TICK.finditer(txt):
        t = m.group(1).rstrip(".,;:)")
        if "/" not in t or t.startswith(("/venv", "/tmp", "http")) or "*" in t:
            continue
        if any(c in t for c in "()=<>'\"[]{}|") or t.endswith("/") and False:
            continue
        cand = [t] if t.startswith(ROOTS) else [os.path.join(base, t), t]
        if not any(exists(c) for c in cand):
            bad.append(("path", t))
    return bad


for d in DOCS + NBS:
    b = check(d)
    print("%-48s %s" % (d, "ok" if not b else ""))
    for kind, x in b:
        print("    missing %s: %s" % (kind, x))
