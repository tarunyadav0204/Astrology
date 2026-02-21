/**
 * Push notifications: request permission, get Expo push token, register with backend,
 * and handle notification tap (e.g. open Chat).
 * Requires: npx expo install expo-device expo-notifications expo-constants
 */
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { nudgeAPI } from './api';

// Optional: show notification when app is in foreground (default is no)
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Request permission and return Expo push token, or null if denied/unavailable.
 * Must run on a physical device for push to work; simulator often returns null.
 */
export async function registerForPushNotificationsAsync() {
  if (!Device.isDevice) {
    return null;
  }
  try {
    const { status: existing } = await Notifications.getPermissionsAsync();
    let final = existing;
    if (existing !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      final = status;
    }
    if (final !== 'granted') {
      return null;
    }
    const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
    const tokenResult = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    return tokenResult?.data ?? null;
  } catch (e) {
    return null;
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
  try {
    const platform = Platform.OS === 'ios' ? 'ios' : 'android';
    await nudgeAPI.registerDeviceToken(pushToken.trim(), platform);
    if (__DEV__) console.log('[Push] Device token registered with backend');
  } catch (err) {
    if (__DEV__) console.warn('[Push] Failed to register device token:', err?.response?.status, err?.message);
    // Don't throw; app should work without push
  }
}

/**
 * Register for push and send token to backend. Call after login or when app
 * opens with an existing session.
 */
export async function registerPushTokenIfLoggedIn() {
  try {
    const pushToken = await registerForPushNotificationsAsync();
    if (pushToken) {
      await registerDeviceTokenWithBackend(pushToken);
    } else if (__DEV__) {
      console.log('[Push] No push token (permission denied or not a device)');
    }
  } catch (e) {
    if (__DEV__) console.warn('[Push] registerPushTokenIfLoggedIn error:', e?.message);
  }
}

/**
 * Set up listener for when user taps a notification. navigationRef should be
 * the ref from NavigationContainer so we can navigate to Home (Chat).
 */
export function setupNotificationResponseListener(navigationRef) {
  const sub = Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content?.data;
    const cta = data?.cta;
    try {
      if (navigationRef?.current && (cta === 'astroroshni://chat' || !cta)) {
        navigationRef.current.navigate('Home');
      }
    } catch (e) {
      // ignore
    }
  });
  return () => Notifications.removeNotificationSubscription(sub);
}
