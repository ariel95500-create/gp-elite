#!/bin/bash
# The targeted verification of correction L1 (../../PLAN_RELEASE_1.4.md,
# "Correction L1 after M4"): the corrected wheel of ec44e8e, the same version
# 1.4.0, in /venv14r2 and /venv14r2x. One step at a time on the machine:
#   sh verify.sh COMMIT a   M1, TP and TPT10, the cases with a negative
#                           column, M4 (about an hour)
#   sh verify.sh COMMIT b   the count on the 3,892 fits (about 50 minutes)
#   sh verify.sh COMMIT c   M3 (about 40 minutes)
# The scripts run from a copy of benchmarks/, examples/ and the READMEs of the
# commit given, without the package beside them.
C=$1; PART=$2
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad
R=/home/user/gp-elite/benchmarks/results_1.4/release
L=$R/l1
W=$S/work14b
if [ ! -d $W ]; then
  mkdir -p $W && (cd /home/user/gp-elite && git archive $C benchmarks examples tests README.md README.fr.md) | tar -x -C $W
  cp -r /home/user/m2_13_run/benchmarks/_pmlb_cache $W/benchmarks/
  echo "$C" > $W/COMMIT
fi
[ "$(cat $W/COMMIT)" = "$C" ] || { echo "the copy is of $(cat $W/COMMIT): stop"; exit 1; }
[ -e $W/gp_elite ] && { echo "a package beside the scripts: stop"; exit 1; }
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
unset PYTHONPATH
lscpu > $L/machine_$PART.txt
echo "--- part $PART, copy of $C, $(date -u '+%F %T'), kernel $(uname -r)" >> $L/verify.log
cd $W
if [ "$PART" = a ]; then
  /venv14r2/bin/python benchmarks/speed_equivalence.py run $L/M1_equiv_1.4.0_l1
  /venv13p/bin/python benchmarks/speed_equivalence.py compare $R/M1_equiv_1.4.0 $L/M1_equiv_1.4.0_l1 > $L/M1_compare_release_vs_l1.txt 2>&1
  echo "M1 done $(date -u '+%F %T')" >> $L/verify.log
  /venv13p/bin/python benchmarks/tp_diagnostic.py run --python /venv14r2/bin/python \
    --out $L/tp_l1.jsonl --workers 2 --draws 0,1,2,3,4 >> $L/verify.log 2>&1
  /venv13p/bin/python benchmarks/tp_diagnostic.py run --python /venv14r2/bin/python \
    --out $L/tpt10_l1.jsonl --workers 2 --draws 0,1,2,3,4 --set tpt10 >> $L/verify.log 2>&1
  echo "TP and TPT10 done $(date -u '+%F %T')" >> $L/verify.log
  /venv14r2x/bin/python -I $R/m4/log_scan/negative.py > $L/negative_l1.txt 2>&1
  echo "negative done $(date -u '+%F %T')" >> $L/verify.log
  T=$S/m4tests14b
  rm -rf $T && mkdir -p $T && cp -r $W/tests $T/
  WHL=$(ls $S/rel14b/dist/gp_elite-1.4.0-py3-none-any.whl)
  declare -A PY=([3.9.25]=/root/.local/share/uv/python/cpython-3.9-linux-x86_64-gnu/bin/python3.9
                 [3.11.18]=/usr/bin/python3.11
                 [3.14.6]=/root/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14)
  : > $L/m4_summary.txt
  for v in 3.9.25 3.11.18 3.14.6; do
    E=/venvt14b_$v
    if [ ! -d $E ]; then
      uv venv -q --python ${PY[$v]} $E
      grep -v "^gp-elite" /home/user/gp-elite/benchmarks/results_1.3/release/m4/requirements_$v.txt > $S/m4req_$v.txt
      uv pip install -q --python $E/bin/python -r $S/m4req_$v.txt
      uv pip install -q --python $E/bin/python --no-deps $WHL
    fi
    uv pip freeze --python $E/bin/python > $L/m4_requirements_$v.txt 2>/dev/null
    (cd $T/tests && $E/bin/python -I -m pytest -q -p no:cacheprovider . > $L/m4_pytest_$v.txt 2>&1)
    echo "[$v] $(grep -E 'passed|failed' $L/m4_pytest_$v.txt | tail -1); LAPACK messages: $(grep -c DLASCL $L/m4_pytest_$v.txt)" >> $L/m4_summary.txt
  done
  echo "M4 done $(date -u '+%F %T')" >> $L/verify.log
elif [ "$PART" = b ]; then
  /venv14r2/bin/python -I $R/m4/log_scan/count.py run $L/count_l1.jsonl
  /venv14r2/bin/python -I $R/m4/log_scan/count.py report $L/count_l1.jsonl > $L/count_l1.txt
  echo "count done $(date -u '+%F %T')" >> $L/verify.log
elif [ "$PART" = c ]; then
  O=$S/rel14b/m3
  mkdir -p $O/tp
  cp /home/user/gp-elite/benchmarks/results_1.3/release/m3/tp_six_lois.py $O/tp_six_lois.py
  cd $O && /venv14r2x/bin/python $W/benchmarks/release_claims/run_claims.py /venv14r2x/bin/python $W $O
  cd $O && /venv14r2x/bin/python $W/benchmarks/case_studies.py kepler > $O/case_kepler.txt 2>&1
  cd $O && /venv14r2x/bin/python $W/benchmarks/case_studies.py hubble > $O/case_hubble.txt 2>&1
  cd $O && /venv14r2x/bin/python $W/benchmarks/case_studies.py nikuradse $O/case_nikuradse > $O/case_nikuradse_driver.txt 2>&1
  cd $O && /venv14r2x/bin/python $W/benchmarks/results_0.9/phase5/mechanics/kepler_minmax_check.py > $O/kepler_minmax_check.txt 2>&1
  cd $O && /venv14r2x/bin/python $W/benchmarks/release_claims/deduced_constant_check.py > $O/deduced_constant_venv14rx.txt 2>&1
  cd $O/tp && /venv14r2x/bin/python $O/tp_six_lois.py > $O/notebook_tp_six_lois_1.4.0.txt 2>&1
  /venv13p/bin/python -I $L/m3_compare_l1.py $R/m3 $O > $L/m3_compare_release_vs_l1.txt 2>&1
  echo "M3 done $(date -u '+%F %T')" >> $L/verify.log
fi
echo "--- part $PART ends $(date -u '+%F %T')" >> $L/verify.log
