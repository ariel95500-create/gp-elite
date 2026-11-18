"""Second review of M5 (1.4.0): do the French pages give the same figures as
the English ones?

  python3 -I fr_en_numbers.py

For each pair of pages, extracts the numbers (decimal comma read as a point,
thin and ordinary spaces inside a number and the thousands comma removed)
and prints those that appear a different number of times in the two pages.
Code blocks are kept: their numbers must agree too. A difference is a lead
to read, not a finding by itself.
"""
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
PAIRS = [("README.md", "README.fr.md"), ("LIMITATIONS.md", "LIMITATIONS.fr.md"),
         ("docs/usage.md", "docs/fr/utilisation.md"), ("docs/units.md", "docs/fr/unites.md"),
         ("docs/robust.md", "docs/fr/robuste.md"), ("docs/examples.md", "docs/fr/exemples.md"),
         ("docs/measurements.md", "docs/fr/mesures.md"),
         ("docs/features.md", "docs/fr/caracteristiques.md")]
NUM = re.compile(r"(?<![\w.])[-−]?\d+(?:[   ]\d{3})*(?:[.,]\d+)?(?:e[-+]?\d+)?")


def numbers(text):
    text = re.sub(r"\]\([^)]*\)", "]", text)          # drop link targets
    text = re.sub(r"https?://\S+", "", text)
    out = []
    for m in NUM.finditer(text):
        s = m.group(0).replace("−", "-")
        s = re.sub(r"[   ]", "", s)
        # 1,161 (English thousands) and 0,9979 (French decimal) are told apart
        # by the three digits after an English comma
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        s = s.replace(",", ".")
        out.append(s)
    return Counter(out)


for en, fr in PAIRS:
    a = numbers(open(os.path.join(REPO, en), encoding="utf-8").read())
    b = numbers(open(os.path.join(REPO, fr), encoding="utf-8").read())
    diff = sorted(set(a) | set(b), key=lambda s: (len(s), s))
    d = [(s, a[s], b[s]) for s in diff if a[s] != b[s]]
    print("== %s / %s: %s" % (en, fr, "same numbers" if not d else ""))
    for s, x, y in d:
        print("   %-14s EN %d  FR %d" % (s, x, y))
