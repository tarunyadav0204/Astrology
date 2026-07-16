/**
 * Push notifications no-op for Expo Web. Web Push can be added later.
 * Must export the same names as pushNotifications.js so App.js lazy requires work.
 */

export function setupNotificationHandler() {}

export async function getPushPermissionStatusAsync() {
  return 'denied';
}

export async function registerForPushNotificationsAsync() {
  return { token: null, reason: 'not_device' };
}

export async function registerDeviceTokenWithBackend() {
  return { ok: false, reason: 'web_unsupported' };
}

export async function syncPushTokenIfPermissionGranted() {
  return { ok: false, reason: 'web_unsupported' };
}

export async function registerPushTokenIfLoggedIn() {
  return { ok: false, reason: 'web_unsupported' };
}

export async function handleColdStartNotificationResponse() {
  return false;
}

export function setupNotificationResponseListener() {
  return () => {};
}

export async function getLastNotificationResponseAsync() {
  return null;
}

export default {
  setupNotificationHandler,
  getPushPermissionStatusAsync,
  registerForPushNotificationsAsync,
  registerDeviceTokenWithBackend,
  syncPushTokenIfPermissionGranted,
  registerPushTokenIfLoggedIn,
  handleColdStartNotificationResponse,
  setupNotificationResponseListener,
  getLastNotificationResponseAsync,
};
