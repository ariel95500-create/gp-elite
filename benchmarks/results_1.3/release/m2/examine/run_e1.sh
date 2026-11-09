#!/bin/sh
# E1 of PLAN.md in this folder: I.18.12, kinds ufeyn_n10 and feyn_n10, seeds
# 5 to 24, 1.2.0 (/venv12p) against 1.3.0 (/venv13r), paired as in M2, from
# the copy of benchmarks/ of 7a09425 that M2 ran from.
RUN=/home/user/m2_13_run
O=/home/user/m2_13_examine
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- E1, bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r), $(date -u +%Y-%m-%dT%H:%M)"
/venv12p/bin/python benchmarks/phase1_bench.py run-paired \
  --python /venv12p/bin/python --out $O/e1_1.2.0.jsonl \
  --python /venv13r/bin/python --out $O/e1_1.3.0.jsonl \
  --pairs 2 --kinds ufeyn_n10,feyn_n10 --problems I.18.12 \
  --seeds 5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
