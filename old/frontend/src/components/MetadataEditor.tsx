import React from 'react';
import { Box, Typography, Snackbar, Alert } from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, FormProvider } from 'react-hook-form';

import { APIService } from '../services/api';
import { useAppStore } from '../store/appStore';
import { EditorHeader } from './editor/EditorHeader';
import { EditorContent } from './editor/EditorContent';
import { FileUploadDialog } from './editor/FileUploadDialog';
import { analyzeFormData } from '../utils/formAnalyzer';
import { normalizeDataBySchema } from '../utils/schemaUtils';
import { useScrollSync } from '../hooks/useScrollSync';
import { useFieldStatus } from '../hooks/useFieldStatus';

const MetadataEditor: React.FC = () => {
  const { selectedProjectId, selectedDatasetId, selectedMetadataType, setSelectedMetadataType } = useAppStore();

  // Local state for editing context
  const [editingContext, setEditingContext] = React.useState<'project' | 'dataset'>('dataset');

  // Navigation state
  const [activeSection, setActiveSection] = React.useState<string>('');

  const queryClient = useQueryClient();

  // Toast notification state
  const [toast, setToast] = React.useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // File upload state
  const [uploading, setUploading] = React.useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploadComment, setUploadComment] = React.useState('');

  const showToast = (message: string, severity: 'success' | 'error') => {
    setToast({ open: true, message, severity });
  };

  const hideToast = () => {
    setToast(prev => ({ ...prev, open: false }));
  };

  // Available metadata types
  const metadataTypes: Array<{ value: string; label: string; level: 'project' | 'dataset' }> = [
    { value: 'project_descriptive', label: 'Project Descriptive', level: 'project' as const },
    { value: 'project_administrative', label: 'Project Administrative', level: 'project' as const },
    { value: 'dataset_administrative', label: 'Dataset Administrative', level: 'dataset' as const },
    { value: 'dataset_structural', label: 'Dataset Structural', level: 'dataset' as const },
    { value: 'experiment_contextual', label: 'Experiment Contextual', level: 'dataset' as const },
  ];

  // Determine entity ID based on editing context
  const entityId = editingContext === 'project' ? selectedProjectId : selectedDatasetId;

  // Determine if current metadata type matches the editing context
  const currentMetadataType = metadataTypes.find(type => type.value === selectedMetadataType);

  // Determine editing context for UI
  const isEditingProject = editingContext === 'project';

  // Filter available metadata types based on current editing context
  const availableMetadataTypes = isEditingProject
    ? metadataTypes.filter(type => type.level === 'project')
    : metadataTypes.filter(type => type.level === 'dataset');

  // Update editing context when selection changes
  React.useEffect(() => {
    if (selectedDatasetId && !selectedProjectId) {
      setEditingContext('dataset');
    } else if (selectedProjectId && !selectedDatasetId) {
      setEditingContext('project');
    } else if (selectedProjectId && selectedDatasetId) {
      if (editingContext === 'dataset' || editingContext === 'project') {
        // Keep current context
      } else {
        setEditingContext('dataset');
      }
    }
  }, [selectedProjectId, selectedDatasetId, editingContext]);

  // Clear invalid metadata type selection when context changes
  React.useEffect(() => {
    if (selectedMetadataType && currentMetadataType) {
      const isValidSelection = isEditingProject
        ? currentMetadataType.level === 'project'
        : currentMetadataType.level === 'dataset';

      if (!isValidSelection) {
        setSelectedMetadataType(null);
      }
    }
  }, [isEditingProject, selectedMetadataType, currentMetadataType, setSelectedMetadataType]);

  // Fetch metadata when entity and type are selected
  const {
    data: metadataFile,
    isLoading,
    error,
    refetch: refetchMetadata,
  } = useQuery({
    queryKey: ['metadata', editingContext, entityId, selectedMetadataType],
    queryFn: () => {
      if (!entityId || !selectedMetadataType) {
        return Promise.reject(new Error('No entity or metadata type selected'));
      }

      if (editingContext === 'project') {
        if (selectedMetadataType === 'project_descriptive' || selectedMetadataType === 'project_administrative') {
          return APIService.getProjectMetadata(entityId, selectedMetadataType);
        } else {
          throw new Error(`Invalid metadata type '${selectedMetadataType}' for project context`);
        }
      } else {
        if (selectedMetadataType !== 'project_descriptive' && selectedMetadataType !== 'project_administrative') {
          return APIService.getMetadata(entityId, selectedMetadataType);
        } else {
          throw new Error(`Invalid metadata type '${selectedMetadataType}' for dataset context`);
        }
      }
    },
    enabled: !!entityId && !!selectedMetadataType && !!editingContext,
  });

  // Initialize form
  const methods = useForm({
    defaultValues: metadataFile?.content || {},
  });

  // Clean invalid enum values from metadata content
  const cleanInvalidEnumValues = (content: Record<string, any>, schema: Record<string, any>): Record<string, any> => {
    if (!schema || !schema.properties) return content;

    const cleaned = { ...content };
    Object.entries(schema.properties).forEach(([fieldName, fieldSchema]: [string, any]) => {
      if (fieldSchema.enum && Array.isArray(fieldSchema.enum)) {
        const value = cleaned[fieldName];
        if (value && !fieldSchema.enum.includes(value)) {
          cleaned[fieldName] = '';
        }
      }
    });
    return cleaned;
  };

  // Update form when metadata changes
  React.useEffect(() => {
    if (metadataFile?.content && metadataFile?.schema_definition) {
      const cleanedContent = cleanInvalidEnumValues(metadataFile.content, metadataFile.schema_definition);
      methods.reset(cleanedContent);
    }
  }, [metadataFile, methods]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: Record<string, any>) => {
      if (!entityId || !selectedMetadataType) {
        return Promise.reject(new Error('No entity or metadata type selected'));
      }

      const normalized = normalizeDataBySchema(metadataFile?.schema_definition as any, data);
      if (editingContext === 'project') {
        return APIService.updateProjectMetadata(entityId, selectedMetadataType, { content: normalized });
      } else {
        return APIService.updateMetadata(entityId, selectedMetadataType, { content: normalized });
      }
    },
    onSuccess: async () => {
      queryClient.invalidateQueries({
        queryKey: ['metadata', editingContext, entityId, selectedMetadataType],
      });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      await refetchMetadata();
      showToast('Metadata saved successfully!', 'success');
    },
    onError: (error) => {
      showToast(`Failed to save: ${(error as Error).message}`, 'error');
    },
  });

  const handleSave = methods.handleSubmit((data) => {
    updateMutation.mutate(data);
  }, (errors) => {
    console.log('Form validation errors:', errors);
  });

  const handleReset = () => {
    if (metadataFile?.content) {
      methods.reset(metadataFile.content);
      showToast('Form reset to original values', 'success');
    }
  };

  const handleDataChange = (_data: Record<string, any>) => {
    // Data change is handled by the form
  };

  // Get form analysis for scroll sync
  const formData = methods.watch();
  const formErrors = methods.formState.errors;
  const analysis = React.useMemo(() => {
    return metadataFile ? analyzeFormData(metadataFile, formData, formErrors) : null;
  }, [metadataFile, formData, formErrors]);

  // Field status tracking
  const fieldStatus = useFieldStatus({
    formMethods: methods,
    originalData: metadataFile?.content || {},
    requiredFields: metadataFile?.schema_definition?.required || [],
    systemFields: [
      'created_by', 'created_date', 'last_modified_by', 'last_modified_date',
      'project_identifier', 'dataset_identifier', 'associated_project_identifier',
      'dataset_identifier_link', 'experiment_identifier_run_id', 'experiment_template_type'
    ]
  });

  // Scroll synchronization
  const { scrollToSection, scrollToField } = useScrollSync({
    sections: analysis?.sections || [],
    activeSection,
    onActiveSectionChange: setActiveSection,
    threshold: 0.3,
    rootMargin: '-10% 0px -10% 0px'
  });

  // Navigation handlers
  const handleSectionClick = (sectionId: string) => {
    scrollToSection(sectionId);
  };

  const handleFieldClick = (sectionId: string, fieldId: string) => {
    scrollToField(fieldId, sectionId);
  };

  // Set active section to first section when metadata loads
  React.useEffect(() => {
    if (analysis && !activeSection && analysis.sections.length > 0) {
      setActiveSection(analysis.sections[0].id);
    }
  }, [analysis, activeSection]);

  const handleRefresh = () => {
    if (entityId && selectedMetadataType) {
      refetchMetadata();
      showToast('Metadata refreshed successfully!', 'success');
    }
  };

  const handleContextChange = (context: 'project' | 'dataset') => {
    setEditingContext(context);

    if (context === 'project' && selectedProjectId) {
      setSelectedMetadataType('project_descriptive');
    } else if (context === 'dataset' && selectedDatasetId) {
      setSelectedMetadataType(null);
    }
  };

  const handleMetadataTypeChange = (type: string) => {
    setSelectedMetadataType(type);
  };

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: ({ file, comment }: { file: File; comment?: string }) => {
      if (!selectedDatasetId) {
        return Promise.reject(new Error('No dataset selected'));
      }
      return APIService.uploadFile(selectedDatasetId, file, comment);
    },
    onSuccess: (data) => {
      showToast(`File "${data.filename}" uploaded successfully!`, 'success');
      setUploading(false);
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setUploadComment('');

      queryClient.invalidateQueries({
        queryKey: ['metadata', editingContext, entityId, selectedMetadataType],
      });

      if (selectedMetadataType === 'dataset_structural') {
        refetchMetadata();
      }
    },
    onError: (error) => {
      showToast(`Failed to upload file: ${(error as Error).message}`, 'error');
      setUploading(false);
    },
  });

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadDialogOpen(true);
  };

  const handleUploadClick = () => {
    setUploadDialogOpen(true);
  };

  const handleUploadConfirm = (file: File, comment: string) => {
    setUploading(true);
    uploadMutation.mutate({ file, comment: comment || undefined });
  };

  const handleUploadCancel = () => {
    setUploadDialogOpen(false);
    setSelectedFile(null);
    setUploadComment('');
  };

  if (!selectedDatasetId) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
        flexDirection="column"
      >
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select a dataset to edit metadata
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Choose a project and dataset from the browser on the left
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <FormProvider {...methods}>
        <EditorHeader
          entityId={entityId}
          isEditingProject={isEditingProject}
          selectedMetadataType={selectedMetadataType}
          availableMetadataTypes={availableMetadataTypes}
          editingContext={editingContext}
          onContextChange={handleContextChange}
          onMetadataTypeChange={handleMetadataTypeChange}
          onSave={handleSave}
          onReset={handleReset}
          onRefresh={handleRefresh}
          onUploadClick={handleUploadClick}
          isSaving={updateMutation.isPending}
          isUploading={uploading}
          hasSelectedDataset={!!selectedDatasetId}
          hasMetadataTypeSelected={!!selectedMetadataType}
          mutationError={updateMutation.error as Error | null}
          mutationSuccess={updateMutation.isSuccess}
        />

        <EditorContent
          selectedMetadataType={selectedMetadataType}
          isLoading={isLoading}
          error={error as Error | null}
          metadataFile={metadataFile}
          analysis={analysis}
          fieldStatus={fieldStatus}
          activeSection={activeSection}
          onSectionClick={handleSectionClick}
          onFieldClick={handleFieldClick}
          formMethods={methods}
          onDataChange={handleDataChange}
          isEditingProject={isEditingProject}
        />
      </FormProvider>

      {/* Toast Notifications */}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={hideToast}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={hideToast} severity={toast.severity} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>

      {/* File Upload Dialog */}
      <FileUploadDialog
        open={uploadDialogOpen}
        selectedFile={selectedFile}
        uploadComment={uploadComment}
        uploading={uploading}
        onClose={handleUploadCancel}
        onUpload={handleUploadConfirm}
        onFileChange={handleFileSelect}
        onCommentChange={setUploadComment}
      />
    </Box>
  );
};

export default MetadataEditor;
