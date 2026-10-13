# Phase 6 (users) — plan

Written on 13 October 2026, after phases 4 and 5. The plan of 0.9 names four
deliverables, and its exit criterion: an independent review that finds no
discrepancy between the documents and the records.

1. **The French notebook at the level of the English one.** Done on 13
   October: `examples/quickstart.fr.ipynb` gains step 4, the real data of
   Nikuradse (five steps, as the English notebook); its two new code cells
   were run and return the front the text describes, identical with the
   0.9.0 wheel and with the engine of this branch.
2. **Three case studies on public data**, each a short notebook: the data
   and their source, what the engine returns, what it does not find, and a
   held-out check. The author chose the three on 13 October: Kepler with
   units, Nikuradse in full, Hubble in 1929. Their protocol, written before
   any of their figures is measured, follows.
3. **A page of the limits**: what the engine does not do, with the records
   behind each point. Written on 13 October, `LIMITATIONS.md` and
   `LIMITATIONS.fr.md` (nine points; figures from the campaigns of phases 4
   and 5, to be measured again on the wheel).
4. **The paper brought up to date**, after the release figures are measured.

The figures of the README, the notebooks, the case studies and the paper are
measured again on the wheel of the next version, as for 0.9.0; the
documents of phase 6 are written first, their figures filled from those
measurements.

## Protocol of the case studies

Written on 13 October, before any figure of the three studies is measured.

**Common to the three.** Each study is a notebook in `examples/case_studies/`;
its data are in `examples/case_studies/data/`, with their source in the file,
except Nikuradse's, loaded from PMLB as in the quickstart and checked by
SHA-256 (`benchmarks/pmlb_frozen.py`). Every figure the notebooks print or
state comes from `benchmarks/case_studies.py <study>`, one process per study,
`PYTHONHASHSEED=0`, `parallel=False`, a number of `generations` (no time
limit), seeds 0 to 4. A notebook shows seed 0; its text says how many of the
five seeds return the same thing, and the spread of the others. The frozen
test set is not used. The figures are measured again on the wheel of the
release, as every public figure.

**Kepler with units.**

- Data: the mean elements of Simon et al. (1994, Astron. Astrophys. 282,
  663), as tabulated in `plan94.c` of ERFA, in the source package
  pyerfa 2.0.1.5 on PyPI (SHA-256 17d6b24f…f6c0). For the eight planets
  (Earth–Moon barycentre for the Earth): the semi-major axis a in au, and
  the linear term of the mean longitude in arcseconds per Julian millennium,
  from which the period is P = 1 296 000 000 / term, in Julian years. The
  NASA pages proposed at first cannot be reached from the measuring machine,
  and the figures of the quickstart cannot be traced to one source: the
  study uses this one instead.
- SI conversion: au = 149 597 870 700 m (IAU 2012 B2), year = 365.25 × 86 400
  s. Reference: G·M☉ = 1.3271244e20 m³ s⁻², nominal value of IAU 2015 B3. Both
  constants checked in `astropy/constants/iau2015.py` (astropy 6.1.4 source
  package).
- What the data are: in these mean elements the semi-major axis is tied to
  the mean motion by Kepler's law with the mass of the planet (checked before
  any fit: within 6e-5 from Mercury to Jupiter, 2.5e-3 to 2.8e-3 from Saturn
  to Neptune, with the masses and Gauss's constant of the same file). The study
  tests what the engine recovers and deduces from such a table, not Kepler's
  law; the notebook says so.
- Fit A, the eight planets: `GPEliteRegressor(units=['m'], target_units='s',
  unknown_constant=True, generations=30, speed='fast', parallel=False)`.
  Reported: the formula, the constant and its units, G·M☉ = (2π/c)² against
  the reference.
- Fit B, held out: the same estimator fitted on Mercury to Mars, predicting
  Jupiter to Neptune. Reported: the largest relative error on the period.
- Fit C, without units: `GPEliteRegressor(generations=30, speed='fast',
  parallel=False)` on the same data in au and years, on the eight planets
  and on the split of B. Reported: the formulas and the error of B.

**Hubble in 1929.**

- Data: R package Sleuth2, dataset `case0701` (Ramsey and Schafer, The
  Statistical Sleuth, 2nd edition, case study 7.1; from Hubble 1929, Proc.
  Natl. Acad. Sci. 15, 168): 24 nebulae, distance in megaparsecs, recession
  velocity in km/s; distances rounded to the three decimals of the source
  (the file stores them in single precision). A second transcription, R
  package lmreg, dataset `stars1`, differs on one row: 0.63 Mpc, −200 km/s
  instead of +200.
- Fit A, the 24 nebulae: `GPEliteRegressor(units=['Mpc'],
  target_units='km/s', unknown_constant=True, generations=30, speed='fast',
  parallel=False)`. Reported: the formula, the constant and its units,
  against least squares through the origin and with an intercept.
- Fit B, without units: `GPEliteRegressor(generations=30, speed='fast',
  parallel=False)`, the same report.
- Fit C, held out: A and B fitted on the 18 nebulae up to 1.1 Mpc,
  predicting the 6 beyond. Reported: the root mean square error on the 6,
  against least squares through the origin on the same split.
- Fit D, the other transcription: A and B again on `stars1`.
- Whether the seeds of the power law, B1, E1 and N1 place anything on these
  data, read from the seed functions of the engine: the notebook says what
  the noise-tolerant seeds do here, whatever it is.

**Nikuradse in full.**

- Data: PMLB `nikuradse_1` (Nikuradse 1933; 362 rows, six roughness ratios),
  checked by SHA-256.
- Protocol: that of `benchmarks/real_nikuradse.py`, unchanged (random 70/30
  split with seed 0; `generations=30, restarts=4, validation_split=0.15`; the
  Prandtl–von Kármán relation with no fitted parameter as the reference; the
  roughness 126 removed from training, with the level bias in standard
  deviations of the removed curve), run for the seeds 0 to 4 of the engine
  (an option `--seed`, default 0, added to the script; nothing else
  changes). Reported: the front on the test rows, the shortest forms, the
  champion, and the level bias of each form on the removed roughness against
  the reference's.

**What the notebooks say they do not find** is written after the figures,
from them, and never by choosing among the seeds.
