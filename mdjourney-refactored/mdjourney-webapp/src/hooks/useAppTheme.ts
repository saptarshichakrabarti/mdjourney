import { useState, useMemo } from 'react';
import { createTheme } from '@mui/material';

type ThemeMode = 'light' | 'dark';

// Define your light and dark theme palettes
const lightPalette = {
  mode: 'light' as ThemeMode,
  primary: {
    main: '#3FA5BC',
    dark: '#318a9f',
  },
  secondary: {
    main: '#FDB813',
  },
  error: {
    main: '#dc3545',
  },
  warning: {
    main: '#ffc107',
  },
  success: {
    main: '#28a745',
  },
  info: {
    main: '#17a2b8',
  },
  background: {
    default: '#f8f9fa',
    paper: '#FFFFFF',
  },
  text: {
    primary: '#333333',
    secondary: '#6c757d',
  },
};

const darkPalette = {
  mode: 'dark' as ThemeMode,
  primary: {
    main: '#4FC3F7', // A lighter blue for dark mode
    dark: '#2196F3',
  },
  secondary: {
    main: '#FFC107', // Keep secondary color vibrant
  },
  error: {
    main: '#FF6B6B',
  },
  warning: {
    main: '#FFA726',
  },
  success: {
    main: '#66BB6A',
  },
  info: {
    main: '#26C6DA',
  },
  background: {
    default: '#121212', // Standard dark theme background
    paper: '#1E1E1E',   // A slightly lighter paper color
  },
  text: {
    primary: '#E0E0E0', // Light text for dark backgrounds
    secondary: '#BDBDBD',
  },
};

const themeConfig = {
  typography: {
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-notchedOutline legend': {
            maxWidth: 0,
            paddingLeft: 0,
            paddingRight: 0,
            transition: 'max-width 150ms ease',
          },
        },
      },
    },
    MuiFormControl: {
      styleOverrides: {
        root: {
          '& .MuiInputLabel-shrink + .MuiOutlinedInput-root .MuiOutlinedInput-notchedOutline legend': {
            maxWidth: '1000px',
            paddingLeft: '6px',
            paddingRight: '6px',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },

  },
};

export const useAppTheme = () => {
  const [mode, setMode] = useState<ThemeMode>('light');

  const toggleTheme = () => {
    setMode((prevMode: ThemeMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  const theme = useMemo(() => {
    const palette = mode === 'light' ? lightPalette : darkPalette;
    return createTheme({ palette, ...themeConfig });
  }, [mode]);

  return { theme, toggleTheme, mode };
};
