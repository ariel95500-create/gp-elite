"""Examination of the out-of-domain collapses of the decision bench (phase 2
of 0.9, benchmarks/results_0.9/PLAN_PHASE2.md, plan of the examination).

Runs again the 65 out-of-domain fits of R6 and R7raw (seeds 0 to 4) as
benchmarks/phase1_bench.py does (same data, budget, one process per fit) and
records, for the returned model and every entry of its Pareto front, what the
examination looks at. Never touches the frozen test set.

Usage, from the repository root (the engine is the gp_elite package of the
given Python; for the examination, gp-elite 0.8.0 from PyPI):
  python benchmarks/collapse_exam.py run --python /path/to/venv/bin/python \
         --out benchmarks/results_0.9/collapses_0.8.0.jsonl --workers 3
  python benchmarks/collapse_exam.py report benchmarks/results_0.9/collapses_0.8.0.jsonl
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
import warnings
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BASELINE = os.path.join(HERE, "results_0.9", "baseline_0.8.0.jsonl")


def jobs():
    import phase1_bench as P
    return [j for j in P.all_jobs()
            if j["kind"] in ("real", "realraw") and j["split"] == "ood"]


def key(j):
    return (j["kind"], j["problem"], j["seed"])


def _r2(y, p):
    import decision_bench as D
    return 1.0 - D.one_minus_r2(y, p)


def _ops(node):
    out, stack = set(), [node]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if n.left is not None or n.right is not None:
            out.add(str(n.value))
        stack += [n.left, n.right]
    return sorted(out)


def _facts(model, node_engine, Xtr, ytr, Xo, yo):
    """R² in and out of the domain, how far the predictions go, operators,
    and the verdict of the engine's near-domain guard."""
    import gp_elite.core as C
    with np.errstate(all="ignore"):
        po = np.asarray(model.predict(Xo), dtype=float)
        pt = np.asarray(model.predict(Xtr), dtype=float)
    span = float(np.max(np.abs(ytr - ytr.mean()))) or 1e-300
    reach = float(np.max(np.abs(po - ytr.mean()))) / span \
        if np.all(np.isfinite(po)) else float("inf")
    return dict(r2_ood=_r2(yo, po), r2_train=_r2(ytr, pt), reach=reach,
                ops=_ops(node_engine),
                near_stable=bool(C._near_domain_stable(node_engine)))


def run_one(job):
    import gp_elite
    import phase1_bench as P
    from gp_elite import symbolic_regression
    Xtr, ytr, Xo, yo, _, _, _, pool, _ = P._data(job)
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, generations=P.GENERATIONS,
                                time_limit=P.TIME_LIMIT, seed=job["seed"],
                                parallel=False, verbose=False, operators=pool)
    dt = time.time() - t0
    lo, hi = Xtr.min(axis=0), Xtr.max(axis=0)
    w = np.where(hi > lo, hi - lo, 1.0)
    excess = np.max(np.maximum(np.maximum(Xo - hi, lo - Xo), 0.0) / w, axis=1)
    rec = dict(job, time=round(dt, 2), engine_file=gp_elite.__file__,
               engine_version=getattr(gp_elite, "__version__", "?"),
               n_train=int(len(ytr)), n_ood=int(len(yo)),
               ood_var_ratio=float(np.var(yo) / (np.var(ytr) or 1e-300)),
               ood_mean_shift=float((yo.mean() - ytr.mean()) / (ytr.std() or 1e-300)),
               excess_median=float(np.median(excess)), excess_max=float(excess.max()),
               rows_outside_box=int((excess > 0).sum()),
               expr=r.expression, size=int(r.size),
               r2_validation=r.r2_validation, formula_exact=r.formula_exact)
    node_engine = r.eval_node if (getattr(r, "eval_node", None) is not None) else r.node
    rec.update(_facts(r, node_engine, Xtr, ytr, Xo, yo))
    rec["r2"] = rec["r2_ood"]
    par = []
    for e in r.pareto or []:
        ne = e.eval_node if getattr(e, "eval_node", None) is not None else e.node
        d = dict(size=int(e.size), r2_validation=e.r2_validation,
                 mse_validation=float(e.mse_validation),
                 formula_exact=e.formula_exact, expr=e.expression[:200])
        d.update(_facts(e, ne, Xtr, ytr, Xo, yo))
        par.append(d)
    rec["pareto"] = par
    rec["date"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["pythonhashseed"] = os.environ.get("PYTHONHASHSEED")
    return rec


def drive(python, out, workers):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(key(json.loads(line)))
    todo = [j for j in jobs() if key(j) not in done]
    print("%d fits to run, %d done" % (len(todo), len(done)), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    running, n = [], 0
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
                dict(j, status="CRASH", r2=-1e30, error=(se or so)[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            n += 1
            if n % 10 == 0:
                print("%d recorded, %d left" % (n, len(todo) + len(still)), flush=True)
        running = still


def report(path):
    recs = {key(r): r for r in map(json.loads, open(path)) if True}
    base = {key(r): r for r in map(json.loads, open(BASELINE))
            if r["kind"] in ("real", "realraw") and r["split"] == "ood"}
    print("%d fits run again, %d in the baseline; crashes %d" % (
        len(recs), len(base), sum(1 for r in recs.values() if r.get("status") == "CRASH")))
    col_b = {k for k, r in base.items() if r["r2"] < 0}
    col_r = {k for k, r in recs.items() if r["r2"] < 0}
    print("collapses: baseline %d, run again %d, both %d, either %d" % (
        len(col_b), len(col_r), len(col_b & col_r), len(col_b | col_r)))
    print("\nkind | dataset | seed | R² ood baseline | R² ood again | n ood | "
          "ood var/train var | ood mean shift (sd) | rows outside box | "
          "excess max | reach | near-stable | size | ops | formula")
    for k in sorted(col_b | col_r, key=lambda k: min(base[k]["r2"], recs[k]["r2"])):
        r = recs[k]
        print("%s | %s | %d | %.4g | %.4g | %d | %.3g | %+.2f | %d | %.2f | %.3g | %s | %d | %s | %s" % (
            k[0], k[1], k[2], base[k]["r2"], r["r2"], r["n_ood"],
            r["ood_var_ratio"], r["ood_mean_shift"], r["rows_outside_box"],
            r["excess_max"], r["reach"], r["near_stable"], r["size"],
            ",".join(r["ops"]), r["expr"][:90]))
    print("\nPareto fronts of the collapses run again (size | val R² | R² ood | reach | near-stable | ops)")
    for k in sorted(col_r, key=lambda k: recs[k]["r2"]):
        print("  %s %s s%d" % k)
        for e in recs[k]["pareto"]:
            print("    %3d | %s | %.4g | %.3g | %s | %s" % (
                e["size"], "%.4f" % e["r2_validation"] if e["r2_validation"] is not None else "-",
                e["r2_ood"], e["reach"], e["near_stable"], ",".join(e["ops"])))
    rr = list(recs.values())
    print("\nnear-domain guard on the returned models: stable %d of %d; "
          "among the collapses %d of %d" % (
              sum(r["near_stable"] for r in rr), len(rr),
              sum(recs[k]["near_stable"] for k in col_r), len(col_r)))


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
