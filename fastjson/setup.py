"""Setup script for fastjson package."""

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

# Sources - using vendored vitaut/zmij
sources = ["src/fastjson_module.c"]
if os.name == "nt":
    sources += [
        "third_party/zmij/zmij.cc",
        "third_party/common/zmij_c_shim.cc",
    ]
else:
    sources += ["third_party/zmij/zmij.c"]

# Include directories
include_dirs = [
    "src",
    "third_party/zmij",
]

# Compiler flags (pure C, no C++ needed)
extra_compile_args = []

print(f"Building fastjson with vendored vitaut/zmij at {zmij_path}", file=sys.stderr)

# Define the extension module
ext_modules = [
    Extension(
        "fastjson._fastjson",
        sources=sources,
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
    )
]

setup(
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    ext_modules=ext_modules,
)
