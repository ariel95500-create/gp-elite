"""gp-elite against gplearn on the decision bench
(benchmarks/results_0.9/PLAN_GPLEARN.md).

gplearn runs one generation at a time (warm_start) until the budget of 30 s
is spent; gp-elite's side is the phase 1 baseline (gp-elite 0.8.0 from PyPI,
same data, splits, seeds and budget on the same machine).

Usage, from the repository root:
  python benchmarks/compare_gplearn.py run --python /path/to/gplearn-venv/bin/python \
         --out benchmarks/results_0.9/gplearn_0.4.3.jsonl --workers 3
  python benchmarks/compare_gplearn.py report benchmarks/results_0.9/gplearn_0.4.3.jsonl
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BASELINE = os.path.join(HERE, "results_0.9", "baseline_0.8.0.jsonl")
BUDGET, MAX_GEN = 30.0, 1000
FUNCTIONS = ("add", "sub", "mul", "div", "sqrt", "log", "abs", "neg", "inv",
             "max", "min", "sin", "cos", "tan")
KINDS = ("feyn", "real", "realraw")


def jobs():
    import phase1_bench as P
    return [j for j in P.all_jobs() if j["kind"] in KINDS]


def key(j):
    return (j["kind"], j["problem"], j["split"], j["seed"])


def run_one(job):
    import warnings
    import gplearn
    import sklearn
    from gplearn.genetic import SymbolicRegressor
    import decision_bench as D
    import phase1_bench as P
    Xtr, ytr, Xte, yte, Xo, yo, _, _, _ = P._data(job)
    m = SymbolicRegressor(population_size=1000, generations=1, warm_start=True,
                          random_state=job["seed"], n_jobs=1,
                          function_set=FUNCTIONS)
    t0 = time.time()
    g = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        while True:
            g += 1
            m.set_params(generations=g)
            m.fit(Xtr, ytr)
            # gplearn's own stopping rule (stopping_criteria, 0 by default),
            # which a generation-by-generation run would otherwise skip
            if m.run_details_["best_fitness"][-1] <= m.stopping_criteria:
                break
            if time.time() - t0 >= BUDGET or g >= MAX_GEN:
                break
    dt = time.time() - t0
    with np.errstate(all="ignore"):
        e = D.one_minus_r2(yte, m.predict(Xte))
    rec = dict(job, engine="gplearn", engine_version=gplearn.__version__,
               sklearn=sklearn.__version__, numpy=np.__version__,
               time=round(dt, 2), generations=g, err=e, r2=1.0 - e,
               size=int(m._program.length_), expr=str(m._program)[:300],
               time_limit_reached=bool(dt >= BUDGET))
    if job["kind"] == "feyn":
        rec["status"] = "EXACT" if e < 1e-9 else "NEAR" if e < 1e-3 else "MISS"
        if Xo is not None and yo is not None and len(yo) >= 20:
            with np.errstate(all="ignore"):
                rec["err_ood"] = D.one_minus_r2(yo, m.predict(Xo))
    rec.update(date=time.strftime("%Y-%m-%dT%H:%M:%S"),
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               python=sys.version.split()[0])
    return rec


def drive(python, out, workers):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(key(json.loads(line)))
    todo = [j for j in jobs() if key(j) not in done]
    print("%d fits to run, %d done" % (len(todo), len(done)), flush=True)
    # the repository root on PYTHONPATH: benchmarks/feynman_bench.py, which
    # builds the F41 data, imports gp_elite at load time; nothing of it runs
    # in a gplearn fit
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONPATH=os.path.dirname(HERE))
    running, n, t0 = [], 0, time.time()
    while todo or running:
        while todo and len(running) < workers:
            j = todo.pop(0)
            running.append((j, subprocess.Popen(
                [python, os.path.abspath(__file__), "one", json.dumps(j)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd=os.path.dirname(HERE))))
        time.sleep(0.2)
        still = []
        for j, p in running:
            if p.poll() is None:
                still.append((j, p))
                continue
            so, se = p.communicate()
            lines = [l for l in so.splitlines() if l.startswith("{")]
            rec = json.loads(lines[-1]) if p.returncode == 0 and lines else \
                dict(j, engine="gplearn", status="CRASH" if j["kind"] == "feyn"
                     else None, err=1e30, r2=-1e30, error=(se or so)[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            n += 1
            if n % 25 == 0:
                print("%d recorded, %d left, %.0f s" % (
                    n, len(todo) + len(still), time.time() - t0), flush=True)
        running = still


def report(path):
    from collections import Counter
    gp = {key(r): r for r in map(json.loads, open(path))}
    ge = {key(r): r for r in map(json.loads, open(BASELINE)) if r["kind"] in KINDS}
    both = sorted(set(gp) & set(ge))
    print("%d gplearn fits, %d gp-elite fits, %d paired; gplearn crashes %d" % (
        len(gp), len(ge), len(both),
        sum(1 for r in gp.values() if r.get("error"))))
    print("\n| suite | tool | fits | EXACT | NEAR | MISS | median 1 − R² | "
          "median size | median generations | median time (s) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for tool, src in (("gp-elite 0.8.0", ge), ("gplearn 0.4.3", gp)):
        rr = [src[k] for k in both if k[0] == "feyn"]
        st = Counter(r.get("status") for r in rr)
        print("| F41 | %s | %d | %d | %d | %d | %.3g | %.0f | %.0f | %.1f |" % (
            tool, len(rr), st["EXACT"], st["NEAR"], st["MISS"] + st["CRASH"],
            np.median([r["err"] for r in rr]), np.median([r["size"] for r in rr]),
            np.median([r.get("generations", 0) for r in rr]),
            np.median([r["time"] for r in rr])))
    print("\n| suite | split | tool | fits | median R² | mean R² | worst R² | "
          "collapses (R² < 0) | median size |")
    print("|---|---|---|---|---|---|---|---|---|")
    for kind, name in (("real", "R6"), ("realraw", "R7raw")):
        for split, pred in (("folds", lambda s: s.startswith("fold")),
                            ("out of domain", lambda s: s == "ood")):
            ks = [k for k in both if k[0] == kind and pred(k[2])]
            for tool, src in (("gp-elite 0.8.0", ge), ("gplearn 0.4.3", gp)):
                r2 = np.array([src[k]["r2"] for k in ks], dtype=float)
                print("| %s | %s | %s | %d | %.3f | %.3g | %.3g | %d | %.0f |" % (
                    name, split, tool, len(ks), np.median(r2), np.mean(r2),
                    r2.min(), int((r2 < 0).sum()),
                    np.median([src[k]["size"] for k in ks])))
    print("\npaired, fit by fit (gp-elite − gplearn)")
    fe = [k for k in both if k[0] == "feyn"]
    print("  F41: exact in gp-elite only %d, in gplearn only %d, both %d" % (
        sum(1 for k in fe if ge[k]["status"] == "EXACT" != gp[k].get("status")),
        sum(1 for k in fe if gp[k].get("status") == "EXACT" != ge[k]["status"]),
        sum(1 for k in fe if ge[k]["status"] == gp[k].get("status") == "EXACT")))
    for kind, name in (("real", "R6"), ("realraw", "R7raw")):
        ks = [k for k in both if k[0] == kind]
        d = np.array([ge[k]["r2"] - gp[k]["r2"] for k in ks])
        print("  %s: median paired R² difference %+.4f; gp-elite better in %d of"
              " %d fits" % (name, np.median(d), int((d > 0).sum()), len(ks)))
    print("\nexamples, F41 seed 0 (gplearn's formula)")
    for k in [k for k in fe if k[3] == 0][:8]:
        print("  %-10s gp-elite %-5s gplearn %-5s %s" % (
            k[1], ge[k]["status"], gp[k].get("status"), gp[k].get("expr", "")[:110]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=3)
    o = sub.add_parser("one")
    o.add_argument("job")
    s = sub.add_parser("report")
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        drive(a.python, a.out, a.workers)
    elif a.cmd == "one":
        print(json.dumps(run_one(json.loads(a.job))))
    else:
        report(a.path)


if __name__ == "__main__":
    main()
