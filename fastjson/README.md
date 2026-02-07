# fastjson

Python package (CPython extension) JSON serializer with a fast path for `list[float]` / `tuple[float]`.

## API

```python
import fastjson

# Fast path (exact float sequences)
json_str = fastjson.dumps([1.0, 2.5, 3.0])
```

## Compatibility (drop-in)

`fastjson` aims to be a **drop-in replacement** for Python's standard library `json` module.

- `fastjson.dumps()` is intended to be **byte-for-byte identical** to `json.dumps()` for all inputs and options.
- This includes matching exception type and message.
- For any input/options combination not supported by the native fast paths, `fastjson` falls back to stdlib `json.dumps()`.

Notes:
- The float-only fast path supports stdlib-default and compact separators. Unsupported `separators` values fall back to stdlib.
- The hybrid path (mixed lists) honors `separators=`.
- `ensure_ascii=` is ignored on the fast path (it only outputs ASCII for numbers anyway).

## Install (from source)

```bash
uv pip install -e .
```

## Features

- Fast float formatting using vitaut/zmij
- Fast path for exact float sequences
- Slow path delegates to stdlib `json.dumps()`

## When It’s Fast

`fastjson` is meant for “big numeric arrays → JSON”, e.g. time series or embedding-like vectors:

- `list[float]` / `tuple[float]` (fast path)
- Mixed `list/tuple` that is *mostly* floats, with occasional `None`/`bool`/`int` (hybrid path)

On these workloads, `fastjson` can be ~20–30x faster than stdlib `json.dumps()` when using compact
separators (`separators=(',', ':')`).

It is *not* a general-purpose replacement for `json` on arbitrary nested objects; for top-level `dict`
and deeply mixed structures it will typically fall back to stdlib and be about the same speed.

![Benchmark speedup chart](../bench/plots/json_speedup.svg)

Chart labels:
- `1e4`: random finite float list, 10,000 elements
- `1e5`: random finite float list, 100,000 elements
- `mixed_1e5_nulls`: mostly floats, 100,000 total, with periodic `None` → `null` values (every 20 items)
