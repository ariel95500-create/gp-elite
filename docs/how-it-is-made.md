# How GP_ELITE is made

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/comment-il-est-fait.md).

GP_ELITE has been developed with an AI assistant, Claude (Anthropic), since May
2026, across several successive versions. The author, Sabri Hakou, decides;
the assistant writes the code and the documents, and runs the measurements.
This page says who does what, and how you can check it yourself.

## Before the assistant

The project began without AI. The representation of expressions and the
generation of trees, the protected operators, the asymmetric island model, the
fitting of constants with Adam, the seeding, the interactive console and the
suite of test problems are the author's work. They are still in the engine,
modified since.

## Who does what

The author decides:

- which leads to try, by validating the plan of the next version before any
  measurement (for 1.4, on 11 November 2026);
- whether a version is released, its name and its date (1.4.0 "Signal", on
  23 November 2026);
- what enters `main`: every pull request is merged by the author;
- the publication: the author uploads the files to PyPI; for 1.4.0, after
  checking their SHA-256.

The assistant carries out the work:

- it proposes leads and writes the plans;
- it writes the code, the tests, the measurement scripts, the documentation and
  the paper;
- it runs the measurements, writes the reports and tells the author of any
  departure from the plan.

The assistant never writes directly to `main` and has no access to the PyPI
account.

## What the history shows

As of 23 November 2026:

- Since 27 September 2026, every commit written with the assistant carries the
  line `Co-Authored-By: Claude`. That is the case of 481 of the 547 commits of
  `main`.
- None of these commits was written directly to `main`. All of them entered it
  through one of the eleven pull requests the author merged, from 5 October to
  23 November 2026.
- Before 27 September, the files were committed by the author, and the history
  does not tell what came from the assistant.

## How it is checked

- **The plan before the measurement.** Since 0.8, the hypothesis and the
  criteria of a change to the search are committed before its first
  measurement; the git history shows the order.
- **The results published, whatever they are.** For 1.4, four changes were
  measured; three were not adopted, and their results are published all the
  same
  ([`benchmarks/results_1.4/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.4)).
- **Frozen test sets.** Since 0.9, each version is also measured on sets fixed
  before any decision, which are never used to make one.
- **Two independent reviews before each version, since 0.9.** They are two
  other sessions of the assistant, which have not seen the work. They check the
  claims of the documents against the records and the code. For 1.4.0, they
  raised 26 points, all corrected or answered
  ([first](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_1.4/release/M5_review1.md),
  [second](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_1.4/release/M5_review2.md)).

The method in detail is in [How GP_ELITE is measured](measurements.md).

## Why say it

Code written with an AI raises distrust, and rightly so. Saying it, and showing
how it is checked, is better than keeping quiet about it. Nothing here asks to
be believed: every figure points to its records and to the scripts that
produce them again, and the limits are written down
([what GP_ELITE does not do](../LIMITATIONS.md)).

The paper says so too, in its section "AI usage disclosure"
([`paper/paper.md`](https://github.com/ariel95500-create/gp-elite/blob/main/paper/paper.md)):
the scientific claims, their limits and the responsibility for the whole are
the author's.

If GP_ELITE fails on your data,
[say so](https://github.com/ariel95500-create/gp-elite/issues/new/choose): it
is useful information.
