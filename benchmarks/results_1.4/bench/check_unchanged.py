# -*- coding: utf-8 -*-
"""The bench options of 1.4 leave the benches of before unchanged.

Plan: ../PLAN.md, "The benches". phase1_bench.py gets --noise-draws and the
kinds of TF78N; tp_diagnostic.py gets --set tpt10. This script compares the
two files with those of the commit before (f93f77b):

  1. without the new options, the jobs are the same, in the same order,
     with the same keys;
  2. the data of every job are the same arrays, byte for byte;
  3. the new jobs are those the plan counts, and their data are sound.

    python benchmarks/results_1.4/bench/check_unchanged.py > check_unchanged.txt
"""
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
BEFORE = "f93f77b"
sys.path.insert(0, BENCH)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def before(fname, tmp):
    """The file of the commit before, written beside nothing else."""
    text = subprocess.run(["git", "-C", ROOT, "show",
                           "%s:benchmarks/%s" % (BEFORE, fname)],
                          capture_output=True, text=True, check=True).stdout
    path = os.path.join(tmp, "before_" + fname)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    mod = load("before_" + fname[:-3], path)
    mod.HERE = BENCH                    # its data files are those of the bench
    return mod


def digest(arrays):
    h = hashlib.sha256()
    for a in arrays:
        if a is None:
            h.update(b"None")
        elif isinstance(a, np.ndarray):
            h.update(str(a.shape).encode() + str(a.dtype).encode())
            h.update(np.ascontiguousarray(a).tobytes())
        else:
            h.update(repr(a).encode())
    return h.hexdigest()


def main():
    ok = True

    def check(label, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-66s %s" % (label, "holds" if cond else "FAILS"))

    with tempfile.TemporaryDirectory() as tmp:
        P0 = before("phase1_bench.py", tmp)
        T0 = before("tp_diagnostic.py", tmp)
        import phase1_bench as P1
        import tp_diagnostic as T1

        print("== phase1_bench.py, against %s" % BEFORE)
        for units in (False, True):
            a, b = P0.all_jobs(units), P1.all_jobs(units)
            check("jobs, with_units=%s: %d before, %d now, same list"
                  % (units, len(a), len(b)), a == b)
            check("their keys are the same",
                  [P0.key(j) for j in a] == [P1.key(j) for j in b])
        jobs = P1.all_jobs(True)
        seen, n_same, n_diff = set(), 0, []
        for j in jobs:
            k = (j["kind"], j["problem"], j["split"])   # the data ignore the seed
            if k in seen:
                continue
            seen.add(k)
            if digest(P0._data(j)) == digest(P1._data(j)):
                n_same += 1
            else:
                n_diff.append(k)
        check("data of the %d distinct (kind, problem, split): identical"
              % len(seen), not n_diff)
        if n_diff:
            print("    differ:", n_diff[:5])

        print("\n== the new draws of the noise (--noise-draws 1,2,3,4)")
        P1.NOISE_DRAWS = [1, 2, 3, 4]
        P1.BENCH_SEEDS = [0]
        conf = [j for j in P1.all_jobs(False)
                if j["kind"] in ("feyn_n1", "feyn_n10")]
        check("feyn_n1 and feyn_n10 at seed 0: %d jobs (the plan: 328)"
              % len(conf), len(conf) == 328)
        check("their keys are all distinct",
              len({P1.key(j) for j in conf}) == len(conf))
        P1.NOISE_DRAWS = [0, 1]
        mixed = [j for j in P1.all_jobs(False) if j["kind"] == "feyn_n1"]
        check("draw 0 asked for with another: the job of before, no field",
              sum("noise_draw" not in j for j in mixed) == 41
              and sum(j.get("noise_draw") == 1 for j in mixed) == 41)
        P1.NOISE_DRAWS = None
        P1.BENCH_SEEDS = [0, 1, 2, 3, 4]
        same_x = same_clean = distinct = 0
        level = []
        for j in conf:
            base = dict(j)
            base.pop("noise_draw")
            d0, d = P1._data(base), P1._data(j)
            same_x += digest(d0[:1] + d0[2:]) == digest(d[:1] + d[2:])
            same_clean += np.array_equal(d0[8], d[8])
            distinct += not np.array_equal(d0[1], d[1])
            level.append(float(np.std(d[1] - d[8]) / np.std(d[8]))
                         / P1.NOISE[j["kind"]])
        check("inputs, test rows and clean targets: those of draw 0",
              same_x == len(conf) and same_clean == len(conf))
        check("noisy targets: other than those of draw 0, in every job",
              distinct == len(conf))
        targets = {}
        for j in conf:
            targets.setdefault((j["kind"], j["problem"]), set()).add(
                digest([P1._data(j)[1]]))
        check("the four draws of an equation differ from one another",
              all(len(v) == 4 for v in targets.values()))
        print("    noise measured / noise asked for: median %.3f, from %.3f "
              "to %.3f" % (np.median(level), min(level), max(level)))

        print("\n== TF78N, the frozen noisy test set (on request only)")
        tn = [j for j in P1.all_jobs(False, True) if j["kind"] in P1.TESTN_KINDS]
        check("%d jobs (the plan: 312), 78 per kind, seed 5"
              % len(tn), len(tn) == 312 and all(j["seed"] == 5 for j in tn)
              and all(sum(j["kind"] == k for j in tn) == 78
                      for k in P1.TESTN_KINDS))
        check("they are not among the jobs of a run without them",
              not [j for j in P1.all_jobs(True) if j["kind"] in P1.TESTN_KINDS])
        same = clean_ok = 0
        level, seeds = [], set()
        import test_set as TS
        for j in tn:
            d = P1._data(j)
            d0 = P1._data(dict(j, kind="tf"))
            same += digest(d0[:1] + d0[2:8]) == digest(d[:1] + d[2:8])
            clean_ok += np.array_equal(d[8], d0[1])
            level.append(float(np.std(d[1] - d[8]) / np.std(d[8]))
                         / P1.NOISE[j["kind"]])
            seeds.add(7000 + 500 + TS.names("TF78").index(j["problem"]))
        check("inputs, test and out-of-domain rows: those of TF78",
              same == len(tn))
        check("clean targets: the training targets of TF78",
              clean_ok == len(tn))
        check("their generators (7500 to 7577) are not those of F41 "
              "(7000 to 7040)", min(seeds) == 7500 and max(seeds) == 7577)
        a = P1._data(dict(kind="tf_n1", problem=tn[0]["problem"], split="test",
                          seed=5))
        b = P1._data(dict(kind="utf_n1", problem=tn[0]["problem"],
                          split="test", seed=5))
        check("with and without units: the same noisy targets",
              np.array_equal(a[1], b[1]))
        print("    noise measured / noise asked for: median %.3f, from %.3f "
              "to %.3f" % (np.median(level), min(level), max(level)))

        print("\n== tp_diagnostic.py, against %s" % BEFORE)
        draws = tuple(range(15))
        a, b = T0.all_jobs(draws), T1.all_jobs(draws)
        check("jobs of the diagnostic, draws 0 to 14: %d before, %d now, same"
              % (len(a), len(b)), a == b)
        check("default jobs (draws 0 to 4): %d, same"
              % len(T1.all_jobs()), T0.all_jobs() == T1.all_jobs())
        seen, diff = set(), 0
        for j in b:
            k = (j["exp"], j["n"], j["noise"], j["draw"])
            if k in seen:
                continue
            seen.add(k)
            diff += digest(T0.data(*k)) != digest(T1.data(*k))
        check("data of the %d distinct tables: identical" % len(seen),
              diff == 0)

        print("\n== TPT10, the frozen test set for teaching (--set tpt10)")
        tj = T1.all_jobs(exp_set="tpt10")
        check("%d jobs (the plan: 400), 10 experiments, two arms"
              % len(tj), len(tj) == 400
              and len({j["exp"] for j in tj}) == 10
              and sum(j["arm"] == "plain" for j in tj) == 200)
        check("its experiments are numbered 10 to 19 in the generator",
              [T1.experiment(e["key"])[0] for e in T1.EXPERIMENTS_T]
              == list(range(10, 20)))
        check("no key of TPT10 is a key of the diagnostic",
              not {e["key"] for e in T1.EXPERIMENTS_T}
              & {e["key"] for e in T1.EXPERIMENTS})
        used = {}
        for src, lst in (("tp", T1.EXPERIMENTS), ("tpt10", T1.EXPERIMENTS_T)):
            for e in lst:
                k = T1.experiment(e["key"])[0]
                for n in T1.SIZES:
                    for nz in T1.NOISES:
                        for d in range(15):
                            used.setdefault(
                                100003 * d + 1009 * n
                                + int(round(1000 * nz)) + 17 * k,
                                []).append((src, e["key"], n, nz, d))
        clash = [v for v in used.values()
                 if len({x[0] for x in v}) > 1]
        check("no table of TPT10 shares the generator of a table of the "
              "diagnostic", not clash)
        print("    the plan's table, read back from the list:")
        for e in T1.EXPERIMENTS_T:
            X, y, yc, Xg, yg = T1.data(e["key"], 10, 0.02, 0)
            print("    %-13s %-28s %-9s %s; target from %.4g to %.4g; %s"
                  % (e["key"], e["law"], e["pool"],
                     ", ".join("%s %g to %g" % (nm, lo, hi)
                               for nm, lo, hi, _u in e["inputs"]),
                     float(np.min(yg)), float(np.max(yg)),
                     "within reach under units"
                     if e["key"] in T1.REACHABLE_UNITS_T
                     else "not within reach under units"))
        finite = all(np.all(np.isfinite(T1.data(e["key"], n, nz, d)[i]))
                     for e in T1.EXPERIMENTS_T for n in T1.SIZES
                     for nz in T1.NOISES for d in range(5) for i in range(5))
        check("every table and grid of TPT10 is finite", finite)

    print("\n" + ("All of it holds." if ok else "SOMETHING FAILS."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
