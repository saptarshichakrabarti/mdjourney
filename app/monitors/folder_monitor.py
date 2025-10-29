"""
Folder monitoring module for the FAIR metadata automation system.
Handles real-time monitoring of folder creation and file changes.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from app.core.config import (
    DATASET_PREFIX,
    PROJECT_PREFIX,
    get_monitor_path,
)
from app.services.file_processor import process_file_with_dirmeta
from app.services.metadata_generator import (
    check_contextual_metadata_completion,
    generate_complete_metadata_file,
    generate_dataset_files,
    generate_project_file,
    get_metadata_generator,
)


class FolderCreationHandler(FileSystemEventHandler):
    """Handles file system events for folder and file creation/modification."""

    def __init__(self) -> None:
        """Initialize the folder creation handler."""
        print("Initializing FolderCreationHandler...")

        from app.services.file_processor import get_file_processor
        from app.services.metadata_generator import get_metadata_generator

        self.metadata_generator = get_metadata_generator()
        self.file_processor = get_file_processor()
        print("FolderCreationHandler initialized successfully")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle folder and file creation events."""
        src_path = str(event.src_path)
        print(f"Event: Created - {src_path} (is_directory: {event.is_directory})")
        print(f"Event handler: {self}")

        # Temporarily disable filtering to debug
        # if self._should_ignore_path(src_path):
        #     print(f"Ignoring: {src_path}")
        #     return

        if event.is_directory:
            print(f"Handling directory creation: {src_path}")
            self._handle_directory_creation(src_path)
        else:
            print(f"Handling file creation: {src_path}")
            self._handle_file_creation(src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file and directory move events."""
        src_path = str(event.src_path)
        dest_path = str(event.dest_path)
        print(
            f"Event: Moved - {src_path} -> {dest_path} (is_directory: {event.is_directory})"
        )

        if self._should_ignore_path(dest_path):
            print(f"Ignoring: {dest_path}")
            return

        if event.is_directory:
            self._handle_directory_creation(dest_path)
        else:
            # Prefer dataset-root aware handling for moved files as well
            dataset_root = self._find_dataset_root(dest_path)
            if dataset_root is not None and not self._should_ignore_path(dest_path):
                print(f"Processing moved file in dataset (nested supported): {dest_path}")
                process_file_with_dirmeta(dest_path, dataset_root)
            else:
                self._handle_file_creation(dest_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events for Phase 5 triggers."""
        src_path = str(event.src_path)
        if self._should_ignore_path(src_path):
            return

        if not event.is_directory:
            self._handle_file_modification(src_path)

    def _should_ignore_path(self, path: str) -> bool:
        """Check if a path should be ignored (Git/DVC files, etc.)."""
        # Ignore Git and DVC files/directories
        if any(part in path for part in [
            ".git", ".dvc", "__pycache__", ".DS_Store",
            "node_modules", ".venv", "venv", "env", "dist", "build", ".next"
        ]):
            return True

        # Ignore temporary files created by editors
        if any(part in path for part in [".tmp", ".swp", ".swo", "~", ".bak"]):
            return True

        # Ignore metadata files themselves to avoid loops (only for files, not directories)
        if (
            os.path.isfile(path)
            and path.endswith((".json", ".md", ".txt"))
            and ".metadata" in path
        ):
            return True

        # Ignore schema template directories - these should not contain data files
        if ".template_schemas" in path:
            return True

        return False

    def _handle_directory_creation(self, path: str) -> None:
        """Handle directory creation events."""
        dirname = os.path.basename(path)

        # Ignore system folders at the very start
        if dirname.startswith(".") or dirname in [
            ".metadata",
            ".git",
            ".dvc",
            "__pycache__",
        ]:
            print(f"Ignoring system folder: {dirname}")
            return

        if dirname.startswith(PROJECT_PREFIX):
            print(f"Project folder detected: {path}")
            try:
                generate_project_file(path)
            except Exception as e:
                print(f"Error generating project file: {e}")
        elif dirname.startswith(DATASET_PREFIX):
            # Check if it's a dataset folder (inside a project folder)
            parent_dir = os.path.dirname(path)
            parent_dirname = os.path.basename(parent_dir)
            if parent_dirname.startswith(PROJECT_PREFIX):
                print(f"Dataset folder detected: {path}")
                try:
                    # Get project ID from parent project folder
                    project_file_path = os.path.join(
                        parent_dir, ".metadata", "project_descriptive.json"
                    )
                    project_id = None

                    if os.path.exists(project_file_path):
                        try:
                            with open(project_file_path, "r") as f:
                                project_data = json.load(f)
                                project_id = project_data.get("project_identifier")
                        except Exception as e:
                            print(f"Error reading project file: {e}")

                    if project_id:
                        print(
                            f"Generating dataset metadata with project ID: {project_id}"
                        )
                        generate_dataset_files(path, project_id)
                    else:
                        # Use the project folder name as fallback project ID
                        fallback_project_id = parent_dirname
                        print(f"Using fallback project ID: {fallback_project_id}")
                        generate_dataset_files(path, fallback_project_id)
                except Exception as e:
                    print(f"Error generating dataset files: {e}")
            else:
                print(
                    f"Warning: Dataset folder '{dirname}' created outside of a project folder. Dataset folders must be inside project folders (p_*)."
                )
        else:
            # Check if it's a dataset folder (inside a project folder) - legacy support
            # But ignore .metadata folders and other system folders
            if dirname.startswith(".") or dirname in [".metadata", ".git", ".dvc"]:
                print(f"Ignoring system folder: {dirname}")
                return

            parent_dir = os.path.dirname(path)
            parent_dirname = os.path.basename(parent_dir)
            if parent_dirname.startswith(PROJECT_PREFIX):
                print(
                    f"Warning: Non-prefixed folder '{dirname}' created in project folder. Consider using '{DATASET_PREFIX}' prefix for dataset folders."
                )
                print(f"Attempting to generate dataset metadata for: {path}")

                # Try to generate dataset metadata
                project_file_path = os.path.join(
                    parent_dir, ".metadata", "project_descriptive.json"
                )
                project_id = None

                if os.path.exists(project_file_path):
                    try:
                        with open(project_file_path, "r") as f:
                            project_data = json.load(f)
                            project_id = project_data.get("project_identifier")
                    except Exception as e:
                        print(f"Error reading project file: {e}")

                if project_id:
                    print(f"Generating dataset metadata with project ID: {project_id}")
                    generate_dataset_files(path, project_id)
                else:
                    # Use the project folder name as fallback project ID
                    fallback_project_id = parent_dirname
                    print(f"Using fallback project ID: {fallback_project_id}")
                    generate_dataset_files(path, fallback_project_id)

    def _handle_file_creation(self, file_path: str) -> None:
        """Handle file creation events."""
        # Add a small delay to ensure file is fully written
        import time

        time.sleep(0.1)

        # Check if file still exists (might be a temporary file that was deleted)
        if not os.path.exists(file_path):
            print(f"File no longer exists, skipping: {file_path}")
            return

        # Check if this path should be ignored (including .metadata directories)
        if self._should_ignore_path(file_path):
            print(f"Ignoring file creation: {file_path}")
            return

        dataset_path = os.path.dirname(file_path)

        # Skip if we're inside a .metadata directory or if the file itself is in a .metadata directory
        if ".metadata" in dataset_path or ".metadata" in file_path:
            print(f"Skipping file creation inside .metadata directory: {file_path}")
            return

        # Try to find the dataset root (supports nested files in subfolders)
        dataset_root = self._find_dataset_root(file_path)

        if dataset_root is not None:
            if not self._should_ignore_path(file_path):
                print(f"New file detected in dataset (nested supported): {file_path}")
                process_file_with_dirmeta(file_path, dataset_root)
            return

        else:
            # Check if this might be a dataset folder that needs metadata generation
            parent_dir = os.path.dirname(dataset_path)
            parent_dirname = os.path.basename(parent_dir)
            dataset_dirname = os.path.basename(dataset_path)

            if parent_dirname.startswith(PROJECT_PREFIX):
                # Check if the folder has the proper dataset prefix
                if dataset_dirname.startswith(DATASET_PREFIX):
                    print(f"File created in dataset folder: {file_path}")
                    print(
                        f"Attempting to generate dataset metadata for: {dataset_path}"
                    )

                    # Try to generate dataset metadata
                    project_file_path = os.path.join(
                        parent_dir, ".metadata", "project_descriptive.json"
                    )
                    project_id = None

                    if os.path.exists(project_file_path):
                        try:
                            with open(project_file_path, "r") as f:
                                project_data = json.load(f)
                                project_id = project_data.get("project_identifier")
                        except Exception as e:
                            print(f"Error reading project file: {e}")

                    if project_id:
                        print(
                            f"Generating dataset metadata with project ID: {project_id}"
                        )
                        generate_dataset_files(dataset_path, project_id)
                        # Now process the file
                        if not self._should_ignore_path(file_path):
                            print(
                                f"Processing file after metadata generation: {file_path}"
                            )
                            process_file_with_dirmeta(file_path, dataset_path)
                    else:
                        print(
                            f"Could not determine project ID for dataset: {dataset_path}"
                        )
                else:
                    print(
                        f"Warning: File created in non-prefixed folder '{dataset_dirname}' within project. Consider using '{DATASET_PREFIX}' prefix for dataset folders."
                    )
                    print(
                        f"Attempting to generate dataset metadata for: {dataset_path}"
                    )

                    # Try to generate dataset metadata (legacy support)
                    project_file_path = os.path.join(
                        parent_dir, ".metadata", "project_descriptive.json"
                    )
                    project_id = None

                    if os.path.exists(project_file_path):
                        try:
                            with open(project_file_path, "r") as f:
                                project_data = json.load(f)
                                project_id = project_data.get("project_identifier")
                        except Exception as e:
                            print(f"Error reading project file: {e}")

                    if project_id:
                        print(
                            f"Generating dataset metadata with project ID: {project_id}"
                        )
                        generate_dataset_files(dataset_path, project_id)
                        # Now process the file
                        if not self._should_ignore_path(file_path):
                            print(
                                f"Processing file after metadata generation: {file_path}"
                            )
                            process_file_with_dirmeta(file_path, dataset_path)
                    else:
                        print(
                            f"Could not determine project ID for dataset: {dataset_path}"
                        )

    def _find_dataset_root(self, path: str):
        """Walk up from a file/dir to locate the nearest directory containing a dataset_structural.json.

        Returns the dataset root path or None if not found.
        """
        try:
            current = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path))
            while True:
                struct_path = os.path.join(current, ".metadata", "dataset_structural.json")
                if os.path.exists(struct_path):
                    return current
                parent = os.path.dirname(current)
                if parent == current:
                    return None
                current = parent
        except Exception:
            return None

    def _handle_file_modification(self, file_path: str) -> None:
        """Handle file modification events for Phase 5 triggers."""
        # Check if this is an experiment contextual metadata file
        if (
            file_path.endswith("experiment_contextual.json")
            and ".metadata" in file_path
        ):
            dataset_path = os.path.dirname(
                os.path.dirname(file_path)
            )  # Go up from .metadata
            print(f"Experiment contextual metadata modified: {file_path}")

            # Check if contextual metadata is complete (Trigger 5)
            is_complete, experiment_id = check_contextual_metadata_completion(
                dataset_path
            )
            if is_complete and experiment_id:
                print(
                    f"Contextual metadata complete, generating V2 metadata: {experiment_id}"
                )
                generate_complete_metadata_file(dataset_path, experiment_id)


class FolderMonitor:
    """Manages folder monitoring for the FAIR metadata system."""

    def __init__(self, monitor_path: Optional[str] = None) -> None:
        """Initialize the folder monitor.

        Args:
            monitor_path: Path to monitor (defaults to config)
        """
        if monitor_path:
            # Path is provided directly (e.g., from --path)
            self.monitor_path = Path(monitor_path)
        else:
            # Get path from the already-initialized configuration
            self.monitor_path = get_monitor_path()

        # Ensure the global config reflects the active monitor path
        try:
            from app.core.config import set_monitor_path

            set_monitor_path(str(self.monitor_path))
        except Exception as e:
            print(f"Warning: Failed to update global MONITOR_PATH: {e}")

        self.observer: Optional[Any] = None
        self.event_handler: Optional[Any] = None
        self.is_running = False

    def _should_ignore_path(self, path: str) -> bool:
        """Check if a path should be ignored (Git/DVC files, etc.)."""
        # Ignore Git and DVC files/directories
        if any(part in path for part in [
            ".git", ".dvc", "__pycache__", ".DS_Store",
            "node_modules", ".venv", "venv", "env", "dist", "build", ".next"
        ]):
            return True

        # Ignore temporary files created by editors
        if any(part in path for part in [".tmp", ".swp", ".swo", "~", ".bak"]):
            return True

        # Ignore metadata files themselves to avoid loops (only for files, not directories)
        if (
            os.path.isfile(path)
            and path.endswith((".json", ".md", ".txt"))
            and ".metadata" in path
        ):
            return True

        # Ignore schema template directories - these should not contain data files
        if ".template_schemas" in path:
            return True

        return False

    def start_monitoring(self, recursive: bool = True) -> bool:
        """Start monitoring the specified path.

        Args:
            recursive: Whether to monitor subdirectories recursively

        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            if self.is_running:
                print("Monitoring is already running")
                return True

            # Ensure the monitor path exists
            self.monitor_path.mkdir(parents=True, exist_ok=True)

            # Create event handler and observer
            print("Creating event handler...")
            self.event_handler = FolderCreationHandler()
            print("Creating observer...")
            self.observer = Observer()
            print(
                f"Scheduling observer for path: {self.monitor_path} (recursive: {recursive})"
            )
            self.observer.schedule(
                self.event_handler, str(self.monitor_path), recursive=recursive
            )

            # Start monitoring
            print("Starting observer...")
            self.observer.start()
            self.is_running = True
            print(f"Started monitoring: {self.monitor_path}")
            print(f"Observer alive: {self.observer.is_alive()}")

            # Process existing files that might have been moved while monitor was off
            self._process_existing_files()

            return True

        except Exception as e:
            print(f"Error starting monitoring: {e}")
            return False

    def _process_existing_files(self) -> None:
        """Process existing files and generate missing metadata for existing directories."""
        print("Processing existing files and directories...")

        for root, dirs, files in os.walk(self.monitor_path):
            # Skip ignored directories
            dirs[:] = [
                d for d in dirs if not self._should_ignore_path(os.path.join(root, d))
            ]

            # Generate missing project/dataset metadata
            try:
                dirname = os.path.basename(root)
                # Project-level metadata
                if dirname.startswith(PROJECT_PREFIX):
                    project_metadata_path = os.path.join(
                        root, ".metadata", "project_descriptive.json"
                    )
                    project_admin_metadata_path = os.path.join(
                        root, ".metadata", "project_administrative.json"
                    )

                    if not os.path.exists(project_metadata_path):
                        print(f"Generating missing project metadata for: {root}")
                        try:
                            generate_project_file(root)
                        except Exception as e:
                            print(f"Error generating project file for {root}: {e}")

                    # Generate missing project administrative metadata
                    if not os.path.exists(project_admin_metadata_path) and os.path.exists(project_metadata_path):
                        print(f"Generating missing project administrative metadata for: {root}")
                        try:
                            # Get project ID from existing project descriptive metadata
                            with open(project_metadata_path, "r") as f:
                                project_data = json.load(f)
                                project_id = project_data.get("project_identifier")

                            if project_id:
                                # Generate project administrative metadata
                                metadata_dir = os.path.join(root, ".metadata")
                                generator = get_metadata_generator()
                                generator._generate_project_admin_file(root, project_id, metadata_dir)
                            else:
                                print(f"Could not find project ID in {project_metadata_path}")
                        except Exception as e:
                            print(f"Error generating project administrative metadata for {root}: {e}")

                    # Ensure dataset metadata inside this project
                    for d in list(dirs):
                        dataset_dir = os.path.join(root, d)
                        if os.path.isdir(dataset_dir):
                            if d.startswith(DATASET_PREFIX) or not d.startswith("."):
                                struct_path = os.path.join(
                                    dataset_dir, ".metadata", "dataset_structural.json"
                                )
                                if not os.path.exists(struct_path):
                                    print(
                                        f"Generating missing dataset metadata for: {dataset_dir}"
                                    )
                                    project_id = None
                                    try:
                                        with open(project_metadata_path, "r") as pf:
                                            pdata = json.load(pf)
                                            project_id = pdata.get("project_identifier")
                                    except Exception:
                                        project_id = None
                                    if not project_id:
                                        project_id = dirname
                                    try:
                                        generate_dataset_files(dataset_dir, project_id)
                                    except Exception as e:
                                        print(
                                            f"Error generating dataset files for {dataset_dir}: {e}"
                                        )
            except Exception as e:
                print(f"Error during existing directory processing at {root}: {e}")

            # Process existing files in already-identified dataset directories
            if os.path.exists(
                os.path.join(root, ".metadata", "dataset_structural.json")
            ):
                dataset_root = root
                for subroot, subdirs, subfiles in os.walk(dataset_root):
                    # Skip ignored directories (including .metadata) while descending
                    subdirs[:] = [
                        d for d in subdirs if not self._should_ignore_path(os.path.join(subroot, d))
                    ]
                    for file in subfiles:
                        file_path = os.path.join(subroot, file)
                        if not self._should_ignore_path(file_path):
                            print(f"Processing existing file: {file_path}")
                            process_file_with_dirmeta(file_path, dataset_root)

    def stop_monitoring(self) -> bool:
        """Stop monitoring.

        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        try:
            if not self.is_running or self.observer is None:
                print("Monitoring is not running")
                return True

            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("Stopped monitoring")
            return True

        except Exception as e:
            print(f"Error stopping monitoring: {e}")
            return False

    def run_continuously(self, recursive: bool = True) -> None:
        """Run monitoring continuously until interrupted.

        Args:
            recursive: Whether to monitor subdirectories recursively
        """
        if self.start_monitoring(recursive):
            try:
                print("Monitor is running. Press Ctrl+C to stop.")
                while self.is_running:
                    import time

                    time.sleep(1)
                    # Check if observer is still alive
                    if self.observer and not self.observer.is_alive():
                        print("Observer died unexpectedly!")
                        break
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                self.stop_monitoring()
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                self.stop_monitoring()

    def get_status(self) -> Dict[str, Any]:
        """Get the current monitoring status.

        Returns:
            Dictionary containing monitoring status information
        """
        return {
            "is_running": self.is_running,
            "monitor_path": str(self.monitor_path),
            "observer_active": self.observer.is_alive() if self.observer else False,
        }


# Global instance for singleton pattern
_folder_monitor: Optional[FolderMonitor] = None


def get_folder_monitor(monitor_path: Optional[str] = None) -> FolderMonitor:
    """Get the global folder monitor instance.

    Args:
        monitor_path: Path to monitor (optional)

    Returns:
        FolderMonitor instance
    """
    global _folder_monitor
    if _folder_monitor is None:
        _folder_monitor = FolderMonitor(monitor_path)
    return _folder_monitor


def start_monitoring(
    monitor_path: Optional[str] = None, recursive: bool = True
) -> bool:
    """Start folder monitoring.

    Args:
        monitor_path: Path to monitor (optional)
        recursive: Whether to monitor subdirectories recursively

    Returns:
        True if monitoring started successfully, False otherwise
    """
    monitor = get_folder_monitor(monitor_path)
    return monitor.start_monitoring(recursive)


def stop_monitoring() -> bool:
    """Stop folder monitoring.

    Returns:
        True if monitoring stopped successfully, False otherwise
    """
    global _folder_monitor
    if _folder_monitor is not None:
        return _folder_monitor.stop_monitoring()
    return True


def run_continuously(
    monitor_path: Optional[str] = None, recursive: bool = True
) -> bool:
    """Run folder monitoring continuously.

    Args:
        monitor_path: Path to monitor (optional)
        recursive: Whether to monitor subdirectories recursively

    Returns:
        True if monitoring started successfully, False otherwise
    """
    monitor = get_folder_monitor(monitor_path)
    monitor.run_continuously(recursive)
    return True


def get_monitor_status() -> Dict[str, Any]:
    """Get the current monitoring status.

    Returns:
        Dictionary containing monitoring status information
    """
    global _folder_monitor
    if _folder_monitor is not None:
        return _folder_monitor.get_status()
    return {
        "is_running": False,
        "monitor_path": str(get_monitor_path()),
        "observer_active": False,
    }


if __name__ == "__main__":
    """Run the folder monitor when executed directly."""
    import argparse

    from app.core.config import find_config_file, initialize_config

    parser = argparse.ArgumentParser(description="FAIR Metadata Folder Monitor")
    parser.add_argument("--path", help="Path to monitor (overrides config file)")
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't monitor subdirectories recursively",
    )

    args = parser.parse_args()

    # --- CENTRALIZED CONFIGURATION LOGIC ---
    # If a path is NOT provided via command line, load from the config file.
    if not args.path:
        print("No --path argument provided, searching for .fair_meta_config.yaml...")
        config_file = find_config_file()
        if config_file:
            print(f"Found config file: {config_file}")
            if not initialize_config(str(config_file)):
                print("FATAL: Could not initialize configuration from file. Exiting.")
                sys.exit(1)
        else:
            print("FATAL: No config file found and no --path specified. Exiting.")
            sys.exit(1)
    # ----------------------------------------

    try:
        print("Starting FAIR Metadata Folder Monitor...")
        # Now run_continuously will use the config that we just loaded.
        # The args.path will correctly override it if provided.
        success = run_continuously(
            monitor_path=args.path, recursive=not args.no_recursive
        )
        if success:
            print("Folder monitor started successfully")
        else:
            print("Failed to start folder monitor")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping folder monitor...")
        stop_monitoring()
    except Exception as e:
        print(f"Error running folder monitor: {e}")
        sys.exit(1)
