import { storage } from '../services/storage';

export const PENDING_PAID_ACTION_KEY = 'guest_pending_paid_action';
export const GUEST_ID_PREFIX = 'guest_';

export const isGuestId = (id) =>
  typeof id === 'string' && id.startsWith(GUEST_ID_PREFIX);

export const makeGuestProfileId = () =>
  `${GUEST_ID_PREFIX}${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

export const getAuthTokenSafe = async () => {
  try {
    return await storage.getAuthToken();
  } catch (_) {
    return null;
  }
};

export const isGuestSession = async () => !(await getAuthTokenSafe());

export const setPendingPaidAction = async (action) => {
  try {
    if (!action) {
      await storage.removeItem(PENDING_PAID_ACTION_KEY);
      return;
    }
    await storage.setItem(
      PENDING_PAID_ACTION_KEY,
      JSON.stringify({ ...action, savedAt: Date.now() }),
    );
  } catch (_) {
    /* ignore */
  }
};

export const getPendingPaidAction = async () => {
  try {
    const raw = await storage.getItem(PENDING_PAID_ACTION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Expire after 30 minutes
    if (!parsed?.savedAt || Date.now() - parsed.savedAt > 30 * 60 * 1000) {
      await clearPendingPaidAction();
      return null;
    }
    return parsed;
  } catch (_) {
    return null;
  }
};

export const clearPendingPaidAction = async () => {
  try {
    await storage.removeItem(PENDING_PAID_ACTION_KEY);
  } catch (_) {
    /* ignore */
  }
};

const normalizeCoord = (value) => {
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return '';
  return String(Math.round(n * 1000000) / 1000000);
};

const normalizeDate = (value) => {
  if (!value) return '';
  const raw = String(value);
  return raw.includes('T') ? raw.split('T')[0] : raw;
};

const normalizeTime = (value) => {
  if (!value) return '';
  const raw = String(value);
  if (raw.includes('T')) {
    const parsed = new Date(raw);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toTimeString().slice(0, 5);
    }
  }
  return raw.slice(0, 8);
};

export const birthFingerprint = (profile) => {
  if (!profile) return '';
  return [
    normalizeDate(profile.date),
    normalizeTime(profile.time),
    normalizeCoord(profile.latitude),
    normalizeCoord(profile.longitude),
    String(profile.name || '').trim().toLowerCase(),
  ].join('|');
};

/**
 * Upload local guest (or unsynced) birth profiles to the server after login.
 * Returns the preferred active birth details to keep on device.
 */
export const mergeGuestProfilesAfterLogin = async ({ chartAPI }) => {
  const localProfiles = (await storage.getBirthProfiles()) || [];
  const activeLocal = await storage.getBirthDetails();

  let serverCharts = [];
  try {
    const chartsRes = await chartAPI.getExistingCharts('', 50, 0);
    serverCharts = Array.isArray(chartsRes?.data?.charts) ? chartsRes.data.charts : [];
  } catch (_) {
    serverCharts = [];
  }

  const serverFingerprints = new Set(
    serverCharts.map((c) => birthFingerprint(c)).filter(Boolean),
  );

  const guestsToUpload = localProfiles.filter((p) => {
    if (!p?.date || !p?.time || p?.latitude == null || p?.longitude == null) return false;
    const fp = birthFingerprint(p);
    if (!fp || serverFingerprints.has(fp)) return false;
    // Upload guest ids always; also upload local-only profiles without a numeric server id.
    return isGuestId(p.id) || p.id == null || Number.isNaN(Number(p.id));
  });

  const uploaded = [];
  for (const profile of guestsToUpload) {
    try {
      const birthData = {
        name: profile.name,
        date: normalizeDate(profile.date),
        time: typeof profile.time === 'string'
          ? profile.time
          : (profile.time?.toTimeString?.().split(' ')[0] || String(profile.time)),
        place: profile.place || '',
        latitude: profile.latitude,
        longitude: profile.longitude,
        gender: profile.gender || '',
        relation: profile.relation || 'other',
        relation_order: profile.relation_order,
        relation_side: profile.relation_side || '',
        relation_label: profile.relation_label || '',
        is_family_member: profile.is_family_member,
      };
      const chartData = await chartAPI.calculateChart(birthData);
      const actualData = chartData?.data || chartData;
      const birthChartId = actualData?.birth_chart_id;
      if (!birthChartId) continue;
      const synced = {
        ...profile,
        id: birthChartId,
        date: birthData.date,
        time: birthData.time,
      };
      uploaded.push(synced);
      serverFingerprints.add(birthFingerprint(synced));
    } catch (_) {
      /* keep local; user can retry later */
    }
  }

  // Rebuild local list: keep non-guest locals + uploaded + server charts not already present
  const byFp = new Map();
  for (const p of localProfiles) {
    if (isGuestId(p.id)) continue;
    const fp = birthFingerprint(p);
    if (fp) byFp.set(fp, p);
  }
  for (const p of uploaded) {
    byFp.set(birthFingerprint(p), p);
  }
  for (const chart of serverCharts) {
    const mapped = {
      id: chart.id || chart._id,
      name: chart.name,
      date: chart.date,
      time: chart.time,
      place: chart.place,
      latitude: chart.latitude,
      longitude: chart.longitude,
      gender: chart.gender,
      relation: chart.relation || 'other',
      relation_order: chart.relation_order ?? null,
      relation_side: chart.relation_side || '',
      relation_label: chart.relation_label || '',
      is_family_member: !!chart.is_family_member,
      isSelf: String(chart.relation || '').trim().toLowerCase() === 'self',
    };
    const fp = birthFingerprint(mapped);
    if (fp && !byFp.has(fp)) byFp.set(fp, mapped);
  }

  const mergedProfiles = Array.from(byFp.values());
  await storage.setBirthProfiles(mergedProfiles);

  // Prefer previously active local chart (matched by fingerprint), else self, else first
  let nextActive = null;
  if (activeLocal) {
    const fp = birthFingerprint(activeLocal);
    nextActive = mergedProfiles.find((p) => birthFingerprint(p) === fp) || null;
  }
  if (!nextActive) {
    nextActive =
      mergedProfiles.find((p) => String(p.relation || '').toLowerCase() === 'self') ||
      mergedProfiles[0] ||
      null;
  }
  if (nextActive) {
    await storage.setBirthDetails(nextActive);
  }

  return { mergedProfiles, active: nextActive, uploadedCount: uploaded.length };
};
