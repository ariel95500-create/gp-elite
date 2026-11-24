# M5, second independent review: the split itself (24 November 2026)

An agent that had seen neither the work nor the other review reviewed the
split on HEAD 6950444 (`gp_elite/`, `tests/` and `pyproject.toml` are the
same at 6e8480c, where its review ended): is any behaviour changed, does the
rule of the shared state hold everywhere. It compared `core.py` of 1.4.0
with the 19 modules of 1.5 statement by statement after the rule of the
shared state, checked the scope of every global name, ran four probes of the
door under pytest 8.4.2 and 9.2.0, 41 very small fits, and a negative control
in which its checks caught four planted faults (`m5/review2/`). Its answer:
the engine's code is 1.4.0's after the rule (393 statements of 393
identical, none missing), the rule holds everywhere, and import time is
sound. It reported 13 findings (`m5/review2_report.md`): 8 change behaviour
in cases the checks of the plan did not measure, 3 could, and 2 are
documentation; none changes the model a fit returns through the API, the
estimator or the console, and none breaks the repository's own tests,
benches or package. Each was checked against the code and the probe it
names, and holds.

Four are corrected in the code (f5fc346), with the documentation of a fifth;
the others are documented, in the CHANGELOG (1.5.0) and the architecture
pages. The corrected code was checked with the review's own scripts
(`m5/after/`), and built and measured again as the second candidate of the
release (`candidate2/`, and this folder's README).

| # | Finding | What was done |
|---|---|---|
| 1 | A name other than the state's, deleted on `gp_elite.core` and then set again (`monkeypatch.delattr` and its undo), was set on core only: the next fit failed | Corrected: the door records at import, for each name, the modules of the engine that hold the same object, and passes every set and delete on to them. Seven new tests in `tests/test_door.py`; on the former door all but one fail. The review's probe, run again under pytest 9.2.0 with Python 3.11 and 8.4.2 with Python 3.9: 6 of 455 observations differ from 1.4.0 instead of 32, those of findings 2, 5 and 6 and a name 1.4.0 never had, which no function reads (`m5/after/compare_door.txt`); its scenario A now fits (`m5/after/door_demo.txt`) |
| 2 | `unittest.mock.patch` with `create=True` on a name of the state deletes it from `gp_elite.state` when the patch ends | Documented: pytest's `monkeypatch`, or `mock.patch` without `create`, puts it back. As the review says, a copy in core's dictionary would go stale, and mock would put the stale value back |
| 3 | 1.4.0 cannot load a pickle made by 1.5 (the classes name their new modules) | Documented; 1.5 loads the pickles of 1.4.0 and predicts the same |
| 4 | `core.py` no longer runs as a plain script, and the files no longer work as loose modules in a folder | Documented, with the ways that work as before (`gp-elite`, `python -m gp_elite`, `python -m gp_elite.core`). The fallbacks for loose files in `api.py`, `formula.py` and `final_choice.py` stay as in 1.4.0: the modules outside the engine do not change in 1.5 |
| 5 | `importlib.reload(gp_elite.core)` no longer makes the engine afresh | Documented |
| 6 | `vars(gp_elite.core)` and `gp_elite.core.__dict__` no longer hold or reach the state; `type(gp_elite.core)` is `_Door` | Documented |
| 7 | `from gp_elite.core import *` loses the 7 public names of the state and gains `state`; setting `core.state` would replace the state in every module | Documented. The door no longer passes `state` on, and its descriptors keep their own reference to `gp_elite.state`: setting `core.state` changes nothing else (a new test) |
| 8 | The warning for a script without the `__main__` guard comes from `search.py`: a filter on the module `gp_elite.core` no longer silences it | Documented |
| 9 | Option 7 of the console registered `gp_elite.console` as `core` | Corrected: it registers `gp_elite.core`, as in 1.4.0. `m5/after/console_alias_check.py` runs the line as it is in `console.py`: the module registered lacks only the two names a fit sets, as in 1.4.0 |
| 10 | The initializer of the pool registered an empty module named `parallel` in each worker | Corrected: it registers `core` and `gp_v20` from `core.py`, as in 1.4.0 (`m5/after/parallel_probe_init.txt`) |
| 11 | Annotations name classes their module does not import: `typing.get_type_hints` failed on 29 functions and on `gp_elite.state`, and `core.__annotations__` is empty | Corrected where the order of the modules allows it: 8 imports of `Config` and `Node` marked "named in annotations only", and the typing names in `state.py`. It now fails on 4 functions only, whose annotations name a class of a module after theirs, and not on `gp_elite.state` (`m5/after/type_hints_probe.txt`); these and `core.__annotations__` are documented |
| 12 | `help(gp_elite.core)` documents none of the engine's functions; their `__module__`, `inspect` and tracebacks name the new modules | Documented |
| 13 | (a) the docstring of `state.py` on the memories, (b) the comment of `_TIME_LIMIT_HIT` cut mid-sentence, (c) "moved without change" in 15 modules that carry the rule of the state, (d) the CHANGELOG and the architecture pages say more than was measured | (a), (b) and (c) corrected in f5fc346: the 15 docstrings say the module reads and sets the names of the shared state in `gp_elite.state`; numeric and simplification keep "moved without change". (d) The CHANGELOG and both architecture pages no longer say that nothing a user can observe changes, or that scripts written for 1.4.0 work unchanged, and they list the changes above |

The review's scripts, run again on the corrected code (`m5/after/`):
- `compare_split.py`: 391 statements of 1.4.0 identical after the rule, 2
  different, which are the corrections of findings 9 and 10, none missing; 1.5
  adds the door and the 8 imports of finding 11;
- the five static checks: unchanged but for the line numbers and the 8
  imports, all of modules above their importer;
- `names_values.py`: the names of `gp_elite.core` as before, with the door's
  two new private names (`_HOLDERS`, `_STATE`); `import *` as in finding 7.
