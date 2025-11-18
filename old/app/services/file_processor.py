"""
File processing module for the FAIR metadata automation system.
Handles file metadata extraction and processing using pluggable file scanners.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.security import (
    InputValidator,
    PathSanitizer,
)
from app.core.exceptions import (
    SecurityError,
    PathTraversalError,
)

from app.services.schema_manager import get_schema_manager
from app.services.version_control import get_vc_manager
from app.utils.helpers import calculate_checksum_incremental, get_current_timestamp

from .interfaces import IFileScanner


class FileProcessor:
    """Handles file processing and metadata extraction for the FAIR system."""

    def __init__(self, scanner: Optional[IFileScanner] = None) -> None:
        """
        Initialize the file processor.

        Args:
            scanner: File scanner implementation to use. If None, will use DirmetaScanner.
        """
        self.schema_manager = get_schema_manager()
        self.vc_manager = get_vc_manager()

        # Use provided scanner or default to DirmetaScanner
        if scanner is not None:
            self.scanner = scanner
        else:
            from .scanners import DirmetaScanner

            self.scanner = DirmetaScanner()

    def process_new_file(self, file_path: str, dataset_path: str) -> bool:
        """
        Process a new file and update dataset structural metadata.

        Args:
            file_path: Path to the file to process
            dataset_path: Path to the dataset directory

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Validate and sanitize paths
            validated_file_path = PathSanitizer.sanitize_path(file_path)
            validated_dataset_path = PathSanitizer.sanitize_path(dataset_path)

            # Check if file exists and has content
            if not validated_file_path.exists():
                print(f"File does not exist: {validated_file_path}")
                return False

            # Check file size - skip very small files that might be incomplete
            file_size = validated_file_path.stat().st_size
            if file_size < 10:  # Skip files smaller than 10 bytes
                print(
                    f"File too small, likely incomplete: {validated_file_path} ({file_size} bytes)"
                )
                return False

            # Use the scanner to get file metadata
            file_metadata = self.scanner.scan_file(validated_file_path)

            # Map scanner output to our schema structure
            mapped_metadata = self._map_scanner_output_to_schema(
                file_metadata, str(validated_file_path), str(validated_dataset_path)
            )

            # Update dataset structural file
            success = self._update_dataset_structural_file(
                str(validated_dataset_path), mapped_metadata, str(validated_file_path)
            )

            if success:
                # Commit metadata changes to Git and add data file to DVC
                try:
                    self.vc_manager.commit_metadata_changes(
                        f"Update file metadata: {validated_file_path.name}"
                    )

                    # Add data file to DVC tracking
                    self.vc_manager.add_data_file_to_dvc(str(validated_file_path), str(validated_dataset_path))
                except Exception as e:
                    print(f"Warning: Could not commit version control changes: {e}")

            return success

        except (SecurityError, PathTraversalError) as e:
            print(f"Security error processing file {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return False

    def _map_scanner_output_to_schema(
        self, file_metadata: Dict[str, Any], file_path: str, dataset_path: str
    ) -> Dict[str, Any]:
        """
        Map scanner output to our schema structure.

        Args:
            file_metadata: Raw metadata from the scanner
            file_path: Path to the file
            dataset_path: Path to the dataset directory

        Returns:
            Mapped metadata in our schema format
        """
        return {
            "file_name": os.path.basename(file_path),
            "role": "raw_data",
            "file_path": os.path.relpath(file_path, dataset_path),
            "file_extension": file_metadata.get("extension", "").lstrip("."),
            "file_size_bytes": file_metadata.get("size_bytes", 0),
            "checksum": file_metadata.get("checksum", ""),
            "checksum_algorithm": "SHA256",
            "file_type_os": "file",
            "file_permissions": file_metadata.get("permissions", "-rw-r--r--"),
            "file_accessed_utc": file_metadata.get(
                "accessed_time", get_current_timestamp()
            ),
            "file_created_utc": file_metadata.get(
                "created_time", get_current_timestamp()
            ),
            "file_modified_utc": file_metadata.get(
                "modified_time", get_current_timestamp()
            ),
            "file_owner": file_metadata.get("owner", "unknown"),
            "file_group": file_metadata.get("group", "unknown"),
            "file_encoding": file_metadata.get("encoding", "unknown"),
            "file_mime_type": file_metadata.get(
                "mime_type", "application/octet-stream"
            ),
            "file_compression": file_metadata.get("compression", "none"),
            "file_encryption": file_metadata.get("encryption", "none"),
            "file_validation_status": "validated",
            "file_processing_date": get_current_timestamp(),
        }

    def _update_dataset_structural_file(
        self, dataset_path: str, file_metadata: Dict[str, Any], file_path: str
    ) -> bool:
        """
        Update the dataset structural metadata file with new file information.

        Args:
            dataset_path: Path to the dataset directory
            file_metadata: File metadata to add
            file_path: Path to the processed file

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Load existing structural metadata
            struct_filepath = os.path.join(
                dataset_path, ".metadata", "dataset_structural.json"
            )

            if not os.path.exists(struct_filepath):
                print(f"Dataset structural file not found: {struct_filepath}")
                return False

            with open(struct_filepath, "r") as f:
                struct_data = json.load(f)

            # Initialize file_descriptions if it doesn't exist
            if "file_descriptions" not in struct_data:
                struct_data["file_descriptions"] = []

            # Check if file already exists in descriptions
            file_name = os.path.basename(file_path)
            existing_file = None
            for file_desc in struct_data["file_descriptions"]:
                if file_desc.get("file_name") == file_name:
                    existing_file = file_desc
                    break

            if existing_file:
                # Update existing file description
                existing_file.update(file_metadata)
                print(f"Updated existing file description: {file_name}")
            else:
                # Add new file description
                struct_data["file_descriptions"].append(file_metadata)
                print(f"Added new file description: {file_name}")

            # Update file organization summary
            file_count = len(struct_data["file_descriptions"])
            total_size = sum(
                f.get("file_size_bytes", 0) for f in struct_data["file_descriptions"]
            )
            file_types = list(
                set(
                    f.get("file_extension", "")
                    for f in struct_data["file_descriptions"]
                )
            )

            if "file_organization" not in struct_data:
                struct_data["file_organization"] = {}

            struct_data["file_organization"].update(
                {
                    "file_count": file_count,
                    "total_size_bytes": total_size,
                    "file_types": file_types,
                }
            )

            # Validate updated data against schema
            struct_schema = self.schema_manager.get_dataset_struct_schema()
            if self.schema_manager.validate_json(struct_data, struct_schema):
                # Save updated structural metadata
                with open(struct_filepath, "w") as f:
                    json.dump(struct_data, f, indent=4)
                print(f"Updated dataset structural file: {struct_filepath}")
                return True
            else:
                print(
                    "Failed to update dataset structural file due to validation errors"
                )
                return False

        except Exception as e:
            print(f"Error updating dataset structural file: {e}")
            return False

    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            File metadata dictionary or None if not found
        """
        try:
            # Use the scanner to get file metadata
            return self.scanner.scan_file(Path(file_path))

        except Exception as e:
            print(f"Error getting file metadata: {e}")
            return None

    def process_multiple_files(
        self, file_paths: List[str], dataset_path: str
    ) -> Dict[str, bool]:
        """
        Process multiple files and update dataset metadata.

        Args:
            file_paths: List of file paths to process
            dataset_path: Path to the dataset directory

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        for file_path in file_paths:
            results[file_path] = self.process_new_file(file_path, dataset_path)
        return results

    def validate_file_metadata(self, file_metadata: Dict[str, Any]) -> bool:
        """
        Validate file metadata against schema.

        Args:
            file_metadata: File metadata to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Get the appropriate schema for file metadata
            # For now, use a simple validation approach
            required_fields = ["file_name", "file_path", "file_size_bytes", "checksum"]

            for field in required_fields:
                if field not in file_metadata:
                    print(f"Missing required field: {field}")
                    return False

                if not file_metadata[field]:
                    print(f"Empty required field: {field}")
                    return False

            return True

        except Exception as e:
            print(f"Error validating file metadata: {e}")
            return False

    def get_dataset_file_summary(self, dataset_path: str) -> Dict[str, Any]:
        """
        Get a summary of all files in a dataset.

        Args:
            dataset_path: Path to the dataset directory

        Returns:
            Dictionary containing file summary information
        """
        try:
            struct_filepath = os.path.join(
                dataset_path, ".metadata", "dataset_structural.json"
            )

            if not os.path.exists(struct_filepath):
                return {
                    "file_count": 0,
                    "total_size_bytes": 0,
                    "file_types": [],
                    "files": [],
                }

            with open(struct_filepath, "r") as f:
                struct_data = json.load(f)

            file_descriptions = struct_data.get("file_descriptions", [])
            file_organization = struct_data.get("file_organization", {})

            return {
                "file_count": file_organization.get(
                    "file_count", len(file_descriptions)
                ),
                "total_size_bytes": file_organization.get("total_size_bytes", 0),
                "file_types": file_organization.get("file_types", []),
                "files": file_descriptions,
            }

        except Exception as e:
            print(f"Error getting dataset file summary: {e}")
            return {
                "file_count": 0,
                "total_size_bytes": 0,
                "file_types": [],
                "files": [],
            }


# Global instance for singleton pattern
_file_processor: Optional[FileProcessor] = None


def get_file_processor() -> FileProcessor:
    """Get the global file processor instance.

    Returns:
        FileProcessor instance
    """
    global _file_processor
    if _file_processor is None:
        _file_processor = FileProcessor()
    return _file_processor


# Convenience functions for direct access
def process_new_file(file_path: str, dataset_path: str) -> bool:
    """Process a new file."""
    return get_file_processor().process_new_file(file_path, dataset_path)


def process_file_with_dirmeta(file_path: str, dataset_path: str) -> bool:
    """Process a file with dirmeta (deprecated, use process_new_file)."""
    return get_file_processor().process_new_file(file_path, dataset_path)


def get_file_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific file."""
    return get_file_processor().get_file_metadata(file_path)


def process_multiple_files(file_paths: List[str], dataset_path: str) -> Dict[str, bool]:
    """Process multiple files."""
    return get_file_processor().process_multiple_files(file_paths, dataset_path)


def get_dataset_file_summary(dataset_path: str) -> Dict[str, Any]:
    """Get dataset file summary."""
    return get_file_processor().get_dataset_file_summary(dataset_path)
