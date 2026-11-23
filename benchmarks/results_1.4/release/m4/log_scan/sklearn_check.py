# -*- coding: utf-8 -*-
"""Beside M4 of the release of 1.4.0, deciding nothing: which test printed
the "On entry to DLASCL ..." messages of M4?

The release README attributes them to the check of scikit-learn
check_positive_only_tag_during_fit, which tests/test_gp_elite.py runs through
check_estimator: it fits the estimator on the iris data minus their overall
mean, whose fourth column is then negative throughout. This script runs that
one check on the estimator of the test (GPEliteRegressor(generations=5,
speed="ultrafast", random_state=0)), with the measured wheel and with the
corrected one, and the run counts the LAPACK messages it prints:

  /venvt14_3.11.18/bin/python -I sklearn_check.py > sklearn_check_measured.txt 2>&1
  /venvt14b_3.11.18/bin/python -I sklearn_check.py > sklearn_check_corrected.txt 2>&1
"""
import warnings

import gp_elite
from gp_elite import GPEliteRegressor
from sklearn.utils.estimator_checks import check_positive_only_tag_during_fit

if __name__ == "__main__":        # the islands' workers re-import this file
    warnings.filterwarnings("ignore")
    print("gp_elite", gp_elite.__version__, gp_elite.__file__, flush=True)
    est = GPEliteRegressor(generations=5, speed="ultrafast", random_state=0)
    check_positive_only_tag_during_fit("GPEliteRegressor", est)
    print("check_positive_only_tag_during_fit passed", flush=True)
