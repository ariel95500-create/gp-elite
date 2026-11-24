#!/bin/bash
# M4 of the release of 1.5.0 (../../PLAN.md): the test suite of the commit
# given (tests/, copied alone into an empty folder) against the wheel given,
# installed in a fresh environment for each Python (/venvt15_*, with the
# pins of the M4 of 1.4, the wheel of 1.4.0 left out), one Python after the
# other; then twine check --strict on the wheel and the source archive.
#   bash run.sh <commit> <dist folder>
C=$1
DIST=$2
D=$(cd "$(dirname "$0")" && pwd)
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad
W=$(ls $DIST/gp_elite-1.5.0-py3-none-any.whl)
T=$S/m4tests15
declare -A PY=([3.9.25]=/root/.local/share/uv/python/cpython-3.9.25-linux-x86_64-gnu/bin/python3.9
               [3.11.18]=/usr/bin/python3.11
               [3.14.6]=/root/.local/share/uv/python/cpython-3.14.6-linux-x86_64-gnu/bin/python3.14)
rm -rf $T && mkdir -p $T && (cd /home/user/gp-elite && git archive $C tests) | tar -x -C $T
: > $D/summary.txt
echo "tests of $C, wheel $(basename $W) $(sha256sum $W | cut -c1-16), $(date -u +%Y-%m-%dT%H:%M)" >> $D/summary.txt
for v in 3.9.25 3.11.18 3.14.6; do
  E=/venvt15_$v
  rm -rf $E
  uv venv -q --python ${PY[$v]} $E
  grep -v "^gp-elite" /home/user/gp-elite/benchmarks/results_1.4/release/m4/requirements_$v.txt > $S/m4req15_$v.txt
  uv pip install -q --python $E/bin/python -r $S/m4req15_$v.txt
  uv pip install -q --python $E/bin/python --no-deps $W
  uv pip freeze --python $E/bin/python > $D/requirements_$v.txt 2>/dev/null
  cd $T/tests && PYTHONHASHSEED=0 $E/bin/python -I -m pytest -q -p no:cacheprovider . > $D/pytest_$v.txt 2>&1
  echo "[$v] $($E/bin/python -c 'import platform, gp_elite; print(platform.python_version(), gp_elite.__version__, gp_elite.__file__)') $(grep -E 'passed|failed' $D/pytest_$v.txt | tail -1)" >> $D/summary.txt
done
cd $DIST && uvx twine check --strict gp_elite-1.5.0* > $D/twine_check.txt 2>&1
echo "twine: $(tr '\n' ' ' < $D/twine_check.txt)" >> $D/summary.txt
echo "all done" >> $D/summary.txt
