# zmij-fastjson

Fast, stdlib-compatible JSON serialization for large float-heavy `list`/`tuple` inputs.

## Repository Structure

```
zmij-fastjson/
├── fastjson/       # High-level fast JSON serializer
├── bench/          # Benchmarks (pyperf-based)
└── tools/          # Utility scripts
```

## What’s Here

- **`fastjson`**: Drop-in replacement for the standard library `json` module, with native fast paths for large
  `list[float]` / `tuple[float]` (and some float-heavy sequences).
  - Contract: `fastjson.dumps()` is byte-for-byte identical to `json.dumps()` for all inputs and options,
    including matching exception type and message.
  - Performance: when the input and options are supported by the native fast paths (for example float sequences with
    stdlib-default or compact separators), `fastjson` bypasses stdlib and formats directly in C.
  - `separators=` may be any length-2 string sequence (tuple/list). Unsupported separators fall back to stdlib.

If your workload is “big numeric arrays -> JSON”, this repo is designed to help.

## Development Setup (uv)

### Setup

```bash
# Create virtual environment
uv venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install package in editable mode
uv pip install -e ./fastjson[dev]
```

### Testing

```bash
export UV_CACHE_DIR=/tmp/uv-cache  # optional (useful on locked-down environments)
uv run -m pytest -q fastjson/tests/
```

### Benchmarking

```bash
# JSON serialization benchmark (fastjson vs stdlib json)
uv run python bench/pyperf_json.py -o bench/results/json.json

# Macro benchmark (complex nested structures)
uv run python bench/pyperf_macro.py -o bench/results/macro.json

# Optional float formatting micro-benchmark (requires separate pyzmij install)
uv run python bench/pyperf_float.py -o bench/results/float.json

# View results
uv run python -m pyperf show bench/results/json.json
```

#### Performance expectations

`fastjson` is optimized for large `list/tuple` sequences that are mostly numeric (especially `float`),
optionally with occasional `null` (`None`). On such inputs it can be ~20-30x faster than stdlib `json`
when producing compact JSON (`separators=(',', ':')`) in local benchmarks.

On generic JSON (top-level `dict`, deeply nested mixed types), `fastjson` usually falls back to stdlib
and performance is expected to be similar.

![Benchmark speedup chart](bench/plots/json_speedup.svg)

Bench labels in the chart:
- **`1e4`**: random finite `float` list with **10,000** elements (`datasets.random_finite_f64_values(10_000, ...)`)
- **`1e5`**: random finite `float` list with **100,000** elements (`datasets.random_finite_f64_values(100_000, ...)`)
- **`mixed_1e5_nulls`**: mostly floats (100,000 total), with `None` -> `null` inserted periodically (currently every 20 items)
  (`datasets.mostly_floats_with_nulls(100_000, null_every=20, ...)`)

## Implementation

- **fastjson**: high-performance JSON serializer
  - Fast path: `list[float]` / `tuple[float]` using C directly
  - Slow path: fallback to stdlib `json.dumps()` for other types
  - NaN/Inf handling with `allow_nan` parameter

- **Benchmarks**: pyperf-based comparison suite

## Roadmap

- Expand edge-case coverage (subnormals, max/min finite values).
- Add fuzz/property-based tests for robustness.
