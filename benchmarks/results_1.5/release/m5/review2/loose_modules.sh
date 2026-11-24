#!/bin/bash
# Review 2 of M5, question 5: the "loose modules" use that api.py and formula.py
# still offer ("usage direct : api.py a cote de core.py"; "loose modules next
# to each other"): the .py files of the package copied into one plain folder,
# and `from api import symbolic_regression` run there. One tiny fit
# (generations=2, parallel=False).
# Usage: loose_modules.sh WORK_DIR
WORK=$1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 OMP_NUM_THREADS=1
for tag in 1.4.0 1.5; do
  if [ $tag = 1.4.0 ]; then PKG=/venv14p/lib/python3.11/site-packages/gp_elite; PY=/venv14p/bin/python;
  else PKG=/home/user/gp-elite/gp_elite; PY=/venv15s/bin/python; fi
  D=$WORK/loose_$tag
  rm -rf "$D"; mkdir -p "$D"
  cp $PKG/*.py "$D"/
  rm -f "$D/__init__.py" "$D/__main__.py"
  echo "== $tag: $(ls $D | wc -l) files copied from the package (without __init__ and __main__)"
  (cd "$D" && $PY -c "
import numpy as np, io, contextlib
from api import symbolic_regression
X = np.random.RandomState(0).uniform(1, 5, (60, 2))
with contextlib.redirect_stdout(io.StringIO()):
    r = symbolic_regression(X, X[:, 0] * X[:, 1], generations=2, seed=0, parallel=False, verbose=False)
print('fit runs:', r.expression)
" 2>&1 | tail -4)
done
