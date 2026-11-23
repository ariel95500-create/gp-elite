# The checks of the plan before the first fit (23 November 2026)

- `data_check.txt`: the data of three equations (0 at the four numbers of
  rows; 17 with 5, 10 and 20 added variables; 35 at 100 rows and with 20
  added). Every value is finite; the added columns cover the ranges of the
  equation's variables and stand in a drawn order among them.
- `fits.jsonl`: three fits run with `size_bench.py one`, each in its own
  process (`PYTHONHASHSEED=0`, one BLAS thread), from a copy of
  `benchmarks/` without the package, with 1.4.0 from `/venv14p`. Each
  records a count of generations above zero and a time to the first
  generation, as the plan asks:
  - equation 0 (I.12.1) at 100 rows: exact in 1 generation, 0.6 s;
  - equation 0 at 100,000 rows: exact in 1 generation, 4.5 s;
  - equation 17 with 20 added variables: near, 102 generations, 30.6 s,
    first generation at 2.2 s; its formula uses no added variable.
