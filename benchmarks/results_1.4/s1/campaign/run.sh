#!/bin/sh
# Campaign S1 (benchmarks/results_1.4/PLAN.md): the TP diagnostic, draws 0 to
# 4 (or the draws given, for the confirmation: 10,11,12,13,14), 1.3.0 from
# PyPI (A, the candidate before S1 since N2 is withdrawn) against the
# candidate with S1 (B, the wheel of 9d2c96d in /venv14s1), each job with
# both at the same time, two jobs at a time, from a copy of the benches at
# the commit given. Run as a background task of the session.
C=$1; TAG=$2; DRAWS=${3:-0,1,2,3,4}
RUN=/home/user/s1_run
O=/home/user/s1_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_${TAG}_$(date -u +%Y%m%dT%H%M).txt
echo "--- campaign S1 ($TAG, draws $DRAWS), benches of $(cat $RUN/COMMIT), kernel $(uname -r), $(date -u +%Y-%m-%dT%H:%M)"
/venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
  --python /venv13p/bin/python --out $O/tp_${TAG}_1.3.0.jsonl \
  --python /venv14s1/bin/python --out $O/tp_${TAG}_s1.jsonl \
  --workers 2 --draws $DRAWS
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
