/**
 * Sentry bootstrap for Expo Web.
 * Avoids @sentry/react-native native wiring; tags environment as mobile-web.
 * Full browser Sentry SDK can replace this later without changing call sites.
 */
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const dsn =
  (Constants.expoConfig?.extra?.sentryDsn &&
    String(Constants.expoConfig.extra.sentryDsn).trim()) ||
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_SENTRY_DSN) ||
  '';

let initialized = false;

if (typeof dsn === 'string' && dsn.trim().length > 0 && typeof window !== 'undefined') {
  try {
    // Soft init marker — native Sentry RN APIs are not reliable on web export.
    // Errors still surface via ErrorBoundary / runtimeGuard.
    if (typeof __DEV__ !== 'undefined' && __DEV__) {
      console.info('[Sentry] mobile-web bootstrap (no-op SDK; environment tagged)');
    }
    window.__ASTROROSHNI_SENTRY_ENV__ = 'mobile-web';
    window.__ASTROROSHNI_SENTRY_DSN__ = dsn.trim();
    initialized = true;
    if (Platform.OS === 'web') {
      // Reserved for future @sentry/browser init without blocking boot.
    }
  } catch (e) {
    if (typeof __DEV__ !== 'undefined' && __DEV__) {
      console.warn('[Sentry] web init skipped', e?.message || e);
    }
  }
}

export function attachSentryNavigation() {
  /* no-op on web until browser SDK is wired */
}

export function isSentryInitialized() {
  return initialized;
}
