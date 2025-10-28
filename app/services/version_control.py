#!/usr/bin/env python3
"""
Version Control Integration Module for Phase 4
Handles Git and DVC operations for metadata and data versioning.
"""

import datetime
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class VersionControlManager:
    """Manages Git and DVC operations for the FAIR metadata system."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize the version control manager.

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.git_path = self.repo_path / ".git"
        self.dvc_path = self.repo_path / ".dvc"

        # Initialize Git repository if it doesn't exist
        if not self.git_path.exists():
            self._init_git_repo()

        # Initialize DVC if not already initialized
        self._init_dvc()

    def _init_git_repo(self) -> None:
        """Initialize a new Git repository at the repo root."""
        try:
            # Initialize Git at the repo root
            subprocess.run(
                ["git", "init"], cwd=self.repo_path, check=True, capture_output=True
            )
            print(f"Initialized Git repository in {self.repo_path}")

            # Create a README file for initial commit
            readme_path = self.repo_path / "README.md"
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
                ["git", "commit", "-m", "Initial commit: FAIR metadata system setup"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            print("Created initial Git commit")

        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e}")
            raise

    def _init_dvc(self) -> None:
        """Initialize DVC at the repo root if not already initialized."""
        try:
            # Check if DVC is already initialized
            if not self.dvc_path.exists():
                subprocess.run(
                    ["dvc", "init"], cwd=self.repo_path, check=True, capture_output=True
                )
                print("Initialized DVC")

                # Add .dvc to Git
                subprocess.run(
                    ["git", "add", ".dvc"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initialize DVC"],
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
        try:
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
                # Add all metadata files
                subprocess.run(
                    ["git", "add", "*.json", "*.md", "*.txt"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

            # Commit changes
            commit_message = message or "Update metadata files"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            print(f"Committed metadata changes: {commit_message}")

        except subprocess.CalledProcessError as e:
            print(f"Error committing metadata changes: {e}")
            raise

    def add_data_file_to_dvc(self, file_path: str, dataset_path: str) -> None:
        """Add a data file to DVC tracking.

        Args:
            file_path: Path to the data file to add
            dataset_path: Path to the dataset directory
        """
        try:
            # Convert to relative path from repo root
            file_path_obj = Path(file_path).resolve()
            rel_file_path = file_path_obj.relative_to(self.repo_path)

            # Check if file is already tracked by DVC
            dvc_file = str(rel_file_path) + ".dvc"
            if os.path.exists(os.path.join(self.repo_path, dvc_file)):
                print(f"File {os.path.basename(file_path)} is already tracked by DVC")
                return

            # Add file to DVC (DVC will create .dvc file alongside the data file)
            subprocess.run(
                ["dvc", "add", str(rel_file_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Add the .dvc file to Git
            if os.path.exists(os.path.join(self.repo_path, dvc_file)):
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
                    message = f"Add data file to DVC: {filename}"
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
            raise

    def get_git_status(self) -> Dict[str, Any]:
        """Get the current Git status.

        Returns:
            Dictionary containing Git status information
        """
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
            raise

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get the Git history for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of commit information dictionaries
        """
        try:
            # Convert to relative path from repo root
            file_path_obj = Path(file_path).resolve()
            rel_file_path = file_path_obj.relative_to(self.repo_path)

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

    def revert_to_commit(self, commit_hash: str) -> None:
        """Revert the repository to a specific commit.

        Args:
            commit_hash: Hash of the commit to revert to
        """
        try:
            subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            print(f"Reverted to commit: {commit_hash}")

        except subprocess.CalledProcessError as e:
            print(f"Error reverting to commit: {e}")
            raise


# Global instance for singleton pattern
_vc_manager: Optional[VersionControlManager] = None


def init_version_control(repo_path: str = ".") -> VersionControlManager:
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
