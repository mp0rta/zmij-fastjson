"""Smoke tests for pyzmij package."""

import pyzmij


def test_import():
    """Test that the module imports correctly."""
    assert hasattr(pyzmij, 'format_finite')
    assert hasattr(pyzmij, 'format_many_len')
    assert hasattr(pyzmij, 'bench_format_many')


def test_format_finite_basic():
    """Test basic format_finite functionality."""
    # Test simple values
    result = pyzmij.format_finite(1.0)
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Test negative
    result = pyzmij.format_finite(-1.0)
    assert isinstance(result, str)
    
    # Test zero
    result = pyzmij.format_finite(0.0)
    assert isinstance(result, str)


def test_format_finite_pi():
    """Test formatting pi."""
    pi = 3.141592653589793
    result = pyzmij.format_finite(pi)
    assert isinstance(result, str)
    assert '3.14' in result or result == repr(pi)


def test_format_many_len():
    """Test batch formatting."""
    floats = [1.0, 2.0, 3.0, 4.0, 5.0]
    total = pyzmij.format_many_len(floats)
    assert isinstance(total, int)
    assert total > 0
    
    # Should be sum of individual lengths
    individual_sum = sum(len(pyzmij.format_finite(f)) for f in floats)
    assert total == individual_sum


def test_format_finite_roundtrip():
    """Test that formatted values can be parsed back."""
    test_values = [0.0, 1.0, -1.0, 3.14159, 1e10, 1e-10, 1.5, -0.5]
    
    for val in test_values:
        formatted = pyzmij.format_finite(val)
        parsed = float(formatted)
        assert parsed == val or abs(parsed - val) < abs(val) * 1e-15
