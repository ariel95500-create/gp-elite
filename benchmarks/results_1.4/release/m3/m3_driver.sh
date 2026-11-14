#!/bin/bash
# M3 of PLAN_RELEASE_1.4.md, one step after the other, nothing else on the
# machine (started after M2 ended). W is a copy of benchmarks/, examples/ and
# the READMEs of the commit given, without the package beside them; O is
# where the records go. The steps of the M3 of 1.3
# (../../../results_1.3/release/m3/m3_driver.sh) with 1.4.0 (/venv14rx), the
# deduced constant with 1.3.0 (/venv13rx) beside it, and the TP notebook run
# four times, 1.3.0 and 1.4.0 in turn, to compare its times on one day. The
# notebook is run as the script of its code cells without the pip line, the
# script of the M3 of 1.2 and 1.3 to the byte (tp_six_lois.py).
C=$1
S=/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad
W=$S/work14
O=$S/rel14/m3
if [ ! -d $W ]; then
  mkdir -p $W && (cd /home/user/gp-elite && git archive $C benchmarks examples README.md README.fr.md) | tar -x -C $W
  echo "$C" > $W/COMMIT
fi
[ -e $W/gp_elite ] && { echo "a package beside the scripts: stop"; exit 1; }
mkdir -p $O/tp $O/tp_timing/notebook_pair
cp /home/user/gp-elite/benchmarks/results_1.3/release/m3/tp_six_lois.py $O/tp_six_lois.py
lscpu > $O/machine.txt
echo "start $(date -u '+%F %T'), copy of $(cat $W/COMMIT), kernel $(uname -r)" >> $O/m3_driver.log
cd $O && /venv14rx/bin/python $W/benchmarks/release_claims/run_claims.py /venv14rx/bin/python $W $O
echo "run_claims done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv14rx/bin/python $W/benchmarks/case_studies.py kepler > $O/case_kepler.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv14rx/bin/python $W/benchmarks/case_studies.py hubble > $O/case_hubble.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv14rx/bin/python $W/benchmarks/case_studies.py nikuradse $O/case_nikuradse > $O/case_nikuradse_driver.txt 2>&1
echo "case studies done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O && PYTHONHASHSEED=0 /venv14rx/bin/python $W/benchmarks/results_0.9/phase5/mechanics/kepler_minmax_check.py > $O/kepler_minmax_check.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv13rx/bin/python $W/benchmarks/release_claims/deduced_constant_check.py > $O/deduced_constant_venv13rx.txt 2>&1
cd $O && PYTHONHASHSEED=0 /venv14rx/bin/python $W/benchmarks/release_claims/deduced_constant_check.py > $O/deduced_constant_venv14rx.txt 2>&1
echo "checks done $(date -u '+%F %T')" >> $O/m3_driver.log
cd $O/tp && PYTHONHASHSEED=0 /venv14rx/bin/python $O/tp_six_lois.py > $O/notebook_tp_six_lois_1.4.0.txt 2>&1
echo "notebook done $(date -u '+%F %T')" >> $O/m3_driver.log
P=$O/tp_timing/notebook_pair
for run in 1 2; do
  cd $P && PYTHONHASHSEED=0 /venv13rx/bin/python -I $O/tp_six_lois.py > $P/run${run}_1.3.0.txt 2>&1
  cd $P && PYTHONHASHSEED=0 /venv14rx/bin/python -I $O/tp_six_lois.py > $P/run${run}_1.4.0.txt 2>&1
done
echo "notebook pair done $(date -u '+%F %T')" >> $O/m3_driver.log
echo "all done $(date -u '+%F %T')" >> $O/m3_driver.log
