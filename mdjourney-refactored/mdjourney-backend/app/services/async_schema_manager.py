"""
Async schema manager with caching for the FAIR metadata automation system.
Provides asynchronous schema loading and validation with intelligent caching.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.cache import cached, get_schema_cache
from app.core.config import get_monitor_path
from app.core.exceptions import SchemaNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class AsyncSchemaManager:
    """Async schema manager with caching for improved performance."""

    def __init__(self) -> None:
        """Initialize the async schema manager."""
        self.schema_cache = get_schema_cache()
        try:
            self.monitor_path = get_monitor_path()
        except RuntimeError:
            # Config not initialized, use current directory
            self.monitor_path = Path(".")

        # Cache for schema resolution info
        self._resolution_cache: Dict[str, Dict[str, Any]] = {}

    @cached(ttl_seconds=3600, cache_type="schema")  # Cache schemas for 1 hour
    async def load_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a schema asynchronously with caching.

        Args:
            schema_name: Name of the schema file to load

        Returns:
            Schema dictionary or None if not found
        """
        # Get project root for packaged schemas
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

        # Try multiple locations for schema files
        schema_locations = [
            project_root / "packaged_schemas" / schema_name,
            self.monitor_path / ".template_schemas" / schema_name,
        ]

        # Add custom schema path if configured
        try:
            from app.core.config import CUSTOM_SCHEMA_PATH
            if CUSTOM_SCHEMA_PATH:
                schema_locations.insert(1, Path(CUSTOM_SCHEMA_PATH) / schema_name)
        except Exception:
            pass

        # Run file I/O in thread pool
        loop = asyncio.get_event_loop()

        for schema_path in schema_locations:
            if schema_path.exists():
                try:
                    schema_data = await loop.run_in_executor(
                        None, self._load_json_file, schema_path
                    )
                    if schema_data:
                        logger.debug(f"Loaded schema {schema_name} from {schema_path}")
                        return schema_data
                except Exception as e:
                    logger.warning(f"Error loading schema from {schema_path}: {e}")
                    continue

        logger.warning(f"Schema {schema_name} not found in any location")
        return None

    @cached(ttl_seconds=1800, cache_type="schema")  # Cache contextual schemas for 30 minutes
    async def get_contextual_template_schema(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        Get contextual template schema asynchronously with caching.

        Args:
            template_type: Type of contextual template

        Returns:
            Schema dictionary or None if not found
        """
        # Get project root for packaged schemas
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

        # Try multiple locations for contextual schemas
        contextual_locations = [
            project_root / "packaged_schemas/contextual" / f"{template_type}.json",
            self.monitor_path / ".template_schemas/contextual" / f"{template_type}.json",
        ]

        # Add custom schema path if configured
        try:
            from app.core.config import CUSTOM_SCHEMA_PATH
            if CUSTOM_SCHEMA_PATH:
                contextual_locations.insert(1, Path(CUSTOM_SCHEMA_PATH) / "contextual" / f"{template_type}.json")
        except Exception:
            pass

        # Run file I/O in thread pool
        loop = asyncio.get_event_loop()

        for schema_path in contextual_locations:
            if schema_path.exists():
                try:
                    schema_data = await loop.run_in_executor(
                        None, self._load_json_file, schema_path
                    )
                    if schema_data:
                        logger.debug(f"Loaded contextual schema {template_type} from {schema_path}")
                        return schema_data
                except Exception as e:
                    logger.warning(f"Error loading contextual schema from {schema_path}: {e}")
                    continue

        logger.warning(f"Contextual schema {template_type} not found in any location")
        return None

    async def discover_contextual_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover all available contextual schemas asynchronously.

        Returns:
            Dictionary mapping schema IDs to schema information
        """
        schemas = {}

        # Get project root for packaged schemas
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

        # Define locations to search
        locations = [
            (project_root / "packaged_schemas/contextual", "default"),
            (self.monitor_path / ".template_schemas/contextual", "local_override"),
        ]

        # Add custom schema path if configured
        try:
            from app.core.config import CUSTOM_SCHEMA_PATH
            if CUSTOM_SCHEMA_PATH:
                locations.insert(1, (Path(CUSTOM_SCHEMA_PATH) / "contextual", "custom_override"))
        except Exception:
            pass

        # Run file discovery in thread pool
        loop = asyncio.get_event_loop()

        for schema_path, source in locations:
            if schema_path.exists():
                try:
                    discovered_schemas = await loop.run_in_executor(
                        None, self._discover_schemas_in_directory, schema_path, source
                    )
                    schemas.update(discovered_schemas)
                except Exception as e:
                    logger.warning(f"Error discovering schemas in {schema_path}: {e}")

        return schemas

    def _discover_schemas_in_directory(self, schema_dir: Path, source: str) -> Dict[str, Dict[str, Any]]:
        """Discover schemas in a directory (sync function for thread pool)."""
        schemas = {}

        for schema_file in schema_dir.glob("*.json"):
            try:
                with open(schema_file, "r") as f:
                    schema_data = json.load(f)
                    schema_id = schema_file.stem
                    schemas[schema_id] = {
                        "title": schema_data.get("title", schema_id),
                        "description": schema_data.get("description"),
                        "source": source,
                        "path": str(schema_file),
                    }
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading schema file {schema_file}: {e}")
                continue

        return schemas

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file (sync function for thread pool)."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading JSON file {file_path}: {e}")
            return None

    async def validate_json(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validate JSON data against schema asynchronously.

        Args:
            data: Data to validate
            schema: Schema to validate against

        Returns:
            True if validation passes, False otherwise
        """
        # Run validation in thread pool as it can be CPU intensive
        loop = asyncio.get_event_loop()

        try:
            # Import jsonschema here to avoid import issues
            import jsonschema

            # Run validation in thread pool
            await loop.run_in_executor(
                None, jsonschema.validate, data, schema
            )
            return True
        except Exception as e:
            logger.warning(f"JSON validation failed: {e}")
            return False

    async def get_schema_resolution_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get schema resolution information with caching.

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary with resolution information
        """
        # Check cache first
        if schema_name in self._resolution_cache:
            return self._resolution_cache[schema_name]

        # Get project root for packaged schemas
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

        # Determine resolution source
        resolution_info = {"resolution_source": "default"}

        # Check if schema exists in different locations
        schema_locations = [
            (project_root / "packaged_schemas", "packaged_default"),
            (self.monitor_path / ".template_schemas", "local_override"),
        ]

        # Add custom schema path if configured
        try:
            from app.core.config import CUSTOM_SCHEMA_PATH
            if CUSTOM_SCHEMA_PATH:
                schema_locations.insert(1, (Path(CUSTOM_SCHEMA_PATH), "custom_override"))
        except Exception:
            pass

        for schema_dir, source in schema_locations:
            schema_path = schema_dir / schema_name
            if schema_path.exists():
                resolution_info["resolution_source"] = source
                resolution_info["resolved_path"] = str(schema_path)
                break

        # Cache the resolution info
        self._resolution_cache[schema_name] = resolution_info

        return resolution_info

    async def invalidate_schema_cache(self, schema_name: Optional[str] = None) -> None:
        """
        Invalidate schema cache entries.

        Args:
            schema_name: Specific schema to invalidate, or None to invalidate all
        """
        if schema_name:
            # Invalidate specific schema
            cache_keys = [
                f"load_schema:{hash(schema_name)}",
                f"get_contextual_template_schema:{hash(schema_name)}",
            ]
            for cache_key in cache_keys:
                await self.schema_cache.delete(cache_key)

            # Remove from resolution cache
            self._resolution_cache.pop(schema_name, None)
        else:
            # Invalidate all schemas
            await self.schema_cache.clear()
            self._resolution_cache.clear()

    async def preload_common_schemas(self) -> None:
        """Preload commonly used schemas into cache."""
        common_schemas = [
            "project_descriptive.json",
            "project_administrative_schema.json",
            "dataset_administrative_schema.json",
            "dataset_structural_schema.json",
            "experiment_contextual_schema.json",
            "instrument_technical_schema.json",
            "complete_metadata_schema.json",
        ]

        # Load schemas concurrently
        tasks = [self.load_schema(schema_name) for schema_name in common_schemas]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Preloaded {len(common_schemas)} common schemas into cache")


# Global async schema manager instance
_async_schema_manager: Optional[AsyncSchemaManager] = None


def get_async_schema_manager() -> AsyncSchemaManager:
    """Get the global async schema manager instance."""
    global _async_schema_manager
    if _async_schema_manager is None:
        _async_schema_manager = AsyncSchemaManager()
    return _async_schema_manager
