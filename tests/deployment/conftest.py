"""
Deployment test configuration.

These tests hit a LIVE backend — they need a running API + worker.
Set BASE_URL to target Azure or local.
"""

import os

import pytest
import requests


def pytest_configure(config):
    """Register deployment markers."""
    config.addinivalue_line("markers", "deployment: tests that hit a live backend")


def pytest_collection_modifyitems(items):
    """Auto-mark all tests in this directory as deployment tests."""
    for item in items:
        if "deployment" in str(item.fspath):
            item.add_marker(pytest.mark.deployment)


@pytest.fixture(scope="session", autouse=True)
def verify_backend_reachable():
    """Fail fast if the backend isn't running."""
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    try:
        resp = requests.get(f"{base_url}/health", timeout=10)
        if resp.status_code != 200:
            pytest.skip(f"Backend at {base_url} returned {resp.status_code}")
    except requests.ConnectionError:
        pytest.skip(
            f"Backend not reachable at {base_url}. "
            f"Start with: uvicorn app.main:app --port 8000"
        )
