# -*- coding: utf-8 -*-
"""Mechanics of N2, before any fit of its campaign (benchmarks/results_1.4/
PLAN.md, "Mechanics of N2"). Every fit or stage runs in its own process,
PYTHONHASHSEED=0, one BLAS thread.

  python mechanics.py run OUT_DIR          (from any folder; about 20 min)
  python mechanics.py report OUT_DIR > mechanics.txt

Item 1, the exact seeds are untouched: 95 fits bounded by 20 generations,
with no time limit (F41 and U41 at seed 0, R6 and R7raw at fold 0), with
1.3.0 from PyPI (/venv13p) and with the candidate (this repository).
Where the noise-tolerant stage of 1.3.0 does not run, the model must be
that of 1.3.0. The other fits are reported.

Items 2 to 4, on the 82 noisy targets of F41 (seed 0, 1 % and 10 %): the
noise-tolerant stage is called by a fit of one generation, and its inputs
(the training rows after the hold-out, in the internal variables) are
kept. In the candidate the stage is then run twice on them: with N2
switched off (core._TOLERANT_N2 = False, the code of 1.3.0) and on. The
seeds of the first run are checked against those 1.3.0 from PyPI prints on
the same fit; every form they hold must be among the seeds of the second.
A candidate "has the structure of the law" when its constants, refitted on
the noiseless targets of the same rows with the engine's finishing step,
leave less than 1e-9 of their variance (the test of structure of the
bench).

Items 5 and 6: the candidates on the 13 real fits, with their scores, and
the time of the stage, from the fits of item 1.

[N2b] With N2B_MECHANICS=1 in the environment, the candidate is N2b on
1.3.0: N2 on, without the fit of the constants of its candidates, and E2 and
S1 off, whatever the defaults of the engine (benchmarks/results_1.4/PLAN.md,
"Decision of the author after the campaigns of N2 and S1").
"""
import io
import json
import os
import subprocess
import sys
import time
import warnings
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.dirname(BENCH)
PY13 = "/venv13p/bin/python"
ENGINES = {"1.3.0": "/nonexistent", "candidate": ROOT}
NAMED = ("I.40.1", "II.35.18", "II.11.27", "I.32.5", "III.19.51")
GENS = 20


def _setup(engine_dir):
    sys.path.insert(0, engine_dir)
    sys.path.insert(1, BENCH)


def _n2b(C):
    """[N2b] The candidate of the mechanics of N2b, set before a fit."""
    if os.environ.get("N2B_MECHANICS") == "1" and hasattr(C, "_TOLERANT_N2"):
        C._TOLERANT_N2 = True
        C._TOLERANT_REFIT = False
        C._E2_SEEDS = False
        C._SMALL_CV = False


def _jobs_bounded():
    with redirect_stdout(io.StringIO()):
        import decision_bench as D
        import feynman_bench as F
    out = []
    for kind in ("feyn", "ufeyn"):
        for i, p in enumerate(F.PROBS):
            out.append(dict(kind=kind, problem=p[0], index=i, split="test", seed=0))
    for kind, names in (("real", D.REAL), ("realraw", D.REAL_RAW)):
        for n in names:
            out.append(dict(kind=kind, problem=n, split="fold0", seed=0))
    return out


def _jobs_noisy():
    with redirect_stdout(io.StringIO()):
        import feynman_bench as F
    return [dict(kind=kind, problem=p[0], index=i, split="test", seed=0)
            for kind in ("feyn_n1", "feyn_n10") for i, p in enumerate(F.PROBS)]


# ───────────────────────────────────────────────────────────── one fit ──

def one_fit(job):
    """Item 1: one fit of GENS generations, no time limit."""
    import phase1_bench as B
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    import decision_bench as D
    Xtr, ytr, Xte, yte, _xo, _yo, names, pool, _clean = B._data(job)
    _n2b(C)
    kw = dict(generations=GENS, seed=job["seed"], parallel=False, verbose=False,
              operators=pool)
    if names is not None:
        kw["feature_names"] = names
    if job["kind"] == "ufeyn":
        import units_table as U
        units, tunits = U.units_of(job["problem"], names)
        kw.update(units=units, target_units=tunits)
    cands = []
    if hasattr(C, "_refit_inner"):              # the candidate: its candidates
        orig = C._refit_inner

        def noted(tree, X, y, cfg):
            out = orig(tree, X, y, cfg)
            cands.append((C.to_string(out), C._seed_rel_error(out, X, y)))
            return out
        C._refit_inner = noted
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, **kw)
    tr = C.TRACE.value
    return dict(job, engine=gp_elite.__file__, time=round(time.time() - t0, 2),
                expr=r.expression, err=D.one_minus_r2(yte, r.predict(Xte)),
                size=int(r.size), formula_exact=r.formula_exact,
                stage_ran="tolerant_seed_s" in tr,
                stage_s=tr.get("tolerant_seed_s"),
                exact_seeds=[k for k in ("power_law_seed", "binomial_seed",
                                         "elementary_seed") if tr.get(k)],
                tolerant_seed=tr.get("tolerant_seed"),
                tolerant_cands=tr.get("tolerant_cands"),
                candidates=sorted(cands, key=lambda c: c[1])[:40])


# ─────────────────────────────────────────────────────────── one stage ──

def _structure_err(tree, X, y_clean, cfg):
    """1 - R² of a candidate refitted on the noiseless targets of its rows
    (internal variables), with the engine's finishing step."""
    import gp_elite.core as C
    with np.errstate(all="ignore"):
        fitted = C._lm_to_convergence(tree.copy(), X, y_clean, cfg)
        t = fitted if fitted is not None else tree.copy()
        return C._seed_rel_error(t, X, y_clean)


def one_stage(job):
    """Items 2 to 4 on one noisy target (candidate engine only)."""
    import phase1_bench as B
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    Xtr, ytr, _xte, _yte, _xo, _yo, names, pool, clean = B._data(job)
    if not hasattr(C, "_TOLERANT_N2"):
        # 1.3.0: the seeds it places on this fit, as it prints them
        with redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            symbolic_regression(Xtr, ytr, generations=1, seed=job["seed"],
                                parallel=False, verbose=False, operators=pool,
                                feature_names=names)
        return dict(job, engine=gp_elite.__file__,
                    stage_ran="tolerant_seed_s" in C.TRACE.value,
                    tolerant_seed=C.TRACE.value.get("tolerant_seed"))
    _n2b(C)
    seen = {}
    orig_stage, orig_refit = C._make_tolerant_seeds, C._refit_inner

    def stage(xs, ys, cfg, power_done=False):
        if seen:                                    # a later restart
            return orig_stage(xs, ys, cfg, power_done)
        C._TOLERANT_N2 = False
        old = orig_stage(xs, ys, cfg, power_done)
        old_text = C.TRACE.value.get("tolerant_seed")
        C._TOLERANT_N2 = True
        cands = []

        def noted(tree, X, y, cfg_):
            out = orig_refit(tree, X, y, cfg_)
            cands.append(out)
            return out
        C._refit_inner = noted
        t0 = time.time()
        new = orig_stage(xs, ys, cfg, power_done)
        dt = time.time() - t0
        C._refit_inner = orig_refit
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        # the rows of the stage: its targets are the noisy training targets
        # divided by the scale of the target
        ytr_n = np.asarray(ytr, dtype=float)
        scale = float(C._target_scale(ytr_n))      # as the API divides y
        rows = np.array([int(np.argmin(np.abs(ytr_n - v))) for v in y * scale])
        matched = bool(np.allclose(ytr_n[rows], y * scale, rtol=1e-9, atol=0)
                       and len(set(rows.tolist())) == len(rows))
        yc = np.asarray(clean, dtype=float)[rows] / scale
        law = C._pred_rel_error(yc, y)            # the law itself
        old_h = [t.canonical_hash() for t in old]
        new_h = [t.canonical_hash() for t in new]
        cand_rows = []
        for t in cands:
            cand_rows.append(dict(
                expr=C.to_string(t)[:220], score=C._seed_rel_error(t, X, y),
                structure=_structure_err(t, X, yc, cfg) < 1e-9,
                placed=t.canonical_hash() in new_h,
                has_log="log(" in C.to_string(t),
                has_trig="sin(" in C.to_string(t) or "cos(" in C.to_string(t)))
        seen.update(
            n_rows=len(y), rows_matched=matched, law_score=law,
            power_done=bool(power_done),
            old=[C.to_string(t) for t in old], old_text=old_text,
            old_structure=[_structure_err(t, X, yc, cfg) < 1e-9 for t in old],
            new=[C.to_string(t) for t in new],
            new_structure=[_structure_err(t, X, yc, cfg) < 1e-9 for t in new],
            old_forms_kept=all(h in new_h for h in old_h),
            stage_s=round(dt, 3), candidates=sorted(
                cand_rows, key=lambda c: c["score"]))
        return new
    C._make_tolerant_seeds = stage
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(Xtr, ytr, generations=1, seed=job["seed"],
                            parallel=False, verbose=False, operators=pool,
                            feature_names=names)
    C._make_tolerant_seeds = orig_stage
    return dict(job, engine=gp_elite.__file__, stage_ran=bool(seen), **seen)


# ───────────────────────────────────────────────────────────── driver ──

def _child(cmd, engine, job):
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    p = subprocess.run([PY13, "-I", os.path.abspath(__file__), cmd,
                        ENGINES[engine], json.dumps(job)],
                       capture_output=True, text=True, env=env, cwd="/")
    lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
    if p.returncode != 0 or not lines:
        return dict(job, crash=True, stderr=p.stderr[-600:])
    return json.loads(lines[-1])


def run(out_dir, parts=("bounded", "stage")):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(out_dir, exist_ok=True)
    _setup(ROOT)
    work = []
    for eng in ENGINES:
        if "bounded" in parts:
            for j in _jobs_bounded():
                work.append(("one-fit", eng, j, "bounded_%s.jsonl" % eng))
        if "stage" in parts:
            for j in _jobs_noisy():
                work.append(("one-stage", eng, j, "stage_%s.jsonl" % eng))
    print("%d processes" % len(work), flush=True)
    with ThreadPoolExecutor(4) as ex:
        recs = list(ex.map(lambda w: (w[3], _child(w[0], w[1], w[2])), work))
    files = {}
    for name, rec in recs:
        files.setdefault(name, []).append(rec)
    for name, rr in files.items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            for rec in rr:
                fh.write(json.dumps(rec) + "\n")
    print("written:", sorted(files))


def _load(path):
    return [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]


def report(out_dir):
    A = {(r["kind"], r["problem"]): r for r in _load(os.path.join(out_dir, "bounded_1.3.0.jsonl"))}
    B = {(r["kind"], r["problem"]): r for r in _load(os.path.join(out_dir, "bounded_candidate.jsonl"))}
    crashes = [k for k in list(A) + list(B) if (A.get(k) or {}).get("crash")
               or (B.get(k) or {}).get("crash")]
    print("engines: %s / %s" % (sorted({r.get("engine") for r in A.values()}),
                                sorted({r.get("engine") for r in B.values()})))
    print("crashes: %d" % len(crashes))
    print("\n== 1. The exact seeds are untouched: %d bounded fits (%d generations, "
          "no time limit)" % (len(A), GENS))
    same, differ, other = [], [], []
    for k in A:
        a, b = A[k], B[k]
        if a["stage_ran"]:
            other.append(k)
        elif a["expr"] == b["expr"] and a["err"] == b["err"]:
            same.append(k)
        else:
            differ.append(k)
    print("  noise-tolerant stage of 1.3.0 not run: %d fits; the model of the "
          "candidate is that of 1.3.0 in %d, differs in %d"
          % (len(same) + len(differ), len(same), len(differ)))
    for k in differ:
        print("    DIFFERS %s %s: %s / %s" % (k[0], k[1], A[k]["expr"][:80], B[k]["expr"][:80]))
    print("  stage of 1.3.0 run: %d fits (reported, decide nothing)" % len(other))
    n_same = sum(1 for k in other if A[k]["expr"] == B[k]["expr"])
    print("    same model in %d of them; the others:" % n_same)
    for k in other:
        a, b = A[k], B[k]
        if a["expr"] == b["expr"]:
            continue
        print("    %-8s %-10s 1-R² test %.3g -> %.3g; seeds placed %s -> %s" % (
            k[0], k[1], a["err"], b["err"],
            "none" if not a.get("tolerant_seed") else len(a["tolerant_seed"].split(" | ")),
            "none" if not b.get("tolerant_seed") else len(b["tolerant_seed"].split(" | "))))
    for kind in ("feyn", "ufeyn"):
        ea = sum(1 for k in A if k[0] == kind and A[k]["err"] < 1e-9)
        eb = sum(1 for k in B if k[0] == kind and B[k]["err"] < 1e-9)
        print("  %s: exact (1-R² < 1e-9 on the test rows) in %d of 41 with 1.3.0, "
              "%d with the candidate" % (kind, ea, eb))

    print("\n== 5. The real data: the candidates of the stage on the 13 real fits")
    for k in B:
        if k[0] not in ("real", "realraw"):
            continue
        b, a = B[k], A[k]
        c = b.get("candidates") or []
        best = c[0][1] if c else None
        print("  %-8s %-24s 1.3.0 places %s; candidate: %s; best score %s; placed %s" % (
            k[0], k[1], "none" if not a.get("tolerant_seed") else a["tolerant_seed"][:60],
            b.get("tolerant_cands"), "-" if best is None else "%.4f" % best,
            "none" if not b.get("tolerant_seed") else b["tolerant_seed"][:80]))
    print("\n== 6. The time of the stage on the fits of item 1 (where it runs), s")
    for eng, R in (("1.3.0", A), ("candidate", B)):
        t = [r["stage_s"] for r in R.values() if r.get("stage_s") is not None]
        if t:
            print("  %-9s %d fits: median %.3f, largest %.3f" % (
                eng, len(t), float(np.median(t)), max(t)))

    S13 = {(r["kind"], r["problem"]): r for r in _load(os.path.join(out_dir, "stage_1.3.0.jsonl"))}
    SC = {(r["kind"], r["problem"]): r for r in _load(os.path.join(out_dir, "stage_candidate.jsonl"))}
    print("\n== 2. No seed is lost: the 82 noisy targets of F41 (seed 0)")
    ran = [k for k in SC if SC[k].get("stage_ran")]
    print("  the stage runs on %d targets; rows of the stage found in the "
          "training rows on %d" % (len(ran), sum(1 for k in ran if SC[k]["rows_matched"])))
    same_text = sum(1 for k in ran if SC[k]["old_text"] == S13[k].get("tolerant_seed"))
    print("  N2 off: the seeds printed are those of 1.3.0 from PyPI on %d of %d"
          % (same_text, len(ran)))
    for k in ran:
        if SC[k]["old_text"] != S13[k].get("tolerant_seed"):
            print("    DIFFER %s %s" % k)
    n_old = sum(1 for k in ran if SC[k]["old"])
    kept = sum(1 for k in ran if SC[k]["old"] and SC[k]["old_forms_kept"])
    print("  1.3.0 places a seed on %d targets; every form it places is placed by "
          "the candidate on %d" % (n_old, kept))
    for k in ran:
        if SC[k]["old"] and not SC[k]["old_forms_kept"]:
            print("    LOST on %s %s" % k)
    print("  seeds placed: %d targets with 1.3.0, %d with the candidate; "
          "%d seeds in all against %d"
          % (n_old, sum(1 for k in ran if SC[k]["new"]),
             sum(len(SC[k]["old"]) for k in ran), sum(len(SC[k]["new"]) for k in ran)))
    for lvl in ("feyn_n1", "feyn_n10"):
        ks = [k for k in ran if k[0] == lvl]
        print("  %s: a seed with the structure of the law placed on %d targets "
              "with 1.3.0, %d with the candidate (of %d where the stage runs)"
              % (lvl, sum(1 for k in ks if any(SC[k]["old_structure"])),
                 sum(1 for k in ks if any(SC[k]["new_structure"])), len(ks)))
        lost = [k[1] for k in ks if any(SC[k]["old_structure"])
                and not any(SC[k]["new_structure"])]
        won = [k[1] for k in ks if any(SC[k]["new_structure"])
               and not any(SC[k]["old_structure"])]
        print("    gained: %s" % (", ".join(won) or "none"))
        print("    lost: %s" % (", ".join(lost) or "none"))
    print("\n== 3. The second pass: the five equations that lose the single sign")
    for p in NAMED:
        for lvl in ("feyn_n1", "feyn_n10"):
            r = SC.get((lvl, p))
            if not r or not r.get("stage_ran"):
                print("  %-9s %-8s the stage does not run" % (p, lvl))
                continue
            made = any(c["structure"] for c in r["candidates"])
            placed = any(r["new_structure"])
            print("  %-9s %-8s the law leaves %.2e (%s the threshold); a candidate "
                  "with its form: %s; placed: %s; 1.3.0 places %d seed(s)" % (
                      p, lvl, r["law_score"],
                      "within" if r["law_score"] <= 0.015 else "above",
                      "yes" if made else "NO", "yes" if placed else "no",
                      len(r["old"])))
    print("\n== 4. The best kept")
    r = SC[("feyn_n1", "III.15.12")]
    tr = [c for c in r["candidates"] if c["has_trig"] and c["structure"]]
    print("  III.15.12, 1 %%: a trigonometric candidate with the structure of the "
          "law: %s; placed: %s" % ("yes" if tr else "NO",
                                   "yes" if any(c["placed"] for c in tr) else "NO"))
    for c in tr[:2]:
        print("    %s (score %.2g)" % (c["expr"][:150], c["score"]))
    r = SC[("feyn_n1", "I.44.4")]
    lg = [c for c in r["candidates"] if c["has_log"] and c["structure"]]
    print("  I.44.4, 1 %%: a candidate with the logarithm and the structure of the "
          "law: %s; placed: %s" % ("yes" if lg else "NO",
                                   "yes" if any(c["placed"] for c in lg) else "no"))
    for c in lg[:2]:
        print("    %s (score %.2g)" % (c["expr"][:150], c["score"]))
    t = [SC[k]["stage_s"] for k in ran]
    print("\n== 6. The time of the stage on the 82 noisy targets: median %.3f s, "
          "largest %.3f s" % (float(np.median(t)), max(t)))


def main():
    cmd = sys.argv[1]
    if cmd in ("one-fit", "one-stage"):
        _setup(sys.argv[2])
        job = json.loads(sys.argv[3])
        out = one_fit(job) if cmd == "one-fit" else one_stage(job)
        print(json.dumps(out))
    elif cmd == "run":
        run(sys.argv[2], tuple(sys.argv[3].split(",")) if len(sys.argv) > 3
            else ("bounded", "stage"))
    else:
        report(sys.argv[2])


if __name__ == "__main__":
    main()
