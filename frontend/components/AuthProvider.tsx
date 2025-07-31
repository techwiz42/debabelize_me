'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, authService, AuthStatus } from '../services/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = async () => {
    try {
      setIsLoading(true);
      const status: AuthStatus = await authService.checkAuthStatus();
      setUser(status.user || null);
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authService.login(email, password);
      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
      authService.clearCache();
    } catch (error) {
      console.error('Logout failed:', error);
      // Clear local state even if API call fails
      setUser(null);
      authService.clearCache();
    }
  };

  const register = async (email: string, password: string) => {
    try {
      await authService.register(email, password);
      // Don't set user here - they need to confirm email first
    } catch (error) {
      throw error;
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};