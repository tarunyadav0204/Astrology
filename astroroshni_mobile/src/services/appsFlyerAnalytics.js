/**
 * AppsFlyer MMP: install attribution + revenue events for paid UA (Appvestor, etc.).
 * Safe no-op in Expo Go, web, or when EXPO_PUBLIC_APPSFLYER_DEV_KEY is unset.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';

let sdkModule = null;
let sdkUnavailable = false;
let initStarted = false;
let sdkReady = false;
let conversionListener = null;
let deepLinkListener = null;

function getExtra() {
  return Constants.expoConfig?.extra || {};
}

function isExpoGoRuntime() {
  return Constants.appOwnership === 'expo' || Constants.executionEnvironment === 'storeClient';
}

function afLog(...args) {
  const extra = getExtra();
  if (!__DEV__ && !extra.appsFlyerDebug) return;
  console.log('[APPSFLYER]', ...args);
}

function getSdk() {
  if (sdkUnavailable || Platform.OS === 'web') return null;
  if (sdkModule) return sdkModule;
  try {
    sdkModule = require('react-native-appsflyer').default || require('react-native-appsflyer');
  } catch {
    sdkUnavailable = true;
    sdkModule = null;
  }
  return sdkModule;
}

export function isAppsFlyerConfigured() {
  if (isExpoGoRuntime() || Platform.OS === 'web') return false;
  const { appsFlyerDevKey, appsFlyerIosAppId } = getExtra();
  if (!appsFlyerDevKey) return false;
  if (Platform.OS === 'ios' && !appsFlyerIosAppId) return false;
  return true;
}

function sanitizeEventValues(params = {}) {
  const out = {};
  for (const [key, value] of Object.entries(params)) {
    if (value == null) continue;
    const safeKey = String(key).slice(0, 80);
    if (typeof value === 'string' || typeof value === 'number') {
      out[safeKey] = value;
    } else if (typeof value === 'boolean') {
      out[safeKey] = value ? '1' : '0';
    } else {
      out[safeKey] = String(value).slice(0, 300);
    }
  }
  return out;
}

function extractConversionPayload(res) {
  const nested = res && typeof res === 'object' ? res.data || res : null;
  if (!nested || typeof nested !== 'object' || Array.isArray(nested)) return null;
  return {
    af_status: nested.af_status || nested.status || null,
    media_source: nested.media_source || null,
    campaign: nested.campaign || null,
    campaign_id: nested.campaign_id || null,
    adset: nested.adset || nested.af_adset || null,
    ad: nested.ad || nested.af_ad || null,
    channel: nested.af_channel || nested.channel || null,
    attribution_raw: nested,
  };
}

async function persistConversion(payload) {
  try {
    const { persistAcquisitionAttribution } = require('./acquisitionTracking');
    await persistAcquisitionAttribution(payload);
  } catch (error) {
    afLog('persist conversion failed', String(error?.message || error));
  }
}

function registerConversionListener(appsFlyer) {
  if (conversionListener || typeof appsFlyer.onInstallConversionData !== 'function') return;
  conversionListener = appsFlyer.onInstallConversionData((res) => {
    afLog('conversion data', res);
    const payload = extractConversionPayload(res);
    if (!payload) return;
    persistConversion(payload).catch(() => {});
  });
}

function registerDeepLinkListener(appsFlyer) {
  if (deepLinkListener || typeof appsFlyer.onDeepLink !== 'function') return;
  deepLinkListener = appsFlyer.onDeepLink((res) => {
    afLog('deep link', res);
    const payload = extractConversionPayload(res);
    if (!payload) return;
    persistConversion(payload).catch(() => {});
  });
}

export async function initAppsFlyerAnalytics() {
  if (initStarted) return sdkReady;
  initStarted = true;

  if (!isAppsFlyerConfigured()) {
    if (__DEV__) {
      console.log('[AppsFlyer] disabled — set EXPO_PUBLIC_APPSFLYER_DEV_KEY (and iOS app id)');
    }
    return false;
  }

  const appsFlyer = getSdk();
  if (!appsFlyer || typeof appsFlyer.initSdk !== 'function') {
    if (__DEV__) {
      console.log('[AppsFlyer] native module missing — rebuild after adding react-native-appsflyer');
    }
    sdkUnavailable = true;
    return false;
  }

  const extra = getExtra();
  registerConversionListener(appsFlyer);
  registerDeepLinkListener(appsFlyer);

  const options = {
    devKey: extra.appsFlyerDevKey,
    isDebug: Boolean(extra.appsFlyerDebug),
    onInstallConversionDataListener: true,
    onDeepLinkListener: true,
    timeToWaitForATTUserAuthorization: 15,
  };
  if (Platform.OS === 'ios' && extra.appsFlyerIosAppId) {
    options.appId = String(extra.appsFlyerIosAppId);
  }

  return new Promise((resolve) => {
    appsFlyer.initSdk(
      options,
      (result) => {
        sdkReady = true;
        afLog('init ok', result);
        resolve(true);
      },
      (error) => {
        sdkReady = false;
        afLog('init failed', String(error?.message || error));
        resolve(false);
      }
    );
  });
}

export function logAppsFlyerEvent(eventName, params = {}) {
  if (!sdkReady || !eventName) return;
  const appsFlyer = getSdk();
  if (!appsFlyer || typeof appsFlyer.logEvent !== 'function') return;
  const values = sanitizeEventValues(params);
  appsFlyer.logEvent(
    String(eventName),
    values,
    () => afLog('event', eventName),
    (error) => afLog('event failed', eventName, String(error?.message || error))
  );
}

export function logAppsFlyerPurchase(amount, currency, extras = {}) {
  const value = Number(amount);
  if (!(value > 0)) return;
  logAppsFlyerEvent('af_purchase', {
    af_revenue: value,
    af_currency: currency || 'INR',
    af_content_id: extras.content_id || extras.contentId || extras.productId,
    af_content_type: extras.content_type || extras.contentType || 'credits',
    ...sanitizeEventValues(extras),
  });
}

export function logAppsFlyerStandardEvent(eventKey, params = {}) {
  switch (eventKey) {
    case 'complete_registration':
    case 'sign_up':
      logAppsFlyerEvent('af_complete_registration', {
        af_registration_method: params.method || params.registration_method || 'mobile',
      });
      return;
    case 'purchase':
      logAppsFlyerPurchase(params.amount ?? params.value, params.currency || 'INR', params);
      return;
    case 'subscribe':
      logAppsFlyerEvent('af_subscribe', {
        af_revenue: Number(params.value ?? params.amount ?? 0) || undefined,
        af_currency: params.currency || 'INR',
        af_content_id: params.content_id || params.productId,
        af_content_type: params.content_type || 'subscription',
      });
      return;
    case 'start_trial':
      logAppsFlyerEvent('af_start_trial', {
        af_content_id: params.content_id || params.productId,
        af_content_type: params.content_type || 'subscription_trial',
      });
      return;
    case 'initiate_checkout':
    case 'begin_checkout':
      logAppsFlyerEvent('af_initiated_checkout', {
        af_content_id: params.content_id || params.productId,
        af_currency: params.currency || 'INR',
        af_price: params.value ?? params.amount,
      });
      return;
    case 'login':
      logAppsFlyerEvent('af_login', { method: params.method || 'mobile' });
      return;
    default:
      return;
  }
}

export async function setAppsFlyerUserId(userId) {
  if (!sdkReady) return;
  const appsFlyer = getSdk();
  if (!appsFlyer || typeof appsFlyer.setCustomerUserId !== 'function') return;
  const id = userId != null && String(userId).trim() ? String(userId).trim() : '';
  try {
    appsFlyer.setCustomerUserId(id);
  } catch (error) {
    afLog('setCustomerUserId failed', String(error?.message || error));
  }
}
