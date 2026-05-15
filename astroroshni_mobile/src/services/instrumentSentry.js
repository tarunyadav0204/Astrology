import * as Sentry from '@sentry/react-native';
import Constants from 'expo-constants';
import * as Application from 'expo-application';
import { Platform } from 'react-native';

const sentryNavigationIntegration = Sentry.reactNavigationIntegration();

const dsn =
  (Constants.expoConfig?.extra?.sentryDsn &&
    String(Constants.expoConfig.extra.sentryDsn).trim()) ||
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_SENTRY_DSN) ||
  '';

let initialized = false;

if (typeof dsn === 'string' && dsn.trim().length > 0) {
  try {
    Sentry.init({
      dsn: dsn.trim(),
      debug: __DEV__,
      environment: __DEV__ ? 'development' : 'production',
      tracesSampleRate: __DEV__ ? 1.0 : 0.12,
      integrations: [sentryNavigationIntegration],
      initialScope: (scope) => {
        const v = Constants.expoConfig?.version;
        if (v) scope.setTag('app.version', String(v));
        if (Constants.expoConfig?.slug) scope.setTag('expo.slug', String(Constants.expoConfig.slug));

        // Store / native build: Android versionCode, iOS CFBundleVersion (what you bump per upload).
        const nativeBuild =
          Application.nativeBuildVersion ||
          (Platform.OS === 'android'
            ? Constants.expoConfig?.android?.versionCode
            : Constants.expoConfig?.ios?.buildNumber);
        if (nativeBuild != null && String(nativeBuild).trim() !== '') {
          scope.setTag('app.build', String(nativeBuild));
          if (Platform.OS === 'android') {
            scope.setTag('android.version_code', String(nativeBuild));
          } else if (Platform.OS === 'ios') {
            scope.setTag('ios.build_number', String(nativeBuild));
          }
        }

        return scope;
      },
    });
    initialized = true;
  } catch (e) {
    if (__DEV__) {
      console.warn('[Sentry] init failed; app continues without crash reporting.', e?.message || e);
    }
  }
}

/**
 * Call from NavigationContainer ref so Sentry can attach route context to errors.
 */
export function attachSentryNavigation(nav) {
  if (!initialized || !nav) return;
  try {
    sentryNavigationIntegration.registerNavigationContainer(nav);
  } catch (_) {
    /* ignore */
  }
}

export function isSentryInitialized() {
  return initialized;
}
