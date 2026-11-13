# -*- coding: utf-8 -*-
"""Campaign N2, the cause of its loss without noise (README.md of the
campaign). N2 is not adopted: on F41, I.16.6 goes from 4 exact fits of 5 to
2, and I.26.2 from 3 to 0. This script runs again the ten fits of these two
equations (kind feyn, seeds 0 to 4, the job of the campaign) with the wheel
of the candidate (/venv14n2), in one of three variants of its noise-tolerant
stage, set before the fit:

  n2        N2 as measured;
  norefit   N2 without the fit of the constants of each candidate
            (core._refit_inner returns its tree);
  off       N2 switched off (core._TOLERANT_N2 = False, the code of 1.3.0).

It decides nothing: it reads which part of N2 moves these fits. Under a
time budget of 30 s, timing alone moves some fits from one run to the next.

  /venv14n2/bin/python examine.py run OUT.jsonl      (4 fits at a time)
  /venv14n2/bin/python examine.py report OUT.jsonl
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
VARIANTS = ("n2", "norefit", "off")
PROBS = ("I.16.6", "I.26.2")


def one(variant, job):
    sys.path.insert(0, BENCH)
    import gp_elite.core as C
    if variant == "norefit":
        C._refit_inner = lambda tree, X, y, cfg: tree
    elif variant == "off":
        C._TOLERANT_N2 = False
    import phase1_bench as B
    rec = B.run_one(job)
    rec["variant"] = variant
    return rec


def run(out):
    sys.path.insert(0, BENCH)
    import feynman_bench as F
    names = [p[0] for p in F.PROBS]
    jobs = [(v, dict(kind="feyn", problem=p, index=names.index(p), split="test", seed=s))
            for v in VARIANTS for p in PROBS for s in range(5)]
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def go(vj):
        v, j = vj
        p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "one", v,
                            json.dumps(j)], capture_output=True, text=True, env=env, cwd="/")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if p.returncode == 0 and lines else dict(j, variant=v, crash=True,
                                                                               err=p.stderr[-300:])
    with ThreadPoolExecutor(4) as ex:
        recs = list(ex.map(go, jobs))
    with open(out, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


def report(path):
    recs = [json.loads(l) for l in open(path)]
    print("engine %s; %d fits, crashes %d" % (sorted({r.get("engine_file") for r in recs}),
                                               len(recs), sum(bool(r.get("crash")) for r in recs)))
    for p in PROBS:
        for v in VARIANTS:
            rr = sorted((r for r in recs if r["problem"] == p and r["variant"] == v),
                        key=lambda r: r["seed"])
            print("  %-8s %-8s exact %d of 5 (seeds %s); seeds placed: %s" % (
                p, v, sum(r.get("status") == "EXACT" for r in rr),
                [r["seed"] for r in rr if r.get("status") == "EXACT"],
                len((rr[0].get("tolerant_seed") or "").split(" | ")) if rr and rr[0].get("tolerant_seed") else 0))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        print(json.dumps(one(sys.argv[2], json.loads(sys.argv[3]))))
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        report(sys.argv[2])
