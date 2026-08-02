/**
 * Devanagari often has no true 800-weight face in the system/web stack,
 * so fontWeight 800/900 is synthesized and looks blobbed/shadowed.
 * Letter-spacing + uppercase also break Hindi metrics.
 */

export function isHindiLocale(language) {
  const code = String(language || '').toLowerCase().split(/[-_]/)[0];
  return code === 'hi' || code === 'hindi';
}

/** Soften Latin-tuned headline styles when UI language is Hindi. */
export function hindiReadableTextStyle(language, base = {}) {
  if (!isHindiLocale(language)) return base;
  const next = { ...base };
  const weight = String(next.fontWeight || '');
  // Cap at 600 — heavier weights are usually synthetic for Devanagari and look smudged.
  if (weight === '900' || weight === '800' || weight === '700' || weight === 'bold') {
    next.fontWeight = '600';
  }
  if (next.letterSpacing != null && next.letterSpacing > 0) {
    next.letterSpacing = 0;
  }
  if (next.textTransform === 'uppercase') {
    next.textTransform = 'none';
  }
  return next;
}
