"""fastjson - drop-in replacement for Python's stdlib json (with native fast paths)."""

from __future__ import annotations

from typing import Any

import json as _json

try:
    from ._fastjson import dumps as _native_dumps
    from ._fastjson import dumps_ndarray as _native_dumps_ndarray

    _NATIVE = True
except ImportError as e:
    raise RuntimeError(
        f"Failed to load native extension _fastjson: {e}. "
        "Please ensure the package is properly built with: uv pip install -e ./fastjson"
    ) from e


def _is_supported_separators(separators: Any) -> bool:
    if separators is None:
        return True
    try:
        item_sep, key_sep = separators  # tuple/list/etc
    except Exception:
        return False
    return (item_sep, key_sep) in {(",", ":"), (", ", ": ")}


def _can_use_native_dumps(
    *,
    skipkeys: bool,
    ensure_ascii: bool,
    check_circular: bool,
    allow_nan: bool,
    cls: Any,
    indent: Any,
    separators: Any,
    default: Any,
    sort_keys: bool,
    kw: dict[str, Any],
) -> bool:
    # Conservatively use the native path only when all non-fast-path options are default,
    # so output remains byte-for-byte identical to json.dumps().
    if skipkeys is not False:
        return False
    if check_circular is not True:
        return False
    # For strict drop-in behavior, defer allow_nan=False to stdlib to preserve exact exception messages,
    # which can vary across CPython versions.
    if allow_nan is not True:
        return False
    if cls is not None:
        return False
    if indent is not None:
        return False
    if default is not None:
        return False
    if sort_keys is not False:
        return False
    if kw:
        return False
    return _is_supported_separators(separators)


def dumps(
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: Any = None,
    indent: Any = None,
    separators: Any = None,
    default: Any = None,
    sort_keys: bool = False,
    **kw: Any,
) -> str:
    """Drop-in replacement for json.dumps, with optional native fast paths."""

    if _can_use_native_dumps(
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        cls=cls,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        kw=kw,
    ):
        return _native_dumps(obj, ensure_ascii=ensure_ascii, separators=separators, allow_nan=allow_nan)

    return _json.dumps(
        obj,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        cls=cls,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kw,
    )


def dump(obj: Any, fp: Any, *args: Any, **kwargs: Any) -> None:
    return _json.dump(obj, fp, *args, **kwargs)


def loads(s: Any, *args: Any, **kwargs: Any) -> Any:
    return _json.loads(s, *args, **kwargs)


def load(fp: Any, *args: Any, **kwargs: Any) -> Any:
    return _json.load(fp, *args, **kwargs)


def dumps_ndarray(
    array: Any,
    *,
    nan: str = "raise",
    precision: int | None = None,
) -> str:
    """Serialize a 1D or 2D C-contiguous float array to a JSON string.

    Parameters
    ----------
    array : numpy.ndarray or buffer-protocol object
        Must be C-contiguous with dtype float32 or float64.
    nan : str
        How to handle NaN/Inf: 'raise' (default), 'null', or 'skip'.
    precision : int or None
        If None, use shortest representation. If int 0-20, fixed decimal places.

    Returns
    -------
    str
        JSON string like "[1.0,2.0,3.0]" (1D) or "[[1.0,2.0],[3.0,4.0]]" (2D).
    """
    return _native_dumps_ndarray(array, nan=nan, precision=precision)


JSONEncoder = _json.JSONEncoder
JSONDecoder = _json.JSONDecoder
JSONDecodeError = _json.JSONDecodeError


__all__ = [
    "dump",
    "dumps",
    "dumps_ndarray",
    "load",
    "loads",
    "JSONDecodeError",
    "JSONDecoder",
    "JSONEncoder",
    "_NATIVE",
]
