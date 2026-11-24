"""The moves of Part A of ../PLAN.md, one after the other, each checked by
the short version of A1 before the next.

For each module of layout.txt, in its order, from the first not made yet:
  1. move_group.py <module> (the plain move, checked on the syntax trees,
     and every name of gp_elite.core of 1.4.0 still there);
  2. run_a1.sh /venv15s/bin/python <dir> short (the 13 configurations and
     F41 with the defaults, on the working tree);
  3. compare_a1.py <baseline of 1.4.0> <dir> --short, kept in a1/;
The move is committed and pushed as soon as it is made (so that the
working tree stays clean), then the comparison, in a second commit; at the
first difference the script stops, for it to be looked at before the next
move. A module already moved and committed but not yet checked is checked
first.

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


def commit(paths, msg):
    sh(["git", "add"] + paths)
    r = sh(["git", "commit", "-q", "-m", msg + "\n\n" + FOOTER])
    if r.returncode:
        print("STOP: the commit failed\n" + r.stdout + r.stderr, flush=True)
        return False
    if not push():
        print("STOP: the push failed", flush=True)
        return False
    return True


def main(baseline, last=None):
    order, _m, _f = L.read_layout(os.path.join(HERE, "layout.txt"))
    modules = [m for m in order if m != "core"]
    os.makedirs(os.path.join(HERE, "a1"), exist_ok=True)
    for i, module in enumerate(modules, start=2):
        path = os.path.join(ROOT, "gp_elite", module + ".py")
        report = os.path.join(HERE, "a1", "%02d_%s.txt" % (i, module))
        if os.path.exists(report):
            continue                    # moved and checked
        doc = G.MODULES[module].replace("\n", " ")
        if not os.path.exists(path):
            r = sh(["python3", os.path.join(HERE, "move_group.py"), module])
            print(r.stdout + r.stderr, flush=True)
            if r.returncode:
                print("STOP: the move of %s failed" % module, flush=True)
                return 1
            summary = "; ".join(r.stdout.strip().splitlines())
            if not commit(["gp_elite/%s.py" % module, "gp_elite/core.py"],
                          "Split %d: gp_elite/%s.py\n\n%s\n\nMoved from core.py "
                          "without change, checked on the syntax trees (%s); core.py "
                          "imports the names back. The short A1 follows." % (
                              i, module, doc, summary)):
                return 1
        # the move is committed: the short A1 before the next
        out = "/home/user/a1_%02d_%s" % (i, module)
        subprocess.run(["rm", "-rf", out])
        r = sh(["sh", os.path.join(HERE, "run_a1.sh"), PY, out, "short"])
        if r.returncode:
            print("STOP: run_a1.sh failed for %s\n%s" % (module, r.stderr[-1000:]), flush=True)
            return 1
        r = sh([PY, os.path.join(HERE, "compare_a1.py"), baseline, out, "--short"], cwd=HERE)
        same = r.returncode == 0 and "ALL IDENTICAL" in r.stdout
        with open(report, "w") as fh:
            fh.write("Short A1 after the move of %s (step %d of the split): 1.4.0 from "
                     "PyPI (%s) against the working tree (%s).\n\n" % (module, i, baseline, out))
            fh.write(r.stdout)
        print(r.stdout[-1500:], flush=True)
        if not commit([os.path.relpath(report, ROOT)],
                      "Split %d: the short A1 %s\n\nThe 13 configurations and the 205 "
                      "fits of F41 with the defaults, against 1.4.0 from PyPI, after the "
                      "move of gp_elite/%s.py (split/a1/%02d_%s.txt)." % (
                          i, "holds, all identical" if same else "DIFFERS", module, i, module)):
            return 1
        if not same:
            print("STOP: the short A1 differs after the move of %s" % module, flush=True)
            return 1
        print("DONE %s" % module, flush=True)
        if module == last:
            break
    print("ALL MOVES DONE", flush=True)
    return 0


if __name__ == "__main__":
    args = [a for a in _ARGS if not a.startswith("--")]
    sys.exit(main(args[0], args[1] if len(args) > 1 else None))
