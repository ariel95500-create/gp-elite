"""Check that the options added for plan 1.3 leave the other runs unchanged.

phase1_bench.py (--problems) and tp_diagnostic.py (--experiments), against
their versions of commit 496704b, before the options: the same jobs, and
without the option the same jobs kept by every run. Then the jobs each new
option keeps: Dtrig and TPsnell of benchmarks/results_1.3/PLAN.md. The
fits themselves are not changed by the options, which only choose jobs.

  python benchmarks/results_1.3/a1/bench_options_check.py
"""
import importlib.util
import io
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
    print("\nALL CHECKS HOLD" if ok else "\nA CHECK FAILS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
