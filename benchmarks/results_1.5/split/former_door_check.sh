#!/bin/sh
# Made after M5, for the first review (finding 6): tests/test_door.py as
# committed with the door of data descriptors (eb2eac5), run against the
# package of the commit before it (6ba1356, the door of Split 1), and against
# the package of eb2eac5, under pytest 9.2.0 (Python 3.11) and pytest 8.4.2
# (Python 3.9). Run from the root of the repository.
#   sh benchmarks/results_1.5/split/former_door_check.sh
S=$(mktemp -d)
for c in 6ba1356 eb2eac5; do
  mkdir -p $S/pkg_$c && git archive $c gp_elite | tar -x -C $S/pkg_$c
done
mkdir -p $S/tests && git show eb2eac5:tests/test_door.py > $S/tests/test_door.py \
  && git show eb2eac5:tests/core_names_1.4.0.txt > $S/tests/core_names_1.4.0.txt
for py in /venv15s/bin/python /venvt15_3.9.25/bin/python; do
  for c in 6ba1356 eb2eac5; do
    v=$(cd $S/tests && PYTHONPATH=$S/pkg_$c $py -c "import sys, pytest, gp_elite; print('Python', sys.version.split()[0], 'pytest', pytest.__version__, 'package of', '$c' if gp_elite.__file__.startswith('$S/pkg_$c/') else 'ANOTHER PACKAGE')")
    r=$(cd $S/tests && PYTHONPATH=$S/pkg_$c PYTHONHASHSEED=0 $py -m pytest -q -p no:cacheprovider test_door.py 2>&1 | tail -1)
    echo "$v: $r"
  done
done
rm -rf $S
