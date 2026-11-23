"""A3 of ../PLAN.md: the speed of the engine in modules against 1.4.0.

F41 with the defaults of the API (phase1_bench.py one, the jobs of --defaults
--kinds feyn), one fit at a time, the two engines interleaved fit by fit (A
then B on even jobs, B then A on odd ones), each fit in its own process
(PYTHONHASHSEED=0, one BLAS thread). The time of a fit is the one the bench
records (the call to symbolic_regression). Criterion: the total time of B
within 3 % of that of A. Beside, deciding nothing: the import time of
gp_elite with each engine, median of 20 imports in fresh processes.

    python time_a3.py <python A> <python B> <out.jsonl>
"""
import json
import os
import statistics
import subprocess
import sys
import time

BENCH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", ".."))
sys.path.insert(0, BENCH)


def env():
    e = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
             OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    e.pop("PYTHONPATH", None)
    return e


def fit(python, job):
    p = subprocess.run([python, os.path.join(BENCH, "phase1_bench.py"), "one",
                        json.dumps(job)], capture_output=True, text=True,
                       env=env(), cwd="/tmp")
    lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
    if p.returncode != 0 or not lines:
        raise RuntimeError("fit failed: %s" % (p.stderr or p.stdout)[-400:])
    return json.loads(lines[-1])


def import_time(python, n=20):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        subprocess.run([python, "-I", "-c", "import gp_elite"], env=env(), cwd="/tmp",
                       check=True)
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts)


def main(pa, pb, out):
    import phase1_bench as P
    P.DEFAULTS = True
    jobs = [dict(j, defaults=True) for j in P.all_jobs() if j["kind"] == "feyn"]
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["i"] for l in open(out) if l.strip()}
    for i, job in enumerate(jobs):
        if i in done:
            continue
        order = [("A", pa), ("B", pb)] if i % 2 == 0 else [("B", pb), ("A", pa)]
        rec = dict(i=i, problem=job["problem"], seed=job["seed"])
        for name, py in order:
            r = fit(py, job)
            rec[name] = r["time"]
            rec[name + "_expr"] = r["expr"]
        with open(out, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
    recs = [json.loads(l) for l in open(out) if l.strip()]
    ta, tb = sum(r["A"] for r in recs), sum(r["B"] for r in recs)
    same = sum(1 for r in recs if r["A_expr"] == r["B_expr"])
    print("%d fits each; total A %.1f s, B %.1f s, ratio %.4f; same formula in %d"
          % (len(recs), ta, tb, tb / ta, same))
    print("A3 %s (within 3 %%)" % ("holds" if abs(tb / ta - 1) <= 0.03 else "FAILS"))
    print("import time, median of 20: A %.3f s, B %.3f s" % (import_time(pa), import_time(pb)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
