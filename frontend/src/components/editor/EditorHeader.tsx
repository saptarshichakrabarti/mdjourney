import React from 'react';
import {
  Box,
  Typography,
  Button,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon, CloudUpload as UploadIcon } from '@mui/icons-material';

interface MetadataType {
  value: string;
  label: string;
  level: 'project' | 'dataset';
}

interface EditorHeaderProps {
  entityId: string | null;
  isEditingProject: boolean;
  selectedMetadataType: string | null;
  availableMetadataTypes: MetadataType[];
  editingContext: 'project' | 'dataset';
  onContextChange: (context: 'project' | 'dataset') => void;
  onMetadataTypeChange: (type: string) => void;
  onSave: () => void;
  onReset: () => void;
  onRefresh: () => void;
  onUploadClick: () => void;
  isSaving: boolean;
  isUploading: boolean;
  hasSelectedDataset: boolean;
  hasMetadataTypeSelected: boolean;
  mutationError: Error | null;
  mutationSuccess: boolean;
}

export const EditorHeader: React.FC<EditorHeaderProps> = ({
  entityId,
  isEditingProject,
  selectedMetadataType,
  availableMetadataTypes,
  editingContext,
  onContextChange,
  onMetadataTypeChange,
  onSave,
  onReset,
  onRefresh,
  onUploadClick,
  isSaving,
  isUploading,
  hasSelectedDataset,
  hasMetadataTypeSelected,
  mutationError,
  mutationSuccess,
}) => {
  return (
    <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Metadata Editor
          </Typography>
          {entityId && (
            <Typography variant="caption" color="text.secondary">
              Editing {isEditingProject ? 'Project' : 'Dataset'}: {entityId}
            </Typography>
          )}
        </Box>
        <Tooltip title="Refresh metadata">
          <span>
            <IconButton onClick={onRefresh} size="small" disabled={!hasMetadataTypeSelected}>
              <RefreshIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {/* Context Toggle and Metadata Type Selector */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        {/* Context Toggle */}
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Context</InputLabel>
          <Select
            value={editingContext}
            label="Context"
            onChange={(e) => onContextChange(e.target.value as 'project' | 'dataset')}
          >
            <MenuItem value="project">
              Project
            </MenuItem>
            <MenuItem value="dataset">
              Dataset
            </MenuItem>
          </Select>
        </FormControl>

        {/* Metadata Type Selector */}
        <FormControl fullWidth size="small">
          <InputLabel>Metadata Type</InputLabel>
          <Select
            value={selectedMetadataType || ''}
            label="Metadata Type"
            onChange={(e) => onMetadataTypeChange(e.target.value)}
          >
            {availableMetadataTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={onSave}
          disabled={isSaving || !hasMetadataTypeSelected}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onReset}
          disabled={!hasMetadataTypeSelected}
        >
          Reset
        </Button>
        <Button
          variant="outlined"
          startIcon={<UploadIcon />}
          onClick={onUploadClick}
          disabled={!hasSelectedDataset || isUploading}
        >
          {isUploading ? 'Uploading...' : 'Upload File'}
        </Button>
      </Box>

      {/* Error Display */}
      {mutationError && (
        <Alert severity="error" sx={{ mt: 1 }}>
          Failed to save: {mutationError.message}
        </Alert>
      )}

      {/* Success Display */}
      {mutationSuccess && (
        <Alert severity="success" sx={{ mt: 1 }}>
          Metadata saved successfully!
        </Alert>
      )}
    </Box>
  );
};

