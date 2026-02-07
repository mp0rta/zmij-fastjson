"""Test that native extension is loaded."""

import pyzmij


def test_native_extension_loaded():
    """Ensure the native C extension is loaded, not fallback."""
    assert pyzmij._NATIVE is True, "Native extension _pyzmij must be loaded"


def test_format_finite_is_native():
    """Verify format_finite is from the C extension."""
    # Check that the function is callable and works
    result = pyzmij.format_finite(1.5)
    assert isinstance(result, str)
    assert result == "1.5"
