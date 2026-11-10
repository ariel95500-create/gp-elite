#!/bin/sh
# Review 1: read-only git checks (commit times of the plans and records, what
# the candidate changes, the engine since 492863e).
cd /home/user/gp-elite
echo "== commits from the candidate to the reviewed HEAD"
git log --format="%h %ad %s" --date=iso 5492296^..e598e4d
echo "== files of the plan commits"
for c in b724372 fd3973c 7fe0665; do git show --stat --format="%h %ad %s" --date=iso $c | head -6; done
echo "== what 5492296 changes"
git show --stat --format="%h %s" 5492296 | tail -6
echo "== gp_elite/ from 492863e to 5492296, and from 5492296 to e598e4d"
git diff --stat 492863e 5492296 -- gp_elite/
git diff --stat 5492296 e598e4d -- gp_elite/ tests/ pyproject.toml
echo "== documents changed since 5492296"
git diff --stat 5492296 e598e4d -- README.md README.fr.md CHANGELOG.md LIMITATIONS.md LIMITATIONS.fr.md paper/paper.md examples/ benchmarks/results_1.1/DIAGNOSTIC_TP.md benchmarks/release_claims/
