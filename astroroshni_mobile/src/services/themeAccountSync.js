import AsyncStorage from '@react-native-async-storage/async-storage';
import { normalizeThemeId } from '../theme/tokens';

export const APP_THEME_KEY = 'appTheme';

let applyAccountTheme = null;

export function registerThemeAccountApplier(fn) {
  applyAccountTheme = typeof fn === 'function' ? fn : null;
}

export async function persistThemeToAccount(themeId) {
  const normalized = normalizeThemeId(themeId);
  try {
    const { userSettingsAPI } = require('./api');
    await userSettingsAPI.updateThemePreference(normalized);
  } catch (_) {
    // Local storage remains the on-device copy when the account write fails.
  }
}

export async function syncThemeWithAccountAfterAuth() {
  let localTheme = null;
  try {
    localTheme = await AsyncStorage.getItem(APP_THEME_KEY);
  } catch (_) {
    localTheme = null;
  }

  try {
    const { userSettingsAPI } = require('./api');
    const response = await userSettingsAPI.getThemePreference();
    const raw = String(response?.data?.theme_id || '').trim();
    const accountTheme = raw ? normalizeThemeId(raw) : null;
    const knownAccountTheme = Boolean(raw) && accountTheme === raw;
    if (knownAccountTheme && accountTheme) {
      applyAccountTheme?.(accountTheme);
      try {
        await AsyncStorage.setItem(APP_THEME_KEY, accountTheme);
      } catch (_) {}
      return accountTheme;
    }
    if (!raw && localTheme) {
      await persistThemeToAccount(localTheme);
    }
  } catch (_) {
    // Guests and offline sessions keep the device theme.
  }
  return localTheme;
}
