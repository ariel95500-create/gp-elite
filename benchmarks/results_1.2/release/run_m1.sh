#!/bin/bash
# M1 of PLAN_RELEASE_1.2.md: the thirteen reference configurations, 1.1.0 from PyPI then the 1.2.0 wheel.
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/m1
cd $S/benchmarks
unset PYTHONPATH
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
echo "== M1 $(date -u +%FT%TZ) $(lscpu | grep 'Model name' | sed 's/  */ /g') $(nproc) cores"
for v in 11p 12b; do
  echo "== /venv$v $(/venv$v/bin/python -c 'import gp_elite;print(gp_elite.__version__, gp_elite.__file__)')"
  /venv$v/bin/python speed_equivalence.py run $S/M1_equiv_venv$v
done
/venv12b/bin/python speed_equivalence.py compare $S/M1_equiv_venv11p $S/M1_equiv_venv12b > $S/M1_compare_1.1.0_vs_1.2.0.txt; echo "compare exit $?"
echo "== M1 done $(date -u +%FT%TZ)"
