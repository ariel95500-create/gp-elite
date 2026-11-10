"""Mechanics 1 and 3 of change A1 (benchmarks/results_1.3/PLAN.md).

1. The pools without the arcsine are untouched: fits bounded by 20
   generations, with no time limit, on F41 seed 0 and U41 seed 0 (the 31
   equations of the pool physical) and on R6 and R7raw (fold 0 of each
   dataset); and the nine experiments of the TP diagnostic of the pool
   physical, both arms, draw 0, under the API defaults. Each engine runs
   every job in its own process; the records are then compared.
3. A fit of I.30.5 with the pool trig and generations=200 draws the
   arcsine (candidate only).

  python mechanics.py run --python /venv12p/bin/python --out m_1.2.0.jsonl
  python mechanics.py run --python /venv13a/bin/python --out m_a1.jsonl
  python mechanics.py compare m_1.2.0.jsonl m_a1.jsonl
  python mechanics.py find --python /venv13a/bin/python --out find.jsonl
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


def jobs():
    import feynman_bench as F
    import decision_bench as D
    import tp_diagnostic as TP
    out = []
    for kind in ("feyn", "ufeyn"):
        for i, p in enumerate(F.PROBS):
            if p[5] == "physical":
                out.append(dict(bench="phase1", kind=kind, problem=p[0], index=i,
                                split="test", seed=0))
    for kind, names in (("real", D.REAL), ("realraw", D.REAL_RAW)):
        for n in names:
            out.append(dict(bench="phase1", kind=kind, problem=n, split="fold0",
                            seed=0))
    for j in TP.all_jobs(draws=(0,)):
        if TP.experiment(j["exp"])[1]["pool"] == "physical":
            out.append(dict(j, bench="tp"))
    return out


def key(j):
    if j["bench"] == "tp":
        return ("tp", j["arm"], j["exp"], j["n"], j["noise"], j["draw"])
    return (j["bench"], j["kind"], j["problem"], j["split"], j["seed"])


def one(job):
    if job["bench"] == "phase1":
        import phase1_bench as B
        B.TIME_LIMIT, B.GENERATIONS = None, 20
        rec = B.run_one({k: v for k, v in job.items() if k != "bench"})
        keep = ("expr", "err", "size", "formula_exact", "units_ok", "generations",
                "engine_file", "engine_version", "time")
        return dict(job, **{k: rec.get(k) for k in keep})
    if job["bench"] == "tp":
        import tp_diagnostic as TP
        rec = TP.worker({k: v for k, v in job.items() if k != "bench"})
        keep = ("expr", "err_train", "err_grid", "law", "size", "generations",
                "patience_stop", "engine_file", "engine_version", "time")
        return dict(job, **{k: rec.get(k) for k in keep})
    if job["bench"] == "find":
        import warnings
        import decision_bench as D
        import gp_elite.core as C
        from gp_elite import symbolic_regression
        seen = {"offered": 0, "with_arcsin": 0}
        track0 = C._track_val_candidate

        def has_arcsin(t):
            return t is not None and (t.value == "arcsin" or has_arcsin(t.left)
                                      or has_arcsin(t.right))

        def track(cand):
            seen["offered"] += 1
            seen["with_arcsin"] += int(has_arcsin(cand))
            return track0(cand)
        C._track_val_candidate = track
        Xtr, ytr, Xte, yte, Xo, yo, names, pool = D.feyn_data(job["index"])
        t0 = time.time()
        with redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = symbolic_regression(Xtr, ytr, feature_names=names, operators="trig",
                                    generations=200, seed=job["seed"],
                                    parallel=False, verbose=False)
        e = D.one_minus_r2(yte, r.predict(Xte))
        return dict(job, expr=r.expression, err=e, status=("EXACT" if e < 1e-9 else
                    "NEAR" if e < 1e-3 else "MISS"), returned_arcsin=has_arcsin(r.node),
                    time=round(time.time() - t0, 1), **seen)
    raise ValueError(job)


def _env():
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    return env


def drive(python, js, out, workers):
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in js if key(j) not in done]
    print("%d jobs to run, %d done" % (len(todo), len(done)), flush=True)

    def run1(j):
        p = subprocess.run([python, "-I", os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True,
                           env=_env(), cwd="/")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        if p.returncode != 0 or not lines:
            return dict(j, crash=True, stderr=p.stderr[-500:])
        return json.loads(lines[-1])

    with ThreadPoolExecutor(workers) as ex, open(out, "a") as fh:
        for i, rec in enumerate(ex.map(run1, todo)):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if (i + 1) % 20 == 0:
                print("%d/%d %s" % (i + 1, len(todo), time.strftime("%H:%M:%S")),
                      flush=True)


def compare(a, b):
    A = {key(r): r for r in map(json.loads, open(a)) if True}
    B = {key(r): r for r in map(json.loads, open(b)) if True}
    fields = ("expr", "err", "size", "formula_exact", "units_ok", "generations",
              "err_train", "err_grid", "law", "patience_stop")
    same, diff, crash = 0, [], 0
    for k in sorted(A, key=str):
        ra, rb = A[k], B.get(k)
        if rb is None or ra.get("crash") or rb.get("crash"):
            crash += 1
            print("missing or crashed: %s" % (k,))
            continue
        d = [f for f in fields if ra.get(f) != rb.get(f)]
        if d:
            diff.append((k, d))
        else:
            same += 1
    groups = {}
    for k in A:
        g = k[0] if k[0] == "tp" else k[1]
        groups.setdefault(g, [0, 0])
        groups[g][1] += 1
        if k not in dict(diff) and k in B and not A[k].get("crash") \
                and not B[k].get("crash"):
            groups[g][0] += 1
    print("Fits compared: %d; identical in every field: %d; different: %d; "
          "missing or crashed: %d" % (len(A), same, len(diff), crash))
    for g, (s, n) in sorted(groups.items()):
        print("  %s: %d of %d identical" % (g, s, n))
    for k, d in diff:
        print("DIFFERENT %s: %s" % (k, d))
        print("    A: %s" % A[k].get("expr"))
        print("    B: %s" % B[k].get("expr"))
    print("ALL IDENTICAL" if not diff and not crash else "DIFFERENCES")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("job")
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    f = sub.add_parser("find")
    f.add_argument("--python", required=True)
    f.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    a = ap.parse_args()
    if a.cmd == "one":
        print(json.dumps(one(json.loads(a.job)), default=float))
    elif a.cmd == "run":
        drive(a.python, jobs(), a.out, a.workers)
    elif a.cmd == "find":
        import feynman_bench as F
        idx = [i for i, p in enumerate(F.PROBS) if p[0] == "I.30.5"][0]
        drive(a.python, [dict(bench="find", kind="find", problem="I.30.5", index=idx,
                              split="test", seed=0)], a.out, 1)
    else:
        compare(a.a, a.b)


if __name__ == "__main__":
    main()
