/**
 * Shared list and helpers for phone auth (login, register, forgot password).
 */

export const COUNTRY_CODES = [
  { code: '+1', country: 'US/CA', flag: '🇺🇸', name: 'United States/Canada' },
  { code: '+44', country: 'UK', flag: '🇬🇧', name: 'United Kingdom' },
  { code: '+91', country: 'IN', flag: '🇮🇳', name: 'India' },
  { code: '+61', country: 'AU', flag: '🇦🇺', name: 'Australia' },
  { code: '+971', country: 'AE', flag: '🇦🇪', name: 'UAE' },
  { code: '+65', country: 'SG', flag: '🇸🇬', name: 'Singapore' },
  { code: '+60', country: 'MY', flag: '🇲🇾', name: 'Malaysia' },
  { code: '+81', country: 'JP', flag: '🇯🇵', name: 'Japan' },
  { code: '+86', country: 'CN', flag: '🇨🇳', name: 'China' },
  { code: '+49', country: 'DE', flag: '🇩🇪', name: 'Germany' },
  { code: '+33', country: 'FR', flag: '🇫🇷', name: 'France' },
];

/** National number max length (digits only, excluding country code). */
export function getNationalPhoneMaxLength(countryCode) {
  if (countryCode === '+1' || countryCode === '+91') return 10;
  return 15;
}

/** Minimum digits required before Continue / Send is allowed. */
export function getNationalPhoneMinLength(countryCode) {
  if (countryCode === '+1' || countryCode === '+91') return 10;
  return 8;
}

export function isNationalPhoneValid(countryCode, nationalDigits) {
  const d = nationalDigits || '';
  const min = getNationalPhoneMinLength(countryCode);
  const max = getNationalPhoneMaxLength(countryCode);
  return d.length >= min && d.length <= max;
}

/** True when selected dial code is India (SMS-first; email not required for OTP). */
export function otpEmailRequiredForCountry(countryCode) {
  return (countryCode || '') !== '+91';
}

/**
 * Mirrors backend `_is_india_number` for legacy single-field phone inputs (no country picker).
 */
export function isIndiaPhoneForOtp(phone) {
  const raw = String(phone || '')
    .trim()
    .replace(/\s/g, '')
    .replace(/-/g, '')
    .replace(/\(/g, '')
    .replace(/\)/g, '');
  if (!raw) return false;
  if (raw.startsWith('+1')) return false;
  if (raw.startsWith('+91')) return true;
  const digits = raw.replace(/\D/g, '');
  if (digits.length === 11 && digits.startsWith('1')) return false;
  if (digits.length === 12 && digits.startsWith('91')) return true;
  if (digits.length === 10 && !raw.startsWith('+')) return true;
  return false;
}

/** Registration / reset OTP email required for all numbers except India-shaped ones. */
export function otpEmailRequiredForPhone(phone) {
  return !isIndiaPhoneForOtp(phone);
}
