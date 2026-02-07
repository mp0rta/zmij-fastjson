"""Basic tests for format_finite function."""

import pyzmij


def test_format_finite_zero():
    """Test formatting zero."""
    result = pyzmij.format_finite(0.0)
    # C extension uses %.17g, may differ from Python repr
    assert result in ["0.0", "0"]
    assert float(result) == 0.0


def test_format_finite_negative_zero():
    """Test formatting negative zero."""
    result = pyzmij.format_finite(-0.0)
    # C extension uses %.17g, may differ from Python repr
    assert result in ["-0.0", "-0"]
    assert float(result) == 0.0


def test_format_finite_one_point_five():
    """Test formatting 1.5."""
    result = pyzmij.format_finite(1.5)
    assert float(result) == 1.5


def test_format_finite_pi():
    """Test formatting pi."""
    pi = 3.141592653589793
    result = pyzmij.format_finite(pi)
    # Round-trip check
    assert float(result) == pi


def test_format_finite_integer():
    """Test formatting integer-valued float."""
    result = pyzmij.format_finite(42.0)
    assert float(result) == 42.0


def test_format_finite_negative():
    """Test formatting negative number."""
    result = pyzmij.format_finite(-123.456)
    assert float(result) == -123.456


def test_format_finite_small():
    """Test formatting small number."""
    result = pyzmij.format_finite(1e-10)
    assert float(result) == 1e-10


def test_format_finite_large():
    """Test formatting large number."""
    result = pyzmij.format_finite(1e10)
    assert float(result) == 1e10
