/** Add real text labels so sentiment does not depend on color or CSS content. */
export const labelChatSentiment = (html) => String(html || '').replace(
  /(<span\b[^>]*class=["'][^"']*chat-sentiment-(positive|negative)[^"']*["'][^>]*>)/gi,
  (_match, opening, kind) => `${opening}<small class="chat-sentiment-label">${kind.toLowerCase() === 'positive' ? '✓ Support' : '! Caution'} · </small>`
);
