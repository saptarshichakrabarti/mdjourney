"""
Service modules for MDJourney.
Provides factory functions for service instances.
"""

from typing import Optional

# Import service classes
from .file_processor import FileProcessor
from .metadata_generator import MetadataGenerator
from .schema_manager import SchemaManager, get_schema_manager
from .async_schema_manager import AsyncSchemaManager, get_async_schema_manager
from .version_control import VersionControlManager, get_vc_manager
from .scanners import DirmetaScanner, BasicFileScanner

# Re-export convenience functions
from .file_processor import process_file_with_dirmeta
from .metadata_generator import (
    generate_project_file,
    generate_dataset_files,
    create_experiment_contextual_template,
    generate_complete_metadata_file,
    check_contextual_metadata_completion,
)
from .schema_manager import (
    load_schema,
    validate_json,
    resolve_schema_path,
    get_schema_resolution_info,
    list_available_schemas,
)

__all__ = [
    # Classes
    "FileProcessor",
    "MetadataGenerator",
    "SchemaManager",
    "AsyncSchemaManager",
    "VersionControlManager",
    "DirmetaScanner",
    "BasicFileScanner",
    # Factory functions
    "get_schema_manager",
    "get_async_schema_manager",
    "get_vc_manager",
    "get_metadata_generator",
    # Convenience functions
    "process_file_with_dirmeta",
    "generate_project_file",
    "generate_dataset_files",
    "create_experiment_contextual_template",
    "generate_complete_metadata_file",
    "check_contextual_metadata_completion",
    "load_schema",
    "validate_json",
    "resolve_schema_path",
    "get_schema_resolution_info",
    "list_available_schemas",
]


def get_metadata_generator():
    """Get the global metadata generator instance."""
    from .metadata_generator import get_metadata_generator as _get_metadata_generator
    return _get_metadata_generator()
