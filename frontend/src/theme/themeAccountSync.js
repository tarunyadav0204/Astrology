export const THEME_STORAGE_KEY = 'astroroshni_theme';

let applyAccountTheme = null;

export function registerThemeAccountApplier(fn) {
  applyAccountTheme = typeof fn === 'function' ? fn : null;
}

const readLocalTheme = () => {
  try {
    return window.localStorage.getItem(THEME_STORAGE_KEY);
  } catch (_) {
    return null;
  }
};

const writeLocalTheme = (themeId) => {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, themeId);
  } catch (_) {
    /* Theme persistence is optional when storage is unavailable. */
  }
};

export async function persistThemeToAccount(themeId) {
  try {
    const { apiService } = await import('../services/apiService');
    await apiService.updateAppTheme(themeId);
  } catch (_) {
    // Local storage remains the on-device copy when the account write fails.
  }
}

export async function syncStoredThemeWithAccount(normalizeTheme) {
  const localTheme = readLocalTheme();
  const normalize = typeof normalizeTheme === 'function' ? normalizeTheme : (value) => value;
  try {
    const { apiService } = await import('../services/apiService');
    const preference = await apiService.getAppTheme();
    const raw = String(preference?.theme_id || '').trim();
    const accountTheme = raw ? normalize(raw) : null;
    const knownAccountTheme = Boolean(raw) && accountTheme === raw;
    if (knownAccountTheme && accountTheme) {
      applyAccountTheme?.(accountTheme);
      writeLocalTheme(accountTheme);
      return accountTheme;
    }
    if (!raw && localTheme) {
      await persistThemeToAccount(normalize(localTheme));
    }
  } catch (_) {
    // Guests and offline sessions keep the device theme.
  }
  return localTheme;
}
