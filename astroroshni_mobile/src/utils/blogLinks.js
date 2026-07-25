export function normalizeHttpsUrl(value) {
  const raw = value != null ? String(value).trim() : '';
  if (!raw) return '';
  try {
    const parsed = new URL(raw);
    if (parsed.protocol !== 'https:' || !parsed.hostname) return '';
    return parsed.toString();
  } catch (_) {
    return '';
  }
}

export function extractFirstHttpsUrl(value) {
  const body = value != null ? String(value) : '';
  const match = body.match(/https:\/\/[^\s<>"']+/i);
  if (!match || match.index == null) {
    return { url: '', body };
  }

  const candidate = match[0].replace(/[.,!?;:)\]}]+$/g, '');
  const url = normalizeHttpsUrl(candidate);
  if (!url) {
    return { url: '', body };
  }

  const bodyWithoutUrl = `${body.slice(0, match.index)}${body.slice(match.index + candidate.length)}`
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/[ \t]+([.,!?;:])/g, '$1')
    .replace(/:\s*[.!?]?$/, '')
    .trim();
  return { url, body: bodyWithoutUrl };
}

export function astroRoshniBlogSlug(value) {
  const normalized = normalizeHttpsUrl(value);
  if (!normalized) return '';
  try {
    const parsed = new URL(normalized);
    const hostname = parsed.hostname.toLowerCase().replace(/^www\./, '');
    if (hostname !== 'astroroshni.com') return '';
    const match = parsed.pathname.match(/^\/blog\/([^/]+)\/?$/i);
    return match ? decodeURIComponent(match[1]).trim() : '';
  } catch (_) {
    return '';
  }
}
