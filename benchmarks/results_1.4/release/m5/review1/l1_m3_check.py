"""M5 review 1 (read-only): the records of M3 and of the verification of L1
read against what the release README, the CHANGELOG and the docs say.

  python3 -I l1_m3_check.py benchmarks

- l1/count_l1.jsonl against m4/log_scan/count.jsonl, job by job, and where
  the noise-tolerant stage runs by suite (with the status of the F41 fits in
  M2, to see whether it runs on fits whose law comes back exact);
- the counts of l1/m3_compare_release_vs_l1.txt and of
  m3_compare_1.3.0_vs_1.4.0.txt (same / differs / new);
- the small-data check and the scaling bench of M3 against the M3 of 1.3;
- the six fits of the TP notebook, in each run of M3.
"""
import json
import os
import re
import sys
from collections import Counter


def main(bench):
    rel = os.path.join(bench, "results_1.4", "release")
    key = lambda r: tuple(r.get(x) for x in ("set", "kind", "problem", "split", "seed",
                                             "exp", "n", "noise", "draw", "arm"))
    m4 = {key(r): (r["stage_ran"], tuple(r["errors"])) for r in
          map(json.loads, open(os.path.join(rel, "m4/log_scan/count.jsonl"), encoding="utf-8"))}
    l1 = {key(r): (r["stage_ran"], tuple(r["errors"])) for r in
          map(json.loads, open(os.path.join(rel, "l1/count_l1.jsonl"), encoding="utf-8"))}
    print("count: %d and %d jobs, same keys %s, the same record in %d; errors in %d and %d"
          % (len(m4), len(l1), set(m4) == set(l1), sum(m4[k] == l1.get(k) for k in m4),
             sum(bool(v[1]) for v in m4.values()), sum(bool(v[1]) for v in l1.values())))
    runs = Counter((k[1], v[0]) for k, v in l1.items() if k[0] == "bench")
    print("the stage runs, by suite: " + ", ".join(
        "%s %d/%d" % (s, runs[(s, True)], runs[(s, True)] + runs[(s, False)])
        for s in sorted({k[1] for k in l1 if k[0] == "bench"})))
    m2 = {}
    for line in open(os.path.join(rel, "m2/campaignR_1.4.0.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        m2[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    f41 = Counter()
    one_gen = Counter()
    for k, r in m2.items():
        if k[0] != "feyn":
            continue
        ran = l1[("bench",) + k + (None,) * 5][0]
        f41[(ran, r["status"] == "EXACT")] += 1
        if ran and r["status"] == "EXACT" and r.get("generations", 99) <= 1:
            one_gen[k[1]] += 1
    print("F41 (stage runs, exact in M2): %s" % dict(f41))
    print("F41 fits exact in one generation where the stage runs, by equation: %s" % dict(one_gen))

    for name in ("l1/m3_compare_release_vs_l1.txt", "m3_compare_1.3.0_vs_1.4.0.txt"):
        c = Counter(l.split()[0] for l in open(os.path.join(rel, name), encoding="utf-8")
                    if re.match(r"^(same|differs|new)\s", l))
        print("%s: %s" % (name, dict(c)))

    for v in ("1.3", "1.4"):
        rows = [json.loads(l) for l in open(os.path.join(
            bench, "results_%s/release/m3/small_data_release.jsonl" % v), encoding="utf-8")]
        print("small data %s, 2.5 exp(-0.7x) + 0.3: %s" % (v, [
            (r["seed"], r["size"], r["expr"], r["r2_test"]) for r in rows
            if r.get("law") == "2.5 exp(-0.7x) + 0.3"]))
    for v in ("1.3", "1.4"):
        txt = open(os.path.join(bench, "results_%s/release/m3/scaling.txt" % v), encoding="utf-8").read()
        for n in ("1000", "10000"):
            t = [float(x) for x in re.findall(r"^\s+N=%s\s+rep=0\s+\S+.*?(\d+\.\d)s" % n, txt, re.M)]
            print("scaling %s, N=%s: %d fits, %.1f s in all" % (v, n, len(t), sum(t)))
        i166 = re.findall(r"^I\.16\.6\s+\|(.*)\|", txt, re.M)
        print("scaling %s, I.16.6 by size: %s" % (v, i166))
    for f in ("m3/notebook_tp_six_lois_1.4.0.txt", "m3/tp_timing/notebook_pair/run1_1.3.0.txt",
              "m3/tp_timing/notebook_pair/run2_1.3.0.txt", "m3/tp_timing/notebook_pair/run1_1.4.0.txt",
              "m3/tp_timing/notebook_pair/run2_1.4.0.txt", "l1/m3/notebook_tp_six_lois_1.4.0.txt"):
        txt = open(os.path.join(rel, f), encoding="utf-8").read()
        fits = re.findall(r"formule trouvée : (.*?)\s+\((\d+) s\)", txt)
        print("%-45s %d s in all: %s" % (f, sum(int(s) for _, s in fits),
                                         [s for _, s in fits]))


if __name__ == "__main__":
    main(sys.argv[1])
