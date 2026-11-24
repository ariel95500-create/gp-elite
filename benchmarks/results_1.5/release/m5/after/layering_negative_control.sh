#!/bin/sh
# tests/test_layering.py on a copy of gp_elite/ with four planted faults that
# keep the package importable: a module below imported in a function
# (tree -> console), a module outside the engine imported at import time
# (fitting -> formula, under `if False:`), gp_elite.core imported in a
# function (data -> core), and a module the order does not list (extra.py).
# All four must be caught. Run from the root of the repository.
#   sh benchmarks/results_1.5/release/m5/after/layering_negative_control.sh PYTHON
PY=$1
S=$(mktemp -d)
cp -r gp_elite $S/ && cp tests/test_layering.py $S/
cd $S && python3 - <<'PYEOF'
p = 'gp_elite/tree.py'; s = open(p).read()
s = s.replace("from . import state\n", "from . import state\n\n\ndef _planted_below():\n    from .console import run   # planted\n    return run\n", 1); open(p, 'w').write(s)
p = 'gp_elite/fitting.py'; s = open(p).read()
s = s.replace("from . import state\n", "from . import state\nif False:\n    from .formula import tree_to_formula   # planted\n", 1); open(p, 'w').write(s)
p = 'gp_elite/data.py'; s = open(p).read()
s = s.replace("from . import state\n", "from . import state\n\n\ndef _planted_core():\n    from . import core   # planted\n    return core\n", 1); open(p, 'w').write(s)
open('gp_elite/extra.py', 'w').write('X = 1\n')
PYEOF
echo "package imported from: $(PYTHONPATH=$S $PY -c 'import gp_elite; print(gp_elite.__file__)')"
PYTHONPATH=$S PYTHONHASHSEED=0 $PY -m pytest test_layering.py -q -p no:cacheprovider 2>&1 | grep -E "^E  |passed|failed"
rm -rf $S
