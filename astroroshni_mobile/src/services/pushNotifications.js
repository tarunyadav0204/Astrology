/**
 * Push notifications: request permission, get Expo push token, register with backend,
 * and handle notification tap (e.g. open Chat).
 * Requires: npx expo install expo-device expo-notifications expo-constants
 *
 * IMPORTANT (iOS): Do not call any Notifications.* at module load time. iOS can crash
 * if the native notification module is used before the app bridge is ready. All setup
 * is deferred via setupNotificationHandler() and setupNotificationResponseListener()
 * called from App.js after mount.
 */
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { nudgeAPI } from './api';

// Fallback when Constants.expoConfig.extra.eas.projectId is missing (e.g. some release builds). Must match app.json extra.eas.projectId.
const EAS_PROJECT_ID_FALLBACK = '8e33070b-ac6c-42e0-a089-bd830019bb1a';

let notificationHandlerSet = false;

/**
 * Call once after app has mounted (e.g. from App.js useEffect). Required on iOS to avoid
 * crash from touching Notifications before native bridge is ready.
 */
export function setupNotificationHandler() {
  if (notificationHandlerSet) return;
  try {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
    notificationHandlerSet = true;
  } catch (e) {
    if (__DEV__) console.warn('[Push] setupNotificationHandler failed:', e?.message);
  }
}

/**
 * Request permission and get Expo push token.
 * @returns {{ token: string | null, reason: 'ok' | 'not_device' | 'denied' | 'token_failed', errorDetail?: string }}
 */
export async function registerForPushNotificationsAsync() {
  if (!Device.isDevice) {
    return { token: null, reason: 'not_device' };
  }
  try {
    const { status: existing } = await Notifications.getPermissionsAsync();
    let final = existing;
    if (existing !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      final = status;
    }
    if (final !== 'granted') {
      return { token: null, reason: 'denied' };
    }
    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ??
      Constants.easConfig?.projectId ??
      EAS_PROJECT_ID_FALLBACK;
    const tokenResult = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    const token = tokenResult?.data ?? null;
    if (!token) {
      return { token: null, reason: 'token_failed', errorDetail: 'No token returned' };
    }
    return { token, reason: 'ok' };
  } catch (e) {
    const msg = e?.message ?? String(e);
    if (__DEV__) console.warn('[Push] registerForPushNotificationsAsync error:', msg);
    return { token: null, reason: 'token_failed', errorDetail: msg || 'Unknown error' };
  }
}

/**
 * Send the Expo push token to the backend so nudges can be delivered.
 * Uses authenticated API (Bearer token). No-op if token is null/empty.
 */
export async function registerDeviceTokenWithBackend(pushToken) {
  if (!pushToken || typeof pushToken !== 'string' || !pushToken.trim()) {
    if (__DEV__) console.log('[Push] registerDeviceTokenWithBackend: no token, skip');
    return;
  }
  const platform = Platform.OS === 'ios' ? 'ios' : 'android';
  await nudgeAPI.registerDeviceToken(pushToken.trim(), platform);
  if (__DEV__) console.log('[Push] Device token registered with backend');
}

/**
 * Register for push and send token to backend. Call after login or when app
 * opens with an existing session.
 */
/**
 * @returns {Promise<{ ok: boolean, message: string }>} ok true if token was sent to backend, message for user/alert
 */
export async function registerPushTokenIfLoggedIn() {
  try {
    const { token, reason, errorDetail } = await registerForPushNotificationsAsync();
    if (reason !== 'ok' || !token) {
      const messages = {
        not_device: 'Push notifications require a physical device. They don\'t work in the simulator.',
        denied: 'Notifications are turned off. Open Settings → AstroRoshni → Notifications and allow notifications, then try again.',
        token_failed: 'Could not get notification token. Try again or reinstall the app.',
      };
      let message = messages[reason] || messages.token_failed;
      if (reason === 'token_failed' && errorDetail) {
        message += ` (${errorDetail})`;
      }
      return { ok: false, message };
    }
    await registerDeviceTokenWithBackend(token);
    return { ok: true, message: 'Notifications registered.' };
  } catch (e) {
    const msg = e?.response?.status === 401 ? 'Session expired. Please log in again.' : (e?.message || 'Failed to register.');
    if (__DEV__) console.warn('[Push] registerPushTokenIfLoggedIn error:', e?.message);
    return { ok: false, message: msg };
  }
}

/**
 * Process a notification response and navigate to Home (Chat).
 * - Native-specific event (data.native_id present): set that native in storage, then open chat.
 * - Global event (no native_id): prefer the birth chart marked as "self"; only if none, keep existing selected native. Then open chat.
 * Used by both the tap listener and cold-start handling.
 * @param {{ notification: { request: { content?: { data?: object } } } }} response - from addNotificationResponseReceivedListener or getLastNotificationResponseAsync
 * @param {React.RefObject} navigationRef - ref from NavigationContainer
 */
async function processNotificationResponse(response, navigationRef) {
  const data = response?.notification?.request?.content?.data;
  if (!data) return;
  const cta = data?.cta;
  const question = data?.question && String(data.question).trim() ? String(data.question).trim() : undefined;
  const nativeId = data?.native_id != null ? String(data.native_id).trim() : null;
  const { storage } = require('./storage');
  const { chartAPI } = require('./api');
  try {
    if (nativeId) {
      // Native-specific event: switch to the chart this notification is for
      let profiles = await storage.getBirthProfiles();
      let profile = (profiles || []).find(
        (p) => String(p?.id) === nativeId || String(p?._id) === nativeId
      );
      if (!profile) {
        try {
          const res = await chartAPI.getExistingCharts();
          const apiCharts = res?.data?.charts || [];
          const chart = apiCharts.find(
            (c) => String(c?.id) === nativeId || String(c?._id) === nativeId
          );
          if (chart) {
            profile = {
              id: chart.id ?? chart._id,
              name: chart.name,
              date: chart.date,
              time: chart.time,
              place: chart.place,
              latitude: chart.latitude,
              longitude: chart.longitude,
              gender: chart.gender,
              relation: chart.relation,
              isSelf: chart.relation === 'self',
            };
          }
        } catch (_) {}
      }
      if (profile) {
        await storage.setBirthDetails(profile);
      }
    } else {
      // Global event: prefer "self" chart so chat uses the user's own chart; only if no self, keep existing native
      const profiles = await storage.getBirthProfiles();
      const selfProfile = (profiles || []).find(
        (p) => p?.relation === 'self' || p?.isSelf === true
      );
      if (selfProfile) {
        await storage.setBirthDetails(selfProfile);
      }
      // else: leave current selected native unchanged (getBirthDetails stays as is)
    }
    if (navigationRef?.current && (cta === 'astroroshni://chat' || !cta)) {
      const sessionId = data?.session_id != null ? String(data.session_id).trim() : null;
      navigationRef.current.navigate('Home', {
        startChat: true,
        ...(question && { initialMessage: question }),
        ...(sessionId && { responseReadySessionId: sessionId }),
      });
    }
  } catch (e) {
    if (__DEV__) console.warn('[Push] processNotificationResponse error:', e?.message);
  }
}

/**
 * Handle notification tap when app was killed (cold start). The system delivers the tap
 * before our listener is registered; Expo stores it as the "last notification response".
 * Call this once after the navigator is ready (e.g. from App.js with a short delay).
 */
export async function handleColdStartNotificationResponse(navigationRef) {
  try {
    const response = await Notifications.getLastNotificationResponseAsync();
    if (response && navigationRef?.current) {
      await processNotificationResponse(response, navigationRef);
    }
  } catch (e) {
    if (__DEV__) console.warn('[Push] handleColdStartNotificationResponse failed:', e?.message);
  }
}

/**
 * Set up listener for when user taps a notification. navigationRef should be
 * the ref from NavigationContainer so we can navigate to Home (Chat).
 * If data.native_id is present, sets that native as selected in storage before
 * opening chat so the question is answered for the correct chart.
 */
export function setupNotificationResponseListener(navigationRef) {
  try {
    const sub = Notifications.addNotificationResponseReceivedListener(async (response) => {
      await processNotificationResponse(response, navigationRef);
    });
    return () => {
      try {
        Notifications.removeNotificationSubscription(sub);
      } catch (_) {}
    };
  } catch (e) {
    if (__DEV__) console.warn('[Push] setupNotificationResponseListener failed:', e?.message);
    return () => {};
  }
}
