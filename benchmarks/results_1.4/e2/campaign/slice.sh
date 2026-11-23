#!/bin/sh
# One slice of campaign E2 (benchmarks/results_1.4/PLAN.md): 1.3.0 from PyPI
# (A) against the candidate with E2 (the wheel of 476a1a4 in /venv14e2, B),
# every job with both at the same time, two jobs at a time, from a copy of
# the benches at the commit given. A call runs the TP diagnostic (draws 0 to
# 4, or those given for the confirmation, TAG conf: 10,11,12,13,14) if it is
# not done, else one slice of at most 6,300 s of Dnoise and Dguard; run as a
# background task of the session, the benches resume.
C=$1; TAG=${2:-main}; DRAWS=${3:-0,1,2,3,4}
RUN=/home/user/e2_run
O=/home/user/e2_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/gp-elite/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_${TAG}_$(date -u +%Y%m%dT%H%M).txt
t=$(wc -l < $O/tp_${TAG}_e2.jsonl 2>/dev/null || echo 0)
if [ "$t" -lt 400 ]; then
  echo "--- TP $TAG (draws $DRAWS) $(date -u +%Y-%m-%dT%H:%M), benches of $(cat $RUN/COMMIT), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
    --python /venv13p/bin/python --out $O/tp_${TAG}_1.3.0.jsonl \
    --python /venv14e2/bin/python --out $O/tp_${TAG}_e2.jsonl --workers 2 --draws $DRAWS
  echo "--- TP ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
[ "$TAG" = "main" ] || { echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"; exit 0; }
K=feyn,real,realraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10
a=$(wc -l < $O/bench_1.3.0.jsonl 2>/dev/null || echo 0)
b=$(wc -l < $O/bench_e2.jsonl 2>/dev/null || echo 0)
if [ "$a" -lt 1360 ] || [ "$b" -lt 1360 ]; then
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv13p/bin/python --out $O/bench_1.3.0.jsonl \
    --python /venv14e2/bin/python --out $O/bench_e2.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
  echo "--- slice ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
