#!/bin/bash
# M3 of PLAN_RELEASE_1.0.md, one step after the other, nothing else on the machine.
W=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/work10
O=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/rel10/m3
mkdir -p $O
echo "start $(date '+%F %T')" >> $O/m3_driver.log
cd $O && /venv10x/bin/python $W/benchmarks/release_claims/run_claims.py /venv10x/bin/python $W $O
echo "run_claims done $(date '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv10x/bin/python $W/benchmarks/case_studies.py kepler > $O/case_kepler.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv10x/bin/python $W/benchmarks/case_studies.py hubble > $O/case_hubble.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv10x/bin/python $W/benchmarks/case_studies.py nikuradse $O/case_nikuradse > $O/case_nikuradse_driver.txt 2>&1
echo "case studies done $(date '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv10x/bin/python $W/../work10/benchmarks/results_0.9/phase5/mechanics/kepler_minmax_check.py > $O/kepler_minmax_check.txt 2>&1
echo "all done $(date '+%F %T')" >> $O/m3_driver.log
