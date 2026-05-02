export function buildQueryContext() {
  let timezoneName = null;
  try {
    timezoneName = Intl?.DateTimeFormat?.().resolvedOptions?.().timeZone || null;
  } catch (e) {
    timezoneName = null;
  }

  const now = new Date();
  return {
    timezone_name: timezoneName,
    utc_offset_minutes: -now.getTimezoneOffset(),
    client_now_iso: now.toISOString(),
  };
}

