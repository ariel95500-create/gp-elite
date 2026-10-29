# Measurements of the release 1.1.0

What `../PLAN_RELEASE_1.1.md` asks before gate 6, as it was measured. The
machine is an Intel Xeon at 2.8 GHz, 4 cores, AVX-512; every fit runs in its own
process with `PYTHONHASHSEED=0`.

The first candidate (engine U1) was measured up to M3 (`candidate1/`). M3 found
the TP notebook slower than with 1.0.0. The author chose to correct before the
release, and change U2 was adopted (`../PLAN_U2.md`). Everything below is the
second candidate.

## The release candidate

Commit 6e0e296 carries the engine of 26349ef (U1 and U2); the commits after
26349ef change benchmarks and documents only. Its wheel and source archive,
built from a clean export, are in `environments.txt` with their SHA-256 and the
`uv pip freeze` of three environments:
- `/venv11b`: the wheel alone, with the packages of `/venv11` (Python 3.11.15,
  NumPy 2.4.6, scikit-learn 1.9.1);
- `/venv11bx`: the same, with the packages of `/venv11x`;
- `/venv10p`: gp-elite 1.0.0 installed from PyPI on 29 October 2026, the day it
  was published, with the packages of `/venv10`. Its `gp_elite/` files are
  identical to those of the measured wheel of 1.0.0.

## M1, equivalence (29 October 2026)

`M1_equiv_1.1.0/`: the thirteen reference configurations of
`benchmarks/speed_equivalence.py`, run with the wheel in `/venv11b`.

- `M1_compare_adopted_vs_wheel.txt`: identical to the adopted engine
  (`../mechanics/equiv_U2`).
- `M1_compare_candidate1_vs_candidate2.txt`: identical to the first candidate.
  None of the thirteen configurations reaches the case U2 changes.

## M2, campaign R paired with 1.0.0

Running since 20:14 on 29 October (`m2/driver.sh`): 1.0.0 from PyPI
(`/venv10p`) against the second candidate (`/venv11b`), 2,780 fits per version,
with the same suites and criteria as the first candidate.
