"""Prototype for plan 1.2 (decides nothing): under units=, what do the seed
finders find that the gate of dimensions sets aside, and how well does it
fit compared with the model returned?

The engine runs as it is (gp-elite 1.1.0 from PyPI). Wrapped without
changing what they return:
- the four seed finders (_make_power_law_seeds, _make_binomial_seeds,
  _make_elementary_seeds, _make_tolerant_seeds), to keep the rows they see;
- _typed_seeds, to keep the seeds the gate rejects (core.py of 1.1.0, line
  4181).
After the fit, each rejected seed is scored on those rows (1 - R², in the
engine's variables) beside the returned model (1 - R² of predict() on the
training rows; R² does not depend on the scale of y).

Jobs: the units arm of the TP diagnostic (200 fits, tp_diagnostic.py) and the
units kinds of the decision bench (phase1_bench.py: ufeyn, ufeyn_n1,
ufeyn_n10; 615 fits, 30 s each). One process per fit, PYTHONHASHSEED=0.

  python benchmarks/results_1.2/prototype/units_rejected.py run \\
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

FINDERS = ("_make_power_law_seeds", "_make_binomial_seeds",
           "_make_elementary_seeds", "_make_tolerant_seeds")


def install():
    import gp_elite.core as C
    st = dict(rows=None, finder=None, rejected=[])
    for name in FINDERS:
        orig = getattr(C, name)

        def wrap(xs, ys, cfg, *a, _orig=orig, _name=name, **k):
            st["rows"], st["finder"] = (xs, ys), _name
            return _orig(xs, ys, cfg, *a, **k)
        setattr(C, name, wrap)
    orig_t = C._typed_seeds

    def typed(seeds, cfg):
        kept = orig_t(seeds, cfg)
        ids = {id(t) for t in kept}
        for t in seeds or []:
            if id(t) not in ids:
                st["rejected"].append((st["finder"], t.copy(), st["rows"]))
        return kept
    C._typed_seeds = typed
    return st


def score(st):
    import numpy as np
    import gp_elite.core as C
    out = []
    for finder, t, rows in st["rejected"]:
        if rows is None:
            continue
        xs, ys = rows
        try:
            with np.errstate(all="ignore"):
                p = np.asarray(C.evaluate_vector(t, xs), dtype=float)
                e = float(np.mean((p - ys) ** 2) / (np.var(ys) or 1e-30))
            e = e if np.isfinite(e) else 1e30
        except Exception:                                  # noqa: BLE001
            e = 1e30
        out.append(dict(finder=finder, err=e, size=int(C.tree_size(t)),
                        expr=C.to_string(t)[:160]))
    out.sort(key=lambda d: d["err"])
    return out


def one(job):
    import numpy as np
    st = install()
    if job["bench"] == "tp":
        import tp_diagnostic as TP
        from gp_elite import symbolic_regression
        import gp_elite.api as A
        holder = {}
        orig = A.symbolic_regression

        def keep(X, y, **kw):
            r = orig(X, y, **kw)
            holder["r"], holder["X"], holder["y"] = r, X, y
            return r
        TP.symbolic_regression = keep          # tp_diagnostic imports it in worker()
        import gp_elite
        gp_elite.symbolic_regression = keep
        rec = TP.worker(job)
        rec.pop("front", None)
        r, X, y = holder["r"], holder["X"], holder["y"]
    else:
        import phase1_bench as P
        import gp_elite
        holder = {}
        orig = gp_elite.symbolic_regression

        def keep(X, y, **kw):
            r = orig(X, y, **kw)
            holder["r"], holder["X"], holder["y"] = r, X, y
            return r
        gp_elite.symbolic_regression = keep
        rec = P.run_one(job)
        r, X, y = holder["r"], holder["X"], holder["y"]
    with np.errstate(all="ignore"):
        p = np.asarray(r.predict(X), dtype=float)
        e = float(np.mean((p - y) ** 2) / (np.var(y) or 1e-30))
    rej = score(st)
    rec.update(bench=job["bench"], err_train_returned=e if np.isfinite(e) else 1e30,
               n_rejected=len(rej), rejected=rej[:6],
               best_rejected_err=rej[0]["err"] if rej else None)
    return rec


def jobs():
    import tp_diagnostic as TP
    import phase1_bench as P
    out = [dict(j, bench="tp") for j in TP.all_jobs() if j["arm"] == "units"]
    out += [dict(j, bench="p1") for j in P.all_jobs(with_units=True)
            if j["kind"] in ("ufeyn", "ufeyn_n1", "ufeyn_n10")]
    return out


def key(j):
    return json.dumps({k: j[k] for k in sorted(j) if k in (
        "bench", "exp", "n", "noise", "draw", "arm", "kind", "problem",
        "split", "seed")}, sort_keys=True)


def drive(python, outdir, workers):
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "units_rejected.jsonl")
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
