#!/bin/sh
# M1 of the release of 1.5.0 (../PLAN.md, "The release of 1.5.0"): A1 in
# full, A3 and A4 on the wheel built for the release (from a clean export
# of the candidate), installed alone in /venv15r with the packages of
# /venv14p, against 1.4.0 from PyPI (/venv14p). One after the other, A3
# alone on the machine.
R=/home/user/gp-elite/benchmarks/results_1.5/release
SPLIT=/home/user/gp-elite/benchmarks/results_1.5/split
echo "--- M1 starts $(date -u +%Y-%m-%dT%H:%M), $(lscpu | grep 'Model name' | sed 's/  */ /g'), kernel $(uname -r)"
/venv15r/bin/python -I -c "import gp_elite; print('engine', gp_elite.__version__, gp_elite.__file__)"
# A1 in full, compared with the run of 1.4.0 of the split (a1_140)
rm -rf /home/user/a1_rel
sh $SPLIT/run_a1.sh /venv15r/bin/python /home/user/a1_rel full
cd $SPLIT && /venv15r/bin/python compare_a1.py /home/user/a1_140 /home/user/a1_rel > $R/M1_A1.txt 2>&1
echo "--- A1: $(tail -1 $R/M1_A1.txt) $(date -u +%H:%M)"
# A3, alone
rm -f /home/user/a3_rel.jsonl
cd $SPLIT && /venv14p/bin/python time_a3.py /venv14p/bin/python /venv15r/bin/python /home/user/a3_rel.jsonl > $R/M1_A3.txt 2>&1
cp /home/user/a3_rel.jsonl $R/M1_A3_timing.jsonl
echo "--- A3: $(grep -E 'A3|ratio' $R/M1_A3.txt | tr '\n' ' ') $(date -u +%H:%M)"
# A4: the test of the door against the installed wheel, from a copy of tests/
T=/tmp/m1_tests15; rm -rf $T && mkdir -p $T && (cd /home/user/gp-elite && git archive HEAD tests) | tar -x -C $T
cd $T/tests && PYTHONHASHSEED=0 /venv15r/bin/python -I -m pytest -q -p no:cacheprovider test_door.py > $R/M1_A4.txt 2>&1
echo "--- A4: $(tail -1 $R/M1_A4.txt) $(date -u +%H:%M)"
echo "--- M1 ends $(date -u +%Y-%m-%dT%H:%M)"
