"""Prototype for plan 1.2 (decides nothing): what would a stop on patience
change on the fits of the TP diagnostic?

The rule tried, outside the engine: in the generation loop, the champion's
error (the one the engine's early stop already reads, core.py of 1.1.0, line
9249) counts as a gain when it falls below (1 - EPS) times the best error
seen so far; when no gain has come for P generations, the loop ends as it
does on an exact law. gp-elite 1.1.0 from PyPI runs otherwise unchanged:
_holdout_mse is wrapped to keep the value it returns, and
_early_stop_threshold, called only in the generation loops, returns +inf
once the patience is spent, which ends the loop through its own test.

Jobs: the 400 fits of the TP diagnostic (tp_diagnostic.py, draws 0 to 4),
for each value of P given; EPS = 0.01. One process per fit,
PYTHONHASHSEED=0.

  python benchmarks/results_1.2/prototype/patience_try.py run \\
         --python /venv11p/bin/python --out DIR --workers 4 --patience 20 10
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

EPS = 0.01


def install(patience):
    import gp_elite.core as C
    st = dict(gen=-1, last=None, best=None, best_gen=0, stop_gen=None)
    orig_isl, orig_h, orig_t = C.evolve_island, C._holdout_mse, C._early_stop_threshold

    def isl(*a, **k):
        g = a[3] if len(a) > 3 else k.get("generation", 0)
        st["gen"] = max(st["gen"], int(g))
        return orig_isl(*a, **k)

    def h(node, xs, ys):
        m = orig_h(node, xs, ys)
        st["last"] = m
        return m

    def thr(cfg, ys):
        t = orig_t(cfg, ys)
        m, g = st["last"], st["gen"]
        if m is None:
            return t
        if st["best"] is None or m < st["best"] * (1.0 - EPS):
            st["best"], st["best_gen"] = m, g
        elif g - st["best_gen"] >= patience:
            st["stop_gen"] = g
            return float("inf")
        return t
    C.evolve_island, C._holdout_mse, C._early_stop_threshold = isl, h, thr
    return st


def one(job):
    import numpy as np
    import gp_elite
    st = install(int(job["patience"]))
    import tp_diagnostic as TP
    holder = {}
    orig = gp_elite.symbolic_regression

    def keep(X, y, **kw):                  # pass-through, to score the model
        r = orig(X, y, **kw)
        holder.update(r=r, X=X, y=y)
        return r
    gp_elite.symbolic_regression = keep    # tp_diagnostic imports it in worker()
    rec = TP.worker({k: v for k, v in job.items() if k not in ("patience", "bench")})
    rec.pop("front", None)
    rec.update(patience=job["patience"], eps=EPS, stop_gen=st["stop_gen"],
               last_gen=st["gen"], best_gen=st["best_gen"], bench="tp")
    if "r" in holder:
        # 1 - R² of predict() on the training rows, as units_rejected.py
        # records it for the model returned under units.
        with np.errstate(all="ignore"):
            y = np.asarray(holder["y"], dtype=float)
            p = np.asarray(holder["r"].predict(holder["X"]), dtype=float)
            e = float(np.mean((p - y) ** 2) / (np.var(y) or 1e-30))
        rec["err_train"] = e if np.isfinite(e) else 1e30
    return rec


def jobs(patiences):
    import tp_diagnostic as TP
    return [dict(j, bench="tp", patience=p) for p in patiences for j in TP.all_jobs()]


def key(j):
    return json.dumps({k: j[k] for k in sorted(j) if k in (
        "exp", "n", "noise", "draw", "arm", "patience")}, sort_keys=True)


def drive(python, outdir, workers, patiences):
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "patience.jsonl")
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in jobs(patiences) if key(j) not in done]
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
    r.add_argument("--patience", type=int, nargs="+", default=[20])
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
        drive(a.python, a.out, a.workers, a.patience)


if __name__ == "__main__":
    main()
