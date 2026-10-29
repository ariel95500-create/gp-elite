#!/bin/sh
# M2 of PLAN_RELEASE_1.1.md: campaign R, 1.0.0 (its measured wheel, /venv10)
# against 1.1.0 (its wheel, /venv11), every job with both at the same time,
# two jobs at a time, in time slices of 6,300 s, until every job is done.
cd "$(dirname "$0")/../../../.."
K=feyn,real,realraw,tf,ts,tr,trraw,feyn_n1,feyn_n10,ufeyn,ufeyn_n1,ufeyn_n10,utf
O=benchmarks/results_1.1/release/m2
while :; do
  a=$(wc -l < $O/campaignR_1.0.0.jsonl 2>/dev/null || echo 0)
  b=$(wc -l < $O/campaignR_1.1.0.jsonl 2>/dev/null || echo 0)
  [ "$a" -ge 2780 ] && [ "$b" -ge 2780 ] && break
  echo "--- slice $(date -u +%Y-%m-%dT%H:%M) ($a and $b done)"
  /venv10/bin/python benchmarks/phase1_bench.py run-paired \
    --python /venv10/bin/python --out $O/campaignR_1.0.0.jsonl \
    --python /venv11/bin/python --out $O/campaignR_1.1.0.jsonl \
    --pairs 2 --kinds $K --max-seconds 6300
done
echo "--- all done $(date -u +%Y-%m-%dT%H:%M)"
