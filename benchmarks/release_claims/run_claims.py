"""M3 of benchmarks/results_0.9/PLAN_RELEASE_0.9.md: every public figure
measured again on an installed package, with the commands of
benchmarks/results_0.8/README.md, in two queues side by side (two
measurements at a time), PYTHONHASHSEED=0, one process per command.

  python benchmarks/release_claims/run_claims.py <python> <workdir> <outdir>

<python>  the interpreter of a fresh environment where the package to measure
          is installed, with sympy, gplearn and matplotlib for the scripts
          that use them.
<workdir> a copy of benchmarks/, examples/ and README.md WITHOUT the gp_elite
          package beside them: several scripts put the repository root first
          on sys.path when it holds gp_elite/, and would measure the sources
          instead of the package.
<outdir>  where the records go; every command runs there.

The islands run in sequence under the default parallel=None, as on the 2-core
machine of the 0.8 figures (sitecustomize.py in this folder); an explicit
parallel=True still runs them in parallel. The import time is measured
without that switch.
"""
import os
import subprocess
import sys
import threading
import time

PY, WORK, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(WORK, "benchmarks")
E = os.path.join(WORK, "examples")
ENV = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1",
           PYTHONPATH=HERE, GP_ELITE_AUTO_SEQUENTIAL="1", MPLBACKEND="Agg")
LOG_LOCK = threading.Lock()


def readme_block(start_marker, extra=""):
    """The first ```python block of README.md after `start_marker`."""
    text = open(os.path.join(WORK, "README.md"), encoding="utf-8").read()
    i = text.index(start_marker)
    i = text.index("```python\n", i) + len("```python\n")
    return text[i:text.index("```", i)] + extra


def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def hooke_csv():
    """The Hooke data of test_constante_mystere.py (150 points, seed 0), as a
    CSV for the console."""
    import numpy as np
    rng = np.random.RandomState(0)
    x = rng.uniform(0.01, 0.10, 150)
    rows = "\n".join("%.6f,%.6f" % (a, 250.0 * a) for a in x)
    return write("hooke.csv", "elongation,force\n" + rows + "\n")


def jobs():
    q1 = [
        ("feynman_bench 0 15", [PY, f"{B}/feynman_bench.py", "0", "15"], "feynman15.txt"),
        ("feynman_bench 12 15 none", [PY, f"{B}/feynman_bench.py", "12", "15",
                                      "--normalize", "none"], "feynman_angles_normalize_none.txt"),
        ("duel 0 15", [PY, f"{B}/duel.py", "0", "15"], "duel_gplearn.txt"),
        ("constante", [PY, f"{B}/test_constante_mystere.py"], "mystery_constant.txt"),
        ("robust", [PY, f"{E}/robust_regression.py"], "robust_example.txt"),
        ("kepler demo", [PY, f"{E}/kepler_demo.py"], "kepler_demo.txt"),
        ("battery", [PY, f"{E}/battery_soh.py"], "battery_example.txt"),
        ("readme kepler", [PY, write("readme_kepler.py", readme_block(
            "![GP_ELITE rediscovers", "print(result.formula_exact)\n"))], "readme_kepler.txt"),
        ("usage", [PY, write("usage_example.py", readme_block(
            "### Programmatically"))], "usage_example.txt"),
        ("console", [PY, "-c", "from gp_elite.cli import main; main()"],
         "console_hooke.txt", "6\n%s\n\n\n\n\nm\nN\ny\n\n\n" % hooke_csv()),
        ("fuzz", [PY, f"{B}/formula_fuzz.py"], "formula_fuzz.txt"),
        ("pools", [PY, f"{B}/pools_check.py"], "pools_check.txt"),
    ]
    for s in ("kepler30", "hooke", "coulomb", "torque", "optionB", "tp", "nikuradse"):
        q1.append(("snippet " + s, [PY, f"{B}/notebook_claims.py", s],
                   "notebook_snippet_%s.txt" % s))
    q1 += [
        ("robustness", [PY, f"{B}/robustness_check.py", "--out",
                        f"{OUT}/robustness_check.jsonl"], "robustness_check_run.txt"),
        ("robustness summary", [PY, f"{B}/robustness_check.py", "--summary",
                                f"{OUT}/robustness_check.jsonl"], "robustness_check.txt"),
        ("scale", [PY, f"{B}/scale_check.py"], "scale_check_release.txt"),
        ("small data", [PY, f"{B}/small_data_check.py", "--arm", "F", "--out",
                        f"{OUT}/small_data_release.jsonl"], "small_data_run.txt"),
        ("small data summary", [PY, f"{B}/small_data_check.py", "--summary",
                                f"{OUT}/small_data_release.jsonl"], "small_data_release.txt"),
        ("bad inputs", [PY, f"{B}/bad_input_check.py"], "bad_inputs.txt"),
        ("nikuradse full", [PY, f"{B}/real_nikuradse.py"], "nikuradse_full.txt"),
        ("kepler plot", [PY, f"{E}/kepler_plot.py"], "kepler_plot.txt"),
        ("import time", None, "import_time.txt"),
    ]
    q2 = [
        ("ab_ood", [PY, f"{B}/ab_ood.py", "--out", f"{OUT}/units_ab_ood.jsonl"],
         "units_ab_ood.txt"),
        ("units", [PY, f"{B}/feynman_units.py", "--out", f"{OUT}/feynman15_units.jsonl"],
         "feynman15_units.txt"),
        ("scaling", [PY, f"{B}/feynman_scaling.py", "--out", f"{OUT}/scaling.jsonl"],
         "scaling.txt"),
        ("time_limit", [PY, f"{B}/time_limit_check.py"], "time_limit_check.txt"),
    ]
    return q1, q2


def import_time(path):
    code = ('import time; t = time.perf_counter(); import gp_elite; '
            'print("%.3f" % (time.perf_counter() - t))')
    env = dict(os.environ, PYTHONHASHSEED="0")
    env.pop("PYTHONPATH", None)
    vals = [subprocess.run([PY, "-c", code], capture_output=True, text=True,
                           env=env, cwd=OUT).stdout.strip() for _ in range(7)]
    with open(path, "w") as fh:
        fh.write("# import time of gp_elite, 7 fresh processes, seconds "
                 "(python -c '%s')\n%s\n" % (code, " ".join(vals)))


def queue(name, items):
    for item in items:
        label, cmd, out = item[:3]
        stdin = item[3] if len(item) > 3 else None
        with LOG_LOCK, open(os.path.join(OUT, "claims_queues.txt"), "a") as fh:
            fh.write("%s == %s %s\n" % (name, label, time.strftime("%Y-%m-%d %H:%M:%S")))
        path = os.path.join(OUT, out)
        if cmd is None:
            import_time(path)
            continue
        with open(path, "w", encoding="utf-8") as fh:
            p = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True,
                               input=stdin, env=ENV, cwd=OUT)
        if p.returncode != 0:
            with LOG_LOCK, open(os.path.join(OUT, "claims_queues.txt"), "a") as fh:
                fh.write("%s    exit code %d\n" % (name, p.returncode))
    with LOG_LOCK, open(os.path.join(OUT, "claims_queues.txt"), "a") as fh:
        fh.write("%s == done %s\n" % (name, time.strftime("%Y-%m-%d %H:%M:%S")))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    q1, q2 = jobs()
    threads = [threading.Thread(target=queue, args=("queue1", q1)),
               threading.Thread(target=queue, args=("queue2", q2))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
