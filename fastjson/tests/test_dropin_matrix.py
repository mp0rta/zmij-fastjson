import json
import math
import random
import struct

import pytest

import fastjson


def assert_same_dumps(obj, **kwargs):
    try:
        got = fastjson.dumps(obj, **kwargs)
    except Exception as e_fast:  # noqa: BLE001 - we want exact parity with stdlib
        with pytest.raises(type(e_fast)) as e_std:
            json.dumps(obj, **kwargs)
        assert str(e_fast) == str(e_std.value)
    else:
        expected = json.dumps(obj, **kwargs)
        assert got == expected


def generate_finite_floats(*, n: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    out: list[float] = []
    while len(out) < n:
        bits = rng.getrandbits(64)
        x = struct.unpack("!d", struct.pack("!Q", bits))[0]
        if math.isfinite(x):
            out.append(x)
    return out


KWARGS_CASES: list[dict] = [
    {},
    {"ensure_ascii": True},
    {"ensure_ascii": False},
    {"allow_nan": True},
    {"allow_nan": False},  # finite-only dataset => should behave the same
    {"separators": None},
    {"separators": (", ", ": ")},
    {"separators": (",", ":")},
    {"separators": [", ", ": "]},
    {"separators": [",", ":"]},
    {"separators": ",:"},  # stdlib accepts 2-length strings via sequence unpacking
    {"separators": (";", ":")},  # unsupported => fallback (still identical)
    {"check_circular": True},
    {"check_circular": False},
    {"indent": None},
    {"indent": 2},
    {"sort_keys": False},
    {"sort_keys": True},
    {"cls": json.JSONEncoder},
    {"default": str},
    # Combined cases (exercise routing)
    {"separators": (",", ":"), "ensure_ascii": False},
    {"indent": 2, "sort_keys": True, "ensure_ascii": False},
]


@pytest.mark.parametrize("kwargs", KWARGS_CASES)
def test_dropin_seeded_random_finite_float_sequence(kwargs):
    values = [0.0, -0.0, 1.0, -1.0] + generate_finite_floats(n=400, seed=0)

    assert_same_dumps(values, **kwargs)
    assert_same_dumps(tuple(values), **kwargs)


@pytest.mark.parametrize(
    "obj",
    [
        {"b": 2, "a": 1, "x": [1.0, 2.0, 3.0]},
        {"nested": {"k": "v", "arr": [0.0, -0.0, 1.0]}},
        [1, 2, 3, 4],
        ["café", "a\"b\nc", "line\u2028sep"],
        [1.0, None, 2.0, True, False, 3, "x", {"k": 1.0}],
    ],
)
@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"ensure_ascii": True},
        {"ensure_ascii": False},
        {"separators": (",", ":")},
        {"separators": (", ", ": ")},
        {"indent": 2},
        {"sort_keys": True},
        {"check_circular": False},
    ],
)
def test_dropin_common_objects_matrix(obj, kwargs):
    assert_same_dumps(obj, **kwargs)

