"""
Schema service for the FAIR Metadata Enrichment API.
Handles schema-related business logic.
"""

import logging
from typing import Any, Dict, List, Optional

from models.pydantic_models import SchemaInfo
from app.core.cache import get_schema_cache
from app.core.config import get_monitor_path
from app.services.async_schema_manager import get_async_schema_manager
from app.services.schema_manager import get_schema_manager

logger = logging.getLogger(__name__)


class SchemaService:
    def __init__(self, schema_manager: Optional[Any] = None) -> None:
        self.monitor_path = get_monitor_path()
        self.schema_cache = get_schema_cache()
        if schema_manager is not None:
            self.schema_manager = schema_manager
        else:
            self.schema_manager = get_schema_manager()
        self.async_schema_manager = get_async_schema_manager()

    async def list_contextual_schemas(self) -> List[SchemaInfo]:
        """Get the list of all available contextual schemas."""
        # Check cache first
        cache_key = "contextual_schemas_list"
        cached_data = await self.schema_cache.get(cache_key)
        if cached_data:
            # Reconstruct SchemaInfo objects from cached data
            schemas = []
            for schema_data in cached_data:
                schemas.append(SchemaInfo(**schema_data))
            return schemas

        schemas = []

        # Use async schema manager for better performance
        contextual_schemas = await self.async_schema_manager.discover_contextual_schemas()

        for schema_id, schema_info in contextual_schemas.items():
            schema_obj = SchemaInfo(
                schema_id=schema_id,
                schema_title=schema_info.get("title", schema_id),
                schema_description=schema_info.get("description"),
                source=schema_info.get("source", "default"),
            )
            schemas.append(schema_obj)

        # Cache the serialized data
        serialized_schemas = [schema.dict() for schema in schemas]
        await self.schema_cache.set(cache_key, serialized_schemas, ttl_seconds=1800)

        return schemas

    async def get_schema(self, schema_type: str, schema_id: str) -> Dict[str, Any]:
        """Get the full JSON content of a specific schema."""
        # Handle contextual schemas specially
        if schema_type == "contextual":
            schema = await self.async_schema_manager.get_contextual_template_schema(schema_id)
            if not schema:
                raise ValueError(f"Contextual schema {schema_id} not found")
            return schema

        # Map schema_type to actual schema file names
        schema_mapping = {
            "project": "project_descriptive.json",
            "project_administrative": "project_administrative_schema.json",
            "dataset_administrative": "dataset_administrative_schema.json",
            "dataset_structural": "dataset_structural_schema.json",
            "experiment_contextual": "experiment_contextual_schema.json",
            "instrument_technical": "instrument_technical_schema.json",
            "complete_metadata": "complete_metadata_schema.json",
        }

        if schema_type not in schema_mapping:
            raise ValueError(f"Unknown schema type: {schema_type}")

        schema_name = schema_mapping[schema_type]
        schema = await self.async_schema_manager.load_schema(schema_name)

        if not schema:
            raise ValueError(f"Schema {schema_id} not found")

        return schema
