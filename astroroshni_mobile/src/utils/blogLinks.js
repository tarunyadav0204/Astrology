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
