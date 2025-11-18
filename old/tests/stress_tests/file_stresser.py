import logging
import os
import random
import shutil
import time
import uuid
from multiprocessing import Pool, cpu_count

# Configure logger for this module
logger = logging.getLogger(__name__)

# Define a base path for file operations. In a real scenario, this would
# be the directory monitored by the application.
BASE_MONITOR_PATH = "./monitored_directory"


def generate_unique_id():
    """Generates a short, unique identifier."""
    return str(uuid.uuid4())[:8]


def create_dummy_file(directory_path, file_size_kb_min=5, file_size_kb_max=50 * 1024):
    """Creates a file with a random name, extension, and size in the given directory."""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        extensions = ['.csv', '.bin', '.dat', '.txt', '.json', '.xml']
        filename = f"data_{generate_unique_id()}{random.choice(extensions)}"
        filepath = os.path.join(directory_path, filename)

        # Generate random file size in bytes
        file_size = random.randint(file_size_kb_min * 1024, file_size_kb_max * 1024)

        with open(filepath, 'wb') as f:
            f.write(os.urandom(file_size))

        logger.info(f"Created dummy file: {filepath} ({file_size / 1024:.2f} KB)")
        return filepath
    except Exception as e:
        logger.error(f"Failed to create dummy file in {directory_path}: {e}", exc_info=True)
        return None


def create_project_structure(args):
    """
    Creates a complete project folder with a random name, a random number of datasets,
    and dummy files. Designed to be called by multiprocessing.
    """
    base_path, run_id = args
    proj_id = generate_unique_id()
    project_folder_name = f"p_{run_id}_{proj_id}"
    project_path = os.path.join(base_path, project_folder_name)

    try:
        os.makedirs(project_path, exist_ok=True)
        logger.info(f"Created project folder: {project_path}")

        num_datasets = random.randint(2, 10)
        for _ in range(num_datasets):
            dataset_id = generate_unique_id()
            dataset_folder_name = f"d_{dataset_id}"
            dataset_path = os.path.join(project_path, dataset_folder_name)
            create_dummy_file(dataset_path)

        return project_path
    except Exception as e:
        logger.error(f"Failed to create project structure for {project_path}: {e}", exc_info=True)
        return None


def cleanup(base_path, run_id):
    """
    Safely removes all directories and files created during a specific test run.
    """
    logger.info(f"Starting cleanup for run_id: {run_id} in path: {base_path}")
    if not os.path.exists(base_path):
        logger.warning(f"Cleanup path {base_path} does not exist. Nothing to clean.")
        return

    items = os.listdir(base_path)
    cleanup_count = 0
    for item in items:
        # The naming convention is key to safe cleanup.
        if item.startswith(f"p_{run_id}_"):
            item_path = os.path.join(base_path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.info(f"Successfully removed directory: {item_path}")
                    cleanup_count += 1
            except Exception as e:
                logger.error(f"Failed to remove directory {item_path}: {e}", exc_info=True)
    logger.info(f"Cleanup complete. Removed {cleanup_count} project directories.")


# --- Stress Test Scenarios ---

def run_concurrency_test(base_path, run_id, num_projects=100):
    """Creates multiple projects in parallel to test concurrent file creation."""
    logger.info(f"--- Starting Concurrency Test: Creating {num_projects} projects ---")
    start_time = time.time()
    # Use half of the available CPUs to avoid overwhelming the system
    num_processes = max(1, cpu_count() // 2)
    with Pool(processes=num_processes) as pool:
        # Prepare arguments for each process
        args_list = [(base_path, run_id) for _ in range(num_projects)]
        pool.map(create_project_structure, args_list)
    duration = time.time() - start_time
    logger.info(f"--- Concurrency Test finished in {duration:.2f} seconds ---")


def run_breadth_test(base_path, run_id, num_datasets=2000):
    """Creates one project with thousands of datasets to test performance with wide directories."""
    logger.info(f"--- Starting Breadth Test: Creating {num_datasets} datasets in a single project ---")
    start_time = time.time()
    project_path = os.path.join(base_path, f"p_{run_id}_wide_project")
    os.makedirs(project_path, exist_ok=True)

    for i in range(num_datasets):
        dataset_id = generate_unique_id()
        dataset_path = os.path.join(project_path, f"d_{dataset_id}")
        create_dummy_file(dataset_path, file_size_kb_min=1, file_size_kb_max=50) # smaller files for this test
        if (i + 1) % 100 == 0:
            logger.info(f"Breadth Test progress: {i + 1}/{num_datasets} datasets created.")

    duration = time.time() - start_time
    logger.info(f"--- Breadth Test finished in {duration:.2f} seconds ---")


def run_churn_test(base_path, run_id, num_iterations=500, keep_fraction=0.1):
    """Creates and deletes datasets rapidly to test filesystem and monitoring churn."""
    logger.info(f"--- Starting Churn Test: {num_iterations} create/delete cycles ---")
    start_time = time.time()
    project_path = os.path.join(base_path, f"p_{run_id}_churn_project")
    os.makedirs(project_path, exist_ok=True)

    created_paths = []
    for i in range(num_iterations):
        # Create a dataset
        dataset_id = generate_unique_id()
        dataset_path = os.path.join(project_path, f"d_{dataset_id}")
        create_dummy_file(dataset_path, file_size_kb_min=1, file_size_kb_max=10)
        created_paths.append(dataset_path)

        # Delete a random existing dataset (but not all of them)
        if len(created_paths) > num_iterations * keep_fraction:
            path_to_delete = random.choice(created_paths)
            try:
                shutil.rmtree(path_to_delete)
                logger.info(f"Churn Test: Deleted {path_to_delete}")
                created_paths.remove(path_to_delete)
            except Exception as e:
                logger.error(f"Churn Test: Failed to delete {path_to_delete}: {e}")

        if (i + 1) % 50 == 0:
            logger.info(f"Churn Test progress: {i + 1}/{num_iterations} cycles complete.")

    duration = time.time() - start_time
    logger.info(f"--- Churn Test finished in {duration:.2f} seconds ---")


def main(run_id):
    """Main function to run all file stress tests."""
    # VERY FIRST STEP: Configure the logger for THIS process.
    from . import logger_config
    logger_config.setup_logger(run_id)

    # Ensure the base directory for monitoring exists
    os.makedirs(BASE_MONITOR_PATH, exist_ok=True)
    logger.info(f"Base monitoring path set to: {BASE_MONITOR_PATH}")

    logger.info("====== Starting File System Stress Test Suite ======")
    run_concurrency_test(BASE_MONITOR_PATH, run_id)
    run_breadth_test(BASE_MONITOR_PATH, run_id)
    run_churn_test(BASE_MONITOR_PATH, run_id)
    logger.info("====== File System Stress Test Suite Finished ======")


if __name__ == '__main__':
    # This block is for standalone testing of the file stresser module.
    # The `run_suite.py` script will be the main entry point for the whole suite.
    from .logger_config import setup_logger

    test_run_id = f"standalone_file_test_{int(time.time())}"
    logger = setup_logger(test_run_id)

    try:
        main(test_run_id)
    except Exception as e:
        logger.critical(f"An unhandled exception occurred in file_stresser: {e}", exc_info=True)
    finally:
        # In a standalone test, we clean up immediately.
        # In the full suite, cleanup is handled by run_suite.py.
        print("\nStandalone test finished. Starting cleanup...")
        cleanup(BASE_MONITOR_PATH, test_run_id)
        print("Cleanup complete.")
