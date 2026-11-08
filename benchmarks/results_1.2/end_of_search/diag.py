"""The diagnostic of the end of the search (PLAN.md in this folder).

The engine is observed by wrapping five of its functions from this script;
no file of the package is changed. Each fit is the fit of the bench
(benchmarks/phase1_bench.py, run_one), in its own process, with
PYTHONHASHSEED=0 and one BLAS thread. After the timed fit, every distinct
candidate the search offered to the pool is put through the engine's own
polish (_polish_finalists, on that candidate alone, with no deadline), and
is "within reach" if a variant comes back exact on the hold-out by the test
of _track_if_exact.

  python diag.py check --python /venv12p/bin/python --out check.jsonl
  python diag.py run --python /venv12p/bin/python --jobs jobs.jsonl \
         --out records.jsonl --workers 4
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)


def _install():
    """Wrap the end of the search; return the state the wraps fill."""
    import numpy as np
    import gp_elite.core as C
    S = dict(phase="search", offered={}, n_offer=0, finalists=None,
             pool=None, fin=[], started=[], cur=None, conv=set(),
             admitted=[], xs=None, ys=None, cfg=None, polish_s=None,
             after_deadline_s=None, selected=None, n_polish_calls=0)

    def h(node):
        try:
            return node.exact_hash()
        except Exception:
            return None

    track0 = C._track_val_candidate

    def track(cand):
        ids = {id(t[3]) for t in C._VAL_CANDS}
        track0(cand)
        if cand is None or C._VAL_XS is None or S["phase"] == "offline":
            return
        entered = any(id(t[3]) not in ids for t in C._VAL_CANDS)
        k = h(cand)
        if k is None:
            return
        if S["phase"] == "search":
            S["n_offer"] += 1
            e = S["offered"].get(k)
            if e is None:
                S["offered"][k] = dict(node=cand.copy(), entered=entered,
                                       n=1, size=int(C.tree_size(cand)))
            else:
                e["n"] += 1
                e["entered"] = e["entered"] or entered
        elif S["phase"] == "polish" and entered:
            S["admitted"].append(k)

    fin0 = C._finalists

    def finalists(cfg, k=8):
        out = fin0(cfg, k)
        top = sorted(C._VAL_CANDS, key=lambda t: (t[0], t[2]))[:k]
        top_ids = {id(t[3]) for t in top}
        S["finalists"] = [dict(hash=h(t[3]), size=int(t[2]), mse=t[0],
                               group="best" if id(t[3]) in top_ids else "small")
                          for t in out]
        S["pool"] = [dict(hash=h(t[3]), size=int(t[2]), mse=t[0])
                     for t in C._VAL_CANDS]
        return out

    pol0 = C._polish_finalists

    def polish(top, xs, ys, cfg):
        if S["phase"] == "offline":
            return pol0(top, xs, ys, cfg)
        S["n_polish_calls"] += 1
        S.update(phase="polish", xs=xs, ys=ys, cfg=cfg,
                 fin=[h(t[3]) for t in top])
        dl = getattr(cfg, "DEADLINE", None)
        t0 = time.time()
        S["after_deadline_s"] = None if dl is None else round(t0 - dl, 3)
        try:
            return pol0(top, xs, ys, cfg)
        finally:
            S["polish_s"] = round(time.time() - t0, 3)
            S["phase"] = "after"

    adam0 = C.optimize_constants_adam

    def adam(node, *a, **kw):
        if S["phase"] == "polish":
            k = h(node)
            if k in S["fin"] and k not in S["started"]:
                S["cur"] = k
                S["started"].append(k)
        return adam0(node, *a, **kw)

    lm0 = C._lm_to_convergence

    def lm(node, *a, **kw):
        if S["phase"] == "polish" and S["cur"] is not None:
            S["conv"].add(S["cur"])
        return lm0(node, *a, **kw)

    sel0 = C._select_one_se

    def select(champion, champ_val):
        out = sel0(champion, champ_val)
        if S["phase"] != "offline":
            S["selected"] = dict(hash=h(out[0]), size=int(C.tree_size(out[0])),
                                 mse=out[1])
        return out

    C._track_val_candidate = track
    C._finalists = finalists
    C._polish_finalists = polish
    C.optimize_constants_adam = adam
    C._lm_to_convergence = lm
    C._select_one_se = select
    return S


def _within_reach(S):
    """Each distinct candidate offered during the search, through the polish
    of the engine alone and with no deadline: exact on the hold-out or not."""
    import numpy as np
    import gp_elite.core as C
    xs, ys, cfg = S["xs"], S["ys"], S["cfg"]
    if xs is None or C._VAL_YS is None or len(C._VAL_YS) < 2:
        return None
    var_val = float(np.var(C._VAL_YS))
    floor = C._EXACT_REL * var_val
    keep_pool = list(C._VAL_CANDS)
    keep_dl = getattr(cfg, "DEADLINE", None)
    keep_stable = C._is_numerically_stable
    S["phase"] = "offline"
    cfg.DEADLINE = None
    # Within reach is read on the polish alone: the stability guard of the
    # pool is lifted here, and read apart on the candidate as the search
    # offered it (class 2 of PLAN.md).
    C._is_numerically_stable = lambda cand: True
    reach = {}
    t0 = time.time()
    try:
        for k, e in S["offered"].items():
            del C._VAL_CANDS[:]
            with redirect_stdout(io.StringIO()), np.errstate(all="ignore"):
                try:
                    C._polish_finalists([(0.0, 0.0, e["size"], e["node"])],
                                        xs, ys, cfg)
                except Exception:
                    pass
            # Exact by the test of _track_if_exact: hold-out MSE at most
            # _EXACT_REL times the variance of the hold-out targets.
            best = min((t[0] for t in C._VAL_CANDS), default=float("inf"))
            reach[k] = dict(reach=bool(best <= floor),
                            best_rel=(best / var_val) if np.isfinite(best) else None)
    finally:
        C._is_numerically_stable = keep_stable
        del C._VAL_CANDS[:]
        C._VAL_CANDS.extend(keep_pool)
        cfg.DEADLINE = keep_dl
    S["offline_s"] = round(time.time() - t0, 1)
    return reach


def one(job):
    import numpy as np
    import phase1_bench as B
    wrap = not job.get("no_wrap")
    if job.get("gens_only"):
        B.TIME_LIMIT, B.GENERATIONS = None, int(job["gens_only"])
    S = _install() if wrap else None
    bench_job = {k: v for k, v in job.items()
                 if k not in ("no_wrap", "gens_only", "study_status",
                              "study_generations", "arm")}
    rec = B.run_one(bench_job)
    rec.update({k: job[k] for k in job if k not in bench_job})
    if not wrap:
        return rec
    import gp_elite.core as C
    reach = _within_reach(S)
    stable = {}
    for k, e in S["offered"].items():
        if reach and reach[k]["reach"]:
            try:
                stable[k] = bool(C._is_numerically_stable(e["node"]))
            except Exception:
                stable[k] = False
    pool = {p["hash"] for p in (S["pool"] or [])}
    fin = {f["hash"]: f for f in (S["finalists"] or [])}
    cands = []
    for k, e in S["offered"].items():
        if reach and reach[k]["reach"]:
            cands.append(dict(
                size=e["size"], offered=e["n"], entered=e["entered"],
                stable=stable.get(k), in_pool=k in pool,
                finalist=fin[k]["group"] if k in fin else None,
                conv_ran=k in S["conv"], best_rel=reach[k]["best_rel"],
                expr=C.to_string(e["node"])[:200]))
    rec.update(diag=dict(
        n_offer=S["n_offer"], n_distinct=len(S["offered"]),
        pool_size=len(S["pool"] or []), finalists=S["finalists"],
        conv_ran=len(S["conv"]), started=len(S["started"]),
        polish_s=S["polish_s"], after_deadline_s=S["after_deadline_s"],
        n_polish_calls=S["n_polish_calls"], admitted=len(S["admitted"]),
        selected=S["selected"], offline_s=S.get("offline_s"),
        within_reach=cands))
    return rec


def _env():
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    return env


def _key(j):
    return (j["kind"], j["problem"], j["split"], j["seed"],
            j.get("budget_factor"), j.get("gens_only"), bool(j.get("no_wrap")))


def drive(python, jobs, out, workers):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(_key(json.loads(line)))
    todo = [j for j in jobs if _key(j) not in done]
    print("%d jobs to run, %d already done" % (len(todo), len(done)), flush=True)
    env, running, n = _env(), [], 0
    while todo or running:
        while todo and len(running) < workers:
            j = todo.pop(0)
            p = subprocess.Popen([python, os.path.abspath(__file__), "one",
                                  json.dumps(j)], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=env, text=True)
            running.append((p, j, time.time()))
        time.sleep(0.5)
        for item in list(running):
            p, j, t0 = item
            if p.poll() is None:
                continue
            running.remove(item)
            o, e = p.communicate()
            lines = [l for l in o.splitlines() if l.startswith("{")]
            if p.returncode != 0 or not lines:
                rec = dict(j, status="CRASH", error=(e or "")[-400:])
            else:
                rec = json.loads(lines[-1])
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            n += 1
            print("%d done: %s %s seed %s k=%s -> %s (%.0f s)"
                  % (n, j["kind"], j["problem"], j["seed"],
                     j.get("budget_factor"), rec.get("status"),
                     time.time() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("job")
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--jobs", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    c = sub.add_parser("check")
    c.add_argument("--python", required=True)
    c.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "one":
        print(json.dumps(one(json.loads(a.job)), default=float))
    elif a.cmd == "run":
        jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
        drive(a.python, jobs, a.out, a.workers)
    else:
        # The check of the wrap (PLAN.md): two F41 fits bounded by
        # generations only, with and without the wrap.
        base = [dict(kind="feyn", problem="I.8.14", index=None, split="test",
                     seed=0, gens_only=60),
                dict(kind="feyn", problem="I.30.5", index=None, split="test",
                     seed=0, gens_only=60)]
        import feynman_bench as F
        idx = {p[0]: i for i, p in enumerate(F.PROBS)}
        jobs = []
        for j in base:
            j["index"] = idx[j["problem"]]
            jobs += [dict(j), dict(j, no_wrap=True)]
        drive(a.python, jobs, a.out, 4)


if __name__ == "__main__":
    main()
