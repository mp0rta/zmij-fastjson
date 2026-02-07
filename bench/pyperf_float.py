# bench/pyperf_float.py
import pyperf
import datasets
import json
import pyperf_util

def main():
    runner = pyperf_util.make_runner()

    # Datasets (keep them stable)
    fixed = datasets.fixed_f64_values()
    rand_bits = datasets.random_finite_f64_values(200_000, seed=1)
    json_like = datasets.uniform_real_f64(200_000, seed=2, lo=-1e6, hi=1e6)
    near0 = datasets.near_zero_real_f64(200_000, seed=3, scale=1e-3)
    ints = datasets.integral_looking_f64(200_000, seed=4)

    import pyzmij  # your extension

    # 1) C-loop benchmark (preferred)
    runner.bench_func("pyzmij.bench_format_many/fixed", lambda: pyzmij.bench_format_many(fixed))
    runner.bench_func("pyzmij.bench_format_many/rand_bits", lambda: pyzmij.bench_format_many(rand_bits))
    runner.bench_func("pyzmij.bench_format_many/json_like", lambda: pyzmij.bench_format_many(json_like))
    runner.bench_func("pyzmij.bench_format_many/near0", lambda: pyzmij.bench_format_many(near0))
    runner.bench_func("pyzmij.bench_format_many/ints", lambda: pyzmij.bench_format_many(ints))

    # 2) Baseline repr in Python loop (less precise, but useful as a quick baseline)
    def py_repr_sum(xs):
        s = 0
        for x in xs:
            s += len(repr(x))
        return s

    runner.bench_func("py.repr_sum/rand_bits", lambda: py_repr_sum(rand_bits))

if __name__ == "__main__":
    main()
