#!/bin/bash
# Copy the records of campaign C1 into the repository, commit and push them.
cd /home/user/gp-elite
C=benchmarks/results_1.2/c1
for f in /home/user/c1_records/tp_C1.jsonl /home/user/c1_records/d_C1.jsonl /home/user/c1_records/run_c1.log; do
  [ -f "$f" ] && cp "$f" $C/
done
git add $C && git commit -q -m "Campaign C1: records at $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EWHDf9m7w3MoDeyD7ewSDZ" && timeout 90 git push -q -u origin claude/peaceful-knuth-4q7m4p
git log --oneline -1
wc -l $C/*_C1.jsonl 2>/dev/null
