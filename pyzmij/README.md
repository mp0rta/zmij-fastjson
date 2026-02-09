# pyzmij

Python C extension for the Żmij (vitaut/zmij) float formatting library.

## API

```python
import pyzmij

# Format a single float
s = pyzmij.format_finite(3.141592653589793)

# General formatter (optional JSON compatibility)
s2 = pyzmij.format(1.0, json_compatible=True)  # "1.0"

# Batch formatter (returns list[str])
items = pyzmij.format_many([1.0, -0.0, 3.14], json_compatible=True)

# Batch format and get total output length (sequence input)
total_len = pyzmij.format_many_len([1.0, 2.0, 3.0])
```

## Semantics

`format_finite(x)` returns the **shortest** correctly-rounded decimal representation for finite floats.
In particular, integer-valued floats may not include a trailing `.0` (e.g. `1.0` may format as `"1"`).

Input contract:
- `format(x, *, json_compatible=False, allow_non_finite=False)` accepts a Python `float`.
- `format_finite(x)` accepts a Python `float` only (rejects `int`, `str`, `None`, NaN, and Inf).
- `format_many(seq, *, json_compatible=False, allow_non_finite=False)` returns `list[str]`.
- `format_many_len(seq)` accepts a sequence (for example `list` or `tuple`) whose items are all `float`.
- `format_many_len` returns only total formatted length (`int`).
- `bench_format_many(seq)` remains available as a compatibility alias.

`json_compatible` means "match JSON float text conventions":
- finite integer-looking values keep a decimal point (`1.0` -> `"1.0"`)
- negative zero keeps its sign (`-0.0` -> `"-0.0"`)
- if `allow_non_finite=True`, non-finite values use JSON tokens (`NaN`, `Infinity`, `-Infinity`)

If you need byte-for-byte compatibility with `json.dumps()` for float sequences, see the `fastjson` package
in this repo.

## Building

```bash
uv pip install -e .
```

This package vendors its `vitaut/zmij` dependency under `third_party/` (no git submodule required).

For PyPI release steps, see `pyzmij/RELEASING.md`.
