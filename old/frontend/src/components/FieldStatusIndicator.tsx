import React from 'react';
import { Box, Tooltip, Chip } from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Edit,
  Lock,
  RadioButtonUnchecked
} from '@mui/icons-material';
import type { FieldStatus } from '../hooks/useFieldStatus';

interface FieldStatusIndicatorProps {
  status?: FieldStatus;
  variant?: 'icon' | 'chip' | 'badge';
  size?: 'small' | 'medium';
  showTooltip?: boolean;
}

const FieldStatusIndicator: React.FC<FieldStatusIndicatorProps> = ({
  status,
  variant = 'icon',
  size = 'small',
  showTooltip = true
}) => {
  // Return null if no status provided
  if (!status) {
    return null;
  }

  // Determine the primary status and styling
  const getPrimaryStatus = () => {
    if (status.isSystemField) {
      return {
        type: 'system',
        icon: <Lock sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
        color: 'var(--fair-text-secondary)',
        bgColor: 'var(--fair-border-light)',
        label: 'System Field',
        tooltip: 'This field is automatically managed by the system'
      };
    }

    if (status.hasError) {
      return {
        type: 'error',
        icon: <Error sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
        color: 'var(--fair-error)',
        bgColor: 'var(--fair-error-bg)',
        label: 'Error',
        tooltip: status.errorMessage || 'This field has validation errors'
      };
    }

    if (status.isCompleted) {
      return {
        type: 'completed',
        icon: <CheckCircle sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
        color: 'var(--fair-success)',
        bgColor: 'var(--fair-success-bg)',
        label: 'Completed',
        tooltip: 'This field is completed'
      };
    }

    if (status.isRequired && status.isEmpty) {
      return {
        type: 'required',
        icon: <Warning sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
        color: 'var(--fair-warning)',
        bgColor: 'var(--fair-warning-bg)',
        label: 'Required',
        tooltip: 'This field is required and must be filled'
      };
    }

    if (status.isModified) {
      return {
        type: 'modified',
        icon: <Edit sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
        color: 'var(--fair-info)',
        bgColor: 'var(--fair-info-bg)',
        label: 'Modified',
        tooltip: 'This field has been modified'
      };
    }

    return {
      type: 'empty',
      icon: <RadioButtonUnchecked sx={{ fontSize: size === 'small' ? 14 : 16, margin: 0, padding: 0, display: 'block' }} />,
      color: 'var(--fair-text-secondary)',
      bgColor: 'transparent',
      label: 'Empty',
      tooltip: 'This field is empty'
    };
  };

  const primaryStatus = getPrimaryStatus();

  // Render based on variant
  const renderIndicator = () => {
    switch (variant) {
      case 'chip':
        return (
          <Chip
            icon={primaryStatus.icon}
            label={primaryStatus.label}
            size={size}
            sx={{
              backgroundColor: primaryStatus.bgColor,
              color: primaryStatus.color,
              border: `1px solid ${primaryStatus.color}`,
              fontSize: size === 'small' ? '0.75rem' : '0.875rem',
              height: size === 'small' ? 20 : 24,
              '& .MuiChip-icon': {
                color: primaryStatus.color,
              },
            }}
          />
        );

      case 'badge':
        return (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              px: 1,
              py: 0.25,
              borderRadius: 'var(--fair-radius-sm)',
              backgroundColor: primaryStatus.bgColor,
              color: primaryStatus.color,
              fontSize: size === 'small' ? '0.75rem' : '0.875rem',
              fontWeight: 500,
              border: `1px solid ${primaryStatus.color}`,
            }}
          >
            {primaryStatus.icon}
            {primaryStatus.label}
          </Box>
        );

      case 'icon':
      default:
        return (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: size === 'small' ? 20 : 24,
              height: size === 'small' ? 20 : 24,
              borderRadius: '50%',
              backgroundColor: primaryStatus.bgColor,
              color: primaryStatus.color,
              border: primaryStatus.type !== 'empty' ? `1px solid ${primaryStatus.color}` : 'none',
              position: 'relative',
              '& .MuiSvgIcon-root': {
                margin: 0,
                padding: 0,
                display: 'block',
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
              },
            }}
          >
            {primaryStatus.icon}
          </Box>
        );
    }
  };

  const indicator = renderIndicator();

  if (showTooltip) {
    return (
      <Tooltip title={primaryStatus.tooltip} arrow placement="top">
        {indicator}
      </Tooltip>
    );
  }

  return indicator;
};

export default FieldStatusIndicator;