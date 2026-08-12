import React, { createContext, useState, useContext, useEffect, useMemo, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, StatusBar } from 'react-native';
import i18n from '../locales/i18n';
import { storage } from '../services/storage';
import {
  THEME_DEFINITIONS,
  THEME_PALETTES,
  normalizeThemeId,
  layoutTokens,
  typographyTokens,
} from '../theme/tokens';

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

// Compatibility export for older imports. New UI should use the semantic
// `colors` object from useTheme rather than choosing a palette directly.
export const THEMES = THEME_PALETTES;

/** PWA / Expo Web: browser & installed-app chrome (Android status bar) follows theme. */
function syncWebChromeTheme(themeId) {
  if (Platform.OS !== 'web' || typeof document === 'undefined') return;
  const palette = THEME_PALETTES[themeId] || THEME_PALETTES.heritage;
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
  appleBar.setAttribute('content', palette.colorScheme === 'dark' ? 'black-translucent' : 'default');
  document.documentElement.style.backgroundColor = shellBg;
  document.documentElement.style.setProperty('--ar-shell-bg', shellBg);
  document.documentElement.style.colorScheme = palette.colorScheme || 'light';
  document.documentElement.dataset.theme = themeId;
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
      barStyle="light-content"
      backgroundColor={colors.headerSurface}
      translucent={false}
    />
  );
}

export const ThemeProvider = ({ children, initialTheme, initialPanditMode = false }) => {
  const resolvedConsumer = normalizeThemeId(initialTheme);
  const startPandit = Boolean(initialPanditMode);
  const [consumerThemeId, setConsumerThemeId] = useState(resolvedConsumer);
  const [isPanditMode, setIsPanditMode] = useState(startPandit);
  const [isLoading, setIsLoading] = useState(false);

  const themeId = isPanditMode ? 'pandit' : consumerThemeId;
  const activeDefinition = THEME_DEFINITIONS.find((item) => item.id === consumerThemeId)
    || THEME_DEFINITIONS[0];
  // Compatibility mode allows hundreds of existing dark/light checks to keep
  // behaving while new screens use themeId and semantic tokens.
  const theme = isPanditMode ? 'pandit' : activeDefinition.colorScheme === 'dark' ? 'dark' : 'light';

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
    syncWebChromeTheme(themeId);
  }, [themeId]);

  const loadTheme = async () => {
    try {
      setIsLoading(true);
      const [savedTheme, panditFlag] = await Promise.all([
        AsyncStorage.getItem(APP_THEME_KEY),
        AsyncStorage.getItem(PANDIT_MODE_KEY),
      ]);
      const nextConsumer = normalizeThemeId(savedTheme);
      const panditOn = panditFlag === '1' || panditFlag === 'true';
      setConsumerThemeId(nextConsumer);
      setIsPanditMode(panditOn);
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
    try {
      await AsyncStorage.setItem(PANDIT_MODE_KEY, '1');
      await applyPanditLanguage();
    } catch (error) {
      console.error('Error saving pandit mode:', error);
    }
  }, []);

  const exitPanditMode = useCallback(async () => {
    setIsPanditMode(false);
    try {
      await AsyncStorage.setItem(PANDIT_MODE_KEY, '0');
      await restoreConsumerLanguage();
    } catch (error) {
      console.error('Error clearing pandit mode:', error);
    }
  }, []);

  const setTheme = useCallback(async (nextTheme) => {
    const normalized = normalizeThemeId(nextTheme);
    setConsumerThemeId(normalized);
    if (isPanditMode) setIsPanditMode(false);
    try {
      await AsyncStorage.setItem(APP_THEME_KEY, normalized);
      if (isPanditMode) await AsyncStorage.setItem(PANDIT_MODE_KEY, '0');
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  }, [isPanditMode]);

  const toggleTheme = async () => {
    if (isPanditMode) {
      // Leaving white pandit shell → restore consumer preference.
      await exitPanditMode();
      return;
    }
    await setTheme(theme === 'dark' ? 'heritage' : 'midnight');
  };

  const isAndroidLight = Platform.OS === 'android' && theme !== 'dark';
  const palette = THEME_PALETTES[themeId] || THEME_PALETTES.heritage;
  const colors = useMemo(() => ({
    ...palette,
    onSurfaceInverse: palette.onSurfaceInverse || palette.textInverse,
    onSurfaceInverseMuted: palette.onSurfaceInverseMuted || palette.textInverseMuted,
  }), [palette]);

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
        themeId,
        setTheme,
        themes: THEME_DEFINITIONS,
        themeDefinition: activeDefinition,
        colors,
        toggleTheme,
        isLoading,
        getCardElevation,
        androidLightCardFixStyle,
        isPanditMode,
        enterPanditMode,
        exitPanditMode,
        layout: layoutTokens,
        typography: typographyTokens,
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
