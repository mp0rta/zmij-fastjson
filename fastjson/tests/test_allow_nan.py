"""Test allow_nan parameter for NaN/Inf handling."""

import json
import pytest
import fastjson
import math


def test_allow_nan_true_with_nan():
    """Test allow_nan=True with NaN value."""
    data = [1.0, float("nan"), 2.0]
    result = fastjson.dumps(data, allow_nan=True)
    expected = json.dumps(data, allow_nan=True)
    assert result == expected


def test_allow_nan_true_with_inf():
    """Test allow_nan=True with Infinity."""
    data = [1.0, float("inf"), 2.0]
    result = fastjson.dumps(data, allow_nan=True)
    expected = json.dumps(data, allow_nan=True)
    assert result == expected


def test_allow_nan_true_with_neg_inf():
    """Test allow_nan=True with -Infinity."""
    data = [1.0, float("-inf"), 2.0]
    result = fastjson.dumps(data, allow_nan=True)
    expected = json.dumps(data, allow_nan=True)
    assert result == expected


def test_allow_nan_false_with_nan():
    """Test allow_nan=False with NaN raises ValueError."""
    data = [1.0, float("nan"), 2.0]
    with pytest.raises(ValueError) as e_fast:
        fastjson.dumps(data, allow_nan=False)
    with pytest.raises(ValueError) as e_std:
        json.dumps(data, allow_nan=False)
    assert str(e_fast.value) == str(e_std.value)


def test_allow_nan_false_with_inf():
    """Test allow_nan=False with Infinity raises ValueError."""
    data = [1.0, float("inf"), 2.0]
    with pytest.raises(ValueError) as e_fast:
        fastjson.dumps(data, allow_nan=False)
    with pytest.raises(ValueError) as e_std:
        json.dumps(data, allow_nan=False)
    assert str(e_fast.value) == str(e_std.value)


def test_allow_nan_false_with_neg_inf():
    """Test allow_nan=False with -Infinity raises ValueError."""
    data = [1.0, float("-inf"), 2.0]
    with pytest.raises(ValueError) as e_fast:
        fastjson.dumps(data, allow_nan=False)
    with pytest.raises(ValueError) as e_std:
        json.dumps(data, allow_nan=False)
    assert str(e_fast.value) == str(e_std.value)


def test_default_allow_nan_true():
    """Test that default allow_nan is True."""
    data = [1.0, float("nan"), 2.0]
    # Should not raise by default
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected
