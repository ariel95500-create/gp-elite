#!/bin/sh
# One slice of campaign N2 (see driver.sh), for a run under the session's own
# background tasks: the container of the session stops when the session is
# idle, and a detached process does not keep it running (the first run of
# driver.sh stopped at 00:06:58 UTC on 13 November, 619 jobs done of 1,360).
# Each call runs one slice of at most 6,300 s of Dnoise and Dguard, or, once
# they are done, the TP diagnostic; the benches resume where they stopped.
RUN=/home/user/n2_run
O=/home/user/n2_records
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
K=feyn,real,realraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10
lscpu > $O/machine_$(date -u +%Y%m%dT%H%M).txt
a=$(wc -l < $O/bench_1.3.0.jsonl 2>/dev/null || echo 0)
b=$(wc -l < $O/bench_candidate.jsonl 2>/dev/null || echo 0)
if [ "$a" -lt 1360 ] || [ "$b" -lt 1360 ]; then
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv13p/bin/python --out $O/bench_1.3.0.jsonl \
    --python /venv14n2/bin/python --out $O/bench_candidate.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
  echo "--- slice ends $(date -u +%Y-%m-%dT%H:%M)"
  exit 0
fi
t=$(wc -l < $O/tp_candidate.jsonl 2>/dev/null || echo 0)
if [ "$t" -lt 400 ]; then
  echo "--- TP $(date -u +%Y-%m-%dT%H:%M), kernel $(uname -r)"
  /venv13p/bin/python benchmarks/tp_diagnostic.py run-paired \
    --python /venv13p/bin/python --out $O/tp_1.3.0.jsonl \
    --python /venv14n2/bin/python --out $O/tp_candidate.jsonl --workers 2
fi
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
