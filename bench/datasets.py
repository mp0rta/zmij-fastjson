# bench/datasets.py
from __future__ import annotations
import math
import random
import struct
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Any

# ---------- low-level helpers ----------

def f64_from_bits(u: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", u & 0xFFFFFFFFFFFFFFFF))[0]

def f32_from_bits(u: int) -> float:
    return struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0]

def is_finite(x: float) -> bool:
    return math.isfinite(x)

# ---------- datasets: fixed / edge cases ----------

def fixed_f64_values() -> List[float]:
    # dtolnay/zmij bench flavor: 0, short, medium, e, max, plus some practical extras
    e = math.e
    max_finite = f64_from_bits(0x7FEFFFFFFFFFFFFF)
    return [
        0.0,
        -0.0,
        0.1234,
        0.123456789,
        e,
        max_finite,
        1.0,
        -1.0,
        1e-6,
        1e6,
        9007199254740992.0,       # 2^53
        9007199254740993.0,       # 2^53+1 (not exactly representable)
        1.2345678901234567,       # 17 digits-ish
    ]

def edge_bits_f64() -> List[int]:
    # IEEE754 boundary patterns
    return [
        0x0000000000000000,  # +0
        0x8000000000000000,  # -0
        0x0000000000000001,  # min subnormal
        0x000FFFFFFFFFFFFF,  # max subnormal
        0x0010000000000000,  # min normal
        0x7FEFFFFFFFFFFFFF,  # max finite
        0x3FF0000000000000,  # 1.0
        0xBFF0000000000000,  # -1.0
        # values near powers of two (rounding cliffs often live around here)
        0x3FEFFFFFFFFFFFFF,  # just below 1.0
        0x3FF0000000000001,  # just above 1.0
        0x4330000000000000,  # 2^52
        0x4340000000000000,  # 2^53
        0x4350000000000000,  # 2^54
    ]

def edge_f64_values() -> List[float]:
    vals = [f64_from_bits(u) for u in edge_bits_f64()]
    # Ensure finite only (all above are finite)
    return vals

# ---------- datasets: random-bit finite sampling ----------

def random_finite_f64_bits(n: int, seed: int) -> List[int]:
    """Random u64 bit patterns, filtered to finite f64 (exclude NaN/Inf)."""
    rng = random.Random(seed)
    out: List[int] = []
    while len(out) < n:
        u = rng.getrandbits(64)
        x = f64_from_bits(u)
        if is_finite(x):
            out.append(u)
    return out

def random_finite_f64_values(n: int, seed: int) -> List[float]:
    return [f64_from_bits(u) for u in random_finite_f64_bits(n, seed)]

# ---------- datasets: JSON-like real-world distributions ----------

def uniform_real_f64(n: int, seed: int, lo: float = -1e6, hi: float = 1e6) -> List[float]:
    rng = random.Random(seed)
    return [rng.uniform(lo, hi) for _ in range(n)]

def near_zero_real_f64(n: int, seed: int, scale: float = 1e-3) -> List[float]:
    """
    Values clustered near 0; typical for jitter, residuals, deltas.
    Use a signed exponential distribution.
    """
    rng = random.Random(seed)
    out: List[float] = []
    for _ in range(n):
        sign = -1.0 if rng.getrandbits(1) else 1.0
        # expovariate(lambda) has mean 1/lambda; choose lambda = 1/scale
        v = rng.expovariate(1.0 / scale) * sign
        out.append(v)
    return out

def integral_looking_f64(n: int, seed: int, lo: int = -10_000_000, hi: int = 10_000_000) -> List[float]:
    """
    Floats that look like integers (x.0) to stress ADD_DOT_0 behavior and fast-paths.
    """
    rng = random.Random(seed)
    return [float(rng.randint(lo, hi)) for _ in range(n)]

# ---------- macro JSON shapes ----------

def macro_sensor_frame(n_series: int, n_points: int, seed: int) -> Dict[str, Any]:
    """
    Nested dict/list typical for telemetry: multiple time series + metadata.
    """
    rng = random.Random(seed)
    frame = {
        "ts": 1738368000.123456,
        "device": {"id": "dev-001", "fw": "1.2.3"},
        "meta": {"site": "tokyo", "seq": rng.randint(0, 10**9)},
        "series": [],
    }
    for i in range(n_series):
        series = {
            "name": f"s{i}",
            "unit": "ms",
            "values": uniform_real_f64(n_points, seed + 1000 + i, lo=-50.0, hi=50.0),
        }
        frame["series"].append(series)
    return frame


def mostly_floats_with_nulls(n: int, seed: int, null_every: int = 20) -> List[Any]:
    """
    A mixed list that is mostly floats, with periodic None values.

    Intended to simulate sparse sensor streams where missing values are encoded as null.
    """
    xs = random_finite_f64_values(n, seed=seed)
    out: List[Any] = []
    for i, x in enumerate(xs):
        out.append(None if null_every > 0 and (i % null_every) == 0 else x)
    return out
