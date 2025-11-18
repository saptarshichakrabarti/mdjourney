import {
  Box,
  CssBaseline,
  ThemeProvider,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  IconButton,
} from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

import ProjectBrowser from './components/ProjectBrowser';
import MetadataEditor from './components/MetadataEditor';
import ContextPanel from './components/ContextPanel';
import ErrorBoundary from './components/ErrorBoundary';
import { useAppTheme } from './hooks/useAppTheme';
import { useEffect } from 'react';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const { theme, toggleTheme, mode } = useAppTheme();

  // Keep CSS variable-based theming in sync by toggling the `.dark` class
  useEffect(() => {
    const root = document.documentElement;
    if (mode === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: 'background.default' }}>
        {/* Header */}
        <AppBar position="static" color="primary">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              FAIR Metadata Enrichment Tool
            </Typography>
            <IconButton onClick={toggleTheme} color="inherit">
              {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            gap: 2,
            p: 2,
            overflow: 'hidden',
          }}
        >
          {/* Pane 1: Navigation */}
          <Paper
            sx={{
              width: { xs: '100%', md: '24%' },
              minWidth: '280px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <ErrorBoundary>
              <ProjectBrowser />
            </ErrorBoundary>
          </Paper>

          {/* Pane 2: Metadata Editor */}
          <Paper
            sx={{
              flexGrow: 1,
              minWidth: '440px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <ErrorBoundary>
              <MetadataEditor />
            </ErrorBoundary>
          </Paper>

          {/* Pane 3: Context & Validation */}
          <Paper
            sx={{
              width: { xs: '100%', md: '22%' },
              minWidth: '260px',
              maxWidth: '360px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <ErrorBoundary>
              <ContextPanel />
            </ErrorBoundary>
          </Paper>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <AppContent />
      </LocalizationProvider>
    </QueryClientProvider>
  );
}

export default App;
