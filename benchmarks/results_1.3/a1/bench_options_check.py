"""Check that the options added for plan 1.3 leave the other runs unchanged.

phase1_bench.py (--problems) and tp_diagnostic.py (--experiments), against
their versions of commit 496704b, before the options: the same jobs, and
without the option the same jobs kept by every run. Then the jobs each new
option keeps: Dtrig and TPsnell of benchmarks/results_1.3/PLAN.md. The
fits themselves are not changed by the options, which only choose jobs; the
TP worker gains the fields units_ok and units_msg on the units arm, and its
other fields are checked unchanged on two fits.

  python benchmarks/results_1.3/a1/bench_options_check.py
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
OLD = "496704b"
TRIG = ["II.15.4", "I.18.12", "III.15.12", "I.26.2", "I.30.5", "I.37.4",
        "I.50.26", "II.6.15b", "III.9.52", "III.17.37"]
DTRIG_KINDS = ["feyn", "ufeyn", "feyn_n1", "feyn_n10"]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    with redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m


def main():
    ok = True
    sys.path.insert(0, BENCH)
    with tempfile.TemporaryDirectory() as tmp:
        olds = {}
        for name in ("phase1_bench.py", "tp_diagnostic.py"):
            src = subprocess.run(["git", "-C", ROOT, "show",
                                  "%s:benchmarks/%s" % (OLD, name)],
                                 capture_output=True, text=True, check=True).stdout
            p = os.path.join(tmp, name)
            open(p, "w").write(src)
            olds[name] = p
        A = load(olds["phase1_bench.py"], "p1_old")
        B = load(os.path.join(BENCH, "phase1_bench.py"), "p1_new")
        for units in (False, True):
            ja, jb = A.all_jobs(units), B.all_jobs(units)
            print("phase1 jobs (units %s): old %d, new %d, the same: %s"
                  % (units, len(ja), len(jb), ja == jb))
            ok &= ja == jb
        jobs = B.all_jobs(True)
        for kinds in (None, ["feyn", "real"], DTRIG_KINDS):
            old = [j for j in jobs if kinds is None or j["kind"] in kinds]
            new = [j for j in jobs if B._keep(j, kinds)]
            print("phase1 without --problems, kinds %s: %d jobs, as before: %s"
                  % (kinds, len(new), old == new))
            ok &= old == new
        B.PROBLEMS = TRIG
        dtrig = [j for j in B.all_jobs(True) if B._keep(j, DTRIG_KINDS)]
        per = {k: sum(j["kind"] == k for j in dtrig) for k in DTRIG_KINDS}
        probs = sorted({j["problem"] for j in dtrig})
        seeds = sorted({j["seed"] for j in dtrig})
        print("phase1 --problems (Dtrig): %d jobs %s, %d problems, seeds %s"
              % (len(dtrig), per, len(probs), seeds))
        ok &= len(dtrig) == 200 and probs == sorted(TRIG) and seeds == [0, 1, 2, 3, 4]

        TA = load(olds["tp_diagnostic.py"], "tp_old")
        TB = load(os.path.join(BENCH, "tp_diagnostic.py"), "tp_new")
        for draws in (TB.DRAWS, (5, 6, 7, 8, 9)):
            ja, jb = TA.all_jobs(draws), TB.all_jobs(draws)
            print("TP jobs, draws %s: old %d, new %d, the same: %s"
                  % (list(draws), len(ja), len(jb), ja == jb))
            ok &= ja == jb
            for arm in (None, "plain", "units"):
                old = [j for j in ja if arm is None or j["arm"] == arm]
                new = [j for j in jb if TB._keep(j, arm, None)]
                ok &= old == new
            print("TP without --experiments, every arm: as before: %s" % ok)
            snell = [j for j in jb if TB._keep(j, None, ["snell"])]
            print("TP --experiments snell (TPsnell), draws %s: %d jobs, both arms %s"
                  % (list(draws), len(snell), sorted({j["arm"] for j in snell})))
            ok &= len(snell) == 40 and all(j["exp"] == "snell" for j in snell)

        # [1.3] the TP worker records units_ok on the units arm: every field
        # of the old record is the same, on two fits run with both versions
        # and the 1.2.0 wheel
        env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
                   OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        env.pop("PYTHONPATH", None)
        for m in os.listdir(BENCH):
            if m.endswith(".py") and m not in ("tp_diagnostic.py", "phase1_bench.py"):
                os.symlink(os.path.join(BENCH, m), os.path.join(tmp, m))

        def worker(script, job):
            p = subprocess.run(["/venv12p/bin/python", "-I", script, "worker",
                                json.dumps(job)], capture_output=True, text=True,
                               env=env, cwd="/")
            lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
            if p.returncode != 0 or not lines:
                raise SystemExit("worker failed: %s" % p.stderr[-400:])
            return json.loads(lines[-1])
        for job in (dict(exp="gaz", n=10, noise=0.02, draw=0, arm="units"),
                    dict(exp="snell", n=20, noise=0.05, draw=1, arm="plain")):
            ro = worker(olds["tp_diagnostic.py"], job)
            rn = worker(os.path.join(BENCH, "tp_diagnostic.py"), job)
            diff = [k for k in ro if k not in ("time", "date") and ro[k] != rn.get(k)]
            new_f = sorted(set(rn) - set(ro))
            print("TP worker %s: fields of the old record that differ: %s; new fields %s"
                  % (job, diff or "none", new_f))
            ok &= not diff and new_f == (["units_msg", "units_ok"]
                                         if job["arm"] == "units" else [])
    print("\nALL CHECKS HOLD" if ok else "\nA CHECK FAILS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
