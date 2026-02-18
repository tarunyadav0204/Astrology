import React, { createContext, useState, useContext, useEffect, useMemo } from 'react';
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
    gradientAccent: '#f97316',
    cardBackground: 'rgba(255, 255, 255, 0.05)',
    cardBorder: 'rgba(255, 255, 255, 0.1)',
    statusBarStyle: 'light-content',
    strokeMuted: 'rgba(255, 255, 255, 0.3)',
    strokeStrong: 'rgba(255, 255, 255, 0.5)',
  },
  light: {
    background: '#fffbf7',
    backgroundSecondary: '#ffefe6',
    backgroundTertiary: '#ffdfd0',
    surface: 'rgba(249, 115, 22, 0.1)',
    text: '#1c1917',
    textSecondary: '#7c2d12',
    textTertiary: '#9a3412',
    primary: '#ea580c',
    secondary: '#db2777',
    accent: '#d97706',
    success: '#16a34a',
    error: '#dc2626',
    warning: '#d97706',
    gradientStart: '#fffbf7',
    gradientMid: '#ffefe6',
    gradientEnd: '#ffdfd0',
    gradientAccent: '#fde68a',
    cardBackground: '#ffffff',
    cardBorder: 'rgba(234, 88, 12, 0.25)',
    statusBarStyle: 'dark-content',
    // For elements that need to read well on both themes (e.g. zodiac wheel stroke)
    strokeMuted: 'rgba(28, 25, 23, 0.2)',
    strokeStrong: 'rgba(28, 25, 23, 0.35)',
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

  // On Android light theme, use card/surface colors almost same as background and remove elevation/shadow to avoid white inner-shadow look
  const isAndroidLight = Platform.OS === 'android' && theme === 'light';
  const baseColors = THEMES[theme];
  const colors = isAndroidLight
    ? {
        ...baseColors,
        cardBackground: baseColors.background,
        surface: baseColors.backgroundSecondary,
        cardBorder: 'rgba(249, 115, 22, 0.12)',
      }
    : baseColors;

  // Spread this onto any card View to remove elevation and shadow on Android light (fixes white inner shadow)
  const androidLightCardFixStyle = useMemo(() => 
    isAndroidLight
      ? {
          elevation: 0,
          shadowColor: 'transparent',
          shadowOpacity: 0,
          shadowRadius: 0,
          shadowOffset: { width: 0, height: 0 },
        }
      : {}, [isAndroidLight]);

  // Helper function to get card elevation based on theme
  const getCardElevation = (defaultElevation = 3) => {
    if (isAndroidLight) {
      return 0;
    }
    return defaultElevation;
  };

  return (
    <ThemeContext.Provider value={{ theme, colors, toggleTheme, isLoading, getCardElevation, androidLightCardFixStyle }}>
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
