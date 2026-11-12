#!/bin/sh
# Confirmation of N2 (benchmarks/results_1.4/PLAN.md): new draws of the
# noise, 1 to 4, on feyn_n1 and feyn_n10 at seed 0 (328 jobs), 1.3.0 from
# PyPI (A) against the candidate with N2 (B), paired as in driver.sh, from
# the same copy of the benches.
RUN=/home/user/n2_run
O=/home/user/n2_records
cd $RUN
[ -e gp_elite ] && { echo "a package beside the bench: stop"; exit 1; }
lscpu > $O/machine_conf_$(date -u +%Y%m%dT%H%M).txt
echo "--- confirmation of N2, benches of $(cat $RUN/COMMIT), kernel $(uname -r)"
while :; do
  a=$(wc -l < $O/conf_1.3.0.jsonl 2>/dev/null || echo 0)
  b=$(wc -l < $O/conf_candidate.jsonl 2>/dev/null || echo 0)
  [ "$a" -ge 328 ] && [ "$b" -ge 328 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done)"
  /venv13p/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv13p/bin/python --out $O/conf_1.3.0.jsonl \
    --python /venv14n2/bin/python --out $O/conf_candidate.jsonl \
    --pairs 2 --kinds feyn_n1,feyn_n10 --seeds 0 --noise-draws 1,2,3,4 \
    --max-seconds 6300
done
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
