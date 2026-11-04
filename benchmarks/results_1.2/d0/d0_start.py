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
  python benchmarks/results_1.2/d0/d0_start.py run --fastpath --python /venv11p/bin/python

  python benchmarks/results_1.2/d0/d0_start.py run --cure --python /venv11p/bin/python

The third asks whether a fast path accepting up to 12 factors would
change the typed start of these fits (see one_fastpath); the fourth runs
III.19.51 with it, as the U41 campaigns run it (see one_cure).
"""
import argparse
import collections
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


class _Stop(Exception):
    pass


def one_fastpath(job, max_terms=12, compare_max=50):
    """Would a fast path that accepts up to `max_terms` factors (1.1.0: 8)
    change the typed start? During the real start of the fit, each call of
    typed_random_tree runs as in 1.1.0; before it, the state of `random` is
    kept, the same call is replayed from that state with the wider fast
    path, the two trees are compared, and the state after the 1.1.0 call is
    put back, so the start goes on as in 1.1.0. The fit is stopped once its
    islands are built. On III.19.51 only the first `compare_max` calls are
    replayed (each 1.1.0 call there takes about a second)."""
    import random
    import warnings
    import gp_elite
    import gp_elite.core as C
    import gp_elite.dim_search as DS
    o_trt, o_mono, o_init = DS.typed_random_tree, DS._monomial_tree, C.Island.initialize
    st = dict(calls=0, compared=0, differ=0, wide_none=0, t8=0.0, t12=0.0,
              ex=[])

    def wide(target, feats, rng, max_terms_=8, ops=None, **k):
        return o_mono(target, feats, rng, max_terms=max_terms, ops=ops)

    def trt(*a, **k):
        s0 = random.getstate()
        t = time.time()
        r8 = o_trt(*a, **k)
        st["t8"] += time.time() - t
        s1 = random.getstate()
        st["calls"] += 1
        if st["compared"] < compare_max or job.get("problem") != "III.19.51":
            random.setstate(s0)
            DS._monomial_tree = wide
            t = time.time()
            try:
                r12 = o_trt(*a, **k)
            finally:
                DS._monomial_tree = o_mono
            st["t12"] += time.time() - t
            random.setstate(s1)
            st["compared"] += 1
            a8 = C.to_string(r8) if r8 is not None else None
            a12 = C.to_string(r12) if r12 is not None else None
            st["wide_none"] += r12 is None
            if a8 != a12:
                st["differ"] += 1
                if len(st["ex"]) < 3:
                    st["ex"].append([a8, a12])
        return r8

    def initialize(self):
        r = o_init(self)
        if getattr(self, "stigmergic", False):
            raise _Stop()
        return r
    DS.typed_random_tree, C.Island.initialize = trt, initialize
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            if job["bench"] == "u41":
                import decision_bench as D
                import phase1_bench as P1
                import units_table as U
                Xtr, ytr, _a, _b, _c, _d, names, pool = D.feyn_data(job["index"])
                units, tunits = U.units_of(job["problem"], names)
                gp_elite.symbolic_regression(
                    Xtr, ytr, generations=P1.GENERATIONS,
                    time_limit=P1.TIME_LIMIT, seed=job["seed"], parallel=False,
                    verbose=False, operators=pool, feature_names=names,
                    units=units, target_units=tunits)
            else:
                import tp_diagnostic as TP
                TP.worker({k: job[k] for k in ("exp", "n", "noise", "draw", "arm")})
            stopped = False
        except _Stop:
            stopped = True
    return dict(job, mode="fastpath", max_terms=max_terms, stopped=stopped,
                time=round(time.time() - t0, 2), calls=st["calls"],
                compared=st["compared"], differ=st["differ"],
                wide_none=st["wide_none"], t_1_1_0=round(st["t8"], 2),
                t_wide=round(st["t12"], 3), examples=st["ex"],
                engine_version=gp_elite.__version__,
                pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def one_cure(job, max_terms=12):
    """A fit of phase1_bench.run_one, as in the U41 campaigns, with the fast
    path accepting up to `max_terms` factors (1.1.0: 8). Prototype only."""
    import gp_elite.dim_search as DS
    import phase1_bench as P1
    o_mono = DS._monomial_tree

    def wide(target, feats, rng, max_terms_=8, ops=None, **k):
        return o_mono(target, feats, rng, max_terms=max_terms, ops=ops)
    DS._monomial_tree = wide
    rec = P1.run_one(job)
    rec.update(mode="cure", max_terms=max_terms)
    return rec


def cure_jobs():
    import feynman_bench as F
    i = [k for k, p in enumerate(F.PROBS) if p[0] == "III.19.51"][0]
    return [dict(kind=k, problem="III.19.51", index=i, split="test", seed=s)
            for k in ("ufeyn", "ufeyn_n1", "ufeyn_n10") for s in range(5)]


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


def drive(python, workers, fastpath=False, cure=False):
    out = os.path.join(HERE, "d0_cure.jsonl" if cure else
                       "d0_fastpath.jsonl" if fastpath else "d0_start.jsonl")
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    if cure:
        done = {json.dumps([r["kind"], r["seed"]]) for r in
                map(json.loads, open(out))} if os.path.exists(out) else set()
        todo = [j for j in cure_jobs() if json.dumps([j["kind"], j["seed"]]) not in done]
    else:
        todo = [j for j in jobs() if key(j) not in done]
    print("%d jobs to run" % len(todo), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def run(j):
        p = subprocess.run([python, os.path.abspath(__file__),
                            "cure-one" if cure else
                            "fastpath-one" if fastpath else "one",
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


def summary():
    """The figures of D0.md, from d0_start.jsonl, d0_dims.json and
    d0_fastpath.jsonl."""
    def load(n):
        p = os.path.join(HERE, n)
        return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
    R = [r for r in load("d0_start.jsonl") if r.get("status") != "CRASH"]
    print("## The typed start, fit by fit (d0_start.jsonl)\n")
    print("%d fits, %d crashes.\n" % (len(R), len(load("d0_start.jsonl")) - len(R)))
    print("| fit | start, s | whole fit, s | generations | typed draws | "
          "of which None | time of the None, s | fast path | slow path calls "
          "| out of budget | steps of _build_ek |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    R.sort(key=lambda r: -r["init_time"])
    for r in R:
        s = lambda k: sum(i[k] for i in r["inits"])
        name = r.get("problem") or "TP %s, %d pts, %d %%" % (
            r["exp"], r["n"], round(100 * r["noise"]))
        print("| %s | %.2f | %.1f | %d | %d | %d | %.1f | %d | %d | %d | %d |" % (
            name, r["init_time"], r["total"], r["generations"], s("trt"),
            s("trt_none"), s("trt_t_none"), s("mono_ok"), s("build"),
            s("build_out"), s("build_steps")))
    rest = [r["init_time"] for r in R if r.get("problem") != "III.19.51"]
    if rest:
        print("\nAll fits but III.19.51: start at most %.2f s.\n" % max(rest))
    for r in R:
        if r.get("problem") == "III.19.51":
            for i in r["inits"]:
                print("- III.19.51, island %d (%s): n %d, %d draws, %d None, "
                      "%.1f s, %d slow-path calls, %d out of budget" % (
                          i["island"], i["role"], i["n"], i["trt"],
                          i["trt_none"], i["dur"], i["build"], i["build_out"]))
            print()
    pd = os.path.join(HERE, "d0_dims.json")
    D = json.load(open(pd)) if os.path.exists(pd) else []
    if D:
        print("## The exponents the units ask for (d0_dims.json)\n")
        print("Equations whose target needs an exact product of the inputs "
              "with integer exponents, by the sum of their absolute values "
              "(fast path of 1.1.0: sum at most 8, each at most 4):\n")
        c = collections.Counter(r["sum"] for r in D if r.get("rounded_exact")
                                and r["sum"] > 0)
        print(", ".join("sum %d: %d" % (k, c[k]) for k in sorted(c)))
        print("\nAbove the limit: %s\n" % ", ".join(
            "%s (%s)" % (r["problem"], r["rounded"]) for r in D
            if r.get("rounded_exact") and (r["sum"] > 8 or r["max"] > 4)))
    F = [r for r in load("d0_fastpath.jsonl") if r.get("status") != "CRASH"]
    if F:
        print("## A fast path of up to 12 factors, replayed (d0_fastpath.jsonl)\n")
        print("%d fits, %d crashes, %d stopped after their start.\n" % (
            len(F), len(load("d0_fastpath.jsonl")) - len(F),
            sum(r["stopped"] for r in F)))
        ch = [r for r in F if r["differ"]]
        print("Fits whose start would change: %d (%s).\n" % (len(ch), ", ".join(
            r.get("problem") or r["exp"] for r in ch) or "none"))
        print("Typed draws compared: %d, of which different: %d.\n" % (
            sum(r["compared"] for r in F), sum(r["differ"] for r in F)))
        for r in ch:
            print("- %s: %d of %d compared draws differ; the %d draws of "
                  "1.1.0 took %.1f s; the %d replayed with the wider fast path "
                  "%.2f s; e.g. %s" % (
                      r.get("problem") or r["exp"], r["differ"], r["compared"],
                      r["calls"], r["t_1_1_0"], r["compared"], r["t_wide"],
                      r["examples"][:1]))
        print()
    K = [r for r in load("d0_cure.jsonl") if r.get("status") != "CRASH"]
    if K:
        print("## III.19.51 with that fast path, as the U41 campaigns run it "
              "(d0_cure.jsonl)\n")
        B = {}
        pb = os.path.join(HERE, "..", "..", "results_1.1", "campaign", "U41_U1.jsonl")
        if os.path.exists(pb):
            B = {(r["kind"], r["seed"]): r for r in map(json.loads, open(pb))
                 if r["problem"] == "III.19.51"}
        print("| kind | seed | status | structure | time, s | generations | "
              "units ok | 1.1 (U41_U1.jsonl): status, structure, time |")
        print("|---|---|---|---|---|---|---|---|")
        for r in sorted(K, key=lambda r: (r["kind"], r["seed"])):
            b = B.get((r["kind"], r["seed"]))
            print("| %s | %d | %s | %s | %.1f | %d | %s | %s |" % (
                r["kind"], r["seed"], r.get("status"), r.get("structure", "-"),
                r["time"], r["generations"], r.get("units_ok"),
                "%s, %s, %.1f" % (b["status"], b.get("structure", "-"), b["time"])
                if b else "-"))
        print()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--fastpath", action="store_true")
    r.add_argument("--cure", action="store_true")
    o = sub.add_parser("one")
    o.add_argument("job")
    f = sub.add_parser("fastpath-one")
    f.add_argument("job")
    c = sub.add_parser("cure-one")
    c.add_argument("job")
    sub.add_parser("dims")
    sub.add_parser("summary")
    a = ap.parse_args()
    if a.cmd in ("one", "fastpath-one", "cure-one"):
        buf = io.StringIO()
        fn = {"one": one, "fastpath-one": one_fastpath, "cure-one": one_cure}[a.cmd]
        with redirect_stdout(buf):
            rec = fn(json.loads(a.job))
        print(json.dumps(rec, default=str))
    elif a.cmd == "dims":
        dims()
    elif a.cmd == "summary":
        summary()
    else:
        drive(a.python, a.workers, a.fastpath, a.cure)


if __name__ == "__main__":
    main()
