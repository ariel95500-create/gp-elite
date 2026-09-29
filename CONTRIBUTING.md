# Contributing to GP_ELITE

Thank you for considering a contribution. Bug reports are the most valuable
contribution of all — especially "it did not find a law on my data": see the
issue templates, they ask for exactly what is needed to reproduce.

## Development setup

```bash
git clone https://github.com/ariel95500-create/gp-elite.git
cd gp-elite
python -m pip install -e ".[test]"
```

## Running the tests

```bash
python -m pytest tests/ -q
```

Since 0.8 a fit with a given `seed` returns the same model from one launch of
Python to the next without `PYTHONHASHSEED` (a test checks it with several
values and unset). The benchmark scripts still set `PYTHONHASHSEED=0`, which
does no harm. The suite runs on every push (Linux, Python 3.9–3.14, and
Windows).

## Changing the search

A change that alters which model a fit returns (not only how fast) is judged
before it ships: write the hypothesis and the decision criteria in
`benchmarks/results_0.8/PLAN.md` first, then compare the engine with and
without the change with `benchmarks/decision_bench.py` (see its docstring),
and report the outcome in `RESULTS.md`, whether or not the change passes.

`tests/test_guarantees.py` pins down defects that once existed unnoticed
(wrong exported formula, dimensional gate disagreeing with the auditor,
`operators=` ignored, files written into the install directory...). Each of
those tests was checked to **fail on the code that had the defect**. A new
guarantee test is only useful if it fails without the fix — please check that
too.

## Scripts that use parallel islands

Parallel islands start worker processes with the `spawn` method, which re-runs
your script's top-level code in every worker. Protect it:

```python
if __name__ == "__main__":
    main()
```

Without the guard, GP_ELITE detects the situation, falls back to sequential
(same results, one core) and warns once.

## Claims and benchmarks

A number that appears in the README, the release notes or the paper must be
reproducible from a released version installed with `pip install gp-elite`,
with the exact command given next to it. In particular:

- judge every method on the model it **returns** — never on the best candidate
  selected by looking at the test set;
- report mean, median **and** worst case, and count failures (R² < 0);
- run one process per measurement: the engine keeps some module-level state,
  so fits chained in one process are not independent experiments;
- state the hypothesis and the success criterion **before** running.

## Pull requests

Keep them focused, add a test, and describe what you measured. For anything
that changes default behaviour, include a before/after comparison on
`benchmarks/feynman_bench.py`.

## Getting help

Questions about using GP_ELITE are welcome as
[issues](https://github.com/ariel95500-create/gp-elite/issues) — there is no
separate forum. Say what you ran, what you expected and what you got; the
shape of your data is enough, the data itself is not needed.

## Conduct and contact

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1). For a
security problem, do not open an issue: follow [SECURITY.md](SECURITY.md).
Anything you prefer not to post publicly: ariel95500@gmail.com.
