#!/bin/bash
# The third and fourth prototypes of plan 1.2 (plateau_trace.py, then
# patience_try.py with P = 20, 10, 30), started when the second has ended,
# detached, four workers.
cd /home/user/gp-elite
D=benchmarks/results_1.2/prototype
until grep -q "^all done" $D/run2.log 2>/dev/null; do sleep 60; done
echo "start $(date -u '+%FT%H:%M:%SZ')" >> $D/run3.log
/venv11p/bin/python $D/plateau_trace.py run --python /venv11p/bin/python --out $D --workers 4 >> $D/run3.log 2>&1
echo "start $(date -u '+%FT%H:%M:%SZ')" >> $D/run4.log
/venv11p/bin/python $D/patience_try.py run --python /venv11p/bin/python --out $D --workers 4 --patience 20 10 30 >> $D/run4.log 2>&1
