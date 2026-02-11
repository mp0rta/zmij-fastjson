# bench/pyperf_ndarray.py
"""ndarray serialization benchmark: tolist+json vs tolist+fastjson vs dumps_ndarray.

Requires numpy.
"""

import json

import datasets
import fastjson
import pyperf_util


def bench_ndarray(runner, name, arr):
    """Benchmark all serialization paths for a single ndarray dataset."""
    as_list = arr.tolist()

    # Correctness: verify round-trip
    out = fastjson.dumps_ndarray(arr)
    parsed = json.loads(out)
    ref = json.loads(json.dumps(as_list, separators=(",", ":")))
    # Compare with tolerance for float32
    if arr.dtype.itemsize == 4:
        import numpy as np
        if not np.allclose(np.array(parsed, dtype=arr.dtype), arr):
            raise AssertionError(f"round-trip mismatch for {name}")
    else:
        if parsed != ref:
            raise AssertionError(f"mismatch for {name}")

    # 1) stdlib baseline: tolist + json.dumps
    runner.bench_func(
        f"tolist+json.dumps/{name}",
        lambda: json.dumps(arr.tolist(), separators=(",", ":")),
    )

    # 2) existing fast path: tolist + fastjson.dumps
    runner.bench_func(
        f"tolist+fastjson.dumps/{name}",
        lambda: fastjson.dumps(arr.tolist(), separators=(",", ":")),
    )

    # 3) new direct path: dumps_ndarray (zmij shortest)
    runner.bench_func(
        f"fastjson.dumps_ndarray/{name}",
        lambda: fastjson.dumps_ndarray(arr),
    )

    # 4) precision mode: dumps_ndarray(precision=3)
    runner.bench_func(
        f"fastjson.dumps_ndarray_p3/{name}",
        lambda: fastjson.dumps_ndarray(arr, precision=3),
    )


def main():
    runner = pyperf_util.make_runner()

    # Point cloud XYZ (typical LiDAR frame)
    f32_1e5x3 = datasets.ndarray_pointcloud(100_000, 3, "float32", seed=100)
    bench_ndarray(runner, "f32_1e5x3", f32_1e5x3)

    # Point cloud XYZI
    f32_1e5x4 = datasets.ndarray_pointcloud(100_000, 4, "float32", seed=101)
    bench_ndarray(runner, "f32_1e5x4", f32_1e5x4)

    # 1D float64 time series
    f64_1e5 = datasets.ndarray_timeseries(100_000, "float64", seed=102)
    bench_ndarray(runner, "f64_1e5", f64_1e5)

    # Large LiDAR frame (300K points)
    f32_3e5x3 = datasets.ndarray_pointcloud(300_000, 3, "float32", seed=103)
    bench_ndarray(runner, "f32_3e5x3", f32_3e5x3)


if __name__ == "__main__":
    main()
