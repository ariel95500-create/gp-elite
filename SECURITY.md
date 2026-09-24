# Security policy

## Supported versions

Fixes go into the latest release published on PyPI. Older versions are not
patched: upgrade with `pip install -U gp-elite`.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Write to
**ariel95500@gmail.com** with a description and, if you can, a minimal way to
reproduce it. You will get an answer within seven days, and credit in the
release notes if you want it.

## What the library does and does not do

Useful to know when assessing a report:

- GP_ELITE makes no network access.
- `symbolic_regression` and `GPEliteRegressor.fit` read nothing but the arrays
  you pass and write no file at all.
- The interactive console (`gp-elite`) writes its outputs in the current
  directory (`gp_elite_log.csv`, `gp_elite_best.txt`), and some of its demo
  modes load a saved grammar, `grammar_shared_base.json`, from that directory
  if one is present.
- Evolved expressions are compiled to NumPy code with `exec`. The source is
  generated only from the engine's fixed operator table, column indices and
  numeric constants; no string coming from your data or from a file reaches
  it.
- Saved grammars (`export_grammar` / `import_grammar`) are JSON, not pickle.
