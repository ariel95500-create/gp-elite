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
   any of their figures is measured, follows. Done on 13 October:
   `examples/case_studies/`, six notebooks (English and French); results
   below.
3. **A page of the limits**: what the engine does not do, with the records
   behind each point. Written on 13 October, `LIMITATIONS.md` and
   `LIMITATIONS.fr.md` (nine points; figures from the campaigns of phases 4
   and 5, to be measured again on the wheel).
4. **The paper brought up to date**, after the release figures are measured.
5. **The launch of 1.0**, added on 13 October on the author's choice: no
   change of direction for the engine, a campaign the week of the release
   towards the people who can use it. Its plan follows.

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

## Results of the case studies

Measured on 13 October with the engine of this branch (it still reports
version 0.9.0: the number changes at the release), `PYTHONHASHSEED=0`, outputs
in `benchmarks/results_0.9/case_studies/`. The code of each notebook, run as a
script (seed 0, data from the files of the repository), prints the figures of
`case_studies.py` to the last digit, in English and in French.

**Kepler with units** (`kepler.txt`). On the table, a³/T² is 0.99994 to 0.99997
from Mercury to Mars, 1.00080 for Jupiter, 1.0053 to 1.0055 from Saturn to
Neptune. Fit A, five seeds of five: `5.43909e-10 * X0 * sqrt(X0)`, constant in
s/m^1.5, G·M☉ = 1.334467e20 (+0.55 % from the IAU value), pulled by the outer
planets. Fit B, five of five: c = 5.454157e-10 s/m^1.5, G·M☉ = 1.327103e20
(−1.6e-5); outer periods predicted +0.043 % (Jupiter) and +0.27 % to +0.28 %
(Saturn to Neptune), the gap of the table itself; the law is written in five
ways, seed 4 as a difference of two terms in a^1.5, and the deduced constant,
read on the predictions since commit a354dea, is the same for all. Fit C, five of five: `0.00684983 + 0.997207 * X0 *
sqrt(X0)` on the eight planets (2.6 % off on Mercury), `-7.16378e-06 +
1.00003 * X0 * sqrt(X0)` on the four inner ones. In fit C on the eight
planets, the power-law seed and the noise-tolerant seeds (five forms) are
placed; in fit A, under units, none. A diagnostic outside the protocol, fit C
on the eight planets with the noise-tolerant seeds off, returns the same
formula for the five seeds (`kepler_noN1_diagnostic.txt`): here they change
nothing.

**Hubble in 1929** (`hubble.txt`). Five seeds of five, every fit: with units
`423.937 * X0` (constant in km/(Mpc·s)), the line through the origin of least
squares; without units `-40.7836 + 454.158 * X0`, the line with an intercept.
Held out, 6 nebulae beyond 1.1 Mpc: with units `427.063 * X0`, root mean square
error 203.4 km/s, as least squares through the origin; without units
`-74.9921 + 520.269 * X0`, 230.6 km/s. Transcription `stars1`: `415.4 * X0`
and `-68.1539 + 465.903 * X0`. No seed of the power law, B1, E1 or N1 places
anything on these data: the best line leaves 38 % of the variance, far above
the 1.5 % of N1.

**Nikuradse in full** (`nikuradse_seed*.txt` and their telemetry). References
on the 109 test rows: straight line R² 0.6778, line in log10(r_k) 0.9346,
Prandtl–von Kármán 0.9456 (0.9434 on all rows). Five seeds of five open the
front with `1.10108 - 0.133625 * log(r_k)`, R² 0.9357. Seeds 0, 2 and 4 return a
power of r_k at 7 to 9 nodes, R² 0.9441 to 0.9447; seeds 1 and 3 forms in
log(tanh(...)) at 7 and 8 nodes, R² 0.9404 to 0.9426. Champion 48 to 70 nodes,
R² 0.980 to 0.995. Roughness 126 removed: reference level gap +0.042 standard
deviations; the six-node form +0.225 in every seed; 10 to 13 forms per seed,
from −1.20 to +0.88; best per seed 0.014 to 0.225; only two forms do better
than the reference, both of seed 0, at 52 and 59 nodes. A logarithm of a
logarithm of r_k appears in one front of five, in a form of 30 nodes.

**Deviations from the protocol, none in the figures.** The Kepler data are those
of Simon et al. (1994), not the NASA pages proposed to the author: those
cannot be reached from the measuring machine (written in the protocol before
any measurement). After the first Kepler run, `case_studies.py` was made to
print two more things the text needed (a³/T² per planet, and the error per
planet of fit C); the run was made again, and every figure printed before is
unchanged. The first launch of the Nikuradse driver would have moved telemetry
files the repository keeps; it was stopped during seed 0, before anything was
written, and the driver now leaves those files as they were.

## Launch of 1.0

Written on 13 October, before any launch text is drafted.

**Why.** Four months after the first release, the repository has 41 stars, 3
forks and no issue from anyone (13 October; the PyPI download counts cannot be
read from the measuring machine). The author asked whether to change
direction towards a more striking problem, or to campaign on X or Hacker
News. Recommendation, chosen by the author: keep the engine's place (plain
Python and NumPy, physical units, formulas checked against the model, French
documentation), and make it known when 1.0 is out, to targeted audiences.

**When.** The week 1.0 is on PyPI, once the Colab links of the notebooks and
case studies work from `main` and every figure has been measured on the
wheel. Nothing is posted before.

**Channels**, in this order: the SRBench announcement and the JOSS
submission already planned; a "Show HN" on a weekday when the author can
answer for several hours; the Python newsletters that take submitted links
(PyCoder's Weekly, Python Weekly); the "Showcase" posts of r/Python, in the
format its rules ask for on the day; the networks of French-speaking physics
teachers the author knows. X only to point at the demonstration.

**Who does what.** Claude drafts every text in English with a French
translation for the author, the demonstration (Kepler with units in Colab,
two minutes), and answers to the questions likely to come. The author
publishes and answers himself, in his own words; Claude posts nothing
anywhere. Every figure in a launch text is one measured on the wheel of 1.0;
no comparison with another engine that is not in the records.

**What is measured**, 7, 30 and 90 days after the launch: people other than
the author who open an issue or a discussion, or say they use the engine;
stars; PyPI downloads without mirrors (pypistats, read by the author).
Criterion: if fewer than 3 people from outside have written within 90 days,
the audience aimed at is reviewed with the author before any further
campaign.

