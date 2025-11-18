"""
Basic functionality tests to verify the test structure is working.
"""

# Add src to path for imports
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.unit
def test_import_app_modules():
    """Test that all app modules can be imported."""
    try:
        from app.core import config
        from app.monitors import folder_monitor
        from app.services import (
            file_processor,
            metadata_generator,
            schema_manager,
            version_control,
        )
        from app.utils import utils

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import app modules: {e}")


@pytest.mark.unit
def test_config_imports():
    """Test that config module has expected attributes."""
    from app.core.config import MONITOR_PATH, PROJECT_PREFIX, SCHEMA_BASE_PATH

    assert MONITOR_PATH is not None
    assert PROJECT_PREFIX is not None
    assert SCHEMA_BASE_PATH is not None


@pytest.mark.unit
def test_utils_imports():
    """Test that utils module has expected functions."""
    from app.utils.helpers import (
        calculate_checksum_incremental,
        ensure_directory_exists,
        get_current_timestamp,
    )

    assert callable(get_current_timestamp)
    assert callable(calculate_checksum_incremental)
    assert callable(ensure_directory_exists)


@pytest.mark.unit
def test_schema_manager_imports():
    """Test that schema_manager module has expected classes and functions."""
    from app.services.schema_manager import (
        SchemaManager,
        get_schema_manager,
        load_schema,
        validate_json,
    )

    assert SchemaManager is not None
    assert callable(get_schema_manager)
    assert callable(load_schema)
    assert callable(validate_json)


@pytest.mark.unit
def test_metadata_generator_imports():
    """Test that metadata_generator module has expected classes and functions."""
    from app.services.metadata_generator import (
        MetadataGenerator,
        get_metadata_generator,
    )

    assert MetadataGenerator is not None
    assert callable(get_metadata_generator)


@pytest.mark.unit
def test_file_processor_imports():
    """Test that file_processor module has expected classes and functions."""
    from app.services.file_processor import FileProcessor, get_file_processor

    assert FileProcessor is not None
    assert callable(get_file_processor)


@pytest.mark.unit
def test_folder_monitor_imports():
    """Test that folder_monitor module has expected classes and functions."""
    from app.monitors.folder_monitor import (
        FolderCreationHandler,
        FolderMonitor,
        get_folder_monitor,
    )

    assert FolderCreationHandler is not None
    assert FolderMonitor is not None
    assert callable(get_folder_monitor)


@pytest.mark.unit
def test_version_control_imports():
    """Test that version_control module has expected classes and functions."""
    from app.services.version_control import VersionControlManager, get_vc_manager

    assert VersionControlManager is not None
    assert callable(get_vc_manager)


@pytest.mark.unit
def test_singleton_pattern():
    """Test that singleton pattern works for manager classes."""
    import os
    import tempfile

    from app.monitors.folder_monitor import get_folder_monitor
    from app.services.file_processor import get_file_processor
    from app.services.metadata_generator import get_metadata_generator
    from app.services.schema_manager import get_schema_manager
    from app.services.version_control import get_vc_manager

    # Test that multiple calls return the same instance
    schema_manager1 = get_schema_manager()
    schema_manager2 = get_schema_manager()
    assert schema_manager1 is schema_manager2

    metadata_generator1 = get_metadata_generator()
    metadata_generator2 = get_metadata_generator()
    assert metadata_generator1 is metadata_generator2

    file_processor1 = get_file_processor()
    file_processor2 = get_file_processor()
    assert file_processor1 is file_processor2

    # Create a temporary directory for folder monitor testing
    with tempfile.TemporaryDirectory() as temp_dir:
        folder_monitor1 = get_folder_monitor(temp_dir)
        folder_monitor2 = get_folder_monitor(temp_dir)
        assert folder_monitor1 is folder_monitor2

    vc_manager1 = get_vc_manager()
    vc_manager2 = get_vc_manager()
    assert vc_manager1 is vc_manager2


@pytest.mark.unit
def test_path_resolution():
    """Test that path resolution works correctly."""
    from app.core.config import SCHEMA_BASE_PATH

    # Test that schema base path is a valid path
    schema_path = Path(SCHEMA_BASE_PATH)
    assert schema_path.exists() or str(schema_path).endswith(".template_schemas")


@pytest.mark.unit
def test_timestamp_generation():
    """Test that timestamp generation works."""
    from app.utils.helpers import get_current_timestamp

    timestamp = get_current_timestamp()
    assert timestamp is not None
    assert isinstance(timestamp, str)
    assert len(timestamp) > 0


@pytest.mark.unit
def test_directory_creation():
    """Test that directory creation utility works."""
    import os
    import tempfile

    from app.utils.helpers import ensure_directory_exists

    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "test_subdir")
        ensure_directory_exists(Path(test_dir))
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)
