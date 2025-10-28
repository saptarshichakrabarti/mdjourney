"""
Unit tests for the schema manager module.
Tests are isolated and mock external dependencies.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from app.services.schema_manager import (
    SchemaManager,
    get_schema_manager,
    load_schema,
    validate_json,
)


class TestSchemaManager:
    """Test cases for the SchemaManager class."""

    def test_init_default_path(self):
        """Test SchemaManager initialization with default path."""
        manager = SchemaManager()
        assert manager.schema_base_path is not None
        assert isinstance(manager.schema_base_path, Path)
        assert len(manager._schema_cache) == 0

    def test_init_custom_path(self):
        """Test SchemaManager initialization with custom path."""
        custom_path = Path("/custom/schema/path")
        manager = SchemaManager(custom_path)
        assert manager.schema_base_path == custom_path

    def test_load_schema_success(self, sample_project_data):
        """Test successful schema loading."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(sample_project_data))
        ):
            with patch("pathlib.Path.exists", return_value=True):
                manager = SchemaManager()
                schema = manager.load_schema("test_schema.json")

                assert schema is not None
                assert schema == sample_project_data
                # Check that the full path is in the cache
                assert any(
                    "test_schema.json" in key for key in manager._schema_cache.keys()
                )

    def test_load_schema_file_not_found(self):
        """Test schema loading when file doesn't exist."""
        manager = SchemaManager()

        # Mock the file opening to raise FileNotFoundError
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            # Since ALLOW_MISSING_SCHEMAS is False, this should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                manager.load_schema("nonexistent.json")

    def test_load_schema_invalid_json(self):
        """Test schema loading with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("pathlib.Path.exists", return_value=True):
                manager = SchemaManager()

                with pytest.raises(Exception):
                    manager.load_schema("invalid.json")

    def test_validate_json_success(self, sample_project_data):
        """Test successful JSON validation."""
        schema = {
            "type": "object",
            "properties": {"project_identifier": {"type": "string"}},
        }
        manager = SchemaManager()

        result = manager.validate_json(sample_project_data, schema)
        assert result is True

    def test_validate_json_failure(self, sample_project_data):
        """Test JSON validation failure."""
        schema = {
            "type": "object",
            "properties": {"project_identifier": {"type": "integer"}},
        }
        manager = SchemaManager()

        result = manager.validate_json(sample_project_data, schema)
        assert result is False

    def test_validate_json_none_schema_strict(self):
        """Test validation with None schema in strict mode."""
        with patch("app.core.config.STRICT_VALIDATION", True):
            manager = SchemaManager()
            result = manager.validate_json({"test": "data"}, None)
            # With jsonschema, None schema assumes success (more lenient)
            assert result is True

    def test_validate_json_none_schema_lenient(self):
        """Test validation with None schema in lenient mode."""
        with patch("app.core.config.ALLOW_MISSING_SCHEMAS", True):
            manager = SchemaManager()
            result = manager.validate_json({"test": "data"}, None)
            # With jsonschema, None schema assumes success (more lenient)
            assert result is True

    def test_validate_with_schema_file(self, sample_project_data):
        """Test validation with schema file."""
        schema = {
            "type": "object",
            "properties": {"project_identifier": {"type": "string"}},
        }

        with patch.object(SchemaManager, "load_schema", return_value=schema):
            manager = SchemaManager()
            result = manager.validate_with_schema_file(
                sample_project_data, "test_schema.json"
            )
            assert result is True

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        manager = SchemaManager()
        manager._schema_cache["test"] = {"data": "value"}

        assert len(manager._schema_cache) == 1
        manager.clear_cache()
        assert len(manager._schema_cache) == 0

    def test_get_cache_info(self):
        """Test cache information retrieval."""
        manager = SchemaManager()
        manager._schema_cache["test1"] = {"data": "value1"}
        manager._schema_cache["test2"] = {"data": "value2"}

        cache_info = manager.get_cache_info()

        assert cache_info["cache_size"] == 2
        assert "test1" in cache_info["cached_schemas"]
        assert "test2" in cache_info["cached_schemas"]
        assert "schema_base_path" in cache_info


class TestSchemaManagerConvenienceMethods:
    """Test cases for schema manager convenience methods."""

    def test_get_project_schema(self):
        """Test getting project schema."""
        mock_schema = {"type": "object"}
        with patch.object(SchemaManager, "load_schema", return_value=mock_schema):
            manager = SchemaManager()
            schema = manager.get_project_schema()
            assert schema == mock_schema

    def test_get_dataset_admin_schema(self):
        """Test getting dataset admin schema."""
        mock_schema = {"type": "object"}
        with patch.object(SchemaManager, "load_schema", return_value=mock_schema):
            manager = SchemaManager()
            schema = manager.get_dataset_admin_schema()
            assert schema == mock_schema

    def test_get_dataset_struct_schema(self):
        """Test getting dataset structural schema."""
        mock_schema = {"type": "object"}
        with patch.object(SchemaManager, "load_schema", return_value=mock_schema):
            manager = SchemaManager()
            schema = manager.get_dataset_struct_schema()
            assert schema == mock_schema

    def test_get_experiment_contextual_schema(self):
        """Test getting experiment contextual schema."""
        mock_schema = {"type": "object"}
        with patch.object(SchemaManager, "load_schema", return_value=mock_schema):
            manager = SchemaManager()
            schema = manager.get_experiment_contextual_schema()
            assert schema == mock_schema

    def test_get_instrument_technical_schema(self):
        """Test getting instrument technical schema."""
        mock_schema = {"type": "object"}
        with patch.object(SchemaManager, "load_schema", return_value=mock_schema):
            manager = SchemaManager()
            schema = manager.get_instrument_technical_schema()
            assert schema == mock_schema


class TestSchemaManagerValidationMethods:
    """Test cases for schema manager validation methods."""

    def test_validate_project_metadata(self, sample_project_data):
        """Test project metadata validation."""
        mock_schema = {
            "type": "object",
            "properties": {"project_identifier": {"type": "string"}},
        }
        with patch.object(
            SchemaManager, "get_project_schema", return_value=mock_schema
        ):
            manager = SchemaManager()
            result = manager.validate_project_metadata(sample_project_data)
            assert result is True

    def test_validate_dataset_admin_metadata(self, sample_dataset_admin_data):
        """Test dataset admin metadata validation."""
        mock_schema = {
            "type": "object",
            "properties": {"dataset_identifier_link": {"type": "string"}},
        }
        with patch.object(
            SchemaManager, "get_dataset_admin_schema", return_value=mock_schema
        ):
            manager = SchemaManager()
            result = manager.validate_dataset_admin_metadata(sample_dataset_admin_data)
            assert result is True

    def test_validate_dataset_struct_metadata(self, sample_dataset_struct_data):
        """Test dataset structural metadata validation."""
        mock_schema = {
            "type": "object",
            "properties": {"dataset_identifier": {"type": "string"}},
        }
        with patch.object(
            SchemaManager, "get_dataset_struct_schema", return_value=mock_schema
        ):
            manager = SchemaManager()
            result = manager.validate_dataset_struct_metadata(
                sample_dataset_struct_data
            )
            assert result is True

    def test_validate_experiment_contextual_metadata(self):
        """Test experiment contextual metadata validation."""
        test_data = {"experiment_identifier_run_id": "test-123"}
        mock_schema = {
            "type": "object",
            "properties": {"experiment_identifier_run_id": {"type": "string"}},
        }
        with patch.object(
            SchemaManager, "get_experiment_contextual_schema", return_value=mock_schema
        ):
            manager = SchemaManager()
            result = manager.validate_experiment_contextual_metadata(test_data)
            assert result is True

    def test_validate_instrument_technical_metadata(self):
        """Test instrument technical metadata validation."""
        test_data = {"instrument_id": "test-123"}
        mock_schema = {
            "type": "object",
            "properties": {"instrument_id": {"type": "string"}},
        }
        with patch.object(
            SchemaManager, "get_instrument_technical_schema", return_value=mock_schema
        ):
            manager = SchemaManager()
            result = manager.validate_instrument_technical_metadata(test_data)
            assert result is True


class TestGlobalFunctions:
    """Test cases for global convenience functions."""

    def test_get_schema_manager_singleton(self):
        """Test that get_schema_manager returns a singleton."""
        manager1 = get_schema_manager()
        manager2 = get_schema_manager()
        assert manager1 is manager2

    def test_load_schema_convenience(self, sample_project_data):
        """Test load_schema convenience function."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(sample_project_data))
        ):
            with patch("pathlib.Path.exists", return_value=True):
                schema = load_schema("test_schema.json")
                assert schema == sample_project_data

    def test_validate_json_convenience(self, sample_project_data):
        """Test validate_json convenience function."""
        schema = {
            "type": "object",
            "properties": {"project_identifier": {"type": "string"}},
        }
        result = validate_json(sample_project_data, schema)
        assert result is True
