"""The moves of Part A of ../PLAN.md, one after the other, each checked by
the short version of A1 before the next.

For each module of layout.txt, in its order, from the first not made yet:
  1. move_group.py <module> (the plain move, checked on the syntax trees,
     and every name of gp_elite.core of 1.4.0 still there);
  2. run_a1.sh /venv15s/bin/python <dir> short (the 13 configurations and
     F41 with the defaults, on the working tree);
  3. compare_a1.py <baseline of 1.4.0> <dir> --short, kept in a1/;
  4. if all is identical: one commit for the move and its comparison, and a
     push; otherwise the script stops, the move left uncommitted, for the
     difference to be looked at.

    python run_moves.py <baseline dir> [<last module>]
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
PY = "/venv15s/bin/python"
BRANCH = "claude/peaceful-knuth-4q7m4p"
FOOTER = ("Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
          "Claude-Session: https://claude.ai/code/session_01EWHDf9m7w3MoDeyD7ewSDZ\n")

sys.path.insert(0, HERE)
_ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]
import layout_core as L  # noqa: E402
import move_group as G  # noqa: E402


def sh(cmd, **kw):
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=kw.pop("cwd", ROOT), text=True, capture_output=True, **kw)


def push():
    for i in range(4):
        r = sh(["git", "push", "-q", "-u", "origin", BRANCH], timeout=120)
        if r.returncode == 0:
            return True
        print(r.stderr[-500:], flush=True)
        subprocess.run(["sleep", str(2 ** (i + 1))])
    return False


def main(baseline, last=None):
    order, _m, _f = L.read_layout(os.path.join(HERE, "layout.txt"))
    modules = [m for m in order if m != "core"]
    os.makedirs(os.path.join(HERE, "a1"), exist_ok=True)
    for i, module in enumerate(modules, start=2):
        path = os.path.join(ROOT, "gp_elite", module + ".py")
        if os.path.exists(path):
            continue
        r = sh(["python3", os.path.join(HERE, "move_group.py"), module])
        print(r.stdout + r.stderr, flush=True)
        if r.returncode:
            print("STOP: the move of %s failed" % module, flush=True)
            return 1
        summary = r.stdout.strip().splitlines()
        out = "/home/user/a1_%02d_%s" % (i, module)
        subprocess.run(["rm", "-rf", out])
        r = sh(["sh", os.path.join(HERE, "run_a1.sh"), PY, out, "short"])
        if r.returncode:
            print("STOP: run_a1.sh failed for %s\n%s" % (module, r.stderr[-1000:]), flush=True)
            return 1
        r = sh([PY, os.path.join(HERE, "compare_a1.py"), baseline, out, "--short"], cwd=HERE)
        report = os.path.join(HERE, "a1", "%02d_%s.txt" % (i, module))
        with open(report, "w") as fh:
            fh.write("Short A1 after the move of %s (step %d of the split): 1.4.0 from "
                     "PyPI (%s) against the working tree (%s).\n\n" % (module, i, baseline, out))
            fh.write(r.stdout)
        print(r.stdout[-1500:], flush=True)
        if r.returncode or "ALL IDENTICAL" not in r.stdout:
            print("STOP: the short A1 differs after the move of %s" % module, flush=True)
            return 1
        doc = G.MODULES[module].replace("\n", " ")
        msg = ("Split %d: gp_elite/%s.py\n\n%s\n\nMoved from core.py without change (%s); "
               "core.py imports the names back. The short A1 against 1.4.0 (the 13 "
               "configurations and F41 with the defaults): all identical "
               "(split/a1/%02d_%s.txt).\n\n%s" % (
                   i, module, doc, "; ".join(summary), i, module, FOOTER))
        r = sh(["git", "add", "gp_elite/%s.py" % module, "gp_elite/core.py",
                os.path.relpath(report, ROOT)])
        r = sh(["git", "commit", "-q", "-m", msg])
        if r.returncode:
            print("STOP: the commit failed\n" + r.stdout + r.stderr, flush=True)
            return 1
        if not push():
            print("STOP: the push failed", flush=True)
            return 1
        print("DONE %s" % module, flush=True)
        if module == last:
            break
    print("ALL MOVES DONE", flush=True)
    return 0


if __name__ == "__main__":
    args = [a for a in _ARGS if not a.startswith("--")]
    sys.exit(main(args[0], args[1] if len(args) > 1 else None))
