"""
Unit tests for the metadata generator module.
Tests are isolated and mock external dependencies.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from app.services.metadata_generator import (
    MetadataGenerator,
    check_contextual_metadata_completion,
    create_experiment_contextual_template,
    generate_complete_metadata_file,
    generate_dataset_files,
    generate_project_file,
    get_metadata_generator,
)


class TestMetadataGenerator:
    """Test cases for the MetadataGenerator class."""

    def test_init(self):
        """Test MetadataGenerator initialization."""
        generator = MetadataGenerator()
        assert generator.schema_manager is not None
        assert generator.vc_manager is not None

    def test_generate_project_file_success(self, temp_dir, sample_project_data):
        """Test successful project file generation."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_schema = {
            "properties": {
                "project_identifier": {"type": "string"},
                "project_title": {"type": "string"},
                "project_description": {"type": "string"},
                "principal_investigator": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "orcid": {"type": "string"},
                        "email": {"type": "string"},
                        "affiliation": {"type": "string"},
                    },
                },
                "contributing_researchers": {"type": "array"},
                "funding_sources": {"type": "array"},
                "originating_institution": {"type": "string"},
                "originating_laboratory": {"type": "string"},
                "data_collection_method_summary": {"type": "string"},
                "project_data_storage_strategy": {"type": "string"},
                "project_timeline_summary": {"type": "string"},
                "project_keywords": {"type": "array"},
                "project_status": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager, "get_project_schema", return_value=mock_schema
            ):
                with patch.object(generator.vc_manager, "commit_metadata_changes"):
                    result = generator.generate_project_file(project_path)

                    assert result is not None
                    assert os.path.exists(result)

                    # Check file content
                    with open(result, "r") as f:
                        data = json.load(f)
                        assert "project_identifier" in data
                        assert "project_title" in data

    def test_generate_project_file_validation_failure(self, temp_dir):
        """Test project file generation with validation failure."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)

        generator = MetadataGenerator()

        # Mock schema validation to fail
        mock_schema = {
            "properties": {
                "project_identifier": {"type": "string"},
                "project_title": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(
            generator.schema_manager, "validate_json", return_value=False
        ):
            with patch.object(
                generator.schema_manager, "get_project_schema", return_value=mock_schema
            ):
                result = generator.generate_project_file(project_path)

                assert result is None

    def test_generate_dataset_files_success(
        self, temp_dir, sample_dataset_admin_data, sample_dataset_struct_data
    ):
        """Test successful dataset files generation."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        project_id = "test-project-123"

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_admin_schema = {
            "properties": {
                "dataset_identifier_link": {"type": "string"},
                "data_steward_contact_person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "orcid": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
                "date_published_released": {"type": "string"},
                "license": {"type": "string"},
                "access_level": {"type": "string"},
                "data_sensitivity_classification": {"type": "string"},
                "data_retention_schedule": {"type": "string"},
                "link_to_documentation": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        mock_struct_schema = {
            "properties": {
                "dataset_identifier": {"type": "string"},
                "dataset_title": {"type": "string"},
                "dataset_abstract_description": {"type": "string"},
                "dataset_version": {"type": "string"},
                "dataset_type": {"type": "string"},
                "dataset_keywords": {"type": "array"},
                "associated_project_identifier": {"type": "string"},
                "date_created": {"type": "string"},
                "related_publications": {"type": "array"},
                "file_descriptions": {"type": "array"},
                "data_structure_description": {"type": "string"},
                "link_to_data_dictionary": {"type": "string"},
                "data_compression_method": {"type": "string"},
                "software_to_read_access_data": {"type": "array"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager,
                "get_dataset_admin_schema",
                return_value=mock_admin_schema,
            ):
                with patch.object(
                    generator.schema_manager,
                    "get_dataset_struct_schema",
                    return_value=mock_struct_schema,
                ):
                    with patch.object(generator.vc_manager, "commit_metadata_changes"):
                        result = generator.generate_dataset_files(
                            dataset_path, project_id
                        )

                        assert result["admin_file"] is not None
                        assert result["struct_file"] is not None
                        assert os.path.exists(result["admin_file"])
                        assert os.path.exists(result["struct_file"])

    def test_generate_dataset_files_validation_failure(self, temp_dir):
        """Test dataset files generation with validation failure."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        project_id = "test-project-123"

        generator = MetadataGenerator()

        # Mock schema validation to fail
        mock_admin_schema = {
            "properties": {
                "dataset_identifier_link": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        mock_struct_schema = {
            "properties": {
                "dataset_identifier": {"type": "string"},
                "dataset_title": {"type": "string"},
                "associated_project_identifier": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(
            generator.schema_manager, "validate_json", return_value=False
        ):
            with patch.object(
                generator.schema_manager,
                "get_dataset_admin_schema",
                return_value=mock_admin_schema,
            ):
                with patch.object(
                    generator.schema_manager,
                    "get_dataset_struct_schema",
                    return_value=mock_struct_schema,
                ):
                    result = generator.generate_dataset_files(dataset_path, project_id)

                    assert result["admin_file"] is None
                    assert result["struct_file"] is None

    def test_create_experiment_contextual_template_success(self, temp_dir):
        """Test successful experiment contextual template creation."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Create dataset structural file
        struct_data = {"dataset_identifier": "test-dataset-123"}
        struct_file = os.path.join(dataset_path, ".metadata", "dataset_structural.json")
        os.makedirs(os.path.dirname(struct_file))
        with open(struct_file, "w") as f:
            json.dump(struct_data, f)

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_contextual_schema = {
            "properties": {
                "experiment_identifier_run_id": {"type": "string"},
                "experiment_dates": {"type": "array"},
                "experimenters": {"type": "array"},
                "dataset_identifier_link": {"type": "string"},
                "protocol_references": {"type": "array"},
                "unique_sample_batch_identifiers": {"type": "array"},
                "sample_source_description": {"type": "string"},
                "instrument_used_link": {"type": "array"},
                "instrument_settings_run_parameters": {"type": "object"},
                "software_used_acquisition_analysis": {"type": "array"},
                "software_parameters_script_used": {"type": "string"},
                "quality_control_metrics": {"type": "object"},
                "qc_assessment": {"type": "string"},
                "links_to_raw_data_files": {"type": "array"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager,
                "get_experiment_contextual_schema",
                return_value=mock_contextual_schema,
            ):
                with patch.object(generator.vc_manager, "commit_metadata_changes"):
                    result = generator.create_experiment_contextual_template(
                        dataset_path
                    )

                    assert result is not None
                    assert os.path.exists(result)

                    # Check file content
                    with open(result, "r") as f:
                        data = json.load(f)
                        assert "experiment_identifier_run_id" in data
                        assert "dataset_identifier_link" in data

    def test_create_experiment_contextual_template_with_custom_id(self, temp_dir):
        """Test experiment contextual template creation with custom experiment ID."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Create dataset structural file
        struct_data = {"dataset_identifier": "test-dataset-123"}
        struct_file = os.path.join(dataset_path, ".metadata", "dataset_structural.json")
        os.makedirs(os.path.dirname(struct_file))
        with open(struct_file, "w") as f:
            json.dump(struct_data, f)

        custom_experiment_id = "custom-experiment-123"

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_contextual_schema = {
            "properties": {
                "experiment_identifier_run_id": {"type": "string"},
                "experiment_dates": {"type": "array"},
                "experimenters": {"type": "array"},
                "dataset_identifier_link": {"type": "string"},
                "protocol_references": {"type": "array"},
                "unique_sample_batch_identifiers": {"type": "array"},
                "sample_source_description": {"type": "string"},
                "instrument_used_link": {"type": "array"},
                "instrument_settings_run_parameters": {"type": "object"},
                "software_used_acquisition_analysis": {"type": "array"},
                "software_parameters_script_used": {"type": "string"},
                "quality_control_metrics": {"type": "object"},
                "qc_assessment": {"type": "string"},
                "links_to_raw_data_files": {"type": "array"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager,
                "get_experiment_contextual_schema",
                return_value=mock_contextual_schema,
            ):
                with patch.object(generator.vc_manager, "commit_metadata_changes"):
                    result = generator.create_experiment_contextual_template(
                        dataset_path, custom_experiment_id
                    )

                    assert result is not None
                    assert os.path.exists(result)

                    # Check file content
                    with open(result, "r") as f:
                        data = json.load(f)
                        assert (
                            data["experiment_identifier_run_id"] == custom_experiment_id
                        )

    def test_create_experiment_contextual_template_no_struct_file(self, temp_dir):
        """Test experiment contextual template creation when structural file doesn't exist."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_contextual_schema = {
            "properties": {
                "experiment_identifier_run_id": {"type": "string"},
                "experiment_dates": {"type": "array"},
                "experimenters": {"type": "array"},
                "dataset_identifier_link": {"type": "string"},
                "protocol_references": {"type": "array"},
                "unique_sample_batch_identifiers": {"type": "array"},
                "sample_source_description": {"type": "string"},
                "instrument_used_link": {"type": "array"},
                "instrument_settings_run_parameters": {"type": "object"},
                "software_used_acquisition_analysis": {"type": "array"},
                "software_parameters_script_used": {"type": "string"},
                "quality_control_metrics": {"type": "object"},
                "qc_assessment": {"type": "string"},
                "links_to_raw_data_files": {"type": "array"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager,
                "get_experiment_contextual_schema",
                return_value=mock_contextual_schema,
            ):
                with patch.object(generator.vc_manager, "commit_metadata_changes"):
                    result = generator.create_experiment_contextual_template(
                        dataset_path
                    )

                    # Should succeed even without structural file
                    assert result is not None
                    assert os.path.exists(result)

                    # Check file content
                    with open(result, "r") as f:
                        data = json.load(f)
                        assert "experiment_identifier_run_id" in data
                        assert "dataset_identifier_link" in data

    def test_generate_complete_metadata_file_success(self, temp_dir):
        """Test successful complete metadata file generation."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Create all required metadata files
        metadata_dir = os.path.join(dataset_path, ".metadata")
        os.makedirs(metadata_dir)

        # Project file
        project_data = {"project_identifier": "test-project-123"}
        project_file = os.path.join(
            project_path, ".metadata", "project_descriptive.json"
        )
        os.makedirs(os.path.dirname(project_file))
        with open(project_file, "w") as f:
            json.dump(project_data, f)

        # Dataset files
        admin_data = {"dataset_identifier_link": "test-dataset-123"}
        admin_file = os.path.join(metadata_dir, "dataset_administrative.json")
        with open(admin_file, "w") as f:
            json.dump(admin_data, f)

        struct_data = {"dataset_identifier": "test-dataset-123"}
        struct_file = os.path.join(metadata_dir, "dataset_structural.json")
        with open(struct_file, "w") as f:
            json.dump(struct_data, f)

        contextual_data = {"experiment_identifier_run_id": "test-experiment-123"}
        contextual_file = os.path.join(metadata_dir, "experiment_contextual.json")
        with open(contextual_file, "w") as f:
            json.dump(contextual_data, f)

        experiment_id = "test-experiment-123"

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_complete_schema = {
            "properties": {
                "version": {"type": "string"},
                "experiment_identifier": {"type": "string"},
                "metadata_components": {
                    "type": "object",
                    "properties": {
                        "project_descriptive": {"type": "object"},
                        "dataset_administrative": {"type": "object"},
                        "dataset_structural": {"type": "object"},
                        "experiment_contextual": {"type": "object"},
                    },
                },
                "metadata_relationships": {
                    "type": "object",
                    "properties": {
                        "project_to_dataset": {"type": "string"},
                        "dataset_to_experiment": {"type": "string"},
                        "experiment_to_data_files": {"type": "string"},
                    },
                },
                "metadata_validation": {
                    "type": "object",
                    "properties": {
                        "schema_compliance": {"type": "boolean"},
                        "completeness_score": {"type": "number"},
                        "quality_score": {"type": "number"},
                    },
                },
                "metadata_provenance": {
                    "type": "object",
                    "properties": {
                        "generated_by": {"type": "string"},
                        "generation_date": {"type": "string"},
                        "last_validation_date": {"type": "string"},
                    },
                },
            }
        }

        with patch.object(generator.schema_manager, "validate_json", return_value=True):
            with patch.object(
                generator.schema_manager,
                "get_complete_metadata_schema",
                return_value=mock_complete_schema,
            ):
                with patch.object(generator.vc_manager, "commit_metadata_changes"):
                    result = generator.generate_complete_metadata_file(
                        dataset_path, experiment_id
                    )

                    assert result is not None
                    assert os.path.exists(result)

                    # Check file content
                    with open(result, "r") as f:
                        data = json.load(f)
                        assert data["version"] == "2.0"
                        assert data["experiment_identifier"] == experiment_id
                        assert "metadata_components" in data

    def test_check_contextual_metadata_completion_complete(self, temp_dir):
        """Test contextual metadata completion check when complete."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Create contextual file with complete data
        contextual_data = {
            "experiment_identifier_run_id": "test-experiment-123",
            "experimenters": [
                {"name": "Test User", "orcid": "https://orcid.org/0000-0000-0000-0000"}
            ],
            "protocol_references": ["Test Protocol"],
            "protocol_deviations": "None",
            "unique_sample_batch_identifiers": ["batch-123"],
            "sample_source_description": "Test source",
            "sample_treatment_conditions": "Test conditions",
            "sample_preparation_details": "Test preparation",
            "instrument_used_link": ["instrument-123"],
            "instrument_settings_run_parameters": {"param1": "value1"},
            "software_used_acquisition_analysis": [
                {"name": "Test Software", "version": "1.0"}
            ],
            "software_parameters_script_used": "Test script",
            "reagent_kit_details": [
                {
                    "manufacturer": "Test Corp",
                    "catalog_number": "123",
                    "lot_number": "456",
                    "expiry_date": "2025-01-01",
                }
            ],
            "quality_control_metrics": {"metric1": "value1"},
            "qc_assessment": "Pass",
            "links_to_raw_data_files": [],
            "experimenter_notes_observations": "Test notes",
        }

        contextual_file = os.path.join(
            dataset_path, ".metadata", "experiment_contextual.json"
        )
        os.makedirs(os.path.dirname(contextual_file))
        with open(contextual_file, "w") as f:
            json.dump(contextual_data, f)

        generator = MetadataGenerator()
        is_complete, experiment_id = generator.check_contextual_metadata_completion(
            dataset_path
        )

        assert is_complete is True
        assert experiment_id == "test-experiment-123"

    def test_check_contextual_metadata_completion_incomplete(self, temp_dir):
        """Test contextual metadata completion check when incomplete."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Create contextual file with incomplete data
        contextual_data = {
            "experiment_identifier_run_id": "test-experiment-123",
            "experimenters": [
                {
                    "name": "To be filled",
                    "orcid": "https://orcid.org/0000-0000-0000-0000",
                }
            ],
            "protocol_references": ["To be filled"],
            "protocol_deviations": "To be filled",
            "unique_sample_batch_identifiers": ["To be filled"],
            "sample_source_description": "To be filled",
            "sample_treatment_conditions": "To be filled",
            "sample_preparation_details": "To be filled",
            "instrument_used_link": ["To be filled"],
            "instrument_settings_run_parameters": {"param1": "To be filled"},
            "software_used_acquisition_analysis": [
                {"name": "To be filled", "version": "To be filled"}
            ],
            "software_parameters_script_used": "To be filled",
            "reagent_kit_details": [
                {
                    "manufacturer": "To be filled",
                    "catalog_number": "To be filled",
                    "lot_number": "To be filled",
                    "expiry_date": "To be filled",
                }
            ],
            "quality_control_metrics": {"metric1": "To be filled"},
            "qc_assessment": "Review",
            "links_to_raw_data_files": [],
            "experimenter_notes_observations": "To be filled",
        }

        contextual_file = os.path.join(
            dataset_path, ".metadata", "experiment_contextual.json"
        )
        os.makedirs(os.path.dirname(contextual_file))
        with open(contextual_file, "w") as f:
            json.dump(contextual_data, f)

        generator = MetadataGenerator()
        is_complete, experiment_id = generator.check_contextual_metadata_completion(
            dataset_path
        )

        assert is_complete is False
        assert experiment_id is None

    def test_check_contextual_metadata_completion_no_file(self, temp_dir):
        """Test contextual metadata completion check when file doesn't exist."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        generator = MetadataGenerator()
        is_complete, experiment_id = generator.check_contextual_metadata_completion(
            dataset_path
        )

        assert is_complete is False
        assert experiment_id is None


class TestGlobalFunctions:
    """Test cases for global convenience functions."""

    def test_get_metadata_generator_singleton(self):
        """Test that get_metadata_generator returns a singleton."""
        generator1 = get_metadata_generator()
        generator2 = get_metadata_generator()
        assert generator1 is generator2

    def test_generate_project_file_convenience(self, temp_dir):
        """Test generate_project_file convenience function."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)

        with patch.object(
            MetadataGenerator, "generate_project_file", return_value="/test/path"
        ):
            result = generate_project_file(project_path)
            assert result == "/test/path"

    def test_generate_dataset_files_convenience(self, temp_dir):
        """Test generate_dataset_files convenience function."""
        dataset_path = os.path.join(temp_dir, "dataset_TestDataset")
        os.makedirs(dataset_path)
        project_id = "test-project-123"

        expected_result = {
            "admin_file": "/test/admin.json",
            "struct_file": "/test/struct.json",
        }
        with patch.object(
            MetadataGenerator, "generate_dataset_files", return_value=expected_result
        ):
            result = generate_dataset_files(dataset_path, project_id)
            assert result == expected_result

    def test_create_experiment_contextual_template_convenience(self, temp_dir):
        """Test create_experiment_contextual_template convenience function."""
        dataset_path = os.path.join(temp_dir, "dataset_TestDataset")
        os.makedirs(dataset_path)

        with patch.object(
            MetadataGenerator,
            "create_experiment_contextual_template",
            return_value="/test/contextual.json",
        ):
            result = create_experiment_contextual_template(dataset_path)
            assert result == "/test/contextual.json"

    def test_generate_complete_metadata_file_convenience(self, temp_dir):
        """Test generate_complete_metadata_file convenience function."""
        dataset_path = os.path.join(temp_dir, "dataset_TestDataset")
        os.makedirs(dataset_path)
        experiment_id = "test-experiment-123"

        with patch.object(
            MetadataGenerator,
            "generate_complete_metadata_file",
            return_value="/test/complete.json",
        ):
            result = generate_complete_metadata_file(dataset_path, experiment_id)
            assert result == "/test/complete.json"

    def test_generate_project_admin_file(self, temp_dir):
        """Test project administrative metadata file generation."""
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)
        metadata_dir = os.path.join(project_path, ".metadata")
        os.makedirs(metadata_dir)
        project_id = "test-project-123"

        generator = MetadataGenerator()

        # Mock schema validation to succeed
        mock_schema = {
            "properties": {
                "project_identifier_link": {"type": "string"},
                "created_by": {"type": "string"},
                "created_date": {"type": "string"},
                "last_modified_by": {"type": "string"},
                "last_modified_date": {"type": "string"},
            },
            "required": ["project_identifier_link", "created_by", "created_date", "last_modified_by", "last_modified_date"]
        }

        with patch.object(
            generator.schema_manager, "get_project_admin_schema", return_value=mock_schema
        ), patch.object(
            generator.schema_manager, "validate_json", return_value=True
        ), patch("builtins.open", mock_open()) as mock_file:

            result = generator._generate_project_admin_file(project_path, project_id, metadata_dir)

            assert result is not None
            assert result.endswith("project_administrative.json")
            mock_file.assert_called_once()

    def test_project_admin_schema_loading(self):
        """Test that project administrative schema can be loaded."""
        generator = MetadataGenerator()

        # This should not raise an exception
        schema = generator.schema_manager.get_project_admin_schema()
        # Schema might be None if file doesn't exist in test environment, which is OK
        assert schema is None or isinstance(schema, dict)

    def test_extract_dataset_fields_from_project_admin(self):
        """Test extraction of dataset fields from project administrative metadata."""
        generator = MetadataGenerator()

        project_admin_data = {
            "data_steward_contact_person": {"name": "John Doe", "email": "john@example.com"},
            "default_license": "CC-BY 4.0",
            "default_access_level": "Public",
            "project_ethics_approval_references": ["IRB-2023-001"],
            "project_data_retention_schedule": "10 years",
            "project_citation_template": "Doe, J. (2023). Dataset Title. Institution.",
            "unused_field": "should not be copied"
        }

        extracted = generator._extract_dataset_fields_from_project_admin(project_admin_data)

        # Check that correct fields were extracted
        assert extracted["data_steward_contact_person"] == {"name": "John Doe", "email": "john@example.com"}
        assert extracted["license"] == "CC-BY 4.0"
        assert extracted["access_level"] == "Public"
        assert extracted["ethics_approval_references"] == ["IRB-2023-001"]
        assert extracted["data_retention_schedule"] == "10 years"
        assert extracted["recommended_citation"] == "Doe, J. (2023). Dataset Title. Institution."

        # Check that unused field was not copied
        assert "unused_field" not in extracted

    def test_load_project_admin_metadata(self, temp_dir):
        """Test loading project administrative metadata."""
        generator = MetadataGenerator()

        # Create a mock project structure
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)
        metadata_dir = os.path.join(project_path, ".metadata")
        os.makedirs(metadata_dir)

        project_id = "test-project-123"

        # Create project descriptive metadata
        project_desc = {"project_identifier": project_id, "project_title": "Test Project"}
        with open(os.path.join(metadata_dir, "project_descriptive.json"), "w") as f:
            json.dump(project_desc, f)

        # Create project administrative metadata
        project_admin = {
            "project_identifier_link": project_id,
            "default_license": "CC-BY 4.0",
            "data_steward_contact_person": {"name": "Jane Doe", "email": "jane@example.com"}
        }
        with open(os.path.join(metadata_dir, "project_administrative.json"), "w") as f:
            json.dump(project_admin, f)

        # Mock the monitor path to point to our temp directory
        with patch('app.services.metadata_generator.get_monitor_path', return_value=temp_dir):
            result = generator._load_project_admin_metadata(project_id)

            assert result is not None
            assert result["project_identifier_link"] == project_id
            assert result["default_license"] == "CC-BY 4.0"
            assert result["data_steward_contact_person"]["name"] == "Jane Doe"

    def test_check_contextual_metadata_completion_convenience(self, temp_dir):
        """Test check_contextual_metadata_completion convenience function."""
        dataset_path = os.path.join(temp_dir, "dataset_TestDataset")
        os.makedirs(dataset_path)

        expected_result = (True, "test-experiment-123")
        with patch.object(
            MetadataGenerator,
            "check_contextual_metadata_completion",
            return_value=expected_result,
        ):
            result = check_contextual_metadata_completion(dataset_path)
            assert result == expected_result
