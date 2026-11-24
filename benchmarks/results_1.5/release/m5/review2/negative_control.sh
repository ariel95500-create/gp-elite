#!/bin/bash
# Review 2 of M5: a negative control of compare_split.py and unbound_names.py.
# Copies the modules of 1.5 to WORK_DIR, plants four faults, and runs the two
# checks on the copy; each fault must be reported:
#   1. a bare read of a state name in search.py (state._VAL_CANDS -> _VAL_CANDS)
#   2. a changed constant in seeds.py (_SCAN_KEEP + 1)
#   3. a missing import in fitting.py (_pure_mse dropped from its imports)
#   4. a state value captured at import in islands.py (_ALIAS = state._VAL_CANDS)
# Usage: negative_control.sh WORK_DIR   (run from this folder)
WORK=$1
HERE=$(cd "$(dirname "$0")" && pwd)
rm -rf "$WORK/neg" && mkdir -p "$WORK/neg" && cp "$HERE"/../../../../../gp_elite/*.py "$WORK/neg/"
cd "$WORK/neg" && /venv15s/bin/python -I - <<'EOF'
import re
s = open("search.py").read(); s = s.replace("state._VAL_CANDS.clear()", "_VAL_CANDS.clear()", 1); open("search.py", "w").write(s)
s = open("seeds.py").read(); s2 = re.sub(r"^_SCAN_KEEP = (\S+)", lambda m: "_SCAN_KEEP = %s + 1" % m.group(1), s, count=1, flags=re.M); assert s2 != s; open("seeds.py", "w").write(s2)
s = open("fitting.py").read(); s2 = s.replace("from .scoring import (_linear_scale_params, _pure_mse)", "from .scoring import (_linear_scale_params)"); assert s2 != s; open("fitting.py", "w").write(s2)
s = open("islands.py").read(); s += "\n_ALIAS = state._VAL_CANDS\n"; open("islands.py", "w").write(s)
print("four faults planted")
EOF
cd "$HERE" || exit 1
export PYTHONDONTWRITEBYTECODE=1
/venv15s/bin/python -I compare_split.py core_1.4.0.py "$WORK/neg" ../../../split/map.txt \
  | grep -E "^DIFF|^      [-+]|identical [0-9]|bare globals|module or class scope|islands.py line"
/venv15s/bin/python -I unbound_names.py core_1.4.0.py "$WORK/neg" | grep -E "^(fitting|search)"
