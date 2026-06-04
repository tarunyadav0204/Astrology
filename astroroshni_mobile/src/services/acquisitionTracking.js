/**
 * First-party install funnel: stable installation_id per app install (AsyncStorage),
 * first-open ping (anonymous), link after auth. Optional Play install referrer when native module is added.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, Linking } from 'react-native';
import * as Application from 'expo-application';
import { API_BASE_URL, getEndpoint } from '../utils/constants';

const INSTALLATION_ID_KEY = 'astro_installation_id_v1';
const FIRST_OPEN_SENT_KEY = 'astro_acquisition_first_open_sent_v1';

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const BLOCKED_METADATA_KEYS = new Set([
  'password',
  'token',
  'access_token',
  'auth',
  'authorization',
  'otp',
  'code',
  'phone',
  'email',
]);

/** Serialize first-open so parallel callers cannot mint two installation_ids before AsyncStorage settles. */
let firstOpenChain = Promise.resolve();

function generateUuidV4() {
  if (typeof globalThis.crypto !== 'undefined' && typeof globalThis.crypto.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export async function getOrCreateInstallationId() {
  const existing = await AsyncStorage.getItem(INSTALLATION_ID_KEY);
  if (existing && UUID_RE.test(String(existing).trim())) {
    return String(existing).trim();
  }
  const id = generateUuidV4();
  await AsyncStorage.setItem(INSTALLATION_ID_KEY, id);
  return id;
}

async function buildReferrerPayload() {
  const parts = [];
  try {
    const initial = await Linking.getInitialURL();
    if (initial) parts.push(`initial_url=${encodeURIComponent(initial)}`);
  } catch (_) {
    /* ignore */
  }
  if (Platform.OS === 'android' && typeof Application.getInstallReferrerAsync === 'function') {
    try {
      const playReferrer = await Application.getInstallReferrerAsync();
      if (playReferrer) {
        parts.push(`play_install_referrer=${encodeURIComponent(String(playReferrer))}`);
      }
    } catch (_) {
      /* Play Install Referrer can be unavailable on sideloads, emulators, or non-Play installs. */
    }
  }
  const raw = parts.filter(Boolean).join('\n');
  return raw.length > 8000 ? raw.slice(0, 8000) : raw;
}

async function sendAcquisitionFirstOpenOnceBody() {
  try {
    const sent = await AsyncStorage.getItem(FIRST_OPEN_SENT_KEY);
    if (sent === '1') return;

    const installation_id = await getOrCreateInstallationId();
    const app_version =
      Application.nativeApplicationVersion ||
      Application.applicationVersion ||
      null;
    const referrer_raw = await buildReferrerPayload();

    const url = `${API_BASE_URL.replace(/\/+$/, '')}${getEndpoint('/acquisition/first-open')}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        installation_id,
        platform: Platform.OS,
        app_version,
        referrer_raw: referrer_raw || null,
      }),
    });

    if (res.ok) {
      await AsyncStorage.setItem(FIRST_OPEN_SENT_KEY, '1');
      trackAcquisitionFunnelEvent(
        'first_open',
        {
          app_version: app_version || '',
          has_referrer: Boolean(referrer_raw),
          platform: Platform.OS,
        },
        { status: 'success', screenName: 'AppBootstrap' },
      ).catch(() => {});
    }
  } catch (_) {
    /* non-fatal */
  }
}

/**
 * Call once per install (tracked locally). Safe to fire from App bootstrap.
 * Serialized so overlapping calls cannot create two installation rows for one cold start.
 */
export function sendAcquisitionFirstOpenOnce() {
  firstOpenChain = firstOpenChain.then(() => sendAcquisitionFirstOpenOnceBody());
  return firstOpenChain;
}

function safeEventToken(value, fallback = '') {
  return String(value || fallback)
    .trim()
    .replace(/[^a-zA-Z0-9_.:-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 120);
}

function sanitizeEventMetadata(metadata) {
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) return {};
  const safe = {};
  Object.entries(metadata)
    .slice(0, 20)
    .forEach(([key, value]) => {
      const safeKey = safeEventToken(key).slice(0, 80);
      if (!safeKey || BLOCKED_METADATA_KEYS.has(safeKey.toLowerCase())) return;
      if (value == null || typeof value === 'boolean' || typeof value === 'number') {
        safe[safeKey] = value;
      } else if (typeof value === 'string') {
        safe[safeKey] = value.trim().slice(0, 300);
      } else {
        safe[safeKey] = String(value).slice(0, 300);
      }
    });
  return safe;
}

export async function trackAcquisitionFunnelEvent(eventName, metadata = {}, options = {}) {
  try {
    const event_name = safeEventToken(eventName);
    if (!event_name) return;
    const installation_id = await getOrCreateInstallationId();
    const url = `${API_BASE_URL.replace(/\/+$/, '')}${getEndpoint('/acquisition/event')}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        installation_id,
        event_name,
        event_status: safeEventToken(options.status || metadata.status || '').slice(0, 32) || null,
        screen_name: safeEventToken(options.screenName || metadata.screen_name || '').slice(0, 120) || null,
        metadata: sanitizeEventMetadata(metadata),
      }),
    });
    if (!res.ok && __DEV__) {
      const t = await res.text().catch(() => '');
      console.warn('[acquisition] event failed', res.status, event_name, t.slice(0, 200));
    }
  } catch (e) {
    if (__DEV__) console.warn('[acquisition] event error', e?.message);
  }
}

/**
 * After login / register; uses Bearer from storage (set by caller after setAuthToken).
 */
export async function linkAcquisitionInstallationToUser() {
  try {
    const installation_id = await getOrCreateInstallationId();
    const token = await AsyncStorage.getItem('authToken');
    if (!token || !installation_id) return;

    const url = `${API_BASE_URL.replace(/\/+$/, '')}${getEndpoint('/acquisition/link-user')}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        'X-AstroRoshni-Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ installation_id }),
    });
    if (!res.ok && __DEV__) {
      const t = await res.text().catch(() => '');
      console.warn('[acquisition] link-user failed', res.status, t.slice(0, 200));
    }
  } catch (e) {
    if (__DEV__) console.warn('[acquisition] link-user error', e?.message);
  }
}
