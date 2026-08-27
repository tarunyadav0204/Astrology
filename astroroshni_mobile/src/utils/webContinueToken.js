const TOKEN_WITH_TRAILING_PUNCTUATION_RE = /^([A-Za-z0-9_-]{8,200})[.,;:!?)\]}]*$/;

/**
 * Canonicalize a secure continue token copied from a message URL.
 *
 * token_urlsafe never emits punctuation such as a full stop. Some messaging
 * clients nevertheless attach sentence punctuation to a URL, so accepting only
 * that harmless suffix is safe while arbitrary token mutations stay invalid.
 */
export function normalizeWebContinueToken(value) {
  const raw = String(value || '').trim();
  const match = raw.match(TOKEN_WITH_TRAILING_PUNCTUATION_RE);
  return match ? match[1] : raw;
}
