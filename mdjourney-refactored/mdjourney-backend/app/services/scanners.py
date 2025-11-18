"""
File scanner implementations for the FAIR metadata automation system.
Contains concrete implementations of the IFileScanner interface.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.utils.helpers import calculate_checksum_incremental, get_current_timestamp
from .interfaces import IFileScanner


class DirmetaScanner(IFileScanner):
    """A file scanner implementation that uses the 'dirmeta' library.

    This class contains all the dirmeta-specific logic, isolated from the rest of the system.
    """

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file using the dirmeta library and return standardized metadata.

        Args:
            file_path: Path to the file to scan

        Returns:
            Standardized dictionary of file metadata
        """
        try:
            # Import dirmeta here to avoid circular imports
            from dirmeta.scanner import scan_directory

            # Use dirmeta's scan_directory function to get structural details
            scan_results = scan_directory(file_path.parent)

            # Find the specific file in the scan results
            file_metadata = {}
            for result in scan_results:
                if result.get("path") == str(file_path):
                    file_metadata = result
                    break

            # If dirmeta didn't find the file, create basic metadata
            if not file_metadata:
                file_metadata = self._create_basic_metadata(file_path)

            # Calculate checksum if not provided by dirmeta
            if not file_metadata.get("checksum"):
                file_metadata["checksum"] = calculate_checksum_incremental(file_path)

            # Ensure all required fields are present
            return self._standardize_metadata(file_metadata, file_path)

        except ImportError:
            print("Warning: dirmeta library not available, using basic file scanning")
            return self._create_basic_metadata(file_path)
        except Exception as e:
            print(f"Error scanning file {file_path} with dirmeta: {e}")
            return self._create_basic_metadata(file_path)

    def _create_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Create basic file metadata when dirmeta is not available."""
        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "extension": file_path.suffix,
                "mime_type": "application/octet-stream",
                "encoding": "unknown",
                "permissions": self._get_permissions_string(stat.st_mode),
                "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "checksum": calculate_checksum_incremental(file_path),
                "owner": "unknown",
                "group": "unknown",
                "compression": "none",
                "encryption": "none",
            }
        except Exception as e:
            print(f"Error creating basic metadata for {file_path}: {e}")
            return {
                "path": str(file_path),
                "size_bytes": 0,
                "extension": file_path.suffix,
                "mime_type": "application/octet-stream",
                "encoding": "unknown",
                "permissions": "-rw-r--r--",
                "accessed_time": get_current_timestamp(),
                "created_time": get_current_timestamp(),
                "modified_time": get_current_timestamp(),
                "checksum": "",
                "owner": "unknown",
                "group": "unknown",
                "compression": "none",
                "encryption": "none",
            }

    def _standardize_metadata(
        self, metadata: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """Ensure metadata has all required fields in the correct format."""
        return {
            "path": metadata.get("path", str(file_path)),
            "size_bytes": metadata.get("size_bytes", 0),
            "extension": metadata.get("extension", file_path.suffix),
            "mime_type": metadata.get("mime_type", "application/octet-stream"),
            "encoding": metadata.get("encoding", "unknown"),
            "permissions": metadata.get("permissions", "-rw-r--r--"),
            "accessed_time": metadata.get("accessed_time", get_current_timestamp()),
            "created_time": metadata.get("created_time", get_current_timestamp()),
            "modified_time": metadata.get("modified_time", get_current_timestamp()),
            "checksum": metadata.get("checksum", ""),
            "owner": metadata.get("owner", "unknown"),
            "group": metadata.get("group", "unknown"),
            "compression": metadata.get("compression", "none"),
            "encryption": metadata.get("encryption", "none"),
        }

    def _get_permissions_string(self, mode: int) -> str:
        """Convert file mode to permissions string."""
        import stat

        return stat.filemode(mode)


class BasicFileScanner(IFileScanner):
    """A basic file scanner that doesn't require external dependencies.

    This scanner provides basic file metadata using only Python's standard library.
    It can be used as a fallback when dirmeta is not available.
    """

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file using basic Python functionality.

        Args:
            file_path: Path to the file to scan

        Returns:
            Standardized dictionary of file metadata
        """
        try:
            stat = file_path.stat()

            return {
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "extension": file_path.suffix,
                "mime_type": self._guess_mime_type(file_path),
                "encoding": "unknown",
                "permissions": self._get_permissions_string(stat.st_mode),
                "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "checksum": calculate_checksum_incremental(file_path),
                "owner": "unknown",
                "group": "unknown",
                "compression": self._detect_compression(file_path),
                "encryption": "none",
            }
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
            return {
                "path": str(file_path),
                "size_bytes": 0,
                "extension": file_path.suffix,
                "mime_type": "application/octet-stream",
                "encoding": "unknown",
                "permissions": "-rw-r--r--",
                "accessed_time": get_current_timestamp(),
                "created_time": get_current_timestamp(),
                "modified_time": get_current_timestamp(),
                "checksum": "",
                "owner": "unknown",
                "group": "unknown",
                "compression": "none",
                "encryption": "none",
            }

    def _guess_mime_type(self, file_path: Path) -> str:
        """Guess MIME type based on file extension."""
        mime_types = {
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".py": "text/x-python",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".bz2": "application/x-bzip2",
        }
        return mime_types.get(file_path.suffix.lower(), "application/octet-stream")

    def _detect_compression(self, file_path: Path) -> str:
        """Detect compression type based on file extension."""
        compression_extensions = {
            ".gz": "gzip",
            ".bz2": "bzip2",
            ".zip": "zip",
            ".tar": "tar",
            ".7z": "7zip",
            ".rar": "rar",
        }
        return compression_extensions.get(file_path.suffix.lower(), "none")

    def _get_permissions_string(self, mode: int) -> str:
        """Convert file mode to permissions string."""
        import stat

        return stat.filemode(mode)
