"""Sets the phase 2 flags of gp_elite.core in every Python process started
with this directory first on PYTHONPATH (benchmarks/speed_equivalence.py
runs each configuration in its own process). GP_ELITE_ARM: A, F1, F3, F3R or G1.
With GP_ELITE_TRACE_LOG, each process appends its check counters there. The
flags exist in the engine at commit 0038a29 only (PLAN_PHASE2.md, decision).

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
    if _arm in ("F1", "F3", "F3R") and not hasattr(_C, "_GUARD_STRICT"):
        raise SystemExit("the phase 2 flags are not in this engine: run from "
                         "commit 0038a29")
    if _arm == "G1" and not hasattr(_C, "_FAR_GUARD"):
        raise SystemExit("the flag of G1 is not in this engine")
    if hasattr(_C, "_GUARD_STRICT"):
        _C._GUARD_STRICT = _arm in ("F1", "F3", "F3R")
        _C._GUARD_SEARCH = _arm not in ("F3", "F3R")
        _C._GUARD_CATCHUP = _arm == "F3R"
    if hasattr(_C, "_FAR_GUARD"):
        _C._FAR_GUARD = _arm == "G1"

    def _log():
        path = os.environ.get("GP_ELITE_TRACE_LOG")
        if path:
            with open(path, "a") as fh:
                fh.write(json.dumps(dict(
                    arm=_arm, argv=sys.argv[1:3],
                    removed_from_pool=int(_C.TRACE.count.get("pool_rejets_garde", 0)),
                    rejected_in_search=int(_C.TRACE.count.get(
                        "candidats_rejetes_garde", 0)),
                    catchups=int(_C.TRACE.count.get("rattrapages", 0)),
                    far_rejected=int(_C.TRACE.count.get("far_rejets", 0)),
                    catchup=_C.TRACE.value.get("rattrapage"))) + "\n")
    atexit.register(_log)
