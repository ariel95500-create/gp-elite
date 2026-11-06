#!/bin/bash
# Confirmation of H1 (plan 1.2), after the campaign adopted it: TP draws 5
# to 9 and the kinds feyn, feyn_n1 and feyn_n10 of bench D with seeds 5 to 9,
# under the API defaults, the candidate (/venv12c) against A (/venv11p, the
# 1.1.0 wheel from PyPI). Same machine and load as the campaign: 4 fits at a
# time, one arm after the other; every step resumes. Records are written
# outside the repository and copied in by checkpoint.sh.
cd /home/user/gp-elite
C=/home/user/h1_records
mkdir -p $C
KINDS=feyn,feyn_n1,feyn_n10
stamp() { echo "== $1 $(date -u +%FT%TZ) $(lscpu | grep 'Model name' | sed 's/  */ /g') $(nproc) cores"; }
stamp "TP H1 conf"; /venv11p/bin/python benchmarks/tp_diagnostic.py run --python /venv12c/bin/python --out $C/tp_H1_conf.jsonl --workers 4 --draws 5,6,7,8,9
stamp "TP A conf";  /venv11p/bin/python benchmarks/tp_diagnostic.py run --python /venv11p/bin/python --out $C/tp_A_conf.jsonl --workers 4 --draws 5,6,7,8,9
stamp "D H1 conf";  /venv11p/bin/python benchmarks/phase1_bench.py run --python /venv12c/bin/python --out $C/D_H1_conf.jsonl --workers 4 --kinds $KINDS --seeds 5,6,7,8,9 --defaults
stamp "D A conf";   /venv11p/bin/python benchmarks/phase1_bench.py run --python /venv11p/bin/python --out $C/D_A_conf.jsonl --workers 4 --kinds $KINDS --seeds 5,6,7,8,9 --defaults
stamp "all done"
