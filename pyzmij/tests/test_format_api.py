"""Tests for the higher-level format/format_many APIs."""

import pyzmij
import pytest


def test_format_matches_format_finite_for_regular_values():
    for x in [0.0, -0.0, 1.5, -2.75, 1e-10, 1e10]:
        assert pyzmij.format(x) == pyzmij.format_finite(x)


def test_format_json_compatible_appends_dot0():
    assert pyzmij.format(1.0, json_compatible=True) == "1.0"
    assert pyzmij.format(-0.0, json_compatible=True) == "-0.0"
    assert pyzmij.format(3.14, json_compatible=True) == "3.14"


def test_format_non_finite_handling():
    with pytest.raises(ValueError, match="finite"):
        pyzmij.format(float("nan"))

    assert pyzmij.format(float("nan"), allow_non_finite=True) == "nan"
    assert pyzmij.format(float("inf"), allow_non_finite=True) == "inf"
    assert pyzmij.format(float("-inf"), allow_non_finite=True) == "-inf"

    assert pyzmij.format(float("nan"), json_compatible=True, allow_non_finite=True) == "NaN"
    assert pyzmij.format(float("inf"), json_compatible=True, allow_non_finite=True) == "Infinity"
    assert pyzmij.format(float("-inf"), json_compatible=True, allow_non_finite=True) == "-Infinity"


def test_format_many_returns_formatted_list():
    values = [1.0, -0.0, 3.14]
    assert pyzmij.format_many(values) == [pyzmij.format(v) for v in values]
    assert pyzmij.format_many(values, json_compatible=True) == ["1.0", "-0.0", "3.14"]


def test_format_many_rejects_non_float_items():
    with pytest.raises(TypeError, match="sequence item 1 must be float"):
        pyzmij.format_many([1.0, 2, 3.0])
