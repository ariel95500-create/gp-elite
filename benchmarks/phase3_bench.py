"""Phase 3 (the units mode): timings, logs and equivalence on Feynman II.11.3.

benchmarks/results_0.9/PLAN_PHASE3.md. The data and the fit are those of the
typed and untyped arms of ab_ood.py (200 training points, test and
out-of-domain sets of 200 points, operators="physical", speed="fast",
restarts=1, 40 generations), with parallel=False; the generation counter is that of
typed_generations_check.py. One process per fit; the engine is the one the
interpreter imports (PYTHONPATH, or the installed package); PYTHONHASHSEED=0.

  python benchmarks/phase3_bench.py one <typed|untyped> <seed>
      one fit, prints one JSON record (with the engine's own log of the
      generations at which the best model improved)
  python benchmarks/phase3_bench.py side <out.jsonl> <seeds> <jobA> <jobB>
      for each seed, the two jobs run side by side (two processes at once,
      so every timing is taken under the same load); a job is
      label,python,pythonpath,arm (pythonpath empty: the installed package),
      e.g. 080,/venv08/bin/python,,typed ; seeds as 0-9 or 0,2,5 ;
      resumable: a (label, arm, seed) already in <out> is skipped
  python benchmarks/phase3_bench.py report <out.jsonl> [<out2.jsonl> ...]
  python benchmarks/phase3_bench.py e3 <out.jsonl> <python> [<pythonpath>]
  python benchmarks/phase3_bench.py e3_compare <a.jsonl> <b.jsonl>
      equivalence E3: the three laws of test_constante_mystere.py
"""
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, HERE)

GENS = 40
_GEN_RE = re.compile(r"\[GEN (\d+)\|I(\d+)\] FIT=(\S+) RAW=(\S+) SIZE=(\d+) "
                     r"DEPTH=\d+ \(([\d.]+)s\)")
_STOP_RE = re.compile(r"Precision target reached at GEN (\d+)")


def _cpu():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def one(arm, seed):
    import functools
    import io
    import warnings
    from contextlib import redirect_stdout

    import ab_ood
    import gp_elite
    import gp_elite.core as C
    import gp_elite.sklearn_api as SK
    from gp_elite import GPEliteRegressor
    from gp_elite import dim_search as DS
    from speed_equivalence import ser

    # the estimator has no verbose option: the engine prints its log into a
    # buffer either way (api.py), verbose only chooses where it goes
    SK.symbolic_regression = functools.partial(SK.symbolic_regression,
                                               verbose=True)
    gens = [0]
    calls = [0]
    orig = C.evolve_island

    def counted(*args, **kwargs):
        g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        calls[0] += 1
        return orig(*args, **kwargs)
    C.evolve_island = counted

    Xtr, ytr = ab_ood.make_data(200, seed)
    Xte, yte = ab_ood.make_data(200, seed + 5000)
    Xod, yod = ab_ood.make_data_ood(200, seed + 9000)
    # parallel=False as in phase 1: ab_ood.py leaves the default, which runs
    # the islands in parallel processes from four cores up; the 0.8 figures
    # (a 2-core container) ran them in sequence
    kw = dict(operators="physical", generations=GENS, speed="fast", restarts=1,
              random_state=seed, parallel=False)
    if arm == "typed":
        kw.update(units=ab_ood.UNITS, target_units=ab_ood.TARGET)
    elif arm != "untyped":
        raise SystemExit("arm: typed or untyped")
    buf = io.StringIO()
    t0 = time.time()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        est = GPEliteRegressor(**kw)
        with redirect_stdout(buf):
            est.fit(Xtr, ytr)
    dt = time.time() - t0
    with np.errstate(all="ignore"):
        pte = np.asarray(est.predict(Xte), dtype=float)
        pod = np.asarray(est.predict(Xod), dtype=float)
    r2t, r2o = ab_ood._r2(yte, pte), ab_ood._r2(yod, pod)
    try:
        ok_dim = bool(DS.is_typed_valid(est.model_.node, ab_ood.FEAT_DIMS,
                                        ab_ood.TARGET_DIM))
    except Exception:
        ok_dim = False
    log = buf.getvalue()
    impr = [[int(m.group(1)), int(m.group(2)), float(m.group(3)),
             float(m.group(4)), int(m.group(5)), float(m.group(6))]
            for m in _GEN_RE.finditer(log)]
    stop = _STOP_RE.search(log)
    rec = dict(
        arm=arm, seed=seed, generations=GENS,
        engine=gp_elite.__file__, version=gp_elite.__version__,
        python=platform.python_version(), numpy=np.__version__, cpu=_cpu(),
        pythonhashseed=os.environ.get("PYTHONHASHSEED"),
        date=time.strftime("%Y-%m-%dT%H:%M:%S"),
        seconds=round(dt, 2), generations_reached=gens[0],
        island_calls=calls[0], sec_per_gen=round(dt / max(gens[0], 1), 3),
        size=int(est.model_.size), r2_test=round(r2t, 6), r2_ood=round(r2o, 6),
        dim_ok=ok_dim, recovered=bool(r2o > 0.999 and ok_dim),
        node=ser(est.model_.node), expression=est.model_.expression[:400],
        pred_test_sha=hashlib.sha256(pte.tobytes()).hexdigest()[:16],
        pred_ood_sha=hashlib.sha256(pod.tobytes()).hexdigest()[:16],
        exact_stop_gen=int(stop.group(1)) if stop else None,
        improvements=impr)
    print(json.dumps(rec))


def one_e3(case):
    """Equivalence E3: one law of test_constante_mystere.py fitted as that
    script fits it (its defaults: 25 generations, 2 restarts, random_state=0,
    unknown_constant=True, parallel left to the engine)."""
    import warnings
    from contextlib import redirect_stdout
    import io

    import test_constante_mystere as TCM
    import gp_elite
    from gp_elite import GPEliteRegressor
    from speed_equivalence import ser, hx

    X, y, spec = getattr(TCM, case)()
    est = GPEliteRegressor(operators="physical", generations=25, speed="fast",
                           restarts=2, random_state=0, units=spec["units"],
                           target_units=spec["target_units"],
                           unknown_constant=True)
    t0 = time.time()
    with warnings.catch_warnings(), redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        est.fit(X, y)
    r = est.model_
    print(json.dumps(dict(
        case=case, engine=gp_elite.__file__, seconds=round(time.time() - t0, 2),
        node=ser(r.node), mse_validation=hx(r.mse_validation),
        constant_units=getattr(est, "constant_units_", None),
        constant_value=hx(getattr(est, "constant_value_", None)),
        pareto=[[p.size, ser(p.node), hx(p.mse_validation)]
                for p in (r.pareto or [])])))


def e3(out, py, pp):
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    if pp:
        env["PYTHONPATH"] = pp
    with open(out, "w") as fh:
        for case in ("cas_hooke", "cas_newton", "cas_gaz"):
            p = subprocess.run([py, os.path.abspath(__file__), "one_e3", case],
                               capture_output=True, text=True, env=env, cwd="/")
            line = (p.stdout.strip().splitlines() or [""])[-1]
            fh.write((line if p.returncode == 0 else json.dumps(
                dict(case=case, error=p.stderr[-500:]))) + "\n")
            print(case, "ok" if p.returncode == 0 else "FAILED", flush=True)


def e3_compare(a, b):
    ra = [json.loads(l) for l in open(a) if l.strip()]
    rb = [json.loads(l) for l in open(b) if l.strip()]
    same = True
    for x, y in zip(ra, rb):
        keys = [k for k in x if k not in ("engine", "seconds")]
        diff = [k for k in keys if x.get(k) != y.get(k)]
        same &= not diff and "error" not in x
        print("%-11s %s (%.1f s -> %.1f s)" % (
            x["case"], "same" if not diff else "DIFFERENT: %s" % diff,
            x.get("seconds", 0), y.get("seconds", 0)))
    print("ALL IDENTICAL" if same and len(ra) == len(rb) == 3 else "DIFFERENCES")


def _seeds(text):
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _job(spec):
    label, py, pp, arm = spec.split(",")
    return dict(label=label, python=py, pythonpath=pp, arm=arm)


def _done(out):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                r = json.loads(line)
                if "error" not in r:
                    done.add((r["label"], r["arm"], r["seed"]))
    return done


def side(out, seeds, specs):
    jobs = [_job(s) for s in specs]
    for seed in _seeds(seeds):
        done = _done(out)
        todo = [j for j in jobs if (j["label"], j["arm"], seed) not in done]
        if not todo:
            continue
        procs = []
        for j in todo:
            env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
            env.pop("PYTHONPATH", None)
            if j["pythonpath"]:
                env["PYTHONPATH"] = j["pythonpath"]
            procs.append((j, subprocess.Popen(
                [j["python"], os.path.abspath(__file__), "one", j["arm"], str(seed)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd="/")))
        for j, p in procs:
            so, se = p.communicate()
            try:
                rec = json.loads(so.strip().splitlines()[-1])
            except Exception:
                rec = dict(arm=j["arm"], seed=seed, error=se[-500:])
            rec["label"] = j["label"]
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print("%-8s %-8s seed %d  %s" % (
                j["label"], j["arm"], seed,
                "ERROR" if "error" in rec else "%.1f s, %d generations, %s" % (
                    rec["seconds"], rec["generations_reached"],
                    "exact" if rec["recovered"] else "not exact")), flush=True)


def _med(v):
    return float(np.median(v)) if v else float("nan")


def report(paths):
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(p) if l.strip()]
    errs = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    groups = {}
    for r in rows:
        groups.setdefault((r["label"], r["arm"]), {})[r["seed"]] = r
    print("| engine | arm | fits | median s | worst s | median s/gen | "
          "median generations | valid | exact | median OOD R² |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for (lab, arm), g in sorted(groups.items()):
        v = list(g.values())
        print("| %s | %s | %d | %.1f | %.1f | %.3f | %.0f | %d of %d | %d of %d | %.4f |" % (
            lab, arm, len(v), _med([r["seconds"] for r in v]),
            max(r["seconds"] for r in v), _med([r["sec_per_gen"] for r in v]),
            _med([r["generations_reached"] for r in v]),
            sum(r["dim_ok"] for r in v), len(v), sum(r["recovered"] for r in v),
            len(v), _med([r["r2_ood"] for r in v])))
    labels = sorted({lab for lab, _ in groups})
    for lab in labels:
        t, u = groups.get((lab, "typed"), {}), groups.get((lab, "untyped"), {})
        common = sorted(set(t) & set(u))
        if common:
            ratios = [t[s]["sec_per_gen"] / u[s]["sec_per_gen"] for s in common]
            print("\n%s: typed / untyped seconds per generation, per seed: "
                  "median %.2f, worst %.2f (%d seeds)" % (
                      lab, _med(ratios), max(ratios), len(common)))
    keys = ("node", "size", "pred_test_sha", "pred_ood_sha", "generations_reached")
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            for arm in ("typed", "untyped"):
                ga, gb = groups.get((a, arm), {}), groups.get((b, arm), {})
                common = sorted(set(ga) & set(gb))
                if not common:
                    continue
                diff = [s for s in common
                        if any(ga[s][k] != gb[s][k] for k in keys)]
                speed = [ga[s]["seconds"] / gb[s]["seconds"] for s in common]
                print("\n%s vs %s, %s, %d seeds: %s; time %s / %s per seed: "
                      "median %.2f, worst %.2f" % (
                          a, b, arm, len(common),
                          "same models" if not diff else "DIFFERENT on seeds %s" % diff,
                          a, b, _med(speed), min(speed)))
    if errs:
        print("\n%d failed fits: %s" % (len(errs), [(r.get("label"), r["arm"],
                                                      r["seed"]) for r in errs]))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == "side":
        side(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif sys.argv[1] == "report":
        report(sys.argv[2:])
    elif sys.argv[1] == "one_e3":
        one_e3(sys.argv[2])
    elif sys.argv[1] == "e3":
        e3(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif sys.argv[1] == "e3_compare":
        e3_compare(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
