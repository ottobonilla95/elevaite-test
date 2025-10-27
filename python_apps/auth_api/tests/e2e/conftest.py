"""
Pytest configuration for E2E tests
"""

import pytest


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests (requires running services)",
    )
    parser.addoption(
        "--opa-url",
        action="store",
        default="http://localhost:8181",
        help="OPA URL for E2E tests",
    )
    parser.addoption(
        "--auth-api-url",
        action="store",
        default="http://localhost:8004/auth-api",
        help="Auth API URL for E2E tests",
    )


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    if not config.getoption("--run-e2e"):
        skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords or "test_e2e" in item.nodeid:
                item.add_marker(skip_e2e)

