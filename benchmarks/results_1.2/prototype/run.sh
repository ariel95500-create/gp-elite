#!/bin/bash
# The prototype of plan 1.2 (champion_trace.py), detached, four workers.
cd /home/user/gp-elite
D=benchmarks/results_1.2/prototype
/venv11p/bin/python $D/champion_trace.py run --python /venv11p/bin/python --out $D --workers 4 >> $D/run.log 2>&1
