import React from 'react';
import { Box, Typography, Button, Alert, AlertTitle } from '@mui/material';
import { Refresh, BugReport } from '@mui/icons-material';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error} resetError={this.handleReset} />;
      }

      // Default error UI
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            p: 4,
            textAlign: 'center',
            backgroundColor: 'var(--fair-background)',
          }}
        >
          <Alert
            severity="error"
            sx={{
              mb: 3,
              maxWidth: 600,
              '& .MuiAlert-icon': {
                fontSize: '2rem',
              },
            }}
          >
            <AlertTitle sx={{ fontSize: '1.25rem', fontWeight: 600 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BugReport />
                Something went wrong
              </Box>
            </AlertTitle>
            <Typography variant="body1" sx={{ mb: 2 }}>
              An unexpected error occurred while rendering this component. This is likely a temporary issue.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Error: {this.state.error.message}
            </Typography>
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={this.handleReset}
              sx={{
                backgroundColor: 'var(--fair-primary)',
                '&:hover': {
                  backgroundColor: 'var(--fair-button-primary-hover)',
                },
              }}
            >
              Try Again
            </Button>

            <Button
              variant="outlined"
              onClick={() => window.location.reload()}
              sx={{
                borderColor: 'var(--fair-border-medium)',
                color: 'var(--fair-text-primary)',
                '&:hover': {
                  borderColor: 'var(--fair-primary)',
                  backgroundColor: 'var(--fair-info-bg)',
                },
              }}
            >
              Reload Page
            </Button>
          </Box>

          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <Box sx={{ mt: 4, p: 2, backgroundColor: 'var(--fair-surface)', borderRadius: 1, maxWidth: 800, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Development Error Details:
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--fair-text-secondary)',
                }}
              >
                {this.state.error.stack}
                {'\n\nComponent Stack:'}
                {this.state.errorInfo.componentStack}
              </Typography>
            </Box>
          )}
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;