#!/bin/sh
# The engine U1 of the campaign (benchmarks/results_1.1/PLAN.md): the Python
# and packages of the 1.0.0 environment (/venv10), the repository's gp_elite
# first on the path, and the flag _SEEDS_UNDER_UNITS set by
# benchmarks/phase2_flags/sitecustomize.py (GP_ELITE_ARM=U1). The records
# carry engine_file and seeds_under_units to show which engine ran.
R="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="$R/benchmarks/phase2_flags:$R"
export GP_ELITE_ARM=U1
exec /venv10/bin/python "$@"
