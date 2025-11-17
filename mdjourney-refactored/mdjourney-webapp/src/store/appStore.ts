import { create } from 'zustand';

export interface AppState {
  // Selected items
  selectedProjectId: string | null;
  selectedDatasetId: string | null;
  selectedMetadataType: string | null;

  // UI state
  focusedField: string | null;
  validationErrors: Record<string, string[]>;

  // Actions
  setSelectedProject: (projectId: string | null) => void;
  setSelectedDataset: (datasetId: string | null) => void;
  setSelectedMetadataType: (metadataType: string | null) => void;
  setFocusedField: (field: string | null) => void;
  setValidationErrors: (errors: Record<string, string[]>) => void;
  clearValidationErrors: () => void;
  resetSelection: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  selectedProjectId: null,
  selectedDatasetId: null,
  selectedMetadataType: null,
  focusedField: null,
  validationErrors: {},

  // Actions
  setSelectedProject: (projectId) =>
    set((state) => ({
      selectedProjectId: projectId,
      // Clear dataset selection when project changes
      selectedDatasetId: projectId ? state.selectedDatasetId : null,
      selectedMetadataType: projectId ? state.selectedMetadataType : null,
    })),

  setSelectedDataset: (datasetId) =>
    set((state) => ({
      selectedDatasetId: datasetId,
      // Clear metadata type when dataset changes
      selectedMetadataType: datasetId ? state.selectedMetadataType : null,
    })),

  setSelectedMetadataType: (metadataType) =>
    set({ selectedMetadataType: metadataType }),

  setFocusedField: (field) => set({ focusedField: field }),

  setValidationErrors: (errors) => set({ validationErrors: errors }),

  clearValidationErrors: () => set({ validationErrors: {} }),

  resetSelection: () =>
    set({
      selectedProjectId: null,
      selectedDatasetId: null,
      selectedMetadataType: null,
      focusedField: null,
      validationErrors: {},
    }),
}));