"""
Custom exception hierarchy for the FAIR metadata automation system.
Provides structured error handling with proper context and chaining.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class MDJourneyError(Exception):
    """
    Base exception for all MDJourney application errors.

    Provides common functionality for error context, logging, and chaining.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the base exception.

        Args:
            message: Human-readable error message
            context: Additional context information (e.g., file paths, IDs)
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause

        # Log the error with context
        self._log_error()

    def _log_error(self) -> None:
        """Log the error with appropriate level and context."""
        log_message = f"{self.__class__.__name__}: {self.message}"
        if self.context:
            log_message += f" | Context: {self.context}"
        if self.cause:
            log_message += f" | Caused by: {type(self.cause).__name__}: {str(self.cause)}"

        logger.error(log_message, exc_info=self.cause)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }


class ConfigurationError(MDJourneyError):
    """Raised when configuration is invalid or missing."""
    pass


class SchemaError(MDJourneyError):
    """Base exception for schema-related errors."""
    pass


class SchemaValidationError(SchemaError):
    """Raised when schema validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        schema_path: Optional[Union[str, Path]] = None,
        data_path: Optional[Union[str, Path]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize schema validation error.

        Args:
            message: Error message
            validation_errors: List of specific validation error messages
            schema_path: Path to the schema file
            data_path: Path to the data file being validated
            cause: Underlying validation exception
        """
        context: Dict[str, Any] = {}
        if validation_errors:
            context["validation_errors"] = validation_errors
        if schema_path:
            context["schema_path"] = str(schema_path)
        if data_path:
            context["data_path"] = str(data_path)

        super().__init__(message, context, cause)
        self.validation_errors = validation_errors or []


class SchemaNotFoundError(SchemaError):
    """Raised when a required schema file cannot be found."""

    def __init__(
        self,
        schema_name: str,
        searched_paths: Optional[List[Union[str, Path]]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize schema not found error.

        Args:
            schema_name: Name of the missing schema
            searched_paths: List of paths that were searched
            cause: Underlying file system exception
        """
        context: Dict[str, Any] = {"schema_name": schema_name}
        if searched_paths:
            context["searched_paths"] = [str(p) for p in searched_paths]

        message = f"Schema '{schema_name}' not found"
        super().__init__(message, context, cause)


class MetadataError(MDJourneyError):
    """Base exception for metadata-related errors."""
    pass


class MetadataGenerationError(MetadataError):
    """Raised when metadata generation fails."""

    def __init__(
        self,
        message: str,
        metadata_type: Optional[str] = None,
        target_path: Optional[Union[str, Path]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize metadata generation error.

        Args:
            message: Error message
            metadata_type: Type of metadata being generated
            target_path: Path where metadata should be generated
            cause: Underlying exception
        """
        context = {}
        if metadata_type:
            context["metadata_type"] = metadata_type
        if target_path:
            context["target_path"] = str(target_path)

        super().__init__(message, context, cause)


class MetadataValidationError(MetadataError):
    """Raised when metadata validation fails."""

    def __init__(
        self,
        message: str,
        metadata_file: Optional[Union[str, Path]] = None,
        validation_errors: Optional[List[str]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize metadata validation error.

        Args:
            message: Error message
            metadata_file: Path to the metadata file
            validation_errors: List of validation error messages
            cause: Underlying validation exception
        """
        context: Dict[str, Any] = {}
        if metadata_file:
            context["metadata_file"] = str(metadata_file)
        if validation_errors:
            context["validation_errors"] = validation_errors

        super().__init__(message, context, cause)
        self.validation_errors = validation_errors or []


class FileSystemError(MDJourneyError):
    """Base exception for file system related errors."""
    pass


class PathNotFoundError(FileSystemError):
    """Raised when a required path cannot be found."""

    def __init__(
        self,
        path: Union[str, Path],
        path_type: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize path not found error.

        Args:
            path: The missing path
            path_type: Type of path (e.g., 'dataset', 'project', 'schema')
            cause: Underlying file system exception
        """
        context = {"path": str(path)}
        if path_type:
            context["path_type"] = path_type

        message = f"{path_type or 'Path'} not found: {path}"
        super().__init__(message, context, cause)


class PermissionError(FileSystemError):
    """Raised when file system permissions are insufficient."""

    def __init__(
        self,
        path: Union[str, Path],
        operation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize permission error.

        Args:
            path: The path with permission issues
            operation: The operation that failed (e.g., 'read', 'write')
            cause: Underlying permission exception
        """
        context = {"path": str(path)}
        if operation:
            context["operation"] = operation

        message = f"Insufficient permissions for {operation or 'operation'} on {path}"
        super().__init__(message, context, cause)


class VersionControlError(MDJourneyError):
    """Raised when version control operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        repository_path: Optional[Union[str, Path]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize version control error.

        Args:
            message: Error message
            operation: The failed operation (e.g., 'commit', 'push')
            repository_path: Path to the repository
            cause: Underlying version control exception
        """
        context = {}
        if operation:
            context["operation"] = operation
        if repository_path:
            context["repository_path"] = str(repository_path)

        super().__init__(message, context, cause)


class APIError(MDJourneyError):
    """Base exception for API-related errors."""
    pass


class ValidationError(APIError):
    """Raised when API request validation fails."""

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize API validation error.

        Args:
            message: Error message
            field_errors: Dictionary mapping field names to error lists
            cause: Underlying validation exception
        """
        context = {}
        if field_errors:
            context["field_errors"] = field_errors

        super().__init__(message, context, cause)
        self.field_errors = field_errors or {}


class ResourceNotFoundError(APIError):
    """Raised when a requested resource cannot be found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        cause: Optional[Exception] = None
    ):
        """
        Initialize resource not found error.

        Args:
            resource_type: Type of resource (e.g., 'dataset', 'project')
            resource_id: Identifier of the missing resource
            cause: Underlying exception
        """
        context = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }

        message = f"{resource_type} '{resource_id}' not found"
        super().__init__(message, context, cause)


# Security-related exceptions
class SecurityError(MDJourneyError):
    """Raised when a security violation is detected."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class InputValidationError(ValidationError):
    """Raised when input validation fails."""
    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal is detected."""
    pass


# Utility functions for error handling
def handle_file_operation(
    operation: str,
    path: Union[str, Path],
    error_handler: Optional[Callable] = None
) -> Callable:
    """
    Decorator to handle file operation errors with proper context.

    Args:
        operation: Description of the operation (e.g., 'read', 'write')
        path: Path being operated on
        error_handler: Optional custom error handler

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                raise PathNotFoundError(path, f"file for {operation}", e)
            except PermissionError as e:
                raise PermissionError(path, operation, e)
            except Exception as e:
                if error_handler:
                    return error_handler(e)
                raise MDJourneyError(
                    f"Failed to {operation} file at {path}",
                    {"operation": operation, "path": str(path)},
                    e
                )
        return wrapper
    return decorator


def create_error_response(error: Exception) -> Dict[str, Any]:
    """
    Create a standardized error response for API endpoints.

    Args:
        error: The exception to convert

    Returns:
        Dictionary suitable for JSON response
    """
    if isinstance(error, MDJourneyError):
        return error.to_dict()
    else:
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": {},
            "cause": None
        }
