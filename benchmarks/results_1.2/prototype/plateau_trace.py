"""Prototype for plan 1.2 (decides nothing): on the exact laws of F41,
without noise, how long does the champion stay without a gain before the
law appears?

A stop on patience (end the search when the champion's error has not
improved for P generations) would cut a fit that sits on a plateau longer
than P generations before it finds the law. This script measures those
plateaus. The engine runs as it is (gp-elite 1.1.0 from PyPI), wrapped as in
champion_trace.py; each generation also records the champion's error as
1 - R² (the in-loop error over the variance of the target), so that any
rule on the error can be replayed afterwards.

Jobs: the kind "feyn" of the decision bench (phase1_bench.py: 41 laws, 5
seeds, 30 s and 1,000 generations). One process per fit, PYTHONHASHSEED=0.

  python benchmarks/results_1.2/prototype/plateau_trace.py run \\
         --python /venv11p/bin/python --out DIR --workers 4
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)
sys.path.insert(0, HERE)

import champion_trace as CT                                     # noqa: E402


def one(job):
    import numpy as np
    import gp_elite.core as C
    state = CT.install_trace()
    var = {}
    orig_thr = C._early_stop_threshold

    def thr(cfg, ys):
        if "v" not in var:
            ref = C._VAL_YS if (C._VAL_YS is not None and len(C._VAL_YS) > 1) else ys
            var["v"] = float(np.var(np.asarray(ref, dtype=float))) or 1e-300
        return orig_thr(cfg, ys)
    C._early_stop_threshold = thr
    t0 = time.time()
    import phase1_bench as P
    rec = P.run_one(job)
    rec.update(CT.summarise(state, t0), bench=job["bench"])
    per_gen = {}
    for g, t, s, m in state["trace"]:
        if g >= 0 and g not in per_gen:
            per_gen[g] = m
    v = var.get("v", 1.0)
    rec["err_by_gen"] = [float("%.4g" % (per_gen[g] / v)) for g in sorted(per_gen)]
    return rec


def jobs():
    import phase1_bench as P
    return [dict(j, bench="p1") for j in P.all_jobs() if j["kind"] == "feyn"]


def drive(python, outdir, workers):
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "plateau.jsonl")
    done = set()
    if os.path.exists(out):
        done = {CT.key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in jobs() if CT.key(j) not in done]
    print("%d jobs to run" % len(todo), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def run(j):
        p = subprocess.run([python, os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd=BENCH)
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if (p.returncode == 0 and lines) else \
            dict(j, status="CRASH", error=(p.stderr or p.stdout)[-400:])

    n = 0
    with ThreadPoolExecutor(workers) as ex, open(out, "a") as fh:
        for rec in ex.map(run, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            n += 1
            if n % 50 == 0:
                print("%d done" % n, flush=True)
    print("all done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    o = sub.add_parser("one")
    o.add_argument("job")
    a = ap.parse_args()
    if a.cmd == "one":
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rec = one(json.loads(a.job))
        print(json.dumps(rec, default=str))
    else:
        drive(a.python, a.out, a.workers)


if __name__ == "__main__":
    main()
