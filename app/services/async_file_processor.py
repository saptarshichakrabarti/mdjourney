"""
Async file processing module for the FAIR metadata automation system.
Handles asynchronous file metadata extraction and processing.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.cache import cached, get_metadata_cache
from app.core.security import InputValidator, PathSanitizer
from app.core.exceptions import SecurityError, PathTraversalError
from app.services.schema_manager import get_schema_manager
from app.services.version_control import get_vc_manager
from app.utils.helpers import calculate_checksum_incremental, get_current_timestamp

from .interfaces import IFileScanner

logger = logging.getLogger(__name__)


class AsyncFileProcessor:
    """Handles asynchronous file processing and metadata extraction for the FAIR system."""

    def __init__(self, scanner: Optional[IFileScanner] = None) -> None:
        """
        Initialize the async file processor.

        Args:
            scanner: File scanner implementation to use. If None, will use DirmetaScanner.
        """
        self.schema_manager = get_schema_manager()
        self.vc_manager = get_vc_manager()
        self.metadata_cache = get_metadata_cache()

        # Use provided scanner or default to DirmetaScanner
        if scanner is not None:
            self.scanner = scanner
        else:
            from .scanners import DirmetaScanner
            self.scanner = DirmetaScanner()

    async def process_new_file(self, file_path: str, dataset_path: str) -> bool:
        """
        Process a new file and update dataset structural metadata asynchronously.

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
                logger.warning(f"File does not exist: {validated_file_path}")
                return False

            # Check file size - skip very small files that might be incomplete
            file_size = validated_file_path.stat().st_size
            if file_size < 10:  # Skip files smaller than 10 bytes
                logger.warning(
                    f"File too small, likely incomplete: {validated_file_path} ({file_size} bytes)"
                )
                return False

            # Use the scanner to get file metadata (run in thread pool for CPU-bound work)
            loop = asyncio.get_event_loop()
            file_metadata = await loop.run_in_executor(
                None, self.scanner.scan_file, validated_file_path
            )

            # Map scanner output to our schema structure
            mapped_metadata = await self._map_scanner_output_to_schema(
                file_metadata, str(validated_file_path), str(validated_dataset_path)
            )

            # Update dataset structural file
            success = await self._update_dataset_structural_file(
                str(validated_dataset_path), mapped_metadata, str(validated_file_path)
            )

            if success:
                # Commit metadata changes to Git and add data file to DVC (run in thread pool)
                try:
                    await loop.run_in_executor(
                        None,
                        self.vc_manager.commit_metadata_changes,
                        f"Update file metadata: {validated_file_path.name}"
                    )

                    # Add data file to DVC tracking
                    await loop.run_in_executor(
                        None,
                        self.vc_manager.add_data_file_to_dvc,
                        str(validated_file_path),
                        str(validated_dataset_path)
                    )
                except Exception as e:
                    logger.warning(f"Could not commit version control changes: {e}")

            return success

        except (SecurityError, PathTraversalError) as e:
            logger.error(f"Security error processing file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False

    async def process_multiple_files(self, file_paths: List[str], dataset_path: str) -> Dict[str, bool]:
        """
        Process multiple files concurrently.

        Args:
            file_paths: List of file paths to process
            dataset_path: Path to the dataset directory

        Returns:
            Dictionary mapping file paths to success status
        """
        tasks = [
            self.process_new_file(file_path, dataset_path)
            for file_path in file_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert results to dictionary
        file_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing file {file_paths[i]}: {result}")
                file_results[file_paths[i]] = False
            else:
                file_results[file_paths[i]] = result

        return file_results

    @cached(ttl_seconds=300, cache_type="metadata")
    async def _map_scanner_output_to_schema(
        self, file_metadata: Dict[str, Any], file_path: str, dataset_path: str
    ) -> Dict[str, Any]:
        """
        Map scanner output to our schema structure with caching.

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
        }

    async def _update_dataset_structural_file(
        self, dataset_path: str, mapped_metadata: Dict[str, Any], file_path: str
    ) -> bool:
        """
        Update the dataset structural metadata file asynchronously.

        Args:
            dataset_path: Path to the dataset directory
            mapped_metadata: Mapped metadata to add
            file_path: Path to the file being processed

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Run file I/O operations in thread pool
            loop = asyncio.get_event_loop()

            # Load existing structural metadata
            structural_file = Path(dataset_path) / ".metadata" / "dataset_structural.json"

            existing_data = await loop.run_in_executor(
                None, self._load_structural_metadata, structural_file
            )

            # Add new file metadata
            if "files" not in existing_data:
                existing_data["files"] = []

            # Check if file already exists in metadata
            file_name = os.path.basename(file_path)
            file_exists = any(
                f.get("file_name") == file_name for f in existing_data["files"]
            )

            if not file_exists:
                existing_data["files"].append(mapped_metadata)

                # Update dataset-level metadata
                existing_data["dataset_file_count"] = len(existing_data["files"])
                existing_data["last_modified_date"] = get_current_timestamp()

                # Save updated metadata
                await loop.run_in_executor(
                    None, self._save_structural_metadata, structural_file, existing_data
                )

                # Invalidate cache for this dataset
                cache_key = f"dataset_structural:{dataset_path}"
                await self.metadata_cache.delete(cache_key)

                return True
            else:
                logger.debug(f"File {file_name} already exists in metadata")
                return True

        except Exception as e:
            logger.error(f"Error updating dataset structural file: {e}")
            return False

    def _load_structural_metadata(self, structural_file: Path) -> Dict[str, Any]:
        """Load structural metadata from file (sync function for thread pool)."""
        if structural_file.exists():
            try:
                with open(structural_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading structural metadata: {e}")

        # Return default structure if file doesn't exist or can't be loaded
        return {
            "dataset_identifier": "",
            "dataset_title": "",
            "dataset_description": "",
            "dataset_file_count": 0,
            "files": [],
            "created_date": get_current_timestamp(),
            "last_modified_date": get_current_timestamp(),
        }

    def _save_structural_metadata(self, structural_file: Path, data: Dict[str, Any]) -> None:
        """Save structural metadata to file (sync function for thread pool)."""
        # Ensure directory exists
        structural_file.parent.mkdir(parents=True, exist_ok=True)

        # Save with atomic write
        temp_file = structural_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # Atomic move
            temp_file.replace(structural_file)

        except Exception as e:
            logger.error(f"Error saving structural metadata: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise

    async def get_dataset_files(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        Get list of files in a dataset with caching.

        Args:
            dataset_path: Path to the dataset directory

        Returns:
            List of file metadata dictionaries
        """
        cache_key = f"dataset_files:{dataset_path}"
        cached_files = await self.metadata_cache.get(cache_key)

        if cached_files is not None:
            return cached_files

        # Load from structural metadata file
        structural_file = Path(dataset_path) / ".metadata" / "dataset_structural.json"

        loop = asyncio.get_event_loop()
        structural_data = await loop.run_in_executor(
            None, self._load_structural_metadata, structural_file
        )

        files = structural_data.get("files", [])

        # Cache the result
        await self.metadata_cache.set(cache_key, files, ttl_seconds=300)

        return files

    async def invalidate_dataset_cache(self, dataset_path: str) -> None:
        """
        Invalidate cache entries for a specific dataset.

        Args:
            dataset_path: Path to the dataset directory
        """
        cache_keys = [
            f"dataset_files:{dataset_path}",
            f"dataset_structural:{dataset_path}",
        ]

        for cache_key in cache_keys:
            await self.metadata_cache.delete(cache_key)


# Global async file processor instance
_async_file_processor: Optional[AsyncFileProcessor] = None


def get_async_file_processor() -> AsyncFileProcessor:
    """Get the global async file processor instance."""
    global _async_file_processor
    if _async_file_processor is None:
        _async_file_processor = AsyncFileProcessor()
    return _async_file_processor
