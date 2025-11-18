"""
Utility functions for the FAIR metadata automation system.
Provides common utilities for timestamps, checksums, and file operations.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import get_checksum_algorithm, get_chunk_size


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def calculate_checksum_incremental(
    filepath: Path,
    algorithm: str = None,
    chunk_size: int = None,
) -> str:
    """
    Calculate checksum of a file using incremental reading.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: from config)
        chunk_size: Size of chunks to read (default: from config)

    Returns:
        Hexadecimal checksum string
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Use config defaults if not provided
    if algorithm is None:
        algorithm = get_checksum_algorithm()
    if chunk_size is None:
        chunk_size = get_chunk_size()

    # Get the hash function
    hash_func = getattr(hashlib, algorithm.lower())()

    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hash_func.update(chunk)

        return str(hash_func.hexdigest())
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {filepath}: {e}")


def ensure_directory_exists(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        Path object for the directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_project_folder(path: Path) -> bool:
    """
    Check if a path represents a project folder.

    Args:
        path: Path to check

    Returns:
        True if the path is a project folder, False otherwise
    """
    from app.core.config import PROJECT_PREFIX

    return path.is_dir() and path.name.startswith(PROJECT_PREFIX)


def is_dataset_folder(path: Path) -> bool:
    """
    Check if a path represents a dataset folder.

    Args:
        path: Path to check

    Returns:
        True if the path is a dataset folder, False otherwise
    """
    if not path.is_dir():
        return False

    # Check if parent is a project folder
    parent = path.parent
    return is_project_folder(parent)


def get_project_id_from_path(path: Path) -> Optional[str]:
    """
    Extract project ID from a project or dataset path.

    Args:
        path: Path to extract project ID from

    Returns:
        Project ID if found, None otherwise
    """
    if is_project_folder(path):
        # This is a project folder, we need to read the metadata
        metadata_file = path / ".metadata" / "project_descriptive.json"
        if metadata_file.exists():
            import json

            try:
                with open(metadata_file, "r") as f:
                    data: Dict[str, Any] = json.load(f)
                    project_id = data.get("project_identifier")
                    return str(project_id) if project_id is not None else None
            except (json.JSONDecodeError, KeyError):
                return None
    elif is_dataset_folder(path):
        # This is a dataset folder, check parent
        return get_project_id_from_path(path.parent)

    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes = int(size_bytes / 1024.0)
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for file system operations.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re

    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"
    return sanitized
