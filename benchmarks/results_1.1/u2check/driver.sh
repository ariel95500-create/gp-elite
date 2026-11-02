#!/bin/sh
# Targeted check of PLAN_U2.md: the units arm of the TP diagnostic (200 fits),
# 1.1.0 (/venv11, engine U1) and U2 (/venvU2, wheel of 26349ef), each job with
# both at the same time, two jobs at a time.
cd "$(dirname "$0")/../../.."
echo "--- start $(date -u +%Y-%m-%dT%H:%M)"
/venv11/bin/python benchmarks/tp_diagnostic.py run-paired \
  --python /venv11/bin/python --out benchmarks/results_1.1/u2check/tp_units_U1.jsonl \
  --python /venvU2/bin/python --out benchmarks/results_1.1/u2check/tp_units_U2.jsonl \
  --workers 2 --arm units
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
