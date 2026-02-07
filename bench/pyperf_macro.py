# bench/pyperf_macro.py
import pyperf
import datasets
import json
import pyperf_util

def main():
    runner = pyperf_util.make_runner()

    obj = datasets.macro_sensor_frame(n_series=8, n_points=5000, seed=123)

    import fastjson
    runner.bench_func("json.dumps/macro", lambda: json.dumps(obj))
    runner.bench_func("fastjson.dumps/macro", lambda: fastjson.dumps(obj))

if __name__ == "__main__":
    main()
