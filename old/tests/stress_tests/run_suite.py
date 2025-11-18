import time
import logging
import subprocess
import os
from multiprocessing import Process

# Import our custom modules
from tests.stress_tests import logger_config
from tests.stress_tests import file_stresser
from tests.stress_tests import api_stresser

# --- Configuration ---
# The main directory where the file stresser will create its chaos.
# This should be the directory your application is monitoring.
MONITOR_PATH = file_stresser.BASE_MONITOR_PATH

# How long the API stress test should run while the file stresser is active.
API_STRESS_DURATION_SECONDS = 15

def main():
    """
    The main orchestrator for the entire stress test suite.
    """
    # 1. Setup Phase
    run_id = f"testrun_{int(time.time())}"
    logger = logger_config.setup_logger(run_id)

    log_file_name = f"test_run_{run_id}.log"
    report_file_name = f"test_run_{run_id}_summary.md"

    logger.info(
        "====== Fire-and-Forget Test Suite Starting ======",
        extra={'details': {'run_id': run_id, 'log_file': log_file_name}}
    )

    # Ensure the base directory for monitoring exists before starting
    os.makedirs(MONITOR_PATH, exist_ok=True)
    logger.info(f"Monitoring path set to: {os.path.abspath(MONITOR_PATH)}")

    file_process = None
    api_process = None

    try:
        # 2. Execution Phase
        # We use multiprocessing to run the file and API stressers truly concurrently.
        # This simulates a realistic scenario where the API is being used while the
        # underlying file system is under heavy load.

        logger.info("Starting concurrent file system and API stress tests...")

        # Create processes
        file_process = Process(target=file_stresser.main, args=(run_id,))
        api_process = Process(target=api_stresser.main, args=(run_id, API_STRESS_DURATION_SECONDS))

        # Start processes
        file_process.start()
        api_process.start()

        # Wait for both processes to complete their work
        api_process.join()
        logger.info("API stresser process has completed.")

        file_process.join()
        logger.info("File stresser process has completed.")

        logger.info("====== Test Execution Finished ======")

    except Exception as e:
        logger.critical(f"A critical error occurred during test execution: {e}", exc_info=True)
    finally:
        # 3. Cleanup & Reporting Phase
        # This block *must* run to ensure we clean up after ourselves and generate the report.

        logger.info("====== Starting Cleanup and Reporting Phase ======")

        # Ensure processes are terminated if they are still alive
        if file_process and file_process.is_alive():
            logger.warning("File stresser process did not terminate correctly. Terminating now.")
            file_process.terminate()
        if api_process and api_process.is_alive():
            logger.warning("API stresser process did not terminate correctly. Terminating now.")
            api_process.terminate()

        # a. Run the cleanup script
        logger.info(f"Running cleanup for run_id '{run_id}'...")
        try:
            file_stresser.cleanup(MONITOR_PATH, run_id)
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.error(f"An error occurred during cleanup: {e}", exc_info=True)

        # b. Run the reporting script
        logger.info("Generating performance report...")
        try:
            # We use subprocess to run the report generator as a separate step.
            # This mimics a real CI/CD pipeline and ensures it runs even if the main script had issues.
            command = ["python", "-m", "tests.stress_tests.generate_report", log_file_name]
            result = subprocess.run(command, capture_output=True, text=True, check=True)

            logger.info("Report generation script executed successfully.")
            print("\n" + "="*50)
            print("Stress test complete. Report generated.")
            print(f"  - Log file: {log_file_name}")
            print(f"  - Report file: {report_file_name}")
            print("="*50 + "\n")

            if result.stdout:
                logger.info(f"Report generator output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Report generator errors:\n{result.stderr}")

        except FileNotFoundError:
            logger.error(f"Could not find generate_report.py. Please ensure it is in the correct path.")
            print("\nERROR: Could not generate report. The 'generate_report.py' script was not found.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Report generation script failed with exit code {e.returncode}.")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            print(f"\nERROR: Report generation failed. Check the log file '{log_file_name}' for details.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while generating the report: {e}", exc_info=True)
            print("\nERROR: An unexpected error occurred during report generation.")

        logger.info("====== Test Suite Finished ======")

if __name__ == '__main__':
    # To run the entire suite, you execute this script.
    main()
