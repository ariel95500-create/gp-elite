"""Check that the options added for plan 1.2 leave the other runs unchanged.

tp_diagnostic.py (--draws, and the fields generations, patience_stop,
err_train) and phase1_bench.py (--defaults), against their versions of
commit 85b198b: the same jobs, the same data, and the same records on a few
fits (every field of the old record, but the time and the date), with the
1.1.0 wheel of /venv11p. Then one fit of each new option.

  python benchmarks/results_1.2/h1/campaign/bench_options_check.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.dirname(BENCH)
PY = "/venv11p/bin/python"
OLD = "85b198b"


def old_copy(name, tmp):
    src = subprocess.run(["git", "-C", ROOT, "show", "%s:benchmarks/%s" % (OLD, name)],
                         capture_output=True, text=True, check=True).stdout
    p = os.path.join(tmp, name)
    open(p, "w").write(src)
    return p


def run(script, args, cwd):
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    p = subprocess.run([PY, script] + args, capture_output=True, text=True,
                       env=env, cwd=cwd)
    lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
    if p.returncode != 0 or not lines:
        raise SystemExit("%s %s failed: %s" % (script, args, p.stderr[-500:]))
    return json.loads(lines[-1])


def same(old, new, skip=("time", "date")):
    return [k for k in old if k not in skip and old[k] != new.get(k)]


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        # every helper module the old copies import comes from benchmarks/
        for m in os.listdir(BENCH):
            if m.endswith(".py") and m not in ("tp_diagnostic.py", "phase1_bench.py"):
                os.symlink(os.path.join(BENCH, m), os.path.join(tmp, m))
        for d in ("_pmlb_cache", "test_set"):
            if os.path.exists(os.path.join(BENCH, d)):
                os.symlink(os.path.join(BENCH, d), os.path.join(tmp, d))
        o_tp, o_p1 = old_copy("tp_diagnostic.py", tmp), old_copy("phase1_bench.py", tmp)
        n_tp, n_p1 = (os.path.join(BENCH, "tp_diagnostic.py"),
                      os.path.join(BENCH, "phase1_bench.py"))
        sys.path.insert(0, BENCH)
        import importlib.util

        def load(path, name):
            spec = importlib.util.spec_from_file_location(name, path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
        A, B = load(o_tp, "tp_old"), load(n_tp, "tp_new")
        ja, jb = A.all_jobs(), B.all_jobs()
        print("TP jobs: old %d, new %d, the same: %s" % (len(ja), len(jb), ja == jb))
        ok &= ja == jb

        def h(j, M):
            X, y, yc, Xg, yg = M.data(j["exp"], j["n"], j["noise"], j["draw"])
            return hashlib.sha256(b"".join(a.tobytes() for a in (X, y, yc, Xg, yg))).hexdigest()
        dsame = all(h(j, A) == h(j, B) for j in ja)
        print("TP data of the 400 jobs: the same: %s" % dsame)
        ok &= dsame
        j5 = B.all_jobs((5, 6, 7, 8, 9))
        print("TP --draws 5..9: %d jobs, draws %s, data distinct from draws 0-4: %s" % (
            len(j5), sorted({j["draw"] for j in j5}),
            not ({h(j, B) for j in j5} & {h(j, B) for j in jb})))
        for j in (dict(exp="gaz", n=10, noise=0.02, draw=0, arm="plain"),
                  dict(exp="rc", n=20, noise=0.05, draw=1, arm="units")):
            ro = run(o_tp, ["worker", json.dumps(j)], "/")
            rn = run(n_tp, ["worker", json.dumps(j)], "/")
            d = same(ro, rn)
            print("TP worker %s: fields of the old record that differ: %s; new fields %s"
                  % (j, d or "none", sorted(set(rn) - set(ro))))
            ok &= not d
        P, Q = load(o_p1, "p1_old"), load(n_p1, "p1_new")
        ka, kb = P.all_jobs(True), Q.all_jobs(True)
        print("phase1 jobs (with units): old %d, new %d, the same: %s" % (
            len(ka), len(kb), ka == kb))
        ok &= ka == kb
        for j in (dict(kind="feyn", problem="I.12.5", index=1, split="test", seed=0),
                  dict(kind="realraw", problem=Q.__dict__.get("_x", None) or
                       __import__("decision_bench").REAL_RAW[0], split="fold0", seed=0)):
            ro = run(o_p1, ["one", json.dumps(j)], ROOT)
            rn = run(n_p1, ["one", json.dumps(j)], ROOT)
            # a fit stopped by its time limit runs as many generations as
            # the clock allows: that count is not compared
            clock = ro.get("time_limit_reached") and rn.get("time_limit_reached")
            d = same(ro, rn, ("time", "date") + (("generations",) if clock else ()))
            print("phase1 one %s: fields that differ: %s%s" % (
                j, d or "none", " (time limit reached in both: generations "
                "%d and %d not compared)" % (ro["generations"], rn["generations"])
                if clock else ""))
            ok &= not d
        jd = dict(kind="feyn_n1", problem="I.12.5", index=1, split="test", seed=0,
                  defaults=True)
        rd = run(n_p1, ["one", json.dumps(jd)], ROOT)
        print("phase1 --defaults, %s: %d generations, %.1f s, defaults %s, status %s"
              % (jd["problem"], rd["generations"], rd["time"], rd.get("defaults"),
                 rd.get("status")))
    print("\nALL CHECKS HOLD" if ok else "\nA CHECK FAILS")


if __name__ == "__main__":
    main()
