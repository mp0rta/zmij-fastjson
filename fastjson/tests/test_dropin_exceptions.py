import json

import pytest

import fastjson


def assert_same_exception(obj, **kwargs):
    with pytest.raises(Exception) as e_fast:
        fastjson.dumps(obj, **kwargs)
    with pytest.raises(Exception) as e_std:
        json.dumps(obj, **kwargs)

    assert type(e_fast.value) is type(e_std.value)
    assert str(e_fast.value) == str(e_std.value)


def test_non_serializable_types_match_exception():
    assert_same_exception(object())
    assert_same_exception(b"bytes")
    assert_same_exception({1, 2, 3})


def test_invalid_separators_match_exception():
    assert_same_exception([1, 2, 3], separators=(",",))  # wrong length
    assert_same_exception([1, 2, 3], separators=(1, 2))  # wrong types
    assert_same_exception([1, 2, 3], separators=",")  # wrong length (string is also a sequence)


def test_allow_nan_false_for_nonfinite_matches_exception_message():
    data = [1.0, float("nan"), 2.0]
    assert_same_exception(data, allow_nan=False)


def test_default_not_callable_matches_exception():
    assert_same_exception(object(), default=1)


def test_cls_not_type_matches_exception():
    assert_same_exception({"a": 1}, cls=1)


def test_circular_reference_matches_exception_message():
    a = []
    a.append(a)
    assert_same_exception(a)


def test_extra_positional_args_match_exception_message():
    with pytest.raises(TypeError) as e_fast:
        fastjson.dumps([1, 2, 3], True)  # pyright: ignore[reportCallIssue]
    with pytest.raises(TypeError) as e_std:
        json.dumps([1, 2, 3], True)  # pyright: ignore[reportCallIssue]
    assert str(e_fast.value) == str(e_std.value)


def test_unknown_kwargs_match_exception_message():
    with pytest.raises(TypeError) as e_fast:
        fastjson.dumps([1, 2, 3], foo=1)  # type: ignore[call-arg]
    with pytest.raises(TypeError) as e_std:
        json.dumps([1, 2, 3], foo=1)  # type: ignore[call-arg]
    assert str(e_fast.value) == str(e_std.value)
