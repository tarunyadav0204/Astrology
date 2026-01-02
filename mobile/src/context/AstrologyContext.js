import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService } from '../services/apiService';

const AstrologyContext = createContext();

export const useAstrology = () => {
  const context = useContext(AstrologyContext);
  if (!context) {
    throw new Error('useAstrology must be used within an AstrologyProvider');
  }
  return context;
};

export const AstrologyProvider = ({ children }) => {
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
    loadStoredBirthData();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        const userData = await AsyncStorage.getItem('userData');
        if (userData) {
          setUser(JSON.parse(userData));
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    }
  };

  const loadStoredBirthData = async () => {
    try {
      const stored = await AsyncStorage.getItem('birthData');
      if (stored) {
        const data = JSON.parse(stored);
        setBirthData(data);
        // Auto-calculate chart if birth data exists
        await calculateChart(data);
      }
    } catch (error) {
      console.error('Error loading stored birth data:', error);
    }
  };

  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      // Clear any existing auth data first
      await AsyncStorage.multiRemove(['authToken', 'userData']);
      
      const response = await apiService.login(credentials);
      
      // Store new auth data
      await AsyncStorage.setItem('authToken', response.access_token);
      await AsyncStorage.setItem('userData', JSON.stringify(response.user));
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return response;
    } catch (error) {
      setError(error.message);
      // Clear any partial auth state on error
      await AsyncStorage.multiRemove(['authToken', 'userData']);
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.multiRemove(['authToken', 'userData', 'birthData']);
      setUser(null);
      setIsAuthenticated(false);
      setBirthData(null);
      setChartData(null);
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const calculateChart = async (data) => {
    try {
      setLoading(true);
      setError(null);
      
      const chart = await apiService.calculateChart(data, user?.phone);
      setChartData(chart);
      setBirthData(data);
      
      // Store birth data for future use
      await AsyncStorage.setItem('birthData', JSON.stringify(data));
      
      return chart;
    } catch (error) {
      setError(error.message);
      // console.error('Error calculating chart:', error);
      if (error.response?.status === 401) {
        await logout();
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const calculateTransits = async (transitDate) => {
    try {
      if (!birthData) {
        throw new Error('Birth data not available');
      }
      
      setLoading(true);
      const transits = await apiService.calculateTransits(birthData, transitDate);
      return transits;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const calculateNavamsa = async () => {
    try {
      if (!birthData) {
        throw new Error('Birth data not available');
      }
      
      setLoading(true);
      const navamsa = await apiService.calculateNavamsa(birthData);
      return navamsa;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const calculateDivisional = async (division) => {
    try {
      if (!birthData) {
        throw new Error('Birth data not available');
      }
      
      setLoading(true);
      const divisional = await apiService.calculateDivisional(birthData, division);
      return divisional;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const calculateYogi = async () => {
    try {
      if (!birthData) {
        throw new Error('Birth data not available');
      }
      
      setLoading(true);
      const yogi = await apiService.calculateYogi(birthData);
      return yogi;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const calculateDashas = async () => {
    try {
      if (!birthData) {
        throw new Error('Birth data not available');
      }
      
      setLoading(true);
      const dashas = await apiService.calculateDashas(birthData);
      return dashas;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    // State
    birthData,
    chartData,
    loading,
    error,
    user,
    isAuthenticated,
    
    // Actions
    login,
    logout,
    calculateChart,
    calculateTransits,
    calculateNavamsa,
    calculateDivisional,
    calculateYogi,
    calculateDashas,
    setBirthData,
    setError,
    setUser,
  };

  return (
    <AstrologyContext.Provider value={value}>
      {children}
    </AstrologyContext.Provider>
  );
};