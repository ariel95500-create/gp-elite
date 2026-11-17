"""M5 review 1 (read-only): the figures of the Nikuradse case study
(examples/case_studies/nikuradse_full*.ipynb, sections 4 and 5) read from the
five records of the M3 of 1.4 (m3/case_nikuradse/nikuradse_seed*.txt).

  python3 -I nikuradse_case.py benchmarks/results_1.4/release/m3/case_nikuradse
"""
import os
import re
import sys


def main(folder):
    allgaps = []
    for s in range(5):
        lines = open(os.path.join(folder, "nikuradse_seed%d.txt" % s),
                     encoding="utf-8").read().splitlines()
        champ = [l for l in lines if l.startswith("champion")]
        front, gen, part = [], [], 0
        for l in lines:
            if l.startswith("front de Pareto"):
                part = 1
            elif "rugosité r_k=" in l and "retirée" in l:
                part = 2
            m = re.match(r"\s+taille\s+(\d+)\s+R2=\s*(-?[\d.]+)\s+(.*)", l)
            if m and part == 1:
                front.append((int(m.group(1)), float(m.group(2)), m.group(3)[:60]))
            m = re.match(r"\s+taille\s+(\d+)\s+biais\s+([+-][\d.]+)s\s+R2=\s*(-?[\d.]+)\s+(.*)", l)
            if m and part == 2:
                gen.append((int(m.group(1)), float(m.group(2)), m.group(4)[:50]))
        pvk = [l for l in lines if "Prandtl-von Karman EXACTE :" in l]
        print("seed %d: %s" % (s, champ[0] if champ else "?"))
        print("   front starts: %s" % (front[:3],))
        print("   section 5: %d forms; gaps %+.3f to %+.3f; best |gap| %.3f; %s"
              % (len(gen), min(g for _, g, _ in gen), max(g for _, g, _ in gen),
                 min(abs(g) for _, g, _ in gen), pvk[0].strip() if pvk else ""))
        better = [(n, g) for n, g, _ in gen if abs(g) < 0.042]
        print("   forms with |gap| below 0.042 (PvK): %s" % better)
        allgaps += [g for _, g, _ in gen]
    print("all seeds: gaps from %+.3f to %+.3f" % (min(allgaps), max(allgaps)))


if __name__ == "__main__":
    main(sys.argv[1])
