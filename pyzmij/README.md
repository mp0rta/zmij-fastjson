# pyzmij

Python C extension for the Żmij (vitaut/zmij) float formatting library.

## API

```python
import pyzmij

# Format a single float
s = pyzmij.format_finite(3.141592653589793)

# Batch format for benchmarking
total_len = pyzmij.bench_format_many([1.0, 2.0, 3.0])
```

## Semantics

`format_finite(x)` returns the **shortest** correctly-rounded decimal representation for finite floats.
In particular, integer-valued floats may not include a trailing `.0` (e.g. `1.0` may format as `"1"`).

If you need byte-for-byte compatibility with `json.dumps()` for float sequences, see the `fastjson` package
in this repo.

## Building

```bash
uv pip install -e .
```

This package vendors its `vitaut/zmij` dependency under `third_party/` (no git submodule required).
