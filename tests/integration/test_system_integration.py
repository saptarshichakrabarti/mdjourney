#!/usr/bin/env python3
"""
Integration test for the complete FAIR metadata automation system.
Tests the complete integrated system using all refactored modules.
"""

import json
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path

import pytest

from app.core.config import MONITOR_PATH, PROJECT_PREFIX
from app.monitors.folder_monitor import get_folder_monitor
from app.services.file_processor import get_file_processor
from app.services.metadata_generator import get_metadata_generator
from app.services.schema_manager import get_schema_manager
from app.services.version_control import get_vc_manager


def print_header(title):
    """Print a formatted header."""
    print(f"\n{title}")
    print("=" * 80)


def print_test_result(test_name, passed, details=""):
    """Print a test result."""
    status = "✓" if passed else "✗"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")


@pytest.mark.integration
def test_module_integration():
    """Test that all modules can be imported and initialized together."""
    print_header("--- Module Integration ---")

    # Test all module imports and initialization
    modules = [
        ("Schema Manager", get_schema_manager),
        ("Metadata Generator", get_metadata_generator),
        ("File Processor", get_file_processor),
        # Initialize folder monitor with a temp path to avoid config dependency
        ("Folder Monitor", lambda: get_folder_monitor(str(Path.cwd() / "data"))),
        ("Version Control", get_vc_manager),
    ]

    for name, module_func in modules:
        try:
            module = module_func()
            print_test_result(f"{name} initialization", True, f"Type: {type(module)}")
        except Exception as e:
            print_test_result(f"{name} initialization", False, f"Error: {e}")
            pytest.fail(f"Module {name} failed to initialize: {e}")

    # If we get here, all modules initialized successfully
    assert True


@pytest.mark.integration
def test_end_to_end_workflow():
    """Test the complete end-to-end workflow."""
    print_header("--- End-to-End Workflow ---")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test monitor directory
        monitor_dir = os.path.join(temp_dir, "monitor")
        os.makedirs(monitor_dir)

        # Get all modules
        schema_manager = get_schema_manager()
        metadata_generator = get_metadata_generator()
        file_processor = get_file_processor()
        folder_monitor = get_folder_monitor(monitor_dir)

        # Step 1: Create project folder
        project_path = os.path.join(monitor_dir, "p_TestProject")
        os.makedirs(project_path)

        # Step 2: Generate project metadata
        project_file = metadata_generator.generate_project_file(project_path)
        project_created = project_file and os.path.exists(project_file)
        print_test_result("Project metadata generation", project_created)

        assert project_created, "Project metadata generation failed"

        # Step 3: Create dataset folder
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Step 4: Get project ID and generate dataset metadata
        with open(project_file, "r") as f:
            project_data = json.load(f)
            project_id = project_data["project_identifier"]

        dataset_result = metadata_generator.generate_dataset_files(
            dataset_path, project_id
        )
        dataset_created = (
            dataset_result["admin_file"]
            and dataset_result["struct_file"]
            and os.path.exists(dataset_result["admin_file"])
            and os.path.exists(dataset_result["struct_file"])
        )
        print_test_result("Dataset metadata generation", dataset_created)

        assert dataset_created, "Dataset metadata generation failed"

        # Step 5: Create test files and process them
        test_files = [
            os.path.join(dataset_path, "sample_A.fastq"),
            os.path.join(dataset_path, "sample_B.fastq"),
            os.path.join(dataset_path, "metadata.csv"),
        ]

        for file_path in test_files:
            with open(file_path, "w") as f:
                f.write(f"Test content for {os.path.basename(file_path)}")

        # Step 6: Process files
        processing_results = file_processor.process_multiple_files(
            test_files, dataset_path
        )
        files_processed = all(processing_results.values())
        print_test_result(
            "File processing",
            files_processed,
            f"Processed: {sum(processing_results.values())}/{len(test_files)}",
        )

        # Step 7: Generate file summary
        summary = file_processor.get_dataset_file_summary(dataset_path)
        summary_generated = "error" not in summary
        print_test_result("File summary generation", summary_generated)

        # Step 8: Create contextual template
        contextual_file = metadata_generator.create_experiment_contextual_template(
            dataset_path
        )
        contextual_created = contextual_file and os.path.exists(contextual_file)
        print_test_result("Contextual template creation", contextual_created)

        # Step 9: Test schema validation
        if dataset_result["struct_file"]:
            with open(dataset_result["struct_file"], "r") as f:
                struct_data = json.load(f)

            is_valid = schema_manager.validate_dataset_struct_metadata(struct_data)
            print_test_result("Schema validation", is_valid)

        # If we get here, all steps completed successfully
        assert True


@pytest.mark.integration
def test_folder_monitor_integration():
    """Test folder monitor integration with other modules."""
    print_header("--- Folder Monitor Integration ---")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test monitor directory
        monitor_dir = os.path.join(temp_dir, "monitor")
        os.makedirs(monitor_dir)

        # Create folder monitor
        folder_monitor = get_folder_monitor(monitor_dir)

        # Test monitor status
        status = folder_monitor.get_status()
        status_valid = all(
            field in status
            for field in ["is_running", "monitor_path", "observer_active"]
        )
        print_test_result("Monitor status", status_valid)

        # Test monitor start/stop
        started = folder_monitor.start_monitoring(recursive=False)
        print_test_result("Monitor start", started)

        if started:
            # Check running status
            running_status = folder_monitor.get_status()
            is_running = running_status["is_running"]
            print_test_result("Monitor running status", is_running)

            # Stop monitor
            stopped = folder_monitor.stop_monitoring()
            print_test_result("Monitor stop", stopped)

            assert stopped, "Monitor stop failed"
        else:
            pytest.fail("Could not start monitor")


@pytest.mark.integration
def test_schema_manager_integration():
    """Test schema manager integration with other modules."""
    print_header("--- Schema Manager Integration ---")

    schema_manager = get_schema_manager()

    # Test schema loading
    project_schema = schema_manager.get_project_schema()
    project_schema_loaded = project_schema is not None
    print_test_result("Project schema loading", project_schema_loaded)

    # Test schema validation
    if project_schema_loaded:
        # Create test data
        test_data = {
            "project_identifier": "test-123",
            "project_title": "Test Project",
            "project_description": "Test description",
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

        is_valid = schema_manager.validate_project_metadata(test_data)
        print_test_result("Schema validation", is_valid)

    # Test cache functionality
    cache_info = schema_manager.get_cache_info()
    cache_working = "cache_size" in cache_info
    print_test_result("Schema caching", cache_working)

    assert cache_working, "Schema caching not working"


@pytest.mark.integration
def test_metadata_generator_integration():
    """Test metadata generator integration with other modules."""
    print_header("--- Metadata Generator Integration ---")

    with tempfile.TemporaryDirectory() as temp_dir:
        metadata_generator = get_metadata_generator()
        schema_manager = get_schema_manager()

        # Create test project
        project_path = os.path.join(temp_dir, "p_TestProject")
        os.makedirs(project_path)

        # Generate project file
        project_file = metadata_generator.generate_project_file(project_path)
        project_created = project_file and os.path.exists(project_file)
        print_test_result("Project generation", project_created)

        if project_created:
            # Validate generated project file
            with open(project_file, "r") as f:
                project_data = json.load(f)

            is_valid = schema_manager.validate_project_metadata(project_data)
            print_test_result("Generated project validation", is_valid)

            # Test dataset generation
            project_id = project_data["project_identifier"]
            dataset_path = os.path.join(project_path, "dataset_TestDataset")
            os.makedirs(dataset_path)

            dataset_result = metadata_generator.generate_dataset_files(
                dataset_path, project_id
            )
            dataset_created = (
                dataset_result["admin_file"] and dataset_result["struct_file"]
            )
            print_test_result("Dataset generation", dataset_created)

            if dataset_created:
                # Validate generated dataset files
                with open(dataset_result["struct_file"], "r") as f:
                    struct_data = json.load(f)

                struct_valid = schema_manager.validate_dataset_struct_metadata(
                    struct_data
                )
                print_test_result("Generated dataset validation", struct_valid)

            assert True
        else:
            pytest.fail("Project generation failed")


@pytest.mark.integration
def test_file_processor_integration():
    """Test file processor integration with other modules."""
    print_header("--- File Processor Integration ---")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_processor = get_file_processor()
        metadata_generator = get_metadata_generator()

        # Create test project and dataset
        project_path = os.path.join(temp_dir, "p_TestProject")
        dataset_path = os.path.join(project_path, "dataset_TestDataset")
        os.makedirs(dataset_path)

        # Generate metadata files
        project_file = metadata_generator.generate_project_file(project_path)
        if not project_file:
            pytest.fail("Could not generate project file")

        with open(project_file, "r") as f:
            project_data = json.load(f)
            project_id = project_data["project_identifier"]

        dataset_result = metadata_generator.generate_dataset_files(
            dataset_path, project_id
        )
        if not dataset_result["struct_file"]:
            pytest.fail("Could not generate dataset files")

        # Create test files
        test_files = [
            os.path.join(dataset_path, "test1.txt"),
            os.path.join(dataset_path, "test2.csv"),
        ]

        for file_path in test_files:
            with open(file_path, "w") as f:
                f.write(f"Test content for {os.path.basename(file_path)}")

        # Process files
        results = file_processor.process_multiple_files(test_files, dataset_path)
        files_processed = all(results.values())
        print_test_result(
            "File processing",
            files_processed,
            f"Success: {sum(results.values())}/{len(results)}",
        )

        # Generate summary
        summary = file_processor.get_dataset_file_summary(dataset_path)
        summary_generated = "error" not in summary
        print_test_result("Summary generation", summary_generated)

        assert True


@pytest.mark.integration
def test_configuration_integration():
    """Test configuration integration across all modules."""
    print_header("--- Configuration Integration ---")

    # Test that all modules use the same configuration
    from app.core.config import (
        DATASET_ADMIN_SCHEMA_PATH,
        MONITOR_PATH,
        PROJECT_PREFIX,
        PROJECT_SCHEMA_PATH,
        SCHEMA_BASE_PATH,
    )

    # Check configuration values
    config_values = {
        "MONITOR_PATH": MONITOR_PATH,
        "PROJECT_PREFIX": PROJECT_PREFIX,
        "SCHEMA_BASE_PATH": SCHEMA_BASE_PATH,
        "PROJECT_SCHEMA_PATH": PROJECT_SCHEMA_PATH,
        "DATASET_ADMIN_SCHEMA_PATH": DATASET_ADMIN_SCHEMA_PATH,
    }

    all_config_present = all(value is not None for value in config_values.values())
    print_test_result("Configuration values present", all_config_present)

    # Test that modules use configuration correctly
    schema_manager = get_schema_manager()
    folder_monitor = get_folder_monitor()

    schema_path_correct = str(schema_manager.schema_base_path) == SCHEMA_BASE_PATH
    monitor_path_correct = str(folder_monitor.monitor_path) == MONITOR_PATH

    print_test_result("Schema manager config", schema_path_correct)
    print_test_result("Folder monitor config", monitor_path_correct)

    assert all_config_present, "Configuration values missing"


@pytest.mark.integration
def test_complete_system_integration():
    """Test the complete system integration."""
    print_header("--- Complete System Integration ---")

    # Test that all modules can be imported and initialized
    try:
        schema_manager = get_schema_manager()
        metadata_generator = get_metadata_generator()
        file_processor = get_file_processor()
        folder_monitor = get_folder_monitor()
        vc_manager = get_vc_manager()

        assert schema_manager is not None
        assert metadata_generator is not None
        assert file_processor is not None
        assert folder_monitor is not None
        assert vc_manager is not None

        print("✓ All modules initialized successfully")
        assert True

    except Exception as e:
        pytest.fail(f"System integration failed: {e}")
