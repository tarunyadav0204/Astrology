import { AppState, InteractionManager, Platform } from 'react-native';
import Constants from 'expo-constants';

let sdkModule = null;
let sdkUnavailable = false;
let initStarted = false;
let sdkReady = false;
let appStateSubscription = null;

function getExtra() {
  return Constants.expoConfig?.extra || {};
}

function isExpoGoRuntime() {
  return Constants.appOwnership === 'expo' || Constants.executionEnvironment === 'storeClient';
}

/** Logs to logcat (tag ReactNativeJS) when __DEV__ or EXPO_PUBLIC_FACEBOOK_DEBUG_LOG=1. */
function fbLog(...args) {
  const extra = getExtra();
  if (!__DEV__ && !extra.facebookDebugLog) return;
  console.log('[FB_EVENTS]', ...args);
}

/** When EXPO_PUBLIC_FACEBOOK_DEBUG_LOG is on, flush so Events Manager “Test events” sees traffic sooner. */
function flushAppEventsIfDebug(AppEventsLogger) {
  if (!getExtra().facebookDebugLog) return;
  try {
    if (AppEventsLogger && typeof AppEventsLogger.flush === 'function') {
      AppEventsLogger.flush();
      fbLog('flush after event');
    }
  } catch {
    /* ignore */
  }
}

export function isFacebookAnalyticsConfigured() {
  if (isExpoGoRuntime()) return false;
  const { facebookAppId, facebookClientToken } = getExtra();
  if (facebookAppId && facebookClientToken) return true;
  // Standalone / dev-client builds often embed App ID in native manifest/plist but omit
  // EXPO_PUBLIC_* from Constants.expoConfig.extra on CI — still log via native SDK.
  if (Platform.OS === 'web') return false;
  if (sdkUnavailable) return false;
  const sdk = getSdk();
  return Boolean(sdk?.Settings);
}

function getSdk() {
  if (sdkUnavailable || Platform.OS === 'web') return null;
  if (sdkModule) return sdkModule;
  try {
    sdkModule = require('react-native-fbsdk-next');
  } catch {
    sdkUnavailable = true;
    sdkModule = null;
  }
  return sdkModule;
}

function getAppEventsLogger() {
  const sdk = getSdk();
  if (!sdk?.AppEventsLogger) return null;
  return sdk.AppEventsLogger;
}

function getAppEventConstants() {
  const AppEventsLogger = getAppEventsLogger();
  if (!AppEventsLogger) {
    return { AppEvents: {}, AppEventParams: {} };
  }
  return {
    AppEvents: AppEventsLogger.AppEvents || {},
    AppEventParams: AppEventsLogger.AppEventParams || {},
  };
}

function paramKey(AppEventParams, name, fallback) {
  return (AppEventParams && AppEventParams[name]) || fallback;
}

function sanitizeParams(params = {}) {
  const out = {};
  for (const [key, value] of Object.entries(params)) {
    if (value == null) continue;
    if (typeof value === 'string' || typeof value === 'number') {
      out[key] = value;
    } else if (typeof value === 'boolean') {
      out[key] = value ? '1' : '0';
    } else {
      out[key] = String(value);
    }
  }
  return out;
}

function contentParams(AppEventParams, params = {}) {
  const P = AppEventParams || {};
  const out = {};
  const contentId = params.content_id ?? params.contentId;
  const contentType = params.content_type ?? params.contentType;
  if (contentId != null) {
    out[paramKey(P, 'ContentID', 'fb_content_id')] = String(contentId);
  }
  if (contentType != null) {
    out[paramKey(P, 'ContentType', 'fb_content_type')] = String(contentType);
  }
  const currency = params.currency;
  if (currency) {
    out[paramKey(P, 'Currency', 'fb_currency')] = String(currency);
  }
  return out;
}

function logFbEvent(AppEventsLogger, eventName, valueToSum = 0, parameters = null) {
  if (!eventName || typeof eventName !== 'string') return;
  if (parameters && Object.keys(parameters).length > 0) {
    if (valueToSum > 0) {
      AppEventsLogger.logEvent(eventName, valueToSum, parameters);
    } else {
      AppEventsLogger.logEvent(eventName, parameters);
    }
  } else if (valueToSum > 0) {
    AppEventsLogger.logEvent(eventName, valueToSum);
  } else {
    AppEventsLogger.logEvent(eventName);
  }
}

/**
 * Meta Events Manager standard app events (for ads / attribution).
 * @see https://developers.facebook.com/docs/app-events/reference
 */
export const MetaStandardEvent = {
  CONTACT: 'meta_contact',
  SEARCH: 'meta_search',
  COMPLETE_REGISTRATION: 'sign_up',
  VIEW_CONTENT: 'meta_view_content',
  SUBSCRIBE: 'meta_subscribe',
  INITIATE_CHECKOUT: 'meta_initiate_checkout',
  START_TRIAL: 'meta_start_trial',
  PURCHASE: 'purchase',
  ADD_PAYMENT_INFO: 'meta_add_payment_info',
};

function dispatchMetaStandardEvent(AppEventsLogger, eventKey, params = {}) {
  const { AppEvents, AppEventParams } = getAppEventConstants();
  const A = AppEvents || {};
  const P = AppEventParams || {};

  switch (eventKey) {
    case MetaStandardEvent.CONTACT:
      logFbEvent(AppEventsLogger, A.Contact || 'Contact');
      return true;

    case MetaStandardEvent.SEARCH: {
      const searchParams = {
        ...contentParams(P, params),
        ...(params.search_string
          ? { [paramKey(P, 'SearchString', 'fb_search_string')]: String(params.search_string) }
          : {}),
      };
      logFbEvent(AppEventsLogger, A.Searched || 'Search', 0, searchParams);
      return true;
    }

    case MetaStandardEvent.COMPLETE_REGISTRATION:
      logFbEvent(AppEventsLogger, A.CompletedRegistration || 'CompleteRegistration', 0, {
        [paramKey(P, 'RegistrationMethod', 'fb_registration_method')]:
          params.registration_method || params.method || 'mobile',
      });
      return true;

    case MetaStandardEvent.VIEW_CONTENT:
      logFbEvent(AppEventsLogger, A.ViewedContent || 'ViewContent', 0, contentParams(P, params));
      return true;

    case MetaStandardEvent.SUBSCRIBE: {
      const value = Number(params.value ?? params.valueToSum ?? 0);
      logFbEvent(
        AppEventsLogger,
        A.Subscribe || 'Subscribe',
        value > 0 ? value : 0,
        contentParams(P, params)
      );
      return true;
    }

    case MetaStandardEvent.INITIATE_CHECKOUT: {
      const value = Number(params.value ?? params.valueToSum ?? 0);
      logFbEvent(
        AppEventsLogger,
        A.InitiatedCheckout || 'InitiateCheckout',
        value > 0 ? value : 0,
        contentParams(P, params)
      );
      return true;
    }

    case MetaStandardEvent.START_TRIAL:
      logFbEvent(AppEventsLogger, A.StartTrial || 'StartTrial', 0, contentParams(P, params));
      return true;

    case MetaStandardEvent.ADD_PAYMENT_INFO: {
      const success = params.success !== false;
      logFbEvent(AppEventsLogger, A.AddedPaymentInfo || 'AddPaymentInfo', 0, {
        [paramKey(P, 'Success', 'fb_success')]: success ? '1' : '0',
        ...contentParams(P, params),
      });
      return true;
    }

    case MetaStandardEvent.PURCHASE:
    case 'credit_purchased': {
      const amount = Number(params.amount ?? params.value ?? params.valueToSum ?? 0);
      if (amount > 0) {
        AppEventsLogger.logPurchase(
          amount,
          params.currency || 'INR',
          contentParams(P, params)
        );
        return true;
      }
      return false;
    }

    default:
      return false;
  }
}

function logLegacyAliases(AppEventsLogger, eventName, params) {
  if (eventName === 'login') {
    AppEventsLogger.logEvent('login', sanitizeParams(params));
    return true;
  }
  return false;
}

/**
 * Log a Meta standard app event. Safe no-op when SDK or credentials are missing.
 */
export function logMetaAppEvent(eventKey, params = {}) {
  if (!isFacebookAnalyticsConfigured()) {
    fbLog('skip event (not configured)', String(eventKey));
    return;
  }
  if (!sdkReady) {
    fbLog('skip event (sdk not ready yet)', String(eventKey));
    return;
  }
  const AppEventsLogger = getAppEventsLogger();
  if (!AppEventsLogger) {
    fbLog('skip event (no AppEventsLogger)', String(eventKey));
    return;
  }

  try {
    if (dispatchMetaStandardEvent(AppEventsLogger, eventKey, params)) {
      fbLog('logged (standard)', String(eventKey));
      flushAppEventsIfDebug(AppEventsLogger);
      return;
    }
    if (logLegacyAliases(AppEventsLogger, eventKey, params)) {
      fbLog('logged (legacy alias)', String(eventKey));
      flushAppEventsIfDebug(AppEventsLogger);
      return;
    }
    AppEventsLogger.logEvent(eventKey, sanitizeParams(params));
    fbLog('logged (custom)', String(eventKey));
    flushAppEventsIfDebug(AppEventsLogger);
  } catch (error) {
    if (__DEV__) {
      console.warn('[Facebook] Meta event failed:', eventKey, error?.message || error);
    }
    fbLog('logEvent error', String(eventKey), String(error?.message || error));
  }
}

export function logFacebookEvent(eventName, params = {}) {
  logMetaAppEvent(eventName, params);
}

export function logFacebookScreenView(screenName, meta = {}) {
  if (!screenName) return;
  logMetaAppEvent(MetaStandardEvent.VIEW_CONTENT, {
    content_id: String(meta.content_id || screenName),
    content_type: String(meta.content_type || 'screen'),
  });
}

async function configureFacebookSdk() {
  const extra = getExtra();
  const hasExtraKeys = Boolean(extra.facebookAppId && extra.facebookClientToken);

  if (!isFacebookAnalyticsConfigured()) {
    if (__DEV__) {
      console.log('[Facebook] App Events disabled — set EXPO_PUBLIC_FACEBOOK_APP_ID and EXPO_PUBLIC_FACEBOOK_CLIENT_TOKEN');
    }
    fbLog('configure aborted: not configured', {
      appOwnership: Constants.appOwnership,
      hasExtraKeys,
      sdkUnavailable,
    });
    return false;
  }

  const sdk = getSdk();
  if (!sdk?.Settings || !sdk?.AppEventsLogger) {
    if (__DEV__) {
      console.log('[Facebook] Native SDK unavailable (rebuild the app after adding react-native-fbsdk-next)');
    }
    fbLog('configure aborted: native module missing', { hasSettings: Boolean(sdk?.Settings) });
    return false;
  }

  const { Settings, AppEventsLogger } = sdk;

  fbLog('configure start', {
    platform: Platform.OS,
    appOwnership: Constants.appOwnership,
    hasExtraKeys,
  });

  try {
    // Align with manifest; if Meta dashboard "Automatic App Event Logging" is OFF, dashboard wins — enable it there too.
    if (Settings.setAutoLogAppEventsEnabled) {
      Settings.setAutoLogAppEventsEnabled(true);
    }
    // Manifest keeps AdvertiserIDCollectionEnabled=false for store builds; for debug-flag builds,
    // turn on at runtime so Test Events / attribution can see GAID (Android 13+ may still need AD_ID in manifest).
    if (
      Platform.OS === 'android' &&
      extra.facebookDebugLog &&
      Settings.setAdvertiserIDCollectionEnabled
    ) {
      Settings.setAdvertiserIDCollectionEnabled(true);
      fbLog('Android: setAdvertiserIDCollectionEnabled(true) for debug build');
    }
    // AndroidManifest / Info.plist use AutoInit — do NOT call Settings.initializeSDK() or setAppID here;
    // double-init crashes the native Facebook SDK on startup.

    if (Platform.OS === 'ios') {
      try {
        const { requestTrackingPermissionsAsync } = require('expo-tracking-transparency');
        const { status } = await requestTrackingPermissionsAsync();
        if (Settings.setAdvertiserTrackingEnabled) {
          await Settings.setAdvertiserTrackingEnabled(status === 'granted');
        }
      } catch {
        if (Settings.setAdvertiserTrackingEnabled) {
          await Settings.setAdvertiserTrackingEnabled(false);
        }
      }
    }

    // react-native-fbsdk-next v13+ does not expose AppEventsLogger.activateApp() in JS.
    // Session / activate_app is handled by the native SDK when AutoLogAppEventsEnabled is set in the manifest.

    if (!appStateSubscription) {
      appStateSubscription = AppState.addEventListener('change', (nextState) => {
        if (nextState === 'active' && sdkReady) {
          try {
            if (typeof AppEventsLogger.flush === 'function') {
              AppEventsLogger.flush();
            }
          } catch {
            /* ignore */
          }
        }
      });
    }

    sdkReady = true;
    try {
      if (typeof AppEventsLogger.flush === 'function') {
        AppEventsLogger.flush();
        fbLog('flush() ok');
      }
    } catch (e) {
      fbLog('flush() failed', String(e?.message || e));
    }
    if (__DEV__) {
      console.log('[Facebook] App Events ready');
    }
    fbLog('configure done, sdkReady=true');
    return true;
  } catch (error) {
    if (__DEV__) {
      console.warn('[Facebook] init failed:', error?.message || error);
    }
    fbLog('configure exception', String(error?.message || error));
    return false;
  }
}

export async function initFacebookAnalytics() {
  if (initStarted) return sdkReady;
  initStarted = true;
  if (isExpoGoRuntime()) {
    sdkUnavailable = true;
    sdkReady = false;
    return false;
  }

  return new Promise((resolve) => {
    InteractionManager.runAfterInteractions(() => {
      configureFacebookSdk().then((ok) => {
        fbLog('initFacebookAnalytics finished', { ok });
        resolve(ok);
      });
    });
  });
}

export async function setFacebookUserId(userId) {
  if (!isFacebookAnalyticsConfigured()) return;
  const AppEventsLogger = getAppEventsLogger();
  if (!AppEventsLogger) return;

  try {
    const id = userId != null && String(userId).trim() ? String(userId).trim() : null;
    AppEventsLogger.setUserID(id);
  } catch (error) {
    if (__DEV__) {
      console.warn('[Facebook] setUserID failed:', error?.message || error);
    }
  }
}

export async function clearFacebookUserId() {
  return setFacebookUserId(null);
}
