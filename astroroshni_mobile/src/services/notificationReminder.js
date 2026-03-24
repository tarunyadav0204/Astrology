/**
 * In-app cadence for users who have not granted push permission (Android).
 * - First prompt: as soon as rules allow (handled by delay in UI).
 * - Repeat: every 7 days unless the user chose "Don't ask again".
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

const KEY_DECLINED_FOREVER = '@notif_reminder_declined_forever';
const KEY_LAST_SHOWN_MS = '@notif_reminder_last_shown_ms';
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

export async function shouldShowPushReminder() {
  if (Platform.OS === 'ios') return false;
  if (!Device.isDevice) return false;

  const declined = await AsyncStorage.getItem(KEY_DECLINED_FOREVER);
  if (declined === '1') return false;

  const { getPushPermissionStatusAsync } = require('./pushNotifications');
  const status = await getPushPermissionStatusAsync();
  if (status === 'granted') return false;

  const lastRaw = await AsyncStorage.getItem(KEY_LAST_SHOWN_MS);
  if (lastRaw == null || lastRaw === '') {
    return true;
  }
  const lastMs = parseInt(lastRaw, 10);
  if (!Number.isFinite(lastMs)) return true;
  return Date.now() - lastMs >= SEVEN_DAYS_MS;
}

export async function recordReminderShown() {
  await AsyncStorage.setItem(KEY_LAST_SHOWN_MS, String(Date.now()));
}

export async function recordReminderDeclinedForever() {
  await AsyncStorage.multiSet([
    [KEY_DECLINED_FOREVER, '1'],
    [KEY_LAST_SHOWN_MS, String(Date.now())],
  ]);
}
