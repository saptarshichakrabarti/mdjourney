
import axios from 'axios';
import type {
  ProjectSummary,
  DatasetSummary,
  SchemaInfo,
  MetadataFile,
  MetadataUpdatePayload,
  ContextualTemplatePayload,
  FinalizePayload,
  FileUploadResponse,
} from '../types/api';
import { API_ENDPOINTS } from '../types/api';


const apiClient = axios.create({
  baseURL: '/api',
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // On session expiry or unauthorized access, force a redirect to the login page.
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);


// API Service class
export class APIService {
  // Health check
  static async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get(API_ENDPOINTS.HEALTH);
    return response.data;
  }

  // Rescan projects and datasets
  static async rescanProjects(): Promise<{ message: string; status: string }> {
    const response = await apiClient.post(API_ENDPOINTS.RESCAN);
    return response.data;
  }

  // Projects
  static async getProjects(): Promise<ProjectSummary[]> {
    const response = await apiClient.get(API_ENDPOINTS.PROJECTS);
    return response.data;
  }

  static async getProjectDatasets(projectId: string): Promise<DatasetSummary[]> {
    const response = await apiClient.get(API_ENDPOINTS.PROJECT_DATASETS(projectId));
    return response.data;
  }

  // Schemas
  static async getContextualSchemas(): Promise<SchemaInfo[]> {
    const response = await apiClient.get(API_ENDPOINTS.CONTEXTUAL_SCHEMAS);
    return response.data;
  }

  static async getSchema(type: string, id: string): Promise<Record<string, any>> {
    const response = await apiClient.get(API_ENDPOINTS.SCHEMA(type, id));
    return response.data;
  }

  // Metadata
  static async getProjectMetadata(projectId: string, type: string): Promise<MetadataFile> {
    const response = await apiClient.get(API_ENDPOINTS.PROJECT_METADATA(projectId, type));
    return response.data;
  }

  static async updateProjectMetadata(
    projectId: string,
    type: string,
    payload: MetadataUpdatePayload
  ): Promise<string> {
    const response = await apiClient.put(API_ENDPOINTS.PROJECT_METADATA(projectId, type), payload);
    return response.data;
  }

  static async getMetadata(datasetId: string, type: string): Promise<MetadataFile> {
    const response = await apiClient.get(API_ENDPOINTS.METADATA(datasetId, type));
    return response.data;
  }

  static async updateMetadata(
    datasetId: string,
    type: string,
    payload: MetadataUpdatePayload
  ): Promise<string> {
    const response = await apiClient.put(API_ENDPOINTS.METADATA(datasetId, type), payload);
    return response.data;
  }

  // Contextual templates
  static async createContextualTemplate(
    datasetId: string,
    payload: ContextualTemplatePayload
  ): Promise<string> {
    const response = await apiClient.post(API_ENDPOINTS.CREATE_CONTEXTUAL(datasetId), payload);
    return response.data;
  }

  // Dataset finalization
  static async finalizeDataset(datasetId: string, payload: FinalizePayload): Promise<string> {
    const response = await apiClient.post(API_ENDPOINTS.FINALIZE_DATASET(datasetId), payload);
    return response.data;
  }

  // File upload
  static async uploadFile(datasetId: string, file: File, comment?: string): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (comment) {
      params.append('comment', comment);
    }

    const response = await apiClient.post(
      `${API_ENDPOINTS.UPLOAD_FILE(datasetId)}?${params.toString()}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }
}

export default apiClient;
