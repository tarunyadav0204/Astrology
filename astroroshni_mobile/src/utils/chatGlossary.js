const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const escapeAttribute = (value) => value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// One pass over visible text: never wrap another tooltip or its attributes.
const wrapGlossaryTerms = (html, glossary, wrapped = new Set()) => {
  const keys = Object.keys(glossary || {})
    .filter((key) => key && String(glossary[key] || '').trim())
    .sort((a, b) => b.length - a.length);
  if (!keys.length) return html;
  const byLower = new Map(keys.map((key) => [key.toLowerCase(), key]));
  const pattern = new RegExp(keys.map((key) => (
    /[^\u0000-\u007f]/.test(key) ? escapeRegex(key) : `\\b${escapeRegex(key)}\\b`
  )).join('|'), 'gi');
  let protectedDepth = 0;
  return String(html || '').split(/(<[^>]*>)/g).map((part) => {
    if (part.startsWith('<')) {
      if (/^<(?:tooltip|term)\b/i.test(part)) protectedDepth += 1;
      if (/^<\/(?:tooltip|term)\b/i.test(part)) protectedDepth = Math.max(0, protectedDepth - 1);
      return part;
    }
    if (protectedDepth) return part;
    return part.replace(pattern, (text) => {
      const key = byLower.get(text.toLowerCase());
      if (!key || wrapped.has(key.toLowerCase())) return text;
      wrapped.add(key.toLowerCase());
      return `<tooltip data-term="${escapeAttribute(key)}">${text}</tooltip>`;
    });
  }).join('');
};

module.exports = { wrapGlossaryTerms };
