"""Second review of M5 (1.4.0): did the longer sections of the README move to
docs/ without being cut (PLAN_RELEASE_1.4.md, "Documents")?

  python3 -I readme_moved.py [OLD_COMMIT]

Reads README.md and README.fr.md at OLD_COMMIT (default ec44e8e, the last
commit before the short README) with git show, splits them into paragraphs,
and looks for each one in the README and the pages of docs/ (docs/fr/ for
the French) of the working tree, by the best difflib ratio. Prints the
paragraphs whose best match is below 0.9, with the match.
"""
import difflib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
OLD = sys.argv[1] if len(sys.argv) > 1 else "ec44e8e"


def paras(text):
    out = []
    for p in re.split(r"\n\s*\n", text):
        p = " ".join(p.split())
        if len(p) > 60:
            out.append(p)
    return out


def new_paras(files):
    out = []
    for f in files:
        out += paras(open(os.path.join(REPO, f), encoding="utf-8").read())
    return out


for old_name, files in (
        ("README.md", ["README.md", "docs/usage.md", "docs/units.md", "docs/robust.md",
                       "docs/examples.md", "docs/measurements.md", "docs/features.md",
                       "LIMITATIONS.md"]),
        ("README.fr.md", ["README.fr.md", "docs/fr/utilisation.md", "docs/fr/unites.md",
                          "docs/fr/robuste.md", "docs/fr/exemples.md", "docs/fr/mesures.md",
                          "docs/fr/caracteristiques.md", "LIMITATIONS.fr.md"])):
    old = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (OLD, old_name)],
                         capture_output=True, text=True, check=True).stdout
    news = new_paras(files)
    print("=== %s at %s: %d paragraphs" % (old_name, OLD, len(paras(old))))
    for p in paras(old):
        best, bp = 0.0, ""
        for q in news:
            sm = difflib.SequenceMatcher(None, p, q, autojunk=False)
            if sm.real_quick_ratio() < best or sm.quick_ratio() < best:
                continue
            r = sm.ratio()
            if r > best:
                best, bp = r, q
        if best < 0.9:
            print("\n-- best %.2f\n   OLD: %s\n   NEW: %s" % (best, p[:700], bp[:700]))
