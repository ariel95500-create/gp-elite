# -*- coding: utf-8 -*-
"""Campaign N2b, beside its criteria (README.md of the campaign): on TP the
point source falls from 18 fits of 20 to 14 in the plain arm. The fits of TP
are reproducible, so what differs between A and B comes from N2b.

This script runs again the 20 fits of the plain arm of the point source
(draws 0 to 4) with A (1.3.0 from PyPI) and B (the wheel of N2b), with the
worker of the TP diagnostic, and records the seeds each places: the
noise-tolerant seeds with their scores (trace "tolerant_seed"). It decides
nothing.

  /venv13p/bin/python examine.py run OUT.jsonl      (4 fits at a time)
  /venv13p/bin/python examine.py report OUT.jsonl CAMPAIGN_A CAMPAIGN_B
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
ENGINES = {"A": "/venv13p/bin/python", "B": "/venv14n2b/bin/python"}
EXPS = ("eclairement",)


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
    jobs = [j for j in T.all_jobs() if j["arm"] == "plain" and j["exp"] in EXPS]
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
                   if r["arm"] == "plain" and r["exp"] in EXPS}
    print("%d fits, crashes %d; engines %s" % (
        len(R), sum(bool(r.get("crash")) for r in R),
        sorted({r.get("engine_file") for r in R})))
    for e in ENGINES:
        same = sum(E[e][k]["expr"] == camp[e][k]["expr"] for k in E[e])
        print("  %s: the model of the campaign again in %d of %d fits" % (e, same, len(E[e])))
    ks = sorted(E["A"])
    kept = sum(set(_seeds(E["A"][k])) <= set(_seeds(E["B"][k])) for k in ks)
    print("  every seed of A placed by B in %d of %d fits" % (kept, len(ks)))
    print("  seeds placed: A %d, B %d; models that differ %d; the law %d -> %d" % (
        sum(len(_seeds(E["A"][k])) for k in ks), sum(len(_seeds(E["B"][k])) for k in ks),
        sum(E["A"][k]["expr"] != E["B"][k]["expr"] for k in ks),
        sum(E["A"][k]["law"] for k in ks), sum(E["B"][k]["law"] for k in ks)))
    for exp in EXPS:
        print("\n%s, the fits one by one (points, noise, draw): the law A, B; the "
              "number of seeds of A and B; the seeds B adds, with their scores" % exp)
        for k in [k for k in ks if k[0] == exp]:
            a, b = E["A"][k], E["B"][k]
            new = [x for x in (b.get("tolerant_seed") or "").split(" | ")
                   if x and x.rsplit(" (", 1)[0] not in set(_seeds(a))]
            print("  %2d pts %d %% draw %d: law %s, %s; seeds %d, %d; added: %s" % (
                k[1], round(100 * k[2]), k[3], a["law"], b["law"], len(_seeds(a)),
                len(_seeds(b)), " | ".join(x[:60] for x in new[:4]) or "none"))
            if a["law"] != b["law"]:
                print("      A: %s" % a["expr"][:110])
                print("      B: %s" % b["expr"][:110])


if __name__ == "__main__":
    if sys.argv[1] == "one":
        print(json.dumps(one(json.loads(sys.argv[2]))))
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        report(sys.argv[2], sys.argv[3], sys.argv[4])
