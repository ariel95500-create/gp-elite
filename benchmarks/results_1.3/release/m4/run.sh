#!/bin/bash
# M4 of PLAN_RELEASE_1.3.md: the test suite of 695d2ff (tests/, copied alone into an
# empty folder) against the wheel of 5492296 installed in a fresh environment
# for each Python (/venvt13_*, with the pins of the M4 of 1.2), one Python after
# the other.
D=$(cd "$(dirname "$0")" && pwd)
T=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/m4tests13/tests
cd $T
: > $D/summary.txt
for v in 3.9.25 3.11.18 3.14.6; do
  PYTHONHASHSEED=0 /venvt13_$v/bin/python -I -m pytest -q -p no:cacheprovider . > $D/pytest_$v.txt 2>&1
  echo "[$v] $(tail -1 $D/pytest_$v.txt)" >> $D/summary.txt
done
echo "all done" >> $D/summary.txt
