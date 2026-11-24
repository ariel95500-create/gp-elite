"""M5 review 1: the figures of the 1.5 parts of each English document and of
its French version, compared as multisets (French "1 381", "0,3" read as
"1,381", "0.3"). Reads text only.

    python3 -I en_fr_numbers.py <repo root>
"""
import collections
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def part(path, start, end):
    text = open(os.path.join(ROOT, path), encoding="utf-8").read()
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


def numbers(text, fr):
    t = text
    if fr:
        t = re.sub(r"(\d) (\d{3})", r"\1\2", t)        # 1 381 -> 1381
        t = re.sub(r"(\d),(\d)", r"\1.\2", t)          # 0,3 -> 0.3
    else:
        t = re.sub(r"(\d),(\d{3})", r"\1\2", t)        # 1,381 -> 1381
    # drop link targets and code paths, keep the prose and the table
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"`[^`]*`", "", t)
    return collections.Counter(re.findall(r"\d+(?:\.\d+)?", t))


PAIRS = [
    ("README note", "README.md", "README.fr.md", ("1.5 changes no model", "The structure of the law"),
     ("La 1.5 ne change aucun", "La structure de la loi")),
    ("architecture, whole", "docs/architecture.md", "docs/fr/architecture.md", ("Until 1.4.0", None),
     ("Jusqu'à la 1.4.0", None)),
    ("features, 1.5", "docs/features.md", "docs/fr/caracteristiques.md", ("**1.5**", "**1.4 "),
     ("**1.5**", "**1.4 ")),
    ("limits, note before point 1", "LIMITATIONS.md", "LIMITATIONS.fr.md", ("Version 1.5 changes", "## 1."),
     ("La version 1.5 ne change", "## 1.")),
    ("limits, point 9", "LIMITATIONS.md", "LIMITATIONS.fr.md", ("## 9.", "## 10."), ("## 9.", "## 10.")),
]
for label, en, fr, (s1, e1), (s2, e2) in PAIRS:
    a = numbers(part(en, s1, e1), fr=False)
    b = numbers(part(fr, s2, e2), fr=True)
    print("== %s: %d figures in English, %d in French" % (label, sum(a.values()), sum(b.values())))
    only_en = a - b
    only_fr = b - a
    print("   only in English:", dict(only_en) or "none")
    print("   only in French:", dict(only_fr) or "none")
