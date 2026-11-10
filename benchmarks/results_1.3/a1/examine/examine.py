"""The examination of A1 (PLAN.md in this folder).

  python examine.py e1jobs ../campaign/Dtrig_B.jsonl e1_jobs.jsonl
      (then: diag.py run --python /venv13a/bin/python --jobs e1_jobs.jsonl ...)
  python examine.py e2a --python /venv12p/bin/python --out e2a_A.jsonl
  python examine.py e2a --python /venv13a/bin/python --out e2a_B.jsonl
  python examine.py e2b ../campaign/TPsnell_B.jsonl
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, BENCH)


def e1jobs(campaign_b, out):
    rs = [json.loads(l) for l in open(campaign_b) if l.strip()]
    js = [dict(kind=r["kind"], problem=r["problem"], index=r["index"],
               split=r["split"], seed=r["seed"], budget_factor=1,
               study_status=r["status"], study_generations=r["generations"])
          for r in rs if r["kind"] == "feyn" and r["problem"] in ("I.26.2", "I.30.5")]
    js.sort(key=lambda j: (j["problem"], j["seed"]))
    with open(out, "w") as fh:
        for j in js:
            fh.write(json.dumps(j) + "\n")
    print("%d jobs written to %s" % (len(js), out))


def e2a(python, out):
    jobs = [dict(exp="snell", n=n, noise=0.0, draw=d, arm="plain")
            for n in (10, 20) for d in range(5)]
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    tp = os.path.join(BENCH, "tp_diagnostic.py")

    def one(j):
        p = subprocess.run([python, "-I", tp, "worker", json.dumps(j)],
                           capture_output=True, text=True, env=env, cwd="/")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        if p.returncode != 0 or not lines:
            return dict(j, crash=True, stderr=p.stderr[-400:])
        return json.loads(lines[-1])
    with ThreadPoolExecutor(4) as ex, open(out, "w") as fh:
        for rec in ex.map(one, jobs):
            fh.write(json.dumps(rec) + "\n")
            print("%s %d points seed %d: law %s, err_law %.3g, %s" % (
                os.path.basename(python.split("/bin")[0]), rec["n"], rec["draw"],
                rec.get("law"), rec.get("err_law", float("nan")),
                (rec.get("expr") or "")[:90]), flush=True)


def e2b(campaign_tp_b):
    import tp_diagnostic as TP
    rs = [json.loads(l) for l in open(campaign_tp_b) if l.strip()]
    print("| arm | points | noise | draw | noise, 1 - R² on the training rows |"
          " err_law of the formula of B | ratio |")
    print("|---|---|---|---|---|---|---|")
    ratios = []
    for r in sorted(rs, key=lambda r: (r["arm"], r["n"], r["noise"], r["draw"])):
        X, y, yc, Xg, yg = TP.data("snell", r["n"], r["noise"], r["draw"])
        noise = float(np.mean((y - yc) ** 2) / np.var(y))
        ratio = r["err_law"] / noise if noise > 0 else float("inf")
        ratios.append(ratio)
        print("| %s | %d | %d %% | %d | %.2e | %.2e | %.3f |" % (
            r["arm"], r["n"], round(100 * r["noise"]), r["draw"], noise,
            r["err_law"], ratio))
    ratios = np.array(ratios)
    print("\nerr_law / noise: median %.3f, at most %.3f; below 1 in %d of %d fits"
          % (np.median(ratios), ratios.max(), int(np.sum(ratios < 1)), len(ratios)))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "e1jobs":
        e1jobs(sys.argv[2], sys.argv[3])
    elif cmd == "e2a":
        a = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        e2a(a["--python"], a["--out"])
    elif cmd == "e2b":
        e2b(sys.argv[2])
