"""
Test data fixtures for integration tests.
Manages the lifecycle of test projects, datasets, and metadata.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import pytest


@pytest.fixture(scope="session")
def test_data_root():
    """Create a temporary root directory for all test data."""
    import os

    # Check if we're running in the integration test script environment
    existing_test_path = os.environ.get("MDJOURNEY_DATA_PATH")
    if existing_test_path:
        # Use the existing path set by the integration script
        data_dir = Path(existing_test_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Using existing test data path from environment: {data_dir}")
        yield data_dir
    else:
        # Create a new temporary directory for standalone test runs
        with tempfile.TemporaryDirectory(prefix="mdjourney_test_") as temp_dir:
            # Set up the test data root similar to the real data structure
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            print(f"Created new test data path: {data_dir}")
            yield data_dir


@pytest.fixture(scope="session")
def test_projects_data(test_data_root):
    """Create test projects with complete metadata structure."""
    projects = []

    # Project 1: Genomics Research
    project1_id = "p_genomics_test"
    project1_path = test_data_root / project1_id
    project1_path.mkdir()

    # Create project metadata
    project1_metadata = {
        "project_identifier": str(uuid4()),
        "project_title": "Genomics Research Test Project",
        "project_description": "A test project for genomics sequencing research",
        "principal_investigator": "Dr. Test Researcher",
        "institution": "Test University",
        "created_date": "2024-01-15T10:00:00Z",
        "last_modified_date": "2024-01-15T10:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Save project metadata
    project1_meta_dir = project1_path / ".metadata"
    project1_meta_dir.mkdir()
    with open(project1_meta_dir / "project_descriptive.json", "w") as f:
        json.dump(project1_metadata, f, indent=2)

    projects.append(
        {
            "project_id": project1_id,
            "path": project1_path,
            "metadata": project1_metadata,
        }
    )

    # Project 2: Microscopy Research
    project2_id = "p_microscopy_test"
    project2_path = test_data_root / project2_id
    project2_path.mkdir()

    project2_metadata = {
        "project_identifier": str(uuid4()),
        "project_title": "Microscopy Imaging Test Project",
        "project_description": "A test project for microscopy imaging research",
        "principal_investigator": "Dr. Image Researcher",
        "institution": "Test Research Institute",
        "created_date": "2024-01-20T14:30:00Z",
        "last_modified_date": "2024-01-20T14:30:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    project2_meta_dir = project2_path / ".metadata"
    project2_meta_dir.mkdir()
    with open(project2_meta_dir / "project_descriptive.json", "w") as f:
        json.dump(project2_metadata, f, indent=2)

    projects.append(
        {
            "project_id": project2_id,
            "path": project2_path,
            "metadata": project2_metadata,
        }
    )

    return projects


@pytest.fixture(scope="session")
def test_datasets_data(test_projects_data):
    """Create test datasets within the test projects."""
    datasets = []

    # Dataset 1: Genomics sequencing data
    project1 = test_projects_data[0]
    dataset1_id = "d_genomics_seq_001"
    dataset1_path = project1["path"] / dataset1_id
    dataset1_path.mkdir()

    # Create dataset metadata directory
    dataset1_meta_dir = dataset1_path / ".metadata"
    dataset1_meta_dir.mkdir()

    # Administrative metadata
    admin_metadata = {
        "dataset_identifier": str(uuid4()),
        "dataset_title": "Genomics Sequencing Dataset 001",
        "dataset_description": "Test dataset for genomics sequencing analysis",
        "associated_project_identifier": project1["metadata"]["project_identifier"],
        "data_type": "genomics",
        "file_format": "FASTQ",
        "created_date": "2024-01-16T09:00:00Z",
        "last_modified_date": "2024-01-16T09:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Structural metadata
    structural_metadata = {
        "dataset_identifier_link": admin_metadata["dataset_identifier"],
        "file_structure": {
            "total_files": 10,
            "total_size_bytes": 1024000,
            "file_types": ["fastq", "txt"],
        },
        "data_organization": "hierarchical",
        "created_date": "2024-01-16T09:00:00Z",
        "last_modified_date": "2024-01-16T09:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Contextual metadata (genomics sequencing)
    contextual_metadata = {
        "experiment_identifier_run_id": f"exp_{dataset1_id}_genomics_sequencing",
        "experiment_template_type": "genomics_sequencing",
        "experiment_name": "Genomics Sequencing Experiment 001",
        "dataset_identifier_link": admin_metadata["dataset_identifier"],
        "experiment_title": "Test Genomics Sequencing",
        "sequencing_platform": "Illumina NovaSeq",
        "sequencing_chemistry": "SBS",
        "read_length": 150,
        "library_preparation": "TruSeq DNA PCR-Free",
        "sample_source_description": "Test biological samples",
        "created_date": "2024-01-16T09:00:00Z",
        "last_modified_date": "2024-01-16T09:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Save all metadata files
    with open(dataset1_meta_dir / "dataset_administrative.json", "w") as f:
        json.dump(admin_metadata, f, indent=2)
    with open(dataset1_meta_dir / "dataset_structural.json", "w") as f:
        json.dump(structural_metadata, f, indent=2)
    with open(dataset1_meta_dir / "experiment_contextual.json", "w") as f:
        json.dump(contextual_metadata, f, indent=2)

    datasets.append(
        {
            "dataset_id": dataset1_id,
            "project_id": project1["project_id"],
            "path": dataset1_path,
            "admin_metadata": admin_metadata,
            "structural_metadata": structural_metadata,
            "contextual_metadata": contextual_metadata,
        }
    )

    # Dataset 2: Microscopy imaging data
    project2 = test_projects_data[1]
    dataset2_id = "d_microscopy_img_001"
    dataset2_path = project2["path"] / dataset2_id
    dataset2_path.mkdir()

    dataset2_meta_dir = dataset2_path / ".metadata"
    dataset2_meta_dir.mkdir()

    # Administrative metadata
    admin_metadata2 = {
        "dataset_identifier": str(uuid4()),
        "dataset_title": "Microscopy Imaging Dataset 001",
        "dataset_description": "Test dataset for microscopy imaging analysis",
        "associated_project_identifier": project2["metadata"]["project_identifier"],
        "data_type": "microscopy",
        "file_format": "TIFF",
        "created_date": "2024-01-21T10:00:00Z",
        "last_modified_date": "2024-01-21T10:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Structural metadata
    structural_metadata2 = {
        "dataset_identifier_link": admin_metadata2["dataset_identifier"],
        "file_structure": {
            "total_files": 25,
            "total_size_bytes": 5120000,
            "file_types": ["tiff", "txt"],
        },
        "data_organization": "temporal",
        "created_date": "2024-01-21T10:00:00Z",
        "last_modified_date": "2024-01-21T10:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Contextual metadata (microscopy imaging)
    contextual_metadata2 = {
        "experiment_identifier_run_id": f"exp_{dataset2_id}_microscopy_imaging",
        "experiment_template_type": "microscopy_imaging",
        "experiment_name": "Microscopy Imaging Experiment 001",
        "dataset_identifier_link": admin_metadata2["dataset_identifier"],
        "experiment_title": "Test Microscopy Imaging",
        "microscope_type": "Confocal",
        "imaging_modality": "Fluorescence",
        "objective_magnification": "63x",
        "numerical_aperture": 1.4,
        "sample_source_description": "Test cell cultures",
        "created_date": "2024-01-21T10:00:00Z",
        "last_modified_date": "2024-01-21T10:00:00Z",
        "created_by": "test_user",
        "last_modified_by": "test_user",
    }

    # Save all metadata files
    with open(dataset2_meta_dir / "dataset_administrative.json", "w") as f:
        json.dump(admin_metadata2, f, indent=2)
    with open(dataset2_meta_dir / "dataset_structural.json", "w") as f:
        json.dump(structural_metadata2, f, indent=2)
    with open(dataset2_meta_dir / "experiment_contextual.json", "w") as f:
        json.dump(contextual_metadata2, f, indent=2)

    datasets.append(
        {
            "dataset_id": dataset2_id,
            "project_id": project2["project_id"],
            "path": dataset2_path,
            "admin_metadata": admin_metadata2,
            "structural_metadata": structural_metadata2,
            "contextual_metadata": contextual_metadata2,
        }
    )

    return datasets


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_data_root, test_projects_data, test_datasets_data):
    """Set up the test environment by configuring the data path."""
    # Set environment variable for the API to use our test data
    import os

    original_data_path = os.environ.get("MDJOURNEY_DATA_PATH")
    os.environ["MDJOURNEY_DATA_PATH"] = str(test_data_root)

    # Force reload of configuration if it's already loaded
    try:
        import app.core.config

        # Use the new reload function to update the config
        if app.core.config.reload_config_from_environment():
            print(f"Successfully reloaded config with test data path: {test_data_root}")
        else:
            print(
                f"Config not yet loaded, will use test data path when initialized: {test_data_root}"
            )
    except ImportError:
        print(
            f"Config module not available, will use test data path when loaded: {test_data_root}"
        )

    # Also try to reload the API server configuration if it's running
    try:
        import time

        import requests

        # Give the API server a moment to start if it's starting
        time.sleep(1)

        # Try to reload the API server configuration
        reload_response = requests.post(
            "http://localhost:8000/api/v1/config/reload", timeout=2
        )
        if reload_response.status_code == 200:
            result = reload_response.json()
            print(f"API server config reload: {result['status']} - {result['message']}")
        else:
            print(f"API server config reload failed: {reload_response.status_code}")
    except Exception as e:
        print(
            f"Could not reload API server config (this is OK if server isn't running): {e}"
        )

    yield {
        "data_root": test_data_root,
        "projects": test_projects_data,
        "datasets": test_datasets_data,
    }

    # Restore original environment
    if original_data_path is not None:
        os.environ["MDJOURNEY_DATA_PATH"] = original_data_path
    elif "MDJOURNEY_DATA_PATH" in os.environ:
        del os.environ["MDJOURNEY_DATA_PATH"]


@pytest.fixture(scope="function")
def api_test_data(setup_test_environment):
    """Provide test data for API integration tests."""
    return setup_test_environment


@pytest.fixture(scope="function")
def sample_project(api_test_data):
    """Get the first test project for single-project tests."""
    return api_test_data["projects"][0]


@pytest.fixture(scope="function")
def sample_dataset(api_test_data):
    """Get the first test dataset for single-dataset tests."""
    return api_test_data["datasets"][0]


@pytest.fixture(scope="function")
def genomics_dataset(api_test_data):
    """Get the genomics test dataset specifically."""
    datasets = api_test_data["datasets"]
    for dataset in datasets:
        if "genomics" in dataset["dataset_id"]:
            return dataset
    raise ValueError("Genomics dataset not found in test data")


@pytest.fixture(scope="function")
def microscopy_dataset(api_test_data):
    """Get the microscopy test dataset specifically."""
    datasets = api_test_data["datasets"]
    for dataset in datasets:
        if "microscopy" in dataset["dataset_id"]:
            return dataset
    raise ValueError("Microscopy dataset not found in test data")
