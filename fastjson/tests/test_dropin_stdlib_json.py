import json

import pytest

import fastjson


def test_dumps_matches_stdlib_for_common_cases():
    cases = [
        None,
        True,
        False,
        0,
        42,
        3.14159,
        -0.0,
        "hello",
        "café",
        [1, 2, 3],
        [1.0, 2.5, 3.0],
        {"a": 1, "b": 2, "c": [1.0, 2.0, 3.0]},
        {"nested": [1, 2, {"deep": "value"}]},
    ]

    for obj in cases:
        assert fastjson.dumps(obj) == json.dumps(obj)


def test_dumps_forwards_kwargs_to_stdlib_when_needed():
    obj = {"b": 2, "a": 1, "s": "café"}

    kwargs_list = [
        {"sort_keys": True},
        {"indent": 2},
        {"ensure_ascii": False},
        {"ensure_ascii": True},
        {"separators": (",", ":")},
        {"separators": [",", ":"]},
    ]

    for kwargs in kwargs_list:
        assert fastjson.dumps(obj, **kwargs) == json.dumps(obj, **kwargs)


def test_skipkeys_behavior_matches_stdlib():
    obj = {("not", "json", "key"): 1, "ok": 2}

    with pytest.raises(TypeError) as e_fast:
        fastjson.dumps(obj, skipkeys=False)
    with pytest.raises(TypeError) as e_std:
        json.dumps(obj, skipkeys=False)
    assert str(e_fast.value) == str(e_std.value)

    assert fastjson.dumps(obj, skipkeys=True) == json.dumps(obj, skipkeys=True)


def test_loads_and_dumps_roundtrip():
    obj = {"x": [1.0, 2.0, 3.0], "y": None, "z": True}
    s = fastjson.dumps(obj)
    assert fastjson.loads(s) == json.loads(s)
