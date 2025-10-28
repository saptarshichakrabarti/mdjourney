import React from 'react';
import { Box, Typography, LinearProgress, Chip } from '@mui/material';
import { CheckCircle, Error } from '@mui/icons-material';

interface ProgressTrackerProps {
  totalFields: number;
  completedFields: number;
  requiredFields: number;
  completedRequiredFields: number;
  errorFields: number;
  title?: string;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  totalFields,
  completedFields,
  requiredFields,
  completedRequiredFields,
  errorFields,
  title = "Form Progress"
}) => {
  const overallProgress = totalFields > 0 ? (completedFields / totalFields) * 100 : 0;
  const requiredProgress = requiredFields > 0 ? (completedRequiredFields / requiredFields) * 100 : 100;

  const getProgressColor = () => {
    if (errorFields > 0) return 'error.main';
    if (requiredProgress === 100) return 'success.main';
    if (requiredProgress > 50) return 'primary.main';
    return 'warning.main';
  };

  const getStatusMessage = () => {
    if (errorFields > 0) return `${errorFields} field${errorFields > 1 ? 's' : ''} have errors`;
    if (requiredProgress === 100) return 'All required fields completed';
    const remaining = requiredFields - completedRequiredFields;
    return `${remaining} required field${remaining > 1 ? 's' : ''} remaining`;
  };

  return (
    <Box
      sx={{
        backgroundColor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 2,
        mb: 2,
        boxShadow: 0,
      }}
    >
      <Typography variant="h6" sx={{ mb: 2, color: 'text.primary', fontWeight: 600 }}>
        {title}
      </Typography>

      {/* Overall Progress */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Overall Progress
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500, color: getProgressColor() }}>
            {Math.round(overallProgress)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={overallProgress}
          sx={{
            height: 8,
            borderRadius: 4,
            backgroundColor: 'divider',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getProgressColor(),
              borderRadius: 4,
            },
          }}
        />
      </Box>

      {/* Required Fields Progress */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Required Fields
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500, color: getProgressColor() }}>
            {completedRequiredFields}/{requiredFields}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={requiredProgress}
          sx={{
            height: 6,
            borderRadius: 3,
            backgroundColor: 'divider',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getProgressColor(),
              borderRadius: 3,
            },
          }}
        />
      </Box>

      {/* Status Indicators */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        <Chip
          icon={<CheckCircle sx={{ fontSize: 16 }} />}
          label={`${completedFields} Completed`}
          size="small"
          sx={{
            backgroundColor: 'success.main',
            color: 'success.contrastText',
            '& .MuiChip-icon': {
              color: 'success.contrastText',
            },
          }}
        />

        {requiredFields > 0 && (
          <Chip
            label={`${requiredFields} Required`}
            size="small"
            sx={{
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
            }}
          />
        )}

        {errorFields > 0 && (
          <Chip
            icon={<Error sx={{ fontSize: 16 }} />}
            label={`${errorFields} Error${errorFields > 1 ? 's' : ''}`}
            size="small"
            sx={{
              backgroundColor: 'error.main',
              color: 'error.contrastText',
              '& .MuiChip-icon': {
                color: 'error.contrastText',
              },
            }}
          />
        )}
      </Box>

      {/* Status Message */}
      <Typography
        variant="body2"
        sx={{
          color: getProgressColor(),
          fontWeight: 500,
          textAlign: 'center',
        }}
      >
        {getStatusMessage()}
      </Typography>
    </Box>
  );
};

export default ProgressTracker;