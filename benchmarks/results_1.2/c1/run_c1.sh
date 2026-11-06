#!/bin/bash
# Campaign C1 of plan 1.2: the candidate (the repository, H1, X1 and C1) on
# the units arm of TP (draws 0 to 9) and the kinds ufeyn, ufeyn_n1 and
# ufeyn_n10 of bench D, under the API defaults; 4 fits at a time, as in
# campaign H1; every step resumes. Records are written outside the
# repository (/home/user/c1_records) and copied in by checkpoint_c1.sh.
cd /home/user/gp-elite
C=/home/user/c1_records
mkdir -p $C
stamp() { echo "== $1 $(date -u +%FT%TZ) $(lscpu | grep 'Model name' | sed 's/  */ /g') $(nproc) cores $(git rev-parse --short HEAD)"; }
stamp "TP C1"; /venv11p/bin/python benchmarks/results_1.2/c1/campaign_c1.py run --python /venv11p/bin/python --part tp --workers 4
stamp "D C1";  /venv11p/bin/python benchmarks/results_1.2/c1/campaign_c1.py run --python /venv11p/bin/python --part d --workers 4
stamp "all done"
