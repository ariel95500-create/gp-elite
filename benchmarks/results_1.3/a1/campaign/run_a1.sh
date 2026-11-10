#!/bin/sh
# Campaign A1 (benchmarks/results_1.3/PLAN.md): 1.2.0 from PyPI (/venv12p, A)
# and the candidate with the arcsine (/venv13a, B), paired, each job started
# with both at the same time, two jobs at a time on the four cores. Dtrig,
# then TPsnell. The bench runs from a copy of the repository at the commit
# given (benchmarks/ only, without the package). Both runs resume.
# With "conf" as second argument: the confirmation, seeds 5 to 9 and draws
# 5 to 9, Dtrig's kinds feyn, feyn_n1 and feyn_n10.
C=$1
RUN=/home/user/a1_run
O=/home/user/a1_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
P=II.15.4,I.18.12,III.15.12,I.26.2,I.30.5,I.37.4,I.50.26,II.6.15b,III.9.52,III.17.37
if [ "$2" = "conf" ]; then
  S="--seeds 5,6,7,8,9"; K=feyn,feyn_n1,feyn_n10; DR="--draws 5,6,7,8,9"; X=_conf
else
  S=""; K=feyn,ufeyn,feyn_n1,feyn_n10; DR=""; X=""
fi
lscpu > $O/machine${X}_$(date -u +%Y%m%dT%H%M).txt
echo "--- campaign A1$X, bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r), $(date -u +%Y-%m-%dT%H:%M)"
/venv12p/bin/python benchmarks/phase1_bench.py run-paired \
  --python /venv12p/bin/python --out $O/Dtrig_A$X.jsonl \
  --python /venv13a/bin/python --out $O/Dtrig_B$X.jsonl \
  --pairs 2 --kinds $K --problems $P $S
/venv12p/bin/python benchmarks/tp_diagnostic.py run-paired \
  --python /venv12p/bin/python --out $O/TPsnell_A$X.jsonl \
  --python /venv13a/bin/python --out $O/TPsnell_B$X.jsonl \
  --workers 2 --experiments snell $DR
echo "--- all done$X $(date -u +%Y-%m-%dT%H:%M)"
