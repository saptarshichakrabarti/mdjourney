# FAIR Metadata Enrichment API - Reference Documentation

**Base URL (Gateway):** `http://localhost:8080/api/v1`
**Base URL (Direct Backend):** `http://localhost:8000/v1`

**Version:** 1.0.0

**Architecture Note:** The refactored system uses a gateway-based architecture. When accessing the API through the gateway (recommended for production), use the `/api/v1/` prefix. When accessing backend instances directly (for development or testing), use the `/v1/` prefix.

**Core Principle:** The API acts as an abstraction layer. The frontend client does not need to know whether the schemas being used are the packaged defaults or a local override. All schema resolution logic is handled transparently by the backend's `SchemaManager`.

## Session Management

### Gateway Session Initialization

Before accessing API endpoints, a session must be initialized through the gateway:

**Endpoint:** `POST /api/session/start`

**Request Body:**
```json
{
  "monitor_path": "./data",
  "environment": "development",
  "api": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "schemas": {
    "base_path": "packaged_schemas"
  }
}
```

**Response:**
```json
{
  "status": "started"
}
```

Upon successful session initialization, the gateway allocates a backend instance and stores session information. All subsequent API requests are routed to the allocated backend instance.

## Authentication

The API supports optional authentication via API keys. When authentication is enabled, include the API key in the `Authorization` header:

```
Authorization: Bearer your-api-key-here
```

**Note:** In the gateway architecture, authentication is handled at the session level. Each session operates with its own backend instance and configuration.

## Rate Limiting

The API implements rate limiting to prevent abuse. Default limits:
- **1000 requests per hour** per IP address
- **100 requests per minute** per authenticated user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

### Core Data Models (Pydantic Schemas)

These models remain the same, as they define the structure of API communication, not the metadata content itself.

```python
# pydantic_models.py (conceptual)

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProjectSummary(BaseModel):
    project_id: str = Field(..., description="Unique identifier for the project, derived from folder name.")
    project_title: Optional[str] = Field(None, description="Title of the project, read from metadata if available.")
    path: str = Field(..., description="Absolute path to the project folder.")
    dataset_count: int = Field(..., description="Number of datasets within the project.")

class DatasetSummary(BaseModel):
    dataset_id: str = Field(..., description="Unique identifier for the dataset, derived from folder name.")
    dataset_title: Optional[str] = Field(None, description="Title of the dataset, read from metadata if available.")
    path: str = Field(..., description="Absolute path to the dataset folder.")
    metadata_status: str = Field(..., description="Current status, e.g., 'V1_Ingested', 'V2_Finalized'.")

class SchemaInfo(BaseModel):
    schema_id: str = Field(..., description="A unique identifier for the schema, e.g., 'genomics_sequencing'.")
    schema_title: str = Field(..., description="A user-friendly title for the schema, e.g., 'Genomics Sequencing Run'.")
    schema_description: Optional[str] = Field(None, description="A brief description of the schema's purpose.")
    source: str = Field(..., description="Indicates the source of the schema ('default' or 'local_override').")

class MetadataFile(BaseModel):
    content: Dict[str, Any] = Field(..., description="The full JSON content of the metadata file.")
    schema_info: SchemaInfo = Field(..., description="Information about the schema used to validate this content.")

class MetadataUpdatePayload(BaseModel):
    content: Dict[str, Any] = Field(..., description="The full JSON content of the metadata file to be saved.")

class ContextualTemplatePayload(BaseModel):
    schema_id: str = Field(..., description="The ID of the contextual schema to use for generating the template.")

class FinalizePayload(BaseModel):
    experiment_id: str = Field(..., description="The unique ID of the experiment to be finalized.")
```

---

## API Endpoints

### Discovery Endpoints

#### `GET /projects`
**Summary:** List all available projects.

**Description:** Scans the `MONITOR_PATH` and returns a summary of each valid project folder.

**Parameters:** None

**Responses:**
- `200 OK`: `List[ProjectSummary]` - Successfully retrieved project list
- `500 Internal Server Error`: Server error occurred

**Example Response:**
```json
[
  {
    "project_id": "p_MyResearchProject",
    "project_title": "My Research Project",
    "path": "/data/p_MyResearchProject",
    "dataset_count": 3
  }
]
```

#### `GET /projects/{project_id}/datasets`
**Summary:** List all datasets within a specific project.

**Description:** Scans a project folder and returns a summary for each dataset.

**Parameters:**
- `project_id` (path, required): The ID of the project

**Responses:**
- `200 OK`: `List[DatasetSummary]` - Successfully retrieved dataset list
- `404 Not Found`: Project does not exist
- `500 Internal Server Error`: Server error occurred

**Example Response:**
```json
[
  {
    "dataset_id": "d_dataset_RNAseq_rep1",
    "dataset_title": "RNA-seq Replicate 1",
    "path": "/data/p_MyResearchProject/d_dataset_RNAseq_rep1",
    "metadata_status": "V1_Ingested"
  }
]
```

#### `POST /rescan`
**Summary:** Trigger a rescan of the monitor path.

**Description:** Forces the system to rescan the monitor path and refresh the project/dataset cache.

**Parameters:** None

**Responses:**
- `200 OK`: `{"message": "Rescan completed successfully"}` - Rescan completed
- `500 Internal Server Error`: Server error occurred

### Schema Endpoints

#### `GET /schemas/contextual`
**Summary:** Get the list of all available contextual schemas.

**Description:** The backend's `SchemaManager` will scan both the packaged default schema directory and the local `.template_schemas/contextual` directory in the active `MONITOR_PATH`. It returns a merged list, with local schemas overriding defaults if they share the same `schema_id`.

**Parameters:** None

**Responses:**
- `200 OK`: `List[SchemaInfo]` - Successfully retrieved contextual schemas
- `500 Internal Server Error`: Server error occurred

**Example Response:**
```json
[
  {
    "schema_id": "genomics_sequencing",
    "schema_title": "Genomics Sequencing Run",
    "schema_description": "Metadata schema for genomics sequencing experiments",
    "source": "default"
  },
  {
    "schema_id": "microscopy_imaging",
    "schema_title": "Microscopy Imaging",
    "schema_description": "Metadata schema for microscopy imaging experiments",
    "source": "local_override"
  }
]
```

#### `GET /schemas/{schema_type}/{schema_id}`
**Summary:** Get the full JSON content of a specific schema.

**Description:** Allows the frontend to fetch the actual schema if needed for advanced client-side validation or form generation. The backend's `SchemaManager` will resolve whether to return the local or default version.

**Parameters:**
- `schema_type` (path, required): Schema type (e.g., `project`, `dataset_administrative`, `contextual`)
- `schema_id` (path, required): The ID of the schema (e.g., `project_descriptive`, `genomics_sequencing`)

**Responses:**
- `200 OK`: `Dict[str, Any]` - The raw JSON Schema content
- `404 Not Found`: Schema cannot be found in either local or default locations
- `500 Internal Server Error`: Server error occurred

**Example Response:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "experiment_id": {
      "type": "string",
      "description": "Unique identifier for the experiment"
    },
    "experiment_date": {
      "type": "string",
      "format": "date",
      "description": "Date when the experiment was conducted"
    }
  },
  "required": ["experiment_id", "experiment_date"]
}

### Metadata Endpoints

#### `GET /datasets/{dataset_id}/metadata/{metadata_type}`
**Summary:** Get the content of a specific metadata file and the schema used to validate it.

**Description:** Reads the specified metadata file (e.g., `dataset_administrative.json`). The backend's `SchemaManager` then determines the correct schema (local or default) that applies to this file and returns both the file content and information about the active schema.

**Parameters:**
- `dataset_id` (path, required): The ID of the dataset
- `metadata_type` (path, required): Metadata type (`project_descriptive`, `dataset_administrative`, `dataset_structural`, `experiment_contextual`)

**Responses:**
- `200 OK`: `MetadataFile` - Successfully retrieved metadata file
- `404 Not Found`: Dataset or metadata file doesn't exist
- `500 Internal Server Error`: Server error occurred

**Example Response:**
```json
{
  "content": {
    "dataset_id": "d_dataset_RNAseq_rep1",
    "dataset_title": "RNA-seq Replicate 1",
    "abstract": "RNA sequencing data from replicate 1",
    "data_steward": "researcher@example.com"
  },
  "schema_info": {
    "schema_id": "dataset_administrative",
    "schema_title": "Dataset Administrative Metadata",
    "schema_description": "Administrative metadata for datasets",
    "source": "default"
  }
}
```

#### `PUT /datasets/{dataset_id}/metadata/{metadata_type}`
**Summary:** Update and save a specific metadata file.

**Description:** The backend receives the new JSON `content`. It uses the `SchemaManager` to resolve and load the correct schema (local override or packaged default). It validates the incoming content against this resolved schema. If valid, it saves the file and commits the change.

**Parameters:**
- `dataset_id` (path, required): The ID of the dataset
- `metadata_type` (path, required): Metadata type (`project_descriptive`, `dataset_administrative`, `dataset_structural`, `experiment_contextual`)

**Request Body:** `MetadataUpdatePayload`
```json
{
  "content": {
    "dataset_title": "Updated Dataset Title",
    "abstract": "Updated abstract",
    "data_steward": "new-steward@example.com"
  }
}
```

**Responses:**
- `200 OK`: `{"message": "Metadata saved successfully"}` - Metadata saved successfully
- `400 Bad Request`: Validation failed (includes detailed error information)
- `404 Not Found`: Dataset does not exist
- `500 Internal Server Error`: Server error occurred

### File Upload Endpoints

#### `POST /datasets/{dataset_id}/upload`
**Summary:** Upload a file to the dataset's metadata folder.

**Description:** Uploads a file to the dataset's `.metadata` directory and automatically adds file information to the dataset's structural metadata. The uploaded file will be stored alongside other metadata files and its information will be tracked in the `file_descriptions` array.

**Parameters:**
- `dataset_id` (path, required): The ID of the dataset
- `comment` (query, optional): Optional description of the file's content or purpose

**Request Body:** `multipart/form-data`
- `file` (required): The file to upload

**Responses:**
- `200 OK`: `FileUploadResponse` - File uploaded successfully
- `404 Not Found`: Dataset does not exist
- `500 Internal Server Error`: Upload failed

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/d_dataset_RNAseq_rep1/upload?comment=Protocol%20documentation" \
  -F "file=@protocol.pdf"
```

**Example Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "protocol.pdf",
  "file_path": "/data/p_MyResearchProject/d_dataset_RNAseq_rep1/.metadata/protocol.pdf",
  "file_size": 245760,
  "comment": "Protocol documentation"
}
```

**File Information Storage:**
After successful upload, the file information is automatically added to the dataset's structural metadata (`dataset_structural.json`) in the `file_descriptions` array:

```json
{
  "file_descriptions": [
    {
      "file_name": "protocol.pdf",
      "role": "uploaded_file",
      "file_path": ".metadata/protocol.pdf",
      "file_description": "Protocol documentation",
      "file_extension": "pdf",
      "file_size_bytes": 245760,
      "file_type_os": "file",
      "file_created_utc": "2024-01-15T10:30:00Z",
      "file_modified_utc": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Security Features:**
- Filename sanitization to prevent path traversal attacks
- Automatic unique naming to prevent file conflicts
- File size validation
- Error handling that doesn't expose sensitive system information

### Experiment Workflow Endpoints

#### `POST /datasets/{dataset_id}/contextual`
**Summary:** Create a new experiment contextual metadata template.

**Description:** The backend receives a `schema_id`. It uses the `SchemaManager` to find the corresponding schema file (local or default). It then calls `metadata_generator.create_experiment_contextual_template`, passing the resolved schema path to generate a template that conforms to the user's choice.

**Parameters:**
- `dataset_id` (path, required): The ID of the dataset

**Request Body:** `ContextualTemplatePayload`
```json
{
  "schema_id": "genomics_sequencing"
}
```

**Responses:**
- `201 Created`: `{"message": "Contextual template created successfully", "file_path": "path/to/new/file.json"}` - Template created successfully
- `404 Not Found`: Dataset or requested `schema_id` does not exist
- `500 Internal Server Error`: Server error occurred

#### `POST /datasets/{dataset_id}/finalize`
**Summary:** Finalize a dataset and generate its V2 complete metadata.

**Description:** The backend's `v2_generator` will perform the completion check. The validation of the `experiment_contextual.json` file will now be dynamic: it will read the `"$schema"` property from within the file itself to load the correct schema for the final validation step.

**Parameters:**
- `dataset_id` (path, required): The ID of the dataset

**Request Body:** `FinalizePayload` (optional)
```json
{
  "experiment_id": "exp_001"
}
```

**Responses:**
- `200 OK`: `{"message": "Dataset finalized successfully", "v2_file_path": "path/to/v2/file.json"}` - Dataset finalized successfully
- `400 Bad Request`: Contextual metadata is incomplete or fails validation against its specified schema
- `404 Not Found`: Dataset or its contextual metadata file does not exist
- `500 Internal Server Error`: Server error occurred

### System Endpoints

#### `GET /health`
**Summary:** Health check endpoint.

**Description:** Returns the current health status of the API service and system configuration.

**Parameters:** None

**Responses:**
- `200 OK`: Health status information

**Example Response:**
```json
{
  "status": "healthy",
  "service": "FAIR Metadata Enrichment API",
  "monitor_path": "/data",
  "monitor_path_absolute": "/absolute/path/to/data",
  "monitor_exists": true,
  "current_dir": "/app"
}
```

#### `POST /config/reload`
**Summary:** Reload system configuration.

**Description:** Forces the system to reload its configuration from the `.fair_meta_config.yaml` file.

**Parameters:** None

**Request Body:** Optional configuration payload

**Responses:**
- `200 OK`: `{"message": "Configuration reloaded successfully"}` - Configuration reloaded successfully
- `500 Internal Server Error`: Configuration reload failed
## Error Handling

The API uses standard HTTP status codes and provides detailed error information in the response body.

### Common Error Responses

#### `400 Bad Request`
```json
{
  "error": "ValidationError",
  "message": "Validation failed",
  "details": {
    "field": "dataset_title",
    "error": "This field is required"
  }
}
```

#### `404 Not Found`
```json
{
  "error": "ResourceNotFoundError",
  "message": "Dataset 'd_nonexistent' not found",
  "details": {
    "resource_type": "dataset",
    "resource_id": "d_nonexistent"
  }
}
```

#### `500 Internal Server Error`
```json
{
  "error": "InternalServerError",
  "message": "An unexpected error occurred",
  "details": {
    "error_id": "err_123456789"
  }
}
```

## Data Models

### Core Data Models (Pydantic Schemas)

These models define the structure of API communication:

```python
class ProjectSummary(BaseModel):
    project_id: str = Field(..., description="Unique identifier for the project")
    project_title: Optional[str] = Field(None, description="Title of the project")
    path: str = Field(..., description="Absolute path to the project folder")
    dataset_count: int = Field(..., description="Number of datasets within the project")

class DatasetSummary(BaseModel):
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    dataset_title: Optional[str] = Field(None, description="Title of the dataset")
    path: str = Field(..., description="Absolute path to the dataset folder")
    metadata_status: str = Field(..., description="Current status (V1_Ingested, V2_Finalized)")

class SchemaInfo(BaseModel):
    schema_id: str = Field(..., description="Unique identifier for the schema")
    schema_title: str = Field(..., description="User-friendly title for the schema")
    schema_description: Optional[str] = Field(None, description="Brief description of the schema's purpose")
    source: str = Field(..., description="Source of the schema ('default' or 'local_override')")

class MetadataFile(BaseModel):
    content: Dict[str, Any] = Field(..., description="The full JSON content of the metadata file")
    schema_info: SchemaInfo = Field(..., description="Information about the schema used to validate this content")

class MetadataUpdatePayload(BaseModel):
    content: Dict[str, Any] = Field(..., description="The full JSON content of the metadata file to be saved")

class ContextualTemplatePayload(BaseModel):
    schema_id: str = Field(..., description="The ID of the contextual schema to use")

class FinalizePayload(BaseModel):
    experiment_id: str = Field(..., description="The unique ID of the experiment to be finalized")

class FileUploadResponse(BaseModel):
    message: str = Field(..., description="Upload status message")
    filename: str = Field(..., description="Name of the uploaded file")
    file_path: str = Field(..., description="Path where the file was stored")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    comment: Optional[str] = Field(None, description="Comment describing the uploaded file")
```

## API Design Principles

### Dynamic Schema Resolution

The API implements a **Schema Resolution Principle** that prioritizes local overrides over packaged defaults:

1. **Local Override First**: Check if a `.template_schemas` directory exists within the current `MONITOR_PATH`. If it contains the required schema, use this local version.

2. **Packaged Default Second**: If no local override is found, fall back to loading the default schema that was packaged with the application.

This allows for:
- **Customization**: Local modifications to schemas for specific projects or institutions
- **Version Control**: Local schemas can be version-controlled with the data
- **Backward Compatibility**: Always falls back to working defaults if local schemas are missing

### Key Benefits

- **Stable API Contract**: The routes and basic request/response models are stable, making frontend development predictable
- **Dynamic Backend Logic**: The complexity of choosing between default and local schemas is entirely encapsulated within the backend `SchemaManager`
- **GUI is Empowered but Simple**: The GUI can discover available schemas, request templates based on a chosen schema, and edit/save metadata without knowing underlying file paths
- **Future-Proof**: When packaged, the `SchemaManager`'s logic for finding default schemas points to the packaged location, while local override logic remains the same