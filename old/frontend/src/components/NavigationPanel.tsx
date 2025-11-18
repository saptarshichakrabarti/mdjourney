import React from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemText, LinearProgress } from '@mui/material';
import { CheckCircle, Warning, Error, RadioButtonUnchecked } from '@mui/icons-material';

interface NavigationPanelProps {
  sections: Array<{
    id: string;
    title: string;
    fields: Array<{
      id: string;
      title: string;
      required: boolean;
      completed: boolean;
      hasError: boolean;
      isEmpty: boolean;
    }>;
  }>;
  activeSection?: string;
  onSectionClick: (sectionId: string) => void;
  onFieldClick: (sectionId: string, fieldId: string) => void;
}

const NavigationPanel: React.FC<NavigationPanelProps> = ({
  sections,
  activeSection,
  onSectionClick,
  onFieldClick,
}) => {
  const getFieldStatusIcon = (field: NavigationPanelProps['sections'][0]['fields'][0]) => {
    if (field.hasError) {
      return <Error sx={{ fontSize: 16, color: 'error.main' }} />;
    }
    if (field.completed) {
      return <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />;
    }
    if (field.required && field.isEmpty) {
      return <Warning sx={{ fontSize: 16, color: 'warning.main' }} />;
    }
    return <RadioButtonUnchecked sx={{ fontSize: 16, color: 'text.secondary' }} />;
  };

  const getSectionProgress = (section: NavigationPanelProps['sections'][0]) => {
    const totalFields = section.fields.length;
    const completedFields = section.fields.filter(f => f.completed).length;
    return totalFields > 0 ? (completedFields / totalFields) * 100 : 0;
  };

  const getSectionStatusColor = (section: NavigationPanelProps['sections'][0]) => {
    const hasErrors = section.fields.some(f => f.hasError);
    const hasRequiredEmpty = section.fields.some(f => f.required && f.isEmpty);
    const isComplete = section.fields.every(f => f.completed || !f.required);

    if (hasErrors) return 'error.main';
    if (hasRequiredEmpty) return 'warning.main';
    if (isComplete) return 'success.main';
    return 'primary.main';
  };

  return (
    <Box
      component="nav"
      role="navigation"
      aria-label="Form section navigation"
      sx={{
        height: '100%',
        width: '100%',
        backgroundColor: 'background.paper',
        overflow: 'auto',
      }}
    >
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ color: 'text.primary', fontWeight: 600, flexGrow: 1 }}>
            Form Navigation
          </Typography>
          <Box sx={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: 'success.main',
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': {
                opacity: 1,
                transform: 'scale(1)',
              },
              '50%': {
                opacity: 0.5,
                transform: 'scale(1.1)',
              },
              '100%': {
                opacity: 1,
                transform: 'scale(1)',
              },
            },
          }} />
        </Box>

        {sections.map((section) => {
          const progress = getSectionProgress(section);
          const statusColor = getSectionStatusColor(section);
          const isActive = activeSection === section.id;

          return (
            <Box key={section.id} sx={{ mb: 3 }}>
              {/* Section Header */}
              <ListItemButton
                onClick={() => onSectionClick(section.id)}
                aria-current={isActive ? 'true' : 'false'}
                aria-label={`Navigate to ${section.title} section, ${Math.round(progress)}% complete`}
                sx={{
                  borderRadius: 1,
                  mb: 1,
                  backgroundColor: isActive ? 'primary.main' : 'transparent',
                  color: isActive ? 'primary.contrastText' : 'text.primary',
                  transition: 'all 0.3s ease',
                  transform: isActive ? 'translateX(4px)' : 'translateX(0px)',
                  boxShadow: isActive ? 1 : 'none',
                  '&:hover': {
                    backgroundColor: isActive ? 'primary.dark' : 'action.hover',
                    transform: 'translateX(4px)',
                  },
                  '&:focus-visible': {
                    outline: '2px solid',
                    outlineColor: 'secondary.main',
                    outlineOffset: '2px',
                  },
                }}
              >
                <ListItemText
                  primary={section.title}
                  primaryTypographyProps={{
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '1rem',
                  }}
                />
              </ListItemButton>

              {/* Progress Bar */}
              <Box sx={{ px: 2, mb: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={progress}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'divider',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: statusColor,
                      borderRadius: 3,
                    },
                  }}
                />
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    textAlign: 'right',
                    mt: 0.5,
                    color: 'text.secondary',
                    fontSize: '0.75rem',
                  }}
                >
                  {Math.round(progress)}% complete
                </Typography>
              </Box>

              {/* Field List */}
              {isActive && (
                <List dense sx={{ pl: 2 }}>
                  {section.fields.map((field) => (
                    <ListItem key={field.id} disablePadding>
                      <ListItemButton
                        onClick={() => onFieldClick(section.id, field.id)}
                        aria-label={`Navigate to ${field.title} field${field.required ? ' (required)' : ''}${field.hasError ? ' (has error)' : ''}${field.completed ? ' (completed)' : ''}`}
                        sx={{
                          borderRadius: 0.5,
                          py: 0.5,
                          px: 1,
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            backgroundColor: 'action.hover',
                            transform: 'translateX(2px)',
                          },
                          '&:focus-visible': {
                            outline: '1px solid',
                            outlineColor: 'secondary.main',
                            outlineOffset: '1px',
                            backgroundColor: 'action.hover',
                          },
                        }}
                      >
                        <Box sx={{ mr: 1 }}>
                          {getFieldStatusIcon(field)}
                        </Box>
                        <ListItemText
                          primary={field.title}
                          primaryTypographyProps={{
                            fontSize: '0.875rem',
                            color: field.hasError ? 'error.main' : 'text.primary',
                          }}
                        />
                        {field.required && (
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'error.main',
                              fontSize: '0.75rem',
                              fontWeight: 'bold',
                            }}
                          >
                            *
                          </Typography>
                        )}
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

export default NavigationPanel;