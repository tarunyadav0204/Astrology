import React, { createContext, useState, useContext, useEffect, useMemo, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, StatusBar } from 'react-native';
import i18n from '../locales/i18n';
import { storage } from '../services/storage';

const ThemeContext = createContext();

export const PANDIT_MODE_KEY = 'panditMode';
export const APP_THEME_KEY = 'appTheme';
export const PANDIT_PREV_LANG_KEY = 'panditModePrevLanguage';
const PANDIT_UI_LANGUAGE = 'hindi';

async function applyPanditLanguage() {
  try {
    const current =
      (await storage.getLanguage()) || i18n.language || 'english';
    const savedPrev = await AsyncStorage.getItem(PANDIT_PREV_LANG_KEY);
    if (!savedPrev) {
      await AsyncStorage.setItem(PANDIT_PREV_LANG_KEY, current);
    }
    if (current !== PANDIT_UI_LANGUAGE) {
      await storage.setLanguage(PANDIT_UI_LANGUAGE);
      await i18n.changeLanguage(PANDIT_UI_LANGUAGE);
    }
  } catch (error) {
    console.error('Error applying pandit language:', error);
  }
}

async function restoreConsumerLanguage() {
  try {
    const prev = await AsyncStorage.getItem(PANDIT_PREV_LANG_KEY);
    await AsyncStorage.removeItem(PANDIT_PREV_LANG_KEY);
    if (prev && prev !== i18n.language) {
      await storage.setLanguage(prev);
      await i18n.changeLanguage(prev);
    } else if (prev) {
      await storage.setLanguage(prev);
    }
  } catch (error) {
    console.error('Error restoring language after pandit mode:', error);
  }
}

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
    strokeMuted: 'rgba(28, 25, 23, 0.2)',
    strokeStrong: 'rgba(28, 25, 23, 0.35)',
  },
  /** Clean white workbench while Pandit mode is on (app-wide). */
  pandit: {
    background: '#FFFFFF',
    backgroundSecondary: '#F4F4F5',
    backgroundTertiary: '#E4E4E7',
    surface: '#FFFFFF',
    text: '#18181B',
    textSecondary: '#52525B',
    textTertiary: '#71717A',
    // Desk chrome: ink/zinc — no orange brand wash
    primary: '#3F3F46',
    secondary: '#52525B',
    accent: '#71717A',
    success: '#16A34A',
    error: '#DC2626',
    warning: '#A16207',
    gradientStart: '#FFFFFF',
    gradientMid: '#FFFFFF',
    gradientEnd: '#FAFAFA',
    gradientAccent: '#F4F4F5',
    cardBackground: '#FFFFFF',
    cardBorder: 'rgba(24, 24, 27, 0.1)',
    statusBarStyle: 'dark-content',
    strokeMuted: 'rgba(24, 24, 27, 0.15)',
    strokeStrong: 'rgba(24, 24, 27, 0.3)',
  },
};

/** PWA / Expo Web: browser & installed-app chrome (Android status bar) follows theme. */
function syncWebChromeTheme(themeName) {
  if (Platform.OS !== 'web' || typeof document === 'undefined') return;
  const palette = THEMES[themeName] || THEMES.dark;
  const shellBg = palette.background;
  const bottomSafe = (
    document.documentElement.style.getPropertyValue('--ar-bottom-safe-color') || ''
  ).trim();
  const chromeBg = bottomSafe || shellBg;
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', chromeBg);
  document.querySelectorAll('meta[name="theme-color"][media]').forEach((el) => {
    el.setAttribute('content', chromeBg);
  });
  let appleBar = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
  if (!appleBar) {
    appleBar = document.createElement('meta');
    appleBar.setAttribute('name', 'apple-mobile-web-app-status-bar-style');
    document.head.appendChild(appleBar);
  }
  appleBar.setAttribute('content', themeName === 'dark' ? 'black-translucent' : 'default');
  document.documentElement.style.backgroundColor = shellBg;
  document.documentElement.style.colorScheme = themeName === 'dark' ? 'dark' : 'light';
  if (document.body) {
    document.body.style.backgroundColor = shellBg;
  }
  const root = document.getElementById('root');
  if (root) root.style.backgroundColor = shellBg;
}

export function ThemedStatusBar() {
  const { colors } = useTheme();
  return (
    <StatusBar
      barStyle={colors.statusBarStyle}
      backgroundColor={colors.background}
      translucent={false}
    />
  );
}

export const ThemeProvider = ({ children, initialTheme, initialPanditMode = false }) => {
  const resolvedConsumer =
    initialTheme === 'light' || initialTheme === 'dark' ? initialTheme : 'dark';
  const startPandit = Boolean(initialPanditMode);
  const [consumerTheme, setConsumerTheme] = useState(resolvedConsumer);
  const [isPanditMode, setIsPanditMode] = useState(startPandit);
  const [theme, setTheme] = useState(startPandit ? 'pandit' : resolvedConsumer);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (initialTheme != null || initialPanditMode) {
      if (initialPanditMode) {
        applyPanditLanguage();
      }
      return undefined;
    }
    loadTheme();
    return undefined;
  }, []);

  useEffect(() => {
    syncWebChromeTheme(theme === 'pandit' ? 'pandit' : theme);
  }, [theme]);

  const loadTheme = async () => {
    try {
      setIsLoading(true);
      const [savedTheme, panditFlag] = await Promise.all([
        AsyncStorage.getItem(APP_THEME_KEY),
        AsyncStorage.getItem(PANDIT_MODE_KEY),
      ]);
      const nextConsumer = savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'dark';
      const panditOn = panditFlag === '1' || panditFlag === 'true';
      setConsumerTheme(nextConsumer);
      setIsPanditMode(panditOn);
      setTheme(panditOn ? 'pandit' : nextConsumer);
      if (panditOn) {
        await applyPanditLanguage();
      }
    } catch (error) {
      console.error('Error loading theme:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const enterPanditMode = useCallback(async () => {
    setIsPanditMode(true);
    setTheme('pandit');
    try {
      await AsyncStorage.setItem(PANDIT_MODE_KEY, '1');
      await applyPanditLanguage();
    } catch (error) {
      console.error('Error saving pandit mode:', error);
    }
  }, []);

  const exitPanditMode = useCallback(async () => {
    setIsPanditMode(false);
    setTheme(consumerTheme);
    try {
      await AsyncStorage.setItem(PANDIT_MODE_KEY, '0');
      await restoreConsumerLanguage();
    } catch (error) {
      console.error('Error clearing pandit mode:', error);
    }
  }, [consumerTheme]);

  const toggleTheme = async () => {
    if (isPanditMode) {
      // Leaving white pandit shell → restore consumer preference.
      await exitPanditMode();
      return;
    }
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setConsumerTheme(newTheme);
    setTheme(newTheme);
    try {
      await AsyncStorage.setItem(APP_THEME_KEY, newTheme);
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  };

  const isAndroidLight = Platform.OS === 'android' && (theme === 'light' || theme === 'pandit');
  const baseColors = THEMES[theme] || THEMES.dark;
  const colors = isAndroidLight && theme === 'light'
    ? {
        ...baseColors,
        cardBackground: baseColors.background,
        surface: baseColors.backgroundSecondary,
        cardBorder: 'rgba(249, 115, 22, 0.12)',
      }
    : baseColors;

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

  const getCardElevation = (defaultElevation = 3) => {
    if (isAndroidLight) {
      return 0;
    }
    return defaultElevation;
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        colors,
        toggleTheme,
        isLoading,
        getCardElevation,
        androidLightCardFixStyle,
        isPanditMode,
        enterPanditMode,
        exitPanditMode,
      }}
    >
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
