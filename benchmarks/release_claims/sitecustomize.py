"""Release measurements (benchmarks/results_0.9/PLAN_RELEASE_0.9.md, M3).

With GP_ELITE_AUTO_SEQUENTIAL=1 in the environment and this directory on
PYTHONPATH, the default `parallel=None` runs the islands in sequence, as on a
machine with fewer than four cores: the machine of the 0.8 figures was a
2-core container, where that default runs them in sequence. An explicit
`parallel=True` still runs them in parallel processes. Nothing else changes.
"""
import os

if os.environ.get("GP_ELITE_AUTO_SEQUENTIAL") == "1":
    import gp_elite.core as _core

    _auto = _core._parallel_enabled

    def _parallel_enabled(cfg):
        if getattr(cfg, "PARALLEL_ISLANDS", None) is None:
            return False
        return _auto(cfg)

    _core._parallel_enabled = _parallel_enabled
