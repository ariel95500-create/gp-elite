# -*- coding: utf-8 -*-
"""Campaign E2, the cause of its result (README.md of the campaign). E2 is
not adopted: in the plain arm of TP, Newton's cooling has the law in 7 fits
of 20 (the plan asks 10) and the point source falls from 18 to 15. The fits
of TP are reproducible (1.3.0 gives the same 400 models in campaigns N2 and
E2), so what differs between A and B comes from E2.

This script runs again the 200 fits of the plain arm (draws 0 to 4) with A
(1.3.0 from PyPI) and with B (the wheel of E2), with the worker of the TP
diagnostic, and records the seeds each places: the exact seeds of the
functions of a monomial (trace "elementary_seed") and the noise-tolerant
seeds with their scores (trace "tolerant_seed", "tolerant_cands"). A seed
placed by B and not by A comes from E2: the two engines differ by E2 alone
on these fits (N2 and S1 are off in B).

It decides nothing.

  /venv13p/bin/python examine.py run OUT.jsonl      (4 fits at a time)
  /venv13p/bin/python examine.py report OUT.jsonl CAMPAIGN_A CAMPAIGN_B
"""
import json
import os
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
ENGINES = {"A": "/venv13p/bin/python", "B": "/venv14e2/bin/python"}


def one(job):
    sys.path.insert(0, BENCH)
    import tp_diagnostic as T
    import gp_elite.core as C
    rec = T.worker(job)
    tr = C.TRACE.value
    for k in ("elementary_seed", "tolerant_seed", "tolerant_cands"):
        rec[k] = tr.get(k)
    return rec


def run(out):
    sys.path.insert(0, BENCH)
    import tp_diagnostic as T
    jobs = [j for j in T.all_jobs() if j["arm"] == "plain"]
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def go(ej):
        eng, j = ej
        p = subprocess.run([ENGINES[eng], "-I", os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True, env=env,
                           cwd="/")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        if p.returncode != 0 or not lines:
            return dict(j, engine=eng, crash=True, stderr=p.stderr[-300:])
        return dict(json.loads(lines[-1]), engine=eng)
    with ThreadPoolExecutor(4) as ex:
        recs = list(ex.map(go, [(e, j) for j in jobs for e in ENGINES]))
    with open(out, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


def _seeds(r):
    s = r.get("tolerant_seed") or ""
    return [x.rsplit(" (", 1)[0] for x in s.split(" | ") if x]


def report(path, camp_a, camp_b):
    key = lambda r: (r["exp"], r["n"], r["noise"], r["draw"])
    R = [json.loads(ln) for ln in open(path, encoding="utf-8")]
    E = {e: {key(r): r for r in R if r["engine"] == e} for e in ENGINES}
    camp = {}
    for e, p in (("A", camp_a), ("B", camp_b)):
        camp[e] = {key(r): r for r in map(json.loads, open(p, encoding="utf-8"))
                   if r["arm"] == "plain"}
    print("%d fits, crashes %d; engines %s" % (
        len(R), sum(bool(r.get("crash")) for r in R),
        sorted({r.get("engine_file") for r in R})))
    for e in ENGINES:
        same = sum(E[e][k]["expr"] == camp[e][k]["expr"] for k in E[e])
        print("  %s: the model of the campaign again in %d of %d fits" % (e, same, len(E[e])))
    ks = sorted(E["A"])
    print("\nBy experiment (plain arm, 20 fits each): the law A -> B; the fits where B "
          "places a seed A does not place (a seed of E2), and the law there A -> B")
    for exp in sorted({k[0] for k in ks}):
        kk = [k for k in ks if k[0] == exp]
        e2 = [k for k in kk if set(_seeds(E["B"][k])) - set(_seeds(E["A"][k]))]
        lost = [k for k in kk if set(_seeds(E["A"][k])) - set(_seeds(E["B"][k]))]
        print("  %-16s law %2d -> %2d; a seed of E2 in %2d fits (law there %d -> %d); "
              "a seed of A not placed by B in %d; models that differ %d" % (
                  exp, sum(E["A"][k]["law"] for k in kk), sum(E["B"][k]["law"] for k in kk),
                  len(e2), sum(E["A"][k]["law"] for k in e2),
                  sum(E["B"][k]["law"] for k in e2), len(lost),
                  sum(E["A"][k]["expr"] != E["B"][k]["expr"] for k in kk)))
        diff_no_e2 = [k for k in kk if E["A"][k]["expr"] != E["B"][k]["expr"]
                      and k not in e2]
        if diff_no_e2:
            print("    models that differ without a seed of E2: %s" % diff_no_e2)
    for exp in ("refroidissement", "eclairement"):
        print("\n%s, the fits one by one (points, noise, draw): the law A, B; the seeds "
              "of E2 placed by B, with their scores; the noise-tolerant candidates of B"
              % exp)
        for k in [k for k in ks if k[0] == exp]:
            a, b = E["A"][k], E["B"][k]
            new = [x for x in (b.get("tolerant_seed") or "").split(" | ")
                   if x and x.rsplit(" (", 1)[0] not in set(_seeds(a))]
            print("  %2d pts %d %% draw %d: law %s, %s; E2 seeds: %s; %s" % (
                k[1], round(100 * k[2]), k[3], a["law"], b["law"],
                " | ".join(new) or "none", b.get("tolerant_cands")))
            if a["law"] != b["law"]:
                print("      A: %s" % a["expr"][:110])
                print("      B: %s" % b["expr"][:110])
    c = Counter()
    for k in ks:
        for x in set(_seeds(E["B"][k])) - set(_seeds(E["A"][k])):
            c[k[0]] += 1
    print("\nSeeds of E2 placed, by experiment: %s" % dict(c))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        print(json.dumps(one(json.loads(sys.argv[2]))))
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        report(sys.argv[2], sys.argv[3], sys.argv[4])
