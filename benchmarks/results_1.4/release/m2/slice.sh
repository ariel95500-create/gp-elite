#!/bin/sh
# M2 of ../../PLAN_RELEASE_1.4.md: 1.3.0 from PyPI (/venv13p) against 1.4.0
# (the wheel of f6a36cd, /venv14r), every job with both at the same time, two
# jobs at a time, from a copy of benchmarks/ of the commit given, without the
# package, with the data cache of the M2 of 1.3 (124 files, each checked
# against its SHA-256 at every load). A call runs TP and TPT10 in one go if
# they are not done, else one slice of at most 6,300 s of the benches (3,092
# jobs); run as a background task of the session, the benches resume. The
# records are written outside the repository and copied in at the end.
C=$1
RUN=/home/user/rel14_m2_run
O=/home/user/rel14_m2_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/m2_13_run/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
[ "$(cat $RUN/COMMIT)" = "$C" ] || { echo "the copy of the benches is of $(cat $RUN/COMMIT): stop"; exit 1; }
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
[ "$(ls benchmarks/_pmlb_cache | wc -l)" -ge 124 ] || { echo "data cache incomplete: stop"; exit 1; }
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
t=$(cat $O/tp_1.4.0.jsonl 2>/dev/null | wc -l)
q=$(cat $O/tpt10_1.4.0.jsonl 2>/dev/null | wc -l)
if [ "$t" -lt 400 ] || [ "$q" -lt 400 ]; then
  echo "--- TP and TPT10 $(date -u +%Y-%m-%dT%H:%M), benches of $C, kernel $(uname -r)"
  /venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
    --python /venv13p/bin/python --out $O/tp_1.3.0.jsonl \
    --python /venv14r/bin/python --out $O/tp_1.4.0.jsonl --workers 2 --draws 0,1,2,3,4
  /venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
    --python /venv13p/bin/python --out $O/tpt10_1.3.0.jsonl \
    --python /venv14r/bin/python --out $O/tpt10_1.4.0.jsonl --workers 2 --draws 0,1,2,3,4 \
    --set tpt10
  echo "--- TP and TPT10 end $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
K=feyn,real,realraw,tf,ts,tr,trraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10,utf,tf_n1,tf_n10,utf_n1,utf_n10
a=$(cat $O/campaignR_1.3.0.jsonl 2>/dev/null | wc -l)
b=$(cat $O/campaignR_1.4.0.jsonl 2>/dev/null | wc -l)
if [ "$a" -lt 3092 ] || [ "$b" -lt 3092 ]; then
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv13p/bin/python --out $O/campaignR_1.3.0.jsonl \
    --python /venv14r/bin/python --out $O/campaignR_1.4.0.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
  echo "--- slice ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
