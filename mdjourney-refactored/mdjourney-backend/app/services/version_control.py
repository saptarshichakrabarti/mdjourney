"""
Version Control Integration Module
Handles Git and DVC operations for metadata and data versioning.
"""

import datetime
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class VersionControlManager:
    """Manages Git and DVC operations for the FAIR metadata system."""

    def __init__(self, repo_path: Optional[str] = None) -> None:
        """Initialize the version control manager.

        Args:
            repo_path: Path to the repository root (defaults to monitor_path from config)
        """
        # Get repo path from config if not provided
        if repo_path is None:
            try:
                from app.core.config import get_monitor_path
                self.repo_path = get_monitor_path()
            except RuntimeError:
                # Config not initialized, use current directory
                self.repo_path = Path(".").resolve()
        else:
            self.repo_path = Path(repo_path).resolve()

        self.git_path = self.repo_path / ".git"
        self.dvc_path = self.repo_path / ".dvc"

        # Check if Git/DVC are enabled in config
        try:
            from app.core.config import is_git_enabled, is_dvc_enabled
            self.git_enabled = is_git_enabled()
            self.dvc_enabled = is_dvc_enabled()
        except Exception:
            # Default to enabled if config not available
            self.git_enabled = True
            self.dvc_enabled = True

        # Initialize Git repository if enabled and it doesn't exist
        if self.git_enabled and not self.git_path.exists():
            self._init_git_repo()

        # Initialize DVC if enabled and not already initialized
        if self.dvc_enabled:
            self._init_dvc()

    def _init_git_repo(self) -> None:
        """Initialize a new Git repository at the repo root."""
        try:
            # Get Git config from app config
            try:
                from app.core.config import (
                    get_git_commit_prefix,
                    get_git_author_name,
                    get_git_author_email,
                )
                commit_prefix = get_git_commit_prefix()
                author_name = get_git_author_name()
                author_email = get_git_author_email()
            except Exception:
                commit_prefix = "FAIR Metadata:"
                author_name = "FAIR Metadata System"
                author_email = "metadata@example.com"

            # Initialize Git at the repo root
            subprocess.run(
                ["git", "init"], cwd=self.repo_path, check=True, capture_output=True
            )
            print(f"Initialized Git repository in {self.repo_path}")

            # Configure Git user
            subprocess.run(
                ["git", "config", "user.name", author_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", author_email],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Create a README file for initial commit
            readme_path = self.repo_path / "README.md"
            if not readme_path.exists():
                with open(readme_path, "w") as f:
                    f.write(
                        "# FAIR-Compliant Research Data Metadata System\n\nThis repository contains metadata and data files managed by the FAIR metadata automation system.\n"
                    )

                # Create initial commit
                subprocess.run(
                    ["git", "add", "README.md"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", f"{commit_prefix} Initial commit: FAIR metadata system setup"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
                print("Created initial Git commit")

        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e}")
            # Don't raise, just log - Git might not be available
        except FileNotFoundError:
            print("Git not found in PATH, skipping Git initialization")

    def _init_dvc(self) -> None:
        """Initialize DVC at the repo root if not already initialized."""
        try:
            # Check if DVC is already initialized
            if not self.dvc_path.exists():
                subprocess.run(
                    ["dvc", "init"], cwd=self.repo_path, check=True, capture_output=True
                )
                print("Initialized DVC")

                # Add .dvc to Git if Git is enabled
                if self.git_enabled and self.git_path.exists():
                    subprocess.run(
                        ["git", "add", ".dvc"],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                    )
                    try:
                        from app.core.config import get_git_commit_prefix
                        commit_prefix = get_git_commit_prefix()
                    except Exception:
                        commit_prefix = "FAIR Metadata:"
                    subprocess.run(
                        ["git", "commit", "-m", f"{commit_prefix} Initialize DVC"],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                    )
                    print("Added DVC to Git")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error initializing DVC: {e}")
            # Don't raise the error, just log it
            print("DVC initialization failed, but continuing...")

    def commit_metadata_changes(
        self, message: Optional[str] = None, files: Optional[List[str]] = None
    ) -> None:
        """Commit metadata changes to Git.

        Args:
            message: Commit message (optional)
            files: Specific files to commit (optional)
        """
        if not self.git_enabled or not self.git_path.exists():
            return

        try:
            # Get commit prefix from config
            try:
                from app.core.config import get_git_commit_prefix
                commit_prefix = get_git_commit_prefix()
            except Exception:
                commit_prefix = "FAIR Metadata:"

            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            if not status_result.stdout.strip():
                print("No changes to commit")
                return

            # Add metadata files to Git
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                    )
            else:
                # Add all .metadata directories and JSON files
                subprocess.run(
                    ["git", "add", "-A", "*.json", "*.md", "*.txt"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

            # Commit changes
            commit_message = message or "Update metadata files"
            if commit_prefix and not commit_message.startswith(commit_prefix):
                commit_message = f"{commit_prefix} {commit_message}"

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            print(f"Committed metadata changes: {commit_message}")

        except subprocess.CalledProcessError as e:
            print(f"Error committing metadata changes: {e}")
            # Don't raise, just log
        except FileNotFoundError:
            print("Git not found in PATH")

    def add_data_file_to_dvc(self, file_path: str, dataset_path: str) -> None:
        """Add a data file to DVC tracking.

        Args:
            file_path: Path to the data file to add
            dataset_path: Path to the dataset directory
        """
        if not self.dvc_enabled:
            return

        try:
            # Convert to relative path from repo root
            file_path_obj = Path(file_path).resolve()
            try:
                rel_file_path = file_path_obj.relative_to(self.repo_path)
            except ValueError:
                # File is outside repo, skip
                print(f"File {file_path} is outside repository root, skipping DVC tracking")
                return

            # Check if file is already tracked by DVC
            dvc_file = str(rel_file_path) + ".dvc"
            if (self.repo_path / dvc_file).exists():
                print(f"File {os.path.basename(file_path)} is already tracked by DVC")
                return

            # Add file to DVC (DVC will create .dvc file alongside the data file)
            subprocess.run(
                ["dvc", "add", str(rel_file_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Add the .dvc file to Git if Git is enabled
            if self.git_enabled and self.git_path.exists() and (self.repo_path / dvc_file).exists():
                subprocess.run(
                    ["git", "add", dvc_file],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

                # Check if there are changes to commit
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                if status_result.stdout.strip():
                    # Commit the .dvc file
                    filename = Path(file_path).name
                    try:
                        from app.core.config import get_git_commit_prefix
                        commit_prefix = get_git_commit_prefix()
                    except Exception:
                        commit_prefix = "FAIR Metadata:"
                    message = f"{commit_prefix} Add data file to DVC: {filename}"
                    subprocess.run(
                        ["git", "commit", "-m", message],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                    )
                    print(f"Added {filename} to DVC tracking")
                else:
                    print(f"No changes to commit for {filename}")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error adding file to DVC: {e}")
            # Don't raise, just log

    def get_git_status(self) -> Dict[str, Any]:
        """Get the current Git status.

        Returns:
            Dictionary containing Git status information
        """
        if not self.git_enabled or not self.git_path.exists():
            return {
                "status": "",
                "branch": "",
                "last_commit": "",
                "has_changes": False,
                "error": "Git not enabled or not initialized",
            }

        try:
            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get last commit
            commit_result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            return {
                "status": result.stdout.strip(),
                "branch": branch_result.stdout.strip(),
                "last_commit": commit_result.stdout.strip(),
                "has_changes": bool(result.stdout.strip()),
            }

        except subprocess.CalledProcessError as e:
            print(f"Error getting Git status: {e}")
            return {
                "status": "",
                "branch": "",
                "last_commit": "",
                "has_changes": False,
                "error": str(e),
            }

    def get_dvc_status(self) -> Dict[str, Any]:
        """Get the current DVC status.

        Returns:
            Dictionary containing DVC status information
        """
        if not self.dvc_enabled:
            return {
                "status": "",
                "has_changes": False,
                "error": "DVC not enabled",
            }

        try:
            result = subprocess.run(
                ["dvc", "status"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            return {
                "status": result.stdout.strip(),
                "has_changes": "not in sync" in result.stdout.lower(),
            }

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error getting DVC status: {e}")
            return {
                "status": "",
                "has_changes": False,
                "error": str(e),
            }

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        """Create a Git tag.

        Args:
            tag_name: Name of the tag
            message: Tag message (uses tag name if None)
        """
        if not self.git_enabled or not self.git_path.exists():
            print("Git not enabled or not initialized")
            return

        try:
            if not message:
                message = f"Tag: {tag_name}"

            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            print(f"Created tag: {tag_name}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating tag: {e}")
            # Don't raise, just log

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get the Git history for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of commit information dictionaries
        """
        if not self.git_enabled or not self.git_path.exists():
            return []

        try:
            # Convert to relative path from repo root
            file_path_obj = Path(file_path).resolve()
            try:
                rel_file_path = file_path_obj.relative_to(self.repo_path)
            except ValueError:
                return []

            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--pretty=format:%H|%an|%ad|%s",
                    "--date=iso",
                    str(rel_file_path),
                ],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            history = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) == 4:
                        history.append(
                            {
                                "hash": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3],
                            }
                        )

            return history

        except subprocess.CalledProcessError as e:
            print(f"Error getting file history: {e}")
            return []


# Global instance for singleton pattern
_vc_manager: Optional[VersionControlManager] = None


def init_version_control(repo_path: Optional[str] = None) -> VersionControlManager:
    """Initialize the version control manager.

    Args:
        repo_path: Path to the repository root

    Returns:
        Initialized VersionControlManager instance
    """
    global _vc_manager
    _vc_manager = VersionControlManager(repo_path)
    return _vc_manager


def get_vc_manager() -> VersionControlManager:
    """Get the global version control manager instance.

    Returns:
        VersionControlManager instance
    """
    global _vc_manager
    if _vc_manager is None:
        _vc_manager = VersionControlManager()
    return _vc_manager
