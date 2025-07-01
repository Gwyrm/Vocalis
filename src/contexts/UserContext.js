import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [preferences, setPreferences] = useState({
    defaultReportType: 'scanner',
    language: 'fr-FR',
    theme: 'light',
    autoSave: true,
    autoSaveInterval: 30000, // 30 seconds
  });
  const [loading, setLoading] = useState(true);

  // Load user data from localStorage on mount
  useEffect(() => {
    const loadUserData = () => {
      try {
        const savedUser = localStorage.getItem('user');
        const savedPreferences = localStorage.getItem('userPreferences');
        
        if (savedUser) {
          setUser(JSON.parse(savedUser));
        }
        
        if (savedPreferences) {
          setPreferences(prev => ({ ...prev, ...JSON.parse(savedPreferences) }));
        }
      } catch (error) {
        console.error('Error loading user data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadUserData();
  }, []);

  // Save user data to localStorage when it changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  }, [user]);

  // Save preferences to localStorage when they change
  useEffect(() => {
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
  }, [preferences]);

  const login = (userData) => {
    setUser(userData);
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const updatePreferences = (newPreferences) => {
    setPreferences(prev => ({ ...prev, ...newPreferences }));
  };

  const updateUser = (updates) => {
    setUser(prev => ({ ...prev, ...updates }));
  };

  const value = {
    user,
    preferences,
    loading,
    login,
    logout,
    updatePreferences,
    updateUser,
    isAuthenticated: !!user,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};