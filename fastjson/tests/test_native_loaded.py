"""Test that native extension is loaded."""

import fastjson


def test_native_extension_loaded():
    """Ensure the native C extension is loaded, not fallback."""
    assert fastjson._NATIVE is True, "Native extension _fastjson must be loaded"


def test_dumps_wrapper_works():
    """Verify dumps is available and works."""
    result = fastjson.dumps({"key": 1.5})
    assert isinstance(result, str)
    assert result == '{"key": 1.5}'
