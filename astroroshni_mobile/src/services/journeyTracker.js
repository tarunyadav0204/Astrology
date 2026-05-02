import { AppState, Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Application from 'expo-application';
import * as Device from 'expo-device';
import { activityAPI } from './api';

const FLUSH_INTERVAL_MS = 4000;
const MAX_BATCH_SIZE = 20;
const SESSION_IDLE_GAP_MS = 30 * 60 * 1000;

let queue = [];
let flushTimer = null;
let flushing = false;
let appStateListenerAttached = false;
const MAX_QUEUE_SIZE = 500;
let journeySessionId = null;
let sessionStartedAtMs = 0;
let lastTrackedAtMs = 0;

const newSessionId = () =>
  `js_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;

const ensureJourneySession = (nowMs) => {
  const now = Number.isFinite(nowMs) ? nowMs : Date.now();
  const shouldRotate =
    !journeySessionId ||
    !lastTrackedAtMs ||
    now - lastTrackedAtMs > SESSION_IDLE_GAP_MS;
  if (shouldRotate) {
    journeySessionId = newSessionId();
    sessionStartedAtMs = now;
  }
  lastTrackedAtMs = now;
  return {
    sessionId: journeySessionId,
    sessionStartedAtMs,
  };
};

const scheduleFlush = () => {
  if (flushTimer) return;
  flushTimer = setTimeout(() => {
    flushTimer = null;
    void flushJourneyEvents();
  }, FLUSH_INTERVAL_MS);
};

const sanitizeMetadata = (metadata) => {
  if (!metadata || typeof metadata !== 'object') return {};
  const out = {};
  Object.entries(metadata).forEach(([k, v]) => {
    if (v == null) return;
    if (typeof v === 'string') out[k] = v.slice(0, 500);
    else if (typeof v === 'number' || typeof v === 'boolean') out[k] = v;
    else out[k] = String(v).slice(0, 500);
  });
  return out;
};

const getAppVersionMetadata = () => {
  const appVersion = Application.nativeApplicationVersion || Constants.expoConfig?.version;
  const nativeBuildVersion = Application.nativeBuildVersion || undefined;
  const fallbackAndroidCode = Constants.expoConfig?.android?.versionCode;
  const fallbackIosBuild = Constants.expoConfig?.ios?.buildNumber;
  const platformBuild =
    Platform.OS === 'android'
      ? (nativeBuildVersion || fallbackAndroidCode)
      : Platform.OS === 'ios'
      ? (nativeBuildVersion || fallbackIosBuild)
      : nativeBuildVersion;

  return {
    app_version: appVersion,
    native_build_version: nativeBuildVersion,
    platform_build_version: platformBuild != null ? String(platformBuild) : undefined,
    android_version_code:
      Platform.OS === 'android' && platformBuild != null ? Number(platformBuild) || String(platformBuild) : undefined,
    ios_build_number:
      Platform.OS === 'ios' && platformBuild != null ? String(platformBuild) : undefined,
  };
};

const getDeviceMetadata = () => ({
  device_name: Device.deviceName,
  device_model_name: Device.modelName,
  device_brand: Device.brand,
  device_manufacturer: Device.manufacturer,
  os_name: Device.osName,
  os_version: Device.osVersion,
  os_build_id: Device.osBuildId,
  android_api_level: Platform.OS === 'android' ? Device.platformApiLevel : undefined,
});

export const trackMobileJourneyEvent = (action, payload = {}) => {
  try {
    if (!appStateListenerAttached) {
      AppState.addEventListener('change', (next) => {
        if (next !== 'active') {
          void flushJourneyEvents();
        }
      });
      appStateListenerAttached = true;
    }
    const nowMs = Date.now();
    const session = ensureJourneySession(nowMs);
    const event = {
      action: String(action || 'mobile_event').slice(0, 120),
      screen_name: payload.screen_name ? String(payload.screen_name).slice(0, 120) : undefined,
      duration_ms: Number.isFinite(Number(payload.duration_ms)) ? Number(payload.duration_ms) : undefined,
      resource_type: payload.resource_type ? String(payload.resource_type).slice(0, 80) : undefined,
      resource_id: payload.resource_id ? String(payload.resource_id).slice(0, 200) : undefined,
      metadata: sanitizeMetadata({
        platform: Platform.OS,
        ...getAppVersionMetadata(),
        ...getDeviceMetadata(),
        journey_session_id: session.sessionId,
        journey_session_started_at: new Date(session.sessionStartedAtMs).toISOString(),
        ...payload.metadata,
      }),
      _attempts: 0,
    };
    queue.push(event);
    if (queue.length > MAX_QUEUE_SIZE) {
      queue = queue.slice(queue.length - MAX_QUEUE_SIZE);
    }
    if (queue.length >= MAX_BATCH_SIZE) {
      void flushJourneyEvents();
    } else {
      scheduleFlush();
    }
  } catch (_) {
    // Silent by design.
  }
};

export const flushJourneyEvents = async () => {
  if (flushing || queue.length === 0) return;
  flushing = true;
  const batch = queue.slice(0, MAX_BATCH_SIZE);
  const payload = batch.map(({ _attempts, ...rest }) => rest);
  try {
    await activityAPI.sendMobileJourneyBatch(payload);
    queue = queue.slice(batch.length);
  } catch (_) {
    // Silent retry with attempt cap.
    const retryBatch = batch
      .map((e) => ({ ...e, _attempts: Number(e._attempts || 0) + 1 }))
      .filter((e) => e._attempts <= 3);
    queue = [...retryBatch, ...queue.slice(batch.length)];
    if (queue.length > MAX_QUEUE_SIZE) {
      queue = queue.slice(0, MAX_QUEUE_SIZE);
    }
  } finally {
    flushing = false;
    if (queue.length > 0) scheduleFlush();
  }
};

