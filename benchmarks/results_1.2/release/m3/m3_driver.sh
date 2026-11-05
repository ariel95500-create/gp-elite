#!/bin/bash
# M3 of PLAN_RELEASE_1.2.md, one step after the other, nothing else on the
# machine (started after M2 ended). W is a copy of benchmarks/, examples/ and
# the READMEs of commit 784152d without the package beside them; O is where the
# records go. The steps of the M3 of 1.1 (../../results_1.1/release/m3/), then
# the TP notebook run four times, 1.1.0 and 1.2.0 in turn, to compare its times
# on one day.
W=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/work12
O=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/rel12/m3
echo "start $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O && /venv12bx/bin/python $W/benchmarks/release_claims/run_claims.py /venv12bx/bin/python $W $O
echo "run_claims done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv12bx/bin/python $W/benchmarks/case_studies.py kepler > $O/case_kepler.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv12bx/bin/python $W/benchmarks/case_studies.py hubble > $O/case_hubble.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv12bx/bin/python $W/benchmarks/case_studies.py nikuradse $O/case_nikuradse > $O/case_nikuradse_driver.txt 2>&1
echo "case studies done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv12bx/bin/python $W/benchmarks/results_0.9/phase5/mechanics/kepler_minmax_check.py > $O/kepler_minmax_check.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv11p/bin/python $W/benchmarks/release_claims/deduced_constant_check.py > $O/deduced_constant_venv11p.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv12bx/bin/python $W/benchmarks/release_claims/deduced_constant_check.py > $O/deduced_constant_venv12bx.txt 2>&1
echo "checks done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O/tp && PYTHONHASHSEED=0 /venv12bx/bin/python $O/tp_six_lois.py > $O/notebook_tp_six_lois_1.2.0.txt 2>&1
echo "notebook done $(date -u '+%F %T')" >> $O/m3_driver.log
P=$O/tp_timing/notebook_pair
for run in 1 2; do
  cd $P && PYTHONHASHSEED=0 /venv11p/bin/python -I $O/tp_six_lois.py > $P/run${run}_1.1.0.txt 2>&1
  cd $P && PYTHONHASHSEED=0 /venv12bx/bin/python -I $O/tp_six_lois.py > $P/run${run}_1.2.0.txt 2>&1
done
echo "notebook pair done $(date -u '+%F %T')" >> $O/m3_driver.log
echo "all done $(date -u '+%F %T')" >> $O/m3_driver.log
