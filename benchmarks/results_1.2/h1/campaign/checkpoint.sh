#!/bin/bash
# Copy the campaign's records into the repository, commit and push them.
cd /home/user/gp-elite
C=benchmarks/results_1.2/h1/campaign
for f in /home/user/h1_records/*.jsonl /home/user/h1_records/run_h1*.log; do
  [ -f "$f" ] && cp "$f" $C/
done
git add $C && git commit -q -m "Campaign H1: records at $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EWHDf9m7w3MoDeyD7ewSDZ" && timeout 90 git push -q -u origin claude/peaceful-knuth-4q7m4p
git log --oneline -1
wc -l $C/*.jsonl
