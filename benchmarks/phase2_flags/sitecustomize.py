"""Sets the phase 2 flags of gp_elite.core in every Python process started
with this directory first on PYTHONPATH (benchmarks/speed_equivalence.py
runs each configuration in its own process). GP_ELITE_ARM: A, F1 or F3.
With GP_ELITE_TRACE_LOG, each process appends its check counters there.

  GP_ELITE_ARM=F3 GP_ELITE_TRACE_LOG=<file> PYTHONHASHSEED=0 \
  PYTHONPATH=benchmarks/phase2_flags:. python benchmarks/speed_equivalence.py run <dir>
"""
import os

_arm = os.environ.get("GP_ELITE_ARM")
if _arm:
    import atexit
    import json
    import sys

    import gp_elite.core as _C
    _C._GUARD_STRICT = _arm in ("F1", "F3")
    _C._GUARD_SEARCH = _arm != "F3"

    def _log():
        path = os.environ.get("GP_ELITE_TRACE_LOG")
        if path:
            with open(path, "a") as fh:
                fh.write(json.dumps(dict(
                    arm=_arm, argv=sys.argv[1:3],
                    removed_from_pool=int(_C.TRACE.count.get("pool_rejets_garde", 0)),
                    rejected_in_search=int(_C.TRACE.count.get(
                        "candidats_rejetes_garde", 0)))) + "\n")
    atexit.register(_log)
