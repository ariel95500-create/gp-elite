"""Sets the phase 2 flags of gp_elite.core in every Python process started
with this directory first on PYTHONPATH (benchmarks/speed_equivalence.py
runs each configuration in its own process). GP_ELITE_ARM: A, F1, F3, F3R, G1, G1b, S2, T1, A1, B1, noB1, E1, noE1, N1,
noN1, U1 or noU1 (B1, E1 and N1 are on by default since their adoption; their
mechanics ran at commits 273061b, 4b12ba7 and 28fae46, where A had them off;
U1 is the change of phase 7, benchmarks/results_1.1/PLAN.md, off by default).
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
    if _arm in ("G1", "G1b") and not hasattr(_C, "_FAR_LINEAR"):
        raise SystemExit("the flags of G1 and G1b are not in this engine: run "
                         "from commit 8330827")
    if hasattr(_C, "_GUARD_STRICT"):
        _C._GUARD_STRICT = _arm in ("F1", "F3", "F3R")
        _C._GUARD_SEARCH = _arm not in ("F3", "F3R")
        _C._GUARD_CATCHUP = _arm == "F3R"
    if hasattr(_C, "_FAR_GUARD"):
        _C._FAR_GUARD = _arm in ("G1", "G1b")
        _C._FAR_EXT = 3.0 if _arm == "G1b" else 1.0
    if hasattr(_C, "_FAR_LINEAR"):
        _C._FAR_LINEAR = _arm == "G1b"
    if _arm == "S2" and not hasattr(_C, "_TRIG_SMART"):
        raise SystemExit("the flag of S2 is not in this engine: run from commit e009b27")
    if hasattr(_C, "_TRIG_SMART"):
        _C._TRIG_SMART = _arm == "S2"
    if _arm == "T1" and not hasattr(_C, "_TRIG_SEEDS"):
        raise SystemExit("the flag of T1 is not in this engine: run from commit ec02331")
    if hasattr(_C, "_TRIG_SEEDS"):
        _C._TRIG_SEEDS = _arm == "T1"
    if _arm == "A1" and not hasattr(_C, "_ARG_MUT"):
        raise SystemExit("the flag of A1 is not in this engine: run from commit 878fd47")
    if hasattr(_C, "_ARG_MUT"):
        _C._ARG_MUT = _arm == "A1"
    if _arm in ("B1", "noB1") and not hasattr(_C, "_BINOMIAL_SEEDS"):
        raise SystemExit("the flag of B1 is not in this engine")
    if _arm in ("B1", "noB1"):                    # PLAN_PHASE4.md, change B1,
        _C._BINOMIAL_SEEDS = _arm == "B1"         # on by default since its adoption
    if _arm in ("E1", "noE1") and not hasattr(_C, "_ELEMENTARY_SEEDS"):
        raise SystemExit("the flag of E1 is not in this engine")
    if _arm in ("E1", "noE1"):                    # PLAN_PHASE4.md, change E1,
        _C._ELEMENTARY_SEEDS = _arm == "E1"       # on by default since its adoption
    if _arm in ("N1", "noN1") and not hasattr(_C, "_TOLERANT_SEEDS"):
        raise SystemExit("the flag of N1 is not in this engine")
    if _arm in ("N1", "noN1"):                    # PLAN_PHASE5.md, change N1,
        _C._TOLERANT_SEEDS = _arm == "N1"         # on by default since its adoption
    if _arm in ("U1", "noU1") and not hasattr(_C, "_SEEDS_UNDER_UNITS"):
        raise SystemExit("the flag of U1 is not in this engine")
    if _arm in ("U1", "noU1"):                    # results_1.1/PLAN.md, change U1
        _C._SEEDS_UNDER_UNITS = _arm == "U1"

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
                    catchup=_C.TRACE.value.get("rattrapage"),
                    binomial_seed=_C.TRACE.value.get("binomial_seed"),
                    elementary_seed=_C.TRACE.value.get("elementary_seed"),
                    tolerant_seed=_C.TRACE.value.get("tolerant_seed"),
                    power_law_seed=_C.TRACE.value.get("power_law_seed"),
                    seeds_rejected_units=int(_C.TRACE.count.get(
                        "graines_rejetees_dim", 0)))) + "\n")
    atexit.register(_log)
