---
title: 'gp-elite: pure-Python symbolic regression with gradient-refined constants and dimensionally-constrained search'
tags:
  - Python
  - symbolic regression
  - genetic programming
  - interpretable machine learning
  - dimensional analysis
  - equation discovery
authors:
  - name: Sabri Hakou
    orcid: 0009-0007-6229-5157
    affiliation: 1
affiliations:
  - index: 1
    name: Independent Researcher, France
date: 14 October 2026
bibliography: paper.bib
---

# Summary

Symbolic regression searches the space of mathematical expressions for a formula
fitting a dataset, returning a closed-form equation instead of a black box. It is
attractive wherever the relationship itself is the object of interest rather than
the prediction: a degradation law, a sensor calibration curve, an engineering
correlation, a candidate physical law.

`gp-elite` is a symbolic-regression library written entirely in Python and NumPy
[@harris2020numpy]. It evolves expressions by genetic programming [@koza1992gp]
and refines each candidate's numerical constants with a Levenberg–Marquardt
least-squares optimizer [@levenberg1944; @marquardt1963], so that evolution
concentrates on the right *structure* while a dedicated numerical routine finds
the right *coefficients*. It exposes a scikit-learn-compatible estimator
[@pedregosa2011sklearn], installs with `pip install gp-elite` with no compiler
and no second language runtime, and holds out a validation split by default to
choose the returned model.

Since version 0.4, users may declare the physical units of their input columns
and of the target. The search is then restricted to dimensionally consistent
expressions: generation, mutation and crossover all preserve dimensions, and a
validity gate rejects unsound candidates on every code path. The engine can no
longer return a formula that fits the numbers while adding hertz to a
dimensionless quantity.

Version 0.5 extends this to laws whose constant is itself dimensioned. The
leading constant may carry a dimension, *deduced* by homogeneity rather than
declared, so the engine reports not only the shape of a law but the **units and
value of its missing physical constant** — recovering the gravitational constant,
and its units, from masses and distances alone.

Version 1.0 fits whole families of laws directly — a monomial times a power of a
binomial (rational forms, roots), or times an exponential, logarithm, hyperbolic
or trigonometric function of a monomial — and seeds the evolutionary search with
them, on noisy data too. On a test set of 78 Feynman equations frozen before this
work and measured once, it recovers the exact law in 213 of 390 fits, against 145
for version 0.9 measured side by side.

# Statement of need

Users who want an interpretable model — laboratory scientists, engineers,
students of evolutionary computation — share a practical need: a
symbolic-regression tool that installs in one command, can be read and modified
in the language they already use, and still recovers precise numerical
constants. These requirements are usually in tension. Engines that fit constants
well tend to rely on compiled or non-Python backends; pure-Python engines that
install easily tend not to fit constants at all, leaving evolution to assemble
numerical values out of random terminals.

`gp-elite` targets that gap, for small-to-medium experimental datasets — roughly
up to ten variables and a few thousand rows — where interpretability matters more
than raw accuracy, and where the analyst knows what their columns mean
physically.

The dimensional mode addresses a second, more specific problem. In scientific
applications, an expression that is numerically excellent but dimensionally
incoherent is not a partial success: it is not a candidate law at all. Making
dimensional consistency a hard constraint of the search, rather than a
post-hoc filter, follows a line of work opened by dimensionally aware genetic
programming [@keijzer1999dimensional], continued by the unit-based decomposition
of AI Feynman [@udrescu2020feynman] and by the units-constrained generation of
`PhySO` [@tenachi2023physo]. What `gp-elite` adds is not the idea but its
availability without a deep-learning stack, from a scikit-learn estimator with a
single `units=` argument.

That line of work carries a restriction this implementation initially inherited:
fitted constants are dimensionless. Under it, a law as elementary as Hooke's
`F = k·x` is unreachable, since no dimensionless constant relates metres to
newtons — yet much of physics is written with dimensioned constants. Lifting it
turns the constraint into an instrument: the analyst supplies what they know,
the units of their columns, and the engine returns what they do not.

# State of the field

The strongest contemporary engines are backed by compiled code: `Operon` is
implemented in C++ [@burlacu2020operon] and `PySR` drives a Julia backend
[@cranmer2023pysr]. Both are faster and, on large benchmarks, more accurate than
a pure-Python implementation can be. They also require a toolchain beyond
`pip`, which raises the barrier for a user who wants to inspect, teach from, or
modify the search itself. At the other end, `gplearn` [@gplearn] is pure Python
and widely used for teaching, but does not perform gradient-based constant
optimization, which limits it on problems whose constants are not small
integers.

`gp-elite` is positioned deliberately between the two: pure Python and
`pip`-installable like `gplearn`, but with Levenberg–Marquardt constant
refinement, linear scaling [@keijzer2003scaling], and $\epsilon$-lexicase
selection [@lacava2016lexicase] as in the compiled engines. Against `gplearn`
under identical data and splits, with a larger population budget for the
baseline (2000 programs over 30 generations, against 400 over 30 generations
and 4 restarts), on a fixed 15-equation subset of the Feynman problems chosen
before any measurement,
and each method judged on the model it returns, it recovers 15/15 exactly
($1 - R^2 < 10^{-9}$ on held-out data) against 6/15 (version 1.0.0,
`benchmarks/duel.py`; 12/15 for version 0.9.0). That
figure is a single-seed head-to-head with one baseline on a subset, not a
benchmark-wide result, and is not comparable to rates published on the full
120-equation Feynman set. The
claim made here is not that `gp-elite` competes with `Operon` or `PySR` on speed
or on large-scale accuracy — it does not.

**Dimensionally-constrained search is not new.** `PhySO` [@tenachi2023physo]
constrains equation generation to obey dimensional analysis by construction,
using deep reinforcement learning with an in-situ units-consistency mechanism,
and reports a substantial gain from doing so on the Feynman benchmark. It is the
closest relative of the mode described here, and the approach it took —
constraining generation rather than filtering results — is the same one.

`gp-elite` differs in three respects rather than in kind. It reaches the
constraint through genetic programming and a typed grammar rather than a learned
policy, so it carries no deep-learning dependency: `numpy`, `pandas` and
`scikit-learn`, no `torch`, no GPU. It runs the same algebra for the constrained
search and for its post-hoc audit, so the two cannot disagree. And it treats the
units of a law's constant as an *unknown to be deduced* rather than an input to
be declared, which — to the authors' knowledge — has no counterpart in the
packages cited above.

# Software design

Five design decisions shaped the library.

*Separating structure from coefficients.* Every candidate is treated as a
parametric template whose constants are fitted by Levenberg–Marquardt, with
scale and offset solved in closed form via linear scaling. Search pressure is
thereby spent on shape, which genetic programming is good at, rather than on
arithmetic, which it is not.

*Constraining rather than filtering.* v0.3 audited dimensions post hoc, which
proved unsatisfying: on the tested problem it reported that none of the returned
models were physically meaningful, without offering a remedy. v0.4 moves the
check inside the search, reusing the same algebra so that auditor and engine
cannot diverge. The cost, on the problem measured below, is a typed generation
1.4 times as long as an untyped one since version 0.9 (median of ten seeds, run
side by side), against 8.5 times in version 0.8, whose typed operators computed
the same dimension keys and reachability tests again millions of times per fit;
the returned models are the same. The benefit is that every returned model is valid by
construction.

*Deducing rather than requiring.* Under `unknown_constant=True` the validity
gate no longer requires an expression to *reach* the target dimension, only to
*have* a well-defined one; the leading constant absorbs the difference, and its
dimension follows as `target / dim(f)`. Typed generation draws random reachable
surrogate targets, so the population spans several dimension classes and
selection retains the one that fits.

*Fitting known families before evolving.* Many laws are a monomial times a
simple function of another monomial. Since version 1.0 such families are fitted
directly. For a power of a binomial and for the exponential, logarithm,
hyperbolic tangent and secant, once a single inner constant is searched in one
dimension, the law becomes a straight line in logarithmic scale, solved by least
squares; for sines and cosines, the frequency is searched on a grid and the rest
is linear. A fitted form that
holds to numerical precision joins the starting population; when none does, one
that leaves at most 1.5 % of the variance unexplained does. The search keeps its
generality and gains starting points. The typed population of the dimensional mode
does not use them yet.

*Reporting honestly by default.* The estimator holds out a validation split,
selects a parsimonious champion within an $R^2$ tolerance, and exposes a
complexity/accuracy Pareto front. The returned formula is written in the user's
own variables, with the internal rescaling folded back into its constants, and
the fit checks that it reproduces the model's predictions. The reported score
comes from held-out rows; since those rows also choose among candidates, it is
documented as an optimistic selection score, not a generalisation estimate.

# Research impact statement

The software is released on PyPI under the MIT licence, with a test suite and
benchmark scripts that regenerate the measured figures quoted in its
documentation.

The dimensional mode has been evaluated in a controlled A/B experiment on
Feynman equation II.11.3, five seeds, identical budget for the unconstrained
and constrained arms (`benchmarks/ab_ood.py`). With version 0.9.0, 0/5
unconstrained models were dimensionally valid, even with four times the
generations; with `units=`, 5/5 were valid and more than twice as small (median
27 versus 59 nodes) at a better test $R^2$ (0.99957 versus 0.99157), and two of
five recovered the exact law, which holds outside the training domain. With
version 1.0.0 this law belongs to a family fitted directly: the unconstrained
search returns it in 5/5 runs, in about a second each, while the constrained
search, unchanged, finds it in 2/5. The constraint guarantees that whatever is
returned is physically coherent; on the laws the engine fits directly, it is no
longer the shortest route to the law.

Each release is also measured once on a test set frozen before any decision of
its development: 78 Feynman equations absent from the decision bench, 14
Strogatz systems and 25 real datasets from PMLB [@olson2017pmlb]. Version 1.0.0
recovers 213 exact laws in 390 fits on its Feynman equations against 145 for
0.9.0, measured side by side at 30 s per fit, and 7 against 8 in 70 on its
Strogatz systems; on its real datasets, the median
$R^2$ moves by less than 0.004 and the number of collapses out of the training
range does not change (`benchmarks/results_0.9/release_1.0/`). Three case studies
on public data accompany it: Kepler's third law with units, where the four
inner planets give the product of the gravitational constant and the mass of
the Sun within 0.002 % of its nominal value; Hubble's measurements of 1929; and
Nikuradse's pipe-friction data, where a whole roughness ratio is held out.

The mystery-constant mode is validated on three reference laws whose answer is
known in advance (`benchmarks/test_constante_mystere.py`, 25 generations, two
restarts). Hooke's law returns `kg·s⁻²` and 250.0 for a true 250; gravitation
returns `m³·kg⁻¹·s⁻²` and 6.674e-11, exact; the ideal gas law returns
`kg·m²·s⁻²·mol⁻¹·K⁻¹` and 8.314462618, the value used to generate the data.
Structure is exact and $R^2 = 1.000000$ in all three.

GP_ELITE is part of the SRBench living benchmark [@lacava2021srbench]: its
maintainers merged the integration in September 2026
(<https://github.com/cavalab/srbench/pull/212>) and its update for version
0.8.0 into the development branch in October 2026
(<https://github.com/cavalab/srbench/pull/227>).

# AI usage disclosure

Generative AI was used extensively in the development of this software, and in
the writing of its documentation and of this paper. The assistant was Claude
(Anthropic), used across several model versions between May and October
2026.

The project began as the author's own work, before any AI involvement: the
expression representation and tree-generation strategies, the protected
operator set, the asymmetric island model, gradient-based constant optimization
using Adam, the seeding mechanism, the interactive console interface and the
benchmark problem suite all predate that phase and, in modified form, remain in
the released version.

From that point onward the assistant acted as a development collaborator. Its
contributions were: co-design and implementation of the stigmergic layer — the
pheromone-weighted fragment library, its evaporation and pruning dynamics, the
fragment co-occurrence graph, the sequence memory, and the stigmergic island;
the refactor from single-variable to multi-variable regression; the subsequent
numerical and statistical layers, namely Levenberg–Marquardt constant
refinement replacing Adam, linear scaling, the Pareto front, $\epsilon$-lexicase
selection, the robust loss, the dimensionally-constrained search and the
deduction of dimensioned constants; diagnosis and correction of specific
defects, including a float64 overflow in the Levenberg–Marquardt optimizer,
two defects in the dimensional mode, an exported formula left in the internal
scaled space, and a cache that could evaluate a model with the constants of
another;
packaging and release engineering; for version 0.8, the speed-ups of the
engine, the fit of constants by variable projection, the final polish of the
finalists, the power-law seeds, the handling of data far from unit scale, and
the protocol of comparisons with criteria written before each measurement,
under which the changes to the search and the final selection were accepted
or rejected; for version 1.0, the families of forms fitted directly, the
noise-tolerant seeds, the correction of the deduced constant and the case
studies; the benchmark and
non-regression scripts distributed in the repository; and the drafting of the
documentation and of this paper.

All AI-assisted output was reviewed and validated by the author before
inclusion, and the direction of the work — which mechanisms to pursue, which
results to trust, which claims to make — remained the author's throughout.
Every correction was accompanied by an executable check: the overflow was
reproduced before being fixed and re-tested afterwards, and the absence of
regression was verified by comparing fits before and after each change on a
fixed set of seeds. The benchmark figures quoted in this paper were produced
with the scripts in the repository, whose raw results, machine and dates are
recorded in `benchmarks/results_0.8/` and, for the figures of versions 0.9.0
and 1.0.0, in `benchmarks/results_0.9/` (`phase3/`, `release/` and
`release_1.0/`), and the project's test
suite passes on
the released version. The scientific claims and
their stated limits are the author's own, as is responsibility for the whole.

# Acknowledgements

This work received no financial support.

# References
