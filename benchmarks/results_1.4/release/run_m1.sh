#!/bin/sh
# M1 of the release of 1.4.0 (../PLAN_RELEASE_1.4.md): the thirteen reference
# configurations of speed_equivalence.py with 1.3.0 from PyPI (/venv13p),
# the candidate of N2b (/venv14n2b) and the release (/venv14r), from a copy of
# benchmarks/ of the commit given, without the package beside it.
C=$1
RUN=/home/user/rel14_m1_run
R=/home/user/gp-elite/benchmarks/results_1.4/release
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/gp-elite/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
unset PYTHONPATH
echo "--- M1, benches of $(cat $RUN/COMMIT), $(date -u +%Y-%m-%dT%H:%M), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r)"
/venv13p/bin/python benchmarks/speed_equivalence.py run $R/M1_equiv_1.3.0
/venv14n2b/bin/python benchmarks/speed_equivalence.py run $R/M1_equiv_n2b
/venv14r/bin/python benchmarks/speed_equivalence.py run $R/M1_equiv_1.4.0
/venv13p/bin/python benchmarks/speed_equivalence.py compare $R/M1_equiv_n2b $R/M1_equiv_1.4.0 > $R/M1_compare_n2b_vs_1.4.0.txt 2>&1
/venv13p/bin/python benchmarks/speed_equivalence.py compare $R/M1_equiv_1.3.0 $R/M1_equiv_1.4.0 > $R/M1_compare_1.3.0_vs_1.4.0.txt 2>&1
echo "--- M1 ends $(date -u +%Y-%m-%dT%H:%M)"
