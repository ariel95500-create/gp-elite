"""Check that the two fields added to the records of phase1_bench.py for
campaign A3 (elementary_seed, tolerant_seed) change nothing else: two fits
bounded by 20 generations, run with the bench of commit 492863e and with the
bench of now, on the candidate /venv13c. Every field of the old record but
the time and the date must be the same.

  python benchmarks/results_1.3/a3/record_fields_check.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
OLD = "492863e"
PY = "/venv13c/bin/python"
WRAP = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import phase1_bench as B
B.TIME_LIMIT, B.GENERATIONS = None, 20
print(json.dumps(B.run_one(json.loads(sys.argv[2]))))
'''


def main():
    ok = True
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory() as tmp:
        for m in os.listdir(BENCH):
            if m.endswith(".py") and m != "phase1_bench.py":
                os.symlink(os.path.join(BENCH, m), os.path.join(tmp, m))
        src = subprocess.run(["git", "-C", ROOT, "show", "%s:benchmarks/phase1_bench.py" % OLD],
                             capture_output=True, text=True, check=True).stdout
        open(os.path.join(tmp, "phase1_bench.py"), "w").write(src)
        w = os.path.join(tmp, "wrap.py")
        open(w, "w").write(WRAP)
        for job in (dict(kind="feyn", problem="I.30.5", index=None, split="test", seed=0),
                    dict(kind="feyn_n1", problem="II.15.4", index=None, split="test", seed=1)):
            sys.path.insert(0, BENCH)
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                import feynman_bench as F
            job["index"] = [i for i, p in enumerate(F.PROBS) if p[0] == job["problem"]][0]
            recs = []
            for bench in (tmp, BENCH):
                p = subprocess.run([PY, "-I", w, bench, json.dumps(job)], capture_output=True,
                                   text=True, env=env, cwd="/")
                lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
                if p.returncode != 0 or not lines:
                    raise SystemExit("failed: %s" % p.stderr[-400:])
                recs.append(json.loads(lines[-1]))
            ro, rn = recs
            diff = [k for k in ro if k not in ("time", "date") and ro[k] != rn.get(k)]
            new = sorted(set(rn) - set(ro))
            print("%s %s seed %d: fields of the old record that differ: %s; new fields %s; "
                  "elementary_seed %s" % (job["kind"], job["problem"], job["seed"],
                                          diff or "none", new, rn.get("elementary_seed")))
            ok &= not diff and new == ["elementary_seed", "tolerant_seed"]
    print("\nALL CHECKS HOLD" if ok else "\nA CHECK FAILS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
