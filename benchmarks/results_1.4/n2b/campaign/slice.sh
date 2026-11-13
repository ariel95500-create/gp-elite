#!/bin/sh
# One slice of campaign N2b (benchmarks/results_1.4/PLAN.md, "Decision of the
# author after the campaigns of N2 and S1"): the candidate with the changes
# kept so far (A, its python and a name given) against the same with N2b (B,
# the wheel in /venv14n2b), every job with both at the same time, two jobs
# at a time, from a copy of the benches at the commit given.
#
#   sh slice.sh COMMIT A_PYTHON A_NAME main
#       the TP diagnostic (draws 0 to 4) if it is not done, else one slice of
#       at most 6,300 s of Dnoise and Dguard (1,360 jobs)
#   sh slice.sh COMMIT A_PYTHON A_NAME conf
#       one slice of the confirmation: feyn_n1 and feyn_n10 at seed 0, the
#       draws of the noise 1 to 4 (328 jobs)
#
# Run as a background task of the session; the benches resume where they
# stopped.
C=$1; PA=$2; NA=$3; TAG=${4:-main}
PB=/venv14n2b/bin/python
RUN=/home/user/n2b_run
O=/home/user/n2b_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/gp-elite/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
[ "$(cat $RUN/COMMIT)" = "$C" ] || { echo "the copy of the benches is of $(cat $RUN/COMMIT): stop"; exit 1; }
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_${TAG}_$(date -u +%Y%m%dT%H%M).txt
if [ "$TAG" = "conf" ]; then
  a=$(wc -l < $O/conf_$NA.jsonl 2>/dev/null || echo 0)
  b=$(wc -l < $O/conf_n2b.jsonl 2>/dev/null || echo 0)
  if [ "$a" -lt 328 ] || [ "$b" -lt 328 ]; then
    echo "--- confirmation, slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done), benches of $C, kernel $(uname -r)"
    /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
      --python $PA --out $O/conf_$NA.jsonl \
      --python $PB --out $O/conf_n2b.jsonl \
      --pairs 2 --kinds feyn_n1,feyn_n10 --seeds 0 --noise-draws 1,2,3,4 \
      --max-seconds 6300
    echo "--- slice ends $(date -u +%Y-%m-%dT%H:%M)"
    exit 0
  fi
  echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
t=$(wc -l < $O/tp_n2b.jsonl 2>/dev/null || echo 0)
if [ "$t" -lt 400 ]; then
  echo "--- TP (draws 0 to 4) $(date -u +%Y-%m-%dT%H:%M), benches of $C, kernel $(uname -r)"
  /venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
    --python $PA --out $O/tp_$NA.jsonl \
    --python $PB --out $O/tp_n2b.jsonl --workers 2 --draws 0,1,2,3,4
  echo "--- TP ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
K=feyn,real,realraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10
a=$(wc -l < $O/bench_$NA.jsonl 2>/dev/null || echo 0)
b=$(wc -l < $O/bench_n2b.jsonl 2>/dev/null || echo 0)
if [ "$a" -lt 1360 ] || [ "$b" -lt 1360 ]; then
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python $PA --out $O/bench_$NA.jsonl \
    --python $PB --out $O/bench_n2b.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
  echo "--- slice ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
