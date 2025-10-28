"""
Pydantic models for the FAIR Metadata Enrichment API.
Defines the structure of API communication and data validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    """Summary information for a project."""

    project_id: str = Field(
        ..., description="Unique identifier for the project, e.g., 'p_MyResearchProject'"
    )
    project_title: Optional[str] = Field(
        None, description="The descriptive title of the project"
    )
    path: str = Field(..., description="Absolute path to the project directory")
    dataset_count: int = Field(
        ..., description="Number of datasets within the project"
    )

    class Config:
        from_attributes = True


class DatasetSummary(BaseModel):
    """Summary information for a dataset."""

    dataset_id: str = Field(
        ..., description="Unique identifier for the dataset, e.g., 'd_dataset_RNAseq_rep1'"
    )
    dataset_title: Optional[str] = Field(
        None, description="The descriptive title of the dataset"
    )
    path: str = Field(..., description="Absolute path to the dataset directory")
    metadata_status: str = Field(
        ..., description="The current metadata completion status, e.g., 'V1_Ingested'"
    )

    class Config:
        from_attributes = True


class ProjectDetail(ProjectSummary):
    """Detailed information for a project including its datasets."""

    datasets: List[DatasetSummary] = Field(
        ..., description="List of datasets contained within the project"
    )


class SchemaInfo(BaseModel):
    """Information about a schema."""

    schema_id: str = Field(
        ...,
        description="A unique identifier for the schema, e.g., 'genomics_sequencing'.",
    )
    schema_title: str = Field(
        ...,
        description="A user-friendly title for the schema, e.g., 'Genomics Sequencing Run'.",
    )
    schema_description: Optional[str] = Field(
        None, description="A brief description of the schema's purpose."
    )
    source: str = Field(
        ...,
        description="Indicates the source of the schema ('default' or 'local_override').",
    )


class MetadataFile(BaseModel):
    """Metadata file content with schema information."""

    content: Dict[str, Any] = Field(
        ..., description="The full JSON content of the metadata file."
    )
    schema_info: SchemaInfo = Field(
        ..., description="Information about the schema used to validate this content."
    )
    schema_definition: Dict[str, Any] = Field(
        ...,
        description="The actual JSON schema definition used to validate this content.",
    )


class MetadataUpdatePayload(BaseModel):
    """Payload for updating metadata files."""

    content: Dict[str, Any] = Field(
        ..., description="The full JSON content of the metadata file to be saved."
    )


class ContextualTemplatePayload(BaseModel):
    """Payload for creating contextual templates."""

    schema_id: Optional[str] = Field(
        None,
        description="The ID of the contextual schema to use for generating the template. If None, uses the default experiment contextual schema.",
    )


class FinalizePayload(BaseModel):
    """Payload for finalizing datasets."""

    experiment_id: str = Field(
        ..., description="The unique ID of the experiment to be finalized."
    )


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    message: str = Field(..., description="Response message.")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Response data if applicable."
    )


class FileUploadResponse(BaseModel):
    """Response for file upload operations."""

    message: str = Field(..., description="Upload status message.")
    filename: str = Field(..., description="Name of the uploaded file.")
    file_path: str = Field(..., description="Path where the file was stored.")
    file_size: int = Field(..., description="Size of the uploaded file in bytes.")
    comment: Optional[str] = Field(None, description="Comment describing the uploaded file.")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message.")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details."
    )
