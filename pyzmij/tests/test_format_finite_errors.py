"""Error handling tests for format_finite function."""

import pytest
import pyzmij


def test_format_finite_rejects_inf():
    """Test that format_finite raises ValueError for positive infinity."""
    with pytest.raises(ValueError, match="finite"):
        pyzmij.format_finite(float("inf"))


def test_format_finite_rejects_negative_inf():
    """Test that format_finite raises ValueError for negative infinity."""
    with pytest.raises(ValueError, match="finite"):
        pyzmij.format_finite(float("-inf"))


def test_format_finite_rejects_nan():
    """Test that format_finite raises ValueError for NaN."""
    with pytest.raises(ValueError, match="finite"):
        pyzmij.format_finite(float("nan"))


def test_format_finite_rejects_string():
    """Test that format_finite raises TypeError for string."""
    with pytest.raises(TypeError):
        pyzmij.format_finite("1.0")


def test_format_finite_rejects_int():
    """Test that format_finite raises TypeError for int."""
    with pytest.raises(TypeError):
        pyzmij.format_finite(1)


def test_format_finite_rejects_none():
    """Test that format_finite raises TypeError for None."""
    with pytest.raises(TypeError):
        pyzmij.format_finite(None)


def test_format_finite_rejects_list():
    """Test that format_finite raises TypeError for list."""
    with pytest.raises(TypeError):
        pyzmij.format_finite([1.0, 2.0])
