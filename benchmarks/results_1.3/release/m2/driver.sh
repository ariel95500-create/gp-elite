#!/bin/sh
# M2 of PLAN_RELEASE_1.3.md: campaign R, 1.2.0 (from PyPI, /venv12p) against
# 1.3.0 (the wheel of 5492296, /venv13r), every job with both at the same
# time, two jobs at a time, in time slices of 6,300 s, until every job is
# done. The bench runs from a copy of the repository at the commit given
# (without the package), with the data cache of the M2 of 1.2 (124 files,
# each checked against its SHA-256 at every load), so that edits of the
# repository during M2 do not touch it; the records are written outside the
# repository and copied in by checkpoint.sh.
C=$1                                  # the commit whose benchmarks/ run
RUN=/home/user/m2_13_run
O=/home/user/m2_13_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  cp -r /home/user/m2_run/benchmarks/_pmlb_cache $RUN/benchmarks/
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
[ "$(ls benchmarks/_pmlb_cache | wc -l)" -ge 124 ] || { echo "data cache incomplete: stop"; exit 1; }
K=feyn,real,realraw,tf,ts,tr,trraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10,utf
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- M2 bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r), $(nproc --all) cores"
while :; do
  a=$(wc -l < $O/campaignR_1.2.0.jsonl 2>/dev/null || echo 0)
  b=$(wc -l < $O/campaignR_1.3.0.jsonl 2>/dev/null || echo 0)
  [ "$a" -ge 2780 ] && [ "$b" -ge 2780 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done)"
  /venv12p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv12p/bin/python --out $O/campaignR_1.2.0.jsonl \
    --python /venv13r/bin/python --out $O/campaignR_1.3.0.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
done
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
