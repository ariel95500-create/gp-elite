#!/bin/bash
# The second prototype of plan 1.2 (units_rejected.py), started when the first
# has ended, detached, four workers.
cd /home/user/gp-elite
D=benchmarks/results_1.2/prototype
until grep -q "^all done" $D/run.log 2>/dev/null; do sleep 60; done
echo "start $(date -u '+%FT%H:%M:%SZ')" >> $D/run2.log
/venv11p/bin/python $D/units_rejected.py run --python /venv11p/bin/python --out $D --workers 4 >> $D/run2.log 2>&1
