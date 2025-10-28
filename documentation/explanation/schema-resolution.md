# Schema Resolution System

## Overview

The FAIR metadata automation system implements a **Schema Resolution Principle** that allows for flexible schema management through local overrides while maintaining backward compatibility with packaged defaults.

## Core Principle

When the system needs a schema (e.g., to validate metadata), it follows this order of precedence:

1. **Local Override First**: Check if a `.template_schemas` directory exists within the current `MONITOR_PATH` (the specific data directory being managed). If it contains the required schema, use this local version.

2. **Packaged Default Second**: If no local override is found, fall back to loading the default schema that was packaged with the application.

## Benefits

- **Customization**: Local modifications to schemas for specific projects or institutions
- **Version Control**: Local schemas can be version-controlled with the data
- **Backward Compatibility**: Always falls back to working defaults if local schemas are missing
- **Institutional Standards**: Different institutions can maintain their own schema variations
- **Schema Evolution**: Gradual migration from old to new schema versions

## Implementation

### SchemaManager Class

The `SchemaManager` class in `src/schema_manager.py` implements the resolution logic:

```python
from src.schema_manager import get_schema_manager, resolve_schema_path

# Get the global schema manager instance
schema_manager = get_schema_manager()

# Resolve a schema path (will check local override first, then packaged default)
resolved_path = resolve_schema_path("project_descriptive.json")

# Load a schema using the resolution logic
schema = schema_manager.load_schema("project_descriptive.json")
```

### Key Methods

#### `resolve_schema_path(schema_name: str) -> Path`
Resolves the path to a schema file following the resolution principle.

#### `load_schema(schema_path: Any) -> Optional[Dict[str, Any]]`
Loads a JSON schema from a file with schema resolution support.

#### `get_schema_resolution_info(schema_name: str) -> Dict[str, Any]`
Gets detailed information about schema resolution for a specific schema.

#### `list_available_schemas() -> Dict[str, Any]`
Lists all available schemas with their resolution information.

## Usage Examples

### Basic Schema Loading

```python
from src.schema_manager import get_schema_manager

schema_manager = get_schema_manager()

# Load project schema (will use local override if available)
project_schema = schema_manager.load_schema("project_descriptive.json")

# Load dataset schema (will use local override if available)
dataset_schema = schema_manager.load_schema("dataset_administrative_schema.json")
```

### Schema Resolution Information

```python
from src.schema_manager import get_schema_resolution_info, list_available_schemas

# Get resolution info for a specific schema
info = get_schema_resolution_info("project_descriptive.json")
print(f"Resolution source: {info['resolution_source']}")
print(f"Local override exists: {info['local_override_exists']}")
print(f"Resolved path: {info['resolved_path']}")

# List all available schemas
all_schemas = list_available_schemas()
for schema_name, info in all_schemas.items():
    print(f"{schema_name}: {info['resolution_source']}")
```

### Creating Local Overrides

To create a local schema override:

1. Create the `.template_schemas` directory in your monitor path:
   ```bash
   mkdir -p monitor/.template_schemas
   ```

2. Copy and modify the desired schema:
   ```bash
   cp .template_schemas/project_descriptive.json monitor/.template_schemas/
   ```

3. Edit the local schema to add custom fields or modify existing ones:
   ```json
   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "title": "Project Descriptive Metadata (Local Override)",
     "description": "Local override with custom fields",
     "type": "object",
     "properties": {
       "project_title": {
         "type": "string",
         "description": "Title of the project"
       },
       "custom_institutional_field": {
         "type": "string",
         "description": "Custom field for institutional requirements"
       }
     },
     "required": ["project_title"]
   }
   ```

## Directory Structure

```
project_root/
├── .template_schemas/                    # Packaged default schemas
│   ├── project_descriptive.json
│   ├── dataset_administrative_schema.json
│   └── ...
├── monitor/                              # Data directory
│   └── .template_schemas/                # Local schema overrides (optional)
│       ├── project_descriptive.json      # Local override
│       └── ...
└── src/
    └── schema_manager.py                 # Schema resolution implementation
```

## Schema Caching

The `SchemaManager` implements caching to improve performance:

- Schemas are cached after first load
- Cache keys are based on resolved file paths
- Cache can be cleared with `clear_cache()`
- Cache information is available via `get_cache_info()`

```python
from src.schema_manager import get_schema_manager

schema_manager = get_schema_manager()

# Clear the cache
schema_manager.clear_cache()

# Get cache information
cache_info = schema_manager.get_cache_info()
print(f"Cached schemas: {cache_info['cached_schemas']}")
print(f"Cache size: {cache_info['cache_size']}")
```

## Best Practices

### 1. Schema Versioning

When creating local overrides, consider versioning:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Project Descriptive Metadata v2.1",
  "version": "2.1",
  "description": "Local override with institutional customizations"
}
```

### 2. Backward Compatibility

Maintain backward compatibility when possible:

- Add new fields as optional
- Don't remove existing required fields without migration plan
- Use schema versioning to track changes

### 3. Documentation

Document local schema changes:

```json
{
  "custom_fields": {
    "institutional_id": "Required by institutional policy",
    "funding_source": "Added for grant compliance"
  },
  "modifications": {
    "project_title": "Made required instead of optional"
  }
}
```

### 4. Testing

Test schema resolution in your environment:

```python
# Test that local overrides are used
local_info = get_schema_resolution_info("project_descriptive.json")
assert local_info['resolution_source'] == 'local_override'

# Test fallback to packaged defaults
# (after removing local override)
packaged_info = get_schema_resolution_info("project_descriptive.json")
assert packaged_info['resolution_source'] == 'packaged_default'
```

## Troubleshooting

### Common Issues

1. **Schema not found**: Check that the schema file exists in either the local override or packaged default location.

2. **Cache issues**: Clear the schema cache if you've updated schemas:
   ```python
   get_schema_manager().clear_cache()
   ```

3. **Permission issues**: Ensure the application has read access to both local and packaged schema directories.

### Debug Information

Use the resolution info methods to debug schema loading:

```python
from src.schema_manager import get_schema_resolution_info

info = get_schema_resolution_info("project_descriptive.json")
print(f"Local override path: {info['local_override_path']}")
print(f"Local override exists: {info['local_override_exists']}")
print(f"Packaged default path: {info['packaged_default_path']}")
print(f"Packaged default exists: {info['packaged_default_exists']}")
```

## Integration with Metadata Generation

The schema resolution system is automatically used by the metadata generation system:

```python
from src.metadata_generator import get_metadata_generator

generator = get_metadata_generator()

# This will automatically use the resolved schema (local override or packaged default)
generator.generate_project_file("p_my_project")
```

The metadata generator will use the appropriate schema based on the resolution principle, ensuring that local customizations are respected while maintaining system reliability.