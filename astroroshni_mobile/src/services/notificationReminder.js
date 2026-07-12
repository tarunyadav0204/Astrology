/**
 * In-app cadence for users who have not granted push permission (Android).
 * - Home modal: every 7 days unless "Don't ask again".
 * - Contextual soft banner (report ready / chat answer): once per session,
 *   per-reason every 7 days, and never stacked with the home modal.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

const KEY_DECLINED_FOREVER = '@notif_reminder_declined_forever';
const KEY_LAST_SHOWN_MS = '@notif_reminder_last_shown_ms';
const KEY_CONTEXTUAL_PREFIX = '@notif_contextual_last_';

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
/** After any prompt, wait before another soft contextual ask. */
const CONTEXTUAL_STACK_GUARD_MS = 30 * 60 * 1000;

let sessionModalShown = false;
let sessionContextualShown = false;

async function baseEligibleForPushAsk() {
  if (Platform.OS === 'ios') return false;
  if (!Device.isDevice) return false;

  const declined = await AsyncStorage.getItem(KEY_DECLINED_FOREVER);
  if (declined === '1') return false;

  const { getPushPermissionStatusAsync } = require('./pushNotifications');
  const status = await getPushPermissionStatusAsync();
  if (status === 'granted') return false;

  return true;
}

export async function shouldShowPushReminder() {
  if (!(await baseEligibleForPushAsk())) return false;

  const lastRaw = await AsyncStorage.getItem(KEY_LAST_SHOWN_MS);
  if (lastRaw == null || lastRaw === '') {
    return true;
  }
  const lastMs = parseInt(lastRaw, 10);
  if (!Number.isFinite(lastMs)) return true;
  return Date.now() - lastMs >= SEVEN_DAYS_MS;
}

/**
 * Soft contextual banner (not a modal).
 * @param {'report_ready' | 'chat_answer' | string} reason
 */
export async function shouldShowContextualPushReminder(reason = 'generic') {
  if (!(await baseEligibleForPushAsk())) return false;
  if (sessionModalShown || sessionContextualShown) return false;

  const lastRaw = await AsyncStorage.getItem(KEY_LAST_SHOWN_MS);
  if (lastRaw) {
    const lastMs = parseInt(lastRaw, 10);
    if (Number.isFinite(lastMs) && Date.now() - lastMs < CONTEXTUAL_STACK_GUARD_MS) {
      return false;
    }
  }

  const reasonKey = `${KEY_CONTEXTUAL_PREFIX}${String(reason || 'generic')}`;
  const reasonLastRaw = await AsyncStorage.getItem(reasonKey);
  if (reasonLastRaw) {
    const reasonLastMs = parseInt(reasonLastRaw, 10);
    if (Number.isFinite(reasonLastMs) && Date.now() - reasonLastMs < SEVEN_DAYS_MS) {
      return false;
    }
  }

  return true;
}

export async function recordReminderShown() {
  sessionModalShown = true;
  sessionContextualShown = true;
  await AsyncStorage.setItem(KEY_LAST_SHOWN_MS, String(Date.now()));
}

export async function recordContextualReminderShown(reason = 'generic') {
  sessionContextualShown = true;
  const now = String(Date.now());
  await AsyncStorage.multiSet([
    [`${KEY_CONTEXTUAL_PREFIX}${String(reason || 'generic')}`, now],
    [KEY_LAST_SHOWN_MS, now],
  ]);
}

export async function recordReminderDeclinedForever() {
  sessionModalShown = true;
  sessionContextualShown = true;
  await AsyncStorage.multiSet([
    [KEY_DECLINED_FOREVER, '1'],
    [KEY_LAST_SHOWN_MS, String(Date.now())],
  ]);
}
