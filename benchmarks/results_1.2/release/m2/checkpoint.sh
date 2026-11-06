#!/bin/bash
# Copy the records of M2 into the repository, commit and push them.
cd /home/user/gp-elite
D=benchmarks/results_1.2/release/m2
for f in /home/user/m2_records/campaignR_1.1.0.jsonl /home/user/m2_records/campaignR_1.2.0.jsonl /home/user/m2_records/driver.log /home/user/m2_records/machine.txt /home/user/m2_records/removed_for_the_data_cache.jsonl; do
  [ -f "$f" ] && cp "$f" $D/
done
git add $D && git commit -q -m "M2 of 1.2.0: records at $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EWHDf9m7w3MoDeyD7ewSDZ" && timeout 90 git push -q -u origin claude/peaceful-knuth-4q7m4p
git log --oneline -1
wc -l $D/campaignR_*.jsonl 2>/dev/null
