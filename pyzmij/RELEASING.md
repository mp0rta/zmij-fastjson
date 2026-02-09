# Releasing `pyzmij`

## One-time setup

1. Create the `pyzmij` project on PyPI.
2. In GitHub repo settings, configure trusted publishing:
   - Provider: GitHub Actions
   - Workflow: `publish-pyzmij.yml`
   - Environment: `pypi`

## Pre-release checks

Run from repo root:

```bash
python -m pip install -U pip build
python -m build pyzmij -s -w
python -m venv .venv-rel
. .venv-rel/bin/activate
python -m pip install -U pip
python -m pip install pyzmij/dist/*.whl
python -c "import pyzmij; print(pyzmij.backend())"
python -m pytest -q pyzmij/tests --ignore=pyzmij/tests/test_repr_compat.py
```

## Release flow

Use a dedicated tag for `pyzmij` releases:

- Tag format: `pyzmij-vX.Y.Z` (example: `pyzmij-v0.1.0`)
- Create a GitHub Release from that tag.

Publishing is automatic through `.github/workflows/publish-pyzmij.yml`:
- Builds wheels on Linux/macOS/Windows for CPython 3.10-3.14
- Builds one sdist
- Uploads all artifacts to PyPI
