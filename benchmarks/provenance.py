"""Provenance fields written into every benchmark record.

engine_version : the gp_elite version that was imported
commit         : the repository commit, when run from a git checkout
                 ("+modified" if gp_elite/ had uncommitted changes)
date           : local date and time of the measurement
pythonhashseed : must be "0" for reproducible runs
"""
import datetime
import os
import subprocess

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(*args):
    try:
        r = subprocess.run(["git", "-C", _ROOT] + list(args), capture_output=True,
                           text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def fields():
    import gp_elite
    d = dict(engine_version=getattr(gp_elite, "__version__", "?"),
             date=datetime.datetime.now().isoformat(timespec="seconds"),
             pythonhashseed=os.environ.get("PYTHONHASHSEED"))
    commit = _git("rev-parse", "--short", "HEAD")
    if commit:
        if _git("status", "--porcelain", "--", "gp_elite"):
            commit += "+modified"
        d["commit"] = commit
    return d
