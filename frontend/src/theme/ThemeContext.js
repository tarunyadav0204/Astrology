import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export const THEME_STORAGE_KEY = 'astroroshni_theme';

export const THEMES = Object.freeze([
  {
    id: 'heritage',
    label: 'Heritage',
    colorScheme: 'light',
    themeColor: '#210b17',
    preview: { canvas: '#f7f1e8', surface: '#210b17', accent: '#d7b878', border: 'rgba(255, 248, 238, 0.22)' },
  },
  {
    id: 'midnight',
    label: 'Midnight',
    colorScheme: 'dark',
    themeColor: '#100b17',
    preview: { canvas: '#100b17', surface: '#281b35', accent: '#d9bd7e', border: 'rgba(255, 248, 238, 0.22)' },
  },
  {
    id: 'clarity',
    label: 'Clarity',
    colorScheme: 'light',
    themeColor: '#265f56',
    preview: { canvas: '#f3f5f4', surface: '#265f56', accent: '#bd9145', border: 'rgba(255, 248, 238, 0.22)' },
  },
  {
    id: 'monochrome',
    label: 'Black & white',
    colorScheme: 'light',
    themeColor: '#050505',
    preview: { canvas: '#f4f4f2', surface: '#050505', accent: '#9a9a9a', border: 'rgba(255, 255, 255, 0.28)' },
  },
]);

const THEME_IDS = new Set(THEMES.map((theme) => theme.id));
const configuredDefault = process.env.REACT_APP_DEFAULT_THEME;
export const DEFAULT_THEME = THEME_IDS.has(configuredDefault) ? configuredDefault : 'heritage';

const ThemeContext = createContext(null);

export const normalizeTheme = (theme) => (THEME_IDS.has(theme) ? theme : DEFAULT_THEME);

const readInitialTheme = () => {
  if (typeof document !== 'undefined') {
    const preloaded = document.documentElement.dataset.theme;
    if (THEME_IDS.has(preloaded)) return preloaded;
  }
  if (typeof window !== 'undefined') {
    try {
      return normalizeTheme(window.localStorage.getItem(THEME_STORAGE_KEY));
    } catch (_) {
      return DEFAULT_THEME;
    }
  }
  return DEFAULT_THEME;
};

const applyThemeToDocument = (themeId) => {
  if (typeof document === 'undefined') return;
  const theme = THEMES.find((item) => item.id === themeId) || THEMES[0];
  document.documentElement.dataset.theme = theme.id;
  document.documentElement.style.colorScheme = theme.colorScheme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', theme.themeColor);
};

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readInitialTheme);

  const setTheme = useCallback((nextTheme) => {
    const normalized = normalizeTheme(nextTheme);
    setThemeState(normalized);
    applyThemeToDocument(normalized);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, normalized);
    } catch (_) {
      /* Theme persistence is optional when storage is unavailable. */
    }
  }, []);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  useEffect(() => {
    const syncThemeAcrossTabs = (event) => {
      if (event.key === THEME_STORAGE_KEY) setThemeState(normalizeTheme(event.newValue));
    };
    window.addEventListener('storage', syncThemeAcrossTabs);
    return () => window.removeEventListener('storage', syncThemeAcrossTabs);
  }, []);

  const value = useMemo(() => ({
    theme,
    setTheme,
    themes: THEMES,
    themeDefinition: THEMES.find((item) => item.id === theme) || THEMES[0],
  }), [setTheme, theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
