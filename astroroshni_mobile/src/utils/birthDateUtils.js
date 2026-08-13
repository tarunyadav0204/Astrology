/**
 * Birth dates are stored as calendar YYYY-MM-DD (or ISO date prefix).
 * `new Date("2025-08-21")` is parsed as UTC midnight → in US timezones the
 * local calendar day becomes Aug 20. Use local date parts for display/pickers.
 */

/**
 * @param {string|undefined|null} str
 * @returns {Date|null} Local calendar date at noon (stable for display & pickers)
 */
export function parseCalendarDateInput(str) {
  if (str == null || str === '') return null;
  const s = typeof str === 'string' ? str.trim() : String(str);
  const dayPart = s.includes('T') ? s.split('T')[0] : s;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dayPart);
  if (m) {
    const y = parseInt(m[1], 10);
    const mo = parseInt(m[2], 10) - 1;
    const d = parseInt(m[3], 10);
    return new Date(y, mo, d, 12, 0, 0, 0);
  }
  const fallback = new Date(s);
  return isNaN(fallback.getTime()) ? null : fallback;
}

/**
 * Normalize a saved birth date for API payloads without shifting its calendar
 * day across time zones. Older app versions stored Date objects, which become
 * full ISO timestamps in AsyncStorage; current APIs expect YYYY-MM-DD.
 *
 * @param {Date|string|undefined|null} value
 * @returns {string}
 */
export function normalizeCalendarDateForApi(value) {
  if (value == null || value === '') return '';

  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
  }

  const raw = String(value).trim();
  const calendarPrefix = /^(\d{4}-\d{2}-\d{2})(?:$|T|\s)/.exec(raw);
  if (calendarPrefix) return calendarPrefix[1];

  const parsed = parseCalendarDateInput(raw);
  if (!parsed || Number.isNaN(parsed.getTime())) return raw;
  return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, '0')}-${String(parsed.getDate()).padStart(2, '0')}`;
}

/**
 * @param {string|undefined|null} dateStr
 * @param {Intl.DateTimeFormatOptions} [options]
 * @param {string} [locale]
 */
export function formatBirthDateForDisplay(
  dateStr,
  options = { month: 'long', day: 'numeric', year: 'numeric' },
  locale = 'en-US'
) {
  const d = parseCalendarDateInput(dateStr);
  if (!d || isNaN(d.getTime())) return '';
  return d.toLocaleDateString(locale, options);
}
