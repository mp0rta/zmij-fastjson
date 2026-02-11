"""Edge-case and seeded fuzz tests for pyzmij."""

import math
import random
import struct

import pyzmij


def f64_from_bits(bits: int) -> float:
    return struct.unpack("!d", struct.pack("!Q", bits & 0xFFFFFFFFFFFFFFFF))[0]


EDGE_BITS = [
    0x0000000000000000,  # +0
    0x8000000000000000,  # -0
    0x0000000000000001,  # min subnormal
    0x000FFFFFFFFFFFFF,  # max subnormal
    0x0010000000000000,  # min normal
    0x3FEFFFFFFFFFFFFF,  # just below 1.0
    0x3FF0000000000000,  # 1.0
    0x3FF0000000000001,  # just above 1.0
    0x4330000000000000,  # 2^52
    0x4340000000000000,  # 2^53
    0x7FEFFFFFFFFFFFFF,  # max finite
]


def test_edge_values_match_repr_roundtrip():
    for bits in EDGE_BITS:
        value = f64_from_bits(bits)
        assert math.isfinite(value)
        formatted = pyzmij.format_finite(value)
        assert float(formatted) == value
        assert pyzmij.format(value, json_compatible=True) == repr(value)


def test_json_compatible_rules_on_edge_values():
    cases = [f64_from_bits(bits) for bits in EDGE_BITS]
    for value in cases:
        out = pyzmij.format(value, json_compatible=True)
        # Integer-looking finite outputs keep .0 in JSON-compatible mode.
        if "." not in repr(value) and "e" not in repr(value) and "E" not in repr(value):
            assert ".0" in out or "e" in out or "E" in out


def test_seeded_fuzz_format_finite_matches_repr():
    rng = random.Random(0)
    checked = 0
    while checked < 2000:
        bits = rng.getrandbits(64)
        value = f64_from_bits(bits)
        if not math.isfinite(value):
            continue
        assert float(pyzmij.format_finite(value)) == value
        assert pyzmij.format(value, json_compatible=True) == repr(value)
        checked += 1


def test_seeded_fuzz_batch_total_len_property():
    rng = random.Random(1)
    for _ in range(40):
        values = []
        while len(values) < 128:
            bits = rng.getrandbits(64)
            value = f64_from_bits(bits)
            if math.isfinite(value):
                values.append(value)

        expected = sum(len(pyzmij.format_finite(value)) for value in values)
        assert pyzmij.format_many_len(values) == expected
