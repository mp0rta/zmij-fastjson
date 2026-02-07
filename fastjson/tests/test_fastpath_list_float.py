"""Test fast path for list[float] serialization."""

import json
import fastjson


def test_list_float_basic():
    """Test basic list of floats."""
    data = [1.0, 2.5, 3.0]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected
    # Should be parseable back
    parsed = json.loads(result)
    assert parsed[0] == 1.0
    assert parsed[1] == 2.5
    assert parsed[2] == 3.0


def test_tuple_float_basic():
    """Test basic tuple of floats."""
    data = (1.0, 2.5, 3.0)
    result = fastjson.dumps(data)
    # JSON arrays don't distinguish list vs tuple
    parsed = json.loads(result)
    assert parsed == [1.0, 2.5, 3.0]


def test_empty_list():
    """Test empty list."""
    data = []
    result = fastjson.dumps(data)
    assert result == "[]"


def test_single_float():
    """Test single element list."""
    data = [3.14159]
    result = fastjson.dumps(data)
    parsed = json.loads(result)
    assert len(parsed) == 1
    assert abs(parsed[0] - 3.14159) < 1e-10


def test_negative_floats():
    """Test negative floats."""
    data = [-1.5, -2.0, -0.0]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected
    parsed = json.loads(result)
    assert parsed[0] == -1.5
    assert parsed[1] == -2.0
    assert parsed[2] == 0.0  # value compares equal; sign is preserved in JSON


def test_large_list():
    """Test larger list of floats."""
    data = [float(i) * 0.5 for i in range(100)]
    result = fastjson.dumps(data)
    parsed = json.loads(result)
    assert len(parsed) == 100


def test_scientific_notation():
    """Test floats in scientific notation range."""
    data = [1e-10, 1e10, 1e-30, 1e30]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected
    parsed = json.loads(result)
    assert len(parsed) == 4


def test_mixed_types_fallback():
    """Test that mixed types fall back to slow path."""
    # This should still work via json module fallback
    data = [1.0, "string", 2.0]
    result = fastjson.dumps(data)
    # Fallback uses json.dumps with default separators
    expected = json.dumps(data)
    assert result == expected


def test_mixed_types_compact_separators_match_python_json():
    data = [1.0, None, 2.0, True, False, 3, "x", {"k": 1.0}]
    result = fastjson.dumps(data, separators=(",", ":"))
    expected = json.dumps(data, separators=(",", ":"))
    assert result == expected


def test_mixed_types_string_escaping_and_ensure_ascii_match_python_json():
    data = [1.0, "a\"b\nc", "café", {"k": "line\u2028sep"}]
    result = fastjson.dumps(data, separators=(",", ":"), ensure_ascii=True)
    expected = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    assert result == expected

    result = fastjson.dumps(data, separators=(",", ":"), ensure_ascii=False)
    expected = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    assert result == expected


def test_nested_list_fallback():
    """Test nested list falls back to slow path."""
    data = [[1.0, 2.0], [3.0, 4.0]]
    result = fastjson.dumps(data)
    # Fallback uses json.dumps with default separators
    expected = json.dumps(data)
    assert result == expected


def test_fastpath_produces_valid_json():
    """Test that fast path produces valid JSON."""
    data = [1.0, 2.5, 3.0, -1.0, 0.0, 1e10]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected
    # Should be parseable
    parsed = json.loads(result)
    assert parsed == data


def test_integer_looking_floats_match_python_json():
    data = [-2342207769386335.0]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected


def test_dot0_added_for_integer_valued_floats():
    data = [0.0, -0.0, 1.0, -1.0]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected


def test_exponent_floats_match_python_json():
    data = [1e16, 1e-300, 1e308]
    result = fastjson.dumps(data)
    expected = json.dumps(data)
    assert result == expected


def test_nan_inf_match_python_json_allow_nan_true():
    data = [float("nan"), float("inf"), float("-inf")]
    result = fastjson.dumps(data, allow_nan=True)
    expected = json.dumps(data, allow_nan=True)
    assert result == expected


def test_float_sequence_with_default_separators_falls_back_to_stdlib():
    data = [1.0, 2.5, 3.0]
    result = fastjson.dumps(data, separators=(", ", ": "))
    expected = json.dumps(data, separators=(", ", ": "))
    assert result == expected


def test_separators_can_be_list_like_stdlib():
    data = [1.0, 2.5, 3.0]
    result = fastjson.dumps(data, separators=[",", ":"])
    expected = json.dumps(data, separators=[",", ":"])
    assert result == expected

    result = fastjson.dumps(data, separators=[", ", ": "])
    expected = json.dumps(data, separators=[", ", ": "])
    assert result == expected
