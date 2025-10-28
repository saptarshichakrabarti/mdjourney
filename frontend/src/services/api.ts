import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
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

// Cache configuration
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class APICache {
  private cache = new Map<string, CacheEntry<any>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  set<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > entry.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  // Clear cache entries matching a pattern
  clearPattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  // Get cache statistics
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
}

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    // Only log errors that are not expected 404s for missing metadata
    const isExpected404 = error.response?.status === 404 &&
      (error.config?.url?.includes('/metadata/experiment_contextual') ||
       error.config?.url?.includes('/metadata/project_descriptive') && error.config?.url?.includes('/datasets/'));

    if (!isExpected404) {
      console.error('API Error:', error);
    }
    return Promise.reject(error);
  }
);

// Global cache instance
const apiCache = new APICache();


// API Service class with caching
export class APIService {
  // Cache TTL configurations (in milliseconds)
  private static readonly CACHE_TTL = {
    PROJECTS: 1 * 60 * 1000,        // 1 minute
    DATASETS: 2 * 60 * 1000,        // 2 minutes
    SCHEMAS: 30 * 60 * 1000,        // 30 minutes
    METADATA: 5 * 60 * 1000,        // 5 minutes
    CONTEXTUAL_SCHEMAS: 30 * 60 * 1000, // 30 minutes
  };

  // Health check
  static async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get(API_ENDPOINTS.HEALTH);
    return response.data;
  }

  // Rescan projects and datasets
  static async rescanProjects(): Promise<{ message: string; status: string }> {
    const response = await apiClient.post(API_ENDPOINTS.RESCAN);

    // Clear project and dataset caches after rescan
    apiCache.clearPattern('^projects');
    apiCache.clearPattern('^datasets');

    return response.data;
  }

  // Projects with caching
  static async getProjects(): Promise<ProjectSummary[]> {
    const cacheKey = 'projects';
    const cached = apiCache.get<ProjectSummary[]>(cacheKey);
    if (cached) {
      console.log('Cache hit: projects');
      return cached;
    }

    console.log('Cache miss: projects, fetching from API');
    const response = await apiClient.get(API_ENDPOINTS.PROJECTS);
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.PROJECTS);
    return data;
  }

  static async getProjectDatasets(projectId: string): Promise<DatasetSummary[]> {
    const cacheKey = `datasets:${projectId}`;
    const cached = apiCache.get<DatasetSummary[]>(cacheKey);
    if (cached) {
      console.log(`Cache hit: datasets for project ${projectId}`);
      return cached;
    }

    console.log(`Cache miss: datasets for project ${projectId}, fetching from API`);
    const response = await apiClient.get(API_ENDPOINTS.PROJECT_DATASETS(projectId));
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.DATASETS);
    return data;
  }

  // Schemas with caching
  static async getContextualSchemas(): Promise<SchemaInfo[]> {
    const cacheKey = 'contextual-schemas';
    const cached = apiCache.get<SchemaInfo[]>(cacheKey);
    if (cached) {
      console.log('Cache hit: contextual schemas');
      return cached;
    }

    console.log('Cache miss: contextual schemas, fetching from API');
    const response = await apiClient.get(API_ENDPOINTS.CONTEXTUAL_SCHEMAS);
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.CONTEXTUAL_SCHEMAS);
    return data;
  }

  static async getSchema(type: string, id: string): Promise<Record<string, any>> {
    const cacheKey = `schema:${type}:${id}`;
    const cached = apiCache.get<Record<string, any>>(cacheKey);
    if (cached) {
      console.log(`Cache hit: schema ${type}:${id}`);
      return cached;
    }

    console.log(`Cache miss: schema ${type}:${id}, fetching from API`);
    const response = await apiClient.get(API_ENDPOINTS.SCHEMA(type, id));
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.SCHEMAS);
    return data;
  }

  // Metadata with caching
  static async getProjectMetadata(projectId: string, type: string): Promise<MetadataFile> {
    const cacheKey = `project-metadata:${projectId}:${type}`;
    const cached = apiCache.get<MetadataFile>(cacheKey);
    if (cached) {
      console.log(`Cache hit: project metadata ${projectId}:${type}`);
      return cached;
    }

    console.log(`Cache miss: project metadata ${projectId}:${type}, fetching from API`);
    const response = await apiClient.get(API_ENDPOINTS.PROJECT_METADATA(projectId, type));
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.METADATA);
    return data;
  }

  static async updateProjectMetadata(
    projectId: string,
    type: string,
    payload: MetadataUpdatePayload
  ): Promise<string> {
    const response = await apiClient.put(API_ENDPOINTS.PROJECT_METADATA(projectId, type), payload);

    // Invalidate related caches
    apiCache.delete(`project-metadata:${projectId}:${type}`);
    apiCache.clearPattern(`^projects`);

    return response.data;
  }

  static async getMetadata(datasetId: string, type: string): Promise<MetadataFile> {
    const cacheKey = `metadata:${datasetId}:${type}`;
    const cached = apiCache.get<MetadataFile>(cacheKey);
    if (cached) {
      console.log(`Cache hit: metadata ${datasetId}:${type}`);
      return cached;
    }

    console.log(`Cache miss: metadata ${datasetId}:${type}, fetching from API`);
    const response = await apiClient.get(API_ENDPOINTS.METADATA(datasetId, type));
    const data = response.data;

    apiCache.set(cacheKey, data, APIService.CACHE_TTL.METADATA);
    return data;
  }

  static async updateMetadata(
    datasetId: string,
    type: string,
    payload: MetadataUpdatePayload
  ): Promise<string> {
    const response = await apiClient.put(API_ENDPOINTS.METADATA(datasetId, type), payload);

    // Invalidate related caches
    apiCache.delete(`metadata:${datasetId}:${type}`);
    apiCache.clearPattern(`^datasets`);

    return response.data;
  }

  // Contextual templates
  static async createContextualTemplate(
    datasetId: string,
    payload: ContextualTemplatePayload
  ): Promise<string> {
    const response = await apiClient.post(API_ENDPOINTS.CREATE_CONTEXTUAL(datasetId), payload);

    // Invalidate related caches
    apiCache.clearPattern(`^datasets`);
    apiCache.delete(`metadata:${datasetId}:experiment_contextual`);

    return response.data;
  }

  // Dataset finalization
  static async finalizeDataset(datasetId: string, payload: FinalizePayload): Promise<string> {
    const response = await apiClient.post(API_ENDPOINTS.FINALIZE_DATASET(datasetId), payload);

    // Invalidate related caches
    apiCache.clearPattern(`^datasets`);
    apiCache.delete(`metadata:${datasetId}:complete_metadata`);

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

  // Cache management methods
  static clearCache(): void {
    apiCache.clear();
    console.log('API cache cleared');
  }

  static clearCachePattern(pattern: string): void {
    apiCache.clearPattern(pattern);
    console.log(`API cache cleared for pattern: ${pattern}`);
  }

  static getCacheStats(): { size: number; keys: string[] } {
    return apiCache.getStats();
  }

  // Preload commonly accessed data
  static async preloadCommonData(): Promise<void> {
    try {
      console.log('Preloading common data...');

      // Preload projects and contextual schemas in parallel
      const [projects] = await Promise.all([
        this.getProjects(),
        this.getContextualSchemas(),
      ]);

      // Preload datasets for each project
      const datasetPromises = projects.map(project =>
        this.getProjectDatasets(project.project_id).catch(error => {
          console.warn(`Failed to preload datasets for project ${project.project_id}:`, error);
          return [];
        })
      );

      await Promise.all(datasetPromises);

      console.log('Common data preloaded successfully');
    } catch (error) {
      console.error('Failed to preload common data:', error);
    }
  }
}

export default APIService;