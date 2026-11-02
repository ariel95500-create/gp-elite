#!/bin/bash
# The 745 jobs of PLAN.md (amended): W0 and W1 at B = 300 s, two jobs at a time,
# in time slices of 6,300 s so that the records can be committed between slices.
cd /home/user/gp-elite
D=benchmarks/results_1.1/srbench_settings/run
until grep -q "^all done" $D/driver.log 2>/dev/null; do
  echo "--- slice $(date '+%FT%H:%M')" >> $D/driver.log
  /venv11p/bin/python benchmarks/srbench_settings.py run --python /venv11p/bin/python \
      --srbench /home/user/cavalab/srbench --outdir $D --pairs 2 --max-seconds 6300 >> $D/driver.log 2>&1
done
