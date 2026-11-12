#!/bin/sh
# Item 1 of the mechanics of N2: the finders of 1.3.0 (PyPI, /venv13p) and of
# the candidate return the same values on the same tables. From the
# repository root.
set -e
D=benchmarks/results_1.4/n2/mechanics
S=${TMPDIR:-/tmp}
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    /venv13p/bin/python -I $D/finders_dump.py /nonexistent $S/finders_1.3.0.txt
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    /venv13p/bin/python -I $D/finders_dump.py "$PWD" $S/finders_candidate.txt
tail -n +2 $S/finders_1.3.0.txt > $S/a.txt
tail -n +2 $S/finders_candidate.txt > $S/b.txt
if cmp -s $S/a.txt $S/b.txt; then
    echo "the two dumps are identical: $(wc -l < $S/a.txt) lines"
    sha256sum $S/a.txt | cut -d' ' -f1
else
    echo "THE DUMPS DIFFER"; diff $S/a.txt $S/b.txt | head -20
fi
