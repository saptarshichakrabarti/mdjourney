"""
Basic regression tests to ensure existing functionality is preserved.
"""

import pytest


@pytest.mark.regression
def test_basic_regression():
    """Basic regression test to ensure the test structure works."""
    assert True


@pytest.mark.regression
def test_import_regression():
    """Test that all modules can still be imported after refactoring."""
    # Updated for refactored package layout
    try:
        from app.core import config
        from app.monitors import folder_monitor
        from app.services import (
            file_processor,
            metadata_generator,
            schema_manager,
            version_control,
        )
        from app.utils import helpers

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import app modules: {e}")


@pytest.mark.regression
def test_config_regression():
    """Test that configuration values are still accessible."""
    import os

    from app.core.config import MONITOR_PATH, PROJECT_PREFIX, SCHEMA_BASE_PATH

    # MONITOR_PATH can be either the default config path or test environment path
    if os.environ.get("MDJOURNEY_DATA_PATH"):
        # During testing, MONITOR_PATH should be the test environment path
        expected_suffix = "/data"
        assert str(MONITOR_PATH).endswith(
            expected_suffix
        ), f"Expected MONITOR_PATH to end with '{expected_suffix}', got: {MONITOR_PATH}"
        # Verify it's a temporary directory path (contains 'tmp' or 'T')
        assert any(
            part in str(MONITOR_PATH) for part in ["tmp", "T"]
        ), f"Expected test temp path, got: {MONITOR_PATH}"
    else:
        # In normal operation, should be the configured data path
        assert str(MONITOR_PATH) in [
            "data",
            "./data",
        ], f"Unexpected MONITOR_PATH: {MONITOR_PATH}"

    assert PROJECT_PREFIX == "p_"
    # Schema base path now points to packaged_schemas in the refactor
    assert SCHEMA_BASE_PATH == "packaged_schemas"
