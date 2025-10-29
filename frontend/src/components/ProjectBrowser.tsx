import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  Folder,
  Storage,
  CheckCircle,
  Pending,
  Refresh,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

import { APIService } from '../services/api';
import { useAppStore } from '../store/appStore';
import type { ProjectSummary, DatasetSummary } from '../types/api';

const ProjectBrowser: React.FC = () => {
  const { selectedProjectId, selectedDatasetId, setSelectedProject, setSelectedDataset } =
    useAppStore();

  // const queryClient = useQueryClient();

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

  const showToast = (message: string, severity: 'success' | 'error') => {
    setToast({ open: true, message, severity });
  };

  const hideToast = () => {
    setToast(prev => ({ ...prev, open: false }));
  };

  // Fetch projects
  const {
    data: projects,
    isLoading: projectsLoading,
    error: projectsError,
    refetch: refetchProjects,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: APIService.getProjects,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Fetch datasets for selected project
  const {
    data: datasets,
    isLoading: datasetsLoading,
    refetch: refetchDatasets,
  } = useQuery({
    queryKey: ['project-datasets', selectedProjectId],
    queryFn: () => selectedProjectId ? APIService.getProjectDatasets(selectedProjectId) : Promise.resolve([]),
    enabled: !!selectedProjectId,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const handleProjectSelect = (projectId: string) => {
    setSelectedProject(projectId);
    setSelectedDataset(null);
  };

  const handleDatasetSelect = (datasetId: string) => {
    setSelectedDataset(datasetId);
  };

  const handleRefresh = async () => {
    try {
      // First trigger a backend rescan
      await APIService.rescanProjects();
      // Then refetch the frontend data
      refetchProjects();
      if (selectedProjectId) {
        refetchDatasets();
      }
      showToast('Projects and datasets refreshed successfully!', 'success');
    } catch (error) {
      console.error('Failed to rescan projects:', error);
      showToast('Failed to refresh projects and datasets', 'error');
      // Still try to refetch even if rescan fails
      refetchProjects();
      if (selectedProjectId) {
        refetchDatasets();
      }
    }
  };

  const getStatusIcon = (metadata_status: string) => {
    switch (metadata_status) {
      case 'V2_Finalized':
        return <CheckCircle color="success" fontSize="small" />;
      case 'V1_Ingested':
        return <Pending color="warning" fontSize="small" />;
      default:
        return <Storage fontSize="small" />;
    }
  };

  const formatMetadataStatus = (metadata_status: DatasetSummary['metadata_status']) => {
    if (!metadata_status) return '';
    const [version, rawLabel] = metadata_status.split('_');
    const label = (rawLabel || '').toLowerCase();
    const titleCased = label.charAt(0).toUpperCase() + label.slice(1);
    const overrides: Record<string, string> = { Finalized: 'Finalised' };
    const displayLabel = overrides[titleCased] || titleCased;
    return `${version}: ${displayLabel}`;
  };

  if (projectsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  if (projectsError) {
    return (
      <Box p={2}>
        <Alert severity="error">
          Failed to load projects: {(projectsError as Error).message}
        </Alert>
      </Box>
    );
  }

    return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          Project Browser
        </Typography>
        <Tooltip title="Refresh projects and datasets">
          <IconButton onClick={handleRefresh} size="small">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      <List sx={{ p: 0 }}>
        {projects?.map((project: ProjectSummary) => (
          <ListItem key={project.project_id} sx={{ p: 0 }}>
            <ListItemButton
              selected={selectedProjectId === project.project_id}
              onClick={() => handleProjectSelect(project.project_id)}
              sx={{ pl: 2 }}
            >
              <ListItemIcon>
                <Folder color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={project.project_title}
                secondary={`${project.folder_count} folders, ${project.dataset_count} datasets`}
              />
            </ListItemButton>

            {selectedProjectId === project.project_id && (
              <Collapse in={true} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {datasetsLoading ? (
                    <Box display="flex" justifyContent="center" p={1}>
                      <CircularProgress size={20} />
                    </Box>
                  ) : (
                    datasets?.map((dataset: DatasetSummary) => (
                      <Box key={dataset.dataset_id} sx={{ pl: 4 }}>
                        <ListItemButton
                          selected={selectedDatasetId === dataset.dataset_id}
                          onClick={() => handleDatasetSelect(dataset.dataset_id)}
                        >
                          <ListItemIcon>
                            {getStatusIcon(dataset.metadata_status)}
                          </ListItemIcon>
                          <ListItemText
                            primary={dataset.dataset_title || dataset.dataset_id.replace('d_', '')}
                            secondary={formatMetadataStatus(dataset.metadata_status)}
                          />
                        </ListItemButton>
                      </Box>
                    ))
                  )}
                </List>
              </Collapse>
            )}
          </ListItem>
        ))}
      </List>

      {/* Toast Notifications */}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={hideToast}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          onClose={hideToast}
          severity={toast.severity}
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProjectBrowser;