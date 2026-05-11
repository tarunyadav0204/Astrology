/**
 * Map raw timeline / monthly-deep API errors to safe copy for Alert.alert.
 * Defense in depth when the server still returns technical strings.
 */

const DEFAULT_MSG =
  'We could not finish this analysis right now. Please try again in a few minutes. If you already have a saved result, use Load saved.';

const BUSY_MSG =
  'Our prediction service is temporarily busy. Please try again in a few minutes.';

export function userFacingTimelineError(raw) {
  if (raw == null) return DEFAULT_MSG;
  const s = String(raw).trim();
  if (!s) return DEFAULT_MSG;
  const lower = s.toLowerCase();

  if (
    lower.includes('not authorized') ||
    lower.includes('unauthorized') ||
    (lower.includes('401') && lower.includes('session'))
  ) {
    return 'Session expired. Please log in again.';
  }
  if (lower.includes('insufficient credit') || lower.includes('need more credit')) {
    return 'You need more credits for this analysis.';
  }

  if (
    lower.includes('resourceexhausted') ||
    lower.includes('totalcachedcontent') ||
    lower.includes('cachedcontent') ||
    lower.includes('createcachedcontent') ||
    lower.includes('context cache') ||
    lower.includes('violations {') ||
    lower.includes('generativelanguage') ||
    lower.includes('google.api') ||
    lower.includes('gemini') ||
    lower.includes('grpc') ||
    lower.includes('no api key')
  ) {
    return DEFAULT_MSG;
  }

  if (
    lower.includes('429') ||
    lower.includes('quota exceeded') ||
    lower.includes('rate limit') ||
    lower.includes('too many requests')
  ) {
    return BUSY_MSG;
  }

  if (lower.includes('traceback') || lower.includes('file "') || lower.includes('0x')) {
    return DEFAULT_MSG;
  }

  if (s.length > 220) {
    return DEFAULT_MSG;
  }

  return s;
}
