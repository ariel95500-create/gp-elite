"""Diagnostic D0 of plan 1.2 (decides nothing): the typed start under units.

Why does III.19.51 under units take 600 to 735 s with time_limit=30? On
gp-elite 1.1.0 from PyPI, wrapped from outside without changing what it
draws or returns, each fit records:
- every call of Island.initialize: the island, its size n, the time from the
  start of the fit, its duration;
- inside it, every call of dim_search.typed_random_tree: success or None, its
  time, whether the fast path (_monomial_tree) gave the tree;
- every call of dim_search._build (the slow path): success, the steps of
  _build_ek it used out of its budget, and whether it ran out of budget;
- the typed mutations (typed_mutate) during the loop: their number and time;
- the time of the whole fit and its generations.

The wrappers draw no random number, so the trees built are those of 1.1.0;
only the times change a little. Item 3 of D0 (what makes the draws hard) is
computed without any fit by `python d0_start.py dims`.

Jobs: U41 seed 0 as phase1_bench.py runs it (generations=1000,
time_limit=30), and the units arm of the TP diagnostic, draw 0, under the
API defaults. One process per fit, PYTHONHASHSEED=0.

  python benchmarks/results_1.2/d0/d0_start.py run --python /venv11p/bin/python --workers 4
  python benchmarks/results_1.2/d0/d0_start.py dims
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)


def install():
    """Wrap the typed start; returns the dict the wrappers fill."""
    import gp_elite.core as C
    import gp_elite.dim_search as DS
    st = dict(t0=None, inits=[], mut_n=0, mut_t=0.0, cur=None)
    o_init, o_trt, o_mono = C.Island.initialize, DS.typed_random_tree, DS._monomial_tree
    o_build, o_mut = DS._build, DS.typed_mutate

    def initialize(self):
        rec = dict(island=self.id, role=getattr(self, "role", "?"),
                   stigmergic=bool(getattr(self, "stigmergic", False)),
                   n=self.cfg.POP_SIZE // self.cfg.N_ISLANDS,
                   max_init_depth=self.cfg.MAX_INIT_DEPTH,
                   at=time.time() - st["t0"], trt=0, trt_none=0, trt_t_ok=0.0,
                   trt_t_none=0.0, mono_ok=0, build=0, build_ok=0,
                   build_out=0, build_steps=0)
        st["cur"] = rec
        t = time.time()
        try:
            return o_init(self)
        finally:
            rec["dur"] = time.time() - t
            rec["pop"] = len(getattr(self, "population", []) or [])
            st["inits"].append(rec)
            st["cur"] = None

    def trt(*a, **k):
        t = time.time()
        r = o_trt(*a, **k)
        rec = st["cur"]
        if rec is not None:
            dt = time.time() - t
            rec["trt"] += 1
            if r is None:
                rec["trt_none"] += 1
                rec["trt_t_none"] += dt
            else:
                rec["trt_t_ok"] += dt
        return r

    def mono(*a, **k):
        r = o_mono(*a, **k)
        if r is not None and st["cur"] is not None:
            st["cur"]["mono_ok"] += 1
        return r

    def build(target, depth, feats, rng, cache, budget, ops=None):
        b0 = budget[0]
        r = o_build(target, depth, feats, rng, cache, budget, ops)
        rec = st["cur"]
        if rec is not None:
            rec["build"] += 1
            rec["build_ok"] += r is not None
            rec["build_out"] += budget[0] <= 0
            rec["build_steps"] += b0 - max(budget[0], 0)
        return r

    def mut(*a, **k):
        t = time.time()
        try:
            return o_mut(*a, **k)
        finally:
            if st["cur"] is None:
                st["mut_n"] += 1
                st["mut_t"] += time.time() - t
    C.Island.initialize = initialize
    DS.typed_random_tree, DS._monomial_tree = trt, mono
    DS._build, DS.typed_mutate = build, mut
    return st


def gen_counter():
    import gp_elite.core as C
    g = [0]
    orig = C.evolve_island

    def counted(*a, **k):
        x = a[3] if len(a) > 3 else k.get("generation", 0)
        g[0] = max(g[0], int(x) + 1)
        return orig(*a, **k)
    C.evolve_island = counted
    return g


def one(job):
    import warnings
    import numpy as np
    import gp_elite
    st = install()
    g = gen_counter()
    if job["bench"] == "u41":
        import decision_bench as D
        import phase1_bench as P1
        import units_table as U
        Xtr, ytr, _Xte, _yte, _Xo, _yo, names, pool = D.feyn_data(job["index"])
        units, tunits = U.units_of(job["problem"], names)
        kw = dict(generations=P1.GENERATIONS, time_limit=P1.TIME_LIMIT,
                  seed=job["seed"], parallel=False, verbose=False,
                  operators=pool, feature_names=names, units=units,
                  target_units=tunits)
        st["t0"] = time.time()
        with redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = gp_elite.symbolic_regression(Xtr, ytr, **kw)
        expr = r.expression
    else:
        import tp_diagnostic as TP
        orig = gp_elite.symbolic_regression

        def timed(X, y, **kw):
            st["t0"] = time.time()
            return orig(X, y, **kw)
        gp_elite.symbolic_regression = timed     # tp_diagnostic imports it in worker()
        rec = TP.worker({k: job[k] for k in ("exp", "n", "noise", "draw", "arm")})
        expr = rec.get("expr", "")
    total = time.time() - st["t0"]
    inits = st["inits"]
    start = max((i["at"] + i["dur"] for i in inits), default=0.0)
    return dict(job, total=round(total, 2), generations=g[0],
                start_end=round(start, 2),
                init_time=round(sum(i["dur"] for i in inits), 2),
                mut_n=st["mut_n"], mut_t=round(st["mut_t"], 2),
                inits=inits, expr=str(expr)[:160],
                engine_version=gp_elite.__version__,
                engine_file=gp_elite.__file__,
                pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                numpy=np.__version__)


def jobs():
    import feynman_bench as F
    import tp_diagnostic as TP
    out = [dict(bench="u41", problem=p[0], index=i, seed=0)
           for i, p in enumerate(F.PROBS)]
    out += [dict(bench="tp", **j) for j in TP.all_jobs()
            if j["arm"] == "units" and j["draw"] == 0]
    # the slowest first, so that it runs beside the others
    out.sort(key=lambda j: j.get("problem") != "III.19.51")
    return out


def key(j):
    return json.dumps({k: j.get(k) for k in ("bench", "problem", "seed", "exp",
                                              "n", "noise", "draw")},
                      sort_keys=True)


def drive(python, workers):
    out = os.path.join(HERE, "d0_start.jsonl")
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
            if n % 10 == 0:
                print("%d done" % n, flush=True)
    print("all done", flush=True)


def dims():
    """Item 3: for each U41 equation, the integer exponents that build the
    target from the input units (least squares, as _monomial_tree solves
    it), their sum and largest value against the limits of _monomial_tree
    (sum at most 8, each at most 4), and the dimensionless inputs."""
    import numpy as np
    import units_table as U
    rows = []
    for name, (feats, target, _n) in U.UNITS41.items():
        bases = sorted({b for d in feats for b in d} | set(target))
        if not bases:
            rows.append(dict(problem=name, exps=[0] * len(feats), sum=0,
                             max=0, fast_path=False, dimless_target=True,
                             dimless_inputs=len(feats), rank=0))
            continue
        V = np.array([[float(d.get(b, 0)) for d in feats] for b in bases])
        y = np.array([float(target.get(b, 0)) for b in bases])
        sol, *_ = np.linalg.lstsq(V, y, rcond=None)
        e = np.round(sol)
        exact = bool(np.linalg.norm(V @ e - y) < 1e-6)
        rows.append(dict(problem=name, exps=[float(x) for x in sol],
                         rounded=[int(x) for x in e], rounded_exact=exact,
                         sum=int(np.abs(e).sum()), max=int(np.abs(e).max()),
                         fast_path=bool(exact and np.abs(e).sum() <= 8
                                        and np.abs(e).max() <= 4 and
                                        np.abs(e).sum() > 0),
                         dimless_target=not any(abs(v) > 1e-9 for v in target.values()),
                         dimless_inputs=sum(1 for d in feats if not d),
                         rank=int(np.linalg.matrix_rank(V)),
                         n_inputs=len(feats), n_bases=len(bases)))
    with open(os.path.join(HERE, "d0_dims.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    for r in rows:
        print("%-10s fast path %-5s sum %2d max %d  rounded %s exact %s" % (
            r["problem"], r["fast_path"], r["sum"], r["max"],
            r.get("rounded"), r.get("rounded_exact")))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--workers", type=int, default=4)
    o = sub.add_parser("one")
    o.add_argument("job")
    sub.add_parser("dims")
    a = ap.parse_args()
    if a.cmd == "one":
        buf = io.StringIO()
        with redirect_stdout(buf):
            rec = one(json.loads(a.job))
        print(json.dumps(rec, default=str))
    elif a.cmd == "dims":
        dims()
    else:
        drive(a.python, a.workers)


if __name__ == "__main__":
    main()
