#!/bin/sh
# Baselines of the two frozen test sets of 1.4, with gp-elite 1.3.0 installed
# from PyPI (/venv13p), before any change of the engine (../PLAN.md).
# From the repository root; both runs resume.
set -e
PY=/venv13p/bin/python
D=benchmarks/results_1.4/bench
$PY benchmarks/tp_diagnostic.py run --python $PY --set tpt10 \
    --out $D/tpt10_1.3.0.jsonl --workers 4
$PY benchmarks/tp_diagnostic.py summary $D/tpt10_1.3.0.jsonl > $D/tpt10_1.3.0.txt
$PY benchmarks/phase1_bench.py run --python $PY \
    --kinds tf_n1,tf_n10,utf_n1,utf_n10 --out $D/tf78n_1.3.0.jsonl --workers 4
$PY benchmarks/phase1_bench.py summary $D/tf78n_1.3.0.jsonl > $D/tf78n_1.3.0.txt
