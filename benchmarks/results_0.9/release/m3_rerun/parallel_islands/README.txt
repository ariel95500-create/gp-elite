Runs of 12 October 2026 with gp-elite 0.9.0 (/venv09x, the wheel), PYTHONHASHSEED=0, WITHOUT the switch
of benchmarks/release_claims/sitecustomize.py, on the 4-core machine: the default parallel=None runs the
islands in parallel worker processes there.

usage_example.py / .txt  the README example as it stood before 12 October (no parallel=), under the
                         `if __name__ == "__main__":` guard: another model than the README printed,
                         0.9999765 of validation R², 14 nodes. The README example now passes parallel=False.
kepler_guard.py / .txt   the README Kepler block under the guard, so that the islands do start in
                         parallel: the same law as printed (0.00279171 + 0.999396 * a * sqrt(a)).
kepler_demo.txt, kepler_plot.txt, pools_check.txt
                         examples/kepler_demo.py, examples/kepler_plot.py, benchmarks/pools_check.py as they
                         are: the same results as the records of ../../m3/ (times aside).
