import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  persistThemeToAccount,
  registerThemeAccountApplier,
  syncStoredThemeWithAccount,
  THEME_STORAGE_KEY,
} from './themeAccountSync';

export { THEME_STORAGE_KEY };

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
    id: 'obsidian',
    label: 'Celestial Obsidian',
    colorScheme: 'dark',
    themeColor: '#120810',
    preview: { canvas: '#120810', surface: '#2a0c1c', accent: '#d8bc7a', border: 'rgba(255, 248, 236, 0.22)' },
  },
  {
    id: 'aurora',
    label: 'Astral Aurora',
    colorScheme: 'light',
    themeColor: '#082732',
    preview: { canvas: '#f3f7f6', surface: '#0b6fe8', accent: '#32cb0b', border: 'rgba(8, 58, 68, 0.22)' },
  },
  {
    id: 'deepLagoon',
    label: 'Deep Lagoon',
    colorScheme: 'light',
    themeColor: '#0f2a2a',
    preview: { canvas: '#d9faf4', surface: '#0f2a2a', accent: '#00bfa6', border: 'rgba(15, 42, 42, 0.24)' },
  },
  {
    id: 'oliveGold',
    label: 'Olive Gold',
    colorScheme: 'light',
    themeColor: '#4f4b38',
    preview: { canvas: '#f2eac9', surface: '#8a8467', accent: '#aaa171', border: 'rgba(79, 75, 56, 0.28)' },
  },
  {
    id: 'oxfordTan',
    label: 'Oxford Tan',
    colorScheme: 'dark',
    themeColor: '#002147',
    preview: { canvas: '#002147', surface: '#10365f', accent: '#d2b48c', border: 'rgba(210, 180, 140, 0.32)' },
  },
  {
    id: 'stargazing',
    label: 'Stargazing',
    colorScheme: 'dark',
    themeColor: '#2c2d31',
    preview: { canvas: '#424348', surface: '#4c4d53', accent: '#C6A97D', border: 'rgba(198, 169, 125, 0.30)' },
  },
  {
    id: 'mistyRose',
    label: 'Misty Rose',
    colorScheme: 'light',
    themeColor: '#633e49',
    preview: { canvas: '#ffe4e1', surface: '#c08081', accent: '#633e49', border: 'rgba(99, 62, 73, 0.26)' },
  },
  {
    id: 'amethystEmber',
    label: 'Amethyst Ember',
    colorScheme: 'light',
    themeColor: '#1a0033',
    preview: { canvas: '#1a0033', surface: '#ffffff', accent: '#ff6b35', border: 'rgba(255, 107, 53, 0.34)' },
  },
  {
    id: 'umberGold',
    label: 'Umber Gold',
    colorScheme: 'light',
    themeColor: '#583714',
    preview: { canvas: '#583714', surface: '#E0C46E', accent: '#FFF6D6', border: 'rgba(224, 196, 110, 0.40)' },
  },
  {
    id: 'lilacRose',
    label: 'Lilac Rose',
    colorScheme: 'light',
    themeColor: '#6968a6',
    preview: { canvas: '#6968a6', surface: '#cf9892', accent: '#fff7f4', border: 'rgba(207, 152, 146, 0.40)' },
  },
  {
    id: 'obsidianPlum',
    label: 'Obsidian Plum',
    colorScheme: 'dark',
    themeColor: '#401f70',
    preview: { canvas: '#401f70', surface: '#3d1b6d', accent: '#cc6475', border: 'rgba(204, 100, 117, 0.40)' },
  },
  {
    id: 'refinedEarth',
    label: 'Refined Earth',
    colorScheme: 'dark',
    themeColor: '#000000',
    preview: { canvas: '#000000', surface: '#1F1F1F', accent: '#E2725B', border: 'rgba(226, 114, 91, 0.40)' },
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
export const DEFAULT_THEME = 'heritage';

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
    persistThemeToAccount(normalized);
  }, []);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  useEffect(() => {
    registerThemeAccountApplier((themeId) => {
      const normalized = normalizeTheme(themeId);
      setThemeState(normalized);
      applyThemeToDocument(normalized);
    });
    if (typeof window !== 'undefined' && window.localStorage.getItem('token')) {
      syncStoredThemeWithAccount(normalizeTheme).catch(() => {});
    }
    return () => registerThemeAccountApplier(null);
  }, []);

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
