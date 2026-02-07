"""Tests for bench_format_many function."""

import pytest
import pyzmij


def test_bench_format_many_returns_int():
    """Test that bench_format_many returns an int."""
    result = pyzmij.bench_format_many([0.0, 1.0, 1.5])
    assert isinstance(result, int)


def test_bench_format_many_empty_list():
    """Test bench_format_many with empty list."""
    result = pyzmij.bench_format_many([])
    assert result == 0


def test_bench_format_many_single_element():
    """Test bench_format_many with single element."""
    result = pyzmij.bench_format_many([1.5])
    expected = len(pyzmij.format_finite(1.5))
    assert result == expected


def test_bench_format_many_multiple_elements():
    """Test bench_format_many with multiple elements."""
    floats = [0.0, 1.0, 1.5, 3.14159, -42.0]
    result = pyzmij.bench_format_many(floats)
    expected = sum(len(pyzmij.format_finite(f)) for f in floats)
    assert result == expected


def test_bench_format_many_rejects_non_float():
    """Test that bench_format_many raises TypeError for non-float items."""
    with pytest.raises(TypeError):
        pyzmij.bench_format_many([1.0, "not a float", 3.0])


def test_bench_format_many_rejects_int():
    """Test that bench_format_many raises TypeError for int items."""
    with pytest.raises(TypeError):
        pyzmij.bench_format_many([1.0, 2, 3.0])


def test_bench_format_many_tuple_input():
    """Test bench_format_many with tuple input."""
    result = pyzmij.bench_format_many((0.0, 1.0, 1.5))
    expected = sum(len(pyzmij.format_finite(f)) for f in (0.0, 1.0, 1.5))
    assert result == expected


def test_bench_format_many_large_list():
    """Test bench_format_many with larger list."""
    floats = [float(i) * 0.5 for i in range(100)]
    result = pyzmij.bench_format_many(floats)
    expected = sum(len(pyzmij.format_finite(f)) for f in floats)
    assert result == expected
