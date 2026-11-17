"""M5 review 1 (read-only): the numbers of each English page against those of
its French version, as multisets, after the French decimal comma and the
spaces of thousands are normalised. A number that one page has and the
other has not is printed with its line, to be read by hand.

  python3 -I fr_en_numbers.py REPO_ROOT
"""
import os
import re
import sys
from collections import Counter

PAIRS = [("README.md", "README.fr.md"), ("LIMITATIONS.md", "LIMITATIONS.fr.md"),
         ("docs/usage.md", "docs/fr/utilisation.md"), ("docs/units.md", "docs/fr/unites.md"),
         ("docs/robust.md", "docs/fr/robuste.md"), ("docs/examples.md", "docs/fr/exemples.md"),
         ("docs/measurements.md", "docs/fr/mesures.md"),
         ("docs/features.md", "docs/fr/caracteristiques.md")]
NUM = re.compile(r"(?<![\w.])[-−+]?\d+(?:[.,]\d+)*(?:e[-+]?\d+)?%?")


def numbers(path):
    out = []
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        if "](" in line:     # link targets hold paths and versions, read the text only
            line = re.sub(r"\]\([^)]*\)", "]", line)
        line = re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", line)   # 1 161 -> 1161
        line = re.sub(r"(?<=\d),(?=\d)", ".", line) if path.find("/fr/") >= 0 or path.endswith(".fr.md") else line.replace(",", "")
        for m in NUM.finditer(line):
            v = m.group(0).replace("−", "-")
            out.append((v, i, line.strip()[:110]))
    return out


def main(root):
    for en, fr in PAIRS:
        ne, nf = numbers(os.path.join(root, en)), numbers(os.path.join(root, fr))
        ce, cf = Counter(v for v, _, _ in ne), Counter(v for v, _, _ in nf)
        only_e, only_f = ce - cf, cf - ce
        print("=== %s (%d numbers) / %s (%d numbers)" % (en, len(ne), fr, len(nf)))
        for v in sorted(only_e):
            lines = [(i, l) for x, i, l in ne if x == v][:2]
            print("  only in EN: %-10s x%d  %s" % (v, only_e[v], lines))
        for v in sorted(only_f):
            lines = [(i, l) for x, i, l in nf if x == v][:2]
            print("  only in FR: %-10s x%d  %s" % (v, only_f[v], lines))


if __name__ == "__main__":
    main(sys.argv[1])
