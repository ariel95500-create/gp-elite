#!/bin/bash
# Campaign H1 of plan 1.2: the candidate (/venv12c, H1 and the typed-start
# correction) and A (/venv11p, the 1.1.0 wheel from PyPI), on TP draws 0 to 4
# and bench D (the API defaults). Each arm with 4 fits at a time, one after
# the other, so that both run under the same load; every step resumes.
cd /home/user/gp-elite
C=benchmarks/results_1.2/h1/campaign
KINDS=feyn,feyn_n1,feyn_n10,real,realraw,ufeyn,ufeyn_n1,ufeyn_n10
stamp() { echo "== $1 $(date -u +%FT%TZ) $(lscpu | grep 'Model name' | sed 's/  */ /g') $(nproc) cores"; }
stamp "TP H1";  /venv11p/bin/python benchmarks/tp_diagnostic.py run --python /venv12c/bin/python --out $C/tp_H1.jsonl --workers 4
stamp "TP A";   /venv11p/bin/python benchmarks/tp_diagnostic.py run --python /venv11p/bin/python --out $C/tp_A.jsonl --workers 4
stamp "D H1";   /venv11p/bin/python benchmarks/phase1_bench.py run --python /venv12c/bin/python --out $C/D_H1.jsonl --workers 4 --kinds $KINDS --defaults
stamp "D A";    /venv11p/bin/python benchmarks/phase1_bench.py run --python /venv11p/bin/python --out $C/D_A.jsonl --workers 4 --kinds $KINDS --defaults
stamp "all done"
