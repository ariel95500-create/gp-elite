"""Prototype for plan 1.2 (decides nothing): when does the champion of a fit
reach the form it ends with?

The engine runs as it is (gp-elite 1.1.0 from PyPI). Two functions of
gp_elite.core are wrapped, without changing what they return:
- evolve_island, to know the generation being run;
- _holdout_mse, which the sequential loop calls once per generation on the
  champion, for its early stop (core.py of 1.1.0, line 9249).
Each call records the generation, the time and the champion's expression;
the numbers of the expression are masked to compare forms.

Jobs: the 400 fits of the TP diagnostic (tp_diagnostic.py, defaults of the
API, 100 generations) and the noisy and real kinds of the decision bench
(phase1_bench.py: F41N1, F41N10, R6, R7raw; 30 s and 1,000 generations).
One process per fit, PYTHONHASHSEED=0, one BLAS thread.

  python benchmarks/results_1.2/prototype/champion_trace.py run \\
         --python /venv11p/bin/python --out DIR --workers 4
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)

NUM = re.compile(r"(?<![A-Za-z_\[\d.])\d+\.?\d*(?:[eE][-+]?\d+)?")


def form(s):
    return NUM.sub("c", s or "")


def install_trace():
    import gp_elite.core as C
    state = dict(gen=-1, trace=[])
    orig_isl, orig_h = C.evolve_island, C._holdout_mse

    def isl(*a, **k):
        g = a[3] if len(a) > 3 else k.get("generation", 0)
        state["gen"] = max(state["gen"], int(g))
        return orig_isl(*a, **k)

    def h(node, xs, ys):
        m = orig_h(node, xs, ys)
        state["trace"].append((state["gen"], time.time(),
                               C.to_string(node) if node is not None else "",
                               float(m)))
        return m
    C.evolve_island, C._holdout_mse = isl, h
    return state


def summarise(state, t0):
    per_gen = {}
    for g, t, s, m in state["trace"]:
        if g >= 0 and g not in per_gen:        # the in-loop call comes first
            per_gen[g] = (t, s, m)
    gens = sorted(per_gen)
    if not gens:
        return dict(n_gens=0)
    forms = [form(per_gen[g][1]) for g in gens]
    final = forms[-1]
    k = len(forms) - 1
    while k > 0 and forms[k - 1] == final:
        k -= 1
    changes = [(gens[i], round(per_gen[gens[i]][0] - t0, 2),
                per_gen[gens[i]][1][:160], per_gen[gens[i]][2])
               for i in range(len(gens)) if i == 0 or forms[i] != forms[i - 1]]
    return dict(n_gens=gens[-1] + 1, loop_end=round(per_gen[gens[-1]][0] - t0, 2),
                gen_stable=gens[k], t_stable=round(per_gen[gens[k]][0] - t0, 2),
                gen0_is_final=forms[0] == final, n_changes=len(changes) - 1,
                final_champion=per_gen[gens[-1]][1][:200], changes=changes[-12:])


def one(job):
    state = install_trace()
    t0 = time.time()
    if job["bench"] == "tp":
        import tp_diagnostic as TP
        rec = TP.worker(job)
        rec.pop("front", None)
    else:
        import phase1_bench as P
        rec = P.run_one(job)
    rec.update(summarise(state, t0), bench=job["bench"])
    return rec


def jobs():
    import tp_diagnostic as TP
    import phase1_bench as P
    out = [dict(j, bench="tp") for j in TP.all_jobs()]
    out += [dict(j, bench="p1") for j in P.all_jobs()
            if j["kind"] in ("feyn_n1", "feyn_n10", "real", "realraw")]
    return out


def key(j):
    return json.dumps({k: j[k] for k in sorted(j) if k in (
        "bench", "exp", "n", "noise", "draw", "arm", "kind", "problem",
        "split", "seed")}, sort_keys=True)


def drive(python, outdir, workers):
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "trace.jsonl")
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in jobs() if key(j) not in done]
    print("%d jobs to run" % len(todo), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def run(j):
        p = subprocess.run([python, os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd=BENCH)
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        rec = json.loads(lines[-1]) if (p.returncode == 0 and lines) else \
            dict(j, status="CRASH", error=(p.stderr or p.stdout)[-400:])
        return rec

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
