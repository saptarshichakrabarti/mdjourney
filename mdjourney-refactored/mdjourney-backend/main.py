"""
FAIR Metadata Enrichment API - Main Application
FastAPI application implementing the metadata enrichment API.
"""

import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from dependencies import (
    get_metadata_service,
    get_project_service,
    get_schema_service,
)
from models.pydantic_models import (
    APIResponse,
    ContextualTemplatePayload,
    DatasetSummary,
    ErrorResponse,
    FileUploadResponse,
    FinalizePayload,
    MetadataFile,
    MetadataUpdatePayload,
    ProjectSummary,
    SchemaInfo,
)
from routers.services import MetadataService, ProjectService, SchemaService
from app.core.config import find_config_file, initialize_config
from app.core.exceptions import (
    MDJourneyError,
    ResourceNotFoundError,
    ValidationError,
    SchemaNotFoundError,
    MetadataGenerationError,
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    InputValidationError,
    PathTraversalError,
    create_error_response,
)
from app.core.security import (
    InputValidator,
    PathSanitizer,
    SecurityHeaders,
    rate_limiter,
)
from app.core.auth import (
    get_current_user,
    get_optional_user,
    get_client_ip,
    RoleBasedAccessControl,
)

logger = logging.getLogger(__name__)

# --- SINGLE POINT OF TRUTH FOR CONFIGURATION ---
# This code runs exactly ONCE when the API server starts up.
# It finds and loads the .fair_meta_config.yaml file into the global state.
# Note: If running via gateway (with --config-file), this will be overridden in load_configuration()
logger.info("--- API Server Starting Up: Initializing Configuration ---")
config_file = find_config_file()
if config_file:
    logger.info(f"Found configuration file: {config_file}")
    if not initialize_config(str(config_file)):
        logger.warning("Could not initialize configuration from file. Will try command-line config if provided.")
        # Don't exit here - allow command-line config to be used
else:
    logger.info("No .fair_meta_config.yaml file found. Will use command-line config if provided.")
    # Don't exit here - allow command-line config to be used
# -----------------------------------------------

# Initialize FastAPI app
app = FastAPI(
    title="FAIR Metadata Enrichment API",
    description="API for managing FAIR-compliant research data metadata",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS with security restrictions
from app.core.config import get_cors_origins, get_api_config

api_config = get_api_config()
cors_config = api_config.get('cors', {})
allowed_origins = cors_config.get('origins', ['http://localhost:5173'])
allow_credentials = cors_config.get('credentials', True)
allow_methods = cors_config.get('methods', ["GET", "POST", "PUT", "DELETE"])
allow_headers = cors_config.get('headers', ["Authorization", "Content-Type", "X-Requested-With"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)


# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Add security headers and rate limiting."""
    # Add security headers
    response = await call_next(request)

    # Add security headers
    security_headers = SecurityHeaders.get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value

    # Rate limiting
    from app.core.config import get_rate_limit_config

    rate_limit_config = get_rate_limit_config()
    if rate_limit_config.get('enabled', True):
        max_requests = rate_limit_config.get('max_requests', 1000)
        window_seconds = rate_limit_config.get('window_seconds', 3600)

        client_ip = get_client_ip(request)
        if not rate_limiter.is_allowed(client_ip, max_requests=max_requests, window_seconds=window_seconds):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "detail": "Too many requests"}
            )

    return response


# Discovery Endpoints


@app.get("/api/v1/projects", response_model=List[ProjectSummary])
async def list_projects(
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    user_info: Optional[Dict] = Depends(get_optional_user)
) -> List[ProjectSummary]:
    """
    List all available projects.

    Scans the MONITOR_PATH and returns a summary of each valid project folder.
    """
    try:
        return await project_service.list_projects()
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/rescan")
async def rescan_projects(
    request: Request,
    user_info: Optional[Dict] = Depends(get_optional_user)
) -> Dict[str, str]:
    """
    Force a rescan of the monitor directory to detect new projects and datasets.

    This endpoint can be called when new files are added to refresh the backend's
    view of available projects and datasets.
    """
    try:
        # Note: With DI, services are created fresh for each request
        # No need to manually re-initialize services
        return {"message": "Rescan completed successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Error during rescan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/projects/{project_id}/datasets", response_model=List[DatasetSummary])
async def list_project_datasets(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    project_service: ProjectService = Depends(get_project_service),
    user_info: Optional[Dict] = Depends(get_optional_user)
) -> List[DatasetSummary]:
    """
    List all datasets within a specific project.

    Scans a project folder and returns a summary for each dataset.
    """
    try:
        # Validate input
        validated_project_id = InputValidator.validate_id(project_id, "Project ID")

        return await project_service.get_project_datasets(validated_project_id)
    except InputValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing datasets for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Schema Endpoints


@app.get("/api/v1/schemas/contextual", response_model=List[SchemaInfo])
async def list_contextual_schemas(
    schema_service: SchemaService = Depends(get_schema_service),
) -> List[SchemaInfo]:
    """
    Get the list of all available contextual schemas.

    The backend's SchemaManager will scan both the packaged default schema directory
    and the local .template_schemas/contextual directory in the active MONITOR_PATH.
    It returns a merged list, with local schemas overriding defaults if they share
    the same schema_id.
    """
    try:
        return await schema_service.list_contextual_schemas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/schemas/{schema_type}/{schema_id}", response_model=Dict[str, Any])
async def get_schema(
    schema_type: str = Path(
        ...,
        description="The type of schema (e.g., 'project', 'dataset_administrative', 'contextual')",
    ),
    schema_id: str = Path(..., description="The ID of the schema"),
    schema_service: SchemaService = Depends(get_schema_service),
) -> Dict[str, Any]:
    """
    Get the full JSON content of a specific schema.

    Allows the frontend to fetch the actual schema if needed for advanced
    client-side validation or form generation. The backend's SchemaManager
    will resolve whether to return the local or default version.
    """
    try:
        return await schema_service.get_schema(schema_type, schema_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Metadata Endpoints


@app.get(
    "/api/v1/projects/{project_id}/metadata/{metadata_type}",
    response_model=MetadataFile,
)
async def get_project_metadata(
    project_id: str = Path(..., description="The ID of the project"),
    metadata_type: str = Path(..., description="The type of metadata file"),
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> MetadataFile:
    """
    Get the content of a specific metadata file for a project.

    Returns the metadata content and the schema used to validate it.
    """
    try:
        return await metadata_service.get_project_metadata(project_id, metadata_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/api/v1/projects/{project_id}/metadata/{metadata_type}", response_model=APIResponse
)
async def update_project_metadata(
    project_id: str = Path(..., description="The ID of the project"),
    metadata_type: str = Path(..., description="The type of metadata file"),
    payload: Optional[MetadataUpdatePayload] = None,
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> APIResponse:
    """
    Update and save a specific metadata file for a project.

    Validates the metadata against the appropriate schema before saving.
    """
    try:
        result = metadata_service.update_project_metadata(
            project_id, metadata_type, payload
        )
        return APIResponse(message=result, data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/datasets/{dataset_id}/metadata/{metadata_type}",
    response_model=MetadataFile,
)
async def get_metadata(
    dataset_id: str = Path(..., description="The ID of the dataset"),
    metadata_type: str = Path(..., description="The type of metadata file"),
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> MetadataFile:
    """
    Get the content of a specific metadata file and the schema used to validate it.

    Reads the specified metadata file (e.g., dataset_administrative.json).
    The backend's SchemaManager then determines the correct schema (local or default)
    that applies to this file and returns both the file content and information
    about the active schema.
    """
    try:
        return metadata_service.get_metadata(dataset_id, metadata_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/api/v1/datasets/{dataset_id}/metadata/{metadata_type}", response_model=APIResponse
)
async def update_metadata(
    dataset_id: str = Path(..., description="The ID of the dataset"),
    metadata_type: str = Path(..., description="The type of metadata file"),
    payload: Optional[MetadataUpdatePayload] = None,
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> APIResponse:
    """
    Update and save a specific metadata file.

    The backend receives the new JSON content. It uses the SchemaManager to resolve
    and load the correct schema (local override or packaged default). It validates
    the incoming content against this resolved schema. If valid, it saves the file
    and commits the change.
    """
    try:
        message = metadata_service.update_metadata(dataset_id, metadata_type, payload)
        return APIResponse(message=message, data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Experiment Workflow Endpoints


@app.post("/api/v1/datasets/{dataset_id}/contextual", response_model=APIResponse)
async def create_contextual_template(
    dataset_id: str = Path(..., description="The ID of the dataset"),
    payload: Optional[ContextualTemplatePayload] = None,
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> APIResponse:
    """
    Create a new experiment contextual metadata template.

    The backend receives a schema_id. It uses the SchemaManager to find the
    corresponding schema file (local or default). It then calls
    metadata_generator.create_experiment_contextual_template, passing the resolved
    schema path to generate a template that conforms to the user's choice.
    """
    try:
        message = metadata_service.create_contextual_template(dataset_id, payload)
        return APIResponse(message=message, data=None)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/datasets/{dataset_id}/finalize", response_model=APIResponse)
async def finalize_dataset(
    dataset_id: str = Path(..., description="The ID of the dataset"),
    payload: Optional[FinalizePayload] = None,
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> APIResponse:
    """
    Finalize a dataset and generate its V2 complete metadata.

    The backend's v2_generator will perform the completion check. The validation
    of the experiment_contextual.json file will now be dynamic: it will read the
    "$schema" property from within the file itself to load the correct schema
    for the final validation step.
    """
    try:
        message = metadata_service.finalize_dataset(dataset_id, payload)
        return APIResponse(message=message, data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint


@app.get("/api/v1/health")
async def health_check(project_service: ProjectService = Depends(get_project_service)) -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        return {
            "status": "healthy",
            "service": "FAIR Metadata Enrichment API",
            "monitor_path": str(project_service.monitor_path),
            "monitor_path_absolute": str(project_service.monitor_path.absolute()),
            "monitor_exists": project_service.monitor_path.exists(),
            "current_dir": str(PathLib.cwd()),
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "FAIR Metadata Enrichment API",
            "error": str(e),
        }


@app.post("/api/v1/config/reload")
async def reload_config(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Reload configuration (optionally setting monitor_path).

    Accepts optional JSON body: {"monitor_path": "/abs/path"}
    """
    try:
        from app.core.config import (
            get_monitor_path,
            reload_config_from_environment,
            set_custom_schema_path,
            set_monitor_path,
        )

        # If explicit paths are provided, set them
        if payload and isinstance(payload, dict):
            changed = False
            if payload.get("monitor_path"):
                set_ok = set_monitor_path(str(payload["monitor_path"]))
                if not set_ok:
                    return {
                        "status": "error",
                        "message": "Invalid monitor_path provided",
                    }
                changed = True
            if payload.get("custom_schema_path"):
                set_custom_schema_path(str(payload["custom_schema_path"]))
                changed = True

            if changed:
                return {
                    "status": "success",
                    "message": "Configuration updated",
                    "monitor_path": str(get_monitor_path()),
                    "monitor_path_absolute": str(get_monitor_path().absolute()),
                    "monitor_path_exists": get_monitor_path().exists(),
                }

        # Otherwise, attempt to reload from environment
        reloaded = reload_config_from_environment()

        if reloaded:
            return {
                "status": "success",
                "message": "Configuration reloaded from environment",
                "monitor_path": str(get_monitor_path()),
                "monitor_path_absolute": str(get_monitor_path().absolute()),
                "monitor_path_exists": get_monitor_path().exists(),
            }
        else:
            return {
                "status": "no_change",
                "message": "No environment override found, using existing configuration",
                "monitor_path": str(get_monitor_path()),
                "monitor_path_absolute": str(get_monitor_path().absolute()),
                "monitor_path_exists": get_monitor_path().exists(),
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to reload configuration: {str(e)}",
        }


# File Upload Endpoints


async def _add_file_to_metadata(
    dataset_id: str,
    file_path: PathLib,
    file_size: int,
    comment: Optional[str],
    project_service: ProjectService
) -> None:
    """Add uploaded file information to the dataset's structural metadata."""
    try:
        from routers.services import MetadataService
        from dependencies import get_metadata_service

        # Get metadata service
        metadata_service = get_metadata_service()

        # Get current structural metadata
        try:
            metadata_file = metadata_service.get_metadata(dataset_id, "dataset_structural")
            current_content = metadata_file.content
        except Exception:
            # If metadata doesn't exist, create basic structure
            current_content = {
                "dataset_identifier": dataset_id,
                "file_descriptions": []
            }

        # Ensure file_descriptions array exists
        if "file_descriptions" not in current_content:
            current_content["file_descriptions"] = []

        # Create file description entry
        file_description = {
            "file_name": file_path.name,
            "role": "uploaded_file",
            "file_path": str(file_path.relative_to(file_path.parent.parent)),  # Relative to dataset
            "file_description": comment or "",
            "file_extension": file_path.suffix.lstrip('.'),
            "file_size_bytes": file_size,
            "file_type_os": "file",
            "file_created_utc": datetime.utcnow().isoformat() + "Z",
            "file_modified_utc": datetime.utcnow().isoformat() + "Z",
        }

        # Add to file descriptions
        current_content["file_descriptions"].append(file_description)

        # Update metadata
        from models.pydantic_models import MetadataUpdatePayload
        payload = MetadataUpdatePayload(content=current_content)
        metadata_service.update_metadata(dataset_id, "dataset_structural", payload)

        logger.info(f"Added file {file_path.name} to dataset structural metadata")

    except Exception as e:
        logger.error(f"Failed to add file to metadata: {str(e)}")
        # Don't raise exception - file upload should still succeed even if metadata update fails


@app.post("/api/v1/datasets/{dataset_id}/upload", response_model=FileUploadResponse)
async def upload_file_to_dataset(
    dataset_id: str = Path(..., description="The ID of the dataset"),
    file: UploadFile = File(..., description="The file to upload"),
    comment: Optional[str] = Query(None, description="Optional comment describing the file"),
    project_service: ProjectService = Depends(get_project_service),
) -> FileUploadResponse:
    """
    Upload a file to the dataset's .metadata folder.

    This endpoint allows users to upload files that will be stored in the
    dataset's .metadata directory alongside the metadata JSON files.
    """
    try:
        # Get the dataset path from the project service
        dataset_path = project_service.get_dataset_path(dataset_id)
        if not dataset_path or not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        # Create .metadata directory if it doesn't exist
        metadata_dir = dataset_path / ".metadata"
        metadata_dir.mkdir(exist_ok=True)

        # Generate safe filename (prevent path traversal)
        import re
        import time
        safe_filename = re.sub(r'[^\w\-_\.]', '_', file.filename)
        if not safe_filename:
            safe_filename = f"uploaded_file_{int(time.time())}"

        # Ensure unique filename
        file_path = metadata_dir / safe_filename
        counter = 1
        while file_path.exists():
            name, ext = os.path.splitext(safe_filename)
            file_path = metadata_dir / f"{name}_{counter}{ext}"
            counter += 1

        # Save the file
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Get file size
        file_size = len(file_content)

        # Add file information to dataset structural metadata
        await _add_file_to_metadata(dataset_id, file_path, file_size, comment, project_service)

        logger.info(f"File uploaded successfully: {file_path} ({file_size} bytes)")

        return FileUploadResponse(
            message="File uploaded successfully",
            filename=file_path.name,
            file_path=str(file_path),
            file_size=file_size,
            comment=comment
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


# Error Handlers


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 errors with detailed information."""
    # Get the detail from HTTPException if available
    detail = getattr(exc, 'detail', str(exc))
    return JSONResponse(
        status_code=404,
        content={
            "error": "Resource not found",
            "details": detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle validation errors with detailed field information."""
    if hasattr(exc, 'errors'):
        # Pydantic validation errors
        field_errors: Dict[str, List[str]] = {}
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(error["msg"])

        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "field_errors": field_errors,
                "path": str(request.url.path),
                "method": request.method
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": str(exc),
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(MDJourneyError)
async def mdjourney_error_handler(request: Request, exc: MDJourneyError) -> JSONResponse:
    """Handle custom MDJourney exceptions."""
    return JSONResponse(
        status_code=400,
        content=create_error_response(exc)
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """Handle resource not found errors."""
    return JSONResponse(
        status_code=404,
        content=create_error_response(exc)
    )


@app.exception_handler(ValidationError)
async def custom_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content=create_error_response(exc)
    )


@app.exception_handler(SchemaNotFoundError)
async def schema_not_found_handler(request: Request, exc: SchemaNotFoundError) -> JSONResponse:
    """Handle schema not found errors."""
    return JSONResponse(
        status_code=404,
        content=create_error_response(exc)
    )


@app.exception_handler(MetadataGenerationError)
async def metadata_generation_error_handler(request: Request, exc: MetadataGenerationError) -> JSONResponse:
    """Handle metadata generation errors."""
    return JSONResponse(
        status_code=500,
        content=create_error_response(exc)
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle internal server errors."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path),
            "method": request.method
        }
    )


def load_configuration(config_path: str) -> dict:
    """
    Loads configuration from a JSON or YAML file.
    This function is used by the gateway to pass session-specific configs.
    """
    print(f"INFO: Backend loading configuration from {config_path}")
    try:
        # Use ConfigManager to load config (supports both JSON and YAML)
        from app.core.config_manager import ConfigManager
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()

        # Initialize global config state
        from app.core.config import initialize_config
        if not initialize_config(config_path):
            raise RuntimeError("Failed to initialize configuration")

        return config
    except Exception as e:
        print(f"ERROR: Backend failed to load config from {config_path}: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="MDJourney Backend Service")
    parser.add_argument("--port", type=int, required=True, help="Port to bind the service to.")
    parser.add_argument("--config-file", type=str, required=True, help="Path to the session's configuration file (JSON or YAML).")

    args = parser.parse_args()
    config = load_configuration(args.config_file)

    # Validation Step: Log keys from the config to prove it was loaded correctly.
    # ConfigManager normalizes keys from gateway format (camelCase) to internal format (snake_case)
    # After normalization, all configs use snake_case matching the template format
    monitor_path = config.get("monitor_path")
    if not monitor_path:
        print(f"WARNING: 'monitor_path' not found in config. Available keys: {list(config.keys())}")
    print(f"INFO: Backend started on port {args.port}. Monitor path: '{monitor_path}'")

    uvicorn.run(app, host="127.0.0.1", port=args.port)
