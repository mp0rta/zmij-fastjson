import os

import pytest

if os.environ.get("PYZMIJ_RUN_REPR_COMPAT") != "1":
    pytest.skip(
        "repr() compatibility test is disabled by default (set PYZMIJ_RUN_REPR_COMPAT=1 to enable)",
        allow_module_level=True,
    )

# bench/datasets.py is a helper module used by benchmarks; add it to sys.path when
# running from the repo root so this test can be enabled without extra deps.
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[2]
bench_dir = repo_root / "bench"
sys.path.insert(0, str(bench_dir))

import datasets  # noqa: E402
import pyzmij  # noqa: E402
import math  # noqa: E402

def test_repr_compat_random_finite():
    n = int(os.environ.get("PYZMIJ_REPR_COMPAT_N", "50000"))
    xs = datasets.random_finite_f64_values(n, seed=0)
    for x in xs:
        assert pyzmij.format_finite(x) == repr(x)

def test_repr_compat_edges():
    for x in datasets.edge_f64_values():
        assert pyzmij.format_finite(x) == repr(x)
