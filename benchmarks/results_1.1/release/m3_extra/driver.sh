#!/bin/bash
# Measurements added after the first review of M5 (PLAN_RELEASE_1.1.md), one after the other,
# nothing else on the machine, PYTHONHASHSEED=0.
O=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/rel11c2/m3_extra
W=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/work11c2
export PYTHONHASHSEED=0
echo "start $(date '+%F %T')" > $O/driver.log
{ echo "# machine, $(date '+%F %T')"; nproc; lscpu | grep -E "Model name|^CPU\(s\)|Flags" | sed 's/Flags:.*avx512f.*/Flags: ... avx512f ... (AVX-512 present)/'; free -g | head -2; } > $O/machine.txt
# 1. the time_limit check, alone, with the wheel of 1.1.0
cd $O && /venv11bx/bin/python $W/benchmarks/time_limit_check.py > $O/time_limit_check_alone.txt 2>&1
echo "time_limit done $(date '+%F %T')" >> $O/driver.log
# 2. the free fall of the TP notebook with its whole trace, 1.0.0 then 1.1.0
cd $O && /venv10x/bin/python -I fall.py > $O/fall_trace_1.0.0.txt 2>&1
cd $O && /venv11bx/bin/python -I fall.py > $O/fall_trace_1.1.0.txt 2>&1
echo "all done $(date '+%F %T')" >> $O/driver.log
