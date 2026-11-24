#!/bin/sh
# M1 of the second candidate of 1.5.0 (../../PLAN.md, "The release of
# 1.5.0"), as for the first (../run_m1.sh): A1 in full, A3 and A4 on the
# wheel of the second candidate, installed alone in /venv15r2 with the
# packages of /venv14p (build.sh), against 1.4.0 from PyPI (/venv14p). One
# after the other, A3 alone on the machine.
#   sh run_m1.sh <commit>
C=$1
R=/home/user/gp-elite/benchmarks/results_1.5/release/candidate2
SPLIT=/home/user/gp-elite/benchmarks/results_1.5/split
echo "--- M1 starts $(date -u +%Y-%m-%dT%H:%M), $(lscpu | grep 'Model name' | sed 's/  */ /g'), $(nproc) cores, kernel $(uname -r), up since $(uptime -s)"
/venv15r2/bin/python -I -c "import platform, gp_elite; print('engine', gp_elite.__version__, gp_elite.__file__, 'python', platform.python_version())"
# A1 in full, compared with the run of 1.4.0 of the split (a1_140)
rm -rf /home/user/a1_rel2
sh $SPLIT/run_a1.sh /venv15r2/bin/python /home/user/a1_rel2 full
cd $SPLIT && /venv15r2/bin/python compare_a1.py /home/user/a1_140 /home/user/a1_rel2 > $R/M1_A1.txt 2>&1
echo "--- A1: $(tail -1 $R/M1_A1.txt) $(date -u +%H:%M)"
# A3, alone
rm -f /home/user/a3_rel2.jsonl
cd $SPLIT && /venv14p/bin/python time_a3.py /venv14p/bin/python /venv15r2/bin/python /home/user/a3_rel2.jsonl > $R/M1_A3.txt 2>&1
cp /home/user/a3_rel2.jsonl $R/M1_A3_timing.jsonl
echo "--- A3: $(grep -E 'A3|ratio' $R/M1_A3.txt | tr '\n' ' ') $(date -u +%H:%M)"
# A4: the test of the door against the installed wheel, from a copy of the
# tests of the candidate
T=/tmp/m1_tests15c2; rm -rf $T && mkdir -p $T && (cd /home/user/gp-elite && git archive $C tests) | tar -x -C $T
cd $T/tests && PYTHONHASHSEED=0 /venv15r2/bin/python -I -m pytest -q -p no:cacheprovider test_door.py > $R/M1_A4.txt 2>&1
echo "--- A4: $(tail -1 $R/M1_A4.txt) $(date -u +%H:%M)"
echo "--- M1 ends $(date -u +%Y-%m-%dT%H:%M)"
