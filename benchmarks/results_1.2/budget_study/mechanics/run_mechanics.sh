#!/bin/bash
# Checks of PLAN.md before the first fit, with 1.2.0 from PyPI (/venv12p).
# A: three jobs without --budget-factors against the records of the M2 of the release.
# B: three jobs with each factor 1, 3 and 10.
D=$(cd "$(dirname "$0")" && pwd)
B=/home/user/gp-elite/benchmarks/phase1_bench.py
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /home/user/gp-elite
for j in '{"kind": "feyn", "problem": "I.12.1", "index": 0, "split": "test", "seed": 0}' \
         '{"kind": "ufeyn", "problem": "I.12.1", "index": 0, "split": "test", "seed": 0}' \
         '{"kind": "feyn", "problem": "I.6.20a", "index": 5, "split": "test", "seed": 1}'; do
  /venv12p/bin/python $B one "$j" | tail -1 >> $D/A_without_option.jsonl
done
for f in 1 3 10; do
  for j in '{"kind": "feyn", "problem": "I.12.1", "index": 0, "split": "test", "seed": 0' \
           '{"kind": "feyn_n1", "problem": "I.12.1", "index": 0, "split": "test", "seed": 0' \
           '{"kind": "real", "problem": "210_cloud", "split": "fold0", "seed": 0'; do
    /venv12p/bin/python $B one "$j, \"budget_factor\": $f}" | tail -1 >> $D/B_factors.jsonl &
  done
  wait
done
echo "done $(date -u +%FT%T)" >> $D/run.log
