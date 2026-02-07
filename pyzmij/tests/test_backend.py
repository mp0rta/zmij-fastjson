"""Test backend selection."""

import pyzmij


def test_backend_returns_string():
    """Test that backend() returns a string."""
    backend = pyzmij.backend()
    assert isinstance(backend, str)


def test_backend_is_vitaut_zmij():
    """Test that backend is 'vitaut/zmij'."""
    backend = pyzmij.backend()
    assert backend == "vitaut/zmij"


def test_backend_matches_expected():
    """Test that backend matches expected value."""
    backend = pyzmij.backend()
    assert backend == "vitaut/zmij"
