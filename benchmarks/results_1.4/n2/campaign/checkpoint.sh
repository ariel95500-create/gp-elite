#!/bin/sh
# Copies the records of campaign N2 into the repository (see driver.sh).
D=$(cd "$(dirname "$0")" && pwd)
cp /home/user/n2_records/*.jsonl /home/user/n2_records/machine_*.txt $D/ 2>/dev/null
cp /home/user/n2_driver_first.log $D/driver_first.log 2>/dev/null
cp /home/user/n2_driver.log $D/driver.log 2>/dev/null
wc -l $D/*.jsonl
