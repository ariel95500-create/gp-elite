"""Phase 1 measurements (benchmarks/results_0.9/PLAN.md).

Measures one engine, budget T (30 s per fit), on:

  F41, R6, R7raw     the decision bench, exactly as benchmarks/decision_bench.py
                     builds it (same data, splits and seeds 0 to 4)
  F41N1, F41N10      F41 with 1 % and 10 % Gaussian noise on the training
                     targets; "structure retrieved" beside the exact count
  TF78, TS14, TR25, TR25raw
                     the frozen test set of benchmarks/test_set.py, seeds 5
                     to 9 (never used to decide)

Every fit runs in its own process with PYTHONHASHSEED=0 and one BLAS thread;
the engine is the gp_elite package importable by the given Python (for the
baseline: gp-elite 0.8.0 installed from PyPI in a fresh environment). The
run resumes: jobs already in the output file are skipped.

Usage, from the repository root:
  python benchmarks/phase1_bench.py run --python /path/to/venv/bin/python \
         --out benchmarks/results_0.9/baseline_0.8.0.jsonl --workers 3
  python benchmarks/phase1_bench.py summary benchmarks/results_0.9/baseline_0.8.0.jsonl
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TIME_LIMIT, GENERATIONS = 30.0, 1000
BENCH_SEEDS = [0, 1, 2, 3, 4]
TEST_SEEDS = [5, 6, 7, 8, 9]
NOISE = {"feyn_n1": 0.01, "feyn_n10": 0.10}
ORDER = ["feyn", "real", "realraw", "tf", "ts", "tr", "trraw",
         "feyn_n1", "feyn_n10"]


# ─────────────────────────────────────────────────────────────── jobs ──

def all_jobs():
    import feynman_bench as F
    import decision_bench as D
    import test_set as T
    out = []
    for kind in ORDER:
        if kind in ("feyn", "feyn_n1", "feyn_n10"):
            for i, p in enumerate(F.PROBS):
                for s in BENCH_SEEDS:
                    out.append(dict(kind=kind, problem=p[0], index=i,
                                    split="test", seed=s))
        elif kind in ("real", "realraw"):
            names = D.REAL if kind == "real" else D.REAL_RAW
            for n in names:
                for k in range(5):
                    out.append(dict(kind=kind, problem=n, split="fold%d" % k,
                                    seed=0))
            for n in names:
                for s in BENCH_SEEDS:
                    out.append(dict(kind=kind, problem=n, split="ood", seed=s))
        elif kind == "tf":
            for n in T.names("TF78"):
                for s in TEST_SEEDS:
                    out.append(dict(kind=kind, problem=n, split="test", seed=s))
        elif kind == "ts":
            for n in T.names("TS14"):
                for sp in ("test", "ood"):
                    for s in TEST_SEEDS:
                        out.append(dict(kind=kind, problem=n, split=sp, seed=s))
        elif kind in ("tr", "trraw"):
            for n in T.names("TR25"):
                for k in range(5):
                    out.append(dict(kind=kind, problem=n, split="fold%d" % k,
                                    seed=TEST_SEEDS[0]))
            for n in T.names("TR25"):
                for s in TEST_SEEDS:
                    out.append(dict(kind=kind, problem=n, split="ood", seed=s))
    return out


def key(j):
    return (j["kind"], j["problem"], j["split"], j["seed"])


# ───────────────────────────────────────────────────────────── worker ──

def _data(job):
    """(Xtr, ytr, Xte, yte, Xo, yo, names, pool, ytr_clean)."""
    import decision_bench as D
    import test_set as T
    kind = job["kind"]
    if kind in ("feyn", "feyn_n1", "feyn_n10"):
        Xtr, ytr, Xte, yte, Xo, yo, names, pool = D.feyn_data(job["index"])
        clean = ytr
        if kind in NOISE:
            rng = np.random.RandomState(7000 + job["index"])
            ytr = ytr + rng.normal(0.0, NOISE[kind] * float(np.std(ytr)),
                                   len(ytr))
        return Xtr, ytr, Xte, yte, Xo, yo, names, pool, clean
    if kind in ("real", "realraw"):
        Xtr, ytr, Xte, yte = D.real_data(job["problem"], job["split"],
                                         raw=kind == "realraw")
        return Xtr, ytr, Xte, yte, None, None, None, "physical", ytr
    if kind == "tf":
        Xtr, ytr, Xte, yte, Xo, yo, names, pool = T.tf_data(job["problem"])
        return Xtr, ytr, Xte, yte, Xo, yo, names, pool, ytr
    if kind == "ts":
        Xtr, ytr, Xte, yte, names, pool = T.ts_data(job["problem"],
                                                    job["split"])
        return Xtr, ytr, Xte, yte, None, None, names, pool, ytr
    if kind in ("tr", "trraw"):
        Xtr, ytr, Xte, yte = T.tr_data(job["problem"], job["split"],
                                       raw=kind == "trraw")
        return Xtr, ytr, Xte, yte, None, None, None, "physical", ytr
    raise ValueError(kind)


def _structure(r, Xtr, ytr_clean, Xte, yte):
    """1 - R² on the clean test rows after refitting the returned model's
    constants on the clean training targets with the engine's own finishing
    step, in the engine's internal variables (PLAN.md)."""
    import gp_elite.core as C
    import decision_bench as D
    node = r.eval_node if (r.eval_node is not None and r.y_scale != 1.0) \
        else r.node
    ys = float(r.y_scale or 1.0)
    xs_tr = r.scaler.transform(Xtr) if r.scaler is not None else Xtr
    xs_te = r.scaler.transform(Xte) if r.scaler is not None else Xte
    cfg = C.make_cfg_nd(n_features=Xtr.shape[1])
    y_int = np.asarray(ytr_clean, dtype=float) / ys
    with redirect_stdout(io.StringIO()), np.errstate(all="ignore"):
        fitted = C._lm_to_convergence(node.copy(), xs_tr, y_int, cfg)
        tree = fitted if fitted is not None else node.copy()
        tree = C._refit_scaling(tree, xs_tr, y_int)
        p = np.asarray(C.evaluate_vector(tree, xs_te), dtype=float) * ys
    return D.one_minus_r2(yte, p)


def run_one(job):
    import warnings
    import gp_elite
    import gp_elite.core as C
    import decision_bench as D
    import test_set as T
    from gp_elite import symbolic_regression

    gens = [0]
    orig = C.evolve_island

    def counted(*args, **kwargs):
        g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        return orig(*args, **kwargs)
    C.evolve_island = counted

    Xtr, ytr, Xte, yte, Xo, yo, names, pool, clean = _data(job)
    kw = dict(generations=GENERATIONS, time_limit=TIME_LIMIT,
              seed=job["seed"], parallel=False, verbose=False, operators=pool)
    if names is not None:
        kw["feature_names"] = names
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, **kw)
    dt = time.time() - t0
    C.evolve_island = orig

    rec = dict(job)
    e = D.one_minus_r2(yte, r.predict(Xte))
    rec.update(time=round(dt, 2), generations=gens[0], size=int(r.size),
               err=e, r2=1.0 - e, formula_exact=r.formula_exact,
               time_limit_reached=bool(getattr(r, "time_limit_reached", False)),
               expr=r.expression[:160], engine_file=gp_elite.__file__,
               engine_version=getattr(gp_elite, "__version__", "?"))
    exact_kind = job["kind"] in ("feyn", "feyn_n1", "feyn_n10", "tf") or (
        job["kind"] == "ts"
        and T.manifest()["datasets"][job["problem"]]["exact_scorable"])
    if exact_kind:
        rec["status"] = ("EXACT" if e < 1e-9 else "NEAR" if e < 1e-3
                         else "MISS")
    if Xo is not None and yo is not None and len(yo) >= 20:
        rec["err_ood"] = D.one_minus_r2(yo, r.predict(Xo))
        rec["n_ood"] = int(len(yo))
    if job["kind"] in NOISE:
        try:
            se = _structure(r, Xtr, clean, Xte, yte)
        except Exception as exc:              # counted, never hidden
            se, rec["structure_error"] = 1e30, repr(exc)[:200]
        rec["err_structure"] = se
        rec["structure"] = bool(se < 1e-9)
    if job["kind"] == "tf":
        rec["family"] = T.manifest()["datasets"][job["problem"]]["family"]
    if job["kind"] in ("feyn", "feyn_n1", "feyn_n10"):
        import feynman_bench as F
        p = F.PROBS[job["index"]]
        rec["family"] = p[6] if len(p) > 6 else "historique"
    import sklearn
    try:
        from numpy._core._multiarray_umath import __cpu_features__ as cpu
    except ImportError:                     # NumPy 1.x
        from numpy.core._multiarray_umath import __cpu_features__ as cpu
    rec.update(date=time.strftime("%Y-%m-%dT%H:%M:%S"),
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               python=sys.version.split()[0], numpy=np.__version__,
               sklearn=sklearn.__version__,
               avx512=bool(cpu.get("AVX512F")), avx2=bool(cpu.get("AVX2")),
               npy_disable=os.environ.get("NPY_DISABLE_CPU_FEATURES", ""))
    return rec


# ───────────────────────────────────────────────────────────── driver ──

def drive(python, out, workers, kinds=None, max_seconds=None):
    """Runs the jobs not yet in `out`. With max_seconds, stops launching new
    fits after that time and returns once the running ones are recorded (the
    next call resumes)."""
    done = set()
    if os.path.exists(out):
        with open(out) as fh:
            for line in fh:
                if line.strip():
                    done.add(key(json.loads(line)))
    todo = [j for j in all_jobs() if key(j) not in done
            and (kinds is None or j["kind"] in kinds)]
    print("%d jobs to run, %d already done" % (len(todo), len(done)),
          flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    running = []
    t_start = time.time()
    n_done = 0
    while todo or running:
        if max_seconds is not None and time.time() - t_start > max_seconds \
                and todo:
            print("time slice over: %d jobs left for the next call"
                  % len(todo), flush=True)
            todo = []
        while todo and len(running) < workers:
            j = todo.pop(0)
            p = subprocess.Popen(
                [python, os.path.abspath(__file__), "one", json.dumps(j)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd=os.path.dirname(HERE))
            running.append((j, p))
        time.sleep(0.2)
        still = []
        for j, p in running:
            if p.poll() is None:
                still.append((j, p))
                continue
            so, se = p.communicate()
            lines = [l for l in so.splitlines() if l.startswith("{")]
            if p.returncode == 0 and lines:
                rec = json.loads(lines[-1])
            else:                       # a crash is a recorded miss
                rec = dict(j, status="CRASH", err=1e30, r2=-1e30,
                           error=(se or so)[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            n_done += 1
            if n_done % 25 == 0:
                el = time.time() - t_start
                print("%d done, %.0f s elapsed, %d left" % (n_done, el, len(todo)
                      + len(still)), flush=True)
        running = still


def summary(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    print("%d records" % len(recs))
    by = {}
    for r in recs:
        by.setdefault(r["kind"], []).append(r)
    for kind in ORDER:
        rr = by.get(kind, [])
        if not rr:
            continue
        t = np.array([r.get("time", np.nan) for r in rr], dtype=float)
        line = "%-9s n=%4d  time median %.1f s, max %.1f s" % (
            kind, len(rr), np.nanmedian(t), np.nanmax(t))
        st = [r.get("status") for r in rr if "status" in r]
        if st:
            line += "  EXACT %d NEAR %d MISS %d CRASH %d" % tuple(
                st.count(x) for x in ("EXACT", "NEAR", "MISS", "CRASH"))
        if any("structure" in r for r in rr):
            line += "  structure %d" % sum(1 for r in rr if r.get("structure"))
        print(line)
        for split_name, pred in (("folds", lambda s: s.startswith("fold")),
                                 ("ood", lambda s: s == "ood"),
                                 ("test", lambda s: s == "test")):
            sub = [r for r in rr if pred(r["split"])]
            if not sub or kind in ("feyn", "feyn_n1", "feyn_n10", "tf"):
                continue
            r2 = np.array([r["r2"] for r in sub], dtype=float)
            print("   %-5s n=%3d  R² median %.3f, worst %.3g, collapses (R²<0) %d,"
                  " formula_exact False %d" % (
                      split_name, len(sub), np.median(r2), r2.min(),
                      int((r2 < 0).sum()),
                      sum(1 for r in sub if r.get("formula_exact") is False)))
        ood = [r["err_ood"] for r in rr if "err_ood" in r
               and r.get("status") != "EXACT"]
        if ood:
            print("   out of domain, models not exact: n=%d, median 1-R² %.3g,"
                  " collapses %d, worst R² %.3g" % (
                      len(ood), np.median(ood), sum(1 for o in ood if o > 1.0),
                      1.0 - max(ood)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=3)
    r.add_argument("--kinds", default=None)
    r.add_argument("--max-seconds", type=float, default=None)
    o = sub.add_parser("one")
    o.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        drive(a.python, a.out, a.workers,
              a.kinds.split(",") if a.kinds else None, a.max_seconds)
    elif a.cmd == "one":
        print(json.dumps(run_one(json.loads(a.job))))
    else:
        summary(a.path)


if __name__ == "__main__":
    main()
