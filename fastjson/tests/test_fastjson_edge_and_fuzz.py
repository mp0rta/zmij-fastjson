"""Edge-case and seeded fuzz tests for fastjson drop-in behavior."""

import json
import math
import random
import struct

import fastjson


def f64_from_bits(bits: int) -> float:
    return struct.unpack("!d", struct.pack("!Q", bits & 0xFFFFFFFFFFFFFFFF))[0]


EDGE_VALUES = [
    f64_from_bits(0x0000000000000000),  # +0
    f64_from_bits(0x8000000000000000),  # -0
    f64_from_bits(0x0000000000000001),  # min subnormal
    f64_from_bits(0x000FFFFFFFFFFFFF),  # max subnormal
    f64_from_bits(0x0010000000000000),  # min normal
    f64_from_bits(0x3FEFFFFFFFFFFFFF),  # just below 1.0
    f64_from_bits(0x3FF0000000000000),  # 1.0
    f64_from_bits(0x3FF0000000000001),  # just above 1.0
    f64_from_bits(0x4330000000000000),  # 2^52
    f64_from_bits(0x4340000000000000),  # 2^53
    f64_from_bits(0x7FEFFFFFFFFFFFFF),  # max finite
]


def test_edge_float_sequences_match_stdlib_default_and_compact():
    values = [value for value in EDGE_VALUES if math.isfinite(value)]
    assert fastjson.dumps(values) == json.dumps(values)
    assert fastjson.dumps(values, separators=(",", ":")) == json.dumps(values, separators=(",", ":"))


def test_seeded_fuzz_finite_float_sequences_match_stdlib():
    rng = random.Random(0)
    values = []
    while len(values) < 600:
        bits = rng.getrandbits(64)
        value = f64_from_bits(bits)
        if math.isfinite(value):
            values.append(value)

    assert fastjson.dumps(values) == json.dumps(values)
    assert fastjson.dumps(values, separators=(",", ":")) == json.dumps(values, separators=(",", ":"))
    assert fastjson.dumps(tuple(values)) == json.dumps(tuple(values))


def test_seeded_fuzz_mostly_floats_with_nulls_match_stdlib():
    rng = random.Random(2)
    values = []
    while len(values) < 300:
        bits = rng.getrandbits(64)
        value = f64_from_bits(bits)
        if math.isfinite(value):
            # periodic nulls to hit mixed-path behavior
            values.append(None if (len(values) % 17) == 0 else value)

    assert fastjson.dumps(values) == json.dumps(values)
    assert fastjson.dumps(values, separators=(",", ":")) == json.dumps(values, separators=(",", ":"))
