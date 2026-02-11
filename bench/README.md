# Benchmarks

Benchmark suite using pyperf for stable measurements.

## Running Benchmarks

```bash
# Stable defaults are baked into the scripts.
# Tunables (env):
# - PYPERF_AFFINITY="0" (comma-separated CPU ids; empty to disable pinning)
# - PYPERF_PROCESSES=1
# - PYPERF_VALUES=40
# - PYPERF_WARMUPS=3
# - PYPERF_MIN_TIME=0.5
# You can also override via pyperf flags, e.g. --rigorous.
export UV_CACHE_DIR=/tmp/uv-cache
export PYPERF_AFFINITY=0  # optional: reduce jitter by pinning to one core

# Float formatting micro-benchmark
uv run python bench/pyperf_float.py -o bench/results/float.json

# JSON meso-benchmark  
uv run python bench/pyperf_json.py -o bench/results/json.json

# Macro-benchmark (complex structures)
uv run python bench/pyperf_macro.py -o bench/results/macro.json

# ndarray benchmark (requires numpy)
uv run python bench/pyperf_ndarray.py -o bench/results/ndarray.json
```

## Viewing Results

```bash
# Compare results
uv run python -m pyperf compare_to --table bench/results/json.json bench/results/macro.json

# Generate report
uv run python tools/report_pyperf.py bench/results/

# Generate a simple SVG chart (no extra deps)
python3 tools/plot_pyperf_svg.py bench/results/json.json -o bench/plots/json_speedup.svg
```

## Benchmark Design

- **pyperf_float.py**: Tests individual float formatting performance
- **pyperf_json.py**: Tests JSON serialization with realistic data patterns
- **pyperf_macro.py**: Tests complex nested structures simulating real workloads
- **pyperf_ndarray.py**: Tests numpy ndarray serialization (tolist baselines vs dumps_ndarray)

Results are written to `bench/results/` (gitignored except .gitkeep).
