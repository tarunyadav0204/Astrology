/**
 * Whether a client-reported chat failure should appear in Admin → Chat errors.
 * CHART_SESSION_MISMATCH: the app usually auto-retries with a new session; only post when
 * ChatScreen tagged the Error as a final user-visible failure (retry/session create failed).
 */
export function shouldPostChatErrorToAdminLogs(error) {
  const msg = String(error?.message || '');
  if (!/CHART_SESSION_MISMATCH/i.test(msg)) return true;
  if (error?.retryFailedAfterChartSessionRecovery) return true;
  if (error?.createSessionFailedAfterChartMismatch) return true;
  return false;
}
