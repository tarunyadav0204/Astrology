import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const ThemeContext = createContext();

export const THEMES = {
  dark: {
    background: '#1a0033',
    backgroundSecondary: '#2d1b4e',
    backgroundTertiary: '#4a2c6d',
    surface: 'rgba(255, 255, 255, 0.1)',
    text: '#ffffff',
    textSecondary: 'rgba(255, 255, 255, 0.7)',
    textTertiary: 'rgba(255, 255, 255, 0.5)',
    primary: '#f97316',
    secondary: '#ec4899',
    accent: '#ffd700',
    success: '#81C784',
    error: '#E57373',
    warning: '#FFB74D',
    gradientStart: '#1a0033',
    gradientMid: '#2d1b4e',
    gradientEnd: '#4a2c6d',
    cardBackground: 'rgba(255, 255, 255, 0.05)',
    cardBorder: 'rgba(255, 255, 255, 0.1)',
    statusBarStyle: 'light-content',
  },
  light: {
    background: '#fff5f0',
    backgroundSecondary: '#ffe8dc',
    backgroundTertiary: '#ffd4c8',
    surface: 'rgba(249, 115, 22, 0.08)',
    text: '#1a1a1a',
    textSecondary: '#7c2d12',
    textTertiary: '#9a3412',
    primary: '#f97316',
    secondary: '#ec4899',
    accent: '#fb923c',
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f59e0b',
    gradientStart: '#fff7ed',
    gradientMid: '#ffedd5',
    gradientEnd: '#fed7aa',
    cardBackground: '#ffffff',
    cardBorder: 'rgba(249, 115, 22, 0.2)',
    statusBarStyle: 'dark-content',
  },
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('dark');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTheme();
  }, []);

  const loadTheme = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('appTheme');
      if (savedTheme) {
        setTheme(savedTheme);
      }
    } catch (error) {
      console.error('Error loading theme:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTheme = async () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    try {
      await AsyncStorage.setItem('appTheme', newTheme);
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  };

  const colors = THEMES[theme];

  // Helper function to get card elevation based on theme
  const getCardElevation = (defaultElevation = 3) => {
    if (Platform.OS === 'android' && theme === 'light') {
      return 0;
    }
    return defaultElevation;
  };

  return (
    <ThemeContext.Provider value={{ theme, colors, toggleTheme, isLoading, getCardElevation }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
