"""
Dependency providers for the FAIR Metadata Enrichment API.
Provides factory functions for creating service instances using FastAPI's dependency injection.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from routers.services import ProjectService, SchemaService, MetadataService
from app.core.config import find_config_file, get_monitor_path, initialize_config
from app.monitors.folder_monitor import FolderMonitor
from app.services.file_processor import FileProcessor
from app.services.metadata_generator import MetadataGenerator
from app.services.schema_manager import SchemaManager

from app.services.version_control import VersionControlManager


def get_schema_manager() -> SchemaManager:
    """Dependency provider for SchemaManager."""
    return SchemaManager()


def get_version_control_manager() -> VersionControlManager:
    """Dependency provider for VersionControlManager."""
    return VersionControlManager()


def get_vc_manager() -> VersionControlManager:
    """Alias for get_version_control_manager for backward compatibility."""
    return get_version_control_manager()


def get_metadata_generator() -> MetadataGenerator:
    """Dependency provider for MetadataGenerator."""
    return MetadataGenerator()


def get_file_processor() -> FileProcessor:
    """Dependency provider for FileProcessor."""
    from app.services.scanners import DirmetaScanner

    scanner = DirmetaScanner()
    return FileProcessor(scanner=scanner)


def get_folder_monitor() -> FolderMonitor:
    """Dependency provider for FolderMonitor."""
    # Initialize configuration if needed
    from app.core.config import MONITOR_PATH

    if MONITOR_PATH is None:
        config_file = find_config_file()
        if config_file and initialize_config(str(config_file)):
            print(f"Configuration initialized from {config_file}")
        else:
            raise RuntimeError("Failed to initialize configuration")

    monitor_path = get_monitor_path()
    return FolderMonitor(str(monitor_path))


# --- API Service Providers ---
# These create the instances of your API-layer services, which in turn
# will depend on the core services above.


def get_project_service() -> "ProjectService":
    """Dependency provider for ProjectService."""
    from routers.services import ProjectService

    metadata_generator = get_metadata_generator()
    return ProjectService(metadata_generator=metadata_generator)


def get_schema_service() -> "SchemaService":
    """Dependency provider for SchemaService."""
    from routers.services import SchemaService

    schema_manager = get_schema_manager()
    return SchemaService(schema_manager=schema_manager)


def get_metadata_service() -> "MetadataService":
    """Dependency provider for MetadataService."""
    from routers.services import MetadataService

    schema_manager = get_schema_manager()
    metadata_generator = get_metadata_generator()
    vc_manager = get_version_control_manager()
    return MetadataService(
        schema_manager=schema_manager,
        metadata_generator=metadata_generator,
        vc_manager=vc_manager,
    )
