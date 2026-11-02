# The test of SRBench for the wrapper of GP_ELITE (2 November 2026)

The tests SRBench runs for a method (`experiment/test.sh`): `test_algorithm.py`
then `test_evaluate_model.py`, with `--ml gp-elite`, on a copy of
`experiment/` of cavalab/srbench at 2aabbb6 (`git archive`), once with gp-elite
1.0.0 and once with 1.1.0, both installed from PyPI in two environments that
differ in that package only (`freeze_venv10q.txt`, `freeze_venv11p.txt`;
`pyyaml`, which SRBench's base environment provides, added to both). The two
runs ran at the same time, `PYTHONHASHSEED=0`.

Both versions pass: 6 tests of `test_algorithm.py` and the test of
`test_evaluate_model.py` (`192_vineyard_small`, test mode, `max_time` 360 s),
which returns the same model with both, `(0.7695974498038386*lugs_1989)`, in
120 and 122 s. The wrapper runs as it is with both versions.
