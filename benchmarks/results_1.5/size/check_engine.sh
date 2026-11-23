#!/bin/sh
# The engine of Part B (PLAN.md): the 11 files of gp_elite/ in /venv14p,
# against those of the merge of 1.4.0 on main (6dc1e35). Run before the first
# fit and after the last; prints one line per file and the verdict.
P=/venv14p/lib/python3.11/site-packages/gp_elite
cd /home/user/gp-elite || exit 1
bad=0
for f in __init__.py __main__.py api.py cli.py core.py dim_search.py dimensions.py formula.py py.typed sklearn_api.py stability.py; do
  a=$(sha256sum < "$P/$f" | cut -c1-64)
  b=$(git show 6dc1e35:gp_elite/$f | sha256sum | cut -c1-64)
  if [ "$a" = "$b" ]; then echo "same      $f $a"; else echo "DIFFERENT $f $a $b"; bad=1; fi
done
/venv14p/bin/python -I -c "import gp_elite; print('version', gp_elite.__version__, gp_elite.__file__)"
[ $bad = 0 ] && echo "the 11 files are those of 6dc1e35" || echo "A FILE DIFFERS: stop and tell the author"
date -u +%Y-%m-%dT%H:%M:%SZ
