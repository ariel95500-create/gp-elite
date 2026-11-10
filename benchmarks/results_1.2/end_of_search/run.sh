#!/bin/sh
# The fits of the diagnostic (PLAN.md): 1.2.0 from PyPI (/venv12p), four at a
# time, from a copy of the repository at the commit given (benchmarks/ only,
# without the package). The run resumes: fits already recorded are skipped.
C=$1
RUN=/home/user/eos_run
O=/home/user/eos_records
if [ ! -d $RUN ]; then
  mkdir -p $RUN && (cd /home/user/gp-elite && git archive $C benchmarks) | tar -x -C $RUN
  echo "$C" > $RUN/COMMIT
fi
mkdir -p $O
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
echo "--- diagnostic, bench of $(cat $RUN/COMMIT), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r), $(date -u +%Y-%m-%dT%H:%M)"
/venv12p/bin/python benchmarks/results_1.2/end_of_search/diag.py run \
  --python /venv12p/bin/python --jobs benchmarks/results_1.2/end_of_search/jobs.jsonl \
  --out $O/records.jsonl --workers 4
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
