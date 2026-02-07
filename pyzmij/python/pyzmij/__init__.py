"""Pyzmij - Python binding for czmij float formatting library."""

try:
    from ._pyzmij import format_finite, bench_format_many, backend

    _NATIVE = True
except ImportError as e:
    # This should not happen in production - raise error instead of warning
    raise RuntimeError(
        f"Failed to load native extension _pyzmij: {e}. "
        "Please ensure the package is properly built with: uv pip install -e ./pyzmij"
    ) from e

__all__ = ["format_finite", "bench_format_many", "backend", "_NATIVE"]
