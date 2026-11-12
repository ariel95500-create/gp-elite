#!/bin/sh
# Campaign N2 of benchmarks/results_1.4/PLAN.md: 1.3.0 from PyPI (/venv13p,
# A) against the candidate with N2 (the wheel of f748793 in /venv14n2, B),
# every job with both at the same time, two jobs at a time: Dnoise and
# Dguard (phase1_bench.py, 1,360 jobs), in time slices of 6,300 s until
# every job is done, then the TP diagnostic (tp_diagnostic.py, draws 0 to 4,
# 400 jobs). The benches run from a copy of the repository at the commit
# given (without the package), with the data cache of the bench, so that
# edits of the repository during the campaign do not touch them; the
# records are written outside the repository and copied in by
# checkpoint.sh.
C=$1                                  # the commit whose benchmarks/ run
RUN=/home/user/n2_run
O=/home/user/n2_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/gp-elite/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
K=feyn,real,realraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- campaign N2, benches of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r), $(nproc --all) cores"
while :; do
  a=$(wc -l < $O/bench_1.3.0.jsonl 2>/dev/null || echo 0)
  b=$(wc -l < $O/bench_candidate.jsonl 2>/dev/null || echo 0)
  [ "$a" -ge 1360 ] && [ "$b" -ge 1360 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv13p/bin/python --out $O/bench_1.3.0.jsonl \
    --python /venv14n2/bin/python --out $O/bench_candidate.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
done
echo "--- TP $(date -u +%Y-%m-%dT%H:%M)"
/venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
  --python /venv13p/bin/python --out $O/tp_1.3.0.jsonl \
  --python /venv14n2/bin/python --out $O/tp_candidate.jsonl --workers 2
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
