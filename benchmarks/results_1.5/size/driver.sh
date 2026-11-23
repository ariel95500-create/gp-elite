#!/bin/sh
# Part B of ../PLAN.md: 1.4.0 from PyPI (/venv14p), the 1,845 fits of
# size_bench.py, four at a time. A first slice of 2,400 s, then the guard of
# the plan (the median time of the first ten fits of each cell against twice
# its budget: past it, the run stops until the author is told), then slices
# of 6,300 s until every job is done. The bench runs from a copy of
# benchmarks/ at the commit given (without the package); the records are
# written outside the repository and copied in by checkpoint.sh.
C=$1                                  # the commit whose benchmarks/ run
RUN=/home/user/size_run
O=/home/user/size_records
B=benchmarks/results_1.5/size/size_bench.py
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- size study, bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), $(nproc --all) cores"
S=2400
while :; do
  n=$(wc -l < $O/campaign.jsonl 2>/dev/null || echo 0)
  [ "$n" -ge 1845 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($n done), $(lscpu | grep 'Model name' | sed 's/  */ /g')"
  /venv14p/bin/python $B run --python /venv14p/bin/python --out $O/campaign.jsonl \
    --workers 4 --max-seconds $S
  if [ $S = 2400 ]; then
    /venv14p/bin/python $B guard $O/campaign.jsonl || { echo "--- guard: stop $(date -u +%Y-%m-%dT%H:%M)"; exit 2; }
    S=6300
  fi
  lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
done
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
