/**
 * Shared list and helpers for phone auth (login, register, forgot password) — aligned with mobile app.
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

export function getNationalPhoneMaxLength(countryCode) {
  if (countryCode === '+1' || countryCode === '+91') return 10;
  return 15;
}

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

/** E.164-style full number for API (country code + national digits only). */
export function buildFullPhone(countryCode, nationalDigits) {
  const d = String(nationalDigits || '').replace(/\D/g, '');
  if (!d) return '';
  return `${countryCode}${d}`;
}
