#!/bin/sh
# Mechanics of S1, item 1 (benchmarks/results_1.4/PLAN.md): tables of 30 rows
# and more are untouched. From the repository root, once the wheel of the
# candidate with S1 is installed in /venv14s1. N2 was not adopted and is
# withdrawn, so the candidate before S1 is 1.3.0 itself (/venv13p).
#  (a) the 95 bounded fits of the mechanics of N2 (20 generations, no time
#      limit), with the candidate with S1, against the records of 1.3.0
#      made there (../../n2/mechanics/records/bounded_1.3.0.jsonl);
#  (b) the 13 reference configurations of speed_equivalence.py (60 rows and
#      more each), with 1.3.0 and the candidate, compared field by field.
set -e
D=benchmarks/results_1.4/s1/mechanics
M=benchmarks/results_1.4/n2/mechanics/mechanics.py
mkdir -p $D/records
/venv14s1/bin/python -I - "$M" "$D/records/bounded_s1.jsonl" <<'PY'
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
M, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(M))
sys.path.insert(1, os.path.normpath(os.path.join(os.path.dirname(M), "..", "..", "..")))
import mechanics as N
env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
env.pop("PYTHONPATH", None)
def one(job):
    p = subprocess.run(["/venv14s1/bin/python", "-I", os.path.abspath(M), "one-fit",
                        "/nonexistent", json.dumps(job)], capture_output=True,
                       text=True, env=env, cwd="/")
    lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
    return json.loads(lines[-1]) if p.returncode == 0 and lines else dict(job, crash=True)
with ThreadPoolExecutor(4) as ex:
    recs = list(ex.map(one, N._jobs_bounded()))
with open(out, "w") as fh:
    for r in recs:
        fh.write(json.dumps(r) + "\n")
print("%d bounded fits written" % len(recs))
PY
for e in 130:/venv13p s1:/venv14s1; do
  name=${e%%:*}; py=${e#*:}/bin/python
  rm -rf $D/records/equiv_$name
  PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    $py benchmarks/speed_equivalence.py run $D/records/equiv_$name > $D/records/equiv_$name.log 2>&1
done
/venv14s1/bin/python benchmarks/speed_equivalence.py compare \
  $D/records/equiv_130 $D/records/equiv_s1 > $D/equiv_compare.txt 2>&1 || true
/venv14s1/bin/python -I - <<'PY' > $D/bounded_compare.txt
import json
A = {(r["kind"], r["problem"]): r for r in map(json.loads,
     open("benchmarks/results_1.4/n2/mechanics/records/bounded_1.3.0.jsonl"))}
B = {(r["kind"], r["problem"]): r for r in map(json.loads,
     open("benchmarks/results_1.4/s1/mechanics/records/bounded_s1.jsonl"))}
diff = [k for k in A if (A[k]["expr"], A[k]["err"]) != (B[k]["expr"], B[k]["err"])]
print("engines: 1.3.0 %s; S1 %s" % (sorted({r.get("engine") for r in A.values()}),
                                 sorted({r.get("engine") for r in B.values()})))
print("the 95 bounded fits: the same model with the candidate as with 1.3.0 in %d of %d" % (len(A) - len(diff), len(A)))
for k in diff:
    print("  DIFFERS %s %s: %s / %s" % (k[0], k[1], A[k]["expr"][:70], B[k]["expr"][:70]))
PY
cat $D/bounded_compare.txt; tail -5 $D/equiv_compare.txt
