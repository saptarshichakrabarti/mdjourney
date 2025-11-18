
import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import apiClient from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'mdjourney_authenticated';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  // Check localStorage first, then verify with backend
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem(AUTH_STORAGE_KEY) === 'true';
  });
  const [isChecking, setIsChecking] = useState(true);

  // Check if session exists on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        // Try to call the health endpoint - if it works, we have a valid session
        // The gateway will return 401 if there's no session
        await apiClient.get('/v1/health');
        setIsAuthenticated(true);
        localStorage.setItem(AUTH_STORAGE_KEY, 'true');
      } catch (error: any) {
        // If we get 401, there's no session
        if (error.response?.status === 401) {
          setIsAuthenticated(false);
          localStorage.removeItem(AUTH_STORAGE_KEY);
        } else {
          // For other errors (network, etc.), keep the localStorage state
          // If localStorage says authenticated, keep it; otherwise clear it
          const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY) === 'true';
          setIsAuthenticated(storedAuth);
        }
      } finally {
        setIsChecking(false);
      }
    };

    // Always check session on mount to verify it's still valid
    checkSession();
  }, []); // Only run on mount

  const login = () => {
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_STORAGE_KEY, 'true');
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  // Show nothing while checking session (prevents flash of login page)
  if (isChecking) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
