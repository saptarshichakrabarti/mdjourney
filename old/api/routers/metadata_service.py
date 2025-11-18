"""
Metadata service for the FAIR Metadata Enrichment API.
Handles metadata-related business logic.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.models.pydantic_models import (
    ContextualTemplatePayload,
    FinalizePayload,
    MetadataFile,
    MetadataUpdatePayload,
    SchemaInfo,
)
from app.core.cache import get_metadata_cache, get_schema_cache
from app.core.config import DATASET_PREFIX, METADATA_SUBDIR, PROJECT_PREFIX, get_monitor_path
from app.core.security import InputValidator, PathSanitizer
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    MetadataGenerationError,
    MetadataValidationError,
    SchemaNotFoundError,
    PathNotFoundError,
    PermissionError,
    MDJourneyError,
    SecurityError,
    PathTraversalError,
    create_error_response,
)
from app.services.metadata_generator import get_metadata_generator
from app.services.async_schema_manager import get_async_schema_manager
from app.services.schema_manager import get_schema_manager, get_schema_resolution_info
from app.services.version_control import get_vc_manager

logger = logging.getLogger(__name__)


class MetadataService:
    def __init__(self, schema_manager: Optional[Any] = None, metadata_generator: Optional[Any] = None, vc_manager: Optional[Any] = None) -> None:
        self.monitor_path = get_monitor_path()
        self.metadata_cache = get_metadata_cache()
        self.schema_cache = get_schema_cache()

        if schema_manager is not None:
            self.schema_manager = schema_manager
        else:
            self.schema_manager = get_schema_manager()

        if metadata_generator is not None:
            self.metadata_generator = metadata_generator
        else:
            self.metadata_generator = get_metadata_generator()

        if vc_manager is not None:
            self.vc_manager = vc_manager
        else:
            self.vc_manager = get_vc_manager()

        self.async_schema_manager = get_async_schema_manager()

    async def get_project_metadata(self, project_id: str, metadata_type: str) -> MetadataFile:
        """Get the content of a specific metadata file for a project and the schema used to validate it."""
        # Find the project
        project_path = self._find_project(project_id)

        # Map metadata_type to file name
        metadata_mapping = {
            "project_descriptive": "project_descriptive.json",
            "project_administrative": "project_administrative.json",
        }

        if metadata_type not in metadata_mapping:
            raise ValueError(f"Unknown project metadata type: {metadata_type}")

        metadata_file = project_path / METADATA_SUBDIR / metadata_mapping[metadata_type]

        if not metadata_file.exists():
            raise ValueError(
                f"Project metadata file {metadata_type} not found for project {project_id}"
            )

        # Load metadata content
        with open(metadata_file, "r") as f:
            content = json.load(f)

        # Get schema information
        schema_mapping = {
            "project_descriptive": "project_descriptive.json",
            "project_administrative": "project_administrative_schema.json",
        }
        schema_name = schema_mapping[metadata_type]
        resolution_info = get_schema_resolution_info(schema_name)

        # Load the actual schema to get title and description
        schema = self.schema_manager.load_schema(schema_name)

        # Mark system-defined identifier fields as read-only in the schema so the frontend can render them as non-editable
        schema = self._with_readonly_identifiers(schema, metadata_type)
        schema_title = (
            schema.get("title", schema_name.replace(".json", ""))
            if schema
            else schema_name.replace(".json", "")
        )
        schema_description = schema.get("description", "") if schema else ""

        schema_info = SchemaInfo(
            schema_id=schema_name.replace(".json", ""),
            schema_title=schema_title,
            schema_description=schema_description,
            source=resolution_info.get("resolution_source", "default"),
        )

        return MetadataFile(
            content=content, schema_info=schema_info, schema_definition=schema or {}
        )

    def update_project_metadata(
        self, project_id: str, metadata_type: str, payload: MetadataUpdatePayload
    ) -> str:
        """Update and save a specific metadata file for a project."""
        # Find the project
        project_path = self._find_project(project_id)

        # Map metadata_type to file name
        metadata_mapping = {
            "project_descriptive": "project_descriptive.json",
            "project_administrative": "project_administrative.json",
        }

        if metadata_type not in metadata_mapping:
            raise ValueError(f"Unknown project metadata type: {metadata_type}")

        metadata_file = project_path / METADATA_SUBDIR / metadata_mapping[metadata_type]

        # Ensure metadata directory exists
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing content to preserve required/system fields
        existing_content = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    existing_content = json.load(f)
            except Exception:
                existing_content = {}

        # Merge existing with incoming updates (shallow) for validation
        merged_content: Dict[str, Any] = dict(existing_content)
        merged_content.update(payload.content or {})

        # Populate audit fields for project metadata prior to validation
        try:
            from app.utils.helpers import get_current_timestamp
        except Exception:
            from datetime import datetime, timezone

            def get_current_timestamp() -> str:
                return datetime.now(timezone.utc).isoformat()

        if metadata_type == "project_descriptive":
            if not merged_content.get("created_date"):
                merged_content["created_date"] = existing_content.get(
                    "created_date", get_current_timestamp()
                )
            if not merged_content.get("created_by"):
                merged_content["created_by"] = existing_content.get(
                    "created_by", "system"
                )
            merged_content["last_modified_date"] = get_current_timestamp()
            merged_content["last_modified_by"] = "system"
        elif metadata_type == "project_administrative":
            if not merged_content.get("created_date"):
                merged_content["created_date"] = existing_content.get(
                    "created_date", get_current_timestamp()
                )
            if not merged_content.get("created_by"):
                merged_content["created_by"] = existing_content.get(
                    "created_by", "system"
                )
            merged_content["last_modified_date"] = get_current_timestamp()
            merged_content["last_modified_by"] = "system"

        # Validate against schema
        schema_mapping = {
            "project_descriptive": "project_descriptive.json",
            "project_administrative": "project_administrative_schema.json",
        }
        schema_name = schema_mapping[metadata_type]
        schema = self.schema_manager.load_schema(schema_name)

        if schema and not self.schema_manager.validate_json(merged_content, schema):
            raise ValueError("Project metadata validation failed against schema")

        # Enforce system-defined identifier fields as non-editable by restoring existing values
        merged_content = self._enforce_system_identifiers(
            metadata_type, merged_content, existing_content
        )

        # Save the metadata
        logger.debug(f"Saving metadata to: {metadata_file}")
        with open(metadata_file, "w") as f:
            json.dump(merged_content, f, indent=2)
            f.flush()  # Ensure data is written to disk
            os.fsync(f.fileno())  # Force sync to disk
        logger.info(f"Metadata saved successfully to: {metadata_file}")

        # Commit changes
        try:
            self.vc_manager.commit_metadata_changes(
                f"Update {metadata_type} for project {project_id}", [str(metadata_file)]
            )
        except Exception as e:
            # Log the error but don't fail the operation
            logger.warning(f"Failed to commit metadata changes: {e}")

        return "Project metadata saved successfully."

    def get_metadata(self, dataset_id: str, metadata_type: str) -> MetadataFile:
        """Get the content of a specific metadata file and the schema used to validate it."""
        # Find the dataset
        dataset_path = self._find_dataset(dataset_id)

        # Map metadata_type to file name
        metadata_mapping = {
            "project_descriptive": "project_descriptive.json",
            "dataset_administrative": "dataset_administrative.json",
            "dataset_structural": "dataset_structural.json",
            "experiment_contextual": "experiment_contextual.json",
        }

        if metadata_type not in metadata_mapping:
            raise ValueError(f"Unknown metadata type: {metadata_type}")

        metadata_file = dataset_path / METADATA_SUBDIR / metadata_mapping[metadata_type]

        if not metadata_file.exists():
            raise ValueError(
                f"Metadata file {metadata_type} not found for dataset {dataset_id}"
            )

        # Load metadata content
        with open(metadata_file, "r") as f:
            content = json.load(f)

        # Backfill/migrate experiment contextual fields if needed
        if metadata_type == "experiment_contextual":
            try:
                changed = False
                run_id = content.get("experiment_identifier_run_id")
                template_type = content.get("experiment_template_type")
                # Derive template type from legacy run_id format: exp_{dataset}_{template}
                if (
                    not template_type
                    and isinstance(run_id, str)
                    and run_id.startswith("exp_")
                ):
                    parts = run_id.split("_")
                    if (
                        len(parts) >= 4
                    ):  # exp_d_dataset_template or exp_d_dataset_template_subtype
                        # Join the template parts (everything after the dataset part)
                        derived = "_".join(parts[3:])
                        content["experiment_template_type"] = derived
                        changed = True
                # Ensure experiment_name exists
                if "experiment_name" not in content:
                    content["experiment_name"] = ""
                    changed = True
                # Ensure run_id is a UUID
                import re as _re
                import uuid as _uuid

                uuid_like = (
                    isinstance(run_id, str)
                    and _re.fullmatch(r"[0-9a-fA-F\-]{36}", run_id) is not None
                )
                if not uuid_like:
                    content["experiment_identifier_run_id"] = str(_uuid.uuid4())
                    changed = True
                if changed:
                    with open(metadata_file, "w") as f2:
                        json.dump(content, f2, indent=2)
                        f2.flush()
                        os.fsync(f2.fileno())
            except Exception:
                pass

        # Get schema information
        schema_mapping = {
            "project_descriptive": "project_descriptive.json",
            "project_administrative": "project_administrative_schema.json",
            "dataset_administrative": "dataset_administrative_schema.json",
            "dataset_structural": "dataset_structural_schema.json",
            "experiment_contextual": "experiment_contextual_schema.json",
        }

        # For contextual metadata, use the specific template schema if available
        if metadata_type == "experiment_contextual":
            template_type = content.get("experiment_template_type")
            if template_type:
                # Try to load the specific template schema
                template_schema = self.schema_manager.get_contextual_template_schema(
                    template_type
                )
                if template_schema:
                    schema = template_schema
                    schema_name = f"contextual/{template_type}.json"
                    resolution_info = {"resolution_source": "packaged_default"}
                else:
                    # Fall back to base schema
                    schema_name = schema_mapping[metadata_type]
                    resolution_info = get_schema_resolution_info(schema_name)
                    schema = self.schema_manager.load_schema(schema_name)
            else:
                # No template type, use base schema
                schema_name = schema_mapping[metadata_type]
                resolution_info = get_schema_resolution_info(schema_name)
                schema = self.schema_manager.load_schema(schema_name)
        else:
            # Non-contextual metadata, use regular mapping
            schema_name = schema_mapping[metadata_type]
            resolution_info = get_schema_resolution_info(schema_name)
            schema = self.schema_manager.load_schema(schema_name)

        # Mark system-defined identifier fields as read-only in the schema so the frontend can render them as non-editable
        schema = self._with_readonly_identifiers(schema, metadata_type)
        schema_title = (
            schema.get("title", schema_name.replace(".json", ""))
            if schema
            else schema_name.replace(".json", "")
        )
        schema_description = schema.get("description", "") if schema else ""

        schema_info = SchemaInfo(
            schema_id=schema_name.replace(".json", ""),
            schema_title=schema_title,
            schema_description=schema_description,
            source=resolution_info.get("resolution_source", "default"),
        )

        return MetadataFile(
            content=content, schema_info=schema_info, schema_definition=schema or {}
        )

    def update_metadata(
        self, dataset_id: str, metadata_type: str, payload: MetadataUpdatePayload
    ) -> str:
        """Update and save a specific metadata file."""
        # Find the dataset
        dataset_path = self._find_dataset(dataset_id)

        # Map metadata_type to file name
        metadata_mapping = {
            "project_descriptive": "project_descriptive.json",
            "dataset_administrative": "dataset_administrative.json",
            "dataset_structural": "dataset_structural.json",
            "experiment_contextual": "experiment_contextual.json",
        }

        if metadata_type not in metadata_mapping:
            raise ValueError(f"Unknown metadata type: {metadata_type}")

        metadata_file = dataset_path / METADATA_SUBDIR / metadata_mapping[metadata_type]

        # Ensure metadata directory exists
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing content to preserve required/system fields
        existing_content: Dict[str, Any] = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    existing_content = json.load(f)
            except Exception:
                existing_content = {}

        # Merge existing with incoming updates (shallow) for validation
        merged_content: Dict[str, Any] = dict(existing_content)
        merged_content.update(payload.content or {})

        # Apply audit fields for contextual metadata prior to validation
        if metadata_type == "experiment_contextual":
            try:
                from app.utils.helpers import get_current_timestamp
            except Exception:
                from datetime import datetime, timezone

                def get_current_timestamp() -> str:
                    return datetime.now(timezone.utc).isoformat()

            # Preserve original created_* if present
            if not merged_content.get("created_date"):
                merged_content["created_date"] = existing_content.get(
                    "created_date", get_current_timestamp()
                )
            if not merged_content.get("created_by"):
                merged_content["created_by"] = existing_content.get(
                    "created_by", "system"
                )

            # Always update last_modified_*
            merged_content["last_modified_date"] = get_current_timestamp()
            merged_content["last_modified_by"] = "system"

        # Validate against schema (use template-specific schema for contextual metadata)
        schema_mapping = {
            "project_descriptive": "project_descriptive.json",
            "dataset_administrative": "dataset_administrative_schema.json",
            "dataset_structural": "dataset_structural_schema.json",
            "experiment_contextual": "experiment_contextual_schema.json",
        }
        if metadata_type == "experiment_contextual":
            # Prefer template-specific schema when available
            template_type = merged_content.get(
                "experiment_template_type"
            ) or existing_content.get("experiment_template_type")
            if template_type:
                schema = self.schema_manager.get_contextual_template_schema(
                    template_type
                )
                if schema is None:
                    # Fallback to base contextual schema if template-specific schema cannot be loaded
                    schema = self.schema_manager.load_schema(
                        schema_mapping[metadata_type]
                    )
            else:
                schema = self.schema_manager.load_schema(schema_mapping[metadata_type])
        else:
            schema = self.schema_manager.load_schema(schema_mapping[metadata_type])

        if schema and not self.schema_manager.validate_json(merged_content, schema):
            raise ValueError("Metadata validation failed against schema")

        # Enforce system-defined identifier fields as non-editable by restoring existing values
        merged_content = self._enforce_system_identifiers(
            metadata_type, merged_content, existing_content
        )

        # Save the metadata
        logger.debug(f"Saving metadata to: {metadata_file}")
        with open(metadata_file, "w") as f:
            json.dump(merged_content, f, indent=2)
            f.flush()  # Ensure data is written to disk
            os.fsync(f.fileno())  # Force sync to disk
        logger.info(f"Metadata saved successfully to: {metadata_file}")

        # Commit changes
        try:
            self.vc_manager.commit_metadata_changes(
                f"Update {metadata_type} for dataset {dataset_id}", [str(metadata_file)]
            )
        except Exception as e:
            # Log the error but don't fail the operation
            logger.warning(f"Failed to commit metadata changes: {e}")

        return "Metadata saved successfully."

    def create_contextual_template(
        self, dataset_id: str, payload: ContextualTemplatePayload
    ) -> str:
        """Create a new experiment contextual metadata template."""
        try:
            # Find the dataset
            dataset_path = self._find_dataset(dataset_id)

            # Generate experiment ID (UUID) and use payload.schema_id as template type
            import uuid as _uuid
            experiment_id = str(_uuid.uuid4())

            # Use the metadata generator to create the contextual template
            # If schema_id is None, template_type will be None and it will use the default schema
            template_file = self.metadata_generator.create_experiment_contextual_template(
                str(dataset_path), experiment_id, template_type=payload.schema_id
            )

            schema_type = payload.schema_id if payload.schema_id else "default"
            return f"Contextual template created successfully at {template_file} using {schema_type} schema"

        except (ResourceNotFoundError, SchemaNotFoundError, MetadataGenerationError, MetadataValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise MDJourneyError(
                f"Unexpected error creating contextual template for dataset {dataset_id}",
                {"dataset_id": dataset_id, "schema_id": payload.schema_id},
                e
            )

    def finalize_dataset(self, dataset_id: str, payload: FinalizePayload) -> str:
        """Finalize a dataset and generate its V2 complete metadata."""
        # Find the dataset
        dataset_path = self._find_dataset(dataset_id)

        # Check if contextual metadata is complete
        is_complete, experiment_id = (
            self.metadata_generator.check_contextual_metadata_completion(
                str(dataset_path)
            )
        )

        if not is_complete:
            raise ValueError(
                f"Contextual metadata is not complete for dataset {dataset_id}"
            )

        if not experiment_id:
            raise ValueError("No experiment ID found in contextual metadata")

        # Use the metadata generator to create the complete metadata file
        try:
            v2_file = self.metadata_generator.generate_complete_metadata_file(
                str(dataset_path), experiment_id
            )

            if v2_file:
                return f"Dataset finalized successfully. V2 metadata saved to {v2_file}"
            else:
                raise ValueError("Failed to generate complete metadata file")

        except Exception as e:
            raise ValueError(f"Failed to finalize dataset: {e}")

    def _find_project(self, project_id: str) -> Path:
        """Find a project by ID with proper path validation."""
        try:
            # Validate the project ID input
            validated_project_id = InputValidator.validate_id(project_id, "Project ID")

            # Construct path safely
            project_path = self.monitor_path / validated_project_id

            # Validate that the path is within the monitor path
            validated_path = PathSanitizer.validate_path_access(project_path, self.monitor_path)

            # Check if project exists and meets criteria
            if (
                validated_path.exists()
                and validated_path.is_dir()
                and validated_project_id.startswith(PROJECT_PREFIX)
            ):
                return validated_path

            raise ValueError(f"Project {validated_project_id} not found")

        except (SecurityError, PathTraversalError) as e:
            raise SecurityError(f"Invalid project path: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Project {project_id} not found")

    def _find_dataset(self, dataset_id: str) -> Path:
        """Find a dataset by ID with proper path validation."""
        try:
            # Validate the dataset ID input
            validated_dataset_id = InputValidator.validate_id(dataset_id, "Dataset ID")

            # Search through projects safely
            for project_dir in self.monitor_path.iterdir():
                if project_dir.is_dir() and project_dir.name.startswith(PROJECT_PREFIX):
                    # Construct dataset path safely
                    dataset_path = project_dir / validated_dataset_id

                    # Validate that the path is within the project directory
                    try:
                        validated_path = PathSanitizer.validate_path_access(dataset_path, project_dir)

                        if (validated_path.exists()
                            and validated_path.is_dir()
                            and validated_dataset_id.startswith(DATASET_PREFIX)):
                            return validated_path

                    except (SecurityError, PathTraversalError):
                        # Skip this path if it's invalid
                        continue

            raise ResourceNotFoundError("dataset", validated_dataset_id)

        except (SecurityError, PathTraversalError) as e:
            raise SecurityError(f"Invalid dataset path: {str(e)}")
        except PermissionError as e:
            raise PermissionError(self.monitor_path, "read", e)
        except Exception as e:
            raise MDJourneyError(
                f"Error searching for dataset {dataset_id}",
                {"dataset_id": dataset_id, "monitor_path": str(self.monitor_path)},
                e
            )

    # --------------------
    # Internal helpers
    # --------------------

    def _with_readonly_identifiers(
        self, schema: Optional[Dict[str, Any]], metadata_type: str
    ) -> Dict[str, Any]:
        """Return a copy of schema with system identifier fields marked as readOnly."""
        if not schema:
            return {}
        try:
            schema_copy = json.loads(json.dumps(schema))  # deep copy
        except Exception:
            schema_copy = dict(schema)

        protected = self._protected_identifier_fields(metadata_type)
        props = schema_copy.get("properties", {})
        for field in protected:
            if field in props and isinstance(props[field], dict):
                props[field]["readOnly"] = True
        schema_copy["properties"] = props
        return schema_copy

    def _protected_identifier_fields(self, metadata_type: str) -> List[str]:
        """List of system-defined identifier fields per metadata type."""
        mapping = {
            "project_descriptive": ["project_identifier"],
            "dataset_structural": [
                "dataset_identifier",
                "associated_project_identifier",
            ],
            "dataset_administrative": [
                "dataset_identifier_link",
                "associated_project_identifier",
            ],
            "experiment_contextual": [
                "experiment_template_type",
                "experiment_identifier_run_id",
                "dataset_identifier_link",
            ],
        }
        return mapping.get(metadata_type, [])

    def _enforce_system_identifiers(
        self,
        metadata_type: str,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ensure system identifier fields cannot be overwritten by client updates.

        If an existing file has values for protected fields, restore them.
        """
        # Shallow copy
        merged = dict(new_content or {})
        for field in self._protected_identifier_fields(metadata_type):
            if field in existing_content:
                merged[field] = existing_content[field]
        return merged
