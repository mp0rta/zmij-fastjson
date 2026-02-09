"""Tests for format_many_len function."""

import pytest
import pyzmij


def test_format_many_len_returns_int():
    """Test that format_many_len returns an int."""
    result = pyzmij.format_many_len([0.0, 1.0, 1.5])
    assert isinstance(result, int)


def test_format_many_len_empty_list():
    """Test format_many_len with empty list."""
    result = pyzmij.format_many_len([])
    assert result == 0


def test_format_many_len_single_element():
    """Test format_many_len with single element."""
    result = pyzmij.format_many_len([1.5])
    expected = len(pyzmij.format_finite(1.5))
    assert result == expected


def test_format_many_len_multiple_elements():
    """Test format_many_len with multiple elements."""
    floats = [0.0, 1.0, 1.5, 3.14159, -42.0]
    result = pyzmij.format_many_len(floats)
    expected = sum(len(pyzmij.format_finite(f)) for f in floats)
    assert result == expected


def test_format_many_len_rejects_non_float():
    """Test that format_many_len raises TypeError for non-float items."""
    with pytest.raises(TypeError):
        pyzmij.format_many_len([1.0, "not a float", 3.0])


def test_format_many_len_rejects_int():
    """Test that format_many_len raises TypeError for int items."""
    with pytest.raises(TypeError):
        pyzmij.format_many_len([1.0, 2, 3.0])


def test_format_many_len_tuple_input():
    """Test format_many_len with tuple input."""
    result = pyzmij.format_many_len((0.0, 1.0, 1.5))
    expected = sum(len(pyzmij.format_finite(f)) for f in (0.0, 1.0, 1.5))
    assert result == expected


def test_format_many_len_large_list():
    """Test format_many_len with larger list."""
    floats = [float(i) * 0.5 for i in range(100)]
    result = pyzmij.format_many_len(floats)
    expected = sum(len(pyzmij.format_finite(f)) for f in floats)
    assert result == expected


def test_bench_format_many_is_compat_alias():
    """Old API name remains as a compatibility alias."""
    floats = [0.0, 1.0, 1.5]
    assert pyzmij.bench_format_many(floats) == pyzmij.format_many_len(floats)
