"""
Interfaces for the FAIR metadata automation system.
Defines abstract base classes and contracts for system components.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class IFileScanner(ABC):
    """Abstract base class for file scanners.

    Defines the contract that any file scanner must adhere to.
    This allows for pluggable file scanning implementations.
    """

    @abstractmethod
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file and return a standardized dictionary of technical metadata.

        Args:
            file_path: Path to the file to scan

        Returns:
            Dictionary containing standardized file metadata with the following structure:
            {
                "path": str,                    # Full path to the file
                "size_bytes": int,              # File size in bytes
                "extension": str,               # File extension (e.g., ".txt")
                "mime_type": str,               # MIME type (e.g., "text/plain")
                "encoding": str,                # File encoding (e.g., "utf-8")
                "permissions": str,             # File permissions (e.g., "-rw-r--r--")
                "accessed_time": str,           # Last accessed time (ISO format)
                "created_time": str,            # Creation time (ISO format)
                "modified_time": str,           # Last modified time (ISO format)
                "checksum": str,                # File checksum (SHA256)
                "owner": str,                   # File owner
                "group": str,                   # File group
                "compression": str,             # Compression type (e.g., "none", "gzip")
                "encryption": str               # Encryption type (e.g., "none")
            }
        """
        pass
