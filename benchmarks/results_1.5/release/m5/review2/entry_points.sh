#!/bin/bash
# Review 2 of M5, question 5: the entry points with an empty stdin, on 1.4.0
# and 1.5 (Python 3.9.25, the wheels installed in /venvt14b_3.9.25 = 1.4.0
# from PyPI and /venvt15_3.9.25 = the tree reviewed), from an empty folder.
# Each output is saved with the install paths replaced by <PKG>, then the
# outputs of the two engines are compared.
#   1. gp-elite                      (the console script, gp_elite.cli:main)
#   2. python -m gp_elite
#   3. python -m gp_elite.core
#   4. python -m gp_elite.core 1x    (an unknown mode: the menu)
#   5. python <site-packages>/gp_elite/core.py   (core.py run as a script)
# Usage: entry_points.sh OUT_DIR WORK_DIR
OUT=$1; WORK=$2
mkdir -p "$OUT" "$WORK"
cd "$WORK" || exit 1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 OMP_NUM_THREADS=1
for tag in 14b 15t; do
  if [ $tag = 14b ]; then V=/venvt14b_3.9.25; else V=/venvt15_3.9.25; fi
  PKG=$V/lib/python3.9/site-packages/gp_elite
  run() {
    name=$1; shift
    timeout 120 "$@" < /dev/null > "$OUT/${tag}_$name.raw" 2>&1
    echo "exit=$?" >> "$OUT/${tag}_$name.raw"
    sed -e "s#$PKG#<PKG>#g" -e "s#$V#<VENV>#g" "$OUT/${tag}_$name.raw" > "$OUT/${tag}_$name.txt"
    rm -f "$OUT/${tag}_$name.raw"
  }
  run console_script $V/bin/gp-elite
  run m_gp_elite $V/bin/python -m gp_elite
  run m_core $V/bin/python -m gp_elite.core
  run m_core_unknown $V/bin/python -m gp_elite.core 1x
  run core_as_script $V/bin/python $PKG/core.py
done
for name in console_script m_gp_elite m_core m_core_unknown core_as_script; do
  if diff -q "$OUT/14b_$name.txt" "$OUT/15t_$name.txt" > /dev/null; then
    echo "$name: identical"
  else
    echo "$name: DIFFERENT"
    diff "$OUT/14b_$name.txt" "$OUT/15t_$name.txt" | head -40
  fi
done
