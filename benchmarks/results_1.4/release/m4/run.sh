#!/bin/bash
# M4 of PLAN_RELEASE_1.4.md: the test suite of the commit given (tests/,
# copied alone into an empty folder) against the wheel of f6a36cd installed
# in a fresh environment for each Python (/venvt14_*, with the pins of the M4
# of 1.2 and 1.3), one Python after the other, after M3.
C=$1
D=$(cd "$(dirname "$0")" && pwd)
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad
W=$(ls $S/rel14/dist/gp_elite-1.4.0-py3-none-any.whl)
T=$S/m4tests14
declare -A PY=([3.9.25]=/root/.local/share/uv/python/cpython-3.9-linux-x86_64-gnu/bin/python3.9
               [3.11.18]=/usr/bin/python3.11
               [3.14.6]=/root/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14)
rm -rf $T && mkdir -p $T && (cd /home/user/gp-elite && git archive $C tests) | tar -x -C $T
: > $D/summary.txt
echo "tests of $C, wheel $(basename $W) $(sha256sum $W | cut -c1-16)" >> $D/summary.txt
for v in 3.9.25 3.11.18 3.14.6; do
  E=/venvt14_$v
  if [ ! -d $E ]; then
    uv venv -q --python ${PY[$v]} $E
    grep -v "^gp-elite" /home/user/gp-elite/benchmarks/results_1.3/release/m4/requirements_$v.txt > $S/m4req_$v.txt
    uv pip install -q --python $E/bin/python -r $S/m4req_$v.txt
    uv pip install -q --python $E/bin/python --no-deps $W
  fi
  uv pip freeze --python $E/bin/python > $D/requirements_$v.txt 2>/dev/null
  cd $T/tests && PYTHONHASHSEED=0 $E/bin/python -I -m pytest -q -p no:cacheprovider . > $D/pytest_$v.txt 2>&1
  echo "[$v] $($E/bin/python -c 'import platform; print(platform.python_version())') $(tail -1 $D/pytest_$v.txt)" >> $D/summary.txt
done
cd $S/rel14/dist && uvx twine check --strict gp_elite-1.4.0* > $D/twine_check.txt 2>&1
echo "all done" >> $D/summary.txt
