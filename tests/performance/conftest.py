"""Configuration for performance tests."""

import pytest


def pytest_configure(config):
    """Configure performance test markers."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests requiring LLM API calls"
    )


def pytest_collection_modifyitems(config, items):
    """Add performance marker to performance tests automatically."""
    for item in items:
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)


@pytest.fixture(scope="session")
def performance_test_data():
    """Shared test data for performance tests."""
    return {
        "expected_baseline": {
            "single_page_entries": 55,
            "multi_page_entries": 117,
            "historical_single_accuracy": 101.9,
            "historical_multi_accuracy": 30.2
        }
    }