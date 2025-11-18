// API Types matching our FastAPI backend models

export interface ProjectSummary {
  project_id: string;
  project_title?: string;
  path: string;
  folder_count: number;
  dataset_count: number;
}

export interface DatasetSummary {
  dataset_id: string;
  dataset_title?: string;
  path: string;
  metadata_status: 'V0_Initial' | 'V1_Ingested' | 'V2_Finalized';
}

export interface SchemaInfo {
  schema_id: string;
  schema_title: string;
  schema_description?: string;
  source: 'default' | 'local_override';
}

export interface MetadataFile {
  content: Record<string, any>;
  schema_info: SchemaInfo;
  schema_definition: Record<string, any>;
}

export interface MetadataUpdatePayload {
  content: Record<string, any>;
}

export interface ContextualTemplatePayload {
  schema_id?: string;
}

export interface FinalizePayload {
  experiment_id: string;
}

export interface FileUploadResponse {
  message: string;
  filename: string;
  file_path: string;
  file_size: number;
  comment?: string;
}

export interface APIResponse<T> {
  data: T;
  message: string;
}

export interface ErrorResponse {
  detail: string;
}

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: '/v1/health',
  RESCAN: '/v1/rescan',
  PROJECTS: '/v1/projects',
  PROJECT_DATASETS: (projectId: string) => `/v1/projects/${projectId}/datasets`,
  CONTEXTUAL_SCHEMAS: '/v1/schemas/contextual',
  SCHEMA: (type: string, id: string) => `/v1/schemas/${type}/${id}`,
  PROJECT_METADATA: (projectId: string, type: string) => `/v1/projects/${projectId}/metadata/${type}`,
  METADATA: (datasetId: string, type: string) => `/v1/datasets/${datasetId}/metadata/${type}`,
  CREATE_CONTEXTUAL: (datasetId: string) => `/v1/datasets/${datasetId}/contextual`,
  FINALIZE_DATASET: (datasetId: string) => `/v1/datasets/${datasetId}/finalize`,
  UPLOAD_FILE: (datasetId: string) => `/v1/datasets/${datasetId}/upload`,
} as const;
