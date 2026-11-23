"""The map of Part A of ../PLAN.md, before any move: what gp_elite/core.py of
1.4.0 holds, which of its module-level names change at run time, which
functions and classes use them, and the module each part would go to.

It reads core.py, the other modules of the package and the tests at a commit
(the merge of 1.4.0 on main, 6dc1e35, by default) through git, parses them
(their syntax trees, without running anything) and prints the map.

A run-time name is a module-level name of core.py that is rebound inside one
of its functions (a `global` statement), or set on `core` from outside: by
the other modules of the package or by the tests (`core.NAME = ...`, also
through an index, `core.NAME[...] = ...`). The names the benches set on
`core` are listed apart: they wrap functions to observe a fit, and Part A
handles them in the benches.

    python benchmarks/results_1.5/split/map_core.py [commit] > map.txt
"""
import ast
import collections
import re
import subprocess
import sys

REV = sys.argv[1] if len(sys.argv) > 1 else "6dc1e35"

# The roles, by the sections of core.py at 6dc1e35 (first line, last line,
# module, what it holds). Read from the file's own section banners.
ROLES = [
    (1, 427, "core", "header, imports, optional dependencies of the CSV mode"),
    (428, 1748, "memory", "the fragment library, the probe set and semantic signatures, the co-graph, the sequence memory"),
    (1749, 2222, "config", "the run trace, Config, the pools of operators"),
    (2223, 2669, "tree", "hashing, Node, to_string, sympy, size, depth, complexity, constants of a tree"),
    (2670, 2896, "numeric", "the protected operators, scalar and vectorised"),
    (2897, 3576, "evaluate", "code generation, the plans of the LM Jacobian, compilation, evaluation"),
    (3577, 4004, "datasets", "the Collatz (Syracuse) features and datasets, build_dataset"),
    (4005, 4101, "evaluate", "Pearson r, the cache of predictions, safe file writing"),
    (4102, 5716, "seeds", "the seeds: motifs, power laws, binomials, elementary forms, noise-tolerant forms"),
    (5717, 6178, "fitness", "linear and robust scaling, the errors, the target scale, feature usage, fitness"),
    (6179, 6240, "operators", "random trees"),
    (6241, 6440, "simplify", "simplification"),
    (6441, 6739, "constants", "the fitting of constants: Levenberg-Marquardt and Adam"),
    (6740, 7511, "operators", "deduplication, lexicase, tournament, crossover, mutations, Pareto ranks, stigmergic trees"),
    (7512, 8184, "islands", "Island, migration, evolve_island"),
    (8185, 8646, "parallel", "the parallel islands: workers, pools, the guard of the main module"),
    (8647, 9613, "selection", "the final choice: early stop, patience, hold-out, finalists, polish, near domain, one-SE, small tables"),
    (9614, 10582, "search", "the hold-out split, the linear candidate, the reset of explorers, evolve"),
    (10583, 10877, "console", "the printed result, the decoy report, the plot, run"),
    (10878, 11423, "data", "the scalers and the loading of CSV files"),
    (11424, 11622, "config", "the populations in n dimensions, make_cfg_nd, make_cfg"),
    (11623, 12999, "console", "the benchmark of the console and the interactive menu"),
]


def git_show(path):
    return subprocess.run(["git", "show", "%s:%s" % (REV, path)], capture_output=True,
                          text=True, check=True).stdout


def git_ls(prefix):
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", REV, prefix],
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split() if p.endswith(".py")]


def role_of(line):
    for a, b, mod, _what in ROLES:
        if a <= line <= b:
            return mod
    return "?"


SET_ON_CORE = re.compile(r"\b(?:core|C|_core|_C)\.([A-Za-z_][A-Za-z0-9_]*)"
                         r"\s*(?:\[[^\]]*\])?\s*=(?!=)")


def main():
    src = git_show("gp_elite/core.py")
    lines = src.count("\n") + (0 if src.endswith("\n") else 1)
    tree = ast.parse(src)

    rebound = collections.defaultdict(set)          # name -> functions
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Global):
                    for n in sub.names:
                        rebound[n].add(node.name)

    def set_from(paths):
        out = collections.defaultdict(set)
        for p in paths:
            for m in SET_ON_CORE.finditer(git_show(p)):
                out[m.group(1)].add(p)
        return out

    by_package = set_from([p for p in git_ls("gp_elite") if p != "gp_elite/core.py"])
    by_tests = set_from(git_ls("tests"))
    by_benches = set_from([p for p in git_ls("benchmarks") if p.count("/") == 1])
    runtime = set(rebound) | set(by_package) | set(by_tests)

    print("# The map of core.py at %s (Part A of benchmarks/results_1.5/PLAN.md)" % REV)
    print()
    print("core.py: %d lines" % lines)
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print("top-level functions and classes: %d" % len(defs))
    print("run-time names: %d (rebound inside core's functions %d; set on core "
          "by the package %d, by the tests %d)" % (
              len(runtime), len(rebound), len(by_package), len(by_tests)))
    print()
    print("## Run-time names: who rebinds them, who sets them from outside")
    for n in sorted(runtime):
        print("%-28s rebound by %-40s set by %s" % (
            n, ",".join(sorted(rebound.get(n, []))) or "-",
            ",".join(sorted(by_package.get(n, set()) | by_tests.get(n, set()))) or "-"))
    print()
    print("## Names the benches (benchmarks/*.py) set on core, apart")
    for n in sorted(by_benches):
        print("%-28s %s" % (n, ",".join(sorted(by_benches[n]))))
    print()

    def used(node):
        names = {x.id for x in ast.walk(node) if isinstance(x, ast.Name)}
        return names & runtime

    def sets(node):
        out = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Global):
                out |= set(sub.names)
        return out & runtime

    print("## Functions and classes, in the order of the file")
    print("%-6s %-6s %5s  %-10s %-34s %s" % ("first", "last", "lines", "module", "name", "run-time names used (set*)"))
    per_mod = collections.defaultdict(lambda: dict(defs=0, lines=0, state=0, state_lines=0, names=set()))
    for n in defs:
        span = n.end_lineno - n.lineno + 1
        mod = role_of(n.lineno)
        u, s = used(n), sets(n)
        tag = ", ".join(sorted(x + ("*" if x in s else "") for x in u))
        print("%-6d %-6d %5d  %-10s %-34s %s" % (n.lineno, n.end_lineno, span, mod, n.name[:34], tag))
        pm = per_mod[mod]
        pm["defs"] += 1
        pm["lines"] += span
        if u:
            pm["state"] += 1
            pm["state_lines"] += span
            pm["names"] |= u
    print()
    print("## Module-level statements other than functions and classes")
    other = collections.Counter()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            other[role_of(node.lineno)] += node.end_lineno - node.lineno + 1
    for mod, n in sorted(other.items(), key=lambda t: -t[1]):
        print("%-10s %5d lines" % (mod, n))
    print()
    print("## By module")
    print("%-10s %5s %6s %12s %12s  %s" % ("module", "defs", "lines", "with state", "state lines", "run-time names used"))
    tot = collections.Counter()
    for mod in sorted(per_mod, key=lambda m: -per_mod[m]["lines"]):
        pm = per_mod[mod]
        print("%-10s %5d %6d %12d %12d  %s" % (mod, pm["defs"], pm["lines"] + other.get(mod, 0),
                                              pm["state"], pm["state_lines"],
                                              ", ".join(sorted(pm["names"]))))
        tot["defs"] += pm["defs"]
        tot["state"] += pm["state"]
        tot["state_lines"] += pm["state_lines"]
        tot["free_lines"] += pm["lines"] - pm["state_lines"]
    print()
    print("functions and classes that use run-time names: %d (%d lines); the "
          "others: %d (%d lines)" % (tot["state"], tot["state_lines"],
                                     tot["defs"] - tot["state"], tot["free_lines"]))
    print()
    print("## The roles")
    for a, b, mod, what in ROLES:
        print("%5d-%-5d %-10s %s" % (a, b, mod, what))


if __name__ == "__main__":
    main()
