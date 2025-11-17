import React from 'react';
import { Box, Typography, Alert, Button } from '@mui/material';
import { FormProvider } from 'react-hook-form';
import LoadingSkeleton from '../LoadingSkeleton';
import SchemaDrivenForm from '../SchemaDrivenForm';
import NavigationPanel from '../NavigationPanel';
import type { MetadataFile as ApiMetadataFile } from '../../types/api';

interface Section {
  id: string;
  title: string;
  fields: any[];
}

interface Analysis {
  sections: Section[];
}

interface EditorContentProps {
  selectedMetadataType: string | null;
  isLoading: boolean;
  error: Error | null;
  metadataFile: ApiMetadataFile | undefined;
  analysis: Analysis | null;
  fieldStatus: any;
  activeSection: string;
  onSectionClick: (sectionId: string) => void;
  onFieldClick: (sectionId: string, fieldId: string) => void;
  formMethods: any;
  onDataChange: (data: Record<string, any>) => void;
  isEditingProject: boolean;
}

export const EditorContent: React.FC<EditorContentProps> = ({
  selectedMetadataType,
  isLoading,
  error,
  metadataFile,
  analysis,
  fieldStatus,
  activeSection,
  onSectionClick,
  onFieldClick,
  formMethods,
  onDataChange,
  isEditingProject,
}) => {
  if (!selectedMetadataType) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
        flexDirection="column"
      >
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select a metadata type
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Choose a metadata type from the dropdown above
        </Typography>
        {isEditingProject ? (
          <Typography variant="body2" color="text.secondary">
            You can edit project-level metadata like project descriptions and administrative information.
          </Typography>
        ) : (
          <Typography variant="body2" color="text.secondary">
            You can edit dataset-level metadata like administrative details, structural information, and experiment context.
          </Typography>
        )}
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}>
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          <LoadingSkeleton variant="form" lines={4} />
        </Box>
        <Box
          sx={{
            width: 280,
            minWidth: 280,
            borderLeft: '1px solid var(--fair-border-light)',
            backgroundColor: 'var(--fair-surface)',
          }}
        >
          <LoadingSkeleton variant="navigation" />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={2}>
        <Alert severity="error">
          {error.message === 'Request failed with status code 404' && selectedMetadataType === 'experiment_contextual'
            ? 'No experiment contextual metadata found. Create a contextual template first.'
            : `Failed to load metadata: ${error.message}`
          }
        </Alert>
        {error.message === 'Request failed with status code 404' && selectedMetadataType === 'experiment_contextual' && (
          <Box mt={2}>
            <Button
              variant="contained"
              onClick={() => {
                console.log('Create contextual template');
              }}
            >
              Create Contextual Template
            </Button>
          </Box>
        )}
      </Box>
    );
  }

  if (!metadataFile) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
        flexDirection="column"
      >
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No metadata found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This dataset doesn't have {selectedMetadataType} metadata yet
        </Typography>
      </Box>
    );
  }

  if (!analysis) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
        flexDirection="column"
      >
        <Typography variant="h6" color="text.secondary">
          Loading form analysis...
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      className="metadata-editor-layout"
      sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}
    >
      <FormProvider {...formMethods}>
        {/* Main Content Area */}
        <Box
          className="form-content"
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Form with Sections */}
          <SchemaDrivenForm
            metadataFile={metadataFile}
            onDataChange={onDataChange}
            sections={analysis.sections}
            activeSection={activeSection}
            fieldStatus={fieldStatus}
          />
        </Box>

        {/* Navigation Panel - Right Side within MetadataEditor */}
        <Box
          className="navigation-panel"
          sx={{
            width: 280,
            minWidth: 280,
            borderLeft: 1,
            borderColor: 'divider',
            backgroundColor: 'background.paper',
            overflow: 'auto',
          }}
        >
          <NavigationPanel
            sections={analysis.sections}
            activeSection={activeSection}
            onSectionClick={onSectionClick}
            onFieldClick={onFieldClick}
          />
        </Box>
      </FormProvider>
    </Box>
  );
};
