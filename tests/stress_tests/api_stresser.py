import logging
import random
import time
import os
import json
from threading import Thread, Lock
from unittest.mock import MagicMock

# Configure logger for this module
logger = logging.getLogger(__name__)

# Base path where file_stresser creates files, used for dynamic discovery
BASE_MONITOR_PATH = "./monitored_directory"
API_BASE_URL = "http://localhost:8000/api"

# --- Mocked Requests Library ---
# This class simulates the behavior of the 'requests' library by interacting
# with the file system, just as a real API would.

class MockResponse:
    def __init__(self, json_data, status_code, reason=""):
        self.json_data = json_data
        self.status_code = status_code
        self.reason = reason
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code} {self.reason}")

class MockRequests:
    def get(self, url, **kwargs):
        logger.debug(f"Mock GET request to: {url}")
        if url.endswith("/projects"):
            return self._get_projects()
        elif "/projects/" in url and url.endswith("/datasets"):
            parts = url.split('/')
            project_id = parts[-2]
            return self._get_datasets(project_id)
        return MockResponse({"error": "Not Found"}, 404)

    def put(self, url, json=None, **kwargs):
        logger.debug(f"Mock PUT request to: {url} with payload: {json}")
        # Simulate validation
        if json and "name" in json and "author" in json:
             # In a real scenario, this would update a file
            return MockResponse({"status": "updated"}, 200)
        return MockResponse({"error": "Invalid payload"}, 400)

    def post(self, url, **kwargs):
        logger.debug(f"Mock POST request to: {url}")
        if "/finalize" in url:
            # Simulate a finalization process
            return MockResponse({"status": "finalization_started"}, 202)
        return MockResponse({"error": "Not Found"}, 404)

    def _get_projects(self):
        try:
            if not os.path.exists(BASE_MONITOR_PATH):
                return MockResponse([], 200)

            all_items = os.listdir(BASE_MONITOR_PATH)
            project_dirs = [d for d in all_items if os.path.isdir(os.path.join(BASE_MONITOR_PATH, d)) and d.startswith('p_')]
            response_data = [{"id": proj_id, "name": proj_id} for proj_id in project_dirs]
            return MockResponse(response_data, 200)
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)

    def _get_datasets(self, project_id):
        project_path = os.path.join(BASE_MONITOR_PATH, project_id)
        try:
            if not os.path.exists(project_path):
                return MockResponse({"error": "Project not found"}, 404)

            all_items = os.listdir(project_path)
            dataset_dirs = [d for d in all_items if os.path.isdir(os.path.join(project_path, d)) and d.startswith('d_')]
            response_data = [{"id": ds_id, "name": ds_id} for ds_id in dataset_dirs]
            return MockResponse(response_data, 200)
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)

# Instantiate the mock
requests = MockRequests()

# --- API Interaction Logic ---

def log_api_call(run_id, endpoint, method, status_code, latency_ms, outcome):
    """Logs a structured message for an API call."""
    logger.info(
        "API request completed",
        extra={
            'details': {
                'run_id': run_id,
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'latency_ms': latency_ms,
                'outcome': outcome
            }
        }
    )

def get_random_target(run_id):
    """Dynamically discovers a random project and dataset via the (mocked) API."""
    start_time = time.time()
    outcome = "failure"
    status_code = -1
    project_id, dataset_id = None, None
    try:
        # Get projects
        endpoint = "/projects"
        projects_resp = requests.get(f"{API_BASE_URL}{endpoint}")
        latency = (time.time() - start_time) * 1000
        status_code = projects_resp.status_code
        if status_code < 500: outcome = "success"
        log_api_call(run_id, endpoint, "GET", status_code, latency, outcome)
        projects_resp.raise_for_status()

        projects = projects_resp.json()
        if not projects:
            return None

        project = random.choice(projects)
        project_id = project['id']

        # Get datasets for the chosen project
        start_time = time.time()
        endpoint = f"/projects/{project_id}/datasets"
        datasets_resp = requests.get(f"{API_BASE_URL}{endpoint}")
        latency = (time.time() - start_time) * 1000
        status_code = datasets_resp.status_code
        if status_code < 500: outcome = "success"
        log_api_call(run_id, endpoint, "GET", status_code, latency, outcome)
        datasets_resp.raise_for_status()

        datasets = datasets_resp.json()
        if not datasets:
            return None

        dataset = random.choice(datasets)
        dataset_id = dataset['id']

        return project_id, dataset_id

    except Exception as e:
        logger.error(f"Failed to get random target: {e}", exc_info=False)
        return None

def generate_metadata_payload(is_valid=True):
    """Generates a random metadata payload, can be valid or invalid."""
    payload = {
        "name": f"Dataset_{int(time.time())}",
        "author": f"user_{random.randint(100, 999)}",
        "source_system": f"ERP{random.randint(1000, 9999)}",
        "is_confidential": random.choice([True, False])
    }
    if not is_valid:
        # Make it invalid by removing a required key
        del payload['name']
    return payload

# --- "User" Simulation Functions ---

def browsing_user(run_id):
    """Simulates a user browsing projects and datasets."""
    logger.debug("Browsing user action started.")
    target = get_random_target(run_id)
    if target is None:
        logger.debug("Browsing user found no target.")

def editing_user(run_id):
    """Simulates a user editing a dataset's metadata."""
    logger.debug("Editing user action started.")
    target = get_random_target(run_id)
    if target is None:
        logger.debug("Editing user found no target to edit.")
        return

    _, dataset_id = target

    # 75% chance to send a valid payload, 25% for invalid
    is_valid_payload = random.random() < 0.75
    payload = generate_metadata_payload(is_valid=is_valid_payload)

    start_time = time.time()
    outcome = "failure"
    status_code = -1
    endpoint = f"/datasets/{dataset_id}/metadata/administrative.json"
    try:
        resp = requests.put(f"{API_BASE_URL}{endpoint}", json=payload)
        status_code = resp.status_code
        if status_code < 500: outcome = "success"
    except Exception:
        outcome = "connection_error"
    finally:
        latency = (time.time() - start_time) * 1000
        log_api_call(run_id, endpoint, "PUT", status_code, latency, outcome)

def finalizing_user(run_id):
    """Simulates a user finalizing a dataset."""
    logger.debug("Finalizing user action started.")
    target = get_random_target(run_id)
    if target is None:
        logger.debug("Finalizing user found no target to finalize.")
        return

    _, dataset_id = target

    start_time = time.time()
    outcome = "failure"
    status_code = -1
    endpoint = f"/datasets/{dataset_id}/finalize"
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}")
        status_code = resp.status_code
        if status_code < 500: outcome = "success"
    except Exception:
        outcome = "connection_error"
    finally:
        latency = (time.time() - start_time) * 1000
        log_api_call(run_id, endpoint, "POST", status_code, latency, outcome)

# --- Main Test Runner ---

def main(run_id, duration_seconds=30):
    """Main function to run the API stress test."""
    # VERY FIRST STEP: Configure the logger for THIS process.
    from . import logger_config
    logger_config.setup_logger(run_id)

    logger.info("====== Starting API Stress Test Suite ======")

    user_actions = [browsing_user, editing_user, finalizing_user]
    # Define the mix of users
    action_weights = [0.6, 0.3, 0.1] # 60% browsers, 30% editors, 10% finalizers

    end_time = time.time() + duration_seconds
    threads = []

    while time.time() < end_time:
        action = random.choices(user_actions, weights=action_weights, k=1)[0]

        # We use threads to simulate concurrent users
        thread = Thread(target=action, args=(run_id,))
        threads.append(thread)
        thread.start()

        time.sleep(random.uniform(0.05, 0.2)) # Stagger user actions

    for thread in threads:
        thread.join()

    logger.info("====== API Stress Test Suite Finished ======")


if __name__ == '__main__':
    # This block is for standalone testing of the API stresser module.
    from .logger_config import setup_logger
    from . import file_stresser # To create some initial data to test against

    test_run_id = f"standalone_api_test_{int(time.time())}"
    logger = setup_logger(test_run_id)

    print("Setting up initial file structure for API test...")
    os.makedirs(BASE_MONITOR_PATH, exist_ok=True)
    # Create a couple of projects for the API to find
    file_stresser.create_project_structure((BASE_MONITOR_PATH, test_run_id))
    file_stresser.create_project_structure((BASE_MONITOR_PATH, test_run_id))
    print("Initial file structure created.")

    try:
        main(test_run_id, duration_seconds=10)
    except Exception as e:
        logger.critical(f"An unhandled exception occurred in api_stresser: {e}", exc_info=True)
    finally:
        print("\nStandalone test finished. Cleaning up files...")
        file_stresser.cleanup(BASE_MONITOR_PATH, test_run_id)
        print("Cleanup complete.")
