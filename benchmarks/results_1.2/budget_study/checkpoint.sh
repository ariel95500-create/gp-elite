#!/bin/bash
# Copy the records of the budget study into the repository, commit and push them.
cd /home/user/gp-elite
D=benchmarks/results_1.2/budget_study
for f in /home/user/budget_records/campaign.jsonl /home/user/budget_records/driver.log /home/user/budget_records/machine_*.txt; do
  [ -f "$f" ] && cp "$f" $D/
done
git add $D && git commit -q -m "Budget study: records at $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EWHDf9m7w3MoDeyD7ewSDZ" && timeout 90 git push -q -u origin claude/peaceful-knuth-4q7m4p
git log --oneline -1
wc -l $D/campaign.jsonl 2>/dev/null
