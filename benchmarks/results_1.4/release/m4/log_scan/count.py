# -*- coding: utf-8 -*-
"""M4 of the release of 1.4.0, beside its criteria: how often does the scan
of the logarithm of N2b (core._elem_log_scan) meet a candidate whose form is
not finite on the data? There np.linalg.lstsq raises LinAlgError (LAPACK
prints "On entry to DLASCL ..."), and the try/except of
_make_tolerant_seeds drops every form of that pass for the fit.

Each job of M2 (benches, TP and TPT10) is run again with 1.4.0 for one
generation, which runs the noise-tolerant stage on the data of the fit; the
exceptions raised inside the passes of N2b are recorded. It decides nothing.

  /venv14r/bin/python count.py run OUT.jsonl     (4 processes)
  /venv14r/bin/python count.py report OUT.jsonl
"""
import io
import json
import os
import subprocess
import sys
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
KINDS = ("feyn,real,realraw,tf,ts,tr,trraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,"
         "ufeyn_n10,utf,tf_n1,tf_n10,utf_n1,utf_n10").split(",")


def _wrap(C, rec):
    for name in ("_make_elementary_seeds", "_make_binomial_seeds",
                 "_make_power_law_seeds", "_elem_log_scan"):
        orig = getattr(C, name)

        def w(*a, _orig=orig, _name=name, **kw):
            try:
                return _orig(*a, **kw)
            except Exception as exc:
                rec.append("%s(%s): %s" % (_name, ",".join(sorted(kw)), type(exc).__name__))
                raise
        setattr(C, name, w)


def one_bench(job):
    import phase1_bench as B
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    rec = []
    _wrap(C, rec)
    Xtr, ytr, _a, _b, _c, _d, names, pool, _clean = B._data(job)
    kw = dict(generations=1, seed=job["seed"], parallel=False, verbose=False, operators=pool)
    if names is not None:
        kw["feature_names"] = names
    if job["kind"] in B.UNITS_ON:                     # as phase1_bench.run_one
        import units_table as U
        units, tunits = (U.units_of_tf(job["problem"], names)
                         if job["kind"] in B.TF_KINDS
                         else U.units_of(job["problem"], names))
        kw.update(units=units, target_units=tunits)
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(Xtr, ytr, **kw)
    return dict(set="bench", kind=job["kind"], problem=job["problem"], split=job["split"],
                seed=job["seed"], stage_ran="tolerant_seed_s" in C.TRACE.value, errors=rec)


def one_tp(job, exp_set):
    import tp_diagnostic as T
    import gp_elite.core as C
    rec = []
    _wrap(C, rec)
    T.worker(job)
    return dict(set=exp_set, arm=job["arm"], exp=job["exp"], n=job["n"], noise=job["noise"],
                draw=job["draw"], stage_ran="tolerant_seed_s" in C.TRACE.value, errors=rec)


def child(chunk):
    sys.path.insert(0, BENCH)
    out = []
    for kind, job in chunk:
        try:
            out.append(one_bench(job) if kind == "bench" else one_tp(job, kind))
        except Exception as exc:                      # noqa: BLE001
            out.append(dict(set=kind, job=job, crash=repr(exc)[:200]))
    return out


def run(path):
    sys.path.insert(0, BENCH)
    with redirect_stdout(io.StringIO()):
        import phase1_bench as B
        import tp_diagnostic as T
        jobs = [("bench", j) for j in B.all_jobs(True, True) if j["kind"] in KINDS]
    jobs += [("tp", j) for j in T.all_jobs()] + [("tpt10", j) for j in T.all_jobs(exp_set="tpt10")]
    chunks = [jobs[i::16] for i in range(16)]
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def go(chunk):
        p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "child",
                            json.dumps(chunk)], capture_output=True, text=True, env=env, cwd="/")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("[")]
        return json.loads(lines[-1]) if lines else [dict(crash=p.stderr[-300:])]
    with ThreadPoolExecutor(4) as ex:
        res = [r for rr in ex.map(go, chunks) for r in rr]
    with open(path, "w", encoding="utf-8") as fh:
        for r in res:
            fh.write(json.dumps(r) + "\n")


def report(path):
    R = [json.loads(ln) for ln in open(path, encoding="utf-8")]
    print("%d fits, crashes %d" % (len(R), sum("crash" in r for r in R)))
    for s in ("bench", "tp", "tpt10"):
        rr = [r for r in R if r.get("set") == s and "crash" not in r]
        hit = [r for r in rr if r["errors"]]
        print("%s: %d fits, the noise-tolerant stage runs in %d; a pass of N2b raises in %d"
              % (s, len(rr), sum(r["stage_ran"] for r in rr), len(hit)))
        c = Counter(e for r in hit for e in set(r["errors"]))
        for e, v in c.most_common():
            print("    %3d fits: %s" % (v, e))
        by = Counter((r.get("kind") or r.get("exp")) for r in hit)
        print("    by kind or experiment: %s" % dict(by))


if __name__ == "__main__":
    if sys.argv[1] == "child":
        print(json.dumps(child(json.loads(sys.argv[2]))))
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        report(sys.argv[2])
