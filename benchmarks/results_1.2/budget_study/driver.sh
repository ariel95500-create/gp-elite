#!/bin/sh
# The budget study (PLAN.md in this folder): 1.2.0 from PyPI (/venv12p), the
# arms T, 3T and 10T of every job one after the other, four fits at a time,
# in time slices of 6,300 s, until every job is done. The bench runs from a
# copy of the repository at the commit given (without the package), with the
# verified data cache of the M2 of 1.2.0 (124 files, each checked against its
# SHA-256 at every load); the records are written outside the repository and
# copied in by checkpoint.sh.
C=$1                                  # the commit whose benchmarks/ run
RUN=/home/user/budget_run
O=/home/user/budget_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/m2_run/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
[ "$(ls benchmarks/_pmlb_cache | wc -l)" -ge 124 ] || { echo "data cache incomplete: stop"; exit 1; }
K=feyn,feyn_n1,feyn_n10,real,realraw,tf,ufeyn
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- budget study, bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), $(nproc --all) cores"
while :; do
  n=$(wc -l < $O/campaign.jsonl 2>/dev/null || echo 0)
  [ "$n" -ge 4020 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($n done), $(lscpu | grep 'Model name' | sed 's/  */ /g')"
  /venv12p/bin/python benchmarks/phase1_bench.py run --python /venv12p/bin/python \
    --out $O/campaign.jsonl --workers 4 --kinds $K --budget-factors 1,3,10 \
    --max-seconds 6300
done
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
