#!/bin/sh
# The second candidate of 1.5.0, after the corrections of the code that M5
# asked for (../M5_review2.md): its wheel and source archive, built with
# uv build from a clean export (git archive) of the commit given; the
# environment /venv15r2, the wheel alone (--no-deps) with the packages of
# /venv14p; and environments.txt, as for the first candidate (../).
#   sh build.sh <commit>
C=$1
D=$(cd "$(dirname "$0")" && pwd)
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/rel15c2
rm -rf $S && mkdir -p $S/src && (cd /home/user/gp-elite && git archive $C) | tar -x -C $S/src
cd $S/src && uv build -q > $S/build.log 2>&1
W=$S/src/dist/gp_elite-1.5.0-py3-none-any.whl
/venv14p/bin/python -m pip freeze 2>/dev/null | grep -v "^gp-elite" > $S/req14p.txt
rm -rf /venv15r2
uv venv -q --python /usr/bin/python3.11 /venv15r2
uv pip install -q --python /venv15r2/bin/python -r $S/req14p.txt
uv pip install -q --python /venv15r2/bin/python --no-deps $W
E=$D/environments.txt
echo "The second release candidate of 1.5.0: commit $C, built with uv build from a clean export (git archive) on $(date -u +'%d %B %Y at %H:%M UTC')." > $E
echo >> $E
(cd $S/src/dist && sha256sum gp_elite-1.5.0-py3-none-any.whl gp_elite-1.5.0.tar.gz) >> $E
echo >> $E
echo "== /venv15r2: the wheel alone (--no-deps), with the packages of /venv14p ($(/venv15r2/bin/python -V))" >> $E
uv pip freeze --python /venv15r2/bin/python 2>/dev/null >> $E
echo >> $E
echo "== /venv14p: gp-elite 1.4.0 from PyPI ($(/venv14p/bin/python -V))" >> $E
/venv14p/bin/python -m pip freeze 2>/dev/null >> $E
echo >> $E
echo "== the files of gp_elite/ in the wheel (SHA-256), and whether each equals the file of $C" >> $E
/venv15r2/bin/python - "$W" "$C" >> $E <<'EOF'
import hashlib, subprocess, sys, zipfile
whl, commit = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(whl)
names = sorted(n for n in z.namelist() if n.startswith("gp_elite/"))
same = 0
for n in names:
    data = z.read(n)
    ref = subprocess.run(["git", "-C", "/home/user/gp-elite", "show", "%s:%s" % (commit, n)],
                         capture_output=True).stdout
    eq = data == ref
    same += eq
    print(hashlib.sha256(data).hexdigest(), n, "same" if eq else "DIFFERENT")
print("%d files, %d equal to the commit" % (len(names), same))
EOF
echo "built: $(tail -1 $E)"
