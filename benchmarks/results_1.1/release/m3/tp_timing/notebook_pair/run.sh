#!/bin/bash
# The TP notebook script, 1.0.0 and the second candidate in turn, alone on the machine.
T=$(cd "$(dirname "$0")" && pwd)  # tp_six_lois.py is ../../tp_six_lois.py, copied beside it for the run
for r in 1 2; do
  for v in 10x 11bx; do
    mkdir -p $T/run_${v}_$r && cd $T/run_${v}_$r
    PYTHONHASHSEED=0 /venv$v/bin/python -I $T/tp_six_lois.py > $T/tp_${v}_run$r.txt 2>&1
    echo "venv$v run $r done $(date '+%F %T')" >> $T/run.log
  done
done
echo "all done" >> $T/run.log
