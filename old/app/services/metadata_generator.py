"""
Metadata generation module for the FAIR metadata automation system.
Handles creation and management of various metadata files.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.config import DATASET_PREFIX, PROJECT_PREFIX, get_monitor_path
from app.core.exceptions import (
    MetadataGenerationError,
    MetadataValidationError,
    SchemaNotFoundError,
    PathNotFoundError,
    PermissionError,
    VersionControlError,
    MDJourneyError,
)
from app.services.schema_manager import get_schema_manager
from app.services.version_control import get_vc_manager
from app.utils.helpers import (
    ensure_directory_exists,
    get_current_date,
    get_current_timestamp,
)

logger = logging.getLogger(__name__)


class MetadataGenerator:
    """Handles generation of all metadata files for the FAIR system based on schema templates."""

    def __init__(self) -> None:
        """Initialize the metadata generator."""
        self.schema_manager = get_schema_manager()
        self.vc_manager = get_vc_manager()

    def _strip_prefix_from_name(self, folder_name: str, prefix: str) -> str:
        """
        Strip prefix from folder name to get clean name for metadata.

        Args:
            folder_name: The folder name (e.g., "p_MyProject" or "d_MyDataset")
            prefix: The prefix to strip (e.g., "p_" or "d_")

        Returns:
            Clean name without prefix (e.g., "MyProject" or "MyDataset")
        """
        if folder_name.startswith(prefix):
            return folder_name[len(prefix) :]
        return folder_name

    def _create_metadata_from_schema(
        self, schema: Dict[str, Any], auto_fill_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create metadata structure from schema template with auto-filled fields.

        Args:
            schema: The JSON schema template
            auto_fill_fields: Fields to auto-fill (IDs, timestamps, etc.)

        Returns:
            Metadata dictionary with correct structure
        """
        metadata = {}
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type")

            # Auto-fill system fields
            if field_name in auto_fill_fields:
                metadata[field_name] = auto_fill_fields[field_name]
                continue

            # Handle different field types
            if field_type == "string":
                # Check if this is a const field
                if "const" in field_schema:
                    # Use the const value
                    metadata[field_name] = field_schema["const"]
                # Check if this is an enum field
                elif "enum" in field_schema:
                    # Use the first enum value as default
                    metadata[field_name] = field_schema["enum"][0]
                # Check if this is a pattern field (like ORCID, email, etc.)
                elif "pattern" in field_schema or "format" in field_schema:
                    # For required pattern fields, provide placeholder values
                    if field_name in ["orcid"]:
                        metadata[field_name] = "https://orcid.org/0000-0000-0000-0000"
                    elif field_name in ["email"]:
                        metadata[field_name] = "placeholder@example.com"
                    else:
                        metadata[field_name] = "To be filled"
                else:
                    metadata[field_name] = "To be filled"
            elif field_type == "integer":
                metadata[field_name] = 0
            elif field_type == "number":
                metadata[field_name] = 0.0
            elif field_type == "boolean":
                metadata[field_name] = False
            elif field_type == "array":
                metadata[field_name] = []
            elif field_type == "object":
                # Recursively handle nested objects
                nested_props = field_schema.get("properties", {})
                nested_metadata = {}
                for nested_field, nested_schema in nested_props.items():
                    nested_type = nested_schema.get("type")
                    if nested_type == "string":
                        # Check if this is a const field
                        if "const" in nested_schema:
                            nested_metadata[nested_field] = nested_schema["const"]
                        # Check if this is an enum field
                        elif "enum" in nested_schema:
                            nested_metadata[nested_field] = nested_schema["enum"][0]
                        # Check if this is a pattern field (like ORCID, email, etc.)
                        elif "pattern" in nested_schema or "format" in nested_schema:
                            # For required pattern fields, provide placeholder values
                            if nested_field in ["orcid"]:
                                nested_metadata[nested_field] = (
                                    "https://orcid.org/0000-0000-0000-0000"
                                )
                            elif nested_field in ["email"]:
                                nested_metadata[nested_field] = (
                                    "placeholder@example.com"
                                )
                            else:
                                nested_metadata[nested_field] = "To be filled"
                        else:
                            nested_metadata[nested_field] = "To be filled"
                    elif nested_type == "integer":
                        nested_metadata[nested_field] = 0
                    elif nested_type == "number":
                        nested_metadata[nested_field] = 0.0
                    elif nested_type == "boolean":
                        nested_metadata[nested_field] = False
                    elif nested_type == "array":
                        nested_metadata[nested_field] = []
                    else:
                        nested_metadata[nested_field] = "To be filled"
                metadata[field_name] = nested_metadata
            else:
                metadata[field_name] = "To be filled"

        return metadata

    def generate_project_file(self, project_path: str) -> Optional[str]:
        """
        Generate the project_descriptive.json file using the schema template.

        Args:
            project_path: Path to the project directory

        Returns:
            Path to the generated project file, or None if failed
        """
        try:
            # Normalize to absolute path to avoid CWD-dependent writes
            project_path = os.path.abspath(project_path)
            # Create .metadata folder for project
            metadata_dir = os.path.join(project_path, ".metadata")
            ensure_directory_exists(Path(metadata_dir))

            project_name = os.path.basename(project_path)
            clean_project_name = self._strip_prefix_from_name(
                project_name, PROJECT_PREFIX
            )
            project_id = str(uuid.uuid4())

            # Load the project schema template
            project_schema = self.schema_manager.get_project_schema()
            if not project_schema:
                print("Failed to load project schema template")
                return None

            # Auto-fill system fields
            auto_fill_fields = {
                "project_identifier": project_id,
                "project_title": clean_project_name,
                "created_by": "system",
                "created_date": get_current_timestamp(),
                "last_modified_by": "system",
                "last_modified_date": get_current_timestamp(),
            }

            # Create metadata structure from schema
            project_data = self._create_metadata_from_schema(
                project_schema, auto_fill_fields
            )

            project_filepath = os.path.join(metadata_dir, "project_descriptive.json")

            if self.schema_manager.validate_json(project_data, project_schema):
                with open(project_filepath, "w") as f:
                    json.dump(project_data, f, indent=4)
                print(f"Generated project file: {project_filepath}")

                # Generate project administrative metadata
                project_admin_filepath = self._generate_project_admin_file(
                    project_path, project_id, metadata_dir
                )
                if project_admin_filepath:
                    print(f"Generated project administrative file: {project_admin_filepath}")

                # Commit metadata changes to Git
                try:
                    self.vc_manager.commit_metadata_changes(
                        f"Create project: {clean_project_name}"
                    )
                except Exception as e:
                    print(f"Warning: Could not commit version control changes: {e}")

                return project_filepath
            else:
                print("Failed to generate project file due to validation errors")
                return None

        except Exception as e:
            print(f"Error generating project file: {e}")
            return None

    def _generate_project_admin_file(
        self, project_path: str, project_id: str, metadata_dir: str
    ) -> Optional[str]:
        """
        Generate the project_administrative.json file using the schema template.

        Args:
            project_path: Path to the project directory
            project_id: UUID of the project
            metadata_dir: Path to the .metadata directory

        Returns:
            Path to the generated project administrative file, or None if failed
        """
        try:
            # Load the project administrative schema template
            project_admin_schema = self.schema_manager.get_project_admin_schema()
            if not project_admin_schema:
                print("Failed to load project administrative schema template")
                return None

            # Auto-fill system fields
            auto_fill_fields = {
                "project_identifier_link": project_id,
                "created_by": "system",
                "created_date": get_current_timestamp(),
                "last_modified_by": "system",
                "last_modified_date": get_current_timestamp(),
            }

            # Create metadata structure from schema
            project_admin_data = self._create_metadata_from_schema(
                project_admin_schema, auto_fill_fields
            )

            project_admin_filepath = os.path.join(metadata_dir, "project_administrative.json")

            if self.schema_manager.validate_json(project_admin_data, project_admin_schema):
                with open(project_admin_filepath, "w") as f:
                    json.dump(project_admin_data, f, indent=4)
                print(f"Generated project administrative file: {project_admin_filepath}")
                return project_admin_filepath
            else:
                print("Failed to generate project administrative file due to validation errors")
                return None

        except Exception as e:
            print(f"Error generating project administrative file: {e}")
            return None

    def _load_project_admin_metadata(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load project administrative metadata for the given project ID.

        Args:
            project_id: UUID of the project

        Returns:
            Project administrative metadata dictionary or None if not found
        """
        try:
            # Find the project directory by scanning for the project_id
            monitor_path = Path(get_monitor_path())
            if not monitor_path.exists():
                return None

            for project_dir in monitor_path.iterdir():
                if not project_dir.is_dir() or not project_dir.name.startswith(PROJECT_PREFIX):
                    continue

                # Check if this project has the matching project_id
                project_metadata_path = project_dir / ".metadata" / "project_descriptive.json"
                if project_metadata_path.exists():
                    try:
                        with open(project_metadata_path, "r") as f:
                            project_data = json.load(f)
                            if project_data.get("project_identifier") == project_id:
                                # Found the project, now load its administrative metadata
                                project_admin_path = project_dir / ".metadata" / "project_administrative.json"
                                if project_admin_path.exists():
                                    with open(project_admin_path, "r") as f:
                                        return json.load(f)
                                break
                    except Exception as e:
                        print(f"Error reading project metadata: {e}")
                        continue

            return None

        except Exception as e:
            print(f"Error loading project administrative metadata: {e}")
            return None

    def _extract_dataset_fields_from_project_admin(self, project_admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant fields from project administrative metadata for dataset use.

        Args:
            project_admin_data: Project administrative metadata dictionary

        Returns:
            Dictionary of fields to copy to dataset administrative metadata
        """
        # Map project admin fields to dataset admin fields
        field_mapping = {
            "data_steward_contact_person": "data_steward_contact_person",
            "default_license": "license",
            "default_access_level": "access_level",
            "default_access_conditions_contact": "access_conditions_contact",
            "default_embargo_end_date": "embargo_end_date",
            "project_ethics_approval_references": "ethics_approval_references",
            "project_consent_framework_summary": "consent_framework_summary",
            "default_data_sensitivity_classification": "data_sensitivity_classification",
            "default_anonymization_method": "anonymization_method",
            "project_data_retention_schedule": "data_retention_schedule",
            "project_citation_template": "recommended_citation",
            "project_documentation_link": "link_to_documentation",
            "project_preservation_location": "preservation_location",
        }

        extracted_fields = {}
        for project_field, dataset_field in field_mapping.items():
            if project_field in project_admin_data and project_admin_data[project_field] is not None:
                extracted_fields[dataset_field] = project_admin_data[project_field]

        return extracted_fields

    def generate_dataset_files(
        self, dataset_path: str, project_id: str
    ) -> Dict[str, Optional[str]]:
        """
        Generate dataset_administrative.json and dataset_structural.json files using schema templates.

        Args:
            dataset_path: Path to the dataset directory
            project_id: UUID of the associated project

        Returns:
            Dictionary with paths to generated files (admin_file, struct_file)
        """
        try:
            # Normalize to absolute path to avoid CWD-dependent writes
            dataset_path = os.path.abspath(dataset_path)
            # Create .metadata folder for dataset
            metadata_dir = os.path.join(dataset_path, ".metadata")
            ensure_directory_exists(Path(metadata_dir))

            dataset_name = os.path.basename(dataset_path)
            clean_dataset_name = self._strip_prefix_from_name(
                dataset_name, DATASET_PREFIX
            )
            dataset_id = str(uuid.uuid4())

            # Generate dataset_administrative.json
            admin_schema = self.schema_manager.get_dataset_admin_schema()
            if not admin_schema:
                print("Failed to load dataset administrative schema template")
                return {"admin_file": None, "struct_file": None}

            admin_auto_fill_fields = {
                "dataset_identifier_link": dataset_id,
                "created_by": "system",
                "created_date": get_current_timestamp(),
                "last_modified_by": "system",
                "last_modified_date": get_current_timestamp(),
            }

            # Load project administrative metadata to copy defaults
            project_admin_data = self._load_project_admin_metadata(project_id)
            if project_admin_data:
                # Copy relevant fields from project administrative metadata
                admin_auto_fill_fields.update(self._extract_dataset_fields_from_project_admin(project_admin_data))

            admin_data = self._create_metadata_from_schema(
                admin_schema, admin_auto_fill_fields
            )

            admin_filepath: Optional[str] = os.path.join(metadata_dir, "dataset_administrative.json")

            if self.schema_manager.validate_json(admin_data, admin_schema) and admin_filepath:
                with open(admin_filepath, "w") as f:
                    json.dump(admin_data, f, indent=4)
                print(f"Generated dataset administrative file: {admin_filepath}")
            else:
                print(
                    "Failed to generate dataset administrative file due to validation errors"
                )
                admin_filepath = None

            # Generate dataset_structural.json
            struct_schema = self.schema_manager.get_dataset_struct_schema()
            if not struct_schema:
                print("Failed to load dataset structural schema template")
                return {"admin_file": admin_filepath, "struct_file": None}

            struct_auto_fill_fields = {
                "dataset_identifier": dataset_id,
                "dataset_title": clean_dataset_name,
                "associated_project_identifier": project_id,
                "created_by": "system",
                "created_date": get_current_timestamp(),
                "last_modified_by": "system",
                "last_modified_date": get_current_timestamp(),
            }

            struct_data = self._create_metadata_from_schema(
                struct_schema, struct_auto_fill_fields
            )

            struct_filepath: Optional[str] = os.path.join(metadata_dir, "dataset_structural.json")

            if self.schema_manager.validate_json(struct_data, struct_schema) and struct_filepath:
                with open(struct_filepath, "w") as f:
                    json.dump(struct_data, f, indent=4)
                print(f"Generated dataset structural file: {struct_filepath}")
            else:
                print(
                    "Failed to generate dataset structural file due to validation errors"
                )
                struct_filepath = None

            # Commit metadata changes to Git
            try:
                self.vc_manager.commit_metadata_changes(
                    f"Create dataset: {clean_dataset_name}"
                )
            except Exception as e:
                print(f"Warning: Could not commit version control changes: {e}")

            return {
                "admin_file": admin_filepath,
                "struct_file": struct_filepath,
            }

        except Exception as e:
            print(f"Error generating dataset files: {e}")
            return {"admin_file": None, "struct_file": None}

    def create_experiment_contextual_template(
        self,
        dataset_path: str,
        experiment_id: Optional[str] = None,
        template_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create the experiment_contextual.json template file using the schema template.

        Args:
            dataset_path: Path to the dataset directory
            experiment_id: Optional experiment ID (auto-generated if None)

        Returns:
            Path to the generated template file, or None if failed
        """
        try:
            # Normalize to absolute path to avoid CWD-dependent writes
            dataset_path = os.path.abspath(dataset_path)
            # Create .metadata folder for dataset if it doesn't exist
            metadata_dir = os.path.join(dataset_path, ".metadata")
            ensure_directory_exists(Path(metadata_dir))

            if not experiment_id:
                experiment_id = str(uuid.uuid4())

            # Load the specific contextual template schema if template_type is provided
            if template_type:
                try:
                    contextual_schema = self.schema_manager.get_contextual_template_schema(
                        template_type
                    )
                    if not contextual_schema:
                        raise SchemaNotFoundError(
                            schema_name=template_type,
                            searched_paths=[f"contextual/{template_type}.json"]
                        )
                except SchemaNotFoundError:
                    logger.warning(f"Contextual template schema '{template_type}' not found, falling back to base schema")
                    # Fall back to base schema
                    contextual_schema = (
                        self.schema_manager.get_experiment_contextual_schema()
                    )
            else:
                # Use base schema if no template_type specified
                contextual_schema = (
                    self.schema_manager.get_experiment_contextual_schema()
                )

            if not contextual_schema:
                raise SchemaNotFoundError(
                    schema_name="experiment_contextual_schema",
                    searched_paths=["experiment_contextual_schema.json"]
                )

            # Auto-fill system fields
            # Check which identifier field the schema uses
            schema_properties = contextual_schema.get("properties", {})
            experiment_id_field = None
            if "experiment_identifier_run_id" in schema_properties:
                experiment_id_field = "experiment_identifier_run_id"
            elif "experiment_identifier_object_id" in schema_properties:
                experiment_id_field = "experiment_identifier_object_id"

            # Check if experiment_template_type has a const value
            template_type_value = template_type or "unknown_template"
            if "experiment_template_type" in schema_properties:
                const_value = schema_properties["experiment_template_type"].get("const")
                if const_value:
                    template_type_value = const_value

            auto_fill_fields = {
                "experiment_template_type": template_type_value,
                "created_by": "system",
                "created_date": get_current_timestamp(),
                "last_modified_by": "system",
                "last_modified_date": get_current_timestamp(),
            }

            # Add the experiment ID field if found
            if experiment_id_field:
                auto_fill_fields[experiment_id_field] = experiment_id

            # Create metadata structure from schema
            contextual_data = self._create_metadata_from_schema(
                contextual_schema, auto_fill_fields
            )
            # Ensure experiment_name field exists and is empty by default
            if "experiment_name" not in contextual_data:
                contextual_data["experiment_name"] = ""

            # Auto-fill dataset_identifier_link from dataset_structural if available
            try:
                struct_file = os.path.join(
                    dataset_path, ".metadata", "dataset_structural.json"
                )
                if os.path.exists(struct_file):
                    with open(struct_file, "r") as sf:
                        struct_data = json.load(sf)
                        ds_id = struct_data.get("dataset_identifier")
                        if ds_id:
                            contextual_data["dataset_identifier_link"] = ds_id
            except Exception as e:
                # Non-fatal; proceed without linking if read fails
                logger.warning(f"Could not auto-fill dataset_identifier_link: {e}")

            contextual_filepath = os.path.join(
                metadata_dir, "experiment_contextual.json"
            )

            # Validate the generated data
            if not self.schema_manager.validate_json(contextual_data, contextual_schema):
                raise MetadataValidationError(
                    "Generated contextual template failed validation",
                    metadata_file=contextual_filepath,
                    validation_errors=["Schema validation failed"]
                )

            # Write the metadata file
            try:
                with open(contextual_filepath, "w") as f:
                    json.dump(contextual_data, f, indent=4)
                logger.info(f"Generated experiment contextual template: {contextual_filepath}")
            except PermissionError as e:
                raise PermissionError(contextual_filepath, "write", e)
            except Exception as e:
                raise MetadataGenerationError(
                    f"Failed to write contextual template to {contextual_filepath}",
                    metadata_type="experiment_contextual",
                    target_path=contextual_filepath,
                    cause=e
                )

            # Commit metadata changes to Git
            try:
                self.vc_manager.commit_metadata_changes(
                    f"Create experiment contextual template: {experiment_id}"
                )
            except Exception as e:
                logger.warning(f"Could not commit version control changes: {e}")
                # Don't fail the entire operation for git commit issues

            return contextual_filepath

        except (SchemaNotFoundError, MetadataValidationError, PermissionError, MetadataGenerationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise MetadataGenerationError(
                f"Unexpected error generating experiment contextual template",
                metadata_type="experiment_contextual",
                target_path=dataset_path,
                cause=e
            )

    def generate_complete_metadata_file(
        self, dataset_path: str, experiment_id: str
    ) -> Optional[str]:
        """
        Generate the complete metadata file (V2) when contextual metadata is complete.

        Args:
            dataset_path: Path to the dataset directory
            experiment_id: The experiment ID

        Returns:
            Path to the generated complete metadata file, or None if failed
        """
        try:
            # Normalize to absolute path to avoid CWD-dependent writes
            dataset_path = os.path.abspath(dataset_path)
            # Create .metadata folder for dataset if it doesn't exist
            metadata_dir = os.path.join(dataset_path, ".metadata")
            ensure_directory_exists(Path(metadata_dir))

            # Load existing metadata files
            # Project files are in the project's metadata directory
            project_path = os.path.dirname(dataset_path)
            project_file = os.path.join(
                project_path, ".metadata", "project_descriptive.json"
            )
            project_admin_file = os.path.join(
                project_path, ".metadata", "project_administrative.json"
            )
            admin_file = os.path.join(metadata_dir, "dataset_administrative.json")
            struct_file = os.path.join(metadata_dir, "dataset_structural.json")
            contextual_file = os.path.join(metadata_dir, "experiment_contextual.json")

            # Check if all required files exist
            required_files = [project_file, project_admin_file, admin_file, struct_file, contextual_file]
            for file_path in required_files:
                if not os.path.exists(file_path):
                    print(f"Required metadata file not found: {file_path}")
                    return None

            # Load and combine metadata
            complete_data: Dict[str, Any] = {
                "version": "2.0",
                "experiment_identifier": experiment_id,
                "metadata_components": {
                    "project_descriptive": {},
                    "project_administrative": {},
                    "dataset_administrative": {},
                    "dataset_structural": {},
                    "experiment_contextual": {},
                },
                "metadata_relationships": {
                    "project_to_dataset": "one_to_many",
                    "dataset_to_experiment": "one_to_many",
                    "experiment_to_data_files": "one_to_many",
                },
                "metadata_validation": {
                    "schema_compliance": True,
                    "completeness_score": 0.0,
                    "quality_score": 0.0,
                },
                "metadata_provenance": {
                    "generated_by": "FAIR Metadata System",
                    "generation_date": get_current_timestamp(),
                    "last_validation_date": get_current_timestamp(),
                },
            }

            # Load individual metadata components
            try:
                with open(project_file, "r") as f:
                    complete_data["metadata_components"]["project_descriptive"] = (
                        json.load(f)
                    )
                with open(project_admin_file, "r") as f:
                    complete_data["metadata_components"]["project_administrative"] = (
                        json.load(f)
                    )
                with open(admin_file, "r") as f:
                    complete_data["metadata_components"]["dataset_administrative"] = (
                        json.load(f)
                    )
                with open(struct_file, "r") as f:
                    complete_data["metadata_components"]["dataset_structural"] = (
                        json.load(f)
                    )
                with open(contextual_file, "r") as f:
                    complete_data["metadata_components"]["experiment_contextual"] = (
                        json.load(f)
                    )
            except Exception as e:
                print(f"Error loading metadata components: {e}")
                return None

            # Calculate completeness and quality scores
            completeness_score = self._calculate_completeness_score(complete_data)
            quality_score = self._calculate_quality_score(complete_data)

            complete_data["metadata_validation"][
                "completeness_score"
            ] = completeness_score
            complete_data["metadata_validation"]["quality_score"] = quality_score

            # Generate complete metadata file
            complete_filepath = os.path.join(metadata_dir, "complete_metadata.json")
            complete_schema = self.schema_manager.get_complete_metadata_schema()

            if self.schema_manager.validate_json(complete_data, complete_schema):
                with open(complete_filepath, "w") as f:
                    json.dump(complete_data, f, indent=4)
                print(f"Generated complete metadata file: {complete_filepath}")

                # Commit metadata changes to Git
                try:
                    self.vc_manager.commit_metadata_changes(
                        f"Generate complete metadata: {experiment_id}"
                    )
                except Exception as e:
                    print(f"Warning: Could not commit version control changes: {e}")

                return complete_filepath
            else:
                print(
                    "Failed to generate complete metadata file due to validation errors"
                )
                return None

        except Exception as e:
            print(f"Error generating complete metadata file: {e}")
            return None

    def check_contextual_metadata_completion(
        self, dataset_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if contextual metadata is complete and ready for V2 generation.

        Args:
            dataset_path: Path to the dataset directory

        Returns:
            Tuple of (is_complete, experiment_id)
        """
        try:
            contextual_file = os.path.join(
                dataset_path, ".metadata", "experiment_contextual.json"
            )

            if not os.path.exists(contextual_file):
                return False, None

            with open(contextual_file, "r") as f:
                contextual_data = json.load(f)

            experiment_id = contextual_data.get("experiment_identifier_run_id")

            # Determine completion based on schema-required fields,
            # but ignore audit/template fields for backward compatibility
            try:
                # Prefer the template-specific schema if available
                template_type = contextual_data.get("experiment_template_type")
                if template_type:
                    schema = self.schema_manager.get_contextual_template_schema(
                        template_type
                    )
                    if not schema:
                        schema = self.schema_manager.get_experiment_contextual_schema()
                else:
                    schema = self.schema_manager.get_experiment_contextual_schema()

                required_fields = set(schema.get("required", [])) if schema else set()
            except Exception:
                required_fields = set(["experiment_identifier_run_id"])  # fallback

            # Ignore audit and template fields in completeness gate
            ignore_fields = {
                "created_by",
                "created_date",
                "last_modified_by",
                "last_modified_date",
                "experiment_template_type",
            }
            gated_required = [f for f in required_fields if f not in ignore_fields]

            for field in gated_required:
                value = contextual_data.get(field)
                # Consider empty string or placeholder as incomplete for required fields
                if value is None:
                    return False, None
                if isinstance(value, str) and (
                    value.strip() == "" or value == "To be filled"
                ):
                    return False, None

            # If present, ensure dataset_identifier_link is populated; try to auto-fill
            if not contextual_data.get("dataset_identifier_link"):
                try:
                    struct_file = os.path.join(
                        dataset_path, ".metadata", "dataset_structural.json"
                    )
                    if os.path.exists(struct_file):
                        with open(struct_file, "r") as sf:
                            struct_data = json.load(sf)
                            ds_id = struct_data.get("dataset_identifier")
                            if ds_id:
                                contextual_data["dataset_identifier_link"] = ds_id
                                # Persist the fix so subsequent checks pass
                                with open(contextual_file, "w") as f:
                                    json.dump(contextual_data, f, indent=4)
                except Exception:
                    pass

            # Optional add-on: scan for placeholders in non-required fields but do not block
            # (Kept minimal to satisfy legacy expectations if needed)
            return True, experiment_id

        except Exception as e:
            print(f"Error checking contextual metadata completion: {e}")
            return False, None

    def _calculate_completeness_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate completeness score for metadata."""
        # Simple implementation - count non-empty fields
        total_fields = 0
        filled_fields = 0

        def count_fields(data: Any) -> None:
            nonlocal total_fields, filled_fields
            if isinstance(data, dict):
                for key, value in data.items():
                    total_fields += 1
                    if isinstance(value, (dict, list)):
                        count_fields(value)
                    elif value and value != "To be filled":
                        filled_fields += 1
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        count_fields(item)
                    else:
                        total_fields += 1
                        if item and item != "To be filled":
                            filled_fields += 1

        count_fields(metadata)
        return filled_fields / total_fields if total_fields > 0 else 0.0

    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate quality score for metadata."""
        # Simple implementation - based on schema validation and completeness
        completeness_score = self._calculate_completeness_score(metadata)
        schema_valid = metadata.get("metadata_validation", {}).get(
            "schema_compliance", False
        )

        if schema_valid:
            return completeness_score * 0.8 + 0.2  # Bonus for schema compliance
        else:
            return completeness_score * 0.6  # Penalty for schema violations


# Global instance for singleton pattern
_metadata_generator: Optional[MetadataGenerator] = None


def get_metadata_generator() -> MetadataGenerator:
    """Get the global metadata generator instance.

    Returns:
        MetadataGenerator instance
    """
    global _metadata_generator
    if _metadata_generator is None:
        _metadata_generator = MetadataGenerator()
    return _metadata_generator


# Convenience functions for direct access
def generate_project_file(project_path: str) -> Optional[str]:
    """Generate project metadata file."""
    return get_metadata_generator().generate_project_file(project_path)


def generate_dataset_files(
    dataset_path: str, project_id: str
) -> Dict[str, Optional[str]]:
    """Generate dataset metadata files."""
    return get_metadata_generator().generate_dataset_files(dataset_path, project_id)


def create_experiment_contextual_template(
    dataset_path: str, experiment_id: Optional[str] = None
) -> Optional[str]:
    """Create experiment contextual metadata template."""
    return get_metadata_generator().create_experiment_contextual_template(
        dataset_path, experiment_id
    )


def generate_complete_metadata_file(
    dataset_path: str, experiment_id: str
) -> Optional[str]:
    """Generate complete metadata file."""
    return get_metadata_generator().generate_complete_metadata_file(
        dataset_path, experiment_id
    )


def check_contextual_metadata_completion(
    dataset_path: str,
) -> Tuple[bool, Optional[str]]:
    """Check contextual metadata completion."""
    return get_metadata_generator().check_contextual_metadata_completion(dataset_path)
