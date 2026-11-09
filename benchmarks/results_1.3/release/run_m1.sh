#!/bin/sh
# M1 of the release of 1.3.0 (PLAN_RELEASE_1.3.md): the thirteen reference
# configurations with 1.2.0 from PyPI (/venv12p) and the candidate (/venv13r).
R=/home/user/gp-elite/benchmarks/results_1.3/release
B=/home/user/gp-elite/benchmarks
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "--- M1, $(date -u +%Y-%m-%dT%H:%M), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r)"
/venv12p/bin/python $B/speed_equivalence.py run $R/M1_equiv_1.2.0
/venv13r/bin/python $B/speed_equivalence.py run $R/M1_equiv_1.3.0
