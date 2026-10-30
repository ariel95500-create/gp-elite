#!/bin/bash
# M4 of PLAN_RELEASE_1.1.md: the test suite of 6e0e296 (tests/ alone in an empty folder)
# against the wheel of the second candidate, one Python after the other.
D=$(cd "$(dirname "$0")" && pwd)
cd $D/tests
for v in 3.9.23 3.11.15 3.14.0rc2; do
  PYTHONHASHSEED=0 /venvt11_$v/bin/python -I -m pytest -q -p no:cacheprovider . > $D/pytest_$v.txt 2>&1
  echo "[$v] $(tail -1 $D/pytest_$v.txt)" >> $D/summary.txt
done
echo "all done" >> $D/summary.txt
