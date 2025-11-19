"""
Pytest configuration and common fixtures for the FAIR metadata automation system tests.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add backend root to path for imports (tests are in mdjourney-backend/tests/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import test data fixtures
from tests.fixtures.test_data import (
    api_test_data,
    genomics_dataset,
    microscopy_dataset,
    sample_dataset,
    sample_project,
    setup_test_environment,
    test_data_root,
    test_datasets_data,
    test_projects_data,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_project_structure(temp_dir):
    """Create a test project structure for testing."""
    # Create monitor directory
    monitor_dir = os.path.join(temp_dir, "monitor")
    os.makedirs(monitor_dir)

    # Create project directory
    project_path = os.path.join(monitor_dir, "p_TestProject")
    os.makedirs(project_path)

    # Create dataset directory
    dataset_path = os.path.join(project_path, "dataset_TestDataset")
    os.makedirs(dataset_path)

    return {
        "temp_dir": temp_dir,
        "monitor_dir": monitor_dir,
        "project_path": project_path,
        "dataset_path": dataset_path,
    }


@pytest.fixture
def mock_dirmeta():
    """Mock dirmeta library for testing."""
    with patch("app.services.file_processor.scan_directory") as mock_scan:
        mock_scan.return_value = [
            {
                "path": "/test/path/file.txt",
                "size_bytes": 1024,
                "extension": ".txt",
                "mime_type": "text/plain",
                "encoding": "utf-8",
                "permissions": "-rw-r--r--",
                "accessed_time": "2024-01-01T00:00:00Z",
                "created_time": "2024-01-01T00:00:00Z",
                "modified_time": "2024-01-01T00:00:00Z",
                "checksum": "abc123",
            }
        ]
        yield mock_scan


@pytest.fixture
def mock_git():
    """Mock Git operations for testing."""
    with patch("app.services.version_control.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_dvc():
    """Mock DVC operations for testing."""
    with patch("app.services.version_control.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        yield mock_run


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "project_identifier": "test-project-123",
        "project_title": "Test Project",
        "project_description": "Test project description",
        "principal_investigator": {
            "name": "Test PI",
            "orcid": "https://orcid.org/0000-0000-0000-0000",
            "email": "test@example.com",
            "affiliation": "Test University",
        },
        "contributing_researchers": [],
        "funding_sources": [],
        "originating_institution": "Test University",
        "originating_laboratory": "Test Lab",
        "data_collection_method_summary": "Test method",
        "keywords": [],
        "created_by": "system",
        "created_date": "2024-01-01T00:00:00Z",
        "last_modified_by": "system",
        "last_modified_date": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_dataset_admin_data():
    """Sample dataset administrative data for testing."""
    return {
        "dataset_identifier_link": "test-dataset-123",
        "data_steward_contact_person": {
            "name": "Test Steward",
            "email": "steward@example.com",
            "orcid": "https://orcid.org/0000-0000-0000-0000",
        },
        "date_published_released": "2024-01-01",
        "license": "CC-BY-4.0",
        "access_level": "Public",
        "access_conditions_contact": "test@example.com",
        "ethics_approval_references": [],
        "consent_framework_summary": "Test consent",
        "data_sensitivity_classification": "Public",
        "anonymization_method": "Test anonymization",
        "data_retention_schedule": "10 years",
        "recommended_citation": "Test citation",
        "link_to_documentation": "",
        "preservation_location": "Test repository",
        "created_by": "system",
        "created_date": "2024-01-01T00:00:00Z",
        "last_modified_by": "system",
        "last_modified_date": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_dataset_struct_data():
    """Sample dataset structural data for testing."""
    return {
        "dataset_identifier": "test-dataset-123",
        "dataset_title": "Test Dataset",
        "dataset_abstract_description": "Test dataset description",
        "dataset_version": "1.0",
        "dataset_type": "Research Data",
        "dataset_keywords": [],
        "associated_project_identifier": "test-project-123",
        "date_created": "2024-01-01",
        "related_publications": [],
        "file_descriptions": [],
        "data_structure_description": "Test structure",
        "link_to_data_dictionary": "",
        "data_compression_method": "none",
        "software_to_read_access_data": [],
        "created_by": "system",
        "created_date": "2024-01-01T00:00:00Z",
        "last_modified_by": "system",
        "last_modified_date": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_file_metadata():
    """Sample file metadata for testing."""
    return {
        "file_name": "test_file.txt",
        "file_path": "data/test_file.txt",
        "file_size_bytes": 1024,
        "checksum": "abc123",
        "checksum_algorithm": "SHA256",
        "file_extension": "txt",
        "mime_type": "text/plain",
        "encoding": "utf-8",
        "file_permissions": "-rw-r--r--",
        "file_accessed_utc": "2024-01-01T00:00:00Z",
        "file_created_utc": "2024-01-01T00:00:00Z",
        "file_modified_utc": "2024-01-01T00:00:00Z",
        "file_metadata_changed_utc": "2024-01-01T00:00:00Z",
        "role": "raw_data",
        "file_type_os": "file",
        "data_format_standard": "",
        "dimensions": "",
        "bit_depth": "",
        "number_of_records": 0,
        "channels": [],
        "acquisition_software": "",
    }
