"""
Schema management module for the FAIR metadata automation system.
Handles JSON schema loading, validation, and caching with support for local overrides.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jsonschema import ValidationError as JSONSchemaValidationError, validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    # Create dummy classes for when jsonschema is not available
    class JSONSchemaValidationError(Exception):
        pass
    def validate(*args, **kwargs):
        raise ImportError("jsonschema library is required. Install with: pip install jsonschema")

from app.core import config as app_config
from app.core.exceptions import (
    SchemaError,
    SchemaNotFoundError,
    SchemaValidationError,
    PathNotFoundError,
    PermissionError,
    MDJourneyError,
)

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages JSON schemas for metadata validation with local override support."""

    def __init__(self, schema_base_path: Optional[Path] = None) -> None:
        """Initialize the schema manager.

        Args:
            schema_base_path: Base path for schema files (defaults to config)
        """
        # Use absolute path to avoid issues when running from different directories
        if schema_base_path:
            self.schema_base_path = Path(schema_base_path)
        else:
            # Get the project root by going up from app/services/ to the project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            self.schema_base_path = project_root / app_config.SCHEMA_BASE_PATH
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def resolve_schema_path(self, schema_name: str) -> Path:
        """
        Resolve schema path following the principle of local override first, then packaged default.

        Resolution order:
        1. Local override: MONITOR_PATH/.template_schemas/{schema_name}
        2. Custom schema directory (from config): CUSTOM_SCHEMA_PATH/{schema_name}
        3. Packaged default: project_root/packaged_schemas/{schema_name}

        Args:
            schema_name: Name of the schema file (e.g., "project_descriptive.json")

        Returns:
            Path to the resolved schema file
        """
        # First priority: explicit per-schema overrides from config (hard override)
        if hasattr(app_config, "SCHEMA_PATH_OVERRIDES"):
            override_explicit = app_config.SCHEMA_PATH_OVERRIDES.get(schema_name)
            if override_explicit:
                p = Path(override_explicit)
                print(f"Using explicit schema override from config: {p}")
                return p

        # Build candidate override directories in priority order
        candidate_dirs = []
        if app_config.MONITOR_PATH is not None:
            # Local per-data-root overrides live under .template_schemas
            candidate_dirs.append(Path(app_config.MONITOR_PATH) / ".template_schemas")
        if app_config.CUSTOM_SCHEMA_PATH is not None:
            candidate_dirs.append(Path(app_config.CUSTOM_SCHEMA_PATH))

        # Try overrides
        for base_dir in candidate_dirs:
            candidate = base_dir / schema_name
            if candidate.exists():
                print(f"Using schema override: {candidate}")
                return candidate

        # Fall back to packaged default
        packaged_schema_path = self.schema_base_path / schema_name
        print(f"Using packaged default schema: {packaged_schema_path}")
        return packaged_schema_path

    def load_schema(self, schema_path: Any) -> Optional[Dict[str, Any]]:
        """
        Load a JSON schema from a file with schema resolution support.

        Args:
            schema_path: Path to the schema file (can be full path or just filename)

        Returns:
            Loaded schema dictionary or None if failed
        """
        try:
            # Convert to Path object
            schema_path_obj = Path(schema_path)

            # If it's a relative path, use schema resolution
            if not schema_path_obj.is_absolute():
                # If the path already contains the schema base directory name, extract just the filename
                if str(schema_path_obj).startswith(app_config.SCHEMA_BASE_PATH):
                    schema_name = schema_path_obj.name
                else:
                    schema_name = schema_path_obj.name

                # Use schema resolution to find the appropriate schema file
                resolved_path = self.resolve_schema_path(schema_name)
            else:
                # Absolute path provided, use as-is
                resolved_path = schema_path_obj

            # Check cache first
            cache_key = str(resolved_path)
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]

            # Load schema from file
            if not resolved_path.exists():
                print(f"Schema file not found: {resolved_path}")
                allow_missing = app_config.allow_missing_schemas()
                if not allow_missing:
                    raise FileNotFoundError(f"Schema file not found: {resolved_path}")
                return None

            with open(resolved_path, "r") as f:
                schema: Dict[str, Any] = json.load(f)

            # Cache the loaded schema
            self._schema_cache[cache_key] = schema
            return schema

        except FileNotFoundError as e:
            error_msg = f"Schema file not found: {resolved_path}"
            allow_missing = app_config.allow_missing_schemas()
            if not allow_missing:
                raise SchemaNotFoundError(
                    schema_name=str(schema_path),
                    searched_paths=[str(resolved_path)],
                    cause=e
                )
            logger.warning(error_msg)
            return None
        except PermissionError as e:
            error_msg = f"Permission denied accessing schema: {resolved_path}"
            allow_missing = app_config.allow_missing_schemas()
            if not allow_missing:
                raise PermissionError(resolved_path, "read", e)
            logger.warning(error_msg)
            return None
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in schema file: {resolved_path}"
            allow_missing = app_config.allow_missing_schemas()
            if not allow_missing:
                raise SchemaError(error_msg, {"schema_path": str(resolved_path)}, e)
            logger.warning(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error loading schema from {resolved_path}"
            allow_missing = app_config.allow_missing_schemas()
            if not allow_missing:
                raise SchemaError(error_msg, {"schema_path": str(resolved_path)}, e)
            logger.warning(error_msg)
            return None

    def validate_json(
        self, data: Dict[str, Any], schema: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Validate JSON data against a schema using the jsonschema library.

        Args:
            data: JSON data to validate
            schema: Schema to validate against

        Returns:
            True if validation passes, False otherwise

        Raises:
            SchemaValidationError: If validation fails and strict mode is enabled
        """
        if schema is None:
            logger.warning("No schema provided for validation, assuming success.")
            return True

        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema library not available, skipping validation")
            return True

        try:
            # The core of the new validation logic
            validate(instance=data, schema=schema)
            return True
        except JSONSchemaValidationError as e:
            # Extract detailed validation errors
            validation_errors = []
            if hasattr(e, 'message'):
                validation_errors.append(e.message)
            if hasattr(e, 'path') and e.path:
                validation_errors.append(f"Path: {' -> '.join(str(p) for p in e.path)}")

            error_msg = f"Schema validation failed: {e.message if hasattr(e, 'message') else str(e)}"

            strict_validation = app_config.is_strict_validation()
            if strict_validation:
                raise SchemaValidationError(
                    error_msg,
                    validation_errors=validation_errors,
                    cause=e
                )

            logger.warning(f"Schema Validation Error: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error during validation: {str(e)}"

            strict_validation = app_config.is_strict_validation()
            if strict_validation:
                raise SchemaValidationError(error_msg, cause=e)

            logger.error(error_msg)
            return False

    def validate_with_schema_file(self, data: Dict[str, Any], schema_path: Any) -> bool:
        """
        Validate JSON data against a schema file.

        Args:
            data: JSON data to validate
            schema_path: Path to the schema file

        Returns:
            True if validation passes, False otherwise
        """
        schema = self.load_schema(schema_path)
        return self.validate_json(data, schema)

    def get_project_schema(self) -> Optional[Dict[str, Any]]:
        """Get the project descriptive schema."""
        return self.load_schema(app_config.PROJECT_SCHEMA_PATH)

    def get_project_admin_schema(self) -> Optional[Dict[str, Any]]:
        """Get the project administrative schema."""
        return self.load_schema(app_config.PROJECT_ADMIN_SCHEMA_PATH)

    def get_dataset_admin_schema(self) -> Optional[Dict[str, Any]]:
        """Get the dataset administrative schema."""
        return self.load_schema(app_config.DATASET_ADMIN_SCHEMA_PATH)

    def get_dataset_struct_schema(self) -> Optional[Dict[str, Any]]:
        """Get the dataset structural schema."""
        return self.load_schema(app_config.DATASET_STRUCT_SCHEMA_PATH)

    def get_experiment_contextual_schema(self) -> Optional[Dict[str, Any]]:
        """Get the experiment contextual schema."""
        return self.load_schema(app_config.EXPERIMENT_CONTEXTUAL_SCHEMA_PATH)

    def get_instrument_technical_schema(self) -> Optional[Dict[str, Any]]:
        """Get the instrument technical schema."""
        return self.load_schema(app_config.INSTRUMENT_TECHNICAL_SCHEMA_PATH)

    def get_complete_metadata_schema(self) -> Optional[Dict[str, Any]]:
        """Get the complete metadata schema."""
        return self.load_schema(app_config.COMPLETE_METADATA_SCHEMA_PATH)

    def validate_project_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate project descriptive metadata."""
        schema = self.get_project_schema()
        return self.validate_json(data, schema)

    def validate_project_admin_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate project administrative metadata."""
        schema = self.get_project_admin_schema()
        return self.validate_json(data, schema)

    def validate_dataset_admin_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate dataset administrative metadata."""
        schema = self.get_dataset_admin_schema()
        return self.validate_json(data, schema)

    def validate_dataset_struct_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate dataset structural metadata."""
        schema = self.get_dataset_struct_schema()
        return self.validate_json(data, schema)

    def validate_experiment_contextual_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate experiment contextual metadata."""
        schema = self.get_experiment_contextual_schema()
        return self.validate_json(data, schema)

    def validate_instrument_technical_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate instrument technical metadata."""
        schema = self.get_instrument_technical_schema()
        return self.validate_json(data, schema)

    def validate_complete_metadata(self, data: Dict[str, Any]) -> bool:
        """Validate complete metadata."""
        schema = self.get_complete_metadata_schema()
        return self.validate_json(data, schema)

    def clear_cache(self) -> None:
        """Clear the schema cache."""
        self._schema_cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the schema cache."""
        return {
            "cached_schemas": list(self._schema_cache.keys()),
            "cache_size": len(self._schema_cache),
            "schema_base_path": str(self.schema_base_path),
        }

    def get_schema_resolution_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get information about schema resolution for a specific schema.

        Args:
            schema_name: Name of the schema file

        Returns:
            Dictionary with resolution information
        """
        # Compute info for local override and custom path
        local_schema_path = None
        local_override_exists = False
        custom_schema_path = None
        custom_override_exists = False

        if app_config.MONITOR_PATH is not None:
            monitor_path = Path(app_config.MONITOR_PATH)
            local_schema_path = monitor_path / ".template_schemas" / schema_name
            local_override_exists = local_schema_path.exists()

        if app_config.CUSTOM_SCHEMA_PATH is not None:
            custom_schema_path = Path(app_config.CUSTOM_SCHEMA_PATH) / schema_name
            custom_override_exists = custom_schema_path.exists()

        packaged_schema_path = self.schema_base_path / schema_name

        # Determine resolution source
        if local_override_exists:
            resolution_source = "local_override"
        elif custom_override_exists:
            resolution_source = "custom_override"
        else:
            resolution_source = "packaged_default"

        return {
            "schema_name": schema_name,
            "local_override_path": (
                str(local_schema_path) if local_schema_path else "N/A"
            ),
            "local_override_exists": local_override_exists,
            "custom_override_path": (
                str(custom_schema_path) if custom_schema_path else "N/A"
            ),
            "custom_override_exists": custom_override_exists,
            "packaged_default_path": str(packaged_schema_path),
            "packaged_default_exists": packaged_schema_path.exists(),
            "resolved_path": str(self.resolve_schema_path(schema_name)),
            "resolution_source": resolution_source,
        }

    def get_contextual_template_schema(
        self, template_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load a specific contextual template schema.

        Args:
            template_type: The template type (e.g., 'microscopy_imaging', 'genomics_sequencing')

        Returns:
            The loaded schema dictionary, or None if not found
        """
        template_path = f"contextual/{template_type}.json"
        schema_path = self.resolve_schema_path(template_path)

        if not schema_path.exists():
            print(f"Contextual template schema not found: {schema_path}")
            return None

        return self.load_schema(schema_path)

    def list_available_schemas(self) -> Dict[str, Any]:
        """
        List all available schemas with their resolution information.

        Returns:
            Dictionary with schema availability information
        """
        schema_names = [
            "project_descriptive.json",
            "project_administrative_schema.json",
            "dataset_administrative_schema.json",
            "dataset_structural_schema.json",
            "experiment_contextual_schema.json",
            "instrument_technical_schema.json",
            "complete_metadata_schema.json",
        ]

        available_schemas = {}
        for schema_name in schema_names:
            available_schemas[schema_name] = self.get_schema_resolution_info(
                schema_name
            )

        return available_schemas


# Global instance for singleton pattern
_schema_manager: Optional[SchemaManager] = None


def get_schema_manager() -> SchemaManager:
    """Get the global schema manager instance.

    Returns:
        SchemaManager instance
    """
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaManager()
    return _schema_manager


# Convenience functions for direct access
def load_schema(schema_path: Any) -> Optional[Dict[str, Any]]:
    """Load a JSON schema from a file."""
    return get_schema_manager().load_schema(schema_path)


def validate_json(data: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> bool:
    """Validate a JSON object against a schema."""
    return get_schema_manager().validate_json(data, schema)


def resolve_schema_path(schema_name: str) -> Path:
    """Resolve schema path using the schema resolution principle."""
    return get_schema_manager().resolve_schema_path(schema_name)


def get_schema_resolution_info(schema_name: str) -> Dict[str, Any]:
    """Get information about schema resolution for a specific schema."""
    return get_schema_manager().get_schema_resolution_info(schema_name)


def list_available_schemas() -> Dict[str, Any]:
    """List all available schemas with their resolution information."""
    return get_schema_manager().list_available_schemas()
