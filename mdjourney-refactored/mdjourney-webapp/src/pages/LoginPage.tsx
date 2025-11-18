
import React, { useState, useCallback } from 'react';
import { Button, Container, Typography, Box, Alert } from '@mui/material';
import apiClient from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import yaml from 'js-yaml';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setError(null); // Clear previous errors
    }
  };

  const handleStartSession = useCallback(async () => {
    if (!selectedFile) {
      setError('Please select a configuration file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const content = event.target?.result;
        if (typeof content !== 'string') {
          throw new Error('Failed to read file content.');
        }
        const config = yaml.load(content);

        // The gateway expects a JSON object, js-yaml provides this.
        await apiClient.post('/api/session/start', config);

        login();
        navigate('/');
      } catch (e: any) {
        console.error('Failed to parse YAML or start session:', e);
        setError(`Failed to process config: ${e.message || 'Unknown error'}`);
      }
    };
    reader.onerror = () => {
        setError('Failed to read the selected file.');
    };
    reader.readAsText(selectedFile);
  }, [selectedFile, login, navigate]);

  return (
    <Container maxWidth="sm">
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2} // Add some spacing between elements
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to MDJourney
        </Typography>
        <Typography variant="subtitle1" component="p" gutterBottom>
          Select your session configuration file to begin.
        </Typography>

        <Button
          variant="outlined"
          component="label" // This makes the button act as a label for the hidden input
        >
          Choose Config File
          <input
            type="file"
            hidden
            accept=".yaml,.yml"
            onChange={handleFileChange}
          />
        </Button>

        {selectedFile && (
          <Typography variant="body1">
            Selected: {selectedFile.name}
          </Typography>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
            {error}
          </Alert>
        )}

        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleStartSession}
          disabled={!selectedFile}
          sx={{ mt: 2 }}
        >
          Start Session
        </Button>
      </Box>
    </Container>
  );
};

export default LoginPage;
