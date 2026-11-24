"""The profiles of Part B of ../../PLAN.md, after the campaign, deciding
nothing: where the time of a fit goes as the table grows.

Written before any profile was run. Three equations of F41, the first with
two, four and six variables, at each size of each axis of size_bench.py:
100, 1,000, 10,000 and 100,000 rows, and 1,000 rows with 5, 10 and 20 added
variables, so seven sizes and 21 fits. Each fit on the data of the campaign
(size_bench.data), seed 0, 20 generations and no time limit (so the fit does
the same work on any machine), parallel=False, one restart, the pool of
operators of its equation. Engine: 1.4.0 from PyPI (/venv14p), whose core.py
is the one of 6dc1e35 (check_engine.sh), so the sections of the map of
core.py hold for its line numbers.

Each fit runs twice, each time in its own process (PYTHONHASHSEED=0, one
BLAS thread, run from /tmp), one fit at a time, with nothing else running:

  plain     timed by phase through a wrap of evolve_island: to the first
            generation (the setup and the seeds), the generations (to the
            return of the last call), after the last generation (the final
            choice, its polish and the result);
  profiled  under cProfile, for the kind of work. The own time of a
            function of gp_elite/core.py goes to the role of its section in
            the map of core.py (../split/map_core.py, ROLES); the code that
            compile_to_numpy and compile_parametric generate is "evaluate";
            the other modules of the package are "other modules"; the time
            of code outside the package (NumPy, built-ins, the wrap) goes to
            the functions of the package that called it, in proportion to
            the time of each call. The roles are grouped:
              evaluating formulas  evaluate, numeric, fitness (the
                                   predictions, the scaling, the errors)
              fitting constants    constants (Levenberg-Marquardt, Adam)
              placing seeds        seeds
              final choice         selection
              the rest             the other roles and modules
            Own time only: the errors computed for a seed count as
            evaluating, not as placing seeds. Beside, inclusive: the time
            under the five seed makers and under the two constant fitters.
            cProfile slows Python code more than NumPy code, so its shares
            lean to the Python side; the plain run is the reference for
            times. The two runs must return the same formula.

  python profile_size.py run /venv14p/bin/python profiles.jsonl
  python profile_size.py show profiles.jsonl
"""
import argparse
import collections
import cProfile
import io
import json
import os
import pstats
import subprocess
import sys
import time
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "split"))

SIZES = ["r100", "r1000", "r10000", "r100000", "k5", "k10", "k20"]
GENERATIONS = 20
SEED = 0
GROUPS = [("evaluating formulas", ("evaluate", "numeric", "fitness")),
          ("fitting constants", ("constants",)),
          ("placing seeds", ("seeds",)),
          ("final choice", ("selection",))]
REST = "the rest"
# the five seed makers that evolve calls, and the two constant fitters (the
# Adam fitter may call the Levenberg-Marquardt one: counted once)
SEED_MAKERS = {4113: "_make_motif_seeds", 4329: "_make_power_law_seeds",
               4637: "_make_binomial_seeds", 5404: "_make_elementary_seeds",
               5609: "_make_tolerant_seeds"}
FITTERS = {6441: "optimize_constants_lm", 6603: "optimize_constants_adam"}
ENGINE_COMMIT = "6dc1e35"        # the merge of 1.4.0, whose core.py the map reads


def equations():
    """The first equation of F41 with two, four and six variables."""
    import feynman_bench as F
    return [next(i for i, p in enumerate(F.PROBS) if p[2] == nv) for nv in (2, 4, 6)]


def _wrap(C, name, new):
    orig = getattr(C, name)
    held = [m for k, m in list(sys.modules.items())
            if (k == "gp_elite" or k.startswith("gp_elite."))
            and getattr(m, name, None) is orig]
    for m in held:
        setattr(m, name, new)

    def undo():
        for m in held:
            setattr(m, name, orig)
    return undo


# ────────────────────────────────────────────────────── attribution ──

def attribute(prof, core_file):
    """The own time of the profiled call by role, the code outside the
    package given to its callers in the package."""
    from map_core import ROLES
    st = pstats.Stats(prof).stats       # func -> (cc, nc, tt, ct, callers)
    core_file = os.path.realpath(core_file)
    pkg = os.path.dirname(core_file) + os.sep

    def role(func):
        fn, line, name = func
        real = os.path.realpath(fn) if fn and not fn.startswith(("<", "~")) else fn
        if real == core_file:
            for a, b, mod, _what in ROLES:
                if a <= line <= b:
                    return mod
            return "core, outside the map"
        if real.startswith(pkg):
            return "other modules"
        if fn == "<string>" and name == "_f":
            return "evaluate"           # the code compile_* generate
        return None

    roleof = {f: role(f) for f in st}

    def shares(f, idx):
        """The callers of f, by the time of their calls: own time (idx 2) or
        time under f (idx 3)."""
        ws = {c: v[idx] for c, v in st[f][4].items()
              if c in st and c != f and v[idx] > 0}
        tot = sum(ws.values())
        return {c: w / tot for c, w in ws.items()} if tot > 0 else {}

    # route[f]: how time spent under a function outside the package is shared
    # among the roles of the package functions above it (a fixed point, so
    # that cycles outside the package, such as copy.deepcopy, end)
    outside = [f for f in st if roleof[f] is None]
    up = {f: shares(f, 3) for f in outside}
    route = {f: {} for f in outside}
    for _ in range(200):
        new = {}
        for f in outside:
            acc = collections.Counter()
            for c, w in up[f].items():
                if roleof[c] is not None:
                    acc[roleof[c]] += w
                else:
                    for r, x in route[c].items():
                        acc[r] += w * x
            new[f] = acc
        route = new

    roles = collections.Counter()
    total = lost = 0.0
    for f, (_cc, _nc, tt, _ct, _callers) in st.items():
        total += tt
        if tt <= 0:
            continue
        if roleof[f] is not None:
            roles[roleof[f]] += tt
            continue
        given = 0.0
        for c, w in shares(f, 2).items():
            if roleof[c] is not None:
                roles[roleof[c]] += tt * w
                given += tt * w
            else:
                for r, x in route[c].items():
                    roles[r] += tt * w * x
                    given += tt * w * x
        lost += tt - given

    groups = collections.Counter()
    for r, t in roles.items():
        g = next((name for name, members in GROUPS if r in members), REST)
        groups[g] += t

    def core_funcs(names, wanted_role):
        found = {f: v for f, v in st.items()
                 if os.path.realpath(f[0]) == core_file and f[2] in names}
        for f in found:
            if roleof[f] != wanted_role:
                raise RuntimeError("%s is not where the map of 1.4.0 puts it" % (f,))
        return found
    core_funcs({"evolve_island"}, "islands")
    makers = core_funcs(set(SEED_MAKERS.values()), "seeds")
    fitters = core_funcs(set(FITTERS.values()), "constants")
    seeds_incl = sum(v[3] for v in makers.values())
    fit_incl = sum(cv[3] for v in fitters.values() for c, cv in v[4].items()
                   if c not in fitters)

    top = sorted(st.items(), key=lambda kv: -kv[1][2])[:15]
    return dict(
        prof_total=round(total, 4),
        roles={r: round(t, 4) for r, t in sorted(roles.items(), key=lambda kv: -kv[1])},
        groups={g: round(groups.get(g, 0.0), 4) for g in [n for n, _m in GROUPS] + [REST]},
        unattributed=round(lost, 4),
        inclusive=dict(seed_makers=round(seeds_incl, 4),
                       constant_fitters=round(fit_incl, 4)),
        top=[dict(func="%s:%d %s" % (os.path.basename(f[0]), f[1], f[2]),
                  role=roleof[f], own=round(v[2], 4), calls=v[1]) for f, v in top])


# ─────────────────────────────────────────────────────────── worker ──

def one(mode, eq, cell):
    import warnings
    import numpy as np
    import gp_elite
    import gp_elite.core as C
    import decision_bench as D
    import size_bench as SB
    from gp_elite import symbolic_regression

    Xtr, ytr, Xte, yte, names, pool, added = SB.data(eq, cell)
    marks = dict(first=None, last=None, gens=0)
    orig = C.evolve_island

    def counted(*args, **kwargs):
        if marks["first"] is None:
            marks["first"] = time.perf_counter()
        g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
        marks["gens"] = max(marks["gens"], int(g) + 1)
        try:
            return orig(*args, **kwargs)
        finally:
            marks["last"] = time.perf_counter()
    undo = _wrap(C, "evolve_island", counted)

    kw = dict(generations=GENERATIONS, seed=SEED, parallel=False, verbose=False,
              operators=pool, feature_names=names)
    prof = cProfile.Profile() if mode == "profiled" else None
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t0 = time.perf_counter()
        if prof is not None:
            prof.enable()
        r = symbolic_regression(Xtr, ytr, **kw)
        if prof is not None:
            prof.disable()
        t1 = time.perf_counter()
    undo()
    if marks["gens"] == 0:
        raise RuntimeError("the wrap of evolve_island was not called")

    e = D.one_minus_r2(yte, r.predict(Xte))
    rec = dict(mode=mode, eq=eq, cell=cell, n_train=int(len(ytr)),
               n_features=len(names), seed=SEED, generations_budget=GENERATIONS,
               time=round(t1 - t0, 4),
               to_first_gen=round(marks["first"] - t0, 4),
               generations_time=round(marks["last"] - marks["first"], 4),
               after_last_gen=round(t1 - marks["last"], 4),
               generations=marks["gens"],
               status="EXACT" if e < 1e-9 else "NEAR" if e < 1e-3 else "MISS",
               err=e, expr=r.expression[:160],
               engine_file=gp_elite.__file__,
               engine_version=getattr(gp_elite, "__version__", "?"),
               python=sys.version.split()[0], numpy=np.__version__,
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               date=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if prof is not None:
        rec.update(attribute(prof, C.__file__))
    return rec


# ─────────────────────────────────────────────────────────── driver ──

def run(python, out):
    jobs = [(eq, cell, mode) for eq in equations() for cell in SIZES
            for mode in ("plain", "profiled")]
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                r = json.loads(line)
                done.add((r["eq"], r["cell"], r["mode"]))
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    # the sections of the map hold only for the core.py of 1.4.0
    import hashlib
    engine = subprocess.run([python, "-I", "-c", "import gp_elite.core as C; print(C.__file__)"],
                            capture_output=True, text=True, env=env, cwd="/tmp",
                            check=True).stdout.strip()
    ref = subprocess.run(["git", "-C", HERE, "show", "%s:gp_elite/core.py" % ENGINE_COMMIT],
                         capture_output=True, check=True).stdout
    if hashlib.sha256(open(engine, "rb").read()).digest() != hashlib.sha256(ref).digest():
        raise RuntimeError("%s is not the core.py of %s" % (engine, ENGINE_COMMIT))
    cpu = subprocess.run(["lscpu"], capture_output=True, text=True).stdout
    model = next((l.split(":", 1)[1].strip() for l in cpu.splitlines()
                  if l.startswith("Model name")), "?")
    for eq, cell, mode in jobs:
        if (eq, cell, mode) in done:
            continue
        p = subprocess.run([python, os.path.abspath(__file__), "one", mode,
                            str(eq), cell], capture_output=True, text=True,
                           env=env, cwd="/tmp")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        if p.returncode != 0 or not lines:
            raise RuntimeError("eq %d %s %s failed: %s" % (
                eq, cell, mode, (p.stderr or p.stdout)[-600:]))
        rec = json.loads(lines[-1])
        if not rec["engine_file"].startswith("/venv14p/"):
            raise RuntimeError("not the engine of PyPI: %s" % rec["engine_file"])
        rec["machine"] = model
        with open(out, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("eq %2d %-8s %-8s %7.2f s, %2d generations, %s" % (
            eq, cell, mode, rec["time"], rec["generations"], rec["status"]),
            flush=True)


def show(path):
    import feynman_bench as F
    recs = [json.loads(l) for l in open(path) if l.strip()]
    by = {(r["eq"], r["cell"], r["mode"]): r for r in recs}
    names = [n for n, _m in GROUPS] + [REST]
    short = ["eval", "const", "seeds", "final", "rest"]
    print("Profiles of Part B (deciding nothing): engine %s, seed %d, %d generations,"
          " no time limit" % (recs[0]["engine_version"], SEED, GENERATIONS))
    print("plain run: time and its phases (%% of it); profiled run: own time by"
          " kind (%% of the profiled time), its ratio to the plain time")
    for eq in sorted({r["eq"] for r in recs}):
        p = F.PROBS[eq]
        print()
        print("eq %d %s (%d variables): %s" % (eq, p[0], p[2], p[1]))
        print("%-8s %6s %4s %4s %-5s %8s %6s %6s %6s | %s %6s %5s" % (
            "size", "rows", "vars", "gens", "", "time s", "to 1st", "gens", "after",
            " ".join("%6s" % s for s in short), "x prof", "same"))
        for cell in SIZES:
            a, b = by.get((eq, cell, "plain")), by.get((eq, cell, "profiled"))
            if a is None:
                continue
            t = a["time"] or 1e-12
            line = "%-8s %6d %4d %4d %-5s %8.2f %5.0f%% %5.0f%% %5.0f%%" % (
                cell, a["n_train"], a["n_features"], a["generations"], a["status"],
                a["time"], 100 * a["to_first_gen"] / t, 100 * a["generations_time"] / t,
                100 * a["after_last_gen"] / t)
            if b is not None:
                tp = b["prof_total"] or 1e-12
                line += " | %s %6.2f %5s" % (
                    " ".join("%5.0f%%" % (100 * b["groups"][n] / tp) for n in names),
                    b["time"] / t, "yes" if b["expr"] == a["expr"] else "NO")
            print(line)
    lost = max((r["unattributed"] / (r["prof_total"] or 1e-12) for r in recs
                if r["mode"] == "profiled"), default=0.0)
    print()
    print("largest share of time not given to a role: %.2f %%" % (100 * lost))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("python")
    r.add_argument("out")
    o = sub.add_parser("one")
    o.add_argument("mode", choices=["plain", "profiled"])
    o.add_argument("eq", type=int)
    o.add_argument("cell", choices=SIZES)
    s = sub.add_parser("show")
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.python, a.out)
    elif a.cmd == "one":
        print(json.dumps(one(a.mode, a.eq, a.cell)))
    elif a.cmd == "show":
        show(a.path)


if __name__ == "__main__":
    main()
