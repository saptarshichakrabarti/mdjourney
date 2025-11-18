import React from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  CircularProgress,
} from '@mui/material';
import { PlayArrow as PlayIcon, CheckCircle as CheckIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { APIService } from '../services/api';
import { useAppStore } from '../store/appStore';
import { getFieldDescription, getFieldTitle } from '../utils/schemaUtils';
import ProgressTracker from './ProgressTracker';


const ContextPanel: React.FC = () => {
  const {
    focusedField,
    selectedDatasetId,
    selectedMetadataType,
  } = useAppStore();

  // Don't use form context in this component - it's not always in a form
  const errors: Record<string, any> = {};
  const queryClient = useQueryClient();
  const [finalizing, setFinalizing] = React.useState(false);
  const [finalizeBanner, setFinalizeBanner] = React.useState<null | { type: 'success' | 'error'; message: string }>(null);

  // Fetch contextual schemas for template creation
  const {
    data: contextualSchemas,
    isLoading: schemasLoading,
  } = useQuery({
    queryKey: ['contextual-schemas'],
    queryFn: APIService.getContextualSchemas,
  });

  // Fetch current metadata for context
  const {
    data: currentMetadata,
  } = useQuery({
    queryKey: ['metadata', 'dataset', selectedDatasetId, selectedMetadataType],
    queryFn: () =>
      selectedDatasetId && selectedMetadataType
        ? APIService.getMetadata(selectedDatasetId, selectedMetadataType)
        : Promise.reject(new Error('No dataset or metadata type selected')),
    enabled: !!selectedDatasetId && !!selectedMetadataType,
  });

  // Derive lightweight progress info if available
  const totalFields = React.useMemo(() => {
    const props = currentMetadata?.schema_definition?.properties || {};
    return Object.keys(props).length || 0;
  }, [currentMetadata]);
  const requiredFields = currentMetadata?.schema_definition?.required || [];
  const completedRequiredFields = React.useMemo(() => {
    const content = currentMetadata?.content || {};
    return requiredFields.filter((f: string) => {
      const v = (content as any)[f];
      if (v === null || v === undefined) return false;
      if (typeof v === 'string') return v.trim() !== '' && v !== 'To be filled';
      if (Array.isArray(v)) return v.length > 0;
      if (typeof v === 'object') return Object.keys(v).length > 0;
      return true;
    }).length;
  }, [currentMetadata, requiredFields]);
  const completedFields = completedRequiredFields; // simple proxy
  const errorFieldsCount = 0;

  // Create contextual template mutation
  const createTemplateMutation = useMutation({
    mutationFn: (schemaId?: string) =>
      selectedDatasetId
        ? APIService.createContextualTemplate(selectedDatasetId, { schema_id: schemaId })
        : Promise.reject(new Error('No dataset selected')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      // Invalidate the specific metadata query for experiment_contextual
      queryClient.invalidateQueries({
        queryKey: ['metadata', 'dataset', selectedDatasetId, 'experiment_contextual']
      });
      // Also invalidate any other metadata queries for this dataset to be safe
      queryClient.invalidateQueries({
        queryKey: ['metadata', 'dataset', selectedDatasetId]
      });
      // Refetch the specific query immediately for snappier UI
      queryClient.refetchQueries({
        queryKey: ['metadata', 'dataset', selectedDatasetId, 'experiment_contextual']
      });
    },
  });

  // Finalize dataset mutation
  const finalizeMutation = useMutation({
    mutationFn: (experimentId: string) =>
      selectedDatasetId
        ? APIService.finalizeDataset(selectedDatasetId, { experiment_id: experimentId })
        : Promise.reject(new Error('No dataset selected')),
  });

  const handleCreateTemplate = (schemaId: string) => {
    createTemplateMutation.mutate(schemaId);
  };

  const handleCreateDefaultTemplate = () => {
    createTemplateMutation.mutate(undefined);
  };

  const handleFinalize = () => {
    if (!currentMetadata?.content?.experiment_identifier_run_id) return;
    setFinalizing(true);
    setFinalizeBanner(null);
    const expId = currentMetadata.content.experiment_identifier_run_id as string;
    finalizeMutation.mutate(expId, {
      onSuccess: () => {
        setFinalizeBanner({ type: 'success', message: 'Dataset finalized successfully.' });
        queryClient.invalidateQueries({ queryKey: ['projects'] });
        queryClient.invalidateQueries({ queryKey: ['metadata', 'dataset', selectedDatasetId, 'experiment_contextual'] });
      },
      onError: (err: any) => {
        const detail = err?.response?.data?.detail || err?.message || 'Failed to finalize dataset';
        setFinalizeBanner({ type: 'error', message: detail });
      },
      onSettled: () => {
        setFinalizing(false);
      },
    });
  };

  const getFieldHelp = () => {
    if (!focusedField || !currentMetadata) return null;

    const description = getFieldDescription(currentMetadata.schema_definition, focusedField);
    const title = getFieldTitle(currentMetadata.schema_definition, focusedField);

    return (
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          {title || focusedField}
        </Typography>
        {description && (
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        )}
      </Box>
    );
  };

  const getValidationErrors = () => {
    const errorEntries = Object.entries(errors);
    if (errorEntries.length === 0) return null;

    return (
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Validation Errors
        </Typography>
        <List dense>
          {errorEntries.map(([field, error]) => (
            <ListItem key={field} sx={{ py: 0 }}>
              <ListItemText
                primary={field}
                secondary={(error?.message as string) || 'Invalid value'}
                primaryTypographyProps={{ variant: 'caption', fontWeight: 'bold' }}
                secondaryTypographyProps={{ variant: 'caption', color: 'error.main' }}
              />
            </ListItem>
          ))}
        </List>
      </Box>
    );
  };

  const canCreateContextual = () => {
    return selectedDatasetId && contextualSchemas && contextualSchemas.length > 0;
  };

  const canFinalize = () => {
    return (
      selectedDatasetId &&
      selectedMetadataType === 'experiment_contextual' &&
      currentMetadata?.content?.experiment_identifier_run_id
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        Context & Validation
      </Typography>

      <Box sx={{ flexGrow: 1, p: 2, display: 'flex', flexDirection: 'column', gap: 2, minHeight: 0 }}>
        {/* Top: Context & Validation (half height) */}
        <Box sx={{ flex: '1 1 50%', overflow: 'auto' }}>
        {/* Field Help */}
        {focusedField && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Field Help
            </Typography>
            {getFieldHelp()}
          </Box>
        )}

        {/* Validation Errors */}
        {Object.keys(errors).length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Divider sx={{ mb: 1 }} />
            {getValidationErrors()}
          </Box>
        )}

        {/* Contextual Template Creation */}
        {canCreateContextual() && (
          <Box sx={{ mt: 1 }}>
            <Divider sx={{ mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Create Contextual Template
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select an experiment type to create contextual metadata:
            </Typography>

            {schemasLoading ? (
              <CircularProgress size={20} />
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {contextualSchemas?.map((schema) => (
                  <Button
                    key={schema.schema_id}
                    variant="outlined"
                    size="small"
                    startIcon={<PlayIcon />}
                    onClick={() => handleCreateTemplate(schema.schema_id)}
                    disabled={createTemplateMutation.isPending}
                    sx={{
                      justifyContent: 'flex-start',
                      color: 'primary.main',
                      borderColor: 'primary.main',
                      '&:hover': {
                        backgroundColor: 'primary.main',
                        color: 'primary.contrastText',
                        borderColor: 'primary.main',
                        '& .MuiChip-root': {
                          color: 'primary.contrastText',
                          borderColor: 'primary.contrastText',
                        }
                      },
                      '&:disabled': {
                        color: 'text.disabled',
                        borderColor: 'text.disabled',
                      }
                    }}
                  >
                    {schema.schema_title}
                    <Chip
                      label={schema.source}
                      size="small"
                      variant="outlined"
                      sx={{
                        ml: 'auto',
                        color: 'inherit',
                        borderColor: 'inherit',
                      }}
                    />
                  </Button>
                ))}

                {/* Default Schema Button */}
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<PlayIcon />}
                  onClick={handleCreateDefaultTemplate}
                  disabled={createTemplateMutation.isPending}
                  sx={{
                    justifyContent: 'flex-start',
                    color: 'secondary.main',
                    borderColor: 'secondary.main',
                    mt: 1,
                    '&:hover': {
                      backgroundColor: 'secondary.main',
                      color: 'secondary.contrastText',
                      borderColor: 'secondary.main',
                    },
                    '&:disabled': {
                      color: 'text.disabled',
                      borderColor: 'text.disabled',
                    }
                  }}
                >
                  System Default Template
                  <Chip
                    label="default"
                    size="small"
                    variant="outlined"
                    sx={{
                      ml: 'auto',
                      color: 'inherit',
                      borderColor: 'inherit',
                    }}
                  />
                </Button>
              </Box>
            )}

            {createTemplateMutation.error && (
              <Alert severity="error" sx={{ mt: 1 }}>
                Failed to create template: {(createTemplateMutation.error as Error).message}
              </Alert>
            )}

            {createTemplateMutation.isSuccess && (
              <Alert severity="success" sx={{ mt: 1 }}>
                Contextual template created successfully!
              </Alert>
            )}
          </Box>
        )}
        </Box>

        {/* Bottom: Progress Tracker panel */}
        {currentMetadata && (
          <Box sx={{ flex: '0 0 auto', mt: 'auto', pt: 1, borderTop: 1, borderColor: 'divider' }}>
            <Typography variant="subtitle2" gutterBottom>
              Progress
            </Typography>
            <ProgressTracker
              totalFields={totalFields}
              completedFields={completedFields}
              requiredFields={requiredFields.length}
              completedRequiredFields={completedRequiredFields}
              errorFields={errorFieldsCount}
              title={`${currentMetadata.schema_info?.schema_title || 'Form'} Progress`}
            />
          </Box>
        )}

        {/* Dataset Finalization */}
        {canFinalize() && (
          <Box sx={{ mt: 1 }}>
            <Divider sx={{ mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Finalize Dataset
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Generate V2 complete metadata when contextual metadata is ready:
            </Typography>

            <Button
              variant="contained"
              color="success"
              startIcon={<CheckIcon />}
              onClick={handleFinalize}
              disabled={finalizing}
              fullWidth
              sx={{
                backgroundColor: 'success.main',
                color: 'success.contrastText',
                '&:hover': {
                  backgroundColor: 'success.dark',
                  color: 'success.contrastText',
                },
                '&:disabled': {
                  backgroundColor: 'action.disabledBackground',
                  color: 'action.disabled',
                }
              }}
            >
              {finalizing ? 'Finalizing...' : 'Finalize Dataset'}
            </Button>

            {finalizeBanner && (
              <Alert severity={finalizeBanner.type} sx={{ mt: 1 }}>
                {finalizeBanner.message}
              </Alert>
            )}
          </Box>
        )}

        {/* No Context */}
        {!focusedField && Object.keys(errors).length === 0 && !canCreateContextual() && !canFinalize() && (
          <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
            <Typography variant="body2">
              Select a field or dataset to see context information
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ContextPanel;