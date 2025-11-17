
import React from 'react';
import { Button, Container, Typography, Box } from '@mui/material';
import apiClient from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleStartSession = async () => {
    try {
      await apiClient.post('/session/start');
      login();
      navigate('/');
    } catch (error) {
      console.error('Failed to start session:', error);
      // Handle login error (e.g., show a message to the user)
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to MDJourney
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleStartSession}
        >
          Start Session
        </Button>
      </Box>
    </Container>
  );
};

export default LoginPage;
