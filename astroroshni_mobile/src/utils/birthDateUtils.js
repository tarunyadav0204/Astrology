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
