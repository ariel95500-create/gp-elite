#!/bin/sh
# A1 of ../PLAN.md for one engine: the gp_elite package that the given Python
# imports (1.4.0 from PyPI in /venv14p; the engine in modules in /venv15s).
#   full:  the 13 configurations of speed_equivalence.py; F41, U41 and F41N1
#          with the defaults of the API (phase1_bench.py --defaults, 615
#          fits); the TP diagnostic (400 fits, its defaults); the console
#          example of run_claims.py (mode 6 on the Hooke table of the M3 of
#          1.4.0, units m and N, the constant deduced)
#   short: the 13 configurations and F41 with the defaults
# Each fit in its own process, PYTHONHASHSEED=0, one BLAS thread, four fits
# at a time; the scripts of benchmarks/ of the working tree, run from /tmp so
# that nothing beside them can be imported as the engine.
#   sh run_a1.sh /venv14p/bin/python /home/user/a1_140 full
PY=$1
OUT=$2
MODE=${3:-full}
B=/home/user/gp-elite/benchmarks
mkdir -p "$OUT"
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
unset PYTHONPATH
cd /tmp || exit 1
$PY -I -c "import gp_elite, numpy, sys; print(gp_elite.__version__, gp_elite.__file__, numpy.__version__, sys.version.split()[0])" > "$OUT/engine.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started.txt"
$PY $B/speed_equivalence.py run "$OUT/equiv" > "$OUT/equiv.log" 2>&1
K=feyn
[ "$MODE" = full ] && K=feyn,ufeyn,feyn_n1
$PY $B/phase1_bench.py run --python $PY --out "$OUT/phase1_defaults.jsonl" \
  --workers 4 --kinds $K --defaults > "$OUT/phase1.log" 2>&1
if [ "$MODE" = full ]; then
  $PY $B/tp_diagnostic.py run --python $PY --out "$OUT/tp.jsonl" --workers 4 > "$OUT/tp.log" 2>&1
  mkdir -p "$OUT/console" && cd "$OUT/console" || exit 1
  printf '6\n%s\n\n\n\n\nm\nN\ny\n\n\n' $B/results_1.4/release/m3/hooke.csv | \
    $PY -c "from gp_elite.cli import main; main()" > console.txt 2>&1
  cd /tmp || exit 1
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/ended.txt"
