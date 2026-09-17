/**
 * Native Firebase Analytics (GA4 app stream). Falls back to no-op when the
 * native module is missing so Measurement Protocol can still send events.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';

let analyticsFn = null;
let sdkUnavailable = false;
let initTried = false;
let sdkReady = false;

function isExpoGoRuntime() {
  return Constants.appOwnership === 'expo' || Constants.executionEnvironment === 'storeClient';
}

function getAnalytics() {
  if (sdkUnavailable || Platform.OS === 'web') return null;
  if (analyticsFn) return analyticsFn;
  try {
    analyticsFn = require('@react-native-firebase/analytics').default;
  } catch {
    sdkUnavailable = true;
    analyticsFn = null;
  }
  return analyticsFn;
}

function sanitizeEventName(eventName) {
  const raw = String(eventName || '')
    .trim()
    .replace(/[^A-Za-z0-9_]/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40);
  if (!raw) return null;
  if (/^[0-9]/.test(raw)) return `e_${raw}`.slice(0, 40);
  const lower = raw.toLowerCase();
  if (lower.startsWith('firebase_') || lower.startsWith('google_') || lower.startsWith('ga_')) {
    return null;
  }
  return raw;
}

function sanitizeItems(items) {
  if (!Array.isArray(items)) return undefined;
  const rows = items.slice(0, 25).map((item) => {
    if (!item || typeof item !== 'object') return null;
    const row = {};
    for (const [key, value] of Object.entries(item)) {
      if (value == null) continue;
      const safeKey = String(key)
        .replace(/[^A-Za-z0-9_]/g, '_')
        .slice(0, 40);
      if (!safeKey) continue;
      if (typeof value === 'string') row[safeKey] = value.slice(0, 100);
      else if (typeof value === 'number' && Number.isFinite(value)) row[safeKey] = value;
    }
    return Object.keys(row).length ? row : null;
  }).filter(Boolean);
  return rows.length ? rows : undefined;
}

function sanitizeParams(params = {}) {
  const out = {};
  let count = 0;
  for (const [key, value] of Object.entries(params)) {
    if (count >= 25) break;
    if (value == null) continue;
    const safeKey = String(key)
      .replace(/[^A-Za-z0-9_]/g, '_')
      .slice(0, 40);
    if (!safeKey) continue;
    if (safeKey === 'items') {
      const items = sanitizeItems(value);
      if (items) {
        out.items = items;
        count += 1;
      }
      continue;
    }
    if (typeof value === 'string') {
      out[safeKey] = value.slice(0, 100);
    } else if (typeof value === 'number' && Number.isFinite(value)) {
      out[safeKey] = value;
    } else if (typeof value === 'boolean') {
      out[safeKey] = value;
    } else {
      out[safeKey] = String(value).slice(0, 100);
    }
    count += 1;
  }
  return out;
}

export async function initFirebaseAnalytics() {
  if (initTried) return sdkReady;
  initTried = true;
  if (isExpoGoRuntime() || Platform.OS === 'web') {
    sdkUnavailable = true;
    return false;
  }
  const analytics = getAnalytics();
  if (typeof analytics !== 'function') {
    if (__DEV__) {
      console.log('[Firebase Analytics] native module missing — rebuild after adding @react-native-firebase/analytics');
    }
    return false;
  }
  try {
    const instance = analytics();
    if (instance && typeof instance.setAnalyticsCollectionEnabled === 'function') {
      await instance.setAnalyticsCollectionEnabled(true);
    }
    sdkReady = true;
    if (__DEV__) console.log('[Firebase Analytics] ready');
    return true;
  } catch (error) {
    if (__DEV__) {
      console.warn('[Firebase Analytics] init failed', error?.message || error);
    }
    sdkReady = false;
    return false;
  }
}

export function isFirebaseAnalyticsReady() {
  return sdkReady;
}

export async function logFirebaseEvent(eventName, params = {}) {
  if (!sdkReady) return false;
  const analytics = getAnalytics();
  if (typeof analytics !== 'function') return false;
  const name = sanitizeEventName(eventName);
  if (!name) return false;
  try {
    const instance = analytics();
    const safeParams = sanitizeParams(params);
    if (name === 'purchase' && typeof instance.logPurchase === 'function') {
      const value = Number(params.amount ?? params.value ?? 0);
      const currency = String(params.currency || 'INR');
      const transactionId = params.transaction_id || params.order_id || params.orderId;
      const itemId = params.content_id || params.productId;
      const items = itemId
        ? [{
            item_id: String(itemId),
            item_name: String(params.item_name || params.content_type || 'credits'),
            item_category: String(params.content_type || 'credits'),
            ...(Number.isFinite(value) ? { price: value } : {}),
            quantity: 1,
          }]
        : sanitizeItems(params.items);
      await instance.logPurchase({
        value: Number.isFinite(value) ? value : 0,
        currency,
        ...(transactionId ? { transaction_id: String(transactionId) } : {}),
        ...(items ? { items } : {}),
      });
      return true;
    }
    if ((name === 'sign_up' || name === 'complete_registration') && typeof instance.logSignUp === 'function') {
      await instance.logSignUp({ method: String(params.method || params.registration_method || 'mobile') });
      return true;
    }
    if (name === 'login' && typeof instance.logLogin === 'function') {
      await instance.logLogin({ method: String(params.method || 'mobile') });
      return true;
    }
    if (typeof instance.logEvent !== 'function') return false;
    await instance.logEvent(name, safeParams);
    return true;
  } catch (error) {
    if (__DEV__) {
      console.warn('[Firebase Analytics] logEvent failed', eventName, error?.message || error);
    }
    return false;
  }
}

export async function logFirebaseScreenView(screenName, params = {}) {
  if (!sdkReady) return false;
  const analytics = getAnalytics();
  if (typeof analytics !== 'function') return false;
  try {
    const instance = analytics();
    if (typeof instance.logScreenView === 'function') {
      await instance.logScreenView({
        screen_name: String(screenName).slice(0, 100),
        screen_class: String(screenName).slice(0, 100),
      });
      return true;
    }
    return logFirebaseEvent('screen_view', { screen_name: screenName, ...params });
  } catch {
    return false;
  }
}

export async function setFirebaseUserId(userId) {
  if (!sdkReady) return;
  const analytics = getAnalytics();
  if (typeof analytics !== 'function') return;
  try {
    const id = userId != null && String(userId).trim() ? String(userId).trim() : null;
    await analytics().setUserId(id);
  } catch (error) {
    if (__DEV__) {
      console.warn('[Firebase Analytics] setUserId failed', error?.message || error);
    }
  }
}
