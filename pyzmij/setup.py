"""Setup script for pyzmij package."""

import os
import sys
from setuptools import setup, Extension, find_packages
from pathlib import Path

# Get the directory containing this file
here = Path(__file__).parent.resolve()

# Use vendored vitaut/zmij sources (no submodule required)
zmij_path = here / "third_party" / "zmij"
if not zmij_path.exists():
    raise RuntimeError(f"Vendored zmij sources not found at {zmij_path}.")

# Sources: pyzmij module + vitaut/zmij implementation
sources = ["src/pyzmij_module.c"]
if os.name == "nt":
    sources += [
        "third_party/zmij/zmij.cc",
        "third_party/common/zmij_c_shim.cc",
    ]
else:
    sources += ["third_party/zmij/zmij.c"]

# Include directories
include_dirs = [
    "third_party/zmij",  # zmij-c.h
]

# Define the extension module
ext_modules = [
    Extension(
        "pyzmij._pyzmij",
        sources=sources,
        include_dirs=include_dirs,
    )
]

print(f"Building pyzmij with vendored vitaut/zmij at {zmij_path}", file=sys.stderr)

setup(
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    ext_modules=ext_modules,
)
