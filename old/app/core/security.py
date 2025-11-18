"""
Security module for the FAIR metadata automation system.
Handles input validation, path sanitization, and security utilities.
"""

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote

from app.core.exceptions import ValidationError, SecurityError


class InputValidator:
    """Validates and sanitizes user inputs to prevent security vulnerabilities."""

    # Allowed characters for IDs (alphanumeric, underscore, hyphen)
    ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

    # Maximum length for various fields
    MAX_ID_LENGTH = 100
    MAX_METADATA_TYPE_LENGTH = 50
    MAX_SCHEMA_TYPE_LENGTH = 50

    # Allowed metadata types
    ALLOWED_METADATA_TYPES = {
        'project_descriptive',
        'dataset_administrative',
        'dataset_structural',
        'experiment_contextual',
        'instrument_technical',
        'complete_metadata'
    }

    # Allowed schema types
    ALLOWED_SCHEMA_TYPES = {
        'project',
        'dataset_administrative',
        'dataset_structural',
        'experiment_contextual',
        'instrument_technical',
        'complete_metadata',
        'contextual'
    }

    @classmethod
    def validate_id(cls, value: str, field_name: str = "ID") -> str:
        """
        Validate and sanitize an ID parameter.

        Args:
            value: The ID value to validate
            field_name: Name of the field for error messages

        Returns:
            Sanitized ID value

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise ValidationError(f"{field_name} cannot be empty")

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")

        # Check length
        if len(value) > cls.MAX_ID_LENGTH:
            raise ValidationError(f"{field_name} exceeds maximum length of {cls.MAX_ID_LENGTH}")

        # Check for path traversal attempts
        if '..' in value or '/' in value or '\\' in value:
            raise ValidationError(f"{field_name} contains invalid characters")

        # Check for allowed characters only
        if not cls.ID_PATTERN.match(value):
            raise ValidationError(f"{field_name} contains invalid characters. Only alphanumeric, underscore, and hyphen are allowed")

        return value.strip()

    @classmethod
    def validate_metadata_type(cls, value: str) -> str:
        """
        Validate metadata type parameter.

        Args:
            value: The metadata type to validate

        Returns:
            Validated metadata type

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise ValidationError("Metadata type cannot be empty")

        if not isinstance(value, str):
            raise ValidationError("Metadata type must be a string")

        if len(value) > cls.MAX_METADATA_TYPE_LENGTH:
            raise ValidationError(f"Metadata type exceeds maximum length of {cls.MAX_METADATA_TYPE_LENGTH}")

        # Check for path traversal attempts
        if '..' in value or '/' in value or '\\' in value:
            raise ValidationError("Metadata type contains invalid characters")

        # Check against allowed values
        if value not in cls.ALLOWED_METADATA_TYPES:
            raise ValidationError(f"Invalid metadata type. Allowed values: {', '.join(cls.ALLOWED_METADATA_TYPES)}")

        return value.strip()

    @classmethod
    def validate_schema_type(cls, value: str) -> str:
        """
        Validate schema type parameter.

        Args:
            value: The schema type to validate

        Returns:
            Validated schema type

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise ValidationError("Schema type cannot be empty")

        if not isinstance(value, str):
            raise ValidationError("Schema type must be a string")

        if len(value) > cls.MAX_SCHEMA_TYPE_LENGTH:
            raise ValidationError(f"Schema type exceeds maximum length of {cls.MAX_SCHEMA_TYPE_LENGTH}")

        # Check for path traversal attempts
        if '..' in value or '/' in value or '\\' in value:
            raise ValidationError("Schema type contains invalid characters")

        # Check against allowed values
        if value not in cls.ALLOWED_SCHEMA_TYPES:
            raise ValidationError(f"Invalid schema type. Allowed values: {', '.join(cls.ALLOWED_SCHEMA_TYPES)}")

        return value.strip()

    @classmethod
    def validate_json_payload(cls, payload: Optional[Dict[str, Any]], max_size: int = 1024 * 1024) -> Optional[Dict[str, Any]]:
        """
        Validate JSON payload for size and content.

        Args:
            payload: The JSON payload to validate
            max_size: Maximum size in bytes

        Returns:
            Validated payload

        Raises:
            ValidationError: If validation fails
        """
        if payload is None:
            return None

        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a JSON object")

        # Check payload size (rough estimate)
        import json
        try:
            payload_str = json.dumps(payload)
            if len(payload_str.encode('utf-8')) > max_size:
                raise ValidationError(f"Payload exceeds maximum size of {max_size} bytes")
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Invalid JSON payload: {str(e)}")

        return payload


class PathSanitizer:
    """Sanitizes file paths to prevent path traversal attacks."""

    @classmethod
    def sanitize_path(cls, path: Union[str, Path], base_path: Optional[Path] = None) -> Path:
        """
        Sanitize a file path to prevent path traversal attacks.

        Args:
            path: The path to sanitize
            base_path: Base path to resolve against (optional)

        Returns:
            Sanitized Path object

        Raises:
            SecurityError: If path traversal is detected
        """
        if isinstance(path, str):
            path = Path(path)

        # Convert to absolute path
        if not path.is_absolute():
            if base_path:
                path = base_path / path
            else:
                path = path.resolve()

        # Normalize the path
        try:
            normalized_path = path.resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid path: {str(e)}")

        # Check for path traversal attempts
        if '..' in str(normalized_path) or normalized_path.parts.count('..') > 0:
            raise SecurityError("Path traversal detected")

        # Additional security checks
        if any(part.startswith('.') and part not in ['.', '..'] for part in normalized_path.parts):
            # Allow hidden files/directories but log them
            pass

        return normalized_path

    @classmethod
    def validate_path_access(cls, path: Path, base_path: Path) -> Path:
        """
        Validate that a path is within the allowed base path.

        Args:
            path: The path to validate
            base_path: The base path that must contain the target path

        Returns:
            Validated path

        Raises:
            SecurityError: If path is outside base path
        """
        try:
            sanitized_path = cls.sanitize_path(path, base_path)

            # Ensure the path is within the base path
            try:
                sanitized_path.relative_to(base_path)
            except ValueError:
                raise SecurityError("Path is outside allowed directory")

            return sanitized_path

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Path validation failed: {str(e)}")


class SecurityHeaders:
    """Manages security headers for HTTP responses."""

    @classmethod
    def get_security_headers(cls) -> Dict[str, str]:
        """
        Get a dictionary of security headers.

        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """
        Check if a client is allowed to make a request.

        Args:
            client_id: Unique identifier for the client
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        import time

        current_time = time.time()

        # Clean old requests outside the window
        if client_id in self._requests:
            self._requests[client_id] = [
                req_time for req_time in self._requests[client_id]
                if current_time - req_time < window_seconds
            ]
        else:
            self._requests[client_id] = []

        # Check if under limit
        if len(self._requests[client_id]) < max_requests:
            self._requests[client_id].append(current_time)
            return True

        return False


# Global rate limiter instance
rate_limiter = RateLimiter()
