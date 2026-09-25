"""The real PMLB datasets used by the 0.7 studies, frozen by content hash.

Each file is downloaded once from PMLB and cached in benchmarks/_pmlb_cache/.
It is then checked against the SHA-256 of its decompressed content as it was
when the published numbers were measured: if PMLB ever changes a file, the
scripts stop instead of silently measuring something else.

The fri_c* datasets of PMLB are synthetic (Friedman functions) and are
deliberately not used.
"""
import gzip
import hashlib
import io
import os
import urllib.request

import numpy as np

URL = "https://media.githubusercontent.com/media/EpistasisLab/pmlb/master/datasets/{n}/{n}.tsv.gz"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pmlb_cache")

# decompressed content, SHA-256 (measured 2026-09-24)
SHA256 = {
    "210_cloud":              "d71692bf6d053f521d2e76f7fe4453e278e3ce964355384b45364e2655cef5ab",
    "228_elusage":            "50c86186dbcd45b5d9bfb86405670d959338398866ce4c79b9e6aac9e0d5fac3",
    "547_no2":                "a462c62f0bab1ec537dd9cc43fa3f31274cb21977d85bca70da885235652f47b",
    "561_cpu":                "d4472ba272f2243bbf0f9745c8fa15e377f6d7c853664820778a110fc5f18f50",
    "690_visualizing_galaxy": "cbb9b13559c250ff6d1768a8750913b1bc60b896c93b8c5567f3fc2f2fef4e16",
    "712_chscase_geyser1":    "b2908f4af12124db401aa4b6a289b6bae709b3d576e9d0cb8677c4e6e7fdaed5",
    "nikuradse_1":            "50eb83a88c4bb77645aa682f2494ad059cd0c84c827e1f6f7636fa15f8a4dbf1",
}
DATASETS = [n for n in SHA256 if n != "nikuradse_1"]   # the six of the 0.7 studies


def load_frame(name):
    """The dataset as a pandas DataFrame, after checking the content hash."""
    if name not in SHA256:
        raise KeyError("%s is not one of the frozen datasets: %s" % (name, list(SHA256)))
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".tsv.gz")
    if not os.path.exists(path):
        urllib.request.urlretrieve(URL.format(n=name), path)
    with gzip.open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256[name]:
        raise RuntimeError(
            "%s: content changed since the published measurements "
            "(sha256 %s, expected %s). Delete %s to re-download, or pin the "
            "old file." % (name, digest, SHA256[name], path))
    import pandas as pd
    return pd.read_csv(io.BytesIO(raw), sep="\t")


def load(name):
    """(X, y) as float arrays, after checking the content hash."""
    d = load_frame(name)
    y = d["target"].to_numpy(dtype=float)
    X = d.drop(columns=["target"]).to_numpy(dtype=float)
    return X, y
