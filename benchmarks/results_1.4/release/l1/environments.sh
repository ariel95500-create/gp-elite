#!/bin/bash
# The files and environments of the corrected release (correction L1), as
# environments.txt records those of the measured release: the SHA-256 of
# the wheel and source archive built from ec44e8e, twine check --strict, the
# gp_elite/ files of the wheel and of /venv14r2 and /venv14r2x against the
# commit, and their uv pip freeze against /venv14r and /venv14rx.
#   bash environments.sh > environments.txt
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad
D=$S/rel14b/dist
C=ec44e8e
G=/home/user/gp-elite
echo "# SHA-256 of the release files built from commit $C (pyproject-build from a clean export, git archive), 16 November 2026"
(cd $D && sha256sum gp_elite-1.4.0-py3-none-any.whl gp_elite-1.4.0.tar.gz)
echo
echo "# twine check --strict"
(cd $D && uvx twine check --strict gp_elite-1.4.0* 2>&1 | grep -v UV_NATIVE_TLS | sed 's/\x1b\[[0-9;]*m//g')
echo
T=$(mktemp -d)
(cd $T && python3 -m zipfile -e $D/gp_elite-1.4.0-py3-none-any.whl whl)
FILES=$(cd $G && git ls-tree --name-only $C gp_elite/ | grep -v "/__pycache__")
n=0; bad=""
for f in $FILES; do
  n=$((n+1))
  git -C $G show $C:$f > $T/ref
  cmp -s $T/ref $T/whl/$f || bad="$bad wheel:$f"
  for E in /venv14r2 /venv14r2x; do
    cmp -s $T/ref $E/lib/python3.11/site-packages/$f || bad="$bad $E:$f"
  done
done
echo "# the $n gp_elite/ files of commit $C, in the wheel and installed in /venv14r2 and /venv14r2x: ${bad:-all identical}"
echo "# against the measured release (f6a36cd), the files that differ:"
for f in $FILES; do
  git -C $G diff --quiet f6a36cd $C -- $f || echo "#   $f"
done
rm -rf $T
for P in "/venv14r2 /venv14r" "/venv14r2x /venv14rx"; do
  set -- $P
  if diff <(uv pip freeze --python $1/bin/python 2>/dev/null | grep -v "^gp-elite") \
          <(uv pip freeze --python $2/bin/python 2>/dev/null | grep -v "^gp-elite") > /dev/null; then
    echo "# $1 has the packages of $2 (uv pip freeze compared, gp-elite aside)"
  else
    echo "# $1 and $2 DIFFER in their packages (gp-elite aside)"
  fi
done
for E in /venv14r2 /venv14r2x; do
  echo
  echo "# $E ($($E/bin/python -c 'import platform; print(platform.python_version())')) — uv pip freeze"
  uv pip freeze --python $E/bin/python 2>/dev/null
done
