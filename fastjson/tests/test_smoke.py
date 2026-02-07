"""Smoke tests for fastjson package."""

import fastjson
import json


def test_import():
    """Test that the module imports correctly."""
    assert hasattr(fastjson, 'dumps')


def test_dumps_basic():
    """Test basic dumps functionality."""
    # Test None
    result = fastjson.dumps(None)
    assert isinstance(result, str)
    assert result == "null"
    
    # Test bool
    assert fastjson.dumps(True) == "true"
    assert fastjson.dumps(False) == "false"
    
    # Test int
    assert fastjson.dumps(42) == "42"
    
    # Test float
    result = fastjson.dumps(3.14)
    assert isinstance(result, str)
    assert "3.14" in result


def test_dumps_string():
    """Test string serialization."""
    assert fastjson.dumps("hello") == '"hello"'
    assert fastjson.dumps("with spaces") == '"with spaces"'


def test_dumps_list():
    """Test list serialization."""
    result = fastjson.dumps([1, 2, 3])
    assert result == "[1, 2, 3]"


def test_dumps_dict():
    """Test dict serialization."""
    result = fastjson.dumps({"a": 1, "b": 2})
    # Order may vary in Python < 3.7, so check both possibilities
    assert result in ['{"a": 1, "b": 2}', '{"b": 2, "a": 1}']


def test_dumps_nested():
    """Test nested structure serialization."""
    data = {"key": [1.0, 2.0, 3.0], "nested": {"a": "value"}}
    result = fastjson.dumps(data)
    assert isinstance(result, str)
    # Verify it's valid JSON
    parsed = json.loads(result)
    assert parsed["key"] == [1.0, 2.0, 3.0]


def test_dumps_with_options():
    """Test dumps with options."""
    data = [1, 2, 3]
    
    # Test separators
    result = fastjson.dumps(data, separators=(",", ":"))
    assert result == "[1,2,3]"
    
    # Test ensure_ascii
    result = fastjson.dumps("café", ensure_ascii=True)
    assert isinstance(result, str)


def test_compat_with_stdlib():
    """Test compatibility with stdlib json."""
    test_cases = [
        None,
        True,
        False,
        42,
        3.14159,
        "hello",
        [1, 2, 3],
        {"a": 1, "b": 2},
        {"nested": [1, 2, {"deep": "value"}]},
    ]
    
    for case in test_cases:
        fast_result = fastjson.dumps(case)
        std_result = json.dumps(case)
        # Parse both and compare
        assert json.loads(fast_result) == json.loads(std_result)
