# Measurements of the release 1.4.0

What `../PLAN_RELEASE_1.4.md` asks before gate 12, as it was measured. The
machine has 4 cores (an Intel Xeon under KVM). Every fit runs in its own
process with `PYTHONHASHSEED=0`. The container does not always run on the same
host, so the versions are compared within one campaign or one day, never
across days.

## The release candidate

Commit f6a36cd carries the engine of 227d837, the candidate of the campaign
of N2b. It changes the version number, opens the CHANGELOG and rewrites one
comment of `gp_elite/core.py`. Its wheel and source archive were built from a
clean export. `environments.txt` gives their SHA-256 and the `uv pip freeze`
of the environments:
- `/venv14r`: the wheel alone, with the packages of `/venv13r` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv14rx`: the same, with the packages of `/venv13rx`, for M3;
- `/venv13p`: gp-elite 1.3.0 installed from PyPI. Its `gp_elite/` files are
  those of the published wheel, downloaded again and checked against its
  SHA-256.

`twine check --strict` passes for both files.

## M1, equivalence (13 November 2026)

`M1_equiv_1.3.0/`, `M1_equiv_n2b/` and `M1_equiv_1.4.0/` hold the thirteen
reference configurations of `benchmarks/speed_equivalence.py`. They were run
with `/venv13p`, `/venv14n2b` and `/venv14r` by `run_m1.sh`, from a copy of
`benchmarks/` of f6a36cd (`M1.log`). As the plan expected:
- **the thirteen of 1.4.0** are identical to those of the candidate of N2b
  (`M1_compare_n2b_vs_1.4.0.txt`);
- **against 1.3.0** (`M1_compare_1.3.0_vs_1.4.0.txt`), twelve are identical,
  and C_big differs in its Pareto front only: its model is the same. C_big is
  a noisy table, 5,000 rows of x0·x1/x2 with Gaussian noise. Run again with
  each version to read its trace, 1.4.0 places twelve noise-tolerant seeds
  there, the six of 1.3.0 among them, where 1.3.0 places six.

The thirteen took 21.8 s with 1.3.0, 21.5 s with the candidate of N2b and
26.2 s with 1.4.0, run in that order. The last two have the same engine, so
these times say nothing about it.

## M2, campaign R paired with 1.3.0

The comparison and the criteria of the plan are
`benchmarks/release_claims/compare_m2_1.4.py`, committed before any record of
M2 existed. To check that it runs, it was tried on records of earlier
campaigns: those of the M2 of 1.3 for the benches, those of campaign N2b for
TP, and the baseline of TPT10 against itself. That printed the counts of the
baseline of TPT10 by experiment, which its plan had left unread; no change
of the engine follows it, and TPT10 decides nothing.

`m2/slice.sh` runs TP and TPT10 in one go, then the benches in slices.
