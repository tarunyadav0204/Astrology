import * as Sentry from '@sentry/react-native';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

const SENTRY_DSN = Constants.expoConfig?.extra?.sentryDsn || '';

export function initCrashReporting() {
  if (!SENTRY_DSN) {
    if (__DEV__) {
      console.log('[Sentry] No DSN configured — crash reporting disabled. Set SENTRY_DSN in app.json extra.');
    }
    return;
  }

  Sentry.init({
    dsn: SENTRY_DSN,
    debug: __DEV__,
    environment: __DEV__ ? 'development' : 'production',
    release: `com.astroroshni.mobile@${Constants.expoConfig?.version || '1.0.0'}`,
    dist: String(
      Platform.OS === 'ios'
        ? Constants.expoConfig?.ios?.buildNumber || '1'
        : Constants.expoConfig?.android?.versionCode || 1
    ),

    tracesSampleRate: __DEV__ ? 1.0 : 0.2,
    enableAutoSessionTracking: true,
    sessionTrackingIntervalMillis: 30000,

    beforeSend(event) {
      if (__DEV__) {
        console.log('[Sentry] Would send event:', event.event_id);
      }
      return event;
    },
  });
}

export function identifyUser(userId, userData = {}) {
  Sentry.setUser({
    id: String(userId),
    ...(userData.name && { username: userData.name }),
    ...(userData.phone && { phone: userData.phone }),
  });
}

export function clearUser() {
  Sentry.setUser(null);
}

export function reportError(error, context = {}) {
  Sentry.withScope((scope) => {
    Object.entries(context).forEach(([key, value]) => {
      scope.setExtra(key, value);
    });
    Sentry.captureException(error);
  });
}

export function addBreadcrumb(message, category = 'app', data = {}) {
  Sentry.addBreadcrumb({
    message,
    category,
    data,
    level: 'info',
  });
}

export function setScreen(screenName) {
  Sentry.addBreadcrumb({
    message: `Navigated to ${screenName}`,
    category: 'navigation',
    level: 'info',
  });
}

export function captureMessage(message, level = 'info') {
  Sentry.captureMessage(message, level);
}

export function setupGlobalJSErrorHandler() {
  const defaultHandler = ErrorUtils.getGlobalHandler();

  ErrorUtils.setGlobalHandler((error, isFatal) => {
    Sentry.withScope((scope) => {
      scope.setTag('isFatal', isFatal);
      scope.setTag('globalHandler', true);
      Sentry.captureException(error);
    });

    if (__DEV__) {
      console.error(`[GlobalErrorHandler] ${isFatal ? 'FATAL' : 'Non-fatal'} JS error:`, error);
    }

    if (defaultHandler) {
      defaultHandler(error, isFatal);
    }
  });
}

export function setupUnhandledPromiseRejectionHandler() {
  const tracking = require('promise/setimmediate/rejection-tracking');
  tracking.enable({
    allRejections: true,
    onUnhandled: (id, error) => {
      Sentry.withScope((scope) => {
        scope.setTag('unhandledPromise', true);
        scope.setExtra('promiseId', id);
        Sentry.captureException(error);
      });

      if (__DEV__) {
        console.warn('[UnhandledPromise] Rejection:', error);
      }
    },
  });
}
