"""
Service layer for the FAIR Metadata Enrichment API.
Handles business logic and integration with existing system components.
"""

# Import service classes from separate modules
from .project_service import ProjectService
from .schema_service import SchemaService
from .metadata_service import MetadataService

# Re-export for backward compatibility
__all__ = ["ProjectService", "SchemaService", "MetadataService"]