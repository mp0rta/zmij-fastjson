import os
from typing import Optional

import pyperf


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return float(value)


def pin_affinity_from_env() -> None:
    # Linux only; ignore if unsupported.
    spec = os.environ.get("PYPERF_AFFINITY", "0").strip()
    if not spec:
        return

    cpus = {int(x) for x in spec.split(",") if x.strip() != ""}
    try:
        os.sched_setaffinity(0, cpus)  # type: ignore[attr-defined]
    except Exception:
        return


def make_runner() -> pyperf.Runner:
    # Prefer a single pinned process by default for lower scheduler noise.
    # Tune via env vars if needed.
    pin_affinity_from_env()
    return pyperf.Runner(
        values=_env_int("PYPERF_VALUES", 40),
        processes=_env_int("PYPERF_PROCESSES", 1),
        warmups=_env_int("PYPERF_WARMUPS", 3),
        min_time=_env_float("PYPERF_MIN_TIME", 0.5),
    )

