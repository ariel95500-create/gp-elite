#!/bin/bash
# M4 of PLAN_RELEASE_1.2.md: the test suite of 971bcec (tests/, copied alone into an
# empty folder; the same as a263177) against the wheel of c3ea7fc installed in a fresh
# environment for each Python, one Python after the other.
D=$(cd "$(dirname "$0")" && pwd)
T=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/m4tests/tests
cd $T
for v in 3.9.25 3.11.18 3.14.6; do
  PYTHONHASHSEED=0 /venvt12_$v/bin/python -I -m pytest -q -p no:cacheprovider . > $D/pytest_$v.txt 2>&1
  echo "[$v] $(tail -1 $D/pytest_$v.txt)" >> $D/summary.txt
done
echo "all done" >> $D/summary.txt
