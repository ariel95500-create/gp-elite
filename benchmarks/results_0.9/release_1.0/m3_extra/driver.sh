#!/bin/bash
# Measurements added after the first review of M5 (PLAN_RELEASE_1.0.md), one after the other,
# nothing else on the machine, gp-elite 1.0.0 wheel (/venv10x), PYTHONHASHSEED=0.
O=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/rel10/m3_extra
W=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/work10
export PYTHONHASHSEED=0
echo "start $(date '+%F %T')" > $O/driver.log
{ echo "# machine, $(date '+%F %T')"; nproc; lscpu | grep -E "Model name|^CPU\(s\)|Flags" | sed 's/Flags:.*avx512f.*/Flags: ... avx512f ... (AVX-512 present)/'; free -g | head -2; } > $O/machine.txt
# 1. the parallel islands, without the switch of release_claims/sitecustomize.py
cd $O/parallel_islands
/venv10x/bin/python usage_example.py > usage_example.txt 2>&1
/venv10x/bin/python kepler_guard.py > kepler_guard.txt 2>&1
/venv10x/bin/python $W/examples/kepler_demo.py > kepler_demo.txt 2>&1
/venv10x/bin/python $W/benchmarks/pools_check.py > pools_check.txt 2>&1
echo "parallel islands done $(date '+%F %T')" >> $O/driver.log
# 2. the time_limit check, alone
cd $O && /venv10x/bin/python $W/benchmarks/time_limit_check.py > time_limit_check_alone.txt 2>&1
echo "time_limit done $(date '+%F %T')" >> $O/driver.log
# 3. the code of the six case-study notebooks, run as scripts from the folder of the notebooks' data
for nb in kepler_units kepler_units.fr hubble_1929 hubble_1929.fr nikuradse_full nikuradse_full.fr; do
  (cd /home/user/gp-elite/examples/case_studies; /venv10x/bin/python $O/notebooks/$nb.py > $O/notebooks/$nb.out.txt 2>&1)
done
echo "notebooks done $(date '+%F %T')" >> $O/driver.log
