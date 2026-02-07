# bench/pyperf_json.py
"""JSON serialization benchmark comparing fastjson vs stdlib json.

Fair comparison: both use compact format (separators=(',', ':')) and allow_nan=True.
"""

import pyperf
import datasets
import json
import fastjson
import pyperf_util


def bench_pair(runner: pyperf.Runner, name: str, values):
    """Benchmark a pair of json vs fastjson for the same dataset."""
    # Align comparison conditions: compact JSON, allow NaN/Inf
    ref = json.dumps(values, separators=(",", ":"), allow_nan=True)
    out = fastjson.dumps(values, separators=(",", ":"), allow_nan=True)

    # Correctness check (run once) - note: vitaut/zmij produces shortest representation
    # which may differ from Python json for integer-valued floats (e.g., "1" vs "1.0")
    # Both are valid JSON representing the same value
    if json.loads(out) != values:
        raise AssertionError(f"mismatch for {name}: parsed values differ from input")
    if out != ref:
        import sys

        print(
            f"Note: {name} - output format differs (both valid JSON): "
            f"fastjson[:40]={out[:40]!r} json[:40]={ref[:40]!r}",
            file=sys.stderr,
        )

    # Benchmark stdlib json
    runner.bench_func(
        f"json.dumps/{name}",
        lambda: json.dumps(values, separators=(",", ":"), allow_nan=True),
    )

    # Benchmark fastjson
    runner.bench_func(
        f"fastjson.dumps/{name}",
        lambda: fastjson.dumps(values, separators=(",", ":"), allow_nan=True),
    )


def main():
    runner = pyperf_util.make_runner()

    # Generate datasets: 10k and 100k finite float values
    values_1e4 = datasets.random_finite_f64_values(10_000, seed=10)
    values_1e5 = datasets.random_finite_f64_values(100_000, seed=11)
    values_mixed_1e5 = datasets.mostly_floats_with_nulls(100_000, seed=12, null_every=20)

    bench_pair(runner, "1e4", values_1e4)
    bench_pair(runner, "1e5", values_1e5)
    bench_pair(runner, "mixed_1e5_nulls", values_mixed_1e5)


if __name__ == "__main__":
    main()
